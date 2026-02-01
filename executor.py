import subprocess
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

def normalize_input_data(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"' and '""' in s:
        s = s[1:-1]
        s = s.replace('""', '"')

    return s

def _normalize_input_to_utf8_bytes(input_data) -> bytes:
    if input_data is None:
        return b""
    if isinstance(input_data, (bytes, bytearray)):
        raw = bytes(input_data)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("cp1251", errors="replace")
        return text.encode("utf-8")
    return str(input_data).encode("utf-8")


def run_code_python(code, input_data, time_limit):
    start = time.time()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as f:
        f.write(code)
        file_path = f.name

    try:
        stdin_bytes = _normalize_input_to_utf8_bytes(input_data)
        if stdin_bytes and not stdin_bytes.endswith(b"\n"):
            stdin_bytes += b"\n"

        result = subprocess.run(
            ["python", file_path],
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
                "memory": 0,
            }
        else:
            return {
                "success": False,
                "output": _truncate(out),
                "error": _truncate(err),
                "time": elapsed,
                "status": "runtime_error",
                "memory": 0,
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Time Limit Exceeded",
            "time": time_limit,
            "status": "time_limit",
            "memory": 0,
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
        "memory": 0,
    }
