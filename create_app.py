"""Application factory for Gunicorn, the Socket.IO runner and local debug."""

import os

from dotenv import load_dotenv
from flask import Flask, request
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
from services.match_service import get_active_match_for_user
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
                active_match = get_active_match_for_user(current_user.id)
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

    @app.before_request
    def update_last_seen():
        touch_current_user_presence()

    return app, socketio
