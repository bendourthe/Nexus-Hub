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
import shutil
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
    assert 'Next: python "' in result.stderr and "edit_guard.py\" diff " in result.stderr, "no helper command"
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


@pytest.mark.parametrize("command", [
    "Set-Content -Path deck.pptx -Value x",
    "'x' | Out-File deck.pptx",
    "sed -i s/a/b/ deck.pptx",
    "curl -o deck.pptx https://example.invalid/x",
    "dd if=other.pptx of=deck.pptx",
    "cd .. && cp work/other.pptx work/deck.pptx",
    "python -c \"from pptx import Presentation; Presentation('deck.pptx').save('deck.pptx')\"",
])
def test_deep_pass_writer_routes_are_blocked(run, work, command):
    """Writers the Phase 9 adversarial pass found unparsed: each must now block outside a worktree."""
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    _user_edits(deck)
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    result = run(_payload("PreToolUse", "Bash", work, command=command), work)
    assert result.returncode == 2, (command, result.stderr)


@pytest.mark.parametrize("command", [
    "Push-Location sub; Set-Content ../deck.pptx x",
    "Set-Content -Path:deck.pptx -Value x",
    "pwsh -Command Set-Content deck.pptx x",
    "Invoke-WebRequest -Uri https://example.invalid/x -OutFile deck.pptx",
    "New-Item -Force deck.pptx -Value x",
    "[IO.File]::WriteAllText('deck.pptx','x')",
    "curl -Lo deck.pptx https://example.invalid/x",
    "wget -qO deck.pptx https://example.invalid/x",
    "(cd sub && cp ../other.pptx ../deck.pptx)",
    "bash -c 'cp other.pptx deck.pptx'",
    "perl -pi -e 's/a/b/' deck.pptx",
    "python < gen_lit.py",
])
def test_deep_pass_cycle2_writer_routes_are_blocked(run, work, command):
    (work / "sub").mkdir()
    (work / "gen_lit.py").write_text("import shutil\nshutil.copy('other.pptx', 'deck.pptx')\n", encoding="utf-8")
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    _user_edits(deck)
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    result = run(_payload("PreToolUse", "Bash", work, command=command), work)
    assert result.returncode == 2, (command, result.stderr)


def test_a_script_that_only_reads_a_file_never_re_records_it(run, work):
    """A user save during a script that merely reads the file must stay a user edit."""
    deck = work / "deck.pptx"
    (work / "reader.py").write_text("from pptx import Presentation\nprint(Presentation('deck.pptx'))\n",
                                    encoding="utf-8")
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    command = "python reader.py"
    assert run(_payload("PreToolUse", "Bash", work, command=command), work).returncode == 0
    _user_edits(deck)
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    run(_payload("PostToolUse", "Bash", work, command=command), work)
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 2


def test_a_generator_rerun_onto_its_own_output_is_re_recorded(run, work):
    """A script that visibly saves its own recorded output: the agent's change, re-recorded."""
    deck = work / "deck.pptx"
    (work / "build.py").write_text("OUT = 'deck.pptx'\n\ndef main(prs):\n    prs.save(OUT)\n", encoding="utf-8")
    run(_payload("PostToolUse", "Write", work, path=deck), work)
    command = "python build.py"
    assert run(_payload("PreToolUse", "Bash", work, command=command), work).returncode == 0
    _deck(deck, "agent version", "regenerated")
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    run(_payload("PostToolUse", "Bash", work, command=command), work)
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 0


def test_a_recorded_changed_untracked_file_in_a_repository_still_blocks(run, tmp_path):
    """Git history holds nothing for an untracked file, so a user edit there is the user's alone."""
    repo = _git_repo(tmp_path / "fresh")
    deck = repo / "deck.pptx"
    _deck(deck, "agent version")
    run(_payload("PostToolUse", "Read", repo, path=deck), repo)
    _user_edits(deck)
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    assert run(_payload("PreToolUse", "Write", repo, path=deck), repo).returncode == 2


def test_an_unrecorded_untracked_file_in_a_repository_only_warns(run, tmp_path):
    """Build logs and ignored outputs are overwritten constantly; blocking them stalls ordinary work."""
    repo = _git_repo(tmp_path / "fresh")
    log = repo / "build.log"
    log.write_text("old build output\n", encoding="utf-8")
    result = run(_payload("PreToolUse", "Bash", repo, command="npm run build > build.log 2>&1"), repo)
    assert result.returncode == 0
    assert "WARNING (git worktree, not blocked)" in result.stderr


def test_a_script_that_copies_from_a_file_never_re_records_it(run, work):
    """A copy SOURCE is not a write: a user save during the copy stays a user edit."""
    deck = work / "deck.pptx"
    (work / "backup.py").write_text("import shutil\nshutil.copy('deck.pptx', 'backup.pptx')\n", encoding="utf-8")
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    command = "python backup.py"
    assert run(_payload("PreToolUse", "Bash", work, command=command), work).returncode == 0
    _user_edits(deck)
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    run(_payload("PostToolUse", "Bash", work, command=command), work)
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 2


def test_a_hook_check_does_not_let_record_release_a_change(run, work, tmp_path):
    deck = work / "deck.pptx"
    (work / "reader.py").write_text("print(open('deck.pptx', 'rb').read(4))\n", encoding="utf-8")
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    run(_payload("PreToolUse", "Bash", work, command="python reader.py"), work)
    _user_edits(deck)
    assert _guard(tmp_path, work, "record", str(deck)).returncode == 3


