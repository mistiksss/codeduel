from flask_login import current_user
from flask_socketio import join_room, leave_room, disconnect

from extensions import db
from models import Match


def _is_participant(match_id) -> bool:
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

    @sio.on("join")
    def on_join(data):
        room = data.get("room") if isinstance(data, dict) else data
        if room is None:
            return
        if not _is_participant(room):
            disconnect()
            return
        join_room(str(room))

    @sio.on("leave")
    def on_leave(data):
        room = data.get("room") if isinstance(data, dict) else data
        if room is not None:
            leave_room(str(room))

    @sio.on("submit_update")
    def on_submit_update(data):
        pass

    @sio.on("typing")
    def on_typing(data):
        room = data.get("room") if isinstance(data, dict) else data
        if room is None:
            return
        if not _is_participant(room):
            disconnect()
            return
        sio.emit("typing", {"typing": True}, to=str(room), include_self=False)