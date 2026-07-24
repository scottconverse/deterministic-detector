import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (?P<file_path>.+)$"
    r"|^\*\*\* Move to: (?P<move_path>.+)$",
    re.MULTILINE,
)


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


def edited_paths(payload: dict) -> list[Path]:
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return []

    raw_paths = []
    file_path = tool_input.get("file_path")
    if isinstance(file_path, str):
        raw_paths.append(file_path)

    command = tool_input.get("command")
    if isinstance(command, str):
        raw_paths.extend(
            match.group("file_path") or match.group("move_path")
            for match in PATCH_PATH_RE.finditer(command)
        )

    cwd_value = payload.get("cwd")
    cwd = Path(cwd_value) if isinstance(cwd_value, str) else Path.cwd()
    paths = []
    seen = set()
    for raw_path in raw_paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = cwd / path
        path = path.resolve()
        if path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def main() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return 0

    ruff = shutil.which("ruff")
    if not ruff:
        return 0

    failures = []
    for path in edited_paths(payload):
        if not path.exists() or path.suffix != ".py" or not find_ruff_config(path):
            continue
        checks = [
            [ruff, "format", "--check", str(path)],
            [ruff, "check", str(path)],
        ]
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
