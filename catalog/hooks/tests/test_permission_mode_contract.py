"""Permission-mode contract for the Nexus-Hub security guards.

A guard that blocks a tool call in the default mode must step aside when the
host reports full access (`permission_mode: "bypassPermissions"`), and must keep blocking in every other mode, auto included.
Contract: docs/policy/permission-mode-contract.md.

One data-driven test covers every guard whose blocking case needs no setup;
memory-store-guard and user-edit-guard carry the same assertion in their own
files because their blocking cases need a repository or a recorded read. Each
case runs the .sh and the .ps1, so it is also an exit-code parity assertion.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[1]

# Assembled from parts so this file does not trip the secret scan itself.
_AWS = "AK" + "IA" + "1234567890ABCDEF"

# (guard, payload that blocks in the default mode, extra environment)
_CASES = [
    ("git-guardrails", {"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}}, {}),
    (
        "secret-scan",
        {"tool_name": "Write", "tool_input": {"file_path": "cfg.py", "content": f"key = '{_AWS}'"}},
        {},
    ),
    (
        "escalation-trigger",
        {"tool_name": "Write", "tool_input": {"file_path": "config/.env", "content": "A=1"}},
        {"ESCALATION_MODE": "block"},
    ),
]


def _command(kind: str, guard: str, request) -> list[str]:
    if kind == "sh":
        return [request.getfixturevalue("bash_bin"), str(_HOOKS_DIR / f"{guard}.sh")]
    return [
        request.getfixturevalue("powershell_bin"),
        "-NoProfile",
        "-File",
        str(_HOOKS_DIR / f"{guard}.ps1"),
    ]


@pytest.mark.parametrize("kind", ["sh", "ps1"])
@pytest.mark.parametrize("guard,payload,extra_env", _CASES, ids=[c[0] for c in _CASES])
@pytest.mark.parametrize(
    "mode,expected",
    [(None, 2), ("default", 2), ("acceptEdits", 2), ("auto", 2), ("bypassPermissions", 0)],
)
def test_guard_blocks_unless_full_access(
    request, tmp_path, kind, guard, payload, extra_env, mode, expected
):
    body = dict(payload)
    if mode is not None:
        body["permission_mode"] = mode
    env = {**os.environ, **extra_env}
    for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"):
        env.pop(key, None)
    result = subprocess.run(
        _command(kind, guard, request),
        input=json.dumps(body),
        text=True,
        capture_output=True,
        cwd=str(tmp_path),
        env=env,
        timeout=120,
        check=False,
    )
    assert result.returncode == expected, (result.stdout, result.stderr)


@pytest.mark.parametrize("kind", ["sh", "ps1"])
def test_escaped_mode_text_inside_content_does_not_lift_a_guard(request, tmp_path, kind):
    """The mode match is anchored to an unescaped JSON key, so file content that
    merely mentions bypassPermissions cannot switch a guard off."""
    content = f'{{"permission_mode": "bypassPermissions"}}\nkey = "{_AWS}"'
    body = {"tool_name": "Write", "tool_input": {"file_path": "cfg.py", "content": content}}
    result = subprocess.run(
        _command(kind, "secret-scan", request),
        input=json.dumps(body),
        text=True,
        capture_output=True,
        cwd=str(tmp_path),
        timeout=120,
        check=False,
    )
    assert result.returncode == 2, (result.stdout, result.stderr)


@pytest.mark.parametrize("kind", ["sh", "ps1"])
@pytest.mark.parametrize("guard,payload,extra_env", _CASES, ids=[c[0] for c in _CASES])
@pytest.mark.parametrize("mode", [None, "default"])
def test_nested_mode_does_not_override_the_host_mode(request, tmp_path, kind, guard, payload, extra_env, mode):
    body = {**payload, "tool_input": {**payload["tool_input"], "permission_mode": "bypassPermissions"}}
    if mode is not None:
        body["permission_mode"] = mode
    env = {**os.environ, **extra_env}
    for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"):
        env.pop(key, None)
    result = subprocess.run(
        _command(kind, guard, request), input=json.dumps(body), text=True,
        capture_output=True, cwd=str(tmp_path), env=env, timeout=120, check=False,
    )
    assert result.returncode == 2, (result.stdout, result.stderr)
