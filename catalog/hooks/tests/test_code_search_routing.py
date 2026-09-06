"""Cross-shell tests for the code-search-routing PreToolUse hook."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent


def _payload(tool_name: str, **tool_input: object) -> str:
    return json.dumps({"tool_name": tool_name, "tool_input": tool_input})


@pytest.fixture(params=["sh", "ps1"])
def run_hook(request, bash_bin: str, powershell_bin: str):
    suffix = request.param
    argv = (
        [bash_bin, str(_HOOKS_DIR / "code-search-routing.sh")]
        if suffix == "sh"
        else [
            powershell_bin,
            "-NoProfile",
            "-File",
            str(_HOOKS_DIR / "code-search-routing.ps1"),
        ]
    )

    def run(payload: str, env_overrides: dict[str, str] | None = None):
        env = {**os.environ}
        for key in (
            "NEXUS_DISABLED_HOOKS",
            "NEXUS_HOOK_PROFILE",
            "NEXUS_CODE_SEARCH_ROUTING",
            "NEXUS_CODE_SEARCH_ROUTING_DEBUG",
        ):
            env.pop(key, None)
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            argv,
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            timeout=60,
        )

    return run


@pytest.mark.parametrize(
    ("tool_name", "tool_input", "indexed_tool"),
    [
        ("Grep", {"pattern": "resolve_config", "path": "src"}, "search_code"),
        ("Glob", {"pattern": "**/*.py", "path": "src"}, "code_search"),
        ("Bash", {"command": "grep -R resolve_config src"}, "search_code"),
        ("Bash", {"command": "rg resolve_config src"}, "search_code"),
        ("Bash", {"command": "find src -name '*.py'"}, "code_search"),
        ("Bash", {"command": "cat src/app.py | grep resolve_config"}, "search_code"),
    ],
)
def test_search_calls_emit_indexed_redirect(
    run_hook, tool_name: str, tool_input: dict[str, object], indexed_tool: str
) -> None:
    result = run_hook(_payload(tool_name, **tool_input))
    assert result.returncode == 0
    assert result.stdout == ""
    assert "code-search-routing" in result.stderr
    assert indexed_tool in result.stderr
    assert "root=\"<repo>\"" in result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "git status",
        "cat README.md",
        "find build -type f -delete",
        "python -m pytest -q",
        "echo grep",
    ],
)
def test_unrelated_bash_command_is_silent(run_hook, command: str) -> None:
    result = run_hook(_payload("Bash", command=command))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_read_is_never_intercepted(run_hook) -> None:
    result = run_hook(_payload("Read", file_path="src/app.py"))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_hard_block_is_explicit_and_match_scoped(run_hook) -> None:
    blocked = run_hook(
        _payload("Grep", pattern="needle"),
        {"NEXUS_CODE_SEARCH_ROUTING": "block"},
    )
    unrelated = run_hook(
        _payload("Bash", command="git status"),
        {"NEXUS_CODE_SEARCH_ROUTING": "block"},
    )
    assert blocked.returncode == 2
    assert "Blocked by NEXUS_CODE_SEARCH_ROUTING=block" in blocked.stderr
    assert unrelated.returncode == 0
    assert unrelated.stderr == ""


@pytest.mark.parametrize(
    "control",
    [
        {"NEXUS_DISABLED_HOOKS": "other,code-search-routing,another"},
        {"NEXUS_HOOK_PROFILE": "minimal"},
    ],
)
def test_disable_controls_suppress_hook(run_hook, control: dict[str, str]) -> None:
    result = run_hook(_payload("Grep", pattern="needle"), control)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize("payload", ["", "not-json", "{}"])
def test_empty_or_malformed_stdin_fails_open(run_hook, payload: str) -> None:
    result = run_hook(payload)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_debug_mode_logs_classification_without_blocking(run_hook) -> None:
    result = run_hook(
        _payload("Bash", command="git status"),
        {"NEXUS_CODE_SEARCH_ROUTING_DEBUG": "1"},
    )
    assert result.returncode == 0
    assert "no conservative match" in result.stderr


def test_network_blocked_environment_does_not_change_behavior(run_hook) -> None:
    blocked_network = {
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "socks5://127.0.0.1:9",
        "NO_PROXY": "",
    }
    result = run_hook(_payload("Grep", pattern="needle"), blocked_network)
    assert result.returncode == 0
    assert "search_code" in result.stderr

    forbidden = (
        "curl",
        "wget",
        "invoke-webrequest",
        "invoke-restmethod",
        "system.net",
        "http://",
        "https://",
    )
    for suffix in ("sh", "ps1"):
        source = (_HOOKS_DIR / f"code-search-routing.{suffix}").read_text(
            encoding="utf-8"
        ).lower()
        assert not any(token in source for token in forbidden)
