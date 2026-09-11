"""Judge user solutions against a task's test cases and compute the score."""

import math

from executor import run_code
from extensions import db
from models import Task, TestCase


def normalize_output(output):
    """Canonicalize program output before comparing with the expected answer.

    Trailing whitespace is stripped and Windows newlines are converted to
    ``\\n``. ``None`` becomes an empty string.
    """
    if output is None:
        return ''
    return output.strip().replace('\r\n', '\n')


def validate_solution(task_id, code, language):
    """Run ``code`` on every test case of ``task_id``.

    Returns a dict with overall ``status``, pass counts, average execution
    time and a per-test ``results`` list. On missing task/cases the dict
    only contains ``error``.
    """
    task = db.session.get(Task, int(task_id))
    if not task:
        return {'error': 'Task not found'}

    test_cases = TestCase.query.filter_by(task_id=task_id).order_by(TestCase.id).all()
    if not test_cases:
        return {'error': 'No test cases found for this task'}

    results = []
    tests_passed = 0
    total_execution_time = 0.0

    for test_case in test_cases:
        run_result = run_code(code, test_case.input_data, task.time_limit, language)
        execution_time = float(run_result.get('time') or 0)
        total_execution_time += execution_time
        test_result = {
            'test_id': test_case.id,
            'status': run_result.get('status', 'system_error'),
            'passed': False,
            'execution_time': execution_time,
            'error': (run_result.get('error') or '')[:200],
        }
        if run_result.get('success'):
            actual_output = normalize_output(run_result.get('output', ''))
            expected_output = normalize_output(test_case.expected_output)
            if actual_output == expected_output:
                test_result['passed'] = True
                test_result['status'] = 'passed'
                tests_passed += 1
            else:
                test_result['status'] = 'wrong_answer'
        results.append(test_result)

    total_tests = len(test_cases)
    pass_ratio = (tests_passed / total_tests) if total_tests else 0.0
    average_execution_time = (total_execution_time / total_tests) if total_tests else 0.0

    if tests_passed == total_tests:
        overall_status = 'accepted'
    elif tests_passed > 0:
        overall_status = 'partially_correct'
    elif any(result['status'] == 'time_limit' for result in results):
        overall_status = 'time_limit'
    elif any(result['status'] == 'compilation_error' for result in results):
        overall_status = 'compilation_error'
    elif any(result['status'] == 'runtime_error' for result in results):
        overall_status = 'runtime_error'
    else:
        overall_status = 'wrong_answer'

    return {
        'status': overall_status,
        'tests_passed': tests_passed,
        'total_tests': total_tests,
        'pass_ratio': pass_ratio,
        'execution_time': average_execution_time,
        'results': results,
    }


def calculate_task_score(
    task_points: int,
    tests_passed: int,
    total_tests: int,
    *,
    is_first_try: bool,
    avg_execution_time: float,
    time_limit: int,
) -> dict:
    """Compute base + bonus points for a judged attempt.

    The formula is unchanged from the original implementation:

    * base = ceil(task_points * tests_passed / total_tests)
    * first-try bonus = ceil(task_points * 0.10) when at least one test passed
    * speed bonus uses 100% / 50% / 20% / 0% of ceil(task_points * 0.08)
      depending on avg_execution_time / time_limit
    * bonus is capped at 25% of task_points
    * total cannot exceed task_points, and a partial solution cannot reach
      the full task_points value
    """
    task_points = int(task_points or 0)
    total_tests = int(total_tests or 0)
    tests_passed = int(tests_passed or 0)

    if task_points <= 0 or total_tests <= 0:
        return {'base': 0, 'bonus': 0, 'total': 0}

    tests_passed = max(0, min(tests_passed, total_tests))
    progress = tests_passed / total_tests
    base_score = math.ceil(task_points * progress)
    if tests_passed == 0:
        base_score = 0

    max_bonus = math.ceil(task_points * 0.25)
    bonus = 0
    if is_first_try and tests_passed > 0:
        bonus += math.ceil(task_points * 0.10)
    if tests_passed > 0 and avg_execution_time is not None and time_limit:
        time_limit_seconds = max(1, int(time_limit))
        ratio = avg_execution_time / time_limit_seconds
        if ratio <= 0.30:
            speed_factor = 1.0
        elif ratio <= 0.60:
            speed_factor = 0.5
        elif ratio <= 0.90:
            speed_factor = 0.2
        else:
            speed_factor = 0.0
        bonus += math.ceil(task_points * 0.08 * speed_factor)

    bonus = min(bonus, max_bonus)
    total = base_score + bonus
    total = min(int(total), int(task_points))
    if total_tests > 0 and tests_passed < total_tests and task_points > 0:
        total = min(total, max(0, int(task_points) - 1))

    return {
        'base': int(base_score),
        'bonus': int(bonus),
        'total': int(total),
    }
