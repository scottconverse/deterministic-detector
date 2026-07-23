import json
import shutil
import subprocess
import sys
from pathlib import Path


def find_ruff_config(start: Path) -> bool:
    current = start.resolve().parent
    while True:
        if (current / "ruff.toml").exists() or (current / ".ruff.toml").exists():
            return True
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            try:
                text = pyproject.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                text = ""
            if "[tool.ruff" in text:
                return True
        if current.parent == current:
            return False
        current = current.parent


def main() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return 0

    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        return 0

    path = Path(file_path)
    if not path.exists() or path.suffix != ".py":
        return 0

    if not find_ruff_config(path):
        return 0

    ruff = shutil.which("ruff")
    if not ruff:
        return 0

    checks = [
        [ruff, "format", "--check", str(path)],
        [ruff, "check", str(path)],
    ]

    failures = []
    for cmd in checks:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except OSError:
            return 0
        if result.returncode != 0:
            failures.append(result.stdout + result.stderr)

    if failures:
        sys.stderr.write("\n".join(failures))
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
