"""Native Antigravity payloads deliver edit and attribution guards through both shells.

The official hooks contract uses toolCall, conversationId, workspacePaths and an
optional post error. Every test launches the real bridge and catalog shell hook
in an isolated home, with filesystem changes observed through the real helper.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
REPO = HOOKS.parents[1]
COMPAT = REPO / "scripts/lib/integrations/_cascade_hook_compat.py"
EDIT_GUARD = REPO / "catalog/skills/workflow/user-edit-preservation/scripts/edit_guard.py"
ATTRIBUTION = REPO / "scripts/nexus_git_attribution.py"
SESSION = "antigravity-real-conversation-1"


@pytest.fixture(params=["sh", "ps1"])
def child(request):
    if request.param == "sh":
        return lambda name: [request.getfixturevalue("bash_bin"), str(HOOKS / f"{name}.sh")]
    return lambda name: [
        request.getfixturevalue("powershell_bin"), "-NoProfile", "-ExecutionPolicy",
        "Bypass", "-File", str(HOOKS / f"{name}.ps1"),
    ]


@pytest.fixture
def work(tmp_path: Path):
    folder = tmp_path / "work"
    folder.mkdir()
    (tmp_path / "home").mkdir()
    (folder / "notes.txt").write_text("old\n", encoding="utf-8")
    return folder


def _env(tmp_path: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("NEXUS_")}
    env.update(
        HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"),
        NEXUS_HUB_HOME=str(tmp_path / "home/.nexus-hub"),
        NEXUS_EDIT_GUARD_SCRIPT=str(EDIT_GUARD),
        NEXUS_EDIT_GUARD_DIR=str(tmp_path / "store"),
        NEXUS_EDIT_GUARD_TIMEOUT_SECONDS="60",
        NEXUS_ATTRIBUTION_SCRIPT=str(ATTRIBUTION),
        NEXUS_ATTRIBUTION_TIMEOUT_SECONDS="60",
    )
    return env


def _payload(work: Path, tool: str, **args) -> dict:
    return {
        "toolCall": {"name": tool, "args": args}, "conversationId": SESSION,
        "workspacePaths": [str(work)],
    }


def _run(child, event: str, payload: dict, tmp_path: Path, cwd: Path, hook="user-edit-guard"):
    result = subprocess.run(
        [sys.executable, str(COMPAT), "antigravity", event, "--", *child(hook)],
        input=json.dumps(payload), text=True, capture_output=True, check=False,
        cwd=str(cwd), env=_env(tmp_path), timeout=120,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout), result


def _write(work: Path, tool="write_to_file") -> dict:
    if tool == "multi_replace_file_content":
        args = {"ReplacementChunks": [{"TargetContent": "old", "ReplacementContent": "new"}]}
    elif tool == "replace_file_content":
        args = {"TargetContent": "old", "ReplacementContent": "new"}
    else:
        args = {"CodeContent": "new\n", "Overwrite": True}
    return _payload(work, tool, TargetFile=str(work / "notes.txt"), **args)


def _read(child, work: Path, tmp_path: Path) -> None:
    output, _ = _run(
        child, "PostToolUse", _payload(work, "view_file", AbsolutePath=str(work / "notes.txt")),
        tmp_path, work,
    )
    assert output == {}


def _record_path(tmp_path: Path) -> Path:
    records = list((tmp_path / "store/records").glob("*.json"))
    assert len(records) == 1
    return records[0]


@pytest.mark.parametrize("tool", ["write_to_file", "replace_file_content", "multi_replace_file_content"])
def test_native_write_refuses_unread_existing_file(child, work, tmp_path, tool):
    output, result = _run(child, "PreToolUse", _write(work, tool), tmp_path, work)
    assert output["decision"] == "deny", (output, result.stderr)
    assert "never recorded" in result.stderr
    assert (work / "notes.txt").read_text(encoding="utf-8") == "old\n"


def test_native_read_records_and_allows_the_next_write(child, work, tmp_path):
    _read(child, work, tmp_path)
    output, result = _run(child, "PreToolUse", _write(work), tmp_path, work)
    assert output["decision"] == "allow", (output, result.stderr)
    assert not result.stderr
    intent_name = ".intent-" + hashlib.sha256(SESSION.encode()).hexdigest()[:16]
    assert (tmp_path / "store" / intent_name).is_file(), "the real conversation did not key the intent"


def test_native_user_change_after_read_is_refused(child, work, tmp_path):
    _read(child, work, tmp_path)
    (work / "notes.txt").write_text("user's own change\n", encoding="utf-8")
    output, result = _run(child, "PreToolUse", _write(work), tmp_path, work)
    assert output["decision"] == "deny", (output, result.stderr)
    assert (work / "notes.txt").read_text(encoding="utf-8") == "user's own change\n"


@pytest.mark.parametrize("error", [None, ""])
def test_native_successful_post_write_records_actual_bytes(child, work, tmp_path, error):
    _read(child, work, tmp_path)
    payload = _write(work)
    output, _ = _run(child, "PreToolUse", payload, tmp_path, work)
    assert output["decision"] == "allow"
    (work / "notes.txt").write_bytes(b"new\n")
    if error is not None:
        payload["error"] = error
    output, _ = _run(child, "PostToolUse", payload, tmp_path, work)
    assert output == {}
    record = json.loads(_record_path(tmp_path).read_text(encoding="utf-8"))
    assert record["sha256"] == hashlib.sha256(b"new\n").hexdigest()
    assert record["from"] == "write"
    next_output, _ = _run(child, "PreToolUse", _write(work), tmp_path, work)
    assert next_output["decision"] == "allow"


def test_native_failed_post_preserves_the_prior_baseline(child, work, tmp_path):
    _read(child, work, tmp_path)
    payload = _write(work)
    output, _ = _run(child, "PreToolUse", payload, tmp_path, work)
    assert output["decision"] == "allow"
    record_path = _record_path(tmp_path)
    before = record_path.read_bytes()
    (work / "notes.txt").write_text("user changed this during the failed tool\n", encoding="utf-8")
    payload["error"] = "write failed"
    output, _ = _run(child, "PostToolUse", payload, tmp_path, work)
    assert output == {}
    assert record_path.read_bytes() == before
    output, _ = _run(child, "PreToolUse", _write(work), tmp_path, work)
    assert output["decision"] == "deny"


def test_native_command_uses_declared_cwd_for_relative_destination(child, work, tmp_path):
    launch = tmp_path / "launch"
    launch.mkdir()
    payload = _payload(work, "run_command", CommandLine="printf new > notes.txt", Cwd=str(work))
    payload["workspacePaths"] = [str(launch)]
    output, _ = _run(child, "PreToolUse", payload, tmp_path, launch)
    assert output["decision"] == "deny"


@pytest.mark.parametrize("multiple_workspaces", [False, True])
def test_undeclared_command_cwd_keeps_the_helpers_process_directory(
    child, work, tmp_path, multiple_workspaces,
):
    _read(child, work, tmp_path)
    launch = tmp_path / "launch"
    launch.mkdir()
    (launch / "notes.txt").write_bytes(b"unread user file\n")
    payload = _payload(work, "run_command", CommandLine="printf new > notes.txt")
    if multiple_workspaces:
        second = tmp_path / "second"
        second.mkdir()
        payload["workspacePaths"].append(str(second))
    output, _ = _run(child, "PreToolUse", payload, tmp_path, launch)
    assert output["decision"] == "deny"
    assert (launch / "notes.txt").read_bytes() == b"unread user file\n"


def test_native_post_command_records_actual_destination(child, work, tmp_path):
    _read(child, work, tmp_path)
    payload = _payload(work, "run_command", CommandLine="printf new > notes.txt", Cwd=str(work))
    output, _ = _run(child, "PreToolUse", payload, tmp_path, work)
    assert output["decision"] == "allow"
    (work / "notes.txt").write_bytes(b"command wrote this\n")
    output, _ = _run(child, "PostToolUse", payload, tmp_path, work)
    assert output == {}
    record = json.loads(_record_path(tmp_path).read_text(encoding="utf-8"))
    assert record["sha256"] == hashlib.sha256(b"command wrote this\n").hexdigest()
    assert record["from"] == "command"


def test_native_commit_attribution_is_refused(child, work, tmp_path):
    trailer = "Co-Authored" + "-By: Claude <noreply@anthropic.com>"
    payload = _payload(
        work, "run_command", CommandLine=f'git commit -m "fix: x" -m "{trailer}"',
        Cwd=str(work),
    )
    output, result = _run(child, "PreToolUse", payload, tmp_path, work, hook="attribution-guard")
    assert output["decision"] == "deny", (output, result.stderr)
    assert (work / "notes.txt").read_text(encoding="utf-8") == "old\n"
