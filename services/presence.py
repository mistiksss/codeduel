"""Keep ``User.is_online`` / ``last_seen`` in sync with request activity."""

import logging
import threading
import time
from datetime import timedelta

from flask_login import current_user

from constants import (
    LAST_SEEN_UPDATE_SECONDS,
    ONLINE_TIMEOUT_MINUTES,
    PRESENCE_SWEEP_INTERVAL_SECONDS,
)
from extensions import db
from models import User
from utils.utc import utc_now

logger = logging.getLogger(__name__)


def mark_stale_users_offline():
    """Set ``is_online=False`` for users not seen within the timeout window."""
    five_minutes_ago = utc_now() - timedelta(minutes=ONLINE_TIMEOUT_MINUTES)
    User.query.filter(
        User.is_online == True,  # noqa: E712
        User.last_seen < five_minutes_ago,
    ).update({'is_online': False})
    db.session.commit()


def run_presence_loop(app):
    """Background loop used by the development server."""
    while True:
        try:
            with app.app_context():
                mark_stale_users_offline()
        except Exception:
            logger.exception('Failed to refresh online status')
        time.sleep(PRESENCE_SWEEP_INTERVAL_SECONDS)


def start_presence_worker(app):
    """Start the daemon thread that marks idle users offline."""
    thread = threading.Thread(target=run_presence_loop, args=(app,), daemon=True)
    thread.start()
    return thread


def touch_current_user_presence():
    """Update ``last_seen`` at most once every LAST_SEEN_UPDATE_SECONDS."""
    if not current_user.is_authenticated:
        return

    now = utc_now()
    last_seen = current_user.last_seen
    if last_seen is None or last_seen.tzinfo is None:
        current_user.last_seen = now
        current_user.is_online = True
        db.session.commit()
        return

    if (now - last_seen).total_seconds() >= LAST_SEEN_UPDATE_SECONDS:
        current_user.last_seen = now
        current_user.is_online = True
        db.session.commit()
