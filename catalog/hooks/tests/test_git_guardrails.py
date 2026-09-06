"""Tests for catalog/hooks/git-guardrails.{sh,ps1}.

Covers:

  * the existing dangerous-pattern blocking (regression),
  * the opt-in protected-branch guard added for the develop+main workflow,
  * the v3.15.6 Phase 2 execution-indirection patterns (AC4): core.hooksPath and
    core.fsmonitor in both the inline `git -c key=value` form and the persistent
    `git config` form, which is group B of the canonical execution-trigger
    surface list in
    catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md,
  * the false-positive guards that matter for group B: a READ of the same key
    (`git config --get core.hooksPath`) and a benign `-c` option must both be
    allowed, or the guardrail becomes an obstacle to ordinary work.

Every test runs against BOTH the bash hook and its PowerShell sibling via the
`run` fixture, so the suite is also the .sh/.ps1 parity check. A missing
interpreter skips only that parameter.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_git_guardrails.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "git-guardrails.sh"
_HOOK_PS1 = _HOOKS_DIR / "git-guardrails.ps1"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="git-guardrails requires git on PATH"
)

_ALLOW = 0
_BLOCK = 2


@pytest.fixture(params=["sh", "ps1"])
def run(request):
    """Invoke either hook implementation with a PreToolUse Bash payload."""
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
        command: str, cwd: Path, env_extra: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_input": {"command": command}})
        env = {**os.environ}
        for key in ("NEXUS_PROTECTED_BRANCHES", "NEXUS_PROTECTED_BRANCH_ALLOW"):
            env.pop(key, None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix,
            input=payload,
            text=True,
            capture_output=True,
            cwd=str(cwd),
            env=env,
            timeout=120,
        )

    return _run


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=str(repo), check=True, capture_output=True, text=True
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A throwaway git repo with main, develop, and feat-x branches."""
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init")
    _git(r, "config", "user.email", "t@example.com")
    _git(r, "config", "user.name", "tester")
    (r / "f.txt").write_text("x\n", encoding="utf-8")
    _git(r, "add", "f.txt")
    _git(r, "commit", "-m", "init")
    _git(r, "branch", "-M", "main")
    _git(r, "branch", "develop")
    _git(r, "branch", "feat-x")
    return r


# --- existing dangerous-pattern behavior (regression) ---


def test_force_push_blocked(run, repo: Path) -> None:
    res = run("git push --force origin main", repo)
    assert res.returncode == _BLOCK
    assert "BLOCKED" in res.stderr


def test_safe_command_allowed(run, repo: Path) -> None:
    assert run("git status", repo).returncode == _ALLOW


@pytest.mark.parametrize(
    "command",
    [
        "git reset --hard HEAD~1",
        "git clean -fd",
        "git branch -D feat-x",
        "git stash drop",
        "git stash clear",
        "rm -rf .git",
    ],
)
def test_destructive_patterns_still_blocked(run, repo: Path, command: str) -> None:
    assert run(command, repo).returncode == _BLOCK, f"regressed: {command}"


# --- v3.15.6 AC4: execution indirection via git metadata (group B) ---


@pytest.mark.parametrize(
    "command",
    [
        "git -c core.hooksPath=/tmp/evil status",
        "git -c core.fsmonitor=evil.sh status",
        # Interleaving another -c option must not be an evasion.
        "git -c protocol.version=2 -c core.hooksPath=/tmp/x status",
        "git -c http.sslVerify=false -c core.fsmonitor=x.sh diff",
        # Spacing around the assignment must not be an evasion.
        "git -c core.hooksPath = /tmp/x status",
    ],
)
def test_inline_execution_indirection_blocked(run, repo: Path, command: str) -> None:
    """`git -c core.hooksPath=` / `core.fsmonitor=` name something git EXECUTES."""
    res = run(command, repo)
    assert res.returncode == _BLOCK, f"not blocked: {command}"
    assert "BLOCKED" in res.stderr


@pytest.mark.parametrize(
    "command",
    [
        "git config core.hooksPath .githooks",
        "git config --local core.fsmonitor evil.sh",
        "git config --global core.hooksPath /tmp/x",
        "git config --add core.hooksPath .githooks",
    ],
)
def test_persistent_execution_indirection_blocked(
    run, repo: Path, command: str
) -> None:
    """The `git config` form persists into .git/config and applies to every later
    operation, so it needs its own check beyond the inline `-c` patterns."""
    res = run(command, repo)
    assert res.returncode == _BLOCK, f"not blocked: {command}"
    assert "execution-indirection" in res.stderr


# --- AC4 false-positive guards (a denylist that blocks real work is a liability) ---


@pytest.mark.parametrize(
    "command",
    [
        # Reads of the same key are harmless and must stay allowed.
        "git config --get core.hooksPath",
        "git config --get-all core.fsmonitor",
        "git config --get-regexp core.*",
        "git config --list",
        "git config --unset core.hooksPath",
        # Benign -c options must stay allowed.
        "git -c user.name=Bob commit -m x",
        "git -c core.pager=cat log",
        "git -c core.autocrlf=false checkout feat-x",
        # Ordinary config writes to unrelated keys.
        "git config user.email a@b.c",
        "git config core.autocrlf false",
    ],
)
def test_benign_git_commands_allowed(run, repo: Path, command: str) -> None:
    res = run(command, repo)
    assert res.returncode == _ALLOW, (
        f"false positive on a benign command: {command} (stderr={res.stderr!r})"
    )


