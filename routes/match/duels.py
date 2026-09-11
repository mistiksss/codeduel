"""Active duel pages and match-status APIs."""

import logging
from datetime import timedelta

from flask import jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from constants import ACTIVE_MATCH_TTL_MINUTES, DUEL_MAX_TIME_SECONDS
from extensions import db
from models import Attempt, Match, MatchResult, Task, TestCase, User
from routes.match.blueprint import match_bp
from routes.match.serializers import (
    load_opponent_and_task,
    opponent_id_for,
    serialize_user_brief,
)
from services.match_service import (
    DUEL_MAX_TIME,
    apply_match_result,
    build_match_response_for_user,
    finalize_match_if_needed,
    get_active_match_for_user,
    get_task_max_score,
    normalize_match_started_at,
)
from utils.extensions_access import get_socketio
from utils.utc import to_utc_aware, utc_now

logger = logging.getLogger(__name__)


def _ensure_forfeit_result(match, user_id: int, score: int, tests_passed: int, total: int, winner_id: int):
    """Insert a placeholder Attempt + MatchResult when a player surrenders."""
    existing = MatchResult.query.filter_by(match_id=match.id, user_id=user_id).first()
    if existing:
        return
    now_ts = utc_now()
    attempt = Attempt(
        user_id=user_id,
        task_id=match.task_id,
        code='',
        language='forfeit',
        status='FORFEIT_WIN' if user_id == winner_id else 'FORFEIT_LOSS',
        execution_time=0.0,
        tests_passed=tests_passed,
        total_tests=total,
        score=score,
        error_message=None,
        submitted_at=now_ts,
    )
    db.session.add(attempt)
    db.session.flush()
    match_result = MatchResult(
        match_id=match.id,
        user_id=user_id,
        attempt_id=attempt.id,
        score=score,
        tests_passed=tests_passed,
        total_tests=total,
        execution_time=0.0,
        submitted_at=now_ts,
    )
    db.session.add(match_result)


@match_bp.route('/api/match/<int:match_id>/status')
@login_required
def get_match_status(match_id):
    """Full match payload including both participants."""
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403
        finalize_match_if_needed(match)
        db.session.refresh(match)
        user_result = MatchResult.query.filter_by(match_id=match_id, user_id=match.user_id).first()
        opponent_result = MatchResult.query.filter_by(
            match_id=match_id, user_id=match.opponent_id,
        ).first()
        user_info = db.session.get(User, match.user_id)
        opponent_info = db.session.get(User, match.opponent_id)
        response_data = build_match_response_for_user(
            match,
            user_result,
            opponent_result,
            current_user.id,
            user_info,
            opponent_info,
            include_participants=True,
        )
        return jsonify(response_data)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@match_bp.route('/api/match/<int:match_id>/opponent_info')
@login_required
def get_opponent_info(match_id):
    """Opponent identity plus their latest judged score in this match."""
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403
        opponent_id = opponent_id_for(match, current_user.id)
        opponent_user = db.session.get(User, opponent_id)
        opponent_result = MatchResult.query.filter_by(
            match_id=match_id, user_id=opponent_id,
        ).first()
        return jsonify({
            'id': opponent_user.id,
            'username': opponent_user.username,
            'elo': opponent_user.elo,
            'has_submitted': opponent_result is not None,
            'score': (opponent_result.score if opponent_result else 0) or 0,
            'tests_passed': (opponent_result.tests_passed if opponent_result else 0) or 0,
            'total_tests': (opponent_result.total_tests if opponent_result else 0) or 0,
            'execution_time': opponent_result.execution_time if opponent_result else None,
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@match_bp.route('/api/match/active')
@login_required
def get_active_match():
    """Latest unfinished match created within the active-match TTL."""
    try:
        active_ttl = utc_now() - timedelta(minutes=ACTIVE_MATCH_TTL_MINUTES)
        match = Match.query.filter(
            or_(Match.user_id == current_user.id, Match.opponent_id == current_user.id),
            Match.result == None,  # noqa: E711
            Match.created_at >= active_ttl,
        ).order_by(Match.created_at.desc()).first()
        if match:
            opponent, task = load_opponent_and_task(match, current_user.id)
            return jsonify({
                'match_id': match.id,
                'opponent': serialize_user_brief(opponent),
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'difficulty': task.difficulty,
                } if task else None,
            })
        return jsonify({'match_id': None})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@match_bp.route('/api/match/forfeit', methods=['POST'])
@login_required
def forfeit_active_match():
    """Surrender the current duel: opponent wins with full task score."""
    try:
        match = get_active_match_for_user(current_user.id)
        if not match:
            return jsonify({'error': 'No active match'}), 400
        match.started_at = normalize_match_started_at(match)
        forfeiter_id = current_user.id
        if forfeiter_id == match.user_id:
            winner_id = match.opponent_id
            stored_result = 'loss'
        else:
            winner_id = match.user_id
            stored_result = 'win'
        task_max = get_task_max_score(match.task_id)
        total_tests = TestCase.query.filter_by(task_id=match.task_id).count()
        _ensure_forfeit_result(match, winner_id, task_max, total_tests, total_tests, winner_id)
        _ensure_forfeit_result(match, forfeiter_id, 0, 0, total_tests, winner_id)
        db.session.commit()
        apply_match_result(match, stored_result)
        db.session.refresh(match)
        try:
            socketio = get_socketio()
            if socketio:
                socketio.emit('match_update', {'match_id': match.id}, room=str(match.id))
        except Exception:
            pass
        user_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.user_id).first()
        opponent_result = MatchResult.query.filter_by(
            match_id=match.id, user_id=match.opponent_id,
        ).first()
        user_info = db.session.get(User, match.user_id)
        opponent_info = db.session.get(User, match.opponent_id)
        response_data = build_match_response_for_user(
            match,
            user_result,
            opponent_result,
            current_user.id,
            user_info,
            opponent_info,
            rating_change_opponent_override=0,
        )
        response_data['ok'] = True
        return jsonify(response_data)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@match_bp.route('/api/match/history')
