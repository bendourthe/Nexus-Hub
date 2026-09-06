"""Ownership-aware file writes shared by the native-surface adapters.

``IntegrationBase._copy_file`` is ownership-blind: any existing destination is
"kept" unless the whole install runs with ``--overwrite``. That is the right
default for a bulk tree copy, but it cannot express the contract the v3.15.8
native surfaces need, where a file Nexus-Hub generated must be repaired when it
drifts while a file the user wrote must be left alone. The distinguishing
information is the install manifest, so the write consults it.

This primitive was introduced for Codex in Phase 5 and is used by Kimi in
Phase 7. It lives here rather than in either platform's module so there is one
implementation of "is this ours?" across every adapter that needs it.
"""

from __future__ import annotations

import os
import stat
import uuid
from pathlib import Path

from .result import FileAction


def is_owned(ctx, key: str, path: Path) -> bool:
    """True when the manifest records ``path`` as written by this integration."""
    return str(path) in set(ctx.manifest.files_for(key))


def _is_junction(path: Path) -> bool:
    checker = getattr(path, "is_junction", None)
    try:
        if checker is not None and checker():
            return True
        reparse_tag = getattr(path.lstat(), "st_reparse_tag", None)
    except OSError:
        return False
    mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", None)
    return mount_point_tag is not None and reparse_tag == mount_point_tag


def _is_link_like(path: Path) -> bool:
    """Return whether replacing ``path`` must not reuse its current inode."""
    if path.is_symlink() or _is_junction(path):
        return True
    try:
        return path.lstat().st_nlink > 1
    except OSError:
        return False


def _relative_within(destination: Path, managed_root: Path) -> Path | None:
    """Return ``destination`` relative to ``managed_root``, or None if outside it.

    Containment is a question about locations, not spellings. Windows 8.3 short
    names and POSIX symlinked parents denote the same directory as their long
    forms while comparing unequal, and ``os.path.abspath`` normalizes neither.
    Comparing only the ``abspath`` spellings therefore turned every write under
    such a root into a silent refusal reported as "kept", with nothing on disk
    and no error raised, so an installer reported success and delivered nothing
    (v4.3.0 Phase 5 regression).

    The canonical comparison is a fallback, never the primary test: the caller
    must walk the ORIGINAL spelling to see symlinked ancestors at all, because
    ``realpath`` resolves exactly the entries that guard exists to detect.
    """
    try:
        return destination.relative_to(managed_root)
    except ValueError:
        pass
    try:
        canonical_root = Path(os.path.realpath(managed_root))
        canonical_destination = Path(os.path.realpath(destination))
        return canonical_destination.relative_to(canonical_root)
    except (OSError, ValueError):
        return None


def _link_like_managed_ancestor(ctx, dst: Path) -> Path | None:
    """Return the first redirecting ancestor inside this install's scope."""
    managed_root = Path(os.path.abspath(ctx.target_root))
    destination = Path(os.path.abspath(dst))
    relative = _relative_within(destination, managed_root)
    if relative is None:
        # The destination is not inside this install's managed root, so there is
        # no managed ancestor to police. Global-scope installs legitimately write
        # outside target_root (~/.copilot, ~/.claude, the VS Code user dir), and
        # refusing those wrote nothing while reporting "kept" (v4.3.0 Phase 5).
        # Leaf-level protection still applies in write_owned_file: a symlink,
        # junction, or hard-linked destination is never written through, and the
        # replacement is an atomic directory-entry swap.
        return None

    current = managed_root
    for part in relative.parts[:-1]:
        current /= part
        if current.is_symlink() or _is_junction(current):
            return current
    return None


def _atomic_replace_bytes(dst: Path, content: bytes) -> None:
    """Replace one directory entry without ever opening ``dst`` for writing."""
    temporary = dst.with_name(f".{dst.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o666,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.replace(temporary, dst)
    finally:
        temporary.unlink(missing_ok=True)


def write_owned_file(ctx, key: str, dst: Path, content: bytes) -> FileAction:
    """Write a generated file, never clobbering one Nexus-Hub does not own.

    An existing destination that the manifest does not record as ours is a
    user-authored file, so it is kept (unless ``--overwrite`` is explicit).
    A destination we do own is refreshed on byte-difference, which is what makes
    an upgrade idempotent and a drifted file repairable.
    """
    link_like_ancestor = _link_like_managed_ancestor(ctx, dst)
    if link_like_ancestor is not None:
        ctx.manifest.log(
            key,
            f"refuse-link-like-ancestor ({link_like_ancestor}): {dst}",
        )
        return FileAction(path=str(dst), action="kept")

    entry_exists = dst.exists() or dst.is_symlink() or _is_junction(dst)
    if entry_exists:
        link_like = _is_link_like(dst)
        if not is_owned(ctx, key, dst) and not ctx.overwrite:
            ctx.manifest.log(key, f"skip-existing (user-authored): {dst}")
            return FileAction(path=str(dst), action="kept")
        if not link_like and dst.is_file() and dst.read_bytes() == content:
            ctx.manifest.track(key, str(dst))
            return FileAction(path=str(dst), action="unchanged")
        if _is_junction(dst):
            ctx.manifest.log(key, f"refuse-managed-junction: {dst}")
            return FileAction(path=str(dst), action="kept")
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            _atomic_replace_bytes(dst, content)
        ctx.manifest.track(key, str(dst))
        return FileAction(path=str(dst), action="updated")
    if not ctx.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        _atomic_replace_bytes(dst, content)
    ctx.manifest.track(key, str(dst))
    return FileAction(path=str(dst), action="created")


def remove_dir_if_empty(path: Path, ctx, result) -> None:
    """Drop a directory only when teardown emptied it completely.

    Per-file tracking means removing the files leaves the parent behind, which
    reads as an install that did not fully uninstall. Removal is best-effort on
    purpose: on Windows a file whose handle is still open by another process
    enters a delete-pending state where it no longer appears in a directory
    listing but still blocks ``rmdir`` with ``PermissionError``. A leftover empty
    directory is cosmetic, whereas raising here would abort the rest of the
    teardown and leave real content behind, so the failure is recorded and
    execution continues.
    """
    if not path.is_dir() or any(path.iterdir()):
        return
    if ctx.dry_run:
        result.add(str(path), "removed")
        return
    try:
        path.rmdir()
    except OSError as exc:
        ctx.manifest.log("install", f"keep-dir (not removable): {path} ({exc})")
        result.add(str(path), "kept")
        return
    result.add(str(path), "removed")


__all__ = ["is_owned", "remove_dir_if_empty", "write_owned_file"]
