"""Behavioral tests for `nexus-hub worktree prune-merged`.

Real Git repositories are built in a temporary directory and the real command runs
against them. Nothing here touches the developer's own repositories or home. Every
child process is started without a console window on Windows.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "nexus_worktrees.py"
NO_WINDOW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


def git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
        **NO_WINDOW,
    )


@pytest.fixture
def sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text(
        "[user]\n\tname = Fixture\n\temail = fixture@example.invalid\n[init]\n\tdefaultBranch = main\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home / ".nexus-hub"))
    monkeypatch.setenv("NEXUS_WORKTREE_STATE", str(tmp_path / "state"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.delenv("NEXUS_WORKTREE_ROOT", raising=False)
    machine = tmp_path / "machine"
    machine.mkdir()
    return machine


@pytest.fixture
def repo(sandbox: Path) -> Path:
    path = sandbox / "main-clone"
    path.mkdir()
    git("init", "-q", cwd=path)
    (path / "a.txt").write_text("one\n", encoding="utf-8")
    git("add", "a.txt", cwd=path)
    git("commit", "-q", "-m", "init", cwd=path)
    git("branch", "develop", cwd=path)
    return path


def add_branch_worktree(repo: Path, name: str, *, commit: bool = True) -> Path:
    dest = repo.parent / "wt" / name
    git("worktree", "add", "-q", "-b", name, str(dest), "develop", cwd=repo)
    if commit:
        (dest / f"{name}.txt").write_text(name + "\n", encoding="utf-8")
        git("add", ".", cwd=dest)
        git("commit", "-q", "-m", f"work {name}", cwd=dest)
    return dest


def merge_into_develop(repo: Path, branch: str, *, squash: bool = False) -> None:
    git("checkout", "-q", "develop", cwd=repo)
    if squash:
        git("merge", "--squash", branch, cwd=repo)
        git("commit", "-q", "-m", f"squash {branch}", cwd=repo)
    else:
        git("merge", "-q", "--no-ff", "-m", f"merge {branch}", branch, cwd=repo)
    git("checkout", "-q", "main", cwd=repo)


def prune(
    repo: Path, *extra: str, cwd: Path | None = None
) -> tuple[int, dict[str, object]]:
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "prune-merged",
            "--repo",
            str(repo),
            "--json",
            *extra,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
        cwd=cwd,
        **NO_WINDOW,
    )
    return proc.returncode, json.loads(proc.stdout)


def rows(report: dict[str, object]) -> dict[str, dict[str, object]]:
    return {Path(w["path"]).name: w for w in report["worktrees"]}  # type: ignore[index]


def branches(repo: Path) -> set[str]:
    out = git(
        "for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=repo
    ).stdout
    return set(out.split())


def test_dry_run_reports_and_changes_nothing(repo: Path) -> None:
    wt = add_branch_worktree(repo, "feat-a")
    merge_into_develop(repo, "feat-a")

    rc, report = prune(repo, "--idle-hours", "0")

    assert rc == 0 and report["status"] == "dry-run"
    row = rows(report)["feat-a"]
    assert (row["action"], row["class"], row["merged_by"]) == (
        "REMOVE",
        "merged-clean",
        "ancestor",
    )
    assert wt.is_dir() and "feat-a" in branches(repo)
    assert report["would_remove"] == 1


def test_apply_removes_merged_clean_worktree_and_branch(repo: Path) -> None:
    wt = add_branch_worktree(repo, "feat-a")
    merge_into_develop(repo, "feat-a")

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    assert rc == 0 and report["removed"] == 1
    assert not wt.exists()
    assert "feat-a" not in branches(repo)
    assert {"main", "develop"} <= branches(repo)
    assert repo.is_dir() and (repo / "a.txt").is_file()


def test_unmerged_worktree_is_kept(repo: Path) -> None:
    wt = add_branch_worktree(repo, "feat-open")

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    row = rows(report)["feat-open"]
    assert rc == 0 and (row["action"], row["reason"], row["class"]) == (
        "KEEP",
        "not-merged",
        "unmerged-clean",
    )
    assert wt.is_dir() and "feat-open" in branches(repo)


def test_merged_but_dirty_worktrees_are_kept(repo: Path) -> None:
    untracked = add_branch_worktree(repo, "feat-untracked")
    modified = add_branch_worktree(repo, "feat-modified")
    staged = add_branch_worktree(repo, "feat-staged")
    for name in ("feat-untracked", "feat-modified", "feat-staged"):
        merge_into_develop(repo, name)
    (untracked / "scratch.txt").write_text("x\n", encoding="utf-8")
    (modified / "feat-modified.txt").write_text("changed\n", encoding="utf-8")
    (staged / "new.txt").write_text("y\n", encoding="utf-8")
    git("add", "new.txt", cwd=staged)

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    assert rc == 0 and report["removed"] == 0
    for name, wt in (
        ("feat-untracked", untracked),
        ("feat-modified", modified),
        ("feat-staged", staged),
    ):
        row = rows(report)[name]
        assert (row["action"], row["reason"], row["class"]) == (
            "KEEP",
            "dirty",
            "merged-dirty",
        )
        assert wt.is_dir() and name in branches(repo)


def test_squash_merged_branch_is_detected_by_content(repo: Path) -> None:
    wt = add_branch_worktree(repo, "feat-squash")
    merge_into_develop(repo, "feat-squash", squash=True)

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    assert rc == 0 and rows(report)["feat-squash"]["merged_by"] == "content"
    assert not wt.exists() and "feat-squash" not in branches(repo)


def test_locked_and_stashed_worktrees_are_kept(repo: Path) -> None:
    locked = add_branch_worktree(repo, "feat-locked")
    stashed = add_branch_worktree(repo, "feat-stash")
    for name in ("feat-locked", "feat-stash"):
        merge_into_develop(repo, name)
    git("worktree", "lock", "--reason", "in use", str(locked), cwd=repo)
    (stashed / "feat-stash.txt").write_text("wip\n", encoding="utf-8")
    git("stash", "push", "-q", cwd=stashed)

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    assert rc == 0
    assert rows(report)["feat-locked"]["reason"] == "locked"
    assert rows(report)["feat-stash"]["reason"] == "stashed"
    assert locked.is_dir() and stashed.is_dir()
    assert git("stash", "list", cwd=repo).stdout.strip()


def test_ignored_files_keep_unless_regenerable(repo: Path) -> None:
    (repo / ".gitignore").write_text("*.local\n__pycache__/\n", encoding="utf-8")
    git("add", ".gitignore", cwd=repo)
    git("commit", "-q", "-m", "ignore", cwd=repo)
    git("branch", "-f", "develop", "main", cwd=repo)
    keeps = add_branch_worktree(repo, "feat-notes")
    cache = add_branch_worktree(repo, "feat-cache")
    for name in ("feat-notes", "feat-cache"):
        merge_into_develop(repo, name)
    (keeps / "notes.local").write_text("mine\n", encoding="utf-8")
    (cache / "__pycache__").mkdir()
    (cache / "__pycache__" / "m.pyc").write_bytes(b"x")

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    assert rc == 0
    assert rows(report)["feat-notes"]["reason"] == "ignored-files"
    assert keeps.is_dir() and not cache.exists()


def test_recently_active_worktree_is_kept_unless_named(repo: Path) -> None:
    wt = add_branch_worktree(repo, "feat-fresh")
    merge_into_develop(repo, "feat-fresh")

    rc, report = prune(repo, "--apply")  # default 24 hour idle window
    assert rc == 0 and rows(report)["feat-fresh"]["reason"] == "recently-active"
    assert wt.is_dir()

    rc, report = prune(repo, "--apply", "--only", "feat-fresh")
    assert rc == 0 and report["removed"] == 1 and not wt.exists()


def test_only_limits_the_candidate_set(repo: Path) -> None:
    keep = add_branch_worktree(repo, "feat-keep")
    drop = add_branch_worktree(repo, "feat-drop")
    for name in ("feat-keep", "feat-drop"):
        merge_into_develop(repo, name)

    rc, report = prune(repo, "--apply", "--only", str(drop))

    assert rc == 0 and set(rows(report)) == {"feat-drop"}
    assert keep.is_dir() and not drop.exists()


def test_worktree_holding_the_current_directory_is_kept(repo: Path) -> None:
    wt = add_branch_worktree(repo, "feat-here")
    merge_into_develop(repo, "feat-here")

    rc, report = prune(repo, "--apply", "--idle-hours", "0", cwd=wt)

    assert rc == 0 and rows(report)["feat-here"]["reason"] == "current-directory"
    assert wt.is_dir()


def test_primary_checkout_and_protected_branches_are_never_removed(repo: Path) -> None:
    dev = repo.parent / "wt" / "dev-tree"
    git("worktree", "add", "-q", str(dev), "develop", cwd=repo)

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    assert rc == 0 and report["removed"] == 0
    assert rows(report)["main-clone"]["reason"] == "primary-checkout"
    assert rows(report)["dev-tree"]["reason"] == "protected-branch"
    assert repo.is_dir() and dev.is_dir() and "develop" in branches(repo)


def test_detached_merged_worktree_is_removed_without_a_branch(repo: Path) -> None:
    dest = repo.parent / "wt" / "detached"
    git("worktree", "add", "-q", "--detach", str(dest), "develop", cwd=repo)

    rc, report = prune(repo, "--apply", "--idle-hours", "0")

    assert rc == 0 and report["removed"] == 1 and not dest.exists()
    assert branches(repo) == {"main", "develop"}


def test_remote_tracking_integration_branch_is_the_merge_target(
    sandbox: Path, repo: Path
) -> None:
    origin = sandbox / "origin.git"
    git("clone", "-q", "--bare", str(repo), str(origin), cwd=sandbox)
    git("remote", "add", "origin", str(origin), cwd=repo)
    git("fetch", "-q", "origin", cwd=repo)
    wt = add_branch_worktree(repo, "feat-remote")
    merge_into_develop(repo, "feat-remote")  # merged locally, not yet pushed

    rc, report = prune(repo, "--idle-hours", "0")
    assert rows(report)["feat-remote"]["reason"] == "not-merged"
    assert report["integration_targets"] == [
        "refs/remotes/origin/develop",
        "refs/remotes/origin/main",
    ]

    git("push", "-q", "origin", "develop", cwd=repo)
    rc, report = prune(repo, "--apply", "--fetch", "--idle-hours", "0")
    assert rc == 0 and report["removed"] == 1 and not wt.exists()


def test_table_output_lists_every_column_and_a_summary(repo: Path) -> None:
    add_branch_worktree(repo, "feat-a")
    merge_into_develop(repo, "feat-a")

    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "prune-merged",
            "--repo",
            str(repo),
            "--idle-hours",
            "0",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
        **NO_WINDOW,
    )

    assert proc.returncode == 0
    assert (
        proc.stdout.splitlines()[0]
        == "path | branch | merged | clean | action | reason"
    )
    assert "summary: 1 would be removed (dry run, nothing removed)" in proc.stdout
    assert os.path.isdir(repo.parent / "wt" / "feat-a")
