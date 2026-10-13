"""Cascade (Devin Desktop / Windsurf) delivery of the guards and approval capture.

v4.13.11 closes two ledger items on the Windsurf adapter:

- DF-5-v4132: `pre_user_prompt` now runs `approval-capture`, so `record create`
  can find the user's approval on Windsurf.
- WN-4-v4131: `user-edit-guard` and `attribution-guard` join the curated lists.

The payload fields were verified on 2026-10-10 against
https://docs.devin.ai/desktop/cascade/hooks: `trajectory_id` identifies the
conversation; `tool_info.command_line` / `cwd` (run events), `tool_info.file_path`
plus `edits[].old_string/new_string` (write events), `tool_info.file_path` (read
events), and `tool_info.user_prompt` (pre_user_prompt); exit 2 blocks a pre-hook.

Every test runs the real `_cascade_hook_compat.py` wrapper with a documented
Cascade payload and a real catalog hook as the child, parametrized over the `.sh`
and `.ps1` siblings, so each assertion is also a parity assertion.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
REPO = HOOKS.parents[1]
COMPAT = REPO / "scripts" / "lib" / "integrations" / "_cascade_hook_compat.py"
EDIT_GUARD = (
    REPO / "catalog" / "skills" / "workflow" / "user-edit-preservation" / "scripts" / "edit_guard.py"
)
ATTRIBUTION = REPO / "scripts" / "nexus_git_attribution.py"
SESSION = "cascade-trajectory-1"

sys.path.insert(0, str(REPO))
from scripts.lib.integrations.windsurf import _CASCADE_HOOKS


@pytest.fixture(params=["sh", "ps1"])
def child(request, bash_bin: str, powershell_bin: str):
    def _argv(hook: str) -> list[str]:
        if request.param == "sh":
            return [bash_bin, str(HOOKS / f"{hook}.sh")]
        return [powershell_bin, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                str(HOOKS / f"{hook}.ps1")]
    return _argv


def _env(home: Path, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("NEXUS_")}
    env.update(HOME=str(home), USERPROFILE=str(home))
    env.update(extra)
    return env


def _cascade(event: str, tool: str, child_argv: list[str], payload: dict, env: dict,
             cwd: Path) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(COMPAT), event, tool, "--", *child_argv]
    return subprocess.run(argv, input=json.dumps(payload), text=True, capture_output=True,
                          env=env, cwd=str(cwd), timeout=120, check=False)


# ----- registration -----------------------------------------------------------


def _registered(event: str) -> set[tuple[str, str]]:
    return set(_CASCADE_HOOKS.get(event, ()))


def test_curated_lists_carry_the_guards_and_capture() -> None:
    assert ("approval-capture.sh", "") in _registered("pre_user_prompt")
    assert ("user-edit-guard.sh", "Write") in _registered("pre_write_code")
    assert ("user-edit-guard.sh", "Write") in _registered("post_write_code")
    assert ("user-edit-guard.sh", "Bash") in _registered("pre_run_command")
    assert ("user-edit-guard.sh", "Bash") in _registered("post_run_command")
    assert ("user-edit-guard.sh", "Read") in _registered("post_read_code")
    assert ("attribution-guard.sh", "Bash") in _registered("pre_run_command")
    assert ("attribution-guard.sh", "Write") in _registered("pre_write_code")


# ----- DF-5: approval capture on pre_user_prompt -----------------------------


def test_pre_user_prompt_capture_stores_the_digest(child, tmp_path: Path) -> None:
    home = tmp_path / "home"
    scripts = home / ".nexus-hub" / "scripts"
    runs = home / ".nexus-hub" / "runs"
    repo = tmp_path / "repo"
    scripts.mkdir(parents=True)
    runs.mkdir(parents=True)
    repo.mkdir()
    shutil.copy(REPO / "scripts" / "completion_gate.py", scripts / "completion_gate.py")
    (runs / "abc.json").write_text(json.dumps({
        "schema": 1, "session_id": SESSION, "repo_root": str(repo),
        "plan": "docs/releases/v0/v0.2/plans/v0.2.0-demo.md"}), encoding="utf-8")
    payload = {"agent_action_name": "pre_user_prompt", "trajectory_id": SESSION,
               "execution_id": "turn-1", "tool_info": {"user_prompt": "Yes, push and merge."}}

    result = _cascade("pre_user_prompt", "", child("approval-capture"), payload,
                      _env(home), repo)

    assert result.returncode == 0, result.stderr
    store = runs / "prompts" / f"{hashlib.sha256(SESSION.encode()).hexdigest()}.jsonl"
    assert store.is_file(), "the Cascade prompt was not captured"
    entries = [json.loads(line) for line in store.read_text(encoding="utf-8").splitlines()]
    assert entries[0]["session"] == SESSION
    assert entries[0]["prompt"] == hashlib.sha256(b"Yes, push and merge.").hexdigest()


# ----- WN-4: attribution-guard on pre_run_command -----------------------------


def _attribution_env(home: Path) -> dict[str, str]:
    return _env(home, NEXUS_ATTRIBUTION_SCRIPT=str(ATTRIBUTION),
                NEXUS_ATTRIBUTION_TIMEOUT_SECONDS="60")


def test_attribution_trailer_in_a_cascade_commit_is_blocked(child, tmp_path: Path) -> None:
    trailer = "Co-Authored" + "-By: Claude <noreply@anthropic.com>"
    payload = {"agent_action_name": "pre_run_command", "trajectory_id": SESSION,
               "tool_info": {"command_line": f'git commit -m "fix: x" -m "{trailer}"',
                             "cwd": str(tmp_path)}}

    result = _cascade("pre_run_command", "Bash", child("attribution-guard"), payload,
                      _attribution_env(tmp_path), tmp_path)

    assert result.returncode == 2, (result.stdout, result.stderr)


def test_clean_cascade_commit_passes_attribution(child, tmp_path: Path) -> None:
    payload = {"agent_action_name": "pre_run_command", "trajectory_id": SESSION,
               "tool_info": {"command_line": 'git commit -m "fix: x"', "cwd": str(tmp_path)}}

    result = _cascade("pre_run_command", "Bash", child("attribution-guard"), payload,
                      _attribution_env(tmp_path), tmp_path)

    assert result.returncode == 0, (result.stdout, result.stderr)


# ----- WN-4: user-edit-guard on read / write events ---------------------------


def _guard_env(home: Path) -> dict[str, str]:
    return _env(home, NEXUS_EDIT_GUARD_SCRIPT=str(EDIT_GUARD),
                NEXUS_EDIT_GUARD_DIR=str(home / "store"),
                NEXUS_EDIT_GUARD_TIMEOUT_SECONDS="60")


def _write_payload(path: Path) -> dict:
    return {"agent_action_name": "pre_write_code", "trajectory_id": SESSION,
            "tool_info": {"file_path": str(path),
                          "edits": [{"old_string": "old", "new_string": "new"}]}}


def test_unread_existing_file_write_is_blocked_outside_git(child, tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    target = work / "notes.txt"
    target.write_text("old\n", encoding="utf-8")

    result = _cascade("pre_write_code", "Write", child("user-edit-guard"),
                      _write_payload(target), _guard_env(tmp_path), work)

    assert result.returncode == 2, (result.stdout, result.stderr)


def test_post_read_record_lets_the_next_write_through(child, tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    target = work / "notes.txt"
    target.write_text("old\n", encoding="utf-8")
    env = _guard_env(tmp_path)
    read = {"agent_action_name": "post_read_code", "trajectory_id": SESSION,
            "tool_info": {"file_path": str(target)}}

    recorded = _cascade("post_read_code", "Read", child("user-edit-guard"), read, env, work)
    result = _cascade("pre_write_code", "Write", child("user-edit-guard"),
                      _write_payload(target), env, work)

    assert recorded.returncode == 0, recorded.stderr
    assert result.returncode == 0, (result.stdout, result.stderr)


def test_user_change_after_the_read_is_blocked(child, tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    target = work / "notes.txt"
    target.write_text("old\n", encoding="utf-8")
    env = _guard_env(tmp_path)
    read = {"agent_action_name": "post_read_code", "trajectory_id": SESSION,
            "tool_info": {"file_path": str(target)}}
    _cascade("post_read_code", "Read", child("user-edit-guard"), read, env, work)
    target.write_text("old\nthe user's own line\n", encoding="utf-8")

    result = _cascade("pre_write_code", "Write", child("user-edit-guard"),
                      _write_payload(target), env, work)

    assert result.returncode == 2, (result.stdout, result.stderr)
