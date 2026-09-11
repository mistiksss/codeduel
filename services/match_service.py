"""Match lifecycle: timing, winner selection, Elo application, API payloads."""

from datetime import timedelta

from sqlalchemy import or_

from constants import DUEL_MAX_TIME_SECONDS, MISSING_EXECUTION_TIME_SENTINEL
from extensions import db
from models import Match, MatchResult, Task, User
from services.elo import calculate_elo_rating
from utils.utc import to_utc_aware, utc_now

DUEL_MAX_TIME = DUEL_MAX_TIME_SECONDS


def normalize_match_started_at(match, now_utc=None):
    """Ensure ``match.started_at`` is a sane timezone-aware UTC datetime.

    Missing ``started_at`` falls back to ``created_at`` (or ``now``).
    Values more than 60 seconds in the future are clamped to ``created_at``.
    """
    if now_utc is None:
        now_utc = utc_now()

    if not getattr(match, 'started_at', None):
        match.started_at = to_utc_aware(getattr(match, 'created_at', None)) or now_utc
        return match.started_at

    started_at = to_utc_aware(match.started_at)
    if started_at > (now_utc + timedelta(seconds=60)):
        fallback = to_utc_aware(getattr(match, 'created_at', None)) or now_utc
        started_at = min(started_at, fallback)

    if started_at != match.started_at:
        match.started_at = started_at

    return started_at


def apply_match_result(match: Match, result: str):
    """Persist the match outcome and update both players' ratings/stats.

    ``result`` is from the ``match.user_id`` player's point of view
    (``win`` / ``loss`` / ``draw``). Already-finalized matches are ignored.
    """
    if match is None or match.result is not None:
        return
    if result not in {'win', 'loss', 'draw'}:
        raise ValueError('Invalid match result')

    now_utc = utc_now()
    started_at = normalize_match_started_at(match, now_utc=now_utc)

    user = db.session.get(User, match.user_id)
    opponent = db.session.get(User, match.opponent_id)
    if not user or not opponent:
        raise RuntimeError('Users not found for match')

    match.result = result

    if result == 'win':
        new_user_elo, new_opponent_elo = calculate_elo_rating(user.elo, opponent.elo, 1)
        user.wins += 1
        user.current_streak += 1
        opponent.losses += 1
        opponent.current_streak = 0
    elif result == 'loss':
        new_user_elo, new_opponent_elo = calculate_elo_rating(user.elo, opponent.elo, 0)
        user.losses += 1
        user.current_streak = 0
        opponent.wins += 1
        opponent.current_streak += 1
    else:
        new_user_elo, new_opponent_elo = calculate_elo_rating(user.elo, opponent.elo, 0.5)
        user.draws += 1
        opponent.draws += 1
        user.current_streak = 0
        opponent.current_streak = 0

    match.user_rating_change = new_user_elo - user.elo
    match.opponent_rating_change = new_opponent_elo - opponent.elo
    user.elo = new_user_elo
    opponent.elo = new_opponent_elo

    user.games_played += 1
    opponent.games_played += 1

    match.ended_at = now_utc
    ended_at = to_utc_aware(match.ended_at)
    started_at = normalize_match_started_at(match, now_utc=ended_at)
    duration = int((ended_at - started_at).total_seconds()) if started_at and ended_at else 0
    match.match_duration = max(0, duration)

    if user.elo > user.best_elo:
        user.best_elo = user.elo
    if opponent.elo > opponent.best_elo:
        opponent.best_elo = opponent.elo

    db.session.commit()


def build_match_response_for_user(
    match,
    user_result,
    opponent_result,
    current_user_id,
    user_info,
    opponent_info,
    include_participants=False,
    rating_change_opponent_override=None,
):
    """Build the JSON payload used by match-status API endpoints.

    Scores and rating changes are rotated so they are always from
    ``current_user_id``'s point of view, except ``include_participants``
    which keeps the stored ``user`` / ``opponent`` sides of the Match row.
    """
    is_user_side = (current_user_id == match.user_id)
    result_for_user = match.result
    if match.result in ['win', 'loss'] and not is_user_side:
        result_for_user = 'win' if match.result == 'loss' else 'loss'
    rating_change_for_user = match.user_rating_change if is_user_side else match.opponent_rating_change
    rating_change_for_opponent = rating_change_opponent_override
    if rating_change_for_opponent is None:
        rating_change_for_opponent = (
            match.opponent_rating_change if is_user_side else match.user_rating_change
        )

    user_score = user_result.score if user_result else 0
    opponent_score = opponent_result.score if opponent_result else 0
    user_tests = user_result.tests_passed if user_result else 0
    user_total = user_result.total_tests if user_result else 0
    opponent_tests = opponent_result.tests_passed if opponent_result else 0
    opponent_total = opponent_result.total_tests if opponent_result else 0
    if not is_user_side:
        user_score, opponent_score = opponent_score, user_score
        user_tests, opponent_tests = opponent_tests, user_tests
        user_total, opponent_total = opponent_total, user_total

    payload = {
        'match_id': match.id,
        'result': match.result,
        'result_for_user': result_for_user,
        'task_id': match.task_id,
        'rating_change_for_user': rating_change_for_user,
        'rating_change_for_opponent': rating_change_for_opponent,
        'score_for_user': user_score,
        'score_for_opponent': opponent_score,
        'tests_passed_for_user': user_tests,
        'total_tests_for_user': user_total,
        'tests_passed_for_opponent': opponent_tests,
        'total_tests_for_opponent': opponent_total,
    }
    if include_participants and user_info and opponent_info:
        payload['created_at'] = match.created_at.isoformat() if match.created_at else None
        payload['user_rating_change'] = match.user_rating_change
        payload['opponent_rating_change'] = match.opponent_rating_change
        payload['participants'] = {
            'user': {
                'id': user_info.id,
                'username': user_info.username,
                'elo': user_info.elo,
                'has_submitted': user_result is not None,
                'score': user_result.score if user_result else 0,
                'tests_passed': user_result.tests_passed if user_result else 0,
                'total_tests': user_result.total_tests if user_result else 0,
            },
            'opponent': {
                'id': opponent_info.id,
                'username': opponent_info.username,
                'elo': opponent_info.elo,
                'has_submitted': opponent_result is not None,
                'score': opponent_result.score if opponent_result else 0,
                'tests_passed': opponent_result.tests_passed if opponent_result else 0,
                'total_tests': opponent_result.total_tests if opponent_result else 0,
            },
        }
    return payload


