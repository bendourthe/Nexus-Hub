"""Containment, identity, and lifecycle guarantees for security-review artifacts.

The interesting cases here are the ones a leaf-only check would pass: a link at
the ROOT, a link at an ANCESTOR, a hard-linked alias, and a file swapped between
validation and open. Each of those reads plausible bytes from the wrong place,
which is precisely the failure a containment primitive exists to stop.

Symlink creation needs privileges on Windows, so the link tests self-skip rather
than failing for an unrelated reason. The skip is reported, never silent: a
suite that quietly stops testing links on the platform with the weaker guarantee
would be worse than no suite.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_MODULE_PATH = (
    _ROOT
    / "catalog"
    / "skills"
    / "code-review"
    / "security-review"
    / "scripts"
    / "_safe_artifact.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("_safe_artifact_under_test", _MODULE_PATH)
    assert spec and spec.loader, f"cannot load {_MODULE_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


safe = _load()


def _can_symlink(tmp_path: Path) -> bool:
    probe = tmp_path / "_symlink_probe"
    target = tmp_path / "_symlink_target"
    target.write_text("x", encoding="utf-8")
    try:
        probe.symlink_to(target)
    except (OSError, NotImplementedError):
        return False
    probe.unlink()
    return True


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "file.txt").write_text("payload", encoding="utf-8")
    return root


# --------------------------------------------------------------------------
# Platform posture is reported, not hidden
# --------------------------------------------------------------------------


def test_platform_guarantee_is_one_of_the_two_documented_values() -> None:
    assert safe.platform_guarantee() in {"prevention", "detection"}


def test_race_safe_primitives_are_available_on_this_host() -> None:
    safe.require_race_safe_primitives()


# --------------------------------------------------------------------------
# Containment
# --------------------------------------------------------------------------


def test_a_contained_path_is_accepted(tree: Path) -> None:
    resolved = safe.assert_contained(tree, tree / "pkg" / "file.txt")
    assert resolved.name == "file.txt"


def test_a_path_outside_the_root_is_rejected(tree: Path) -> None:
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.assert_contained(tree, tree.parent / "elsewhere.txt")
    assert exc.value.code == "outside_root"


def test_a_dot_dot_escape_is_rejected(tree: Path) -> None:
    """Containment is checked after resolution, or `root/../x` satisfies it."""
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.assert_contained(tree, tree / ".." / "escape.txt")
    assert exc.value.code == "outside_root"


def test_reading_a_contained_file_returns_its_bytes(tree: Path) -> None:
    assert safe.open_contained_bytes(tree, tree / "pkg" / "file.txt") == b"payload"


def test_digest_returns_only_a_digest_and_a_size(tree: Path) -> None:
    digest, size = safe.digest_contained_file(tree, tree / "pkg" / "file.txt")
    assert size == len(b"payload")
    assert len(digest) == 64 and digest == digest.lower()


# --------------------------------------------------------------------------
# Links at the root, at an ancestor, and at the leaf
# --------------------------------------------------------------------------


def test_a_link_at_the_leaf_is_rejected(tmp_path: Path, tree: Path) -> None:
    if not _can_symlink(tmp_path):
        pytest.skip("this host does not permit symlink creation")
    secret = tmp_path / "outside-secret.txt"
    secret.write_text("credential", encoding="utf-8")
    link = tree / "pkg" / "innocent.txt"
    link.symlink_to(secret)

    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, link)
    assert exc.value.code in {"link_in_chain", "outside_root"}


def test_a_link_at_an_ancestor_is_rejected(tmp_path: Path, tree: Path) -> None:
    """A leaf-only check passes this and reads bytes from outside the root."""
    if not _can_symlink(tmp_path):
        pytest.skip("this host does not permit symlink creation")
    outside = tmp_path / "outside-dir"
    outside.mkdir()
    (outside / "file.txt").write_text("credential", encoding="utf-8")
    ancestor_link = tree / "linked"
    ancestor_link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, ancestor_link / "file.txt")
    assert exc.value.code in {"link_in_chain", "outside_root"}


def test_a_link_as_the_root_itself_is_rejected(tmp_path: Path, tree: Path) -> None:
    if not _can_symlink(tmp_path):
        pytest.skip("this host does not permit symlink creation")
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(tree, target_is_directory=True)

    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.assert_no_reparse_in_chain(linked_root, linked_root / "pkg" / "file.txt")
    assert exc.value.code == "root_is_link"


def test_a_hard_linked_file_is_rejected(tree: Path, tmp_path: Path) -> None:
    """A hard link has no distinguishable real path.

    An alias outside the root reads identical bytes while defeating containment,
    and there is no way to tell which name is the legitimate one.
    """
    original = tree / "pkg" / "file.txt"
    alias = tmp_path / "alias.txt"
    try:
        os.link(original, alias)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("this host does not support hard links here")

    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, original)
    assert exc.value.code == "hard_linked"


def test_a_directory_is_not_a_readable_artifact(tree: Path) -> None:
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, tree / "pkg")
    assert exc.value.code in {"not_regular_file", "unopenable"}


def _make_junction(link: Path, target: Path) -> bool:
    """Create a Windows junction, which needs no elevation. Returns success."""
    if sys.platform != "win32":
        return False
    import subprocess

    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0 and link.exists()


def test_an_ancestor_junction_is_rejected_even_when_it_points_inside(tmp_path: Path) -> None:
    """Regression: resolving before the chain walk destroyed the evidence.

    The first version of `assert_no_reparse_in_chain` called `resolve()` to work
    out the relative path, which FOLLOWS the junction and returns the real
    location. The chain walk then saw only genuine directories and reported
    clean, so a junction whose target happened to sit inside the root was read
    without complaint.

    This case runs unprivileged on Windows, which is why it caught a defect the
    symlink tests above could not: they skip on the very platform whose
    guarantee is the weaker of the two.
    """
    root = tmp_path / "root"
    real = root / "real"
    real.mkdir(parents=True)
    (real / "file.txt").write_text("credential", encoding="utf-8")
    link = root / "link"
    if not _make_junction(link, real):
        pytest.skip("this host cannot create a junction")

    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(root, link / "file.txt")
    assert exc.value.code == "link_in_chain"


def test_a_root_relative_target_is_read_from_the_root(tmp_path: Path) -> None:
    """A relative target must resolve against the ROOT, never the process CWD.

    Resolving it against the working directory is a silent redirect: the read
    succeeds and returns the wrong file's bytes.
    """
    root = tmp_path / "root"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "file.txt").write_text("payload", encoding="utf-8")
    assert safe.open_contained_bytes(root, Path("pkg/file.txt")) == b"payload"


def test_a_relative_dot_dot_target_is_rejected(tree: Path) -> None:
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, Path("../escape.txt"))
    assert exc.value.code == "outside_root"


def test_a_missing_file_reports_a_stable_code(tree: Path) -> None:
    """Every refusal carries a code a caller can record as a reason code.

    A bare OSError escaping here would read as a crash rather than a refusal,
    and could not be recorded in a receipt at all.
    """
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, tree / "pkg" / "absent.txt")
    assert exc.value.code == "unstattable"


# --------------------------------------------------------------------------
# Byte ceiling, at the limit and one beyond
# --------------------------------------------------------------------------


def test_a_file_at_the_exact_ceiling_is_read(tree: Path) -> None:
    target = tree / "pkg" / "exact.bin"
    target.write_bytes(b"a" * 1024)
    assert len(safe.open_contained_bytes(tree, target, max_bytes=1024)) == 1024


def test_a_file_one_byte_over_the_ceiling_is_rejected(tree: Path) -> None:
    target = tree / "pkg" / "over.bin"
    target.write_bytes(b"a" * 1025)
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, target, max_bytes=1024)
    assert exc.value.code == "artifact_too_large"


# --------------------------------------------------------------------------
# Post-open swap detection
# --------------------------------------------------------------------------


def test_a_post_open_swap_is_detected(tree: Path, monkeypatch) -> None:
    """The window between validating a path and opening it must not be trusted.

    Injecting a different file identity from `fstat` is the deterministic form of
    a real swap, which would otherwise need a race to reproduce.
    """
    target = tree / "pkg" / "file.txt"
    real_fstat = os.fstat

    class _Swapped:
        def __init__(self, base):
            self._base = base

        def __getattr__(self, name):
            if name == "st_ino":
                return self._base.st_ino + 1
            return getattr(self._base, name)

    monkeypatch.setattr(os, "fstat", lambda fd: _Swapped(real_fstat(fd)))
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, target)
    assert exc.value.code == "post_open_swap"


# --------------------------------------------------------------------------
# Owned temporary roots and validated cleanup
# --------------------------------------------------------------------------


def test_an_owned_root_is_created_and_removed() -> None:
    with safe.owned_temp_root() as root:
        assert root.is_dir()
        held = root
    assert not held.exists()


def test_cleanup_refuses_a_directory_it_did_not_create(tmp_path: Path) -> None:
    """Cleanup that trusts its argument is an arbitrary-deletion primitive."""
    victim = tmp_path / "users-important-tree"
    victim.mkdir()
    (victim / "keep.txt").write_text("precious", encoding="utf-8")

    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.cleanup_owned_root(victim)
    assert exc.value.code in {"cleanup_target_not_owned", "cleanup_target_outside_temp"}
    assert (victim / "keep.txt").is_file(), "cleanup deleted a tree it did not own"


def test_cleanup_refuses_a_link(tmp_path: Path) -> None:
    if not _can_symlink(tmp_path):
        pytest.skip("this host does not permit symlink creation")
    real = tmp_path / "real-tree"
    real.mkdir()
    (real / "keep.txt").write_text("precious", encoding="utf-8")
    link = tmp_path / "link-tree"
    link.symlink_to(real, target_is_directory=True)

    with pytest.raises(safe.UnsafeArtifactError):
        safe.cleanup_owned_root(link)
    assert (real / "keep.txt").is_file()


def test_cleanup_on_a_missing_root_is_a_no_op(tmp_path: Path) -> None:
    safe.cleanup_owned_root(tmp_path / "never-existed")


# --------------------------------------------------------------------------
# Atomic writes
# --------------------------------------------------------------------------


def test_atomic_write_creates_the_file_and_leaves_no_staging(tmp_path: Path) -> None:
    destination = tmp_path / "out.json"
    safe.atomic_write_bytes(destination, b'{"a": 1}')
    assert destination.read_bytes() == b'{"a": 1}'
    assert [p.name for p in tmp_path.iterdir()] == ["out.json"]


def test_the_staging_file_is_created_owner_only(tmp_path: Path, monkeypatch) -> None:
    """Asserted by spying on the os.open MODE, not by reading st_mode back.

    On Windows `stat.S_IMODE` reflects only the read-only bit, so a mode-readback
    assertion would pass against a world-writable staging mode on one of the two
    supported platforms. The argument is the observable that actually differs.
    """
    modes: list[int] = []
    real_open = os.open

    def spy_open(path, flags, *args, **kwargs):
        if args:
            modes.append(args[0])
        elif "mode" in kwargs:
            modes.append(kwargs["mode"])
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)
    safe.atomic_write_bytes(tmp_path / "out.json", b"{}")

    assert modes, "os.open was never called with an explicit mode; the spy is not wired"
    assert all(mode == 0o600 for mode in modes), (
        f"staging mode must be owner-only, saw {[oct(m) for m in modes]}"
    )


def test_an_existing_destination_keeps_its_own_mode(tmp_path: Path) -> None:
    """os.replace carries the SOURCE mode, so a refresh must reapply the target's."""
    if sys.platform == "win32":
        pytest.skip("POSIX mode bits are not meaningful on Windows")
    destination = tmp_path / "out.json"
    destination.write_bytes(b"{}")
    os.chmod(destination, 0o640)

    safe.atomic_write_bytes(destination, b'{"updated": true}')
    assert oct(destination.stat().st_mode & 0o777) == oct(0o640)


