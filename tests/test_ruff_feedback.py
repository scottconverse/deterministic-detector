"""Behavioral tests for hooks/ruff_feedback.py.

Every test invokes the hook exactly as Claude Code does: a subprocess with the
PostToolUse JSON payload on stdin. Assertions are on the post-conditions the
plugin promises — exit codes and stderr — not on internals.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

def _find_hook() -> Path:
    # mutmut copies scoped sources into a mutants/ tree and runs the suite
    # from inside it; hooks/ is only in the real repo root. Walk the
    # ancestors of both the test file and the cwd until it appears.
    for anchor in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for base in (anchor, *anchor.parents):
            candidate = base / "hooks" / "ruff_feedback.py"
            if candidate.exists():
                return candidate
    raise FileNotFoundError("hooks/ruff_feedback.py not found from test anchor or cwd")


HOOK = _find_hook()
RUFF = shutil.which("ruff")

VIOLATING_SOURCE = "import os,sys\nx=[1,2 ,3]\n"
CLEAN_SOURCE = "def add(a: int, b: int) -> int:\n    return a + b\n"
RUFF_CONFIG = '[tool.ruff]\nline-length = 100\n'


def run_hook(stdin_bytes: bytes) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_bytes,
        capture_output=True,
        timeout=60,
    )


def payload_for(path: Path) -> bytes:
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(path)},
    }
    return json.dumps(payload).encode("utf-8")


def test_non_python_file_is_ignored(tmp_path):
    target = tmp_path / "notes.txt"
    target.write_text("import os,sys\n")
    result = run_hook(payload_for(target))
    assert result.returncode == 0
    assert result.stderr == b""


def test_missing_file_is_ignored(tmp_path):
    result = run_hook(payload_for(tmp_path / "ghost.py"))
    assert result.returncode == 0
    assert result.stderr == b""


def test_malformed_stdin_is_ignored():
    result = run_hook(b"this is not json {")
    assert result.returncode == 0
    assert result.stderr == b""


def test_payload_without_file_path_is_ignored():
    payload = json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Edit"})
    result = run_hook(payload.encode("utf-8"))
    assert result.returncode == 0
    assert result.stderr == b""


def test_no_ruff_config_up_tree_is_silent(tmp_path):
    target = tmp_path / "orphan.py"
    target.write_text(VIOLATING_SOURCE)
    result = run_hook(payload_for(target))
    assert result.returncode == 0
    assert result.stderr == b""


@pytest.mark.skipif(RUFF is None, reason="ruff not on PATH")
def test_violation_with_config_exits_2_with_findings(tmp_path):
    (tmp_path / "pyproject.toml").write_text(RUFF_CONFIG)
    target = tmp_path / "bad.py"
    target.write_text(VIOLATING_SOURCE)
    result = run_hook(payload_for(target))
    assert result.returncode == 2
    assert b"F401" in result.stderr


@pytest.mark.skipif(RUFF is None, reason="ruff not on PATH")
def test_bom_stdin_still_reaches_verdict(tmp_path):
    (tmp_path / "pyproject.toml").write_text(RUFF_CONFIG)
    target = tmp_path / "bad.py"
    target.write_text(VIOLATING_SOURCE)
    result = run_hook(b"\xef\xbb\xbf" + payload_for(target))
    assert result.returncode == 2
    assert result.stderr != b""


@pytest.mark.skipif(RUFF is None, reason="ruff not on PATH")
def test_clean_file_with_config_is_silent(tmp_path):
    (tmp_path / "pyproject.toml").write_text(RUFF_CONFIG)
    target = tmp_path / "good.py"
    target.write_text(CLEAN_SOURCE)
    result = run_hook(payload_for(target))
    assert result.returncode == 0
    assert result.stderr == b""


@pytest.mark.skipif(RUFF is None, reason="ruff not on PATH")
def test_ruff_toml_config_is_also_discovered(tmp_path):
    (tmp_path / "ruff.toml").write_text('line-length = 100\n')
    target = tmp_path / "bad.py"
    target.write_text(VIOLATING_SOURCE)
    result = run_hook(payload_for(target))
    assert result.returncode == 2
