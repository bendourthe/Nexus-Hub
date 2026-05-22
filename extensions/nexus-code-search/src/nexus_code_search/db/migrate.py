"""Migration helpers between nexus-code-search index schema versions.

v1 -> v2 is intentionally not an in-place data migration: the v1 JSON chunk
index and the v2 SQLite AST graph are semantically different surfaces (chunks
are character-window blobs, nodes are AST symbols). The v1 -> v2 path simply
renames the v1 artifact directory aside and surfaces a clear "please re-index"
message to the caller.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("nexus-code-search")

V1_ARTIFACTS = ("chunks.json", "manifest.json", "chunks.pickle")


@dataclass(frozen=True)
class MigrationResult:
    """Outcome of a v1 -> v2 migration attempt."""

    migrated: bool
    backup_dir: Path | None
    message: str


def detect_v1_index(index_dir: Path) -> bool:
    """Return True if `index_dir` contains a v1 chunk index."""
    if not index_dir.exists():
        return False
    return any((index_dir / name).exists() for name in V1_ARTIFACTS)


def migrate_v1_to_v2(index_dir: Path) -> MigrationResult:
    """Detect a v1 index and rename it aside.

    Behavior:
      - If `index_dir` does not exist OR no v1 artifacts are present: return
        `MigrationResult(migrated=False, backup_dir=None, message=...)`.
      - If a v1 index is present: rename the directory to
        `<dir>.v1-backup` (auto-suffixed with a counter if needed) and return
        `MigrationResult(migrated=True, backup_dir=<new path>, message=...)`.

    The caller is expected to re-run `index_codebase` after this to rebuild
    against the v2 schema. No data is destroyed.
    """
    if not detect_v1_index(index_dir):
        return MigrationResult(
            migrated=False,
            backup_dir=None,
            message=f"No v1 index detected at {index_dir}",
        )

    backup_dir = _resolve_backup_path(index_dir)
    index_dir.rename(backup_dir)
    msg = (
        f"v1 index moved to {backup_dir}. The v2 schema requires a fresh "
        f"index; run `nexus-code-search index <repo>` to rebuild."
    )
    logger.warning(msg)
    return MigrationResult(migrated=True, backup_dir=backup_dir, message=msg)


def _resolve_backup_path(index_dir: Path) -> Path:
    base = index_dir.parent / f"{index_dir.name}.v1-backup"
    candidate = base
    counter = 1
    while candidate.exists():
        candidate = base.with_name(f"{base.name}.{counter}")
        counter += 1
    return candidate
