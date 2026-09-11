"""Characterization tests for Elo and task scoring formulas."""

import math
import unittest

from services.elo import calculate_elo_rating
from services.scoring import calculate_task_score, normalize_output


class EloRatingTests(unittest.TestCase):
    def test_equal_ratings_decisive_game(self):
        winner_elo, loser_elo = calculate_elo_rating(1000, 1000, 1)
        self.assertEqual(winner_elo, 1016)
        self.assertEqual(loser_elo, 984)

    def test_equal_ratings_draw(self):
        first_elo, second_elo = calculate_elo_rating(1000, 1000, 0.5)
        self.assertEqual(first_elo, 1000)
        self.assertEqual(second_elo, 1000)

    def test_equal_ratings_loss_is_symmetric(self):
        first_elo, second_elo = calculate_elo_rating(1000, 1000, 0)
        self.assertEqual(first_elo, 984)
        self.assertEqual(second_elo, 1016)

    def test_favorite_beats_underdog_gains_less_than_32(self):
        winner_elo, loser_elo = calculate_elo_rating(1400, 1000, 1)
        self.assertGreater(winner_elo, 1400)
        self.assertLess(winner_elo, 1400 + 16)
        self.assertLess(loser_elo, 1000)
        self.assertEqual(winner_elo + loser_elo, 1400 + 1000)


class NormalizeOutputTests(unittest.TestCase):
    def test_none_becomes_empty(self):
        self.assertEqual(normalize_output(None), '')

    def test_strips_and_normalizes_newlines(self):
        self.assertEqual(normalize_output('  a\r\nb\r\n  '), 'a\nb')


class TaskScoreTests(unittest.TestCase):
    def test_zero_points_or_tests_returns_zeros(self):
        self.assertEqual(
            calculate_task_score(0, 1, 1, is_first_try=True, avg_execution_time=0.1, time_limit=1),
            {'base': 0, 'bonus': 0, 'total': 0},
        )
        self.assertEqual(
            calculate_task_score(10, 1, 0, is_first_try=True, avg_execution_time=0.1, time_limit=1),
            {'base': 0, 'bonus': 0, 'total': 0},
        )

    def test_no_tests_passed_has_zero_base_and_bonus(self):
        result = calculate_task_score(
            100, 0, 10, is_first_try=True, avg_execution_time=0.01, time_limit=1,
        )
        self.assertEqual(result, {'base': 0, 'bonus': 0, 'total': 0})

    def test_full_solve_first_try_fast_is_capped_at_task_points(self):
        result = calculate_task_score(
            100, 10, 10, is_first_try=True, avg_execution_time=0.1, time_limit=1,
        )
        self.assertEqual(result['base'], 100)
        self.assertEqual(result['bonus'], math.ceil(100 * 0.10) + math.ceil(100 * 0.08 * 1.0))
        self.assertEqual(result['total'], 100)

    def test_partial_solve_cannot_reach_full_points(self):
        result = calculate_task_score(
            100, 9, 10, is_first_try=True, avg_execution_time=0.1, time_limit=1,
        )
        self.assertEqual(result['base'], math.ceil(100 * 0.9))
        self.assertLess(result['total'], 100)
        self.assertLessEqual(result['total'], 99)

    def test_speed_bonus_tiers(self):
        slow = calculate_task_score(
            100, 10, 10, is_first_try=False, avg_execution_time=0.95, time_limit=1,
        )
        mid = calculate_task_score(
            100, 10, 10, is_first_try=False, avg_execution_time=0.5, time_limit=1,
        )
        fast = calculate_task_score(
            100, 10, 10, is_first_try=False, avg_execution_time=0.2, time_limit=1,
        )
        self.assertEqual(slow['bonus'], 0)
        self.assertEqual(mid['bonus'], math.ceil(100 * 0.08 * 0.5))
        self.assertEqual(fast['bonus'], math.ceil(100 * 0.08 * 1.0))

    def test_second_try_has_no_first_try_bonus(self):
        first = calculate_task_score(
            50, 5, 5, is_first_try=True, avg_execution_time=10, time_limit=1,
        )
        second = calculate_task_score(
            50, 5, 5, is_first_try=False, avg_execution_time=10, time_limit=1,
        )
        self.assertGreater(first['bonus'], second['bonus'])
        self.assertEqual(second['bonus'], 0)


if __name__ == '__main__':
    unittest.main()
