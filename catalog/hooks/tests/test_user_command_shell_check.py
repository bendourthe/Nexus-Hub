"""Tests for catalog/hooks/user-command-shell-check.py.

The hook runs as a subprocess, as Claude Code runs it, against synthetic
transcripts written to tmp_path in Claude Code's JSONL shape: one line per
content block, each carrying ``type: "assistant"`` and a ``message`` whose
``id`` groups the blocks of one reply. The Stop payload keys follow the Claude
Code capture recorded in docs/releases/v4/v4.13/development/v4.13.7-decisions.md.

Run with: pytest catalog/hooks/tests/test_user_command_shell_check.py -q
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "user-command-shell-check.py"
CLEARED_ENV = ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "NEXUS_SHELL_CHECK_PLATFORM", "QWEN_PROJECT_DIR")

FENCE = "```"


def _block(label: str, body: str) -> str:
    return f"Run this:\n\n{FENCE}{label}\n{body}\n{FENCE}\n"


def _write_transcript(tmp_path: Path, reply: str) -> Path:
    """A transcript whose last assistant message is split across two lines."""
    head, _, tail = reply.partition("\n")
    entries = [
        {"type": "user", "message": {"role": "user", "content": "do the thing"}},
        {"type": "assistant", "message": {"id": "msg_old", "role": "assistant",
                                          "content": [{"type": "text", "text": _block("powershell", "a && b")}]}},
        {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}},
        {"type": "assistant", "message": {"id": "msg_final", "role": "assistant",
                                          "content": [{"type": "text", "text": head}]}},
        {"type": "assistant", "message": {"id": "msg_final", "role": "assistant",
                                          "content": [{"type": "text", "text": tail}]}},
        {"type": "system", "subtype": "turn_duration"},
    ]
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    return path


def _run(stdin: str, platform: str = "windows", **env: str) -> subprocess.CompletedProcess[str]:
    child_env = {k: v for k, v in os.environ.items() if k not in CLEARED_ENV}
    child_env["NEXUS_SHELL_CHECK_PLATFORM"] = platform
    child_env.update(env)
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True,
                          text=True, encoding="utf-8", env=child_env, timeout=30, check=False)


def _stop(tmp_path: Path, reply: str, platform: str = "windows", **extra: object) -> subprocess.CompletedProcess[str]:
    payload = {"session_id": "s1", "hook_event_name": "Stop", "cwd": str(tmp_path),
               "permission_mode": "default", "stop_hook_active": False,
               "transcript_path": str(_write_transcript(tmp_path, reply))}
    payload.update(extra)
    return _run(json.dumps(payload), platform)


def _message(result: subprocess.CompletedProcess[str]) -> str:
    assert result.returncode == 0
    return json.loads(result.stdout)["systemMessage"]


@pytest.mark.parametrize(
    ("label", "body", "platform", "expected"),
    [
        ("powershell", "git add .\ngit commit -m 'x' && git push", "posix", "`&&` (line 2)"),
        ("ps1", "Test-Path a || exit 1", "posix", "`||` (line 1)"),
        ("", "cmd1 && cmd2", "windows", "`&&` (line 1)"),
        ("pwsh", "cat <<EOF\nhi\nEOF", "windows", "a `<<` heredoc (line 1)"),
        ("PowerShell", "NODE_ENV=production npm run build", "windows", "a leading `VAR=value` prefix (line 1)"),
        ("ps", "export PATH=/x:$PATH", "windows", "`export` (line 1)"),
    ],
)
def test_flagged_powershell_block_warns(tmp_path: Path, label: str, body: str, platform: str, expected: str) -> None:
    message = _message(_stop(tmp_path, _block(label, body), platform))
    assert expected in message and "Windows PowerShell 5.1" in message


@pytest.mark.parametrize(
    ("label", "body", "platform"),
    [
        ("bash", "make build && make test", "windows"),
        ("sh", "export X=1", "windows"),
        ("text", "a || b", "windows"),
        ("", "cmd1 && cmd2", "posix"),
        ("powershell", "npm ci; if ($?) { npm test }", "windows"),
        ("powershell", '$env:X = "1"\n$x = 1\nnpm test', "windows"),
        ("powershell", "# a && b in a comment\nWrite-Host 'a && b' \"c || d\"", "windows"),
    ],
)
def test_clean_or_unchecked_block_is_silent(tmp_path: Path, label: str, body: str, platform: str) -> None:
    result = _stop(tmp_path, _block(label, body), platform)
    assert result.returncode == 0 and result.stdout == ""


def test_only_the_final_assistant_message_is_read(tmp_path: Path) -> None:
    # The earlier message msg_old has a flagged block; the final reply is clean.
    result = _stop(tmp_path, _block("powershell", "npm ci\nnpm test"))
    assert result.stdout == ""


def test_last_assistant_message_takes_precedence(tmp_path: Path) -> None:
    result = _stop(tmp_path, _block("powershell", "npm ci"),
                   last_assistant_message=_block("powershell", "a && b"))
    assert "`&&` (line 1)" in _message(result)


def test_utf8_bom_and_non_ascii_reply_are_read(tmp_path: Path) -> None:
    # A BOM (Windows PowerShell 5.1 pipes add one) and UTF-8 text such as an
    # em-dash must not drop the hook into its silent fail-open path.
    payload = {"hook_event_name": "Stop", "stop_hook_active": False,
               "last_assistant_message": "Done \u2014 run:\n" + _block("powershell", "a && b")}
    assert "`&&` (line 1)" in _message(_run("\ufeff" + json.dumps(payload, ensure_ascii=False)))


def test_several_blocks_are_numbered_and_content_is_not_echoed(tmp_path: Path) -> None:
    reply = _block("powershell", "secret-tool --token abc && go") + _block("ps1", "export Y=2")
    message = _message(_stop(tmp_path, reply))
    assert "block 1, line 1" in message and "block 2, line 1" in message
    assert "secret-tool" not in message and "abc" not in message


def test_stop_hook_active_is_silent(tmp_path: Path) -> None:
    result = _stop(tmp_path, _block("powershell", "a && b"), stop_hook_active=True)
    assert result.returncode == 0 and result.stdout == ""


@pytest.mark.parametrize("foreign", ["turn_id", "cursor_version", "timestamp"])
def test_other_platform_payload_is_silent(tmp_path: Path, foreign: str) -> None:
    result = _stop(tmp_path, _block("powershell", "a && b"), **{foreign: "x", "model": "m"})
    assert result.returncode == 0 and result.stdout == ""


@pytest.mark.parametrize(
    "env",
    [{"NEXUS_DISABLED_HOOKS": "usage-guard,user-command-shell-check"}, {"NEXUS_HOOK_PROFILE": "minimal"}],
)
def test_disabled_hook_is_silent(tmp_path: Path, env: dict[str, str]) -> None:
    payload = {"hook_event_name": "Stop", "stop_hook_active": False,
               "last_assistant_message": _block("powershell", "a && b")}
    result = _run(json.dumps(payload), **env)
    assert result.returncode == 0 and result.stdout == ""


@pytest.mark.parametrize("stdin", ["", "not json", "[1, 2]", '{"hook_event_name": "Stop"}'])
def test_malformed_or_empty_input_is_silent(stdin: str) -> None:
    result = _run(stdin)
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""


def test_missing_transcript_is_silent(tmp_path: Path) -> None:
    payload = {"hook_event_name": "Stop", "stop_hook_active": False,
               "transcript_path": str(tmp_path / "absent.jsonl")}
    result = _run(json.dumps(payload))
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""
