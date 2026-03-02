import subprocess
import tempfile
from pathlib import Path


def execute_ts_code(code: str) -> str:
    """Execute TypeScript with Deno in a sandboxed temp file."""
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False, mode="w") as temp:
        temp.write(code)
        temp_path = Path(temp.name)

    try:
        result = subprocess.run(
            ["deno", "run", "--no-prompt", temp_path.as_posix()],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        return result.stdout.strip()
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Script execution timed out.") from error
    finally:
        temp_path.unlink(missing_ok=True)
