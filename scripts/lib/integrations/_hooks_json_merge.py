"""Ownership-scoped merge for Cursor- and Antigravity-shaped hooks.json (v4.13.2).

Cursor (`{"version": 1, "hooks": {event: [{"command": ...}]}}`) and Antigravity
(`{"<set name>": {"enabled": true, event: [...]}}`) both used to keep a user-edited
hooks.json untouched, which silently left any newly shipped hook uninstalled. This
module gives both the guarantees Codex's `merge_hooks_json` already has:

  - only Nexus-Hub's own entries are replaced; every user entry survives,
  - a malformed or non-object file is never overwritten (kept, reason logged),
  - the previous content is backed up beside the file before the first change,
  - writes go through a temp file, so a failure leaves the original intact,
  - teardown removes only Nexus-Hub entries and deletes the file only when
    nothing else remains.

Ownership is decided by the caller's predicate over an entry's command, the same
signal `_hooks_common.handler_is_owned` uses (a command pointing into the
installed hooks directory). Stdlib only; no outbound calls.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

from .result import FileAction

Owned = Callable[[dict], bool]


def _load(dst: Path) -> tuple[dict | None, str]:
    """Return (object or None, reason). None means: do not touch this file."""
    if not dst.exists():
        return {}, ""
    raw = dst.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        return None, f"skip-malformed-json: {dst} ({exc})"
    if not isinstance(parsed, dict):
        return None, f"skip-non-object-json: {dst}"
    return parsed, ""


def _write(ctx, key: str, dst: Path, obj: dict) -> FileAction:
    content = (json.dumps(obj, indent=2) + "\n").encode("utf-8")
    if dst.exists() and dst.read_bytes() == content:
        ctx.manifest.track_shared(key, str(dst))
        return FileAction(path=str(dst), action="unchanged")
    existed = dst.exists()
    if not ctx.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if existed:
            backup = dst.with_suffix(dst.suffix + ".nexus-hub.bak")
            backup.write_bytes(dst.read_bytes())
            ctx.manifest.track(key, str(backup))
        tmp = dst.with_suffix(dst.suffix + ".nexus-hub.tmp")
        tmp.write_bytes(content)
        os.replace(tmp, dst)
    # Shared, not owned: teardown must prune our entries, never unlink the file.
    ctx.manifest.track_shared(key, str(dst))
    return FileAction(path=str(dst), action="updated" if existed else "created")


def _rewrite(dst: Path, obj: dict, dry_run: bool) -> FileAction:
    """Write a pruned file, restoring the user's exact bytes when nothing else changed.

    When the pruned object equals the content backed up before our first merge,
    the backup's bytes are written back, so uninstall leaves a user's file
    byte-identical (line endings and formatting included). Otherwise the file's
    existing line-ending style is kept.
    """
    backup = dst.with_suffix(dst.suffix + ".nexus-hub.bak")
    current = dst.read_bytes()
    content = (json.dumps(obj, indent=2) + "\n").encode("utf-8")
    if backup.exists():
        try:
            if json.loads(backup.read_text(encoding="utf-8")) == obj:
                content = backup.read_bytes()
        except (json.JSONDecodeError, UnicodeDecodeError):
            # An unparsable backup is not reused; the freshly rendered content is written.
            pass
    elif b"\r\n" in current:
        content = content.replace(b"\n", b"\r\n")
    if current == content:
        return FileAction(path=str(dst), action="unchanged")
    if not dry_run:
        dst.write_bytes(content)
    return FileAction(path=str(dst), action="updated")


def merge_flat_hooks(ctx, key: str, dst: Path, rendered: dict, owned: Owned) -> FileAction:
    """Merge a Cursor-shaped registration into ``dst``, preserving user entries."""
    existing, reason = _load(dst)
    if existing is None:
        ctx.manifest.log(key, reason)
        return FileAction(path=str(dst), action="kept")
    merged = dict(existing)
    for field, value in rendered.items():
        if field != "hooks":
            merged.setdefault(field, value)
    hooks = {event: [e for e in (entries or []) if not (isinstance(e, dict) and owned(e))]
             for event, entries in dict(merged.get("hooks") or {}).items()}
    for event, entries in rendered.get("hooks", {}).items():
        hooks[event] = list(hooks.get(event) or []) + list(entries)
    merged["hooks"] = {event: entries for event, entries in hooks.items() if entries}
    return _write(ctx, key, dst, merged)


def prune_flat_hooks(dst: Path, owned: Owned, dry_run: bool) -> FileAction:
    """Remove Nexus-Hub entries from a Cursor-shaped hooks.json."""
    existing, _ = _load(dst)
    if not dst.exists():
        return FileAction(path=str(dst), action="not-found")
    if existing is None:
        return FileAction(path=str(dst), action="kept")
    hooks = {}
    for event, entries in dict(existing.get("hooks") or {}).items():
        survivors = [e for e in (entries or []) if not (isinstance(e, dict) and owned(e))]
        if survivors:
            hooks[event] = survivors
    remainder = {k: v for k, v in existing.items() if k not in ("hooks", "version")}
    if not hooks and not remainder:
        if not dry_run:
            dst.unlink(missing_ok=True)
        return FileAction(path=str(dst), action="removed")
    out = {k: v for k, v in existing.items() if k != "hooks"}
    out["hooks"] = hooks
    return _rewrite(dst, out, dry_run)


def merge_named_set(ctx, key: str, dst: Path, set_name: str, rendered_set: dict) -> FileAction:
    """Replace only the ``set_name`` hook set in an Antigravity-shaped hooks.json."""
    existing, reason = _load(dst)
    if existing is None:
        ctx.manifest.log(key, reason)
        return FileAction(path=str(dst), action="kept")
    merged = dict(existing)
    merged[set_name] = rendered_set
    return _write(ctx, key, dst, merged)


def prune_named_set(dst: Path, set_name: str, dry_run: bool) -> FileAction:
    """Remove the ``set_name`` hook set; delete the file only when it was the last."""
    existing, _ = _load(dst)
    if not dst.exists():
        return FileAction(path=str(dst), action="not-found")
    if existing is None or set_name not in existing:
        return FileAction(path=str(dst), action="kept" if existing is None else "unchanged")
    remainder = {k: v for k, v in existing.items() if k != set_name}
    if not remainder:
        if not dry_run:
            dst.unlink(missing_ok=True)
        return FileAction(path=str(dst), action="removed")
    return _rewrite(dst, remainder, dry_run)


__all__ = ["merge_flat_hooks", "merge_named_set", "prune_flat_hooks", "prune_named_set"]
