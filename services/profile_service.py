"""Profile stats, badges and the per-task best-attempt picker."""

from datetime import datetime, timezone

from sqlalchemy import func, or_

from constants import ATTEMPT_STATUS_PRIORITY, MISSING_EXECUTION_TIME_SENTINEL
from extensions import db
from models import Attempt, Match, MatchResult, User


def get_user_badges(user):
    """Return a list of ``(title, description)`` badge tuples."""
    badges = []
    wins = getattr(user, 'wins', 0) or 0
    streak = getattr(user, 'current_streak', 0) or 0
    if wins >= 1:
        badges.append(('Первая кровь', '1 победа'))
    if streak > 3:
        badges.append(('В огне', f'серия {streak} побед'))
    return badges


def build_profile_context(profile_user, match_limit=5):
    """Gather template context for the profile page.

    ``solved_tasks_single`` counts distinct accepted attempts that are not
    attached to a duel (``MatchResult``), i.e. training solves only.
    """
    user_attempts = Attempt.query.filter_by(user_id=profile_user.id).all()
    total_attempts = len(user_attempts)
    successful_attempts = len([attempt for attempt in user_attempts if attempt.status == 'accepted'])

    solved_tasks_single = db.session.query(func.count(func.distinct(Attempt.task_id))).outerjoin(
        MatchResult, MatchResult.attempt_id == Attempt.id,
    ).filter(
        Attempt.user_id == profile_user.id,
        Attempt.status == 'accepted',
        MatchResult.id == None,  # noqa: E711
    ).scalar() or 0

    matches = Match.query.filter(
        or_(
            Match.user_id == profile_user.id,
            Match.opponent_id == profile_user.id,
        ),
        Match.result != None,  # noqa: E711
    ).order_by(Match.created_at.desc()).limit(match_limit).all()

    opponent_ids = list({
        match.opponent_id if match.user_id == profile_user.id else match.user_id
        for match in matches
    })
    opponents_by_id = {}
    if opponent_ids:
        opponents_by_id = {
            user.id: user
            for user in User.query.filter(User.id.in_(opponent_ids)).all()
        }

    match_history = []
    for match in matches:
        is_user_side = match.user_id == profile_user.id
        opponent_id = match.opponent_id if is_user_side else match.user_id
        opponent = opponents_by_id.get(opponent_id)
        if is_user_side:
            result_for_user = match.result
        elif match.result == 'win':
            result_for_user = 'loss'
        elif match.result == 'loss':
            result_for_user = 'win'
        else:
            result_for_user = 'draw'
        match_history.append({
            'opponent': opponent.username if opponent else '—',
            'result': result_for_user,
            'rating_change': (
                match.user_rating_change if is_user_side else match.opponent_rating_change
            ),
            'date': match.created_at.strftime('%d.%m.%Y %H:%M') if match.created_at else '',
        })

    rank = User.query.filter(User.elo > profile_user.elo).count() + 1
    wins = getattr(profile_user, 'wins', 0) or 0
    losses = getattr(profile_user, 'losses', 0) or 0
    winrate = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0
    current_streak = getattr(profile_user, 'current_streak', 0) or 0

    return {
        'profile_user': profile_user,
        'total_attempts': total_attempts,
        'successful_attempts': successful_attempts,
        'match_history': match_history,
        'solved_tasks_single': solved_tasks_single,
        'badges': get_user_badges(profile_user),
        'rank': rank,
        'winrate': winrate,
        'current_streak': current_streak,
    }


def best_attempt_status_by_task(attempts):
    """Pick each task's best attempt status using score, status, time, date.

    Comparison key (higher wins): ``(score, status_priority, -exec_time,
    submitted_at timestamp)``.
    """
    best_by_task = {}
    for attempt in attempts:
        task_id = attempt.task_id
        current_best = best_by_task.get(task_id)
        score = attempt.score or 0
        priority = ATTEMPT_STATUS_PRIORITY.get(attempt.status, 0)
        execution_time = (
            attempt.execution_time
            if attempt.execution_time is not None
            else MISSING_EXECUTION_TIME_SENTINEL
        )
        submitted_at = attempt.submitted_at or datetime.min.replace(tzinfo=timezone.utc)
        comparison_key = (score, priority, -execution_time, submitted_at.timestamp())
        if current_best is None or comparison_key > current_best['key']:
            best_by_task[task_id] = {'status': attempt.status, 'key': comparison_key}
    return {task_id: value['status'] for task_id, value in best_by_task.items()}
