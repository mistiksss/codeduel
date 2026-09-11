"""Helpers for submitting and serializing judged solutions."""

from constants import ATTEMPT_STATUS_MESSAGES, CODE_PREVIEW_LENGTH, UNKNOWN_STATUS_MESSAGE
from extensions import db
from models import MatchResult
from utils.utc import utc_now


def get_status_message(status):
    """User-facing Russian label for an attempt status."""
    return ATTEMPT_STATUS_MESSAGES.get(status, UNKNOWN_STATUS_MESSAGE)


def extract_first_error(validation: dict) -> str:
    """Return the first per-test error string from a judge result dict."""
    for result in (validation.get('results') or []):
        if result.get('error'):
            return str(result['error'])
    return ''


def upsert_match_result(match, user_id: int, attempt) -> None:
    """Create or replace this player's ``MatchResult`` with ``attempt``."""
    match_result = MatchResult.query.filter_by(match_id=match.id, user_id=user_id).first()
    now_utc = utc_now()
    if match_result:
        match_result.attempt_id = attempt.id
        match_result.score = attempt.score or 0
        match_result.tests_passed = attempt.tests_passed or 0
        match_result.total_tests = attempt.total_tests or 0
        match_result.execution_time = attempt.execution_time
        match_result.submitted_at = now_utc
        return

    match_result = MatchResult(
        match_id=match.id,
        user_id=user_id,
        attempt_id=attempt.id,
        score=attempt.score or 0,
        tests_passed=attempt.tests_passed or 0,
        total_tests=attempt.total_tests or 0,
        execution_time=attempt.execution_time,
        submitted_at=now_utc,
    )
    db.session.add(match_result)


def serialize_attempt(attempt, *, include_code_preview=False):
    """JSON representation of an Attempt used by the attempts API."""
    payload = {
        'id': attempt.id,
        'user_id': attempt.user_id,
        'task_id': attempt.task_id,
        'language': attempt.language,
        'status': attempt.status,
        'execution_time': round(attempt.execution_time, 3) if attempt.execution_time else None,
        'tests_passed': attempt.tests_passed,
        'total_tests': attempt.total_tests,
        'score': attempt.score,
        'error_message': attempt.error_message,
        'submitted_at': (
            attempt.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.submitted_at else None
        ),
    }
    if include_code_preview:
        code = attempt.code or ''
        payload['code'] = (
            code[:CODE_PREVIEW_LENGTH] + '...' if len(code) > CODE_PREVIEW_LENGTH else code
        )
    return payload


def get_match_broadcast_payload(match) -> dict:
    """Minimal Socket.IO payload; the client re-fetches full match status."""
    return {'match_id': match.id}
