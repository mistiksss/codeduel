"""Application services: judging, matches, matchmaking, profiles."""

from services.elo import calculate_elo_rating
from services.match_service import (
    DUEL_MAX_TIME,
    apply_match_result,
    build_match_response_for_user,
    determine_match_winner,
    finalize_match_if_needed,
    get_active_match_for_user,
    get_task_max_score,
    normalize_match_started_at,
)
from services.matchmaking_service import MatchmakingSystem
from services.scoring import calculate_task_score, normalize_output, validate_solution

__all__ = [
    'DUEL_MAX_TIME',
    'MatchmakingSystem',
    'apply_match_result',
    'build_match_response_for_user',
    'calculate_elo_rating',
    'calculate_task_score',
    'determine_match_winner',
    'finalize_match_if_needed',
    'get_active_match_for_user',
    'get_task_max_score',
    'normalize_match_started_at',
    'normalize_output',
    'validate_solution',
]