def test_atomic_write_refuses_a_link_destination(tmp_path: Path) -> None:
    if not _can_symlink(tmp_path):
        pytest.skip("this host does not permit symlink creation")
    outside = tmp_path / "outside.txt"
    outside.write_text("original", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(outside)

    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.atomic_write_bytes(link, b"overwritten")
    assert exc.value.code == "destination_is_link"
    assert outside.read_text(encoding="utf-8") == "original"


def test_safe_copy_writes_bytes_without_carrying_source_metadata(tree: Path, tmp_path: Path) -> None:
    destination = tmp_path / "copied" / "file.txt"
    digest, size = safe.safe_copy_file(tree, tree / "pkg" / "file.txt", destination)
    assert destination.read_bytes() == b"payload"
    assert size == len(b"payload") and len(digest) == 64
    assert not destination.is_symlink()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction boundary")
def test_root_junction_is_rejected_without_symlink_privilege(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "file.txt").write_text("outside")
    link = tmp_path / "root-link"
    if not _make_junction(link, real):
        pytest.fail("Windows junction fixture could not be created")
    try:
        with pytest.raises(safe.UnsafeArtifactError):
            safe.open_contained_bytes(link, link / "file.txt")
    finally:
        os.rmdir(link)


@pytest.mark.skipif(os.name != "nt", reason="Windows delete-sharing boundary")
def test_directory_guard_prevents_ancestor_rename(tmp_path: Path) -> None:
    directory = tmp_path / "locked"
    directory.mkdir()
    with safe._directory_guard(directory), pytest.raises(PermissionError):
        directory.rename(tmp_path / "moved")
    assert directory.is_dir()


def test_forged_cleanup_sentinel_does_not_authorize_deletion(tmp_path: Path) -> None:
    victim = tmp_path / "unowned"
    victim.mkdir()
    (victim / safe._SENTINEL_NAME).write_text("forged")
    (victim / "keep.txt").write_text("keep")
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.cleanup_owned_root(victim)
    assert exc.value.code == "cleanup_target_not_owned"
    assert (victim / "keep.txt").read_text() == "keep"


def test_copy_identity_is_derived_from_exact_written_bytes(tree: Path, tmp_path: Path, monkeypatch) -> None:
    import hashlib

    original = safe.open_contained_bytes
    reads = []

    def changing_read(*args, **kwargs):
        payload = original(*args, **kwargs)
        reads.append(payload)
        (tree / "pkg/file.txt").write_bytes(b"changed after read")
        return payload

    monkeypatch.setattr(safe, "open_contained_bytes", changing_read)
    destination = tmp_path / "copy.txt"
    digest, size = safe.safe_copy_file(tree, tree / "pkg/file.txt", destination)
    assert len(reads) == 1
    assert digest == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert size == destination.stat().st_size


@pytest.mark.parametrize("limit", [-1, True, safe.MAX_ARTIFACT_BYTES + 1])
def test_invalid_read_limit_is_refused(tree: Path, limit) -> None:
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.open_contained_bytes(tree, tree / "pkg/file.txt", limit)
    assert exc.value.code == "invalid_byte_limit"


def test_interrupted_atomic_write_preserves_destination(tmp_path: Path, monkeypatch) -> None:
    destination = tmp_path / "record.json"
    destination.write_bytes(b"previous")

    def interrupted(*args):
        raise PermissionError("injected replacement failure")

    monkeypatch.setattr(safe.os, "replace", interrupted)
    with pytest.raises(PermissionError):
        safe.atomic_write_bytes(destination, b"next")
    assert destination.read_bytes() == b"previous"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["record.json"]


def test_cleanup_rejects_replaced_token_and_preserves_contents() -> None:
    with safe.owned_temp_root() as root:
        sentinel = root / safe._SENTINEL_NAME
        original = sentinel.read_bytes()
        (root / "keep.txt").write_text("keep")
        sentinel.write_text("forged")
        try:
            with pytest.raises(safe.UnsafeArtifactError) as exc:
                safe.cleanup_owned_root(root)
            assert exc.value.code == "cleanup_target_not_owned"
            assert (root / "keep.txt").read_text() == "keep"
        finally:
            sentinel.write_bytes(original)


def test_absent_identity_primitive_fails_closed(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(safe.os, "lstat", lambda path: SimpleNamespace(st_ino=0, st_dev=0))
    with pytest.raises(safe.UnsafeArtifactError) as exc:
        safe.require_race_safe_primitives()
    assert exc.value.code == "no_race_safe_primitives"
