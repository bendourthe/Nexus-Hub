"""Tests for catalog/hooks/user-edit-guard.{sh,ps1} (v4.13.1 Phase 6).

The hook is a thin adapter over the user-edit-preservation skill's
`edit_guard.py hook`. It must block a change onto a user-edited file outside a
git worktree, warn inside one, release only after `diff` then `accept`, and
never mistake the agent's own Bash-driven change for a user edit. When the
helper cannot decide in time it must fail closed outside a worktree.

Every test runs against BOTH implementations via the `run` fixture, so the
suite is also the .sh/.ps1 parity check; `test_both_print_identical_stderr`
compares the two outputs directly.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_user_edit_guard.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "user-edit-guard.sh"
_HOOK_PS1 = _HOOKS_DIR / "user-edit-guard.ps1"
_HELPER = (_HOOKS_DIR.parent / "skills" / "workflow" / "user-edit-preservation"
           / "scripts" / "edit_guard.py")
_MESSAGE = "This file changed since your last read or write, or was never recorded."
_USER_TEXT = "user-only-paragraph-that-must-never-be-echoed"


def _env(tmp_path: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {**os.environ, "NEXUS_EDIT_GUARD_DIR": str(tmp_path / "store"),
           "NEXUS_EDIT_GUARD_TIMEOUT_SECONDS": "60", "HOME": str(tmp_path / "home"),
           "USERPROFILE": str(tmp_path / "home")}
    for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "NEXUS_EDIT_GUARD_SCRIPT",
                "NEXUS_EDIT_GUARD_SESSION"):
        env.pop(key, None)
    env.update(extra or {})
    return env


def _prefix(kind: str, request) -> list[str]:
    if kind == "sh":
        return [request.getfixturevalue("bash_bin"), str(_HOOK_SH)]
    return [request.getfixturevalue("powershell_bin"), "-NoProfile", "-File", str(_HOOK_PS1)]


@pytest.fixture(params=["sh", "ps1"])
def run(request, tmp_path: Path):
    """Invoke either implementation from a work folder outside any git repository."""
    prefix = _prefix(request.param, request)
    (tmp_path / "home").mkdir(exist_ok=True)

    def _run(payload: dict | str, cwd: Path, extra: dict[str, str] | None = None
             ) -> subprocess.CompletedProcess:
        body = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(prefix, input=body, text=True, capture_output=True,
                              cwd=str(cwd), env=_env(tmp_path, extra), timeout=180, check=False)

    return _run


def _guard(tmp_path: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(_HELPER), *args], cwd=str(cwd), text=True,
                          capture_output=True, env=_env(tmp_path), timeout=60, check=False)


def _payload(event: str, tool: str, cwd: Path, *, path: Path | None = None,
             command: str | None = None, session: str = "S1") -> dict:
    tool_input = {"file_path": str(path)} if path is not None else {"command": command}
    return {"hook_event_name": event, "tool_name": tool, "session_id": session,
            "cwd": str(cwd), "tool_input": tool_input}


def _deck(target: Path, *lines: str) -> None:
    """A minimal Office-style archive: the guard fingerprints its content parts."""
    body = "".join(f"<a:t>{line}</a:t>" for line in lines)
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("ppt/slides/slide1.xml", f"<p:sld>{body}</p:sld>")


@pytest.fixture()
def work(tmp_path: Path) -> Path:
    folder = tmp_path / "work"
    folder.mkdir()
    _deck(folder / "deck.pptx", "agent version")
    _deck(folder / "other.pptx", "another deck")
    return folder


def _user_edits(target: Path) -> None:
    _deck(target, "agent version", _USER_TEXT)


def _git_repo(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


def test_write_onto_user_edited_file_is_blocked_outside_a_worktree(run, work):
    deck = work / "deck.pptx"
    assert run(_payload("PostToolUse", "Read", work, path=deck), work).returncode == 0
    _user_edits(deck)
    result = run(_payload("PreToolUse", "Write", work, path=deck), work)
    assert result.returncode == 2
    assert "[user-edit-guard] BLOCKED" in result.stderr and _MESSAGE in result.stderr
    assert "NEXUS_DISABLED_HOOKS=user-edit-guard" in result.stderr
    assert _USER_TEXT not in result.stderr + result.stdout, "file content was echoed"


def test_copy_onto_user_edited_file_is_blocked(run, work):
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    _user_edits(deck)
    result = run(_payload("PreToolUse", "Bash", work, command="cp other.pptx deck.pptx"), work)
    assert result.returncode == 2
    assert "deck.pptx" in result.stderr


@pytest.mark.parametrize("command", [
    "mv other.pptx deck.pptx",
    "Copy-Item -Path other.pptx -Destination deck.pptx",
    "echo replaced > deck.pptx",
    "python -c \"import shutil; shutil.copy('other.pptx', 'deck.pptx')\"",
])
def test_other_overwrite_routes_are_blocked(run, work, command):
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    _user_edits(deck)
    assert run(_payload("PreToolUse", "Bash", work, command=command), work).returncode == 2


def test_existing_file_without_a_record_is_blocked(run, work):
    result = run(_payload("PreToolUse", "Write", work, path=work / "deck.pptx"), work)
    assert result.returncode == 2
    assert _MESSAGE in result.stderr


def test_new_file_and_unrelated_commands_pass(run, work):
    assert run(_payload("PreToolUse", "Write", work, path=work / "new.pptx"), work).returncode == 0
    assert run(_payload("PreToolUse", "Bash", work, command="ls -la"), work).returncode == 0


def test_inside_a_git_worktree_it_warns_and_passes(run, tmp_path):
    repo = _git_repo(tmp_path / "repo")
    deck = repo / "deck.pptx"
    _deck(deck, "agent version")
    run(_payload("PostToolUse", "Read", repo, path=deck), repo)
    _user_edits(deck)
    result = run(_payload("PreToolUse", "Write", repo, path=deck), repo)
    assert result.returncode == 0
    assert "WARNING (git worktree, not blocked)" in result.stderr
    assert "additionalContext" in result.stdout


def test_accept_after_diff_releases_the_block(run, work, tmp_path):
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    _user_edits(deck)
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 2
    assert _guard(tmp_path, work, "accept", str(deck)).returncode == 3, "accept before diff must refuse"
    assert _guard(tmp_path, work, "diff", str(deck)).returncode == 0
    assert _guard(tmp_path, work, "accept", str(deck)).returncode == 0
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 0


def test_agents_own_bash_change_is_re_recorded_not_blamed_on_the_user(run, work):
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Write", work, path=deck), work)
    command = "python build_deck.py"
    assert run(_payload("PreToolUse", "Bash", work, command=command), work).returncode == 0
    _deck(deck, "agent version", "regenerated by the agent's script")
    assert run(_payload("PostToolUse", "Bash", work, command=command), work).returncode == 0
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 0


def test_formatter_rewrite_right_after_the_agents_write_is_not_a_user_edit(run, work):
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Write", work, path=deck), work)
    _deck(deck, "agent version", "reformatted by a parallel formatter hook")
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 0


def test_user_edit_after_the_settle_window_still_blocks(run, work):
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Write", work, path=deck), work)
    _user_edits(deck)
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 2


def test_post_read_of_a_changed_file_warns(run, work):
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    _user_edits(deck)
    result = run(_payload("PostToolUse", "Read", work, path=deck), work)
    assert result.returncode == 0
    assert "changed since your last read or write" in result.stderr


@pytest.mark.parametrize("body", ["", "not json", "[1, 2]", "{}"])
def test_malformed_or_absent_input_exits_zero(run, work, body):
    assert run(body, work).returncode == 0


def test_user_escape_disables_it_but_minimal_profile_does_not(run, work):
    payload = _payload("PreToolUse", "Write", work, path=work / "deck.pptx")
    assert run(payload, work, {"NEXUS_DISABLED_HOOKS": "user-edit-guard"}).returncode == 0
    assert run(payload, work, {"NEXUS_HOOK_PROFILE": "minimal"}).returncode == 2


@pytest.mark.parametrize("script, budget", [
    ("import time; time.sleep(30)\n", "1"),
    ("import sys; sys.exit(1)\n", "60"),
])
def test_helper_that_cannot_decide_fails_closed_outside_and_warns_inside(run, work, tmp_path, script, budget):
    helper = tmp_path / "stuck_helper.py"
    helper.write_text(script, encoding="utf-8")
    extra = {"NEXUS_EDIT_GUARD_SCRIPT": str(helper), "NEXUS_EDIT_GUARD_TIMEOUT_SECONDS": budget}
    outside = run(_payload("PreToolUse", "Write", work, path=work / "deck.pptx"), work, extra)
    assert outside.returncode == 2
    assert "Cannot verify this file" in outside.stderr

    repo = _git_repo(tmp_path / "repo2")
    inside = run(_payload("PreToolUse", "Write", repo, path=repo / "deck.pptx"), repo, extra)
    assert inside.returncode == 0
    assert "WARNING (git worktree, not blocked)" in inside.stderr

    post = run(_payload("PostToolUse", "Write", work, path=work / "deck.pptx"), work, extra)
    assert post.returncode == 0, "a post step must never block"


def test_both_print_identical_stderr(request, work, tmp_path):
    deck = work / "deck.pptx"
    _guard(tmp_path, work, "record", str(deck), "--from", "read")
    _user_edits(deck)
    results: dict[str, list[tuple[int, str]]] = {"sh": [], "ps1": []}
    for kind, outputs in results.items():
        for payload in (_payload("PreToolUse", "Write", work, path=deck),
                        _payload("PreToolUse", "Bash", work, command="cp other.pptx deck.pptx")):
            proc = subprocess.run(_prefix(kind, request), input=json.dumps(payload), text=True,
                                  capture_output=True, cwd=str(work), env=_env(tmp_path), timeout=180, check=False)
            outputs.append((proc.returncode, proc.stderr.replace("\r\n", "\n")))
    assert results["sh"] == results["ps1"]
    assert all(code == 2 for code, _ in results["sh"])
