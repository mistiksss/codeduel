"""Winner-selection rules used when a duel is finalized."""

import unittest

from services.match_service import determine_match_winner


class DetermineMatchWinnerTests(unittest.TestCase):
    def test_only_user_solved_all_is_win(self):
        self.assertEqual(
            determine_match_winner(10, 5, 3, 2, 1.0, 0.1, True, False),
            'win',
        )

    def test_only_opponent_solved_all_is_loss(self):
        self.assertEqual(
            determine_match_winner(10, 5, 3, 2, 0.1, 1.0, False, True),
            'loss',
        )

    def test_both_solved_all_faster_user_wins(self):
        self.assertEqual(
            determine_match_winner(10, 10, 3, 3, 0.4, 0.9, True, True),
            'win',
        )

    def test_both_solved_all_faster_opponent_wins(self):
        self.assertEqual(
            determine_match_winner(10, 10, 3, 3, 0.9, 0.4, True, True),
            'loss',
        )

    def test_both_solved_all_equal_time_is_draw(self):
        self.assertEqual(
            determine_match_winner(10, 10, 3, 3, 0.5, 0.5, True, True),
            'draw',
        )

    def test_neither_solved_all_more_tests_wins(self):
        self.assertEqual(
            determine_match_winner(10, 90, 4, 3, 5.0, 0.1, False, False),
            'win',
        )
        self.assertEqual(
            determine_match_winner(90, 10, 3, 4, 0.1, 5.0, False, False),
            'loss',
        )

    def test_equal_tests_higher_score_wins(self):
        self.assertEqual(
            determine_match_winner(20, 10, 2, 2, 5.0, 0.1, False, False),
            'win',
        )
        self.assertEqual(
            determine_match_winner(10, 20, 2, 2, 0.1, 5.0, False, False),
            'loss',
        )

    def test_equal_tests_and_score_faster_time_wins(self):
        self.assertEqual(
            determine_match_winner(10, 10, 2, 2, 0.2, 0.8, False, False),
            'win',
        )
        self.assertEqual(
            determine_match_winner(10, 10, 2, 2, 0.8, 0.2, False, False),
            'loss',
        )

    def test_complete_tie_is_draw(self):
        self.assertEqual(
            determine_match_winner(10, 10, 2, 2, 1.0, 1.0, False, False),
            'draw',
        )


if __name__ == '__main__':
    unittest.main()
