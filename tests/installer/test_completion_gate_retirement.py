"""Real installer coverage for retiring the completion-gate Stop registration.

The gate was removed from the default install on 2026-10-28
(docs/decisions/implemented/tooling/2026-10-28-remove-completion-gate-stop-default.md).
A machine that already carries the registration must lose it on the next install,
while every handler the user added (including one that merely shares a name) stays.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.ci.verify_scenarios import isolated_environment
from tests.installer.test_managed_hook_upgrade import (
    _native_installer,
    _run_installer,
    _write_parser_override_bash_env,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

USER_STOP = {"type": "command", "command": "my-stop-check --keep"}
LOOKALIKE = {"type": "command", "command": "bash /opt/mine/completion-gate.sh"}


def _commands(settings: dict, event: str) -> list[str]:
    return [
        str(hook.get("command", ""))
        for entry in settings["hooks"].get(event, [])
        for hook in entry.get("hooks", [])
    ]


def _legacy_settings() -> dict:
    return {
        "hooks": {
            "Stop": [
                # The shipped template shape: gate first, then siblings in one group.
                {"matcher": "", "hooks": [
                    {"type": "command", "command": "bash .claude/hooks/completion-gate.sh"},
                    USER_STOP,
                ]},
                # Shapes the installer writes after host conversion.
                {"matcher": "", "hooks": [
                    {"type": "command", "command": 'bash "/home/u/.claude/hooks/completion-gate.sh"'},
                ]},
                {"matcher": "", "hooks": [
                    {"type": "command",
                     "command": 'powershell -NoProfile -File "C:\\Users\\u\\.claude\\hooks\\completion-gate.ps1"'},
                ]},
                {"matcher": "", "hooks": [LOOKALIKE]},
            ],
            "SessionEnd": [
                {"matcher": "", "hooks": [
                    {"type": "command", "command": "bash .claude/hooks/completion-gate.sh"},
                ]},
            ],
        },
        "customUserSetting": {"preserve": True},
    }


def _prepare(tmp_path: Path, extra_env: dict[str, str] | None = None):
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    (workspace / ".claude").mkdir(parents=True)
    home.mkdir()
    settings_path = workspace / ".claude" / "settings.json"
    settings_path.write_text(json.dumps(_legacy_settings()), encoding="utf-8")
    boundary = tmp_path / "fixture-env"
    boundary.mkdir()
    env = isolated_environment(boundary)
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "CLAUDE_CONFIG_DIR": str(home / ".claude"),
            "NEXUS_HUB_HOME": str(home / ".nexus-hub"),
        }
    )
    if extra_env:
        env.update(extra_env)
    return settings_path, _native_installer(workspace), env


def _assert_retired(settings_path: Path) -> None:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    stop = _commands(settings, "Stop")
    assert not [c for c in stop if "hooks/completion-gate" in c.replace("\\", "/")], stop
    # Only the handlers we own were removed.
    assert USER_STOP["command"] in stop
    assert LOOKALIKE["command"] in stop
    assert any("usage-guard" in c for c in stop), "the rest of the managed Stop chain is still registered"
    # An event that held only the retired handler is dropped, not left empty.
    assert "SessionEnd" not in settings["hooks"] or all(
        "completion-gate" not in c for c in _commands(settings, "SessionEnd")
    )
    assert settings["customUserSetting"] == {"preserve": True}


def test_existing_settings_lose_the_completion_gate_stop_entry(tmp_path: Path) -> None:
    settings_path, command, env = _prepare(tmp_path)
    _run_installer(command, env, 1)
    _assert_retired(settings_path)
    first = settings_path.read_text(encoding="utf-8")
    _run_installer(command, env, 2)
    assert settings_path.read_text(encoding="utf-8") == first


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer coverage (python fallback path)")
def test_posix_python_fallback_also_retires_the_entry(tmp_path: Path) -> None:
    bash_env = _write_parser_override_bash_env(tmp_path / "no-jq.bash")
    settings_path, command, env = _prepare(tmp_path, {"BASH_ENV": str(bash_env)})
    _run_installer(command, env, 1)
    _assert_retired(settings_path)


def test_fresh_template_registers_no_completion_gate() -> None:
    template = json.loads((REPO_ROOT / "catalog" / "hooks" / "settings.json").read_text(encoding="utf-8"))
    every = [c for event in template["hooks"] for c in _commands(template, event)]
    assert not [c for c in every if "completion-gate" in c], every
    assert any("approval-capture" in c for c in _commands(template, "UserPromptSubmit"))
