from datetime import datetime, timezone, timedelta

from sqlalchemy import or_

from extensions import db
from models import User, Task, Match, MatchResult

DUEL_MAX_TIME = 7200


def to_utc_aware(dt):
    if dt is None:
        return None
    if getattr(dt, 'tzinfo', None) is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


def normalize_match_started_at(match, now_utc=None):
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

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


def calculate_elo_rating(rating1, rating2, result1):
    K = 32
    expected1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    expected2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))
    new_rating1 = rating1 + K * (result1 - expected1)
    new_rating2 = rating2 + K * ((1 - result1) - expected2)
    return round(new_rating1), round(new_rating2)


def _apply_match_result(match: Match, result: str):
    if match is None or match.result is not None:
        return
    if result not in {'win', 'loss', 'draw'}:
        raise ValueError('Invalid match result')

    now_utc = datetime.now(timezone.utc)
    started_at = normalize_match_started_at(match, now_utc=now_utc)

    user = db.session.get(User, match.user_id)
    opp = db.session.get(User, match.opponent_id)
    if not user or not opp:
        raise RuntimeError('Users not found for match')

    match.result = result

    if result == 'win':
        new_user_elo, new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 1)
        user.wins += 1
        user.current_streak += 1
        opp.losses += 1
        opp.current_streak = 0
    elif result == 'loss':
        new_user_elo, new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 0)
        user.losses += 1
        user.current_streak = 0
        opp.wins += 1
        opp.current_streak += 1
    else:
        new_user_elo, new_opp_elo = calculate_elo_rating(user.elo, opp.elo, 0.5)
        user.draws += 1
        opp.draws += 1
        user.current_streak = 0
        opp.current_streak = 0

    match.user_rating_change = new_user_elo - user.elo
    match.opponent_rating_change = new_opp_elo - opp.elo
    user.elo = new_user_elo
    opp.elo = new_opp_elo

    user.games_played += 1
    opp.games_played += 1

    match.ended_at = now_utc
    ended_at = to_utc_aware(match.ended_at)
    started_at = normalize_match_started_at(match, now_utc=ended_at)
    duration = int((ended_at - started_at).total_seconds()) if started_at and ended_at else 0
    match.match_duration = max(0, duration)

    if user.elo > user.best_elo:
        user.best_elo = user.elo
    if opp.elo > opp.best_elo:
        opp.best_elo = opp.elo

    db.session.commit()


def _build_match_response_for_user(match, user_result, opponent_result, current_user_id, user_info, opponent_info,
                                   include_participants=False, rating_change_opponent_override=None):
    is_user_side = (current_user_id == match.user_id)
    result_for_user = match.result
    if match.result in ['win', 'loss'] and not is_user_side:
        result_for_user = 'win' if match.result == 'loss' else 'loss'
    rating_change_for_user = match.user_rating_change if is_user_side else match.opponent_rating_change
    rating_change_for_opponent = rating_change_opponent_override
    if rating_change_for_opponent is None:
        rating_change_for_opponent = match.opponent_rating_change if is_user_side else match.user_rating_change

    user_score = user_result.score if user_result else 0
    opp_score = opponent_result.score if opponent_result else 0
    user_tests = user_result.tests_passed if user_result else 0
    user_total = user_result.total_tests if user_result else 0
    opp_tests = opponent_result.tests_passed if opponent_result else 0
    opp_total = opponent_result.total_tests if opponent_result else 0
    if not is_user_side:
        user_score, opp_score = opp_score, user_score
        user_tests, opp_tests = opp_tests, user_tests
        user_total, opp_total = opp_total, user_total

    data = {
        'match_id': match.id,
        'result': match.result,
        'result_for_user': result_for_user,
        'task_id': match.task_id,
        'rating_change_for_user': rating_change_for_user,
        'rating_change_for_opponent': rating_change_for_opponent,
        'score_for_user': user_score,
        'score_for_opponent': opp_score,
        'tests_passed_for_user': user_tests,
        'total_tests_for_user': user_total,
        'tests_passed_for_opponent': opp_tests,
        'total_tests_for_opponent': opp_total,
    }
    if include_participants and user_info and opponent_info:
        data['created_at'] = match.created_at.isoformat() if match.created_at else None
        data['user_rating_change'] = match.user_rating_change
        data['opponent_rating_change'] = match.opponent_rating_change
        data['participants'] = {
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
            }
        }
    return data


def get_task_max_score(task_id: int) -> int:
    task = db.session.get(Task, int(task_id))
    return int(task.points or 0) if task else 0


def get_active_match_for_user(user_id: int):
    match = (Match.query.filter(
        or_(Match.user_id == user_id, Match.opponent_id == user_id),
        Match.result == None
    ).order_by(Match.created_at.desc()).first())

    if not match:
        return None

    if not match.started_at:
        match.started_at = to_utc_aware(match.created_at) or datetime.now(timezone.utc)
        db.session.commit()

    finalize_match_if_needed(match)
    db.session.refresh(match)

    return match if match.result is None else None


def _determine_match_winner(
    user_score: int,
    opponent_score: int,
    user_tests_passed: int,
    opponent_tests_passed: int,
    user_exec_time: float,
    opponent_exec_time: float,
    user_solved_all: bool,
    opponent_solved_all: bool,
) -> str | None:
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
    if match is None or match.result is not None:
        return
    now_utc = datetime.now(timezone.utc)
    normalize_match_started_at(match, now_utc=now_utc)
    db.session.commit()

    user_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.user_id).first()
    opponent_result = MatchResult.query.filter_by(match_id=match.id, user_id=match.opponent_id).first()

    user_score = (user_result.score if user_result else 0) or 0
    opponent_score = (opponent_result.score if opponent_result else 0) or 0
    user_tests_passed = (user_result.tests_passed if user_result else 0) or 0
    opponent_tests_passed = (opponent_result.tests_passed if opponent_result else 0) or 0
    user_exec_time = (
        user_result.execution_time if user_result and user_result.execution_time is not None else 10**9
    )
    opponent_exec_time = (
        opponent_result.execution_time if opponent_result and opponent_result.execution_time is not None else 10**9
    )

    user_solved_all = bool(
        user_result and (user_result.total_tests or 0) > 0
        and (user_result.tests_passed or 0) == (user_result.total_tests or 0)
    )
    opponent_solved_all = bool(
        opponent_result and (opponent_result.total_tests or 0) > 0
        and (opponent_result.tests_passed or 0) == (opponent_result.total_tests or 0)
    )

    if user_solved_all or opponent_solved_all:
        match.result = _determine_match_winner(
            user_score, opponent_score,
            user_tests_passed, opponent_tests_passed,
            user_exec_time, opponent_exec_time,
            user_solved_all, opponent_solved_all,
        )

    if match.result is None:
        started_at = normalize_match_started_at(match, now_utc=now_utc)
        elapsed = int((now_utc - started_at).total_seconds()) if started_at else 0
        if elapsed >= DUEL_MAX_TIME:
            match.result = _determine_match_winner(
                user_score, opponent_score,
                user_tests_passed, opponent_tests_passed,
                user_exec_time, opponent_exec_time,
                user_solved_all, opponent_solved_all,
            )

    if match.result is None:
        return

    _apply_match_result(match, match.result)