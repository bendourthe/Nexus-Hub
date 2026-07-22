"""Git-scoped change map.

Given the files changed since a git ref, emit a change-scoped view: the affected
routes, models, and symbols (those declared in the changed files) plus the
transitively affected test files (via the existing reverse-import BFS). This is
an ephemeral query, not a committed artifact - the CLI prints it and writes
nothing under `.nexus/`.

Conservative by design, matching `affected_tests`: it favors listing something
as affected over missing it.
"""

from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from nexus_code_search.contextmap.model import SIGNIFICANT_KINDS
from nexus_code_search.contextmap.routes import extract_routes
from nexus_code_search.contextmap.schema import extract_schema
from nexus_code_search.graph.affected import affected_tests


@dataclass(frozen=True)
class ChangeMap:
    """A change-scoped view of the codebase since a git ref."""

    ref: str
    changed_files: list[str] = field(default_factory=list)
    affected_routes: list[str] = field(default_factory=list)
    affected_models: list[str] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ref": self.ref,
            "changed_files": self.changed_files,
            "affected_routes": self.affected_routes,
            "affected_models": self.affected_models,
            "affected_symbols": self.affected_symbols,
            "affected_tests": self.affected_tests,
        }


def git_changed_files(root: Path, ref: str) -> list[str] | None:
    """Return repo-relative POSIX paths changed between ``ref`` and the working
    tree, or None when git is unavailable / the ref is invalid / not a repo."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", ref, "--"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, ValueError):
        return None
    if proc.returncode != 0:
        return None
    return sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()})


def compute_change_map(
    conn: sqlite3.Connection, root: Path, ref: str, depth: int = 5
) -> ChangeMap | None:
    """Build a :class:`ChangeMap` for what changed since ``ref``.

    Returns None when the git diff cannot be computed (bad ref / not a repo).
    """
    changed = git_changed_files(root, ref)
    if changed is None:
        return None
    changed_set = set(changed)

    affected_routes = sorted(
        {
            f"{r.method} {r.path}"
            for r in extract_routes(conn, root)
            if r.source_file in changed_set or r.handler_file in changed_set
        }
    )
    affected_models = sorted(
        {m.name for m in extract_schema(conn, root) if m.source_file in changed_set}
    )
    affected_symbols = _symbols_in(conn, changed_set)
    affected = affected_tests(conn, root, list(changed), depth=depth)

    return ChangeMap(
        ref=ref,
        changed_files=changed,
        affected_routes=affected_routes,
        affected_models=affected_models,
        affected_symbols=affected_symbols,
        affected_tests=affected,
    )


def _symbols_in(conn: sqlite3.Connection, changed_set: set[str]) -> list[str]:
    """Significant symbols declared in the changed files."""
    rows = conn.execute(
        "SELECT n.name, n.kind, f.path FROM nodes n JOIN files f ON n.file_id = f.id"
    ).fetchall()
    found = {
        f"{name} ({kind})"
        for name, kind, path in rows
        if kind in SIGNIFICANT_KINDS and path in changed_set
    }
    return sorted(found)
