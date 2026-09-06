"""Append-only mutation ledger next to the entry log.

The entry log is already append-only. This file records *why* an index was
added, superseded, or archived, so an agent can answer "why did I recall X?"
without rewriting any entry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

CHANGELOG_NAME = "changelog.log"


def append_event(
    root: Path,
    action: str,
    index: int,
    source: str,
    reason: str = "",
) -> None:
    """Append one tab-separated changelog row. Never rewrites prior rows."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp}\t{action}\t{index}\tsource={source}"
    if reason:
        line += f"\treason={reason}"
    path = Path(root) / CHANGELOG_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def read_events(root: Path) -> list[str]:
    """Return changelog rows, or an empty list when the file is absent."""
    path = Path(root) / CHANGELOG_NAME
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()
