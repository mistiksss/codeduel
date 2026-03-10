"""Match routes: matchmaking, duel, status, opponent_info, forfeit, history."""
import traceback
from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models import User, Task, Match, MatchResult, MatchmakingQueue, TestCase, Attempt
from services.match_service import (
    to_utc_aware,
    normalize_match_started_at,
    _apply_match_result,
    _build_match_response_for_user,
    get_active_match_for_user,
    get_task_max_score,
    finalize_match_if_needed,
    DUEL_MAX_TIME as duel_max_time,
)

match_bp = Blueprint('match', __name__, url_prefix='')


def get_matchmaking_system():
    from flask import current_app
    return getattr(current_app, 'matchmaking_system', None)


@match_bp.route('/play-with-bot')
@login_required
def play_with_bot():
    return redirect(url_for('tasks'))


@match_bp.route('/matchmaking')
@login_required
def matchmaking_page():
    """Страница поиска матча. Помечаем онбординг завершённым при первом заходе."""
    if not getattr(current_user, 'onboarding_completed', False):
        current_user.onboarding_completed = True
        db.session.commit()
    return render_template('matchmaking.html')


@match_bp.route('/api/matchmaking/start', methods=['POST'])
@login_required
def start_matchmaking():
    try:
        mms = get_matchmaking_system()
        if not mms:
            return jsonify({'success': False, 'error': 'Matchmaking unavailable'}), 500
        data = request.get_json() or {}
        difficulty = data.get('difficulty', 'any')
        print(f"/api/matchmaking/start -> current_user={current_user.id} ({current_user.username}), ELO={current_user.elo}, difficulty={difficulty}")
        active_match = get_active_match_for_user(current_user.id)
        if active_match:
            opponent_id = active_match.opponent_id if current_user.id == active_match.user_id else active_match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, active_match.task_id)
            return jsonify({
                'success': True, 'match_found': True, 'match_id': active_match.id,
                'opponent': {'id': opponent.id, 'username': opponent.username, 'elo': opponent.elo},
                'task_id': active_match.task_id, 'task_title': task.title if task else 'Unknown Task',
                'difficulty': difficulty, 'message': 'У вас уже есть активный матч'
            })
        result = mms.find_opponent(user_id=current_user.id, user_elo=current_user.elo, difficulty=difficulty)
        result['match_found'] = bool(result.get('match_id'))
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка при старте матчмейкинга: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@match_bp.route('/api/matchmaking/queue_count', methods=['GET'])
def get_matchmaking_queue_count():
    try:
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        count = MatchmakingQueue.query.filter(
            MatchmakingQueue.status == 'searching'
        ).join(User, MatchmakingQueue.user_id == User.id).filter(
            or_(User.is_online == True, User.last_seen >= five_minutes_ago)
        ).count()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0, 'error': str(e)})


@match_bp.route('/api/matchmaking/cancel', methods=['POST'])
@login_required
def cancel_matchmaking():
    try:
        get_matchmaking_system().cancel_search(current_user.id)
        match = Match.query.filter(
            or_(Match.user_id == current_user.id, Match.opponent_id == current_user.id),
            Match.result == None
        ).order_by(Match.created_at.desc()).first()
        if match:
            MatchResult.query.filter_by(match_id=match.id).delete()
            db.session.delete(match)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Поиск отменен'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@match_bp.route('/api/matchmaking/status', methods=['GET'])
