"""Sandboxed execution of user-submitted programs."""

from executor.python_runner import run_code_python, truncate_output

__all__ = ['run_code', 'run_code_python', 'truncate_output']


def run_code(code, input_data, time_limit, language):
    """Run ``code`` with ``input_data`` and return a status dict.

    Currently only Python is supported. The returned dict always contains
    ``success``, ``output``, ``error``, ``time`` and ``status``.
    """
    language = (language or '').lower()

    if language == 'python':
        return run_code_python(code, input_data, time_limit)

    return {
        'success': False,
        'output': '',
        'error': f'Unsupported language: {language}',
        'time': 0,
        'status': 'system_error',
    }