def get_task_max_score(task_id: int) -> int:
    """Return the task's ``points`` value, or 0 if the task is missing."""
    task = db.session.get(Task, int(task_id))
    return int(task.points or 0) if task else 0


def get_active_match_for_user(user_id: int):
    """Return the user's latest unfinished match, or ``None``.

    Side effect: missing ``started_at`` is filled in, and expired / fully
    solved matches are finalized before the check.
    """
    match = (
        Match.query.filter(
            or_(Match.user_id == user_id, Match.opponent_id == user_id),
            Match.result == None,  # noqa: E711 — SQL NULL comparison
        )
        .order_by(Match.created_at.desc())
        .first()
    )

    if not match:
        return None

    if not match.started_at:
        match.started_at = to_utc_aware(match.created_at) or utc_now()
        db.session.commit()

    finalize_match_if_needed(match)
    db.session.refresh(match)

    return match if match.result is None else None


def determine_match_winner(
    user_score: int,
    opponent_score: int,
    user_tests_passed: int,
    opponent_tests_passed: int,
    user_exec_time: float,
    opponent_exec_time: float,
    user_solved_all: bool,
    opponent_solved_all: bool,
) -> str | None:
    """Decide the stored ``Match.result`` from the ``user_id`` side.

    Priority: full solve (then faster time) → more tests passed → higher
    score → faster time → draw.
    """
    if user_solved_all or opponent_solved_all:
        if user_solved_all and not opponent_solved_all:
            return 'win'
        if opponent_solved_all and not user_solved_all:
            return 'loss'
        if user_exec_time < opponent_exec_time:
            return 'win'
        if opponent_exec_time < user_exec_time:
            return 'loss'
        return 'draw'
    if user_tests_passed > opponent_tests_passed:
        return 'win'
    if opponent_tests_passed > user_tests_passed:
        return 'loss'
    if user_score > opponent_score:
        return 'win'
    if opponent_score > user_score:
        return 'loss'
    if user_exec_time < opponent_exec_time:
        return 'win'
    if opponent_exec_time < user_exec_time:
        return 'loss'
    return 'draw'


def finalize_match_if_needed(match: Match):
    """Close the match when someone fully solved it or the timer expired.

    Winner detection is delegated to :func:`determine_match_winner`. The
    outcome is then applied through :func:`apply_match_result` so Elo and
    statistics are persisted in the same transaction as ``match.result``.
    """
    if match is None or match.result is not None:
        return
    now_utc = utc_now()
    started_at_before = match.started_at
    normalize_match_started_at(match, now_utc=now_utc)
    if match.started_at != started_at_before:
        db.session.commit()

    user_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.user_id).first()
    opponent_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.opponent_id).first()

    user_score = (user_result.score if user_result else 0) or 0
    opponent_score = (opponent_result.score if opponent_result else 0) or 0
    user_tests_passed = (user_result.tests_passed if user_result else 0) or 0
    opponent_tests_passed = (opponent_result.tests_passed if opponent_result else 0) or 0
    user_exec_time = (
        user_result.execution_time
        if user_result and user_result.execution_time is not None
        else MISSING_EXECUTION_TIME_SENTINEL
    )
    opponent_exec_time = (
        opponent_result.execution_time
        if opponent_result and opponent_result.execution_time is not None
        else MISSING_EXECUTION_TIME_SENTINEL
    )

    user_solved_all = bool(
        user_result and (user_result.total_tests or 0) > 0
        and (user_result.tests_passed or 0) == (user_result.total_tests or 0)
    )
    opponent_solved_all = bool(
        opponent_result and (opponent_result.total_tests or 0) > 0
        and (opponent_result.tests_passed or 0) == (opponent_result.total_tests or 0)
    )

    outcome = None
    if user_solved_all or opponent_solved_all:
        outcome = determine_match_winner(
            user_score, opponent_score,
            user_tests_passed, opponent_tests_passed,
            user_exec_time, opponent_exec_time,
            user_solved_all, opponent_solved_all,
        )

    if outcome is None:
        started_at = normalize_match_started_at(match, now_utc=now_utc)
        elapsed = int((now_utc - started_at).total_seconds()) if started_at else 0
        if elapsed >= DUEL_MAX_TIME:
            outcome = determine_match_winner(
                user_score, opponent_score,
                user_tests_passed, opponent_tests_passed,
                user_exec_time, opponent_exec_time,
                user_solved_all, opponent_solved_all,
            )

    if outcome is None:
        return

    apply_match_result(match, outcome)


# Backward-compatible aliases for any leftover private-name imports.
_apply_match_result = apply_match_result
_build_match_response_for_user = build_match_response_for_user
_determine_match_winner = determine_match_winner
