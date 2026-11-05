"""Exercise Settings guardrail switches through real Bash and PowerShell hooks."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
KEYS = {
    "git-guardrails": "block_dangerous_git",
    "secret-scan": "scan_secrets",
    "user-edit-guard": "protect_user_edits",
    "large-file-guard": "warn_large_files",
}


@pytest.fixture(
    params=[(name, kind) for name in KEYS for kind in ("sh", "ps1")],
    ids=lambda item: "-".join(item),
)
def hook(request, tmp_path: Path):
    """Each invocation receives a private home, store, and non-repository workdir."""
    name, kind = request.param
    shell = request.getfixturevalue("bash_bin" if kind == "sh" else "powershell_bin")
    prefix = [shell] if kind == "sh" else [shell, "-NoProfile", "-File"]
    prefix.append(str(HOOKS / f"{name}.{kind}"))
    home = tmp_path / "home"
    work = tmp_path / "work"
    home.mkdir()
    work.mkdir()
    target = work / "existing.py"
    target.write_text("original\n", encoding="utf-8")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("NEXUS_", "LARGE_FILE_"))
    }
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_EDIT_GUARD_DIR": str(tmp_path / "store"),
            "NEXUS_EDIT_GUARD_TIMEOUT_SECONDS": "60",
            "LARGE_FILE_MAX_LINES": "1",
            "LARGE_FILE_MAX_BYTES": "50000",
        }
    )
    tool_input = {"file_path": str(target), "content": "first\nsecond\nthird\n"}
    tool = "Write"
    if name == "git-guardrails":
        tool, tool_input = (
            "Bash",
            {"command": "git reset --hard", "description": "Reset"},
        )
    elif name == "secret-scan":
        tool_input["content"] = "key = '" + "AK" + "IA" + "1234567890ABCDEF" + "'"
    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "settings-switch",
        "cwd": str(work),
        "tool_name": tool,
        "tool_input": tool_input,
    }
    config = home / ".nexus-hub" / "guardrails.json"

    def invoke(body=None):
        text = (
            body
            if isinstance(body, str)
            else json.dumps(payload if body is None else body)
        )
        return subprocess.run(
            prefix,
            input=text,
            env=env,
            cwd=work,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=120,
            check=False,
        )

    def configure(value):
        config.parent.mkdir(exist_ok=True)
        config.write_text(
            value if isinstance(value, str) else json.dumps(value), encoding="utf-8"
        )

    return name, KEYS[name], work, invoke, configure, payload


def assert_protected(name: str, result: subprocess.CompletedProcess) -> None:
    if name == "large-file-guard":
        assert result.returncode == 0, result.stderr
        assert "Warning:" in result.stderr
    else:
        assert result.returncode == 2, result.stderr
        assert "BLOCKED" in result.stderr


@pytest.mark.parametrize(
    "value,enabled",
    [
        ("absent", True),
        ("missing", True),
        (True, True),
        (False, False),
        ("false", True),
        (0, True),
        (None, True),
        ("malformed", True),
        ("array", True),
        ("trailing", True),
    ],
)
def test_only_exact_false_disables(hook, value, enabled):
    name, key, _work, invoke, configure, _payload = hook
    if value == "missing":
        configure({})
    elif value == "malformed":
        configure('{"' + key + '":false')
    elif value == "array":
        configure([{key: False}])
    elif value == "trailing":
        configure(json.dumps({key: False}) + " trailing")
    elif value != "absent":
        configure({key: value})
    result = invoke()
    if enabled:
        assert_protected(name, result)
    else:
        assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_switch_is_read_again_on_the_next_invocation(hook):
    name, key, _work, invoke, configure, _payload = hook
    configure({key: True})
    assert_protected(name, invoke())
    configure({key: False})
    result = invoke()
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    configure({key: True})
    assert_protected(name, invoke())


def test_lookalike_key_does_not_disable(hook):
    name, key, _work, invoke, configure, _payload = hook
    configure({key.upper(): False})
    assert_protected(name, invoke())


def test_workspace_and_payload_cannot_choose_the_preferences(hook):
    name, key, work, invoke, _configure, payload = hook
    fake = work / ".nexus-hub"
    fake.mkdir()
    (fake / "guardrails.json").write_text(json.dumps({key: False}), encoding="utf-8")
    payload["guardrails"] = {key: False}
    payload["HOME"] = str(work)
    assert_protected(name, invoke(payload))


@pytest.mark.parametrize(
    "hook", [(name, kind) for name in KEYS if name != "large-file-guard" for kind in ("sh", "ps1")],
    indirect=True, ids=lambda item: "-".join(item),
)
@pytest.mark.parametrize("value", [True, False, "absent", "malformed", "true", 1, None])
def test_enabled_settings_guards_apply_in_full_access(hook, value):
    name, key, _work, invoke, configure, payload = hook
    if value == "malformed":
        configure('{"' + key + '":true')
    elif value != "absent":
        configure({key: value})
    payload["permission_mode"] = "bypassPermissions"
    result = invoke(payload)
    if value is False:
        assert result.returncode == 0, result.stderr
    else:
        assert_protected(name, result)


def test_nested_mode_cannot_lift_an_explicit_guard(hook):
    name, key, _work, invoke, configure, payload = hook
    configure({key: True})
    payload["permission_mode"] = "default"
    payload["tool_input"]["permission_mode"] = "bypassPermissions"
    assert_protected(name, invoke(payload))


@pytest.mark.parametrize(
    "hook", [("git-guardrails", "sh"), ("git-guardrails", "ps1")],
    indirect=True, ids=["git-guardrails-sh", "git-guardrails-ps1"],
)
@pytest.mark.parametrize("general,bypass,command,expected", [
    (True, False, "git reset --hard", 2),
    (False, True, "git reset --hard", 0),
    (False, True, "git commit --no-verify", 2),
    (True, False, "git commit --no-verify", 0),
])
def test_git_full_access_guards_are_independent(hook, general, bypass, command, expected):
    _name, _key, _work, invoke, configure, payload = hook
    configure({"block_dangerous_git": general, "block_git_bypass_flags": bypass})
    payload["permission_mode"] = "bypassPermissions"
    payload["tool_input"]["command"] = command
    result = invoke(payload)
    assert result.returncode == expected, result.stderr


@pytest.mark.parametrize("enabled", [True, False])
def test_malformed_payload_retains_existing_allow_behavior(hook, enabled):
    _name, key, _work, invoke, configure, _payload = hook
    configure({key: enabled})
    result = invoke("not JSON")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "hook",
    [("git-guardrails", "sh"), ("git-guardrails", "ps1")],
    indirect=True,
    ids=["git-guardrails-sh", "git-guardrails-ps1"],
)
def test_git_bypass_guard_remains_independent(hook):
    _name, _key, _work, invoke, configure, payload = hook
    configure({"block_dangerous_git": False, "block_git_bypass_flags": True})
    payload["tool_input"]["command"] = "git commit --no-verify -m test"
    result = invoke(payload)
    assert result.returncode == 2, result.stderr
    assert "skips git hooks" in result.stderr


@pytest.mark.parametrize(
    "hook",
    [("large-file-guard", "sh"), ("large-file-guard", "ps1")],
    indirect=True,
    ids=["large-file-guard-sh", "large-file-guard-ps1"],
)
def test_large_file_warning_preserves_unicode_filename(hook):
    _name, _key, work, invoke, _configure, payload = hook
    payload["tool_input"] = {
        "file_path": str(work / "caf\u00e9.py"),
        "content": "ma\u00f1ana\ndeuxi\u00e8me\n",
    }
    result = invoke(payload)
    assert result.returncode == 0, result.stderr
    assert "caf\u00e9.py" in result.stderr
    assert "Warning:" in result.stderr
