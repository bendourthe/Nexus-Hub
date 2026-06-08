"""Tests for catalog/hooks/git-guardrails.sh.

Covers the existing dangerous-pattern blocking (regression) and the opt-in
protected-branch guard added for the develop+main workflow.

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

_HOOK = Path(__file__).parent.parent / "git-guardrails.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("git") is None,
    reason="git-guardrails.sh requires bash and git on PATH",
)


def _run(
    command: str, cwd: Path, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Pipe a PreToolUse JSON payload to the hook and capture its exit + stderr."""
    payload = json.dumps({"tool_input": {"command": command}})
    env = {**os.environ, **env_extra} if env_extra is not None else None
    return subprocess.run(
        ["bash", str(_HOOK)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
    )


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


def test_force_push_blocked(repo: Path) -> None:
    res = _run("git push --force origin main", repo)
    assert res.returncode == 2
    assert "BLOCKED" in res.stderr


def test_safe_command_allowed(repo: Path) -> None:
    assert _run("git status", repo).returncode == 0


# --- opt-in protected-branch guard ---


def test_guard_inert_without_env(repo: Path) -> None:
    """With no NEXUS_PROTECTED_BRANCHES, committing on main is allowed (no behavior change)."""
    _git(repo, "checkout", "main")
    assert _run('git commit -m "x"', repo).returncode == 0


def test_guard_blocks_commit_on_protected(repo: Path) -> None:
    _git(repo, "checkout", "main")
    res = _run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == 2
    assert "protected branch 'main'" in res.stderr


def test_guard_allows_commit_on_feature_branch(repo: Path) -> None:
    _git(repo, "checkout", "feat-x")
    res = _run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == 0


def test_guard_override_allows_one_commit(repo: Path) -> None:
    _git(repo, "checkout", "main")
    res = _run(
        'git commit -m "x"',
        repo,
        {"NEXUS_PROTECTED_BRANCHES": "main", "NEXUS_PROTECTED_BRANCH_ALLOW": "1"},
    )
    assert res.returncode == 0


def test_guard_does_not_block_merge(repo: Path) -> None:
    """Release merges onto the protected branch are intentionally allowed."""
    _git(repo, "checkout", "main")
    res = _run("git merge --no-ff develop", repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == 0


def test_guard_accepts_comma_separated_list(repo: Path) -> None:
    _git(repo, "checkout", "develop")
    res = _run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main,develop"})
    assert res.returncode == 2
