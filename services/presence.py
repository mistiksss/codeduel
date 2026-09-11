"""Keep ``User.is_online`` / ``last_seen`` in sync with request activity."""

import logging
import threading
import time
from datetime import timedelta, timezone

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


def should_refresh_presence(last_seen, now=None, min_interval=LAST_SEEN_UPDATE_SECONDS):
    """Return True when last_seen is missing or older than the throttle window.

    PostgreSQL ``timestamp without time zone`` comes back as a naive datetime.
    Treat naive values as UTC so we do not COMMIT on every request.
    """
    if last_seen is None:
        return True
    now = now or utc_now()
    aware_last_seen = last_seen if last_seen.tzinfo else last_seen.replace(tzinfo=timezone.utc)
    try:
        return (now - aware_last_seen).total_seconds() >= min_interval
    except TypeError:
        return True


def touch_current_user_presence():
    """Update ``last_seen`` at most once every LAST_SEEN_UPDATE_SECONDS."""
    if not current_user.is_authenticated:
        return

    now = utc_now()
    if not should_refresh_presence(current_user.last_seen, now=now):
        return

    current_user.last_seen = now
    current_user.is_online = True
    db.session.commit()
