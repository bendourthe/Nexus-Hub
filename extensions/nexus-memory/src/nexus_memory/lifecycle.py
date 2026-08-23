"""Preview-first maintenance over session-tier entries.

Archival never deletes a log row. `--apply` copies the store aside, then
appends changelog `archived` events. The original entries stay readable.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .changelog import append_event
from .record import parse_record
from .store import MemoryStore

BACKUP_DIR = "backups"


def session_indices(store: MemoryStore) -> list[int]:
    """Return indexes whose envelope tier is `session`."""
    found: list[int] = []
    for index in range(store.count()):
        parsed = parse_record(store.get(index), strict=False)
        if parsed.tier == "session" and not parsed.legacy:
            found.append(index)
    return found


def preview_maintain(store: MemoryStore) -> str:
    """Describe what `--apply` would archive. Makes no writes."""
    indexes = session_indices(store)
    if not indexes:
        return "maintain preview: no session-tier entries to archive\n"
    lines = [
        (
            "maintain preview: would archive the following session-tier "
            f"entries ({len(indexes)}); nothing has been written:"
        ),
    ]
    for index in indexes:
        parsed = parse_record(store.get(index), strict=False)
        summary = parsed.body.replace("\n", " ")[:80]
        lines.append(f"  {index}\tsource={parsed.source}\t{summary}")
    lines.append("re-run with --apply to copy a backup and append changelog rows")
    return "\n".join(lines) + "\n"


def apply_maintain(store: MemoryStore) -> str:
    """Copy the store aside, then record archival in the changelog."""
    indexes = session_indices(store)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path(store.root) / BACKUP_DIR / stamp
    dest.mkdir(parents=True, exist_ok=True)
    root = Path(store.root)
    for item in root.iterdir():
        if item.name == BACKUP_DIR:
            continue
        target = dest / item.name
        if item.is_file():
            shutil.copy2(item, target)
        elif item.is_dir():
            shutil.copytree(item, target)
    for index in indexes:
        parsed = parse_record(store.get(index), strict=False)
        append_event(
            store.root,
            "archived",
            index,
            parsed.source,
            reason="session-tier maintain",
        )
    return (
        f"maintain apply: backup at {dest}; "
        f"archived {len(indexes)} session-tier entries in changelog "
        "(entries were not deleted)\n"
    )
