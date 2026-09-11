"""UTC datetime helpers.

PostgreSQL may return naive timestamps depending on the driver/column type.
Match timing logic always compares timezone-aware UTC datetimes.
"""

from datetime import datetime, timezone


def to_utc_aware(dt):
    """Return ``dt`` as a timezone-aware UTC datetime, or ``None``.

    Naive values are assumed to already be UTC (the historical behaviour
    of this codebase). Aware values are returned unchanged.
    """
    if dt is None:
        return None
    if getattr(dt, 'tzinfo', None) is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


def utc_now():
    """Current time in UTC."""
    return datetime.now(timezone.utc)
