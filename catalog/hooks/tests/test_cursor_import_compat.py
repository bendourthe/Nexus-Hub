"""Regression tests for Cursor importing Nexus-Hub's Claude Code hooks.

Cursor can load ``~/.claude/settings.json`` when third-party configuration is
enabled. Unlike Claude Code, Cursor requires a successful hook to write one JSON
object to stdout. These tests pin the compatibility launcher's cross-consumer
contract for every Nexus-Hub hook registered under ``PreToolUse``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_COMPAT = _HOOKS_DIR / "cursor-hook-compat.py"

_SHELL_HOOKS = (
    "attribution-guard",
    "compress-output",
    "escalation-trigger",
    "git-guardrails",
    "html-responsive-guard",
    "large-file-guard",
    "memory-store-guard",
    "old-version-docs-guard",
    "require-description",
    "require-powershell-description",
    "secret-scan",
    "user-edit-guard",
)

_PYTHON_HOOKS = (
    "format-bash-description.py",
    "format-powershell-description.py",
    "skill-guard.py",
)


@pytest.fixture()
def cursor_payload() -> str:
    return json.dumps(
        {
            "cursor_version": "test",
            "hook_event_name": "preToolUse",
            "tool_name": "Shell",
            "tool_input": {"command": "git status"},
            "cwd": ".",
        }
    )


@pytest.fixture()
def isolated_env(tmp_path: Path) -> dict[str, str]:
    env = {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
    env.pop("NEXUS_CONTEXT_COMPRESS", None)
    env.pop("NEXUS_PROTECTED_BRANCHES", None)
    return env


def _assert_cursor_allow(proc: subprocess.CompletedProcess[str], hook: str) -> None:
    assert proc.returncode == 0, f"{hook} blocked a benign Cursor call: {proc.stderr}"
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{hook} returned non-JSON stdout: {proc.stdout!r}") from exc
    permission = output.get("permission")
    nested = output.get("hookSpecificOutput", {}).get("permissionDecision")
    assert permission == "allow" or nested == "allow", output


@pytest.mark.parametrize("stem", _SHELL_HOOKS)
def test_cursor_imported_shell_hooks_return_json_allow(
    stem: str,
    cursor_payload: str,
    isolated_env: dict[str, str],
    tmp_path: Path,
    bash_bin: str,
    powershell_bin: str,
) -> None:
    sh = subprocess.run(
        [sys.executable, str(_COMPAT), bash_bin, str(_HOOKS_DIR / f"{stem}.sh")],
        input=cursor_payload,
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=isolated_env,
        timeout=180,
    )
    ps = subprocess.run(
        [
            sys.executable,
            str(_COMPAT),
            powershell_bin,
            "-NoProfile",
            "-File",
            str(_HOOKS_DIR / f"{stem}.ps1"),
        ],
        input=cursor_payload,
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=isolated_env,
        timeout=180,
    )
    _assert_cursor_allow(sh, f"{stem}.sh")
    _assert_cursor_allow(ps, f"{stem}.ps1")


@pytest.mark.parametrize("script", _PYTHON_HOOKS)
def test_cursor_imported_python_hooks_return_json_allow(
    script: str,
    cursor_payload: str,
    isolated_env: dict[str, str],
    tmp_path: Path,
) -> None:
    proc = subprocess.run(
        [sys.executable, str(_COMPAT), sys.executable, str(_HOOKS_DIR / script)],
        input=cursor_payload,
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=isolated_env,
        timeout=180,
    )
    _assert_cursor_allow(proc, script)


@pytest.mark.parametrize(
    ("host", "scope", "expected_runner", "expected_script"),
    (
        ("windows", "global", "powershell -NoProfile", "git-guardrails.ps1"),
        ("posix", "global", "bash ", "git-guardrails.sh"),
        ("posix", "workspace", "bash ", "git-guardrails.sh"),
    ),
)
def test_settings_migration_is_host_aware_idempotent_and_scoped(
    host: str,
    scope: str,
    expected_runner: str,
    expected_script: str,
    tmp_path: Path,
) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "bash .claude/hooks/git-guardrails.sh",
                                },
                                {
                                    "type": "command",
                                    "command": "bash .claude/hooks/user-custom.sh",
                                },
                                {
                                    "type": "command",
                                    "command": "bash /opt/custom/git-guardrails.sh",
                                },
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    command = [
        sys.executable,
        str(_COMPAT),
        "--rewrite-settings",
        str(settings),
        "--catalog-hooks-dir",
        str(_HOOKS_DIR),
        "--host",
        host,
        "--scope",
        scope,
    ]
    first = subprocess.run(command, text=True, capture_output=True, timeout=30)
    assert first.returncode == 0, first.stderr
    once = settings.read_text(encoding="utf-8")
    second = subprocess.run(command, text=True, capture_output=True, timeout=30)
    assert second.returncode == 0, second.stderr
    assert settings.read_text(encoding="utf-8") == once

    migrated = json.loads(once)["hooks"]["PreToolUse"][0]["hooks"]
    nexus_command = migrated[0]["command"]
    assert "cursor-hook-compat.py" in nexus_command
    assert expected_runner in nexus_command
    assert expected_script in nexus_command
    expected_base = (
        (settings.parent / "hooks").resolve().as_posix()
        if scope == "global"
        else ".claude/hooks"
    )
    assert expected_base in nexus_command
    assert migrated[1]["command"] == "bash .claude/hooks/user-custom.sh"
    assert migrated[2]["command"] == "bash /opt/custom/git-guardrails.sh"


def test_non_cursor_payload_preserves_hook_stdout_and_exit_code(tmp_path: Path) -> None:
    child = tmp_path / "claude-hook.py"
    child.write_text(
        "import sys\nsys.stdout.write('claude output')\nsys.stderr.write('claude error')\nraise SystemExit(7)\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(_COMPAT), sys.executable, str(child)],
        input='{"hook_event_name":"PreToolUse"}',
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 7
    assert proc.stdout == "claude output"
    assert proc.stderr == "claude error"


@pytest.mark.parametrize(("host", "extension"), (("windows", ".ps1"), ("posix", ".sh")))
def test_full_settings_template_migrates_to_existing_host_scripts(
    host: str, extension: str, tmp_path: Path
) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        (_HOOKS_DIR / "settings.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(_COMPAT),
            "--rewrite-settings",
            str(settings),
            "--catalog-hooks-dir",
            str(_HOOKS_DIR),
            "--host",
            host,
            "--scope",
            "global",
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    migrated = json.loads(settings.read_text(encoding="utf-8"))
    commands = [
        handler["command"]
        for groups in migrated["hooks"].values()
        for group in groups
        for handler in group["hooks"]
    ]
    assert commands
    assert all("cursor-hook-compat.py" in command for command in commands)
    for command in commands:
        final_path = command.rsplit('"', 2)[1]
        final_name = Path(final_path).name
        assert (_HOOKS_DIR / final_name).exists(), command
        if final_name.endswith((".sh", ".ps1")):
            assert final_name.endswith(extension), command


@pytest.mark.parametrize("shell_kind", ("bash", "powershell"))
def test_cursor_dangerous_git_command_still_blocks(
    shell_kind: str,
    isolated_env: dict[str, str],
    tmp_path: Path,
    bash_bin: str,
    powershell_bin: str,
) -> None:
    if shell_kind == "bash":
        hook_command = [bash_bin, str(_HOOKS_DIR / "git-guardrails.sh")]
    else:
        hook_command = [
            powershell_bin,
            "-NoProfile",
            "-File",
            str(_HOOKS_DIR / "git-guardrails.ps1"),
        ]
    payload = json.dumps(
        {
            "cursor_version": "test",
            "hook_event_name": "beforeShellExecution",
            "command": "git reset --hard",
            "cwd": ".",
        }
    )
    proc = subprocess.run(
        [sys.executable, str(_COMPAT), *hook_command],
        input=payload,
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=isolated_env,
        timeout=30,
    )
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["permission"] == "deny"
    assert "BLOCKED" in proc.stderr


@pytest.mark.parametrize("kind", ["sh", "ps1"])
def test_cursor_native_generic_events_record_and_protect_edits(request, tmp_path, kind):
    """A native Cursor read updates the actual ledger before a later edit check."""
    home = tmp_path / "home"
    work = tmp_path / "work"
    home.mkdir()
    work.mkdir()
    target = work / "existing.txt"
    target.write_text("original\n", encoding="utf-8")
    config = home / ".nexus-hub/guardrails.json"
    config.parent.mkdir()
    config.write_text('{"protect_user_edits":true}', encoding="utf-8")
    helper = _HOOKS_DIR.parents[1] / "catalog/skills/workflow/user-edit-preservation/scripts/edit_guard.py"
    env = {key: value for key, value in os.environ.items() if not key.startswith("NEXUS_")}
    env.update(HOME=str(home), USERPROFILE=str(home), NEXUS_EDIT_GUARD_DIR=str(tmp_path / "store"), NEXUS_EDIT_GUARD_SCRIPT=str(helper), NEXUS_EDIT_GUARD_TIMEOUT_SECONDS="60")
    shell = request.getfixturevalue("bash_bin" if kind == "sh" else "powershell_bin")
    child = [shell, str(_HOOKS_DIR / f"user-edit-guard.{kind}")] if kind == "sh" else [shell, "-NoProfile", "-File", str(_HOOKS_DIR / "user-edit-guard.ps1")]
    def invoke(event, tool):
        payload = {"cursor_version": "3.24.18", "conversation_id": "native-edit-ledger", "hook_event_name": event, "tool_name": tool, "tool_input": {"path": str(target), "content": "replacement\n"}, "cwd": str(work)}
        return subprocess.run([sys.executable, str(_COMPAT), *child], input=json.dumps(payload), text=True, capture_output=True, cwd=work, env=env, timeout=120, check=False)
    read = invoke("postToolUse", "Read")
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout) == {}
    target.write_text("user changes\n", encoding="utf-8")
    blocked = invoke("preToolUse", "Write")
    assert blocked.returncode == 2, blocked.stderr
    assert "BLOCKED" in json.loads(blocked.stdout)["user_message"]
    assert "user changes" not in blocked.stdout + blocked.stderr


@pytest.mark.parametrize("kind", ["sh", "ps1"])
def test_cursor_native_generic_secret_scan_blocks_and_switch_disables(request, tmp_path, kind):
    config = tmp_path / ".nexus-hub/guardrails.json"
    config.parent.mkdir()
    shell = request.getfixturevalue("bash_bin" if kind == "sh" else "powershell_bin")
    child = [shell, str(_HOOKS_DIR / f"secret-scan.{kind}")] if kind == "sh" else [shell, "-NoProfile", "-File", str(_HOOKS_DIR / "secret-scan.ps1")]
    payload = {"cursor_version": "3.24.18", "hook_event_name": "preToolUse", "tool_name": "Write", "tool_input": {"path": str(tmp_path / "keys.py"), "content": "key = '" + "AK" + "IA" + "1234567890ABCDEF" + "'"}, "cwd": str(tmp_path)}
    env = {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
    for enabled, expected in [(True, 2), (False, 0)]:
        config.write_text(json.dumps({"scan_secrets": enabled}), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(_COMPAT), *child], input=json.dumps(payload), text=True, capture_output=True, cwd=tmp_path, env=env, timeout=120, check=False)
        assert proc.returncode == expected, proc.stderr
        assert json.loads(proc.stdout)["permission"] == ("deny" if enabled else "allow")
