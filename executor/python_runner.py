"""Run a Python program in a subprocess with a wall-clock timeout."""

import os
import subprocess
import sys
import tempfile
import time

from constants import MAX_OUTPUT_CHARS


def truncate_output(text: str) -> str:
    """Cap captured stdout/stderr so a hostile program cannot fill memory."""
    if not text:
        return ''
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + '\n...<output truncated>...'


def run_code_python(code, input_data, time_limit):
    """Write ``code`` to a temp file and execute it with ``sys.executable``.

    Stdin is encoded as UTF-8. A trailing newline is appended when the
    payload is non-empty and does not already end with one, matching the
    historical judge behaviour.

    Returns a dict with keys ``success``, ``output``, ``error``, ``time``
    and ``status`` (``success``, ``runtime_error`` or ``time_limit``).
    """
    start = time.time()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w', encoding='utf-8') as handle:
        handle.write(code)
        file_path = handle.name

    try:
        stdin_data = input_data
        if stdin_data is None:
            stdin_data = ''
        stdin_bytes = str(stdin_data).encode('utf-8')
        if stdin_bytes and not stdin_bytes.endswith(b'\n'):
            stdin_bytes += b'\n'

        result = subprocess.run(
            [sys.executable, file_path],
            input=stdin_bytes,
            capture_output=True,
            timeout=time_limit,
        )

        elapsed = round(time.time() - start, 3)
        try:
            stdout_text = result.stdout.decode('utf-8')
        except UnicodeDecodeError:
            stdout_text = result.stdout.decode('cp1251', errors='replace')

        try:
            stderr_text = result.stderr.decode('utf-8')
        except UnicodeDecodeError:
            stderr_text = result.stderr.decode('cp1251', errors='replace')

        stdout_text = stdout_text.strip()
        stderr_text = stderr_text.strip()

        if result.returncode == 0:
            return {
                'success': True,
                'output': truncate_output(stdout_text),
                'error': '',
                'time': elapsed,
                'status': 'success',
            }
        return {
            'success': False,
            'output': truncate_output(stdout_text),
            'error': truncate_output(stderr_text),
            'time': elapsed,
            'status': 'runtime_error',
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': 'Time Limit Exceeded',
            'time': time_limit,
            'status': 'time_limit',
        }
    finally:
        os.remove(file_path)
