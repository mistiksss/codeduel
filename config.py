"""Flask configuration loaded from environment variables."""

import os

from sqlalchemy.pool import StaticPool


def _database_uri():
    uri = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('SQLALCHEMY_DATABASE_URI')
        or 'sqlite:///codeduel.db'
    )
    # Render/Heroku still hand out postgres://
    if uri.startswith('postgres://'):
        uri = 'postgresql://' + uri[len('postgres://'):]
    if uri.startswith('postgresql://') and 'sslmode=' not in uri:
        host = uri.split('@')[-1]
        if 'localhost' not in host and '127.0.0.1' not in host:
            uri += ('&' if '?' in uri else '?') + 'sslmode=require'
    return uri


class Config:
    """Production/development config. Secrets come from the environment."""

    SQLALCHEMY_DATABASE_URI = _database_uri()
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
