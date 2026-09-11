"""Access application-scoped objects stored on ``current_app``."""

from flask import current_app


def get_bcrypt():
    """Return the Bcrypt extension bound to the current application."""
    return getattr(current_app, 'bcrypt', None) or current_app.extensions.get('bcrypt')


def get_matchmaking_system():
    """Return the process-wide matchmaking service, if initialised."""
    return getattr(current_app, 'matchmaking_system', None)


def get_socketio():
    """Return the Socket.IO server bound to the current application."""
    return getattr(current_app, 'socketio', None)
