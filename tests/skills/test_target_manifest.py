"""Target-content identity must be complete, deterministic, and leak nothing.

The canary tests are the important ones. Reading a git repository means running
git against configuration that repository controls, and git config can name
hooks, an fsmonitor, filters, external diff and textconv programs, and credential
helpers, several of which execute arbitrary commands. So "did the manifest come
out right" is a weaker question than "did anything the target asked for run".
Every canary here writes a marker file on execution and the assertion is that the
marker does not exist.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _ROOT / "catalog" / "skills" / "code-review" / "security-review" / "scripts"


def _load():
    spec = importlib.util.spec_from_file_location(
        "_target_manifest_under_test", _SCRIPTS / "_target_manifest.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tm = _load()


def test_previously_hashed_leaf_change_invalidates_manifest(tree: Path, monkeypatch) -> None:
    original = tm.safe.digest_contained_file

    def mutate_previous(root, path, *args, **kwargs):
        result = original(root, path, *args, **kwargs)
        if path.name == "app.py":
            (tree / "README.md").write_text("changed after its digest was recorded\n")
        return result

    monkeypatch.setattr(tm.safe, "digest_contained_file", mutate_previous)
    with pytest.raises(tm.TargetManifestError, match="leaf_changed"):
        tm.build_target_manifest(tree)

_GIT = shutil.which("git")


def _trusted_git_reason(candidate: str | None) -> str | None:
    """Return why `candidate` cannot serve as a trusted git, or None if it can.

    `resolve_trusted_git` refuses a non-regular, link-like, or hard-linked
    executable, because a hard link has no distinguishable real path. These
    tests need a git that MEETS that contract; a host whose only git fails it
    cannot exercise them, and reporting that as a failure blames the test for a
    property of the machine.

    Git for Windows is the live case: it ships `git.exe` hard-linked, and a
    stock install exposes only the hard-linked copies on PATH (`mingw64/bin`
    at `st_nlink` 4, `cmd` at 2), while the conforming `bin/git.exe` is not on
    PATH. On such a host these tests skip. CI runners whose git is a single-link
    regular file run them in full.
    """
    if candidate is None:
        return "git is not installed on this host"
    path = Path(candidate)
    try:
        info = path.lstat()
    except OSError as exc:
        return f"git at {path} cannot be stat'd: {exc.__class__.__name__}"
    if stat.S_ISLNK(info.st_mode):
        return f"git at {path} is a symlink, which resolve_trusted_git refuses"
    if not stat.S_ISREG(info.st_mode):
        return f"git at {path} is not a regular file"
    if info.st_nlink != 1:
        return (
            f"git at {path} is hard-linked (st_nlink={info.st_nlink}); "
            "resolve_trusted_git refuses it, so this host cannot supply a "
            "trusted git"
        )
    return None


_GIT_SKIP_REASON = _trusted_git_reason(_GIT)
_needs_git = pytest.mark.skipif(
    _GIT_SKIP_REASON is not None, reason=_GIT_SKIP_REASON or ""
)


@_needs_git
def test_git_never_reads_out_of_scope_tracked_content(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    (root / "included.py").write_bytes(b"x = 1\n")
    (root / "excluded.py").write_bytes(b"x = 2\n")
    subprocess.run([_GIT, "add", "."], cwd=root, check=True, capture_output=True)
    original = tm.safe.open_contained_bytes

    def scoped_read(boundary, path, *args, **kwargs):
        assert path.name != "excluded.py", "out-of-scope source was read"
        return original(boundary, path, *args, **kwargs)

    monkeypatch.setattr(tm.safe, "open_contained_bytes", scoped_read)
    result = tm.build_target_manifest(root, scope=("included.py",), git_path=Path(_GIT))
    assert result["git_classification"]["tracked_paths"] == ["included.py"]
    assert result["git_classification"]["dirty_paths"] == []


@pytest.mark.skipif(os.name != "nt", reason="Windows OS-directory policy")
def test_git_does_not_inherit_poisoned_system_directory(monkeypatch) -> None:
    monkeypatch.setenv("SystemRoot", "target-controlled-marker")
    environment = tm._git_environment()
    assert "target-controlled-marker" not in environment.values()
    assert Path(environment["SystemRoot"]).is_dir()


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    root = tmp_path / "target"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "app.py").write_text("SECRET_TOKEN = 'abc123'\n", encoding="utf-8")
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "junk.js").write_text("x", encoding="utf-8")
    return root


# --------------------------------------------------------------------------
# Shape, determinism, and non-disclosure
# --------------------------------------------------------------------------


def test_a_manifest_covers_in_scope_files_and_skips_generated_trees(tree: Path) -> None:
    manifest = tm.build_target_manifest(tree)
    paths = [entry["path"]["display"] for entry in manifest["entries"]]
    assert paths == ["README.md", "pkg/app.py"]
    assert manifest["entry_count"] == 2


def test_the_manifest_is_deterministic(tree: Path) -> None:
    first = tm.build_target_manifest(tree)
    second = tm.build_target_manifest(tree)
    assert first["manifest_digest"] == second["manifest_digest"]


def test_the_digest_excludes_itself(tree: Path) -> None:
    """Otherwise the field could never be recomputed and checked."""
    manifest = tm.build_target_manifest(tree)
    recomputed = tm.manifest_digest(manifest)
    assert recomputed == manifest["manifest_digest"]


def test_no_file_content_reaches_the_manifest(tree: Path) -> None:
    """A manifest is written to disk and quoted in evidence, so anything it
    carries is effectively published."""
    import json

    serialized = json.dumps(tm.build_target_manifest(tree))
    assert "SECRET_TOKEN" not in serialized
    assert "abc123" not in serialized
    assert "hello" not in serialized


def test_absolute_paths_do_not_reach_the_manifest(tree: Path) -> None:
    import json

    serialized = json.dumps(tm.build_target_manifest(tree))
    assert str(tree) not in serialized
    assert "target" not in json.dumps(
        [entry["path"]["display"] for entry in tm.build_target_manifest(tree)["entries"]]
    )


@pytest.mark.parametrize("name", ["private@example.invalid.txt", "token=PRIVATE_CANARY.json", "ghp_" + "A" * 30 + ".txt"])
def test_sensitive_path_values_fail_without_echo(tmp_path: Path, name: str) -> None:
    (tmp_path / name).write_text("inert canary")
    with pytest.raises(tm.TargetManifestError) as error:
        tm.build_target_manifest(tmp_path)
    assert error.value.code == "sensitive_path_metadata"
    assert name not in str(error.value)


def test_budgets_are_recorded_so_a_reader_knows_what_bounded_the_scan(tree: Path) -> None:
    budgets = tm.build_target_manifest(tree)["budgets"]
    assert budgets["max_files"] == tm.MAX_FILES
    assert budgets["max_file_bytes"] == tm.MAX_FILE_BYTES


def test_the_platform_guarantee_is_recorded(tree: Path) -> None:
    """A provenance record that claims prevention on a detection-only host is
    wrong, so the manifest carries which one it got."""
    assert tm.build_target_manifest(tree)["platform_guarantee"] in {
        "prevention",
        "detection",
    }


def test_declared_scope_restricts_the_manifest(tree: Path) -> None:
    manifest = tm.build_target_manifest(tree, scope=("pkg",))
    assert [entry["path"]["display"] for entry in manifest["entries"]] == ["pkg/app.py"]


# --------------------------------------------------------------------------
# Canonical path identity
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("a/../b", "dot_segment"),
        ("a\x01b", "control_character_in_path"),
        ("NUL", "device_name_in_path"),
        ("COM1.txt", "device_name_in_path"),
        ("a:stream", "alternate_data_stream"),
    ],
)
def test_unsafe_path_components_are_rejected(raw: str, code: str) -> None:
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.canonical_path_identity(Path(raw))
    assert exc.value.code == code


def test_an_absolute_path_is_rejected() -> None:
    absolute = Path("C:/etc/passwd") if os.name == "nt" else Path("/etc/passwd")
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.canonical_path_identity(absolute)
    assert exc.value.code == "absolute_path"


def test_path_identity_binds_bytes_not_just_display_text() -> None:
    """Two visually similar names must not collapse into one entry.

    POSIX filenames are arbitrary bytes, not text, so a manifest keyed on the
    display form alone would treat distinct files as the same one.
    """
    first = tm.canonical_path_identity(Path("pkg/app.py"))
    second = tm.canonical_path_identity(Path("pkg/App.py"))
    assert first["byte_digest"] != second["byte_digest"]
    assert first["normalization_key"] == second["normalization_key"], (
        "these differ only by case, so they must share a collision key"
    )


def test_a_case_collision_inside_one_scope_is_rejected(tmp_path: Path) -> None:
    """Two names that fold together are ambiguous on a case-insensitive host."""
    root = tmp_path / "t"
    root.mkdir()
    (root / "Alpha.txt").write_text("a", encoding="utf-8")
    try:
        (root / "alpha.txt").write_text("b", encoding="utf-8")
    except OSError:
        pytest.skip("host cannot create both spellings")
    if len(list(root.iterdir())) < 2:
        pytest.skip("host filesystem folded the two names into one")

    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(root)
    assert exc.value.code == "path_normalization_collision"


# --------------------------------------------------------------------------
# Failure is total
# --------------------------------------------------------------------------


def test_a_file_over_the_per_file_ceiling_aborts(tree: Path, monkeypatch) -> None:
    monkeypatch.setattr(tm, "MAX_FILE_BYTES", 4)
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(tree)
    assert exc.value.code == "file_too_large"


def test_a_scope_over_the_file_budget_aborts(tree: Path, monkeypatch) -> None:
    monkeypatch.setattr(tm, "MAX_FILES", 1)
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(tree)
    assert exc.value.code == "file_budget_exceeded"


def test_a_scope_over_the_byte_budget_aborts(tree: Path, monkeypatch) -> None:
    monkeypatch.setattr(tm, "MAX_TOTAL_BYTES", 3)
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(tree)
    assert exc.value.code == "byte_budget_exceeded"


def test_a_hard_linked_alias_inside_the_scope_aborts(tree: Path) -> None:
    """Two names for one inode make the manifest ambiguous about what changed."""
    alias = tree / "pkg" / "alias.py"
    try:
        os.link(tree / "pkg" / "app.py", alias)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("this host does not support hard links here")

    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(tree)
    assert exc.value.code in {"unsafe_hard_link", "hard_linked"}


def test_a_root_that_is_a_link_is_refused(tmp_path: Path, tree: Path) -> None:
    linked = tmp_path / "linked-root"
    try:
        linked.symlink_to(tree, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("this host does not permit symlink creation")
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(linked)
    assert exc.value.code == "root_is_link"


# --------------------------------------------------------------------------
# Trusted git resolution
# --------------------------------------------------------------------------


def test_no_git_path_means_no_classification_rather_than_a_guess(tree: Path) -> None:
    """Fail-closed: the manifest is still produced and says it did not classify."""
    classification = tm.build_target_manifest(tree)["git_classification"]
    assert classification["available"] is False
    assert classification["reason_code"] == "trusted_git_unavailable"


def test_a_relative_git_path_is_refused(tree: Path) -> None:
    """A target able to place a file named `git` earlier on the search path
    would otherwise choose the program this module runs."""
    assert tm.resolve_trusted_git(Path("git"), forbidden_roots=(tree,)) is None


def test_a_git_inside_the_target_is_refused(tree: Path) -> None:
    shadow = tree / "git.exe"
    shadow.write_bytes(b"MZ")
    os.chmod(shadow, 0o755)
    assert tm.resolve_trusted_git(shadow, forbidden_roots=(tree,)) is None


def test_a_nonexistent_git_path_is_refused(tmp_path: Path, tree: Path) -> None:
    assert tm.resolve_trusted_git(tmp_path / "absent-git", forbidden_roots=(tree,)) is None


@_needs_git
def test_a_trusted_git_is_accepted_and_digested(tree: Path) -> None:
    resolved = tm.resolve_trusted_git(Path(_GIT), forbidden_roots=(tree,))
    assert resolved is not None
    assert len(resolved["content_digest"]) == 64


@_needs_git
def test_an_unallowlisted_git_command_is_refused(tree: Path) -> None:
    resolved = tm.resolve_trusted_git(Path(_GIT), forbidden_roots=(tree,))
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.run_git(resolved, "push", tree, tree)
    assert exc.value.code == "git_command_not_allowed"


# --------------------------------------------------------------------------
# Git classification over a real repository
# --------------------------------------------------------------------------


def _init_repo(root: Path) -> None:
    run = lambda *a: subprocess.run(
        [_GIT, *a], cwd=root, check=True, capture_output=True
    )
    run("init", "-q")
    run("-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q",
        "--allow-empty", "-m", "init")


@_needs_git
def test_classification_reports_dirty_and_untracked_state(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    (root / "tracked.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run([_GIT, "add", "tracked.py"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        [_GIT, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-q", "-m", "add"],
        cwd=root, check=True, capture_output=True,
    )
    (root / "tracked.py").write_text("x = 2\n", encoding="utf-8")
    (root / "fresh.py").write_text("y = 1\n", encoding="utf-8")

    classification = tm.build_target_manifest(root, git_path=Path(_GIT))["git_classification"]
    assert classification["available"] is True
    assert classification["dirty_paths"] == ["tracked.py"]
    assert classification["untracked_paths"] == ["fresh.py"]
    assert len(classification["head_revision"]) >= 7
    # The digest identifies the bytes; the version says what they are. A reader
    # comparing two manifests needs both to tell a tree change from an upgrade.
    assert classification["git_version"].startswith("git version")
    assert len(classification["git_content_digest"]) == 64


# --------------------------------------------------------------------------
# Canaries: nothing the target asks for may execute
# --------------------------------------------------------------------------


@_needs_git
def test_a_repository_controlled_hook_never_runs(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    marker = tmp_path / "HOOK_RAN.marker"

    hooks = root / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    for name in ("post-index-change", "pre-commit", "post-checkout"):
        hook = hooks / name
        hook.write_text(
            f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8"
        )
        os.chmod(hook, 0o755)

    tm.build_target_manifest(root, git_path=Path(_GIT))
    assert not marker.exists(), "a repository-controlled hook executed"


@_needs_git
def test_a_repository_controlled_fsmonitor_never_runs(tmp_path: Path) -> None:
    """`core.fsmonitor` names a program git will happily execute."""
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    marker = tmp_path / "FSMONITOR_RAN.marker"

    spy = tmp_path / "spy.sh"
    spy.write_text(f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8")
    os.chmod(spy, 0o755)
    with (root / ".git" / "config").open("a", encoding="utf-8") as handle:
        handle.write(f"\n[core]\n\tfsmonitor = {spy.as_posix()}\n")

    tm.build_target_manifest(root, git_path=Path(_GIT))
    assert not marker.exists(), "a repository-controlled fsmonitor executed"


@_needs_git
def test_a_repository_controlled_external_diff_never_runs(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    marker = tmp_path / "DIFF_RAN.marker"

    spy = tmp_path / "diffspy.sh"
    spy.write_text(f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8")
    os.chmod(spy, 0o755)
    (root / "tracked.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run([_GIT, "add", "tracked.py"], cwd=root, check=True, capture_output=True)
    with (root / ".git" / "config").open("a", encoding="utf-8") as handle:
        handle.write(f"\n[diff]\n\texternal = {spy.as_posix()}\n")
    (root / "tracked.py").write_text("x = 2\n", encoding="utf-8")

    tm.build_target_manifest(root, git_path=Path(_GIT))
    assert not marker.exists(), "a repository-controlled external diff executed"


@_needs_git
def test_the_git_environment_carries_no_inherited_search_path() -> None:
    """`LD_PRELOAD` alone is enough to run attacker code inside git."""
    environment = tm._git_environment()
    for leaked in ("PATH", "PATHEXT", "LD_PRELOAD", "LD_LIBRARY_PATH", "GIT_DIR"):
        assert leaked not in environment, f"{leaked} was inherited into the git call"
    assert environment["GIT_TERMINAL_PROMPT"] == "0"


@_needs_git
def test_repository_config_is_never_parsed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    (root / ".git/config").write_text("not valid git config at all\n")
    result = tm.build_target_manifest(root, git_path=Path(_GIT))
    assert result["git_classification"]["available"] is True


@_needs_git
def test_index_and_ignored_identity_are_bound(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    (root / ".gitignore").write_text("ignored.txt\n")
    (root / "tracked.txt").write_text("one\n")
    (root / "ignored.txt").write_text("ignored content\n")
    subprocess.run([_GIT, "add", "tracked.txt"], cwd=root, check=True, capture_output=True)
    first = tm.build_target_manifest(root, git_path=Path(_GIT))
    classification = first["git_classification"]
    assert len(classification["index_digest"]) == 64
    assert classification["ignored_paths"] == ["ignored.txt"]
    assert classification["tracked_paths"] == ["tracked.txt"]
    (root / "tracked.txt").write_text("two\n")
    subprocess.run([_GIT, "add", "tracked.txt"], cwd=root, check=True, capture_output=True)
    second = tm.build_target_manifest(root, git_path=Path(_GIT))
    assert classification["index_digest"] != second["git_classification"]["index_digest"]


@_needs_git
def test_external_git_metadata_is_refused_before_git_runs(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").write_text("gitdir: ../elsewhere\n")
    invoked = []
    monkeypatch.setattr(tm, "run_git", lambda *args: invoked.append(args))
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(root, git_path=Path(_GIT))
    assert exc.value.code == "git_metadata_outside_root"
    assert invoked == []


@_needs_git
def test_submodule_gitlink_and_dirty_state_are_recorded(tmp_path: Path) -> None:
    root = tmp_path / "parent"
    root.mkdir()
    _init_repo(root)
    child = root / "child"
    child.mkdir()
    _init_repo(child)
    subprocess.run([_GIT, "add", "child"], cwd=root, check=True, capture_output=True)
    (child / "untracked.txt").write_text("inert")
    result = tm.build_target_manifest(root, git_path=Path(_GIT))["git_classification"]
    assert result["submodules"][0]["path"] == "child"
    assert len(result["submodules"][0]["gitlink"]) == 40
    assert result["submodules"][0]["classification"]["untracked_paths"] == ["untracked.txt"]
    assert "child" in result["dirty_paths"]


@_needs_git
def test_missing_submodule_checkout_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "parent"
    root.mkdir()
    _init_repo(root)
    oid = subprocess.run([_GIT, "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True).stdout.decode().strip()
    subprocess.run([_GIT, "update-index", "--add", "--cacheinfo", f"160000,{oid},absent"], cwd=root, check=True, capture_output=True)
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(root, git_path=Path(_GIT))
    assert exc.value.code == "submodule_incomplete"


@_needs_git
def test_packed_head_ref_is_bound_without_git_config(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    subprocess.run([_GIT, "pack-refs", "--all"], cwd=root, check=True, capture_output=True)
    result = tm.build_target_manifest(root, git_path=Path(_GIT))
    assert len(result["git_classification"]["head_revision"]) == 40


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_git_output_limits_stop_both_streams(tmp_path: Path, monkeypatch, stream: str) -> None:
    monkeypatch.setattr(tm, "_SAFE_CONFIG", ())
    monkeypatch.setattr(tm, "GIT_MAX_OUTPUT_BYTES", 100)
    monkeypatch.setattr(tm, "_ALLOWED_GIT_COMMANDS", {"version": ("-c", f"import sys; sys.{stream}.write('x'*101)")})
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.run_git({"path": Path(sys.executable)}, "version", tmp_path, tmp_path)
    assert exc.value.code == "git_output_overflow"


def test_git_timeout_is_a_terminal_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tm, "_SAFE_CONFIG", ())
    monkeypatch.setattr(tm, "GIT_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(tm, "_ALLOWED_GIT_COMMANDS", {"version": ("-c", "import time; time.sleep(10)")})
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.run_git({"path": Path(sys.executable)}, "version", tmp_path, tmp_path)
    assert exc.value.code == "git_timeout"


def test_walk_error_cannot_return_a_partial_manifest(tree: Path, monkeypatch) -> None:
    def denied_walk(root, *, followlinks, onerror):
        onerror(PermissionError("TEST_SECRET_CANARY"))
        return iter(())

    monkeypatch.setattr(tm.os, "walk", denied_walk)
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(tree)
    assert exc.value.code == "traversal_failed"
    assert "TEST_SECRET_CANARY" not in str(exc.value)


def test_a_directory_replaced_during_traversal_invalidates_manifest(tree: Path, monkeypatch) -> None:
    original = tm.safe.digest_contained_file
    changed = False

    def add_file(*args):
        nonlocal changed
        result = original(*args)
        if not changed:
            changed = True
            (tree / "new.txt").write_text("new")
        return result

    monkeypatch.setattr(tm.safe, "digest_contained_file", add_file)
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(tree)
    assert exc.value.code == "directory_changed"


@pytest.mark.skipif(os.name != "nt", reason="Windows junction boundary")
def test_directory_junction_is_bound_without_traversal(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    (other / "secret.txt").write_text("TEST_SECRET_CANARY")
    link = root / "directory-link"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(other)], capture_output=True, check=False)
    assert result.returncode == 0
    try:
        manifest = tm.build_target_manifest(root)
        assert manifest["entry_count"] == 1
        assert manifest["entries"][0]["kind"] == "link"
        assert len(manifest["entries"][0]["link_target_digest"]) == 64
        import json
        assert "TEST_SECRET_CANARY" not in json.dumps(manifest)
        assert str(other) not in json.dumps(manifest)
        with pytest.raises(tm.TargetManifestError):
            tm.build_target_manifest(link)
    finally:
        os.rmdir(link)


@_needs_git
def test_worktree_metadata_requires_separate_explicit_authorization(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _init_repo(repository)
    checkout = tmp_path / "checkout"
    subprocess.run([_GIT, "worktree", "add", "--detach", str(checkout), "HEAD"], cwd=repository, check=True, capture_output=True)
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(checkout, git_path=Path(_GIT))
    assert exc.value.code == "git_metadata_outside_root"
    result = tm.build_target_manifest(checkout, git_path=Path(_GIT), metadata_roots=(repository / ".git",))
    assert result["git_classification"]["available"] is True
    assert result["git_classification"]["isolation"] == "sanitized_metadata"


@_needs_git
def test_index_and_worktree_case_alias_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    (root / "lower.txt").write_text("inert")
    subprocess.run([_GIT, "add", "lower.txt"], cwd=root, check=True, capture_output=True)
    (root / "lower.txt").rename(root / "intermediate.txt")
    (root / "intermediate.txt").rename(root / "LOWER.txt")
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.build_target_manifest(root, git_path=Path(_GIT))
    assert exc.value.code == "path_normalization_collision"


@pytest.mark.parametrize("name", ["trailing.", "trailing ", "wild*.txt"])
def test_platform_dependent_path_aliases_are_rejected(name: str) -> None:
    with pytest.raises(tm.TargetManifestError) as exc:
        tm.canonical_path_identity(Path(name))
    assert exc.value.code == "path_alias_unsupported"
