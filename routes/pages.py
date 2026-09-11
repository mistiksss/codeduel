"""Public HTML pages: home, about, tasks, profile, leaderboard."""

from datetime import timedelta

from flask import jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import desc, or_

from constants import (
    ACTIVE_MATCH_TTL_MINUTES,
    ATTEMPT_STATUS_LABELS,
    LEADERBOARD_SIZE,
    PROFILE_MATCH_HISTORY_LIMIT,
)
from extensions import db
from models import Attempt, Match, Task, User
from services.profile_service import (
    best_attempt_status_by_task,
    build_profile_context,
)
from utils.utc import utc_now


def register_page_routes(app):
    """Register template views on ``app`` (endpoint names stay unprefixed)."""

    @app.route('/')
    def main():
        return render_template('main.html')

    @app.route('/main')
    def main_page():
        return render_template('main_reg.html')

    @app.route('/main_reg')
    def main_reg():
        return redirect(url_for('main_page'))

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/about_reg')
    def about_reg():
        return render_template('about_reg.html')

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if current_user.elo > current_user.best_elo:
            current_user.best_elo = current_user.elo
            db.session.commit()

        context = build_profile_context(current_user, match_limit=PROFILE_MATCH_HISTORY_LIMIT)
        context['is_own_profile'] = True
        return render_template('profile.html', **context)

    @app.route('/user/<username>')
    def user_public_profile(username):
        profile_user = User.query.filter_by(username=username).first_or_404()
        context = build_profile_context(profile_user, match_limit=PROFILE_MATCH_HISTORY_LIMIT)
        context['is_own_profile'] = (
            current_user.is_authenticated and current_user.id == profile_user.id
        )
        return render_template('profile.html', **context)

    @app.route('/tasks')
    @login_required
    def tasks():
        all_tasks = Task.query.all()
        attempts = Attempt.query.filter_by(user_id=current_user.id).all()
        best_status_by_task = best_attempt_status_by_task(attempts)
        return render_template(
            'tasks.html',
            tasks=all_tasks,
            best_status_by_task=best_status_by_task,
            status_label=ATTEMPT_STATUS_LABELS,
        )

    @app.route('/task/<int:task_id>')
    @login_required
    def task_detail(task_id):
        task = Task.query.get_or_404(task_id)
        active_ttl = utc_now() - timedelta(minutes=ACTIVE_MATCH_TTL_MINUTES)
        active_match = Match.query.filter(
            Match.task_id == task_id,
            or_(
                Match.user_id == current_user.id,
                Match.opponent_id == current_user.id,
            ),
            Match.result == None,  # noqa: E711
            Match.created_at >= active_ttl,
        ).order_by(Match.created_at.desc()).first()

        opponent = None
        if active_match:
            opponent_id = (
                active_match.opponent_id
                if current_user.id == active_match.user_id
                else active_match.user_id
            )
            opponent = db.session.get(User, opponent_id)

        return render_template(
            'arena.html',
            task=task,
            match=active_match,
            active_match=active_match,
            opponent=opponent,
        )

    @app.route('/leaderboard')
    def leaderboard():
        leaders = _load_leaders()
        return render_template('leaderboard.html', leaders=leaders, current_user=current_user)

    @app.route('/api/leaderboard')
    def api_leaderboard():
        leaders = _load_leaders()
        leaderboard_data = []
        for rank, user in enumerate(leaders, 1):
            leaderboard_data.append({
                'id': user.id,
                'username': user.username,
                'elo': user.elo,
                'rank': rank,
                'is_current_user': current_user.is_authenticated and user.id == current_user.id,
            })
        return jsonify({'leaders': leaderboard_data})


def _load_leaders():
    """Top players by Elo, with a transient ``rank`` attribute for templates."""
    leaders = User.query.order_by(desc(User.elo)).limit(LEADERBOARD_SIZE).all()
    for rank, user in enumerate(leaders, 1):
        user.rank = rank
    return leaders
