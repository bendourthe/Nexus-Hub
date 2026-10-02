"""Pin cursor-hook-compat.py passthrough for non-permission events (v4.13.7 7.3).

usage-guard answers Cursor ``postToolUse`` with ``{"additional_context": ...}``
and ``stop`` with ``{"followup_message": ...}``. Both run through the
compatibility launcher, so these tests pin the launcher's observed behavior:
a valid JSON object on stdout passes through unchanged, and empty or prose
stdout becomes ``{}`` (prose moves to stderr). A non-Cursor payload keeps the
child's stdout byte-for-byte.

Run with: pytest catalog/hooks/tests/test_cursor_hook_compat_passthrough.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_COMPAT = Path(__file__).resolve().parent.parent / "cursor-hook-compat.py"


def _child(tmp_path: Path, stdout: str, exit_code: int = 0) -> Path:
    script = tmp_path / "child-hook.py"
    script.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        f"sys.stdout.write({stdout!r})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    return script


def _run(tmp_path: Path, child: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_COMPAT), sys.executable, str(child)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        timeout=60,
    )


def _cursor(event: str, **extra: object) -> dict:
    return {"cursor_version": "2.4.0", "hook_event_name": event, "conversation_id": "c", **extra}


@pytest.mark.parametrize(
    ("event", "body"),
    [
        ("postToolUse", {"additional_context": "Usage limit: Cursor monthly usage is at 99%."}),
        ("stop", {"followup_message": "Usage limit: Cursor monthly usage is at 99%."}),
    ],
)
def test_guard_output_passes_through_unchanged(tmp_path, event, body):
    child = _child(tmp_path, json.dumps(body) + "\n")
    proc = _run(tmp_path, child, _cursor(event))
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == body
    assert proc.stdout == json.dumps(body) + "\n"


@pytest.mark.parametrize("event", ["postToolUse", "stop"])
def test_empty_output_becomes_an_empty_object(tmp_path, event):
    proc = _run(tmp_path, _child(tmp_path, ""), _cursor(event, loop_count=0))
    assert proc.returncode == 0
    assert proc.stdout.strip() == "{}"


@pytest.mark.parametrize("event", ["postToolUse", "stop"])
def test_prose_output_becomes_an_empty_object_with_prose_on_stderr(tmp_path, event):
    proc = _run(tmp_path, _child(tmp_path, "advisory note\n"), _cursor(event))
    assert proc.returncode == 0
    assert proc.stdout.strip() == "{}"
    assert "advisory note" in proc.stderr


def test_non_cursor_payload_keeps_stdout_byte_for_byte(tmp_path):
    raw = '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "x"}}\n'
    proc = _run(tmp_path, _child(tmp_path, raw), {"hook_event_name": "PostToolUse", "session_id": "s"})
    assert proc.returncode == 0
    assert proc.stdout == raw
