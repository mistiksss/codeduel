"""Application factory for Gunicorn, the Socket.IO runner and local debug."""

import os
import time

from dotenv import load_dotenv

from flask import Flask, g, jsonify, request, render_template
from flask_login import current_user
from flask_socketio import SocketIO

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False

from config import Config
from extensions import bcrypt, db, login_manager
from services.matchmaking_service import MatchmakingSystem
from services.presence import touch_current_user_presence
from services.profile_service import get_user_badges
from sockets import register_socket_handlers
from utils.html import sanitize_html
from utils.navigation import get_active_page

load_dotenv()


def create_app(config_object=None, config_overrides=None):
    """Build the Flask app, Socket.IO server and matchmaking singleton.

    Parameters
    ----------
    config_object:
        A config class (e.g. :class:`config.TestConfig`). Defaults to
        :class:`config.Config`.
    config_overrides:
        Optional dict applied after ``from_object``, used by tests.
    """
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    bcrypt.init_app(app)
    app.bcrypt = bcrypt

    login_manager.init_app(app)

    # Import models so SQLAlchemy registers all tables.
    from models import (  # noqa: F401
        Attempt,
        Match,
        MatchResult,
        MatchmakingQueue,
        Task,
        TestCase,
        User,
    )

    socketio_options = {'cors_allowed_origins': '*'}
    if app.config.get('TESTING'):
        socketio_options['async_mode'] = 'threading'
    socketio = SocketIO(app, **socketio_options)
    app.socketio = socketio
    register_socket_handlers(socketio)

    limiter = None
    if LIMITER_AVAILABLE:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=app.config.get('REDIS_URL') or os.environ.get('REDIS_URL') or 'memory://',
            default_limits=[],
            strategy='fixed-window',
        )

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_template_globals():
        context = {'active_page': get_active_page(request.endpoint if request else None)}
        try:
            if current_user.is_authenticated:
                # Header only needs the id. Avoid finalize+COMMIT on every HTML page.
                from models import Match
                from sqlalchemy import or_
                active_match = (
                    Match.query.filter(
                        or_(Match.user_id == current_user.id, Match.opponent_id == current_user.id),
                        Match.result == None,  # noqa: E711
                    )
                    .order_by(Match.created_at.desc())
                    .first()
                )
                context.update({
                    'active_match': active_match,
                    'active_match_id': (active_match.id if active_match else None),
                    'user_badges': get_user_badges(current_user),
                })
        except Exception as exc:
            app.logger.warning('inject_active_match failed: %s', exc)
        if 'active_match' not in context:
            context.update({
                'active_match': None,
                'active_match_id': None,
                'user_badges': [],
            })
        return context

    app.jinja_env.filters['safe_html'] = sanitize_html

    matchmaking_system = MatchmakingSystem()
    app.matchmaking_system = matchmaking_system

    from routes import register_routes

    register_routes(app, limiter=limiter)

    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()
            from services.bootstrap import seed_if_empty
            seed_if_empty(app)

    @app.errorhandler(429)
    def too_many_requests(_error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Слишком много запросов. Подождите немного.'}), 429
        return render_template('error_429.html'), 429

    @app.before_request
    def update_last_seen():
        g.request_started_at = time.perf_counter()
        touch_current_user_presence()

    @app.after_request
    def log_slow_requests(response):
        started = getattr(g, 'request_started_at', None)
        if started is not None:
            elapsed_ms = (time.perf_counter() - started) * 1000
            if elapsed_ms >= 100:
                app.logger.warning(
                    'slow request %.0fms %s %s',
                    elapsed_ms,
                    request.method,
                    request.path,
                )
        return response

    return app, socketio
