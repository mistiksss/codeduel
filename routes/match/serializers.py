"""JSON snippets reused by matchmaking and duel endpoints."""

from extensions import db
from models import Task, User


def serialize_user_brief(user):
    """Public identity fields used in matchmaking / arena payloads."""
    return {
        'id': user.id,
        'username': user.username,
        'elo': user.elo,
    }


def opponent_id_for(match, user_id):
    """Return the other participant's id."""
    return match.opponent_id if user_id == match.user_id else match.user_id


def load_opponent_and_task(match, user_id):
    """Load the opponent User and Task for ``match`` from the current user's side."""
    opponent = db.session.get(User, opponent_id_for(match, user_id))
    task = db.session.get(Task, match.task_id)
    return opponent, task


def serialize_match_found(match, opponent, task):
    """Common ``match_found`` fields returned by start/status/poll."""
    return {
        'match_id': match.id,
        'opponent': serialize_user_brief(opponent),
        'task_id': match.task_id,
        'task_title': task.title if task else 'Unknown Task',
    }