@login_required
def get_match_history():
    """Last three finished matches for the current user."""
    try:
        matches = Match.query.filter(
            or_(Match.user_id == current_user.id, Match.opponent_id == current_user.id),
            Match.result != None,  # noqa: E711
        ).order_by(Match.created_at.desc()).limit(3).all()
        opponent_ids = list({
            match.opponent_id if match.user_id == current_user.id else match.user_id
            for match in matches
        })
        task_ids = list({match.task_id for match in matches})
        opponents_by_id = (
            {user.id: user for user in User.query.filter(User.id.in_(opponent_ids)).all()}
            if opponent_ids else {}
        )
        tasks_by_id = (
            {task.id: task for task in Task.query.filter(Task.id.in_(task_ids)).all()}
            if task_ids else {}
        )
        match_history = []
        for match in matches:
            opponent_id = opponent_id_for(match, current_user.id)
            opponent = opponents_by_id.get(opponent_id)
            task = tasks_by_id.get(match.task_id)
            if (current_user.id == match.user_id and match.result == 'win') or (
                current_user.id == match.opponent_id and match.result == 'loss'
            ):
                user_result = 'win'
            elif (current_user.id == match.user_id and match.result == 'loss') or (
                current_user.id == match.opponent_id and match.result == 'win'
            ):
                user_result = 'loss'
            else:
                user_result = 'draw'
            rating_change = (
                match.user_rating_change
                if current_user.id == match.user_id
                else match.opponent_rating_change
            )
            match_history.append({
                'match_id': match.id,
                'task_id': match.task_id,
                'task_title': task.title if task else 'Unknown',
                'opponent_username': opponent.username if opponent else '—',
                'opponent_elo': opponent.elo if opponent else 0,
                'result': user_result,
                'rating_change': rating_change,
                'created_at': (
                    match.created_at.strftime('%Y-%m-%d %H:%M') if match.created_at else None
                ),
            })
        return jsonify({'matches': match_history})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@match_bp.route('/duel/<int:match_id>')
@login_required
def duel_arena(match_id):
    """Arena page for an in-progress duel."""
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return redirect(url_for('match.matchmaking_page'))
        finalize_match_if_needed(match)
        db.session.refresh(match)
        if match.result is not None:
            return redirect(url_for('match.matchmaking_page'))
        opponent_id = opponent_id_for(match, current_user.id)
        opponent = db.session.get(User, opponent_id)
        task = Task.query.get_or_404(match.task_id)
        if not match.started_at:
            match.started_at = to_utc_aware(match.created_at) or utc_now()
            db.session.commit()
        else:
            fixed = to_utc_aware(match.started_at)
            if fixed != match.started_at:
                match.started_at = fixed
                db.session.commit()
        started_at = to_utc_aware(match.started_at)
        now_utc = utc_now()
        elapsed_time = int((now_utc - started_at).total_seconds()) if started_at else 0
        time_remaining = max(0, DUEL_MAX_TIME_SECONDS - elapsed_time)
        return render_template(
            'arena.html',
            task=task,
            opponent=opponent,
            current_user=current_user,
            match=match,
            time_remaining=time_remaining,
        )
    except Exception:
        logger.exception('Failed to load duel page')
        return redirect(url_for('match.matchmaking_page'))


@match_bp.route('/api/duel/<int:match_id>/status')
@login_required
def get_duel_status(match_id):
    """Live scoreboard + remaining time for the arena poller."""
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403
        finalize_match_if_needed(match)
        db.session.refresh(match)
        opponent_id = opponent_id_for(match, current_user.id)
        opponent_user = db.session.get(User, opponent_id)
        user_result = MatchResult.query.filter_by(
            match_id=match_id, user_id=current_user.id,
        ).first()
        opponent_result = MatchResult.query.filter_by(
            match_id=match_id, user_id=opponent_id,
        ).first()
        response_data = {
            'match_id': match.id,
            'result': match.result,
            'time_remaining': None,
            'user_rating_change': (
                match.user_rating_change
                if current_user.id == match.user_id
                else match.opponent_rating_change
            ),
            'opponent_rating_change': (
                match.opponent_rating_change
                if current_user.id == match.user_id
                else match.user_rating_change
            ),
            'participants': {
                'user': {
                    **serialize_user_brief(current_user),
                    'has_submitted': user_result is not None,
                    'score': (user_result.score if user_result else 0) or 0,
                    'tests_passed': (user_result.tests_passed if user_result else 0) or 0,
                    'total_tests': (user_result.total_tests if user_result else 0) or 0,
                },
                'opponent': {
                    **serialize_user_brief(opponent_user),
                    'has_submitted': opponent_result is not None,
                    'score': (opponent_result.score if opponent_result else 0) or 0,
                    'tests_passed': (opponent_result.tests_passed if opponent_result else 0) or 0,
                    'total_tests': (opponent_result.total_tests if opponent_result else 0) or 0,
                },
            },
        }
        if match.result is None and match.started_at:
            started_at = to_utc_aware(match.started_at)
            now_utc = utc_now()
            elapsed_time = int((now_utc - started_at).total_seconds()) if started_at else 0
            response_data['time_remaining'] = max(0, DUEL_MAX_TIME - elapsed_time)
        else:
            response_data['time_remaining'] = 0
        return jsonify(response_data)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