def test_touch_does_not_turn_a_user_edit_into_the_agents(run, work):
    """A command that only touches a user-edited file must not re-baseline it."""
    deck = work / "deck.pptx"
    run(_payload("PostToolUse", "Read", work, path=deck), work)
    _user_edits(deck)
    later = deck.stat().st_mtime + 120
    os.utime(deck, (later, later))
    assert run(_payload("PreToolUse", "Bash", work, command="python -c \"print(1)\""), work).returncode == 0
    os.utime(deck, (later + 60, later + 60))  # the "touch"
    post = run(_payload("PostToolUse", "Bash", work, command="python -c \"print(1)\""), work)
    assert "not re-recorded" in post.stderr
    assert run(_payload("PreToolUse", "Write", work, path=deck), work).returncode == 2


def test_a_bare_git_folder_does_not_downgrade_a_block(run, work):
    (work / ".git").mkdir()
    assert run(_payload("PreToolUse", "Write", work, path=work / "deck.pptx"), work).returncode == 2


def test_working_from_the_home_folder_uses_the_default_store(run, tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    notes = home / "notes.pptx"
    _deck(notes, "agent version")
    extra = {"NEXUS_EDIT_GUARD_DIR": ""}
    assert run(_payload("PostToolUse", "Read", home, path=notes), home, extra).returncode == 0
    assert run(_payload("PreToolUse", "Write", home, path=notes), home, extra).returncode == 0


def test_existing_file_without_a_record_is_blocked(run, work):
    result = run(_payload("PreToolUse", "Write", work, path=work / "deck.pptx"), work)
    assert result.returncode == 2
    assert _MESSAGE in result.stderr


def test_new_file_and_unrelated_commands_pass(run, work):
    assert run(_payload("PreToolUse", "Write", work, path=work / "new.pptx"), work).returncode == 0
    assert run(_payload("PreToolUse", "Bash", work, command="ls -la"), work).returncode == 0


def _commit(repo: Path, tmp_path: Path, *names: str) -> None:
    """Commit files in a throwaway repository without the machine's own Git hooks."""
    no_hooks = tmp_path / "no-hooks"
    no_hooks.mkdir(exist_ok=True)
    git = ["git", "-C", str(repo), "-c", "user.name=Test User", "-c", "user.email=test@example.com",
           "-c", f"core.hooksPath={no_hooks}"]
    subprocess.run([*git, "add", *names], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "fixture"], check=True)


def test_inside_a_git_worktree_it_warns_and_passes(run, tmp_path):
    """A tracked file in a real work tree: history holds the user's last commit, so it only warns."""
    repo = _git_repo(tmp_path / "repo")
    deck = repo / "deck.pptx"
    _deck(deck, "agent version")
    _commit(repo, tmp_path, "deck.pptx")
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


def test_generator_script_that_copies_onto_the_edited_deck_is_blocked(run, work, tmp_path):
    """The incident path: the overwrite happens inside the script, not in the command line."""
    synced = tmp_path / "OneDrive"
    synced.mkdir()
    target = synced / "deck.pptx"
    script = work / "build_deck.py"
    script.write_text(f"import shutil\nshutil.copy('deck.pptx', r'{target}')\n", encoding="utf-8")
    command = "python build_deck.py"
    assert run(_payload("PreToolUse", "Bash", work, command=command), work).returncode == 0, "new target must pass"
    shutil.copy(work / "deck.pptx", target)
    assert run(_payload("PostToolUse", "Bash", work, command=command), work).returncode == 0
    _user_edits(target)
    later = target.stat().st_mtime + 120
    os.utime(target, (later, later))
    result = run(_payload("PreToolUse", "Bash", work, command=command), work)
    assert result.returncode == 2, result.stderr
    assert "deck.pptx" in result.stderr


def test_unrecorded_document_named_in_a_script_does_not_block(run, work):
    (work / "report.py").write_text("from pptx import Presentation\nPresentation('other.pptx')\n",
                                    encoding="utf-8")
    assert run(_payload("PreToolUse", "Bash", work, command="python report.py"), work).returncode == 0


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


@pytest.mark.parametrize("hooks_dir, skills_dir", [
    (".claude/hooks", ".claude/skills"),  # Claude Code: skill beside the hooks folder
    (".codex/hooks", ".agents/skills"),  # Codex: skills under the shared .agents folder
])
def test_installed_layouts_find_the_helper(request, work, tmp_path, hooks_dir, skills_dir):
    """An installed hook must find edit_guard.py where the installer puts the skill, not fall back."""
    layout = tmp_path / "installed"
    (layout / hooks_dir).mkdir(parents=True)
    for name in ("user-edit-guard.sh", "user-edit-guard.ps1"):
        (layout / hooks_dir / name).write_bytes((_HOOKS_DIR / name).read_bytes())
    helper_dir = layout / skills_dir / "user-edit-preservation" / "scripts"
    helper_dir.mkdir(parents=True)
    (helper_dir / "edit_guard.py").write_bytes(_HELPER.read_bytes())
    payload = json.dumps(_payload("PreToolUse", "Write", work, path=work / "deck.pptx"))
    for kind, command in (("sh", [request.getfixturevalue("bash_bin"), str(layout / hooks_dir / "user-edit-guard.sh")]),
                          ("ps1", [request.getfixturevalue("powershell_bin"), "-NoProfile", "-File",
                                   str(layout / hooks_dir / "user-edit-guard.ps1")])):
        proc = subprocess.run(command, input=payload, text=True, capture_output=True, cwd=str(work),
                              env=_env(tmp_path), timeout=180, check=False)
        assert proc.returncode == 2, (kind, proc.stderr)
        assert _MESSAGE in proc.stderr, (kind, proc.stderr)
        assert "not found" not in proc.stderr, (kind, proc.stderr)


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
