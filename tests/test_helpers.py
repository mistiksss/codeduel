"""UTC helpers, HTML sanitization, badges and best-attempt picking."""

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from constants import ATTEMPT_STATUS_MESSAGES, UNKNOWN_STATUS_MESSAGE
from services.presence import should_refresh_presence
from services.profile_service import best_attempt_status_by_task, get_user_badges
from services.solution_service import extract_first_error, get_status_message
from utils.html import sanitize_html
from utils.navigation import get_active_page
from utils.utc import to_utc_aware


class UtcHelperTests(unittest.TestCase):
    def test_none_passthrough(self):
        self.assertIsNone(to_utc_aware(None))

    def test_naive_assumed_utc(self):
        naive = datetime(2024, 1, 1, 12, 0, 0)
        aware = to_utc_aware(naive)
        self.assertEqual(aware.tzinfo, timezone.utc)
        self.assertEqual(aware.replace(tzinfo=None), naive)

    def test_aware_unchanged(self):
        aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.assertIs(to_utc_aware(aware), aware)


class HtmlSanitizerTests(unittest.TestCase):
    def test_none_and_empty(self):
        self.assertEqual(str(sanitize_html(None)), '')
        self.assertEqual(str(sanitize_html('   ')), '')

    def test_strips_script_tags(self):
        cleaned = str(sanitize_html('<p>ok</p><script>alert(1)</script>'))
        self.assertIn('<p>ok</p>', cleaned)
        self.assertNotIn('script', cleaned.lower())


class BadgeTests(unittest.TestCase):
    def test_no_wins_no_badges(self):
        user = SimpleNamespace(wins=0, current_streak=0)
        self.assertEqual(get_user_badges(user), [])

    def test_first_blood(self):
        user = SimpleNamespace(wins=1, current_streak=1)
        self.assertEqual(get_user_badges(user), [('Первая кровь', '1 победа')])

    def test_on_fire_requires_streak_greater_than_three(self):
        user = SimpleNamespace(wins=5, current_streak=4)
        badges = get_user_badges(user)
        self.assertEqual(
            badges,
            [('Первая кровь', '1 победа'), ('В огне', 'серия 4 побед')],
        )
        almost = SimpleNamespace(wins=5, current_streak=3)
        self.assertEqual(get_user_badges(almost), [('Первая кровь', '1 победа')])


class BestAttemptTests(unittest.TestCase):
    def test_higher_score_wins(self):
        attempts = [
            SimpleNamespace(
                task_id=1, score=10, status='wrong_answer',
                execution_time=0.1, submitted_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            SimpleNamespace(
                task_id=1, score=20, status='partially_correct',
                execution_time=2.0, submitted_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            ),
        ]
        self.assertEqual(best_attempt_status_by_task(attempts), {1: 'partially_correct'})

    def test_equal_score_prefers_better_status_then_faster_time(self):
        later = datetime(2024, 1, 2, tzinfo=timezone.utc)
        earlier = datetime(2024, 1, 1, tzinfo=timezone.utc)
        attempts = [
            SimpleNamespace(
                task_id=7, score=50, status='accepted',
                execution_time=1.0, submitted_at=later,
            ),
            SimpleNamespace(
                task_id=7, score=50, status='accepted',
                execution_time=0.2, submitted_at=earlier,
            ),
        ]
        self.assertEqual(best_attempt_status_by_task(attempts), {7: 'accepted'})


class PresenceThrottleTests(unittest.TestCase):
    def test_none_always_refreshes(self):
        self.assertTrue(should_refresh_presence(None))

    def test_naive_postgres_timestamp_is_not_refreshed_every_request(self):
        now = datetime(2026, 9, 11, 15, 20, 11, tzinfo=timezone.utc)
        naive = datetime(2026, 9, 11, 15, 20, 10)
        self.assertFalse(should_refresh_presence(naive, now=now, min_interval=15))
        stale = datetime(2026, 9, 11, 15, 19, 50)
        self.assertTrue(should_refresh_presence(stale, now=now, min_interval=15))


class StatusMessageTests(unittest.TestCase):
    def test_known_and_unknown(self):
        self.assertEqual(get_status_message('accepted'), ATTEMPT_STATUS_MESSAGES['accepted'])
        self.assertEqual(get_status_message('nope'), UNKNOWN_STATUS_MESSAGE)

    def test_extract_first_error(self):
        self.assertEqual(extract_first_error({}), '')
        self.assertEqual(
            extract_first_error({'results': [{'error': ''}, {'error': 'boom'}]}),
            'boom',
        )


class ActivePageTests(unittest.TestCase):
    def test_header_mapping(self):
        self.assertEqual(get_active_page('main'), 'main')
        self.assertEqual(get_active_page('tasks'), 'tasks')
        self.assertEqual(get_active_page('profile'), 'profile')
        self.assertEqual(get_active_page('match.matchmaking_page'), 'main')
        self.assertEqual(get_active_page('match.duel_arena'), 'tasks')
        self.assertIsNone(get_active_page('auth.login'))


if __name__ == '__main__':
    unittest.main()
