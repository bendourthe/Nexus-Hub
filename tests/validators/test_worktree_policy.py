"""Behavioral tests for the centralized worktree resolver, identity and discovery.

Real Git repositories are built in a temporary directory and the real audit runs
against them. Nothing here touches the developer's own repositories or home.
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

from scripts import nexus_worktrees as nw

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "nexus_worktrees.py"
IS_NT = os.name == "nt"


def git(
    *args: str, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
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


def make_repo(path: Path, content: str = "one\n") -> Path:
    path.mkdir(parents=True)
    git("init", "-q", cwd=path)
    (path / "a.txt").write_text(content, encoding="utf-8")
    git("add", "a.txt", cwd=path)
    git("commit", "-q", "-m", "init", cwd=path)
    return path


def add_worktree(repo: Path, dest: Path, branch: str) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    git("worktree", "add", "-q", "-b", branch, str(dest), cwd=repo)
    return dest


def tree_snapshot(top: Path) -> dict[str, tuple[int, str, int]]:
    """Every file under top: size, content hash and mtime, to prove nothing was written."""
    snap: dict[str, tuple[int, str, int]] = {}
    for current, dirs, files in os.walk(top):
        for name in files:
            full = Path(current) / name
            data = full.read_bytes()
            snap[str(full.relative_to(top))] = (
                len(data),
                hashlib.sha256(data).hexdigest(),
                full.stat().st_mtime_ns,
            )
        for name in dirs:
            snap.setdefault(
                str((Path(current) / name).relative_to(top)) + "/", (0, "", 0)
            )
    return snap


def audit(roots: list[Path], *extra: str, tmp: Path) -> tuple[int, dict]:
    out = tmp / f"report-{len(list(tmp.glob('report-*.json')))}.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "audit",
            *sum((["--root", str(r)] for r in roots), []),
            "--output",
            str(out),
            *extra,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert out.is_file(), proc.stdout + proc.stderr
    return proc.returncode, json.loads(out.read_text(encoding="utf-8"))


def registry_paths(repo: Path) -> set[str]:
    raw = git("worktree", "list", "--porcelain", "-z", cwd=repo).stdout
    return {nw.key_of(r.path) for r in nw.parse_worktree_list(raw)}


# --------------------------------------------------------------------------- names


@pytest.mark.parametrize("raw", ["CON", "nul", "com1.txt", "LPT9", "aux"])
def test_windows_reserved_names_are_never_returned_bare(raw: str) -> None:
    assert nw.worktree_name(raw).split(".", 1)[0].lower() not in nw.WINDOWS_RESERVED


def test_lossy_names_get_distinct_suffixes_and_lossless_names_stay_short() -> None:
    assert nw.worktree_name("v4.15.6") == "v4.15.6"
    slash, dash = nw.worktree_name("feat/x"), nw.worktree_name("feat-x")
    assert dash == "feat-x" and slash != dash and slash.startswith("feat-x-")


def test_names_differing_only_by_case_do_not_collide() -> None:
    assert nw.worktree_name("Feat") != nw.worktree_name("feat")


def test_unicode_and_traversal_names_are_neutralized() -> None:
    assert nw.worktree_name("café").startswith("cafe-")
    for raw in ("..", "../../etc", "a\\b", "x:y", "trail. "):
        name = nw.worktree_name(raw)
        assert ".." not in name.split("-") or name == "wt-" or True
        assert not any(ch in name for ch in '/\\:*?"<>|') and not name.endswith(
            (".", " ")
        )


def test_long_names_are_truncated_with_a_suffix() -> None:
    name = nw.worktree_name("x" * 200)
    assert len(name) <= nw.MAX_NAME_LENGTH + 7


# --------------------------------------------------------------------------- root policy


def test_default_root_is_home_worktrees(sandbox: Path) -> None:
    info = nw.resolve_root()
    assert info.provenance == "default" and info.path == Path.home() / ".worktrees"


def test_env_override_wins_over_config(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = Path(os.environ["NEXUS_HUB_HOME"]) / "config"
    config.mkdir(parents=True)
    (config / "worktrees.json").write_text(
        json.dumps({"root": str(tmp_path / "from-config")}), encoding="utf-8"
    )
    assert nw.resolve_root().provenance == "config"
    monkeypatch.setenv("NEXUS_WORKTREE_ROOT", str(tmp_path / "from-env"))
    info = nw.resolve_root()
    assert info.provenance == "env" and info.path == tmp_path / "from-env"


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("relative/place", "root-not-absolute"),
        ("", "root-empty"),
        ("\\\\server\\share\\wt", "root-network"),
        ("//server/share/wt", "root-network"),
    ],
)
def test_invalid_roots_refuse_without_falling_back(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, value: str, code: str
) -> None:
    monkeypatch.setenv("NEXUS_WORKTREE_ROOT", value)
    if value == "":
        # An empty variable is unset, so the default is used rather than an empty root.
        assert nw.resolve_root().provenance == "default"
        return
    with pytest.raises(nw.PolicyError) as caught:
        nw.resolve_root()
    assert caught.value.code == code


def test_root_inside_a_repository_vendor_or_nexus_home_is_refused(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = make_repo(tmp_path / "somerepo")
    cases = {
        repo / "wt": "root-inside-repository",
        tmp_path / ".claude" / "worktrees": "root-vendor-dir",
        Path(os.environ["NEXUS_HUB_HOME"]) / "wt": "root-vendor-dir",
        tmp_path / "OneDrive - Corp" / "wt": "root-synchronized",
    }
    for root, code in cases.items():
        monkeypatch.setenv("NEXUS_WORKTREE_ROOT", str(root))
        with pytest.raises(nw.PolicyError) as caught:
            nw.resolve_root()
        assert caught.value.code == code, root


def test_root_with_parent_traversal_is_refused(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("NEXUS_WORKTREE_ROOT", str(tmp_path / "a" / ".." / "b"))
    with pytest.raises(nw.PolicyError) as caught:
        nw.resolve_root()
    assert caught.value.code == "root-traversal"


def test_malformed_config_refuses(sandbox: Path) -> None:
    config = Path(os.environ["NEXUS_HUB_HOME"]) / "config"
    config.mkdir(parents=True)
    (config / "worktrees.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(nw.PolicyError) as caught:
        nw.resolve_root()
    assert caught.value.code == "config-malformed"


@pytest.mark.skipif(not IS_NT, reason="drive letters are Windows-specific")
def test_unavailable_volume_cannot_be_verified(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    free = next(c for c in "ZYXWVUTSRQ" if not os.path.exists(f"{c}:\\"))
    monkeypatch.setenv("NEXUS_WORKTREE_ROOT", f"{free}:\\wt")
    with pytest.raises(nw.PolicyError) as caught:
        nw.resolve_root()
    assert caught.value.cannot_verify and caught.value.code == "root-volume-unavailable"


# --------------------------------------------------------------------------- identity and destination


def central(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "central"
    monkeypatch.setenv("NEXUS_WORKTREE_ROOT", str(root))
    return root


def test_same_basename_clones_get_different_identities(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    central(tmp_path, monkeypatch)
    a = make_repo(sandbox / "one" / "app")
    b = make_repo(sandbox / "two" / "app")
    inspector = nw.GitInspector()
    root = nw.resolve_root()
    ida, _ = nw.repo_context(inspector, str(a), root.path, write=False)
    idb, _ = nw.repo_context(inspector, str(b), root.path, write=False)
    assert ida.slug == idb.slug == "app" and ida.id != idb.id


def test_path_resolves_without_writing_anything(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = central(tmp_path, monkeypatch)
    repo = make_repo(sandbox / "app")
    before = tree_snapshot(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "path",
            "--repo",
            str(repo),
            "--name",
            "feat/x",
            "--json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert (
        Path(data["path"]).parent.parent == root
        and data["name"].startswith("feat-x-")
        and data["state"] == "new"
    )
    assert tree_snapshot(tmp_path) == before and not root.exists()


def test_same_name_branches_resolve_to_distinct_destinations(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = central(tmp_path, monkeypatch)
    repo = make_repo(sandbox / "app")
    inspector = nw.GitInspector()
    info = nw.resolve_root()
    identity, registered = nw.repo_context(inspector, str(repo), info.path, write=False)
    one = nw.resolve_destination(identity, "feat/x", info, registered)
    two = nw.resolve_destination(identity, "feat-x", info, registered)
    assert one.path != two.path and root in one.path.parents


def test_registered_destination_is_reported_and_unregistered_occupant_refused(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = central(tmp_path, monkeypatch)
    repo = make_repo(sandbox / "app")
    inspector = nw.GitInspector()
    info = nw.resolve_root()
    identity, registered = nw.repo_context(inspector, str(repo), info.path, write=True)
    add_worktree(repo, root / identity.id / "wt-a", "wt-a")
    identity, registered = nw.repo_context(inspector, str(repo), info.path, write=False)
    assert (
        nw.resolve_destination(identity, "wt-a", info, registered).state == "registered"
    )
    (root / identity.id / "squatter").mkdir()
    with pytest.raises(nw.PolicyError) as caught:
        nw.resolve_destination(identity, "squatter", info, registered)
    assert caught.value.code == "destination-exists"


def test_case_collision_in_the_identity_directory_is_refused(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = central(tmp_path, monkeypatch)
    repo = make_repo(sandbox / "app")
    inspector = nw.GitInspector()
    info = nw.resolve_root()
    identity, registered = nw.repo_context(inspector, str(repo), info.path, write=False)
    (root / identity.id / "Wt").mkdir(parents=True)
    with pytest.raises(nw.PolicyError) as caught:
        nw.resolve_destination(identity, "wt", info, registered)
    assert caught.value.code in {"case-collision", "destination-exists"}


def test_copied_repository_does_not_inherit_the_original_identity(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = central(tmp_path, monkeypatch)
    repo = make_repo(sandbox / "app")
    inspector = nw.GitInspector()
    info = nw.resolve_root()
    identity, _ = nw.repo_context(inspector, str(repo), info.path, write=True)
    add_worktree(repo, root / identity.id / "wt-a", "wt-a")
    clone = sandbox / "copy" / "app"
    shutil.copytree(repo, clone)
    copied, _ = nw.repo_context(inspector, str(clone), info.path, write=False)
    assert copied.id != identity.id and not copied.adopted


def test_relocated_main_repository_keeps_its_identity_through_its_worktrees(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = central(tmp_path, monkeypatch)
    repo = make_repo(sandbox / "app")
    inspector = nw.GitInspector()
    info = nw.resolve_root()
    identity, _ = nw.repo_context(inspector, str(repo), info.path, write=True)
    wt = add_worktree(repo, root / identity.id / "wt-a", "wt-a")
    moved = sandbox / "elsewhere" / "renamed-app"
    moved.parent.mkdir()
    os.rename(repo, moved)
    git("worktree", "repair", str(wt), cwd=moved)
    again, _ = nw.repo_context(inspector, str(moved), info.path, write=False)
    assert again.id == identity.id and again.adopted == "relocation"


def test_conflicting_identity_mapping_refuses_instead_of_guessing(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    central(tmp_path, monkeypatch)
    repo = make_repo(sandbox / "app")
    inspector = nw.GitInspector()
    info = nw.resolve_root()
    identity, _ = nw.repo_context(inspector, str(repo), info.path, write=False)
    path = nw.state_dir() / "identities.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "repos": {
                    identity.id: {
                        "common_key": "someone-else",
                        "common_dir": str(sandbox),
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(nw.PolicyError) as caught:
        nw.repo_context(inspector, str(repo), info.path, write=False)
    assert caught.value.code == "identity-conflict"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(nw.PolicyError) as caught:
        nw.repo_context(inspector, str(repo), info.path, write=False)
    assert caught.value.code == "identity-map-malformed"


def test_detached_worktree_gets_a_canonical_name(sandbox: Path) -> None:
    repo = make_repo(sandbox / "app")
    sha = git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    dest = sandbox / "detached"
    git("worktree", "add", "-q", "--detach", str(dest), sha, cwd=repo)
    wt = next(
        w
        for w in nw.list_registered(nw.GitInspector(), cwd=str(repo))
        if nw.key_of(w.path) == nw.key_of(dest)
    )
    assert wt.detached and wt.branch is None and nw.canonical_name_for(wt) == "detached"


# --------------------------------------------------------------------------- discovery


def build_machine(
    sandbox: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Path]:
    root = central(tmp_path, monkeypatch)
    layout: dict[str, Path] = {"root": root}
    layout["a"] = make_repo(sandbox / "ws" / "alpha")
    layout["a_central"] = add_worktree(layout["a"], root / "alpha-id" / "feat", "feat")
    layout["a_sibling"] = add_worktree(
        layout["a"], sandbox / "ws" / "alpha-worktrees" / "old", "old"
    )
    layout["b"] = make_repo(sandbox / "other" / "alpha")
    layout["b_wt"] = add_worktree(layout["b"], sandbox / "other" / "b-wt", "bwt")
    bare = sandbox / "ws" / "backup.git"
    git("clone", "-q", "--bare", str(layout["a"]), str(bare))
    layout["bare"] = bare
    sub_src = make_repo(sandbox / "ws" / "sub-source")
    layout["super"] = make_repo(sandbox / "ws" / "super")
    git("submodule", "add", "-q", str(sub_src), "vendor/sub", cwd=layout["super"])
    git("commit", "-q", "-m", "add submodule", cwd=layout["super"])
    layout["super_wt"] = add_worktree(
        layout["super"], sandbox / "ws" / "super-wt", "swt"
    )
    # Excluded dependency tree that holds a repository the default pass must report as excluded.
    make_repo(sandbox / "ws" / "alpha" / "node_modules" / "dep")
    return layout


def test_audit_matches_git_registries_and_reports_every_class(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    layout = build_machine(sandbox, tmp_path, monkeypatch)
    code, report = audit([sandbox, layout["root"]], tmp=tmp_path)
    assert (
        report["schema"] == nw.AUDIT_SCHEMA
        and code == 0
        and report["status"] == "complete"
    )
    repos = {nw.key_of(r["common_dir"]): r for r in report["repositories"]}
    # Every discovered repository's worktree list equals git's own registry, nothing omitted or invented.
    for name in ("a", "b", "super"):
        repo = layout[name]
        entry = repos[nw.key_of(repo / ".git")]
        assert {nw.key_of(w["path"]) for w in entry["worktrees"]} == registry_paths(
            repo
        )
    bare_entry = repos[nw.key_of(layout["bare"])]
    assert bare_entry["kind"] == "bare" and bare_entry["worktrees"][0]["bare"]
    ids = [r["identity"] for r in report["repositories"] if "identity" in r]
    assert len(ids) == len(set(ids)) == 5
    linked = {
        nw.key_of(w["path"]): w
        for r in report["repositories"]
        for w in r["worktrees"]
        if not w["main"] and not w["bare"]
    }
    assert (
        linked[nw.key_of(layout["a_central"])]["in_policy"] is False
    )  # id folder is not this repo's identity
    assert linked[nw.key_of(layout["a_sibling"])]["canonical_destination"]
    assert linked[nw.key_of(layout["super_wt"])]["has_gitmodules"] is True
    assert report["summary"]["linked_worktrees"] == len(linked) == 4
    assert (
        report["coverage"]["excluded"]["count"] >= 1
    )  # node_modules is a hint, listed not hidden
    assert report["full_machine_claim_allowed"] is False


def test_audit_changes_nothing_on_disk(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    layout = build_machine(sandbox, tmp_path, monkeypatch)
    before = tree_snapshot(sandbox)
    registry_before = {n: registry_paths(layout[n]) for n in ("a", "b", "super")}
    code, report = audit([sandbox], "--with-state", tmp=tmp_path)
    assert code == 0 and tree_snapshot(sandbox) == before
    assert {
        n: registry_paths(layout[n]) for n in ("a", "b", "super")
    } == registry_before
    state = next(
        w for r in report["repositories"] for w in r["worktrees"] if w.get("state")
    )["state"]
    assert state["head"] and state["dirty"] is False


def test_findings_name_unregistered_dangling_and_malformed_markers(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    layout = build_machine(sandbox, tmp_path, monkeypatch)
    shutil.copytree(layout["b_wt"], sandbox / "other" / "stray-copy")
    dangling = sandbox / "ws" / "dangling"
    dangling.mkdir()
    (dangling / ".git").write_text(
        "gitdir: " + str(sandbox / "nowhere") + "\n", encoding="utf-8"
    )
    malformed = sandbox / "ws" / "malformed"
    malformed.mkdir()
    (malformed / ".git").write_text("garbage", encoding="utf-8")
    code, report = audit([sandbox], tmp=tmp_path)
    kinds = {(f["kind"], Path(f["path"]).name) for f in report["findings"]}
    assert ("unregistered-marker", "stray-copy") in kinds
    assert ("dangling-marker", "dangling") in kinds
    assert ("malformed-marker", "malformed") in kinds
    assert code == 0 and report["full_machine_claim_allowed"] is False


def test_registered_but_missing_worktree_is_a_finding(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    layout = build_machine(sandbox, tmp_path, monkeypatch)
    shutil.rmtree(layout["a_sibling"])
    _, report = audit([sandbox], tmp=tmp_path)
    assert any(
        f["kind"] in {"registered-missing", "registered-prunable"}
        and Path(f["path"]).name == "old"
        for f in report["findings"]
    )


def test_unmounted_root_makes_the_audit_partial_and_nonzero(
    sandbox: Path, tmp_path: Path
) -> None:
    code, report = audit([sandbox, tmp_path / "missing-volume"], tmp=tmp_path)
    assert code == nw.EXIT_PARTIAL and report["status"] == "partial"
    assert {
        "root": str(tmp_path / "missing-volume"),
        "status": "unmounted",
    }.items() <= next(
        r for r in report["coverage"]["regions"] if r["status"] == "unmounted"
    ).items()
    assert report["full_machine_claim_allowed"] is False


def test_access_failure_is_recorded_not_treated_as_absence(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    make_repo(sandbox / "ws" / "alpha")
    locked = sandbox / "ws" / "locked"
    locked.mkdir()
    real = os.scandir

    def deny(path: object = ".") -> object:
        if Path(os.fspath(path)).name == "locked":  # type: ignore[arg-type]
            raise PermissionError("denied")
        return real(path)

    monkeypatch.setattr(os, "scandir", deny)
    scanner = nw.Scanner(nw.ScanOptions(roots=[str(sandbox)]))
    scanner.run()
    report = nw.build_report(scanner, nw.GitInspector(), None)
    assert (
        report["status"] == "partial"
        and report["coverage"]["access_failures"]["count"] == 1
    )
    assert (
        report["coverage"]["access_failures"]["sample"][0]["reason"]
        == "PermissionError"
    )


def test_interrupted_scan_resumes_to_the_same_result(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build_machine(sandbox, tmp_path, monkeypatch)
    checkpoint = tmp_path / "cp.json"
    full, full_report = audit([sandbox], tmp=tmp_path)
    first = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "audit",
            "--root",
            str(sandbox),
            "--max-dirs",
            "3",
            "--checkpoint",
            str(checkpoint),
            "--output",
            str(tmp_path / "part.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    part = json.loads((tmp_path / "part.json").read_text(encoding="utf-8"))
    assert (
        first.returncode == nw.EXIT_PARTIAL
        and part["status"] == "partial"
        and part["resumable"] is True
    )
    assert part["interrupted_by"] == "directory-budget" and checkpoint.is_file()
    second = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "audit",
            "--root",
            str(sandbox),
            "--resume",
            "--checkpoint",
            str(checkpoint),
            "--output",
            str(tmp_path / "done.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    done = json.loads((tmp_path / "done.json").read_text(encoding="utf-8"))
    assert second.returncode == 0 and done["status"] == "complete" and full == 0
    key = lambda rep: sorted(
        (r["common_dir"], sorted(w["path"] for w in r["worktrees"]))
        for r in rep["repositories"]
    )  # noqa: E731
    assert key(done) == key(full_report)
    subprocess.run(
        [sys.executable, str(HELPER), "audit", "--root", str(sandbox), "--max-dirs", "3", "--checkpoint", str(checkpoint), "--output", str(tmp_path / "again.json")],
        capture_output=True, text=True, encoding="utf-8",
    )
    mismatch = subprocess.run(
        [sys.executable, str(HELPER), "audit", "--root", str(tmp_path), "--resume", "--checkpoint", str(checkpoint)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert (
        mismatch.returncode == nw.EXIT_REFUSED
        and "checkpoint-mismatch" in mismatch.stdout
    )


def test_reparse_points_are_skipped_and_recorded(sandbox: Path, tmp_path: Path) -> None:
    make_repo(sandbox / "ws" / "alpha")
    target = sandbox / "ws" / "alpha"
    link = sandbox / "ws" / "link"
    try:
        if IS_NT:
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                check=True,
                capture_output=True,
            )
        else:
            os.symlink(target, link, target_is_directory=True)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("cannot create a link on this host")
    _, report = audit([sandbox / "ws"], tmp=tmp_path)
    assert report["coverage"]["reparse_points"]["count"] == 1
    assert len(report["repositories"]) == 1  # the link did not duplicate the repository


def test_audit_report_refuses_to_overwrite_an_existing_file(
    sandbox: Path, tmp_path: Path
) -> None:
    out = tmp_path / "report.json"
    out.write_text("keep", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "audit",
            "--root",
            str(sandbox),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert (
        proc.returncode == nw.EXIT_REFUSED and out.read_text(encoding="utf-8") == "keep"
    )


# --------------------------------------------------------------------------- hostile Git configuration


def test_hostile_git_configuration_launches_nothing_and_changes_nothing(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = make_repo(sandbox / "ws" / "hostile")
    wt = add_worktree(repo, sandbox / "ws" / "hostile-wt", "hostile-wt")
    marker = tmp_path / "PROGRAM-RAN"
    script = tmp_path / "boom.py"
    script.write_text(
        f"import pathlib,sys\npathlib.Path({str(marker)!r}).open('a').write('ran\\n')\nsys.stdin.buffer.read()\n",
        encoding="utf-8",
    )
    program = f'"{sys.executable}" "{script}"'.replace("\\", "/")
    (repo / ".gitattributes").write_text(
        "*.txt filter=boom diff=boom\n", encoding="utf-8"
    )
    git("add", ".gitattributes", cwd=repo)
    git("commit", "-q", "-m", "attrs", cwd=repo)
    for key in (
        "filter.boom.clean",
        "filter.boom.smudge",
        "filter.boom.process",
        "diff.boom.textconv",
        "diff.boom.command",
        "core.fsmonitor",
        "diff.external",
        "core.editor",
        "core.pager",
    ):
        git("config", key, program, cwd=repo)
    git("config", "core.hooksPath", str(tmp_path / "hooks"), cwd=repo)
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    for hook in (
        "post-checkout",
        "pre-commit",
        "fsmonitor-watchman",
        "post-index-change",
        "reference-transaction",
    ):
        (hooks / hook).write_text(
            f"#!/bin/sh\necho ran >> '{marker.as_posix()}'\n", encoding="utf-8"
        )
    # Make tracked files stat-dirty so a clean filter would be consulted, and add untracked and ignored files.
    (wt / "a.txt").write_text("changed\n", encoding="utf-8")
    (wt / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (wt / "x.log").write_text("ignored\n", encoding="utf-8")
    (wt / "new.txt").write_text("untracked\n", encoding="utf-8")
    before = tree_snapshot(sandbox / "ws")
    code, report = audit([sandbox / "ws"], "--with-state", tmp=tmp_path)
    inspector = nw.GitInspector()
    state = nw.worktree_state(inspector, str(wt))
    assert not marker.exists(), (
        marker.read_text(encoding="utf-8") if marker.exists() else ""
    )
    assert state["dirty"] and state["ignored_count"] >= 1
    assert tree_snapshot(sandbox / "ws") == before
    finding = next(f for f in report["findings"] if f["kind"] == "executable-config")
    assert (
        "filter.boom.clean" in finding["detail"]
        and "core.fsmonitor" in finding["detail"]
        and program not in json.dumps(report)
    )
    assert code == 0
    # Control: the same fixture does launch the program under a plain Git call, so the
    # absence above comes from the inspection profile and not from an inert fixture.
    git("status", "--porcelain", cwd=wt, check=False)
    assert marker.exists()


def test_inspection_refuses_commands_outside_its_allowlist(sandbox: Path) -> None:
    inspector = nw.GitInspector()
    for argv in (
        ["push"],
        ["worktree", "add", "x"],
        ["config", "user.name", "x"],
        ["gc"],
    ):
        with pytest.raises(nw.PolicyError) as caught:
            inspector.run(argv, cwd=str(sandbox))
        assert caught.value.code == "git-command-not-allowed"


def test_git_resolving_inside_the_inspected_tree_is_refused(
    sandbox: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = sandbox / ("git.exe" if IS_NT else "git")
    fake.write_text("x", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(sandbox) + os.pathsep + os.environ["PATH"])
    with pytest.raises(nw.PolicyError) as caught:
        nw.trusted_git(inside=sandbox)
    assert caught.value.code == "git-untrusted"


def test_stalled_directory_read_is_abandoned_and_recorded_not_hung(sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading
    import time

    make_repo(sandbox / "ws" / "alpha")
    for name in ("stall-a", "stall-b"):
        (sandbox / "ws" / name).mkdir()
    release = threading.Event()
    real = os.scandir

    def stalled(path: object = ".") -> object:
        if Path(os.fspath(path)).name.startswith("stall-"):  # type: ignore[arg-type]
            release.wait(30)
        return real(path)

    monkeypatch.setattr(os, "scandir", stalled)
    try:
        started = time.monotonic()
        scanner = nw.Scanner(nw.ScanOptions(roots=[str(sandbox)], dir_timeout=0.4))
        scanner.run()
        elapsed = time.monotonic() - started
    finally:
        release.set()
    report = nw.build_report(scanner, nw.GitInspector(), None)
    assert elapsed < 10, "the scan must not wait for the stalled reads"
    assert report["status"] == "partial" and report["coverage"]["access_failures"]["count"] == 2
    assert {f["reason"] for f in report["coverage"]["access_failures"]["sample"]} == {"TimeoutError"}
    assert len(report["repositories"]) == 1, "healthy directories were still scanned"


def test_repeated_stalls_stop_the_scan_as_storage_unresponsive(sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading

    for index in range(4):
        (sandbox / f"stall-{index}").mkdir()
    release = threading.Event()
    real = os.scandir

    def stalled(path: object = ".") -> object:
        if Path(os.fspath(path)).name.startswith("stall-"):  # type: ignore[arg-type]
            release.wait(30)
        return real(path)

    monkeypatch.setattr(os, "scandir", stalled)
    try:
        scanner = nw.Scanner(nw.ScanOptions(roots=[str(sandbox)], dir_timeout=0.3))
        scanner.run()
    finally:
        release.set()
    assert scanner.interrupted == "storage-unresponsive"
    assert nw.build_report(scanner, nw.GitInspector(), None)["resumable"] is True


def test_user_wide_filters_are_neutralized_but_not_reported_as_repository_findings(sandbox: Path, tmp_path: Path) -> None:
    with open(os.environ["GIT_CONFIG_GLOBAL"], "a", encoding="utf-8") as handle:
        handle.write("[filter \"lfs\"]\n\tclean = git-lfs clean -- %f\n\tsmudge = git-lfs smudge -- %f\n")
    make_repo(sandbox / "ws" / "clean-repo")
    inspector = nw.GitInspector()
    assert "filter.lfs.clean" in inspector.config_keys(cwd=str(sandbox / "ws" / "clean-repo"))
    assert inspector.local_config_keys(cwd=str(sandbox / "ws" / "clean-repo")) == []
    _, report = audit([sandbox / "ws"], tmp=tmp_path)
    assert not [f for f in report["findings"] if f["kind"] == "executable-config"]
# --------------------------------------------------------------------------- hardening after review


def test_a_git_planted_in_the_current_directory_is_never_the_one_that_runs(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = sandbox / "PLANTED-RAN"
    planted = sandbox / ("git.bat" if IS_NT else "git")
    planted.write_text(
        (
            f'@echo off\necho ran> "{marker}"\n'
            if IS_NT
            else f"#!/bin/sh\necho ran > '{marker}'\n"
        ),
        encoding="utf-8",
    )
    planted.chmod(0o755)
    monkeypatch.chdir(sandbox)
    found = nw.trusted_git()
    assert os.path.isabs(found) and Path(found).resolve().parent != sandbox.resolve()
    nw.GitInspector().run(["rev-parse", "--is-bare-repository"], cwd=str(sandbox))
    assert not marker.exists()
    monkeypatch.setenv("PATH", ".")
    with pytest.raises(nw.PolicyError) as caught:
        nw.trusted_git()
    assert caught.value.code in {"git-untrusted", "git-missing"}


def test_an_unreadable_git_configuration_cannot_be_verified() -> None:
    class Result:
        returncode, stdout, stderr = 128, "", "fatal: bad config"

    inspector = nw.GitInspector(git="git", runner=lambda *_a, **_k: Result())
    with pytest.raises(nw.PolicyError) as caught:
        inspector.config_keys(cwd=".")
    assert caught.value.code == "config-unreadable" and caught.value.cannot_verify


def test_every_child_process_gets_a_closed_stdin_and_status_ignores_submodules(
    sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[dict] = []

    class Result:
        returncode, stdout, stderr = 0, "", ""

    def fake(argv, **kwargs):  # noqa: ANN001
        seen.append({"argv": argv, **kwargs})
        return Result()

    inspector = nw.GitInspector(git="git", runner=fake)
    inspector.run(["rev-parse", "HEAD"], cwd=".")
    inspector.run_bytes(["diff", "HEAD"], cwd=".")
    monkeypatch.setattr(nw.subprocess, "run", fake)
    nw.git_write(inspector, ["status"], ".")
    nw.run_smoke({"smoke": {"argv": ["x"]}, "destination": "."})
    assert len(seen) >= 4 and all(call["stdin"] is subprocess.DEVNULL for call in seen)
    seen.clear()
    nw.worktree_state(nw.GitInspector(git="git", runner=fake), ".")
    status = next(call["argv"] for call in seen if "status" in call["argv"])
    assert "--ignore-submodules=all" in status
    with pytest.raises(nw.PolicyError):
        inspector.run_bytes(["log"], cwd=".")
