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

from pathlib import Path

from .result import FileAction


def is_owned(ctx, key: str, path: Path) -> bool:
    """True when the manifest records ``path`` as written by this integration."""
    return str(path) in set(ctx.manifest.files_for(key))


def write_owned_file(ctx, key: str, dst: Path, content: bytes) -> FileAction:
    """Write a generated file, never clobbering one Nexus-Hub does not own.

    An existing destination that the manifest does not record as ours is a
    user-authored file, so it is kept (unless ``--overwrite`` is explicit).
    A destination we do own is refreshed on byte-difference, which is what makes
    an upgrade idempotent and a drifted file repairable.
    """
    if dst.exists():
        if dst.read_bytes() == content:
            ctx.manifest.track(key, str(dst))
            return FileAction(path=str(dst), action="unchanged")
        if not is_owned(ctx, key, dst) and not ctx.overwrite:
            ctx.manifest.log(key, f"skip-existing (user-authored): {dst}")
            return FileAction(path=str(dst), action="kept")
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content)
        ctx.manifest.track(key, str(dst))
        return FileAction(path=str(dst), action="updated")
    if not ctx.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(content)
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
