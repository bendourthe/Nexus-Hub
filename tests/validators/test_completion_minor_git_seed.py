"""Initial Git seed parity and isolation for private Minor fixtures."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import (  # noqa: F401
    MINOR_DIR, PUSH_URL, Minor, _no_transport_overrides,
)
from .test_run_plan import authenticated_minor


def _git_state(root: Path) -> dict[str, str]:
    work = root / "work"
    return {
        "tree": _git(work, "rev-parse", "HEAD^{tree}"),
        "files": _git(work, "ls-tree", "-r", "--name-only", "HEAD"),
        "head": _git(work, "symbolic-ref", "HEAD"),
        "branches": _git(work, "branch", "--format=%(refname:short)"),
        "tracking": _git(work, "for-each-ref", "--format=%(refname)", "refs/remotes"),
        "author": _git(work, "show", "-s", "--format=%an%n%ae%n%cn%n%ce%n%s"),
        "work_bare": _git(work, "rev-parse", "--is-bare-repository"),
        "remote_bare": _git(root / "remote.git", "rev-parse", "--is-bare-repository"),
    }


def _snapshot(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def test_seeded_minor_preserves_the_original_initial_git_contract(tmp_path, monkeypatch, minor_git_seed):
    original_root, copied_root = tmp_path / "original", tmp_path / "copied"
    original_root.mkdir()
    copied_root.mkdir()
    original = Minor(original_root, monkeypatch)
    copied = Minor(copied_root, monkeypatch, minor_git_seed)
    state = _git_state(copied.tmp)
    assert state == _git_state(original.tmp) == _git_state(minor_git_seed)
    assert state["head"] == "refs/heads/main"
    assert state["branches"].splitlines() == ["develop", "main"]
    tracking = set(state["tracking"].splitlines())
    required_tracking = {"refs/remotes/origin/develop", "refs/remotes/origin/main"}
    assert tracking in (required_tracking, required_tracking | {"refs/remotes/origin/HEAD"})
    assert state["author"].splitlines() == ["Test", "t@example.invalid", "Test", "t@example.invalid", "start"]
    assert state["files"].splitlines() == sorted([
        f"{MINOR_DIR}/v0.5.2-alpha.md", f"{MINOR_DIR}/v0.5.10-omega.md",
    ])
    assert state["work_bare"] == "false" and state["remote_bare"] == "true"
    for fixture in (original, copied):
        assert _git(fixture.work, "status", "--porcelain") == ""
        assert _git(fixture.work, "config", "--get", "remote.origin.url") == str(fixture.remote)
        assert _git(fixture.work, "config", "--get", "remote.origin.pushurl") == PUSH_URL
        head = _git(fixture.work, "rev-parse", "HEAD")
        refs = _git(fixture.work, "for-each-ref", "--format=%(objectname)").splitlines()
        assert len(refs) == 2 + len(tracking) and set(refs) == {head}
        if "refs/remotes/origin/HEAD" in tracking:
            assert _git(fixture.work, "symbolic-ref", "refs/remotes/origin/HEAD") == "refs/remotes/origin/main"
        assert _git(fixture.remote, "symbolic-ref", "HEAD") == "refs/heads/main"
        assert _git(fixture.remote, "for-each-ref", "--format=%(objectname)").splitlines() == [head, head]
        fetch = (fixture.work / ".git" / "FETCH_HEAD").read_text(encoding="utf-8")
        normalized_fetch = fetch.replace(chr(92) * 2, chr(92)).replace(chr(92), "/")
        remote_display = str(fixture.remote).replace(chr(92), "/").removesuffix(".git")
        assert remote_display in normalized_fetch
        seed_display = str(minor_git_seed / "remote.git").replace(chr(92), "/").removesuffix(".git")
        assert seed_display not in normalized_fetch
    assert {p.name for p in minor_git_seed.iterdir()} == {"work", "remote.git", "empty.gitconfig"}


def test_seeded_copies_isolate_files_refs_origin_and_authenticated_records(tmp_path, minor_git_seed):
    with pytest.MonkeyPatch.context() as patch:
        first = authenticated_minor(tmp_path / "first", patch, minor_git_seed)
        first_record = first.record_path()
    with pytest.MonkeyPatch.context() as patch:
        second = authenticated_minor(tmp_path / "second", patch, minor_git_seed)
        second_record = second.record_path()
    assert first_record != second_record
    assert first_record.is_file() and second_record.is_file()
    assert first.env["NEXUS_HUB_RUNS_DIR"] != second.env["NEXUS_HUB_RUNS_DIR"]
    seed_before, second_before = _snapshot(minor_git_seed), _snapshot(second.tmp)
    second_record_before = second_record.read_bytes()
    head = _git(first.work, "rev-parse", "HEAD")
    obj = Path(".git") / "objects" / head[:2] / head[2:]
    for other in (second.work, minor_git_seed / "work"):
        assert not os.path.samefile(first.work / obj, other / obj)
    for fixture in (first, second):
        assert not (fixture.work / ".git" / "objects" / "info" / "alternates").exists()
        assert not (fixture.remote / "objects" / "info" / "alternates").exists()
    (first.work / MINOR_DIR / "v0.5.2-alpha.md").write_text("changed", encoding="utf-8")
    _git(first.work, "branch", "only-first")
    _git(first.remote, "branch", "only-first")
    _git(first.work, "remote", "set-url", "origin", str(first.tmp / "other.git"))
    first_record.write_text("{}", encoding="utf-8")
    assert second_record.read_bytes() == second_record_before
    assert _snapshot(second.tmp) == second_before
    assert _snapshot(minor_git_seed) == seed_before
