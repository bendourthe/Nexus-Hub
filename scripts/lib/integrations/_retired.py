"""Remove copies of catalog items the catalog no longer ships (v4.15.5).

When a command, skill or agent leaves the catalog (a rename or a removal), a
refresh install already drops it from folders it syncs wholesale, such as
Claude Code's ``commands/``. The copies an integration renders one file at a
time were never removed: the command-skill ``skills/<name>/SKILL.md``, Codex
``prompts/<name>.md``, and the Antigravity and Windsurf ``workflows/<name>.md``.
So a removed command kept working, and kept saying it was removed, on most
platforms.

After an integration installs, :func:`retire_removed_items` compares the files
the previous install recorded for it with the files this install produced. A
recorded file that this install did not produce is removed only when every
condition below holds; otherwise it is kept and reported:

- it was written by Nexus-Hub (recorded as ``created``, ``updated`` or
  ``unchanged``, never ``kept``) and has a recorded hash;
- its bytes still match that hash, so a copy the user edited stays;
- it sits in a catalog-content folder (``skills/<name>/``, ``commands/``,
  ``prompts/``, ``workflows/``, ``agents/``) and ``<name>`` is no longer a
  catalog command, skill or agent. An item that still exists but was not
  installed this time (a narrower selection, an opt-in surface turned off)
  is therefore never touched;
- it is a regular file inside the install target, reached without a symlink
  or junction.

Nothing runs on a dry run or an instruction-only install. Folders emptied by a
removal are removed with ``rmdir`` only, up to but never including the content
folder itself.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from ._detection import _norm
from ._stale import _linked, _sha256, _via_link
from .base import long_path
from .result import FileAction, WriteResult

#: Folders whose entries are named after a catalog item.
CONTENT_DIRS = frozenset({"skills", "commands", "prompts", "workflows", "agents"})

#: Record actions that mean Nexus-Hub wrote the file (``kept`` means it did not).
_WRITTEN = frozenset({"created", "updated", "unchanged"})

#: Suffixes a rendered command or agent file can carry, longest first.
_SUFFIXES = (".prompt.md", ".md", ".toml", ".mdc")

_NAMES_CACHE: Dict[str, Optional[Tuple[FrozenSet[str], FrozenSet[str]]]] = {}


def catalog_names(repo_root: Path) -> Optional[Tuple[FrozenSet[str], FrozenSet[str]]]:
    """Return ``(item names, skill category names)`` from the catalog, or None.

    Item names are command and agent file stems plus every folder holding a
    ``SKILL.md``. Unlike the stale-platform check, other file stems do not
    count: a skill's ``examples/status.md`` must not keep ``/status`` alive.
    """
    for candidate in (Path(repo_root) / "catalog", Path(repo_root) / "src" / "catalog"):
        key = str(candidate)
        if key in _NAMES_CACHE:
            return _NAMES_CACHE[key]
        commands = candidate / "commands"
        skills = candidate / "skills"
        if not (commands.is_dir() and skills.is_dir()):
            continue
        names = {p.stem.lower() for p in commands.glob("*.md")}
        agents = candidate / "agents"
        if agents.is_dir():
            names.update(p.stem.lower() for p in agents.iterdir() if p.is_file())
        names.update(p.parent.name.lower() for p in skills.rglob("SKILL.md"))
        categories = frozenset(p.name.lower() for p in skills.iterdir() if p.is_dir())
        _NAMES_CACHE[key] = (frozenset(names), categories)
        return _NAMES_CACHE[key]
    return None


def item_of(path: Path, root: Path) -> Optional[Tuple[str, Path]]:
    """Return ``(catalog item name, content folder)`` for a path under ``root``.

    The first content folder below ``root`` decides, so a folder named
    ``skills`` above the install target, or an ``agents/`` folder inside a
    skill (Codex writes ``skills/<name>/agents/openai.yaml``), cannot mislead
    it. ``skills/<name>/...`` names a skill folder; ``commands/<name>.md``
    (and ``prompts``, ``workflows``, ``agents``) names a file directly inside
    the content folder. Any other shape returns None and is never removed.
    """
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return None
    for index in range(len(parts) - 1):
        folder = parts[index].lower()
        if folder not in CONTENT_DIRS:
            continue
        content = Path(root, *parts[: index + 1])
        if folder == "skills":
            return parts[index + 1].lower(), content
        if index + 1 != len(parts) - 1:
            return None
        name = parts[index + 1].lower()
        for suffix in _SUFFIXES:
            if name.endswith(suffix):
                return name[: -len(suffix)], content
        return None
    return None


def _candidates(
    previous: Iterable[dict], produced: Iterable[FileAction], root: Path, retired
) -> List[dict]:
    """Records this install did not produce, plus files inside a retired skill folder.

    A file under ``skills/<name>/`` can be regenerated by this very install
    while its folder is being retired: Codex writes ``agents/openai.yaml`` for
    every manual-only ``SKILL.md`` it finds in the destination, and the retired
    ``SKILL.md`` is still there when it runs. Such a file still counts when the
    folder's own ``SKILL.md`` is a Nexus-Hub record this install did not
    produce. A user's own skill folder has no such record, so its regenerated
    sidecar is never touched.
    """
    now = {_norm(fa.path) for fa in produced}
    written: Dict[str, dict] = {}
    for record in previous:
        path = record.get("path")
        if path and record.get("action") in _WRITTEN:
            written.setdefault(_norm(path), record)
    folders = set()
    for spelled, record in written.items():
        path = Path(str(record["path"]))
        if spelled in now or path.name.lower() != "skill.md":
            continue
        found = item_of(path, root)
        if found and found[1].name.lower() == "skills" and retired(found[0]):
            folders.add(_norm(path.parent) + os.sep)
    return [
        record
        for spelled, record in written.items()
        if spelled not in now or any(spelled.startswith(folder) for folder in folders)
    ]


def _remove_empty_parents(path: Path, content: Path, result: WriteResult) -> None:
    parent = path.parent
    stop = _norm(content)
    while _norm(parent) != stop and _norm(parent).startswith(stop + os.sep):
        if _linked(parent):
            return
        try:
            long_path(parent).rmdir()  # empty folders only; never rmtree
        except OSError:
            return
        result.add(str(parent), "removed")
        parent = parent.parent


def retire_removed_items(
    ctx, key: str, previous: List[dict], current: WriteResult
) -> WriteResult:
    """Remove ``key``'s recorded copies of items the catalog no longer ships."""
    result = WriteResult()
    if ctx.dry_run or getattr(ctx, "instruction_only", False):
        return result
    names = catalog_names(ctx.repo_root)
    if names is None:
        return result
    items, categories = names
    root = Path(ctx.target_root)
    gone: List[str] = []

    def retired(name: str) -> bool:
        return name not in items and name not in categories

    for record in _candidates(previous, current.files, root, retired):
        path = Path(str(record["path"]))
        if not _norm(path).startswith(_norm(root).rstrip(os.sep) + os.sep):
            # Report only copies of retired items; never remove outside the target.
            found = item_of(path, Path(path.anchor))
            if (
                found is not None
                and found[0] not in items
                and found[0] not in categories
                and os.path.lexists(long_path(path))
            ):
                result.files.append(
                    FileAction(
                        path=str(path),
                        action="kept",
                        reason="outside the install target",
                    )
                )
            continue
        found = item_of(path, root)
        if found is None:
            continue
        name, content = found
        if name in items or name in categories:
            continue
        if not os.path.lexists(long_path(path)):
            # Another platform sharing the folder already removed it.
            gone.append(str(path))
            continue
        if _linked(path) or _via_link(path, [root]) or not long_path(path).is_file():
            result.files.append(
                FileAction(
                    path=str(path), action="kept", reason="a link or not a regular file"
                )
            )
            continue
        expected = record.get("sha256")
        if not expected or _sha256(path) != expected:
            result.files.append(
                FileAction(
                    path=str(path),
                    action="kept",
                    reason=f"/{name} was removed from the catalog, but this copy changed since install",
                )
            )
            continue
        try:
            long_path(path).unlink()
        except OSError as exc:
            result.files.append(
                FileAction(
                    path=str(path),
                    action="kept",
                    reason=f"locked or unreadable ({exc.strerror or exc})",
                )
            )
            continue
        result.add(str(path), "removed")
        _remove_empty_parents(path, content, result)
    removed = [fa.path for fa in result.files if fa.action == "removed"]
    forget = {
        _norm(p) for p in removed + gone if not os.path.lexists(long_path(Path(p)))
    }
    for tracked in ctx.manifest.files_for(key):
        if _norm(tracked) in forget:
            ctx.manifest.untrack(key, tracked)
    # This run's record can list a file just removed (a regenerated sidecar);
    # keeping it would make doctor report the retired copy as missing.
    ctx.manifest.retain_actions(
        key, lambda record: _norm(str(record.get("path", ""))) not in forget
    )
    return result


__all__ = ["CONTENT_DIRS", "catalog_names", "item_of", "retire_removed_items"]
