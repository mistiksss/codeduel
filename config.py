"""Flask configuration loaded from environment variables."""

import os

from sqlalchemy.pool import StaticPool


class Config:
    """Default production/development configuration.

    Environment variable names and fallbacks are unchanged from the
    previous hardcoded setup so existing ``.env`` / systemd files keep working.
    """

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('SQLALCHEMY_DATABASE_URI')
        or 'postgresql://postgres:54321@localhost:5432/code_duel'
    )
    SECRET_KEY = (
        os.environ.get('SECRET_KEY')
        or os.environ.get('FLASK_SECRET_KEY')
        or 'dev-secret-change-in-production'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    CODE_EXECUTION_TIMEOUT = 5
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    REDIS_URL = os.environ.get('REDIS_URL') or 'memory://'


class TestConfig(Config):
    """In-memory SQLite config used by the test suite.

    ``StaticPool`` keeps a single connection so ``:memory:`` tables survive
    across requests inside one test.
    """

    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    }
    WTF_CSRF_ENABLED = False
    REDIS_URL = 'memory://'
