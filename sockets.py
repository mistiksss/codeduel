"""Socket.IO event handlers for the duel arena."""

from flask_login import current_user
from flask_socketio import disconnect, join_room, leave_room

from extensions import db
from models import Match


def _is_match_participant(match_id) -> bool:
    """Return True if the current user is a player in ``match_id``."""
    if not current_user.is_authenticated:
        return False
    try:
        match = db.session.get(Match, int(match_id))
        if not match:
            return False
        return current_user.id in (match.user_id, match.opponent_id)
    except (ValueError, TypeError):
        return False


def register_socket_handlers(socketio):
    """Attach join/leave/typing handlers to ``socketio``."""

    @socketio.on('join')
    def on_join(data):
        room = data.get('room') if isinstance(data, dict) else data
        if room is None:
            return
        if not _is_match_participant(room):
            disconnect()
            return
        join_room(str(room))

    @socketio.on('leave')
    def on_leave(data):
        room = data.get('room') if isinstance(data, dict) else data
        if room is not None:
            leave_room(str(room))

    @socketio.on('submit_update')
    def on_submit_update(data):
        # Kept for protocol compatibility with the arena client.
        return None

    @socketio.on('typing')
    def on_typing(data):
        room = data.get('room') if isinstance(data, dict) else data
        if room is None:
            return
        if not _is_match_participant(room):
            disconnect()
            return
        socketio.emit('typing', {'typing': True}, to=str(room), include_self=False)