# --- opt-in protected-branch guard ---


def test_guard_inert_without_env(run, repo: Path) -> None:
    """With no NEXUS_PROTECTED_BRANCHES, committing on main is allowed."""
    _git(repo, "checkout", "main")
    assert run('git commit -m "x"', repo).returncode == _ALLOW


def test_guard_blocks_commit_on_protected(run, repo: Path) -> None:
    _git(repo, "checkout", "main")
    res = run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == _BLOCK
    assert "protected branch 'main'" in res.stderr


def test_guard_allows_commit_on_feature_branch(run, repo: Path) -> None:
    _git(repo, "checkout", "feat-x")
    res = run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == _ALLOW


def test_guard_override_allows_one_commit(run, repo: Path) -> None:
    _git(repo, "checkout", "main")
    res = run(
        'git commit -m "x"',
        repo,
        {"NEXUS_PROTECTED_BRANCHES": "main", "NEXUS_PROTECTED_BRANCH_ALLOW": "1"},
    )
    assert res.returncode == _ALLOW


def test_guard_does_not_block_merge(run, repo: Path) -> None:
    """Release merges onto the protected branch are intentionally allowed."""
    _git(repo, "checkout", "main")
    res = run("git merge --no-ff develop", repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == _ALLOW


def test_guard_accepts_comma_separated_list(run, repo: Path) -> None:
    _git(repo, "checkout", "develop")
    res = run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main,develop"})
    assert res.returncode == _BLOCK


# --- quiet paths ---


@pytest.mark.parametrize("payload_cmd", ["", "   "])
def test_no_command_is_allowed(run, repo: Path, payload_cmd: str) -> None:
    """A payload without a usable command must not block non-Bash tools."""
    assert run(payload_cmd, repo).returncode == _ALLOW


# ---------------------------------------------------------------------------
# Written-content precision (heredoc bodies)
#
# A command that WRITES a file carries the file's text in the same raw string the
# patterns match against, so documentation that merely NAMES a destructive
# command used to read as an attempt to RUN one. That is not hypothetical: it
# blocked an ordinary docs write, and a guard that blocks documentation is a
# guard that gets switched off.
#
# The dangerous strings below are ASSEMBLED at runtime so this test file does not
# itself trip a scanner that reads it as text.
# ---------------------------------------------------------------------------

_RESET = "git " + "reset " + "--hard"
_CFG_WRITE = "git " + "config core." + "hooksPath=/tmp/x"
_NL = chr(10)
_TAB = chr(9)


def test_destructive_command_still_blocks(run, repo):
    """Regression floor: the real invocation must keep blocking."""
    assert run(_RESET + " HEAD~1", repo).returncode == _BLOCK


def test_pattern_inside_heredoc_body_is_allowed(run, repo):
    """Prose naming a destructive command is a write, not an invocation."""
    cmd = "cat > doc.md <<'EOF'" + _NL + "Never run " + _RESET + " here." + _NL + "EOF"
    assert run(cmd, repo).returncode == _ALLOW


def test_pattern_inside_heredoc_body_still_warns(run, repo):
    """Allowing the write must not make the signal disappear.

    This is what keeps the change in the safe direction: the blocking scan
    matches less, but nothing is silently dropped.
    """
    cmd = "cat > doc.md <<'EOF'" + _NL + "Never run " + _RESET + " here." + _NL + "EOF"
    proc = run(cmd, repo)
    assert proc.returncode == _ALLOW
    assert "written file content" in proc.stderr


def test_real_command_after_a_heredoc_still_blocks(run, repo):
    """Closing a heredoc must resume scanning, or the body becomes an evasion."""
    cmd = "cat > d.md <<'EOF'" + _NL + "notes" + _NL + "EOF" + _NL + _RESET
    assert run(cmd, repo).returncode == _BLOCK


@pytest.mark.parametrize(
    "opener,closer,indent",
    [
        ("<<'EOF'", "EOF", ""),
        ('<<"END"', "END", ""),
        ("<<-EOF", _TAB + "EOF", _TAB),
        ("<<EOF", "EOF", ""),
    ],
    ids=["single-quoted", "double-quoted", "dash-indented", "bare"],
)
def test_heredoc_delimiter_forms(run, repo, opener, closer, indent):
    """All four documented opener forms must strip their body."""
    cmd = "cat > c.md " + opener + _NL + indent + _RESET + _NL + closer
    assert run(cmd, repo).returncode == _ALLOW


def test_config_write_inside_heredoc_is_allowed(run, repo):
    """The execution-indirection guard reads the same stripped scan."""
    cmd = "cat > n.md <<'EOF'" + _NL + _CFG_WRITE + _NL + "EOF"
    assert run(cmd, repo).returncode == _ALLOW


def test_config_write_as_a_command_still_blocks(run, repo):
    assert run(_CFG_WRITE, repo).returncode == _BLOCK


def test_multiline_payload_is_decoded_faithfully(run, repo):
    """Guards the jq-absent fallback path in the .sh hook.

    Without JSON un-escaping, a multi-line command arrives as ONE line carrying a
    literal backslash-n, so every line-oriented check sees a single long line
    rather than a script. The .ps1 sibling never had this bug because
    ConvertFrom-Json decodes escapes, which is exactly why this assertion is
    parametrized over both implementations: it must hold with and without jq.
    """
    cmd = "echo one" + _NL + "echo two" + _NL + _RESET
    assert run(cmd, repo).returncode == _BLOCK