@login_required
def get_matchmaking_status():
    try:
        in_queue = MatchmakingQueue.query.filter_by(user_id=current_user.id, status='searching').first() is not None
        queue_stats = get_matchmaking_system().get_queue_stats(current_user.id) if in_queue else {}
        match = get_active_match_for_user(current_user.id)
        response_data = {'in_queue': in_queue, 'queue_stats': queue_stats, 'match_found': match is not None}
        if match:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, match.task_id)
            response_data.update({
                'match_id': match.id,
                'opponent': {'id': opponent.id, 'username': opponent.username, 'elo': opponent.elo},
                'task_id': match.task_id, 'task_title': task.title if task else 'Unknown Task'
            })
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@match_bp.route('/api/matchmaking/poll', methods=['GET'])
@login_required
def poll_matchmaking():
    try:
        in_queue = MatchmakingQueue.query.filter_by(user_id=current_user.id, status='searching').first() is not None
        ping_ok = get_matchmaking_system().ping_queue(current_user.id) if in_queue else False
        match = get_active_match_for_user(current_user.id)
        if match:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, match.task_id)
            return jsonify({
                'match_found': True, 'match_id': match.id,
                'opponent': {'id': opponent.id, 'username': opponent.username, 'elo': opponent.elo},
                'task_id': match.task_id, 'task_title': task.title if task else 'Unknown Task'
            })
        queue_stats = get_matchmaking_system().get_queue_stats(current_user.id) if in_queue else {'total_players': 0}
        return jsonify({
            'match_found': False, 'still_searching': bool(in_queue), 'in_queue': bool(in_queue),
            'ping_ok': bool(ping_ok), 'queue_stats': queue_stats,
            'message': 'Ожидание соперника...' if in_queue else 'Вы не в очереди. Нажмите Start для нового поиска.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@match_bp.route('/api/matchmaking/ping', methods=['POST'])
@login_required
def ping_matchmaking():
    try:
        success = get_matchmaking_system().ping_queue(current_user.id)
        return jsonify({'success': True, 'message': 'Ping updated'}) if success else jsonify({'success': False, 'error': 'Not in queue'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@match_bp.route('/api/match/<int:match_id>/status')
@login_required
def get_match_status(match_id):
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403
        finalize_match_if_needed(match)
        db.session.refresh(match)
        user_result = MatchResult.query.filter_by(match_id=match_id, user_id=match.user_id).first()
        opponent_result = MatchResult.query.filter_by(match_id=match_id, user_id=match.opponent_id).first()
        user_info = db.session.get(User, match.user_id)
        opponent_info = db.session.get(User, match.opponent_id)
        response_data = _build_match_response_for_user(
            match, user_result, opponent_result, current_user.id,
            user_info, opponent_info, include_participants=True
        )
        if hasattr(current_user, 'has_premium') and current_user.has_premium():
            if opponent_result and opponent_result.attempt_id:
                opp_attempt = db.session.get(Attempt, opponent_result.attempt_id)
                if opp_attempt:
                    response_data['opponent_code'] = opp_attempt.code
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@match_bp.route('/api/match/<int:match_id>/opponent_info')
@login_required
def get_opponent_info(match_id):
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403
        opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
        opponent_user = db.session.get(User, opponent_id)
        opponent_result = MatchResult.query.filter_by(match_id=match_id, user_id=opponent_id).first()
        return jsonify({
            'id': opponent_user.id, 'username': opponent_user.username, 'elo': opponent_user.elo,
            'has_submitted': opponent_result is not None,
            'score': (opponent_result.score if opponent_result else 0) or 0,
            'tests_passed': (opponent_result.tests_passed if opponent_result else 0) or 0,
            'total_tests': (opponent_result.total_tests if opponent_result else 0) or 0,
            'execution_time': opponent_result.execution_time if opponent_result else None,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@match_bp.route('/api/match/active')
@login_required
def get_active_match():
    try:
        active_ttl = datetime.now(timezone.utc) - timedelta(minutes=10)
        match = Match.query.filter(
            or_(Match.user_id == current_user.id, Match.opponent_id == current_user.id),
            Match.result == None,
            Match.created_at >= active_ttl
        ).order_by(Match.created_at.desc()).first()
        if match:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = db.session.get(User, opponent_id)
            task = db.session.get(Task, match.task_id)
            return jsonify({
                'match_id': match.id,
                'opponent': {'id': opponent.id, 'username': opponent.username, 'elo': opponent.elo},
                'task': {'id': task.id, 'title': task.title, 'difficulty': task.difficulty} if task else None
            })
        return jsonify({'match_id': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _ensure_forfeit_result(match, user_id: int, score: int, tests_passed: int, total: int, winner_id: int):
    existing = MatchResult.query.filter_by(match_id=match.id, user_id=user_id).first()
    if existing:
        return
    now_ts = datetime.now(timezone.utc)
    attempt = Attempt(
        user_id=user_id, task_id=match.task_id, code='', language='forfeit',
        status='FORFEIT_WIN' if user_id == winner_id else 'FORFEIT_LOSS',
        execution_time=0.0, memory_used=0, tests_passed=tests_passed, total_tests=total,
        score=score, error_message=None, submitted_at=now_ts,
    )
    db.session.add(attempt)
    db.session.flush()
    mr = MatchResult(match_id=match.id, user_id=user_id, attempt_id=attempt.id, score=score,
                     tests_passed=tests_passed, total_tests=total, execution_time=0.0, submitted_at=now_ts)
    db.session.add(mr)


@match_bp.route('/api/match/forfeit', methods=['POST'])
@login_required
def forfeit_active_match():
    try:
        match = get_active_match_for_user(current_user.id)
        if not match:
            return jsonify({'error': 'No active match'}), 400
        match.started_at = normalize_match_started_at(match)
        forfeiter_id = current_user.id
        if forfeiter_id == match.user_id:
            winner_id = match.opponent_id
            db_result = 'loss'
        else:
            winner_id = match.user_id
            db_result = 'win'
        task_max = get_task_max_score(match.task_id)
        total_tests = TestCase.query.filter_by(task_id=match.task_id).count()
        _ensure_forfeit_result(match, winner_id, task_max, total_tests, total_tests, winner_id)
        _ensure_forfeit_result(match, forfeiter_id, 0, 0, total_tests, winner_id)
        db.session.commit()
        _apply_match_result(match, db_result)
        db.session.refresh(match)
        try:
            from flask import current_app
            sio = getattr(current_app, 'socketio', None)
            if sio:
                sio.emit('match_update', {'match_id': match.id}, room=str(match.id))
        except Exception:
            pass
        user_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.user_id).first()
        opponent_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.opponent_id).first()
        user_info = db.session.get(User, match.user_id)
        opponent_info = db.session.get(User, match.opponent_id)
        response_data = _build_match_response_for_user(
            match, user_result, opponent_result, current_user.id,
            user_info, opponent_info, rating_change_opponent_override=0
        )
        response_data['ok'] = True
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@match_bp.route('/api/match/history')
@login_required
def get_match_history():
    try:
        limit = 20 if (hasattr(current_user, 'has_premium') and current_user.has_premium()) else 3
        matches = Match.query.filter(
            or_(Match.user_id == current_user.id, Match.opponent_id == current_user.id),
            Match.result != None
        ).order_by(Match.created_at.desc()).limit(limit).all()
        opponent_ids = list({m.opponent_id if m.user_id == current_user.id else m.user_id for m in matches})
        task_ids = list({m.task_id for m in matches})
        opponents_by_id = {u.id: u for u in User.query.filter(User.id.in_(opponent_ids)).all()} if opponent_ids else {}
        tasks_by_id = {t.id: t for t in Task.query.filter(Task.id.in_(task_ids)).all()} if task_ids else {}
        match_history = []
        for match in matches:
            opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
            opponent = opponents_by_id.get(opponent_id)
            task = tasks_by_id.get(match.task_id)
            user_result = 'win' if (current_user.id == match.user_id and match.result == 'win') or \
                (current_user.id == match.opponent_id and match.result == 'loss') else \
                'loss' if (current_user.id == match.user_id and match.result == 'loss') or \
                (current_user.id == match.opponent_id and match.result == 'win') else 'draw'
            rating_change = match.user_rating_change if current_user.id == match.user_id else match.opponent_rating_change
            match_history.append({
                'match_id': match.id, 'task_id': match.task_id, 'task_title': task.title if task else 'Unknown',
                'opponent_username': opponent.username if opponent else '—', 'opponent_elo': opponent.elo if opponent else 0,
                'result': user_result, 'rating_change': rating_change,
                'created_at': match.created_at.strftime('%Y-%m-%d %H:%M') if match.created_at else None
            })
        return jsonify({'matches': match_history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@match_bp.route('/duel/<int:match_id>')
@login_required
def duel_arena(match_id):
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return redirect(url_for('match.matchmaking_page'))
        finalize_match_if_needed(match)
        db.session.refresh(match)
        if match.result is not None:
            return redirect(url_for('match.matchmaking_page'))
        opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
        opponent = db.session.get(User, opponent_id)
        task = Task.query.get_or_404(match.task_id)
        if not match.started_at:
            match.started_at = to_utc_aware(match.created_at) or datetime.now(timezone.utc)
            db.session.commit()
        else:
            fixed = to_utc_aware(match.started_at)
            if fixed != match.started_at:
                match.started_at = fixed
                db.session.commit()
        started_at = to_utc_aware(match.started_at)
        now_utc = datetime.now(timezone.utc)
        elapsed_time = int((now_utc - started_at).total_seconds()) if started_at else 0
        time_remaining = max(0, 7200 - elapsed_time)
        is_premium = getattr(current_user, 'has_premium', lambda: False)() if current_user.is_authenticated else False
        return render_template('arena.html', task=task, opponent=opponent, current_user=current_user,
                               match=match, time_remaining=time_remaining, is_premium=is_premium)
    except Exception as e:
        print(f"Ошибка при загрузке страницы дуэли: {e}")
        return redirect(url_for('match.matchmaking_page'))


@match_bp.route('/api/duel/<int:match_id>/status')
@login_required
def get_duel_status(match_id):
    try:
        match = Match.query.get_or_404(match_id)
        if current_user.id not in [match.user_id, match.opponent_id]:
            return jsonify({'error': 'Not a participant in this match'}), 403
        finalize_match_if_needed(match)
        db.session.refresh(match)
        opponent_id = match.opponent_id if current_user.id == match.user_id else match.user_id
        opponent_user = db.session.get(User, opponent_id)
        user_result = MatchResult.query.filter_by(match_id=match_id, user_id=current_user.id).first()
        opponent_result = MatchResult.query.filter_by(match_id=match_id, user_id=opponent_id).first()
        response_data = {
            'match_id': match.id, 'result': match.result, 'time_remaining': None,
            'user_rating_change': match.user_rating_change if current_user.id == match.user_id else match.opponent_rating_change,
            'opponent_rating_change': match.opponent_rating_change if current_user.id == match.user_id else match.user_rating_change,
            'participants': {
                'user': {
                    'id': current_user.id, 'username': current_user.username, 'elo': current_user.elo,
                    'has_submitted': user_result is not None,
                    'score': (user_result.score if user_result else 0) or 0,
                    'tests_passed': (user_result.tests_passed if user_result else 0) or 0,
                    'total_tests': (user_result.total_tests if user_result else 0) or 0,
                },
                'opponent': {
                    'id': opponent_user.id, 'username': opponent_user.username, 'elo': opponent_user.elo,
                    'has_submitted': opponent_result is not None,
                    'score': (opponent_result.score if opponent_result else 0) or 0,
                    'tests_passed': (opponent_result.tests_passed if opponent_result else 0) or 0,
                    'total_tests': (opponent_result.total_tests if opponent_result else 0) or 0,
                }
            }
        }
        if hasattr(current_user, 'has_premium') and current_user.has_premium() and opponent_result and opponent_result.attempt_id:
            opp_attempt = db.session.get(Attempt, opponent_result.attempt_id)
            if opp_attempt:
                response_data['opponent_code'] = opp_attempt.code
        if match.result is None and match.started_at:
            started_at = to_utc_aware(match.started_at)
            now_utc = datetime.now(timezone.utc)
            elapsed_time = int((now_utc - started_at).total_seconds()) if started_at else 0
            response_data['time_remaining'] = max(0, duel_max_time - elapsed_time)
        else:
            response_data['time_remaining'] = 0
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
