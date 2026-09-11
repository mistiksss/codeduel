"""Elo rating update used when a duel ends.

The formula is the standard FIDE-style expected-score model with K=32.
``result1`` is 1 for a win, 0 for a loss and 0.5 for a draw, from player 1's
point of view.
"""

from constants import ELO_K_FACTOR


def calculate_elo_rating(rating1, rating2, result1):
    """Return ``(new_rating1, new_rating2)`` rounded to integers.

    Parameters
    ----------
    rating1, rating2:
        Current integer ratings.
    result1:
        Score of player 1: ``1``, ``0`` or ``0.5``.
    """
    k_factor = ELO_K_FACTOR
    expected1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    expected2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))
    new_rating1 = rating1 + k_factor * (result1 - expected1)
    new_rating2 = rating2 + k_factor * ((1 - result1) - expected2)
    return round(new_rating1), round(new_rating2)
