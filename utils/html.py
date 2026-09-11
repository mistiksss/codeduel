"""HTML sanitization for user-facing rich text (task statements)."""

import bleach
from markupsafe import Markup

from constants import ALLOWED_HTML_TAGS


def sanitize_html(text):
    """Return a Markup-safe HTML snippet with only allowed tags.

    Empty / missing input becomes an empty Markup string so Jinja can
    render task descriptions without extra ``None`` checks.
    """
    if text is None:
        return Markup('')
    raw = str(text).strip()
    if not raw:
        return Markup('')
    cleaned = bleach.clean(raw, tags=ALLOWED_HTML_TAGS, strip=True)
    return Markup(cleaned)
