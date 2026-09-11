"""Matchmaking queue HTTP API."""

import logging
from datetime import timedelta

from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from constants import ONLINE_TIMEOUT_MINUTES
from extensions import db
from models import MatchmakingQueue, User
from routes.match.blueprint import match_bp
from routes.match.serializers import load_opponent_and_task, serialize_match_found
from services.match_service import get_active_match_for_user
from utils.extensions_access import get_matchmaking_system
from utils.utc import utc_now

logger = logging.getLogger(__name__)


@match_bp.route('/play-with-bot')
@login_required
def play_with_bot():
    """Training shortcut: leave the queue and open the task list."""
    matchmaking = get_matchmaking_system()
    if matchmaking:
        matchmaking.cancel_search(current_user.id)
        db.session.commit()
    return redirect(url_for('tasks'))


@match_bp.route('/matchmaking')
@login_required
def matchmaking_page():
    """Matchmaking lobby. Completes onboarding on first visit."""
    if not getattr(current_user, 'onboarding_completed', False):
        current_user.onboarding_completed = True
        db.session.commit()
    return render_template('matchmaking.html')


@match_bp.route('/api/matchmaking/start', methods=['POST'])
@login_required
def start_matchmaking():
    """Join the queue or immediately return an already-active match."""
    try:
        matchmaking = get_matchmaking_system()
        if not matchmaking:
            return jsonify({'success': False, 'error': 'Matchmaking unavailable'}), 500
        payload = request.get_json() or {}
        difficulty = payload.get('difficulty', 'any')
        logger.info(
            '/api/matchmaking/start -> current_user=%s (%s), ELO=%s, difficulty=%s',
            current_user.id,
            current_user.username,
            current_user.elo,
            difficulty,
        )
        active_match = get_active_match_for_user(current_user.id)
        if active_match:
            opponent, task = load_opponent_and_task(active_match, current_user.id)
            response = {
                'success': True,
                'match_found': True,
                **serialize_match_found(active_match, opponent, task),
                'difficulty': difficulty,
                'message': 'У вас уже есть активный матч',
            }
            return jsonify(response)

        result = matchmaking.find_opponent(
            user_id=current_user.id,
            user_elo=current_user.elo,
            difficulty=difficulty,
        )
        result['match_found'] = bool(result.get('match_id'))
        return jsonify(result)
    except Exception as exc:
        logger.exception('Failed to start matchmaking')
        return jsonify({'success': False, 'error': str(exc)}), 500


@match_bp.route('/api/matchmaking/queue_count', methods=['GET'])
def get_matchmaking_queue_count():
    """How many online players are currently searching."""
    try:
        five_minutes_ago = utc_now() - timedelta(minutes=ONLINE_TIMEOUT_MINUTES)
        count = (
            MatchmakingQueue.query.filter(MatchmakingQueue.status == 'searching')
            .join(User, MatchmakingQueue.user_id == User.id)
            .filter(or_(User.is_online == True, User.last_seen >= five_minutes_ago))  # noqa: E712
            .count()
        )
        return jsonify({'count': count})
    except Exception as exc:
        return jsonify({'count': 0, 'error': str(exc)})


@match_bp.route('/api/matchmaking/cancel', methods=['POST'])
@login_required
def cancel_matchmaking():
    """Leave the matchmaking queue. Does not delete an already-created match."""
    try:
        get_matchmaking_system().cancel_search(current_user.id)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Поиск отменен'})
    except Exception:
        db.session.rollback()
        logger.exception('Failed to cancel matchmaking')
        return jsonify({'success': False, 'error': 'Не удалось отменить поиск'}), 500


@match_bp.route('/api/matchmaking/status', methods=['GET'])
@login_required
def get_matchmaking_status():
    """Queue membership plus any active match for the current user."""
    try:
        in_queue = (
            MatchmakingQueue.query.filter_by(
                user_id=current_user.id,
                status='searching',
            ).first() is not None
        )
        queue_stats = (
            get_matchmaking_system().get_queue_stats(current_user.id) if in_queue else {}
        )
        match = get_active_match_for_user(current_user.id)
        response_data = {
            'in_queue': in_queue,
            'queue_stats': queue_stats,
            'match_found': match is not None,
        }
        if match:
            opponent, task = load_opponent_and_task(match, current_user.id)
            response_data.update(serialize_match_found(match, opponent, task))
        return jsonify(response_data)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@match_bp.route('/api/matchmaking/poll', methods=['GET'])
@login_required
def poll_matchmaking():
    """Heartbeat used by the lobby while waiting for an opponent."""
    try:
        in_queue = (
            MatchmakingQueue.query.filter_by(
                user_id=current_user.id,
                status='searching',
            ).first() is not None
        )
        ping_ok = get_matchmaking_system().ping_queue(current_user.id) if in_queue else False
        match = get_active_match_for_user(current_user.id)
        if match:
            opponent, task = load_opponent_and_task(match, current_user.id)
            return jsonify({
                'match_found': True,
                **serialize_match_found(match, opponent, task),
            })
        queue_stats = (
            get_matchmaking_system().get_queue_stats(current_user.id)
            if in_queue
            else {'total_players': 0}
        )
        return jsonify({
            'match_found': False,
            'still_searching': bool(in_queue),
            'in_queue': bool(in_queue),
            'ping_ok': bool(ping_ok),
            'queue_stats': queue_stats,
            'message': (
                'Ожидание соперника...'
                if in_queue
                else 'Вы не в очереди. Нажмите Start для нового поиска.'
            ),
        })
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@match_bp.route('/api/matchmaking/ping', methods=['POST'])
@login_required
def ping_matchmaking():
    """Keep the queue entry alive while the lobby tab is open."""
    try:
        success = get_matchmaking_system().ping_queue(current_user.id)
        if success:
            return jsonify({'success': True, 'message': 'Ping updated'})
        return jsonify({'success': False, 'error': 'Not in queue'})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@match_bp.route('/api/online_players')
def online_players():
    """Online users and how many of them are currently searching."""
    try:
        five_minutes_ago = utc_now() - timedelta(minutes=ONLINE_TIMEOUT_MINUTES)
        total_online = User.query.filter(
            or_(User.is_online == True, User.last_seen >= five_minutes_ago),  # noqa: E712
        ).count()
        total_in_queue = MatchmakingQueue.query.filter_by(status='searching').count()
        return jsonify({
            'total_online': total_online,
            'total_in_queue': total_in_queue,
        })
    except Exception:
        logger.exception('Failed to load online players')
        return jsonify({'total_online': 0, 'total_in_queue': 0}), 500
