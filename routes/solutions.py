"""Solution APIs: submit, dry-run, attempt history, sample tests."""

from flask import current_app, jsonify, request
from flask_login import current_user, login_required

from constants import (
    DEFAULT_RUN_TIME_LIMIT_SECONDS,
    MAX_ATTEMPTS_RETURNED,
    MAX_CODE_LENGTH_CHARS,
    MAX_ERROR_MESSAGE_LENGTH,
    MAX_STDIN_CHARS,
)
from executor import run_code
from extensions import db
from models import Attempt, Match, Task, TestCase
from services.match_service import finalize_match_if_needed
from services.scoring import calculate_task_score, validate_solution
from services.solution_service import (
    extract_first_error,
    get_match_broadcast_payload,
    get_status_message,
    serialize_attempt,
    upsert_match_result,
)
from utils.utc import utc_now


def register_solution_routes(app, limiter=None):
    """Register judging endpoints. Rate-limit submit when a limiter exists."""

    rate_limit = limiter.limit('10 per minute') if limiter else (lambda func: func)

    @app.route('/api/tasks/<int:task_id>/attempts')
    @login_required
    def get_task_attempts(task_id):
        try:
            attempts = (
                Attempt.query.filter_by(user_id=current_user.id, task_id=task_id)
                .order_by(Attempt.submitted_at.desc())
                .limit(MAX_ATTEMPTS_RETURNED)
                .all()
            )
            return jsonify([
                serialize_attempt(attempt, include_code_preview=True)
                for attempt in attempts
            ])
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @app.route('/api/solutions/submit', methods=['POST'])
    @rate_limit
    @login_required
    def submit_solution():
        try:
            payload = request.get_json() or {}
            task_id = payload.get('task_id')
            code = payload.get('code')
            language = (payload.get('language') or 'python').strip().lower()
            match_id = payload.get('match_id')

            if not task_id or not code:
                return jsonify({'error': 'Missing task_id or code'}), 400

            if language != 'python':
                return jsonify({'error': 'Only Python is supported'}), 400

            if len(code) > MAX_CODE_LENGTH_CHARS:
                return jsonify({
                    'error': f'Code exceeds maximum length ({MAX_CODE_LENGTH_CHARS} characters)',
                }), 400

            task = db.session.get(Task, int(task_id))
            if not task:
                return jsonify({'error': 'Task not found'}), 404

            match = None
            if match_id:
                match = db.session.get(Match, int(match_id))
                if not match:
                    return jsonify({'error': 'Match not found'}), 404
                if current_user.id not in [match.user_id, match.opponent_id]:
                    return jsonify({'error': 'Not a participant in this match'}), 403
                if match.result is not None:
                    return jsonify({'error': 'Match already finished'}), 400
                if not match.started_at:
                    match.started_at = utc_now()
                    db.session.commit()

            attempt = Attempt(
                user_id=current_user.id,
                task_id=task.id,
                code=code,
                language=language,
                status='testing',
                submitted_at=utc_now(),
                tests_passed=0,
                total_tests=0,
                score=0,
            )
            db.session.add(attempt)
            db.session.commit()

            socketio = getattr(current_app, 'socketio', None)
            if match_id:
                try:
                    if socketio:
                        socketio.emit('opponent_testing', {}, room=str(match_id))
                except Exception as exc:
                    current_app.logger.warning('socketio opponent_testing emit failed: %s', exc)

            validation = validate_solution(task.id, code, language)

            tests_passed = int(validation.get('tests_passed') or 0)
            total_tests = int(validation.get('total_tests') or 0)
            average_execution_time = float(validation.get('execution_time') or 0.0)

            attempts_count = Attempt.query.filter_by(
                user_id=current_user.id,
                task_id=task.id,
            ).count()
            is_first_try = (attempts_count <= 1)
            score_info = calculate_task_score(
                task_points=int(task.points or 0),
                tests_passed=tests_passed,
                total_tests=total_tests,
                is_first_try=is_first_try,
                avg_execution_time=average_execution_time,
                time_limit=int(task.time_limit or 1),
            )

            attempt.status = validation.get('status', 'error')
            attempt.tests_passed = tests_passed
            attempt.total_tests = total_tests
            attempt.execution_time = average_execution_time
            attempt.score = int(score_info.get('total') or 0)
            attempt.error_message = extract_first_error(validation)[:MAX_ERROR_MESSAGE_LENGTH]

            response_body = {
                'attempt_id': attempt.id,
                'status': attempt.status,
                'score': attempt.score,
                'max_score': int(task.points or 0),
                'tests_passed': attempt.tests_passed,
                'total_tests': attempt.total_tests,
                'execution_time': round(attempt.execution_time, 3) if attempt.execution_time else 0,
                'message': get_status_message(attempt.status),
            }

            if not match_id:
                db.session.commit()
                return jsonify(response_body)

            upsert_match_result(match, current_user.id, attempt)
            db.session.commit()
            finalize_match_if_needed(match)
            db.session.refresh(match)

            try:
                match_payload = get_match_broadcast_payload(match)
                match_payload['is_finished'] = match.result is not None
                if socketio:
                    socketio.emit('match_update', match_payload, room=str(match.id))
                    if match.result:
                        socketio.emit('match_finished', match_payload, room=str(match.id))
            except Exception as exc:
                current_app.logger.error('CRITICAL SOCKET ERROR: %s', exc)

            response_body['match_id'] = match.id
            response_body['match_status'] = match.result if match.result else 'in_progress'
            return jsonify(response_body)

        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception('Failed to submit solution')
            return jsonify({'error': 'Не удалось проверить решение'}), 500

    run_limit = limiter.limit('20 per minute') if limiter else (lambda func: func)

    @app.route('/api/run', methods=['POST'])
    @run_limit
    @login_required
    def run_code_api():
        try:
            payload = request.get_json() or {}
            code = payload.get('code')
            input_data = payload.get('input_data', '')
            language = payload.get('language', 'python')
            try:
                time_limit = int(payload.get('time_limit', DEFAULT_RUN_TIME_LIMIT_SECONDS))
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid time_limit'}), 400

            if not code:
                return jsonify({'error': 'No code provided'}), 400
            if len(code) > MAX_CODE_LENGTH_CHARS:
                return jsonify({
                    'error': f'Code exceeds maximum length ({MAX_CODE_LENGTH_CHARS} characters)',
                }), 400
            if input_data is None:
                input_data = ''
            input_data = str(input_data)
            if len(input_data) > MAX_STDIN_CHARS:
                return jsonify({'error': 'Input is too large'}), 400

            max_timeout = int(current_app.config.get('CODE_EXECUTION_TIMEOUT') or DEFAULT_RUN_TIME_LIMIT_SECONDS)
            time_limit = max(1, min(time_limit, max_timeout))

            result = run_code(code, input_data, time_limit, language)
            return jsonify({
                'success': result['success'],
                'output': result['output'],
                'error': result['error'],
                'execution_time': result['time'],
                'status': result['status'],
            })
        except Exception:
            current_app.logger.exception('Failed to run code')
            return jsonify({'error': 'Не удалось выполнить код'}), 500

    @app.route('/api/attempts/<int:attempt_id>/result')
    @login_required
    def get_attempt_result(attempt_id):
        try:
            attempt = Attempt.query.get_or_404(attempt_id)
            if attempt.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            return jsonify({
                'id': attempt.id,
                'status': attempt.status,
                'tests_passed': attempt.tests_passed,
                'total_tests': attempt.total_tests,
                'score': attempt.score,
                'execution_time': attempt.execution_time,
                'error_message': attempt.error_message,
                'submitted_at': (
                    attempt.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                    if attempt.submitted_at else None
                ),
            })
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500

    @app.route('/api/tasks/<int:task_id>/sample_test')
    @login_required
    def get_sample_test(task_id):
        try:
            test_cases = TestCase.query.filter_by(task_id=task_id, is_hidden=False).all()
            sample_tests = [
                {'input': test_case.input_data, 'expected_output': test_case.expected_output}
                for test_case in test_cases
            ]
            return jsonify({'sample_tests': sample_tests})
        except Exception as exc:
            return jsonify({'error': str(exc)}), 500
