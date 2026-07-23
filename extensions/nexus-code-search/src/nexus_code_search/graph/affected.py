"""Test-impact analysis: which test files might be affected by source changes.

Given a list of files changed in a commit / branch, walk the AST graph in
reverse-import direction until we reach files whose path matches the test
glob. Returns the set of test files that transitively depend on any changed
file.

The algorithm is intentionally conservative: it errs on the side of marking
a test as affected. False positives waste a few CPU seconds in CI; false
negatives let a regression slip through.

Resolution rules for "X imports changed-file":
  1. For each changed file F, collect candidate module names:
     - file stem (`utils.py` -> `utils`)
     - dotted path (`pkg/sub/utils.py` -> `pkg.sub.utils`, `sub.utils`)
  2. Find every `import` node in the graph whose name contains a candidate
     (suffix match on dotted name).
  3. The owning file of that import node is "affected" - it depends on F.
  4. Recurse up to `depth` hops by treating affected files as new "changed"
     files and re-running rules 1-3.
"""

from __future__ import annotations

import sqlite3
from collections import deque
from pathlib import Path, PurePosixPath

from nexus_code_search.types import EdgeKind, NodeKind

# Default test-path heuristic: paths matching any of these substrings (in
# POSIX form) are considered tests. Matches both `tests/` directories and
# `*_test.py` / `test_*.py` filenames common in pytest and Go ecosystems.
DEFAULT_TEST_PATTERNS: tuple[str, ...] = (
    "/tests/",
    "/test/",
    "test_",
    "_test.",
    ".test.",
)


def _module_candidates(rel_path: str) -> set[str]:
    """Return every plausible Python/JS module name a file might be imported as.

    For `src/pkg/utils.py`:
      - `utils`        (file stem - most common in `from x import y`)
      - `pkg.utils`    (parent.stem - dotted import)
      - `src.pkg.utils`(full dotted path - sometimes used)
      - `pkg/utils`    (relative path - JS-style)
    """
    p = PurePosixPath(rel_path)
    stem = p.stem
    parts = list(p.parent.parts)
    candidates = {stem}
    # Build progressively-longer dotted prefixes.
    for i in range(len(parts)):
        suffix_parts = parts[i:] + [stem]
        candidates.add(".".join(suffix_parts))
        candidates.add("/".join(suffix_parts))
    # JS-style: include extension-stripped relative path.
    candidates.add(p.with_suffix("").as_posix())
    candidates.discard("")
    return candidates


def _matches_test(path: str, custom_glob: str | None) -> bool:
    """Decide whether `path` is a test file."""
    if custom_glob:
        # Glob match (POSIX-style); fall back to substring if the glob raises.
        try:
            return PurePosixPath(path).match(custom_glob)
        except Exception:  # noqa: BLE001
            return custom_glob in path
    posix = path.replace("\\", "/")
    name = posix.rsplit("/", 1)[-1]
    if (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.ts")
    ):
        return True
    return any(p in posix for p in DEFAULT_TEST_PATTERNS)


def _files_importing(
    conn: sqlite3.Connection,
    candidates: set[str],
) -> set[str]:
    """Return repo-relative paths of every file with an `import` node whose
    name (or dotted suffix) matches any candidate."""
    if not candidates:
        return set()
    # Pull every import node + its file path; do the suffix-match in Python
    # rather than 100 OR-clauses in SQL.
    rows = conn.execute(
        "SELECT n.name, f.path "
        "FROM nodes n JOIN files f ON n.file_id = f.id "
        "WHERE n.kind = ?",
        (NodeKind.IMPORT.value,),
    ).fetchall()
    affected: set[str] = set()
    for import_name, owning_path in rows:
        if not import_name:
            continue
        if import_name in candidates:
            affected.add(owning_path)
            continue
        # Suffix match: `pkg.utils` candidate should match an import named
        # `from myproject.pkg.utils import foo` -> import_name='myproject.pkg.utils.foo'
        # so try matching the trailing dotted segments.
        for cand in candidates:
            if not cand:
                continue
            if import_name.endswith("." + cand) or import_name.endswith("/" + cand):
                affected.add(owning_path)
                break
    return affected


def most_imported_files(
    conn: sqlite3.Connection, limit: int | None = None
) -> list[tuple[str, int]]:
    """Rank files by how many OTHER files import them (inbound import count).

    This is a FILE-level view: "which files break the most on change", distinct
    from the symbol-level `code_impact` blast radius. It inverts the same
    import-resolution rules `affected_tests` uses, so the two stay consistent.
    Import nodes are loaded once; matching is done in Python. Returns
    `(rel_path, importer_count)` sorted by count descending, then path.
    """
    import_rows = conn.execute(
        "SELECT n.name, f.path "
        "FROM nodes n JOIN files f ON n.file_id = f.id "
        "WHERE n.kind = ?",
        (NodeKind.IMPORT.value,),
    ).fetchall()
    file_paths = [row[0] for row in conn.execute("SELECT path FROM files")]

    counts: list[tuple[str, int]] = []
    for path in file_paths:
        candidates = _module_candidates(path)
        importers: set[str] = set()
        for import_name, owning_path in import_rows:
            if not import_name or owning_path == path:
                continue
            if import_name in candidates or any(
                import_name.endswith("." + cand) or import_name.endswith("/" + cand)
                for cand in candidates
                if cand
            ):
                importers.add(owning_path)
        if importers:
            counts.append((path, len(importers)))

    counts.sort(key=lambda item: (-item[1], item[0]))
    return counts[:limit] if limit is not None else counts


def affected_tests(
    conn: sqlite3.Connection,
    repo_root: Path,
    changed_files: list[Path | str],
    depth: int = 5,
    test_glob: str | None = None,
) -> list[str]:
    """Return every test file affected by changes to `changed_files`.

    `changed_files` may be `Path` objects (resolved against `repo_root`) or
    pre-relativized POSIX strings. The return value is sorted list of POSIX
    relative paths.
    """
    if depth < 1:
        depth = 1

    repo_root = repo_root.resolve()
    seed: set[str] = set()
    for cf in changed_files:
        if isinstance(cf, Path):
            try:
                rel = cf.resolve().relative_to(repo_root).as_posix()
            except ValueError:
                rel = cf.as_posix()
        else:
            rel = cf.replace("\\", "/")
        seed.add(rel)

    # BFS over the reverse-import relation.
    visited: set[str] = set(seed)
    frontier: set[str] = set(seed)
    affected: set[str] = set()
    queue: deque[tuple[str, int]] = deque((p, 0) for p in seed)

    while queue:
        cur_path, cur_depth = queue.popleft()
        if cur_depth >= depth:
            continue
        candidates = _module_candidates(cur_path)
        for owning_path in _files_importing(conn, candidates):
            if owning_path in visited:
                continue
            visited.add(owning_path)
            affected.add(owning_path)
            queue.append((owning_path, cur_depth + 1))

    # Filter to test files.
    result = sorted({p for p in affected if _matches_test(p, test_glob)})
    return result
