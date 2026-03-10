"""Solution validation and task score calculation."""
import math

from extensions import db
from models import Task, TestCase
from executor import run_code


def normalize_output(output):
    """Normalize code output for comparison (strip, unify line endings)."""
    if output is None:
        return ""
    return output.strip().replace('\r\n', '\n')


def validate_solution(task_id, code, language):
    """Run code against all test cases and return validation result."""
    task = db.session.get(Task, int(task_id))
    if not task:
        return {'error': 'Task not found'}
    test_cases = TestCase.query.filter_by(task_id=task_id).order_by(TestCase.id).all()
    if not test_cases:
        return {'error': 'No test cases found for this task'}
    results = []
    tests_passed = 0
    total_execution_time = 0.0
    max_memory_used = 0
    for test_case in test_cases:
        result = run_code(code, test_case.input_data, task.time_limit, language)
        exec_time = float(result.get('time') or 0)
        mem_used = int(result.get('memory') or 0)
        total_execution_time += exec_time
        max_memory_used = max(max_memory_used, mem_used)
        test_result = {
            'test_id': test_case.id,
            'status': result.get('status', 'system_error'),
            'passed': False,
            'execution_time': exec_time,
            'memory_used': mem_used,
            'error': (result.get('error') or '')[:200],
        }
        if result.get('success'):
            normalized_output = normalize_output(result.get('output', ''))
            normalized_expected = normalize_output(test_case.expected_output)
            if normalized_output == normalized_expected:
                test_result['passed'] = True
                test_result['status'] = 'passed'
                tests_passed += 1
            else:
                test_result['status'] = 'wrong_answer'
        results.append(test_result)
    total_tests = len(test_cases)
    pass_ratio = (tests_passed / total_tests) if total_tests else 0.0
    avg_execution_time = (total_execution_time / total_tests) if total_tests else 0.0
    if tests_passed == total_tests:
        overall_status = 'accepted'
    elif tests_passed > 0:
        overall_status = 'partially_correct'
    elif any(r['status'] == 'time_limit' for r in results):
        overall_status = 'time_limit'
    elif any(r['status'] == 'compilation_error' for r in results):
        overall_status = 'compilation_error'
    elif any(r['status'] == 'runtime_error' for r in results):
        overall_status = 'runtime_error'
    else:
        overall_status = 'wrong_answer'
    return {
        'status': overall_status,
        'tests_passed': tests_passed,
        'total_tests': total_tests,
        'pass_ratio': pass_ratio,
        'execution_time': avg_execution_time,
        'memory_used': max_memory_used,
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
    task_points = int(task_points or 0)
    total_tests = int(total_tests or 0)
    tests_passed = int(tests_passed or 0)

    if task_points <= 0 or total_tests <= 0:
        return {"base": 0, "bonus": 0, "total": 0}

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
        tl = max(1, int(time_limit))
        ratio = avg_execution_time / tl
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
        "base": int(base_score),
        "bonus": int(bonus),
        "total": int(total)
    }
