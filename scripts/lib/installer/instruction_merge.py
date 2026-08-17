"""Marker-delimited section replacement for shared instruction files.

Background
----------
Nexus-Hub installs to shared, user-owned files like `CLAUDE.md`, `AGENTS.md`,
and `.cursor/rules/*.mdc`. Older installer code overwrote those files wholesale,
clobbering any user edits. CodeGraph's `targets/shared.ts` (functions
`replaceOrAppendMarkedSection` and `removeMarkedSection`) defines the canonical
algorithm:

  1. If the file does not exist, create it with the marker-wrapped block.
  2. If the file exists and contains both markers, replace the slice between
     them with the new body.
  3. If the file exists and contains a literal pre-marker section header
     (e.g., the v2.1 `## Nexus-Hub` heading), migrate it inline to the marker
     block.
  4. Otherwise, append the marker-wrapped block after a single trailing blank
     line.

Byte-identical re-runs return the `unchanged` action so the runner can short-
circuit per the new WriteResult vocabulary (see scripts/lib/integrations/result.py).

The module is stdlib-only on purpose: this helper runs under the same Python
3.10+ baseline as the rest of the registry runner.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from scripts.lib.integrations.result import Action, FileAction

DEFAULT_START_MARKER = "<!-- NEXUS_HUB_START -->"
DEFAULT_END_MARKER = "<!-- NEXUS_HUB_END -->"


def _file_action(file_path: Path, action: Action) -> FileAction:
    """Create a result without importing the integration registry at load time."""
    from scripts.lib.integrations.result import FileAction

    return FileAction(path=str(file_path), action=action)


def _build_block(body: str, start_marker: str, end_marker: str) -> str:
    """Return the marker-wrapped block exactly as it should appear on disk.

    Body is stripped of leading/trailing whitespace so the wrapping is
    canonical (one newline between marker and body on each side).
    """
    return f"{start_marker}\n{body.strip()}\n{end_marker}\n"


def _atomic_replace_bytes(file_path: Path, content: bytes) -> None:
    """Replace one existing file atomically with bytes staged beside it."""

    mode = file_path.stat().st_mode
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=file_path.parent, prefix=f".{file_path.name}.", delete=False
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.chmod(temporary, mode)
        os.replace(temporary, file_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def merge_marker_section(
    file_path: Path,
    body: str,
    start_marker: str = DEFAULT_START_MARKER,
    end_marker: str = DEFAULT_END_MARKER,
    legacy_header: Optional[str] = None,
    dry_run: bool = False,
) -> FileAction:
    """Merge `body` into `file_path` as a marker-delimited section.

    Parameters
    ----------
    file_path : Path
        Destination file. Created if missing.
    body : str
        The Markdown body to wrap between the markers. Leading/trailing
        whitespace is stripped.
    start_marker / end_marker : str
        HTML-comment markers used to bracket the Nexus-Hub-owned section.
        Defaults to `<!-- NEXUS_HUB_START -->` / `<!-- NEXUS_HUB_END -->`.
    legacy_header : str, optional
        If supplied, an existing literal header (e.g., `## Nexus-Hub`) without
        markers is migrated inline. Migration runs only when both markers are
        absent AND the header is present.
    dry_run : bool
        When True, no bytes are written; the returned FileAction still reflects
        the action that would happen.

    Returns
    -------
    FileAction
        action="created"   - file did not exist
        action="updated"   - file existed; the marker block was rewritten or
                              the legacy header was migrated, OR the block was
                              appended
        action="unchanged" - the resulting bytes match the existing bytes
    """
    new_block = _build_block(body, start_marker, end_marker)

    if not file_path.exists():
        new_bytes = new_block.encode("utf-8")
        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(new_bytes)
        return _file_action(file_path, "created")

    existing = file_path.read_text(encoding="utf-8")

    if start_marker in existing and end_marker in existing:
        new_text = _replace_between_markers(
            existing, new_block, start_marker, end_marker
        )
    elif legacy_header and legacy_header in existing:
        new_text = _migrate_legacy_header(existing, legacy_header, new_block)
    else:
        new_text = _append_block(existing, new_block)

    new_bytes = new_text.encode("utf-8")
    existing_bytes = existing.encode("utf-8")
    if existing_bytes == new_bytes:
        return _file_action(file_path, "unchanged")
    if not dry_run:
        file_path.write_bytes(new_bytes)
    return _file_action(file_path, "updated")


def remove_marker_section(
    file_path: Path,
    start_marker: str = DEFAULT_START_MARKER,
    end_marker: str = DEFAULT_END_MARKER,
    dry_run: bool = False,
) -> FileAction:
    """Strip the marker-delimited section out of `file_path`.

    Returns:
        action="not-found" - file does not exist
        action="kept"      - file exists but contains no marker pair
        action="removed"   - the marker block was removed; file rewritten
                              without it. If the file becomes empty (only the
                              block was present), the file itself is deleted.
        action="unchanged" - file exists, markers present, but resulting bytes
                              match the existing bytes (edge case where the
                              block was already a no-op).
    """
    if not file_path.exists():
        return _file_action(file_path, "not-found")
    existing = file_path.read_text(encoding="utf-8")
    if start_marker not in existing or end_marker not in existing:
        return _file_action(file_path, "kept")
    new_text = _strip_between_markers(existing, start_marker, end_marker)
    new_bytes = new_text.encode("utf-8")
    if existing.encode("utf-8") == new_bytes:
        return _file_action(file_path, "unchanged")
    if not new_text.strip():
        if not dry_run:
            file_path.unlink(missing_ok=True)
        return _file_action(file_path, "removed")
    if not dry_run:
        _atomic_replace_bytes(file_path, new_bytes)
    return _file_action(file_path, "removed")


def _replace_between_markers(
    text: str, new_block: str, start_marker: str, end_marker: str
) -> str:
    # Use rindex so the marker block can quote itself in body text without
    # accidentally truncating at the first nested mention. (A shared instruction
    # template may literally reference both markers when explaining the merge
    # mechanism to the user, e.g. an inline "between <!-- NEXUS:BEGIN --> and
    # <!-- NEXUS:END -->" note in the body.)
    start = text.index(start_marker)
    end = text.rindex(end_marker, start) + len(end_marker)
    # Preserve the trailing newline after the end marker if it existed; otherwise
    # add one so the new block is line-terminated.
    trailing = ""
    rest = text[end:]
    if rest.startswith("\r\n"):
        trailing = "\r\n"
    elif rest.startswith("\n"):
        trailing = "\n"
    head = text[:start]
    tail = text[end + len(trailing) :]
    # `new_block` already ends with \n; preserve the trailing newline that was
    # there before so the file does not grow / shrink an extra blank line.
    block = new_block if new_block.endswith("\n") else new_block + "\n"
    return f"{head}{block.rstrip()}{trailing}{tail}"


def _migrate_legacy_header(text: str, legacy_header: str, new_block: str) -> str:
    """Replace the legacy header section with the marker block.

    The legacy section runs from `legacy_header` to either the next top-level
    heading at the same depth or end of file. We detect depth by counting
    leading `#` characters on the header line.
    """
    idx = text.index(legacy_header)
    header_line_end = text.index("\n", idx) if "\n" in text[idx:] else len(text)
    # Determine heading depth (number of leading `#`).
    raw_header = text[idx:header_line_end].lstrip()
    depth = 0
    for ch in raw_header:
        if ch == "#":
            depth += 1
        else:
            break
    # Find next heading at the same depth or shallower.
    cursor = header_line_end + 1
    next_idx = len(text)
    while cursor < len(text):
        line_end = text.index("\n", cursor) if "\n" in text[cursor:] else len(text)
        line = text[cursor:line_end].lstrip()
        if line.startswith("#"):
            other_depth = 0
            for ch in line:
                if ch == "#":
                    other_depth += 1
                else:
                    break
            if other_depth <= depth:
                next_idx = cursor
                break
        cursor = line_end + 1
    head = text[:idx].rstrip()
    tail = text[next_idx:].lstrip("\n")
    block = new_block.rstrip("\n")
    if head:
        return f"{head}\n\n{block}\n" + (f"\n{tail}" if tail else "")
    return f"{block}\n" + (f"\n{tail}" if tail else "")


def _strip_between_markers(text: str, start_marker: str, end_marker: str) -> str:
    # Mirror the rindex semantics from _replace_between_markers so the
    # uninstall path agrees with the install path on where the block ends.
    start = text.index(start_marker)
    end = text.rindex(end_marker, start) + len(end_marker)
    # Eat one trailing newline that bracketed the block.
    if end < len(text) and text[end] == "\n":
        end += 1
    head = text[:start].rstrip("\n")
    tail = text[end:].lstrip("\n")
    if head and tail:
        return f"{head}\n\n{tail}"
    if head:
        return f"{head}\n"
    if tail:
        return tail
    return ""


def _append_block(existing: str, new_block: str) -> str:
    trimmed = existing.rstrip()
    block = new_block.rstrip("\n")
    if not trimmed:
        return f"{block}\n"
    return f"{trimmed}\n\n{block}\n"
