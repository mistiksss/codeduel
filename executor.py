import subprocess
import sys
import tempfile
import os
import time

MAX_OUTPUT_CHARS = 50_000


def _truncate(text: str) -> str:
    if not text:
        return ""
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n...<output truncated>..."


def run_code_python(code, input_data, time_limit):
    start = time.time()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as f:
        f.write(code)
        file_path = f.name

    try:
        stdin_data = input_data
        if stdin_data is None:
            stdin_data = ""
        stdin_bytes = str(stdin_data).encode("utf-8")
        if stdin_bytes and not stdin_bytes.endswith(b"\n"):
            stdin_bytes += b"\n"

        result = subprocess.run(
            [sys.executable, file_path],
            input=stdin_bytes,
            capture_output=True,
            timeout=time_limit,
        )

        elapsed = round(time.time() - start, 3)
        try:
            out = result.stdout.decode("utf-8")
        except UnicodeDecodeError:
            out = result.stdout.decode("cp1251", errors="replace")

        try:
            err = result.stderr.decode("utf-8")
        except UnicodeDecodeError:
            err = result.stderr.decode("cp1251", errors="replace")

        out = out.strip()
        err = err.strip()

        if result.returncode == 0:
            return {
                "success": True,
                "output": _truncate(out),
                "error": "",
                "time": elapsed,
                "status": "success",
            }
        else:
            return {
                "success": False,
                "output": _truncate(out),
                "error": _truncate(err),
                "time": elapsed,
                "status": "runtime_error",
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Time Limit Exceeded",
            "time": time_limit,
            "status": "time_limit",
        }
    finally:
        os.remove(file_path)


def run_code(code, input_data, time_limit, language):
    language = (language or "").lower()

    if language == "python":
        return run_code_python(code, input_data, time_limit)

    return {
        "success": False,
        "output": "",
        "error": f"Unsupported language: {language}",
        "time": 0,
        "status": "system_error",
    }