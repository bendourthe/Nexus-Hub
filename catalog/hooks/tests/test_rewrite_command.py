"""Tests for catalog/hooks/rewrite-command.{sh,ps1}.

The hook is a thin PreToolUse delegate: it asks
``python -m nexus_context_compressor rewrite`` and maps exit 0/1/2/3 onto
allow / passthrough / deny / ask. Missing Python or a failed import is
passthrough (exit 0, no decision JSON), never auto-allow.

Every assertion runs against both implementations via the ``run`` fixture.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "rewrite-command.sh"
_HOOK_PS1 = _HOOKS_DIR / "rewrite-command.ps1"
_ENGINE_SRC = Path(__file__).resolve().parents[3] / "extensions" / "nexus-context-compressor" / "src"


@pytest.fixture(params=["sh", "ps1"])
def run(request):
    if request.param == "sh":
        prefix = [request.getfixturevalue("bash_bin"), str(_HOOK_SH)]
    else:
        prefix = [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_HOOK_PS1),
        ]

    def _run(
        payload: dict | str,
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        body = payload if isinstance(payload, str) else json.dumps(payload)
        env = {**os.environ}
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(_ENGINE_SRC) + (os.pathsep + existing if existing else "")
        for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"):
            env.pop(key, None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix,
            input=body,
            text=True,
            capture_output=True,
            env=env,
            timeout=120,
            check=False,
        )

    return _run


def _payload(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def test_git_status_is_passthrough(run) -> None:
    proc = run(_payload("git status"))
    assert proc.returncode == 0
    assert "permissionDecision" not in proc.stdout


def test_empty_stdin_is_passthrough(run) -> None:
    proc = run("")
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_host_deny_emits_deny_decision(run, tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps({"permissions": {"deny": ["curl"]}}),
        encoding="utf-8",
    )
    proc = run(
        _payload("curl https://example.invalid"),
        {"CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    body = json.loads(proc.stdout)
    decision = body["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"
