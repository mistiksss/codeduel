"""Flask-SocketIO event handlers for realtime match updates."""
from flask_login import current_user
from flask_socketio import join_room, leave_room, disconnect

from extensions import db
from models import Match


def _is_participant(match_id) -> bool:
    """Check if current_user is a participant of the match."""
    if not current_user.is_authenticated:
        return False
    try:
        match = db.session.get(Match, int(match_id))
        if not match:
            return False
        return current_user.id in (match.user_id, match.opponent_id)
    except (ValueError, TypeError):
        return False


def register_socket_handlers(sio):
    """Register Socket.IO event handlers."""

    @sio.on("join")
    def on_join(data):
        """Join a match room by match ID. Auth: only participants allowed."""
        room = data.get("room") if isinstance(data, dict) else data
        if room is None:
            return
        if not _is_participant(room):
            disconnect()
            return
        join_room(str(room))

    @sio.on("leave")
    def on_leave(data):
        """Leave a match room."""
        room = data.get("room") if isinstance(data, dict) else data
        if room is not None:
            leave_room(str(room))

    @sio.on("submit_update")
    def on_submit_update(data):
        """Ignored. Clients must not trigger match updates via socket. Server emits after HTTP submit."""

    @sio.on("typing")
    def on_typing(data):
        """Broadcast typing indicator to others in the room. Auth: only participants allowed."""
        room = data.get("room") if isinstance(data, dict) else data
        if room is None:
            return
        if not _is_participant(room):
            disconnect()
            return
        sio.emit("typing", {"typing": True}, to=str(room), include_self=False)
