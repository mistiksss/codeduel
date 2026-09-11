"""Application factory, route map, model schema and DB-backed flows."""

import unittest

from constants import DUEL_MAX_TIME_SECONDS
from extensions import db
from models import Attempt, Match, MatchmakingQueue, MatchResult, Task, TestCase, User
from services.match_service import apply_match_result, finalize_match_if_needed
from services.scoring import validate_solution
from tests.helpers import create_task, create_user, login, make_app
from utils.utc import utc_now


EXPECTED_ENDPOINTS = {
    'main': '/',
    'main_page': '/main',
    'main_reg': '/main_reg',
    'about': '/about',
    'about_reg': '/about_reg',
    'profile': '/profile',
    'user_public_profile': '/user/<username>',
    'tasks': '/tasks',
    'task_detail': '/task/<int:task_id>',
    'leaderboard': '/leaderboard',
    'api_leaderboard': '/api/leaderboard',
    'get_task_attempts': '/api/tasks/<int:task_id>/attempts',
    'submit_solution': '/api/solutions/submit',
    'run_code_api': '/api/run',
    'get_attempt_result': '/api/attempts/<int:attempt_id>/result',
    'get_sample_test': '/api/tasks/<int:task_id>/sample_test',
    'health_check': '/health',
    'auth.login': '/login',
    'auth.register': '/register',
    'auth.onboarding': '/onboarding',
    'auth.logout': '/logout',
    'match.play_with_bot': '/play-with-bot',
    'match.matchmaking_page': '/matchmaking',
    'match.start_matchmaking': '/api/matchmaking/start',
    'match.get_matchmaking_queue_count': '/api/matchmaking/queue_count',
    'match.cancel_matchmaking': '/api/matchmaking/cancel',
    'match.get_matchmaking_status': '/api/matchmaking/status',
    'match.poll_matchmaking': '/api/matchmaking/poll',
    'match.ping_matchmaking': '/api/matchmaking/ping',
    'match.get_match_status': '/api/match/<int:match_id>/status',
    'match.get_opponent_info': '/api/match/<int:match_id>/opponent_info',
    'match.get_active_match': '/api/match/active',
    'match.forfeit_active_match': '/api/match/forfeit',
    'match.get_match_history': '/api/match/history',
    'match.duel_arena': '/duel/<int:match_id>',
    'match.get_duel_status': '/api/duel/<int:match_id>/status',
}


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()


class RouteMapTests(DatabaseTestCase):
    def test_all_legacy_endpoints_and_paths_exist(self):
        rules = {rule.endpoint: rule.rule for rule in self.app.url_map.iter_rules()}
        for endpoint, path in EXPECTED_ENDPOINTS.items():
            self.assertIn(endpoint, rules, f'missing endpoint {endpoint}')
            self.assertEqual(rules[endpoint], path, f'{endpoint} path changed')


class ModelSchemaTests(DatabaseTestCase):
    def test_table_names(self):
        self.assertEqual(User.__tablename__, 'users')
        self.assertEqual(Task.__tablename__, 'tasks')
        self.assertEqual(TestCase.__tablename__, 'test_cases')
        self.assertEqual(Attempt.__tablename__, 'attempts')
        self.assertEqual(Match.__tablename__, 'matches')
        self.assertEqual(MatchResult.__tablename__, 'match_results')
        self.assertEqual(MatchmakingQueue.__tablename__, 'matchmaking_queue')

    def test_user_columns(self):
        columns = {column.name for column in User.__table__.columns}
        self.assertTrue(
            {
                'id', 'username', 'email', 'password_hash', 'elo', 'wins', 'losses',
                'draws', 'best_elo', 'games_played', 'current_streak', 'is_online',
                'last_seen', 'onboarding_completed', 'preferred_language',
                'experience_level', 'title',
            }.issubset(columns),
        )


