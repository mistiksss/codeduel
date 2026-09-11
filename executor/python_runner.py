"""Run a Python program in a resource-limited subprocess."""

import os
import resource
import signal
import subprocess
import sys
import tempfile
import time

from constants import (
    MAX_OUTPUT_CHARS,
    SANDBOX_MAX_FILE_BYTES,
    SANDBOX_MEMORY_BYTES,
    SANDBOX_MAX_OPEN_FILES,
)

# Minimal environment so user code cannot read app secrets from the parent.
_SANDBOX_ENV = {
    'PATH': '/usr/bin:/bin',
    'LANG': 'C.UTF-8',
    'LC_ALL': 'C.UTF-8',
    'PYTHONIOENCODING': 'utf-8',
    'PYTHONDONTWRITEBYTECODE': '1',
}


def truncate_output(text: str) -> str:
    """Cap captured stdout/stderr so a hostile program cannot fill memory."""
    if not text:
        return ''
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + '\n...<output truncated>...'


def _decode_pipe(raw: bytes) -> str:
    if not raw:
        return ''
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp1251', errors='replace')


def _sandbox_preexec(cpu_seconds: int):
    """Apply rlimits in the child before exec (Linux)."""

    def _preexec():
        cpu = max(1, int(cpu_seconds))
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        except (ValueError, OSError):
            pass
        try:
            resource.setrlimit(
                resource.RLIMIT_AS,
                (SANDBOX_MEMORY_BYTES, SANDBOX_MEMORY_BYTES),
            )
        except (ValueError, OSError):
            pass
        try:
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (SANDBOX_MAX_FILE_BYTES, SANDBOX_MAX_FILE_BYTES),
            )
        except (ValueError, OSError):
            pass
        try:
            resource.setrlimit(
                resource.RLIMIT_NOFILE,
                (SANDBOX_MAX_OPEN_FILES, SANDBOX_MAX_OPEN_FILES),
            )
        except (ValueError, OSError):
            pass
        # Core dumps off.
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (ValueError, OSError):
            pass

    return _preexec


def _kill_process_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except OSError:
            pass


def run_code_python(code, input_data, time_limit):
    """Write ``code`` to a temp file and execute it with isolated CPython.

    The child gets a clean environment (no parent secrets), ``python -I``
    isolated mode, and rlimits for CPU, address space, file size and fds.
    Wall-clock timeout still applies; the whole process group is killed if
    it overruns.

    Returns a dict with keys ``success``, ``output``, ``error``, ``time``
    and ``status`` (``success``, ``runtime_error`` or ``time_limit``).
    """
    start = time.time()
    work_dir = tempfile.mkdtemp(prefix='codeduel_run_')
    file_path = os.path.join(work_dir, 'solution.py')

    with open(file_path, 'w', encoding='utf-8') as handle:
        handle.write(code)

    stdin_data = '' if input_data is None else str(input_data)
    stdin_bytes = stdin_data.encode('utf-8')
    if stdin_bytes and not stdin_bytes.endswith(b'\n'):
        stdin_bytes += b'\n'

    env = dict(_SANDBOX_ENV)
    env['HOME'] = work_dir
    env['TMPDIR'] = work_dir
    env['TEMP'] = work_dir
    env['TMP'] = work_dir

    cpu_seconds = max(1, int(time_limit) if time_limit else 1)
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, '-I', file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=work_dir,
            env=env,
            start_new_session=True,
            close_fds=True,
            preexec_fn=_sandbox_preexec(cpu_seconds),
        )
        try:
            stdout_raw, stderr_raw = proc.communicate(
                input=stdin_bytes,
                timeout=time_limit,
            )
        except subprocess.TimeoutExpired:
            _kill_process_group(proc)
            proc.communicate()
            return {
                'success': False,
                'output': '',
                'error': 'Time Limit Exceeded',
                'time': time_limit,
                'status': 'time_limit',
            }

        elapsed = round(time.time() - start, 3)
        stdout_text = truncate_output(_decode_pipe(stdout_raw).strip())
        stderr_text = truncate_output(_decode_pipe(stderr_raw).strip())

        if proc.returncode == 0:
            return {
                'success': True,
                'output': stdout_text,
                'error': '',
                'time': elapsed,
                'status': 'success',
            }
        return {
            'success': False,
            'output': stdout_text,
            'error': stderr_text,
            'time': elapsed,
            'status': 'runtime_error',
        }
    finally:
        if proc is not None and proc.poll() is None:
            _kill_process_group(proc)
            try:
                proc.wait(timeout=1)
            except Exception:
                pass
        try:
            os.remove(file_path)
        except OSError:
            pass
        try:
            os.rmdir(work_dir)
        except OSError:
            pass