class AuthAndPagesTests(DatabaseTestCase):
    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['status'], 'healthy')
        self.assertEqual(body['database'], 'connected')

    def test_register_login_and_main_page(self):
        response = self.client.post(
            '/register',
            data={
                'username': 'alice',
                'email': 'alice@example.com',
                'password': 'secret12',
                'confirm_password': 'secret12',
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/onboarding', response.headers['Location'])

        user = User.query.filter_by(username='alice').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.elo, 1000)
        self.assertTrue(user.is_online)

        self.client.get('/logout', follow_redirects=False)
        login_response = login(self.client, 'alice@example.com')
        self.assertEqual(login_response.status_code, 302)
        self.assertTrue(login_response.headers['Location'].endswith('/main'))

    def test_leaderboard_api(self):
        create_user('bob', 'bob@example.com', elo=1200)
        create_user('cara', 'cara@example.com', elo=1100)
        response = self.client.get('/api/leaderboard')
        self.assertEqual(response.status_code, 200)
        leaders = response.get_json()['leaders']
        self.assertEqual(leaders[0]['username'], 'bob')
        self.assertEqual(leaders[0]['rank'], 1)
        self.assertEqual(leaders[1]['username'], 'cara')


class JudgingTests(DatabaseTestCase):
    def test_validate_solution_accepts_correct_python(self):
        task = create_task(cases=[('1 2', '3', False), ('4 5', '9', True)])
        result = validate_solution(
            task.id,
            'a,b=map(int,input().split())\nprint(a+b)',
            'python',
        )
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['tests_passed'], 2)
        self.assertEqual(result['total_tests'], 2)

    def test_submit_solution_training(self):
        create_user('dave', 'dave@example.com')
        task = create_task()
        login(self.client, 'dave@example.com')
        response = self.client.post(
            '/api/solutions/submit',
            json={
                'task_id': task.id,
                'code': 'a,b=map(int,input().split())\nprint(a+b)',
                'language': 'python',
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['status'], 'accepted')
        self.assertEqual(body['tests_passed'], 1)
        self.assertIn('attempt_id', body)
        self.assertIn('message', body)
        self.assertNotIn('match_id', body)
        attempt = db.session.get(Attempt, body['attempt_id'])
        self.assertEqual(attempt.status, 'accepted')
        self.assertGreater(attempt.score, 0)

    def test_run_api_requires_login(self):
        response = self.client.post('/api/run', json={'code': 'print(1)'})
        self.assertEqual(response.status_code, 302)

    def test_sample_tests_and_attempt_history(self):
        create_user('dave', 'dave@example.com')
        task = create_task(cases=[('1 2', '3', False), ('9 9', '18', True)])
        login(self.client, 'dave@example.com')

        samples = self.client.get(f'/api/tasks/{task.id}/sample_test')
        self.assertEqual(samples.status_code, 200)
        self.assertEqual(len(samples.get_json()['sample_tests']), 1)
        self.assertEqual(samples.get_json()['sample_tests'][0]['expected_output'], '3')

        self.client.post(
            '/api/solutions/submit',
            json={'task_id': task.id, 'code': 'print(0)', 'language': 'python'},
        )
        history = self.client.get(f'/api/tasks/{task.id}/attempts')
        self.assertEqual(history.status_code, 200)
        attempts = history.get_json()
        self.assertEqual(len(attempts), 1)
        self.assertIn('code', attempts[0])
        self.assertEqual(attempts[0]['task_id'], task.id)

        run_response = self.client.post(
            '/api/run',
            json={'code': 'print(7)', 'input_data': '', 'language': 'python', 'time_limit': 2},
        )
        self.assertEqual(run_response.status_code, 200)
        self.assertEqual(run_response.get_json()['output'], '7')

    def test_public_and_authed_pages_render(self):
        create_user('dave', 'dave@example.com')
        create_task()
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/about').status_code, 200)
        self.assertEqual(self.client.get('/leaderboard').status_code, 200)
        self.assertEqual(self.client.get('/user/dave').status_code, 200)
        login(self.client, 'dave@example.com')
        self.assertEqual(self.client.get('/tasks').status_code, 200)
        self.assertEqual(self.client.get('/profile').status_code, 200)
        self.assertEqual(self.client.get('/main').status_code, 200)
        self.assertEqual(self.client.get('/matchmaking').status_code, 200)


class MatchLifecycleTests(DatabaseTestCase):
    def test_apply_match_result_updates_elo_and_stats(self):
        user = create_user('eve', 'eve@example.com', elo=1000)
        opponent = create_user('frank', 'frank@example.com', elo=1000)
        task = create_task()
        match = Match(user_id=user.id, opponent_id=opponent.id, task_id=task.id)
        db.session.add(match)
        db.session.commit()

        apply_match_result(match, 'win')
        db.session.refresh(user)
        db.session.refresh(opponent)
        db.session.refresh(match)

        self.assertEqual(match.result, 'win')
        self.assertEqual(user.elo, 1016)
        self.assertEqual(opponent.elo, 984)
        self.assertEqual(user.wins, 1)
        self.assertEqual(opponent.losses, 1)
        self.assertEqual(user.current_streak, 1)
        self.assertEqual(opponent.current_streak, 0)
        self.assertEqual(user.games_played, 1)
        self.assertEqual(match.user_rating_change, 16)
        self.assertEqual(match.opponent_rating_change, -16)
        self.assertIsNotNone(match.ended_at)

    def test_finalize_persists_result_when_user_solves_all(self):
        user = create_user('gina', 'gina@example.com', elo=1000)
        opponent = create_user('hank', 'hank@example.com', elo=1000)
        task = create_task()
        match = Match(user_id=user.id, opponent_id=opponent.id, task_id=task.id)
        db.session.add(match)
        db.session.commit()

        attempt = Attempt(
            user_id=user.id,
            task_id=task.id,
            code='print(3)',
            language='python',
            status='accepted',
            execution_time=0.2,
            tests_passed=1,
            total_tests=1,
            score=100,
        )
        db.session.add(attempt)
        db.session.flush()
        db.session.add(MatchResult(
            match_id=match.id,
            user_id=user.id,
            attempt_id=attempt.id,
            score=100,
            tests_passed=1,
            total_tests=1,
            execution_time=0.2,
        ))
        db.session.commit()

        finalize_match_if_needed(match)
        db.session.refresh(match)
        db.session.refresh(user)
        db.session.refresh(opponent)

        self.assertEqual(match.result, 'win')
        self.assertEqual(user.elo, 1016)
        self.assertEqual(opponent.elo, 984)

    def test_forfeit_awards_win_to_opponent(self):
        user = create_user('ivy', 'ivy@example.com', elo=1000)
        opponent = create_user('jake', 'jake@example.com', elo=1000)
        task = create_task()
        match = Match(
            user_id=user.id,
            opponent_id=opponent.id,
            task_id=task.id,
            started_at=utc_now(),
        )
        db.session.add(match)
        db.session.commit()

        login(self.client, 'ivy@example.com')
        response = self.client.post('/api/match/forfeit')
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body.get('ok'))
        self.assertEqual(body['result'], 'loss')
        self.assertEqual(body['result_for_user'], 'loss')

        db.session.refresh(match)
        db.session.refresh(user)
        db.session.refresh(opponent)
        self.assertEqual(match.result, 'loss')
        self.assertEqual(user.elo, 984)
        self.assertEqual(opponent.elo, 1016)
        self.assertEqual(opponent.wins, 1)

    def test_matchmaking_pairs_two_searchers(self):
        create_task(difficulty='easy')
        kate = create_user('kate', 'kate@example.com', elo=1000, is_online=True)
        leo = create_user('leo', 'leo@example.com', elo=1010, is_online=True)
        matchmaking = self.app.matchmaking_system

        first = matchmaking.find_opponent(kate.id, kate.elo, 'easy')
        self.assertTrue(first.get('in_queue'))
        self.assertFalse(first.get('match_found'))

        second = matchmaking.find_opponent(leo.id, leo.elo, 'easy')
        self.assertTrue(second.get('match_found'), second)
        self.assertEqual(second['opponent']['username'], 'kate')
        match = db.session.get(Match, second['match_id'])
        self.assertIsNotNone(match)
        self.assertIsNone(match.result)
        self.assertEqual({match.user_id, match.opponent_id}, {kate.id, leo.id})

    def test_duel_submit_finalizes_when_all_tests_pass(self):
        user = create_user('gina', 'gina@example.com', elo=1000, is_online=True)
        opponent = create_user('hank', 'hank@example.com', elo=1000, is_online=True)
        task = create_task()
        match = Match(
            user_id=user.id,
            opponent_id=opponent.id,
            task_id=task.id,
            started_at=utc_now(),
        )
        db.session.add(match)
        db.session.commit()

        login(self.client, 'gina@example.com')
        response = self.client.post(
            '/api/solutions/submit',
            json={
                'task_id': task.id,
                'code': 'a,b=map(int,input().split())\nprint(a+b)',
                'language': 'python',
                'match_id': match.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['status'], 'accepted')
        self.assertEqual(body['match_id'], match.id)
        self.assertEqual(body['match_status'], 'win')

        db.session.refresh(match)
        db.session.refresh(user)
        db.session.refresh(opponent)
        self.assertEqual(match.result, 'win')
        self.assertEqual(user.elo, 1016)
        self.assertEqual(opponent.elo, 984)
        self.assertEqual(MatchResult.query.filter_by(match_id=match.id).count(), 1)

    def test_matchmaking_http_start_enqueues_current_user(self):
        create_task(difficulty='easy')
        create_user('kate', 'kate@example.com', elo=1000, is_online=True)
        login(self.client, 'kate@example.com')
        response = self.client.post('/api/matchmaking/start', json={'difficulty': 'easy'})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body.get('success'))
        self.assertFalse(body.get('match_found'))
        self.assertTrue(body.get('in_queue'))
        self.assertEqual(MatchmakingQueue.query.filter_by(status='searching').count(), 1)

    def test_profile_context_counts_training_solves_only(self):
        from services.profile_service import build_profile_context

        user = create_user('mia', 'mia@example.com')
        opponent = create_user('ned', 'ned@example.com')
        task = create_task()
        training = Attempt(
            user_id=user.id, task_id=task.id, code='x', language='python',
            status='accepted', tests_passed=1, total_tests=1, score=10,
        )
        db.session.add(training)
        db.session.flush()
        duel_attempt = Attempt(
            user_id=user.id, task_id=task.id, code='y', language='python',
            status='accepted', tests_passed=1, total_tests=1, score=10,
        )
        db.session.add(duel_attempt)
        db.session.flush()
        match = Match(
            user_id=user.id, opponent_id=opponent.id, task_id=task.id, result='win',
        )
        db.session.add(match)
        db.session.flush()
        db.session.add(MatchResult(
            match_id=match.id, user_id=user.id, attempt_id=duel_attempt.id,
            score=10, tests_passed=1, total_tests=1,
        ))
        db.session.commit()

        context = build_profile_context(user, match_limit=5)
        self.assertEqual(context['total_attempts'], 2)
        self.assertEqual(context['successful_attempts'], 2)
        self.assertEqual(context['solved_tasks_single'], 1)
        self.assertEqual(len(context['match_history']), 1)
        self.assertEqual(context['match_history'][0]['result'], 'win')
        self.assertEqual(context['match_history'][0]['opponent'], 'ned')


class DuelTimerConstantTests(unittest.TestCase):
    def test_duel_length_is_two_hours(self):
        self.assertEqual(DUEL_MAX_TIME_SECONDS, 7200)


if __name__ == '__main__':
    unittest.main()
