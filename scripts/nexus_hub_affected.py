"""CLI dispatcher: `nexus-hub affected <files>` test-impact analysis.

Wraps the `nexus-code-search` `code_affected_tests` graph query so users can
run impact analysis from a shell without booting the MCP server. Reads paths
from positional args or stdin (one path per line, useful with `git diff
--name-only | nexus-hub affected -`).

Usage:
    nexus-hub affected src/foo.py src/bar.py
    git diff --name-only HEAD~1 | nexus-hub affected --root . -
    nexus-hub affected --root /repo --depth 3 --test-glob 'tests/**/*.py' src/foo.py

Exit codes:
    0 -> ran successfully (may return zero affected files)
    1 -> bad arguments
    2 -> no index found at <root>/.nexus/code-index/codegraph.db; run
         index_graph via the MCP server first
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def _find_db(root: Path) -> Path | None:
    candidate = root / ".nexus" / "code-index" / "codegraph.db"
    return candidate if candidate.exists() else None


def _read_paths_from_stdin() -> list[str]:
    return [line.strip() for line in sys.stdin if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-hub affected",
        description="Return test files transitively affected by the given source changes.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Changed files (paths). Use '-' to read paths from stdin.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root (default: current working directory).",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Maximum reverse-import hops to walk (default: 5).",
    )
    parser.add_argument(
        "--test-glob",
        default=None,
        help="POSIX glob to filter test files (e.g. 'tests/**/*.py').",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of newline-separated paths.",
    )

    args = parser.parse_args(argv)

    # Resolve repo root.
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: --root {root} does not exist", file=sys.stderr)
        return 1

    # Resolve input paths.
    files = list(args.files)
    if "-" in files:
        files.remove("-")
        files.extend(_read_paths_from_stdin())
    if not files:
        print("error: no input files given (use positional args or stdin '-')", file=sys.stderr)
        return 1

    db_path = _find_db(root)
    if db_path is None:
        print(
            f"error: no graph index found at {root}/.nexus/code-index/codegraph.db. "
            "Run the MCP `index_graph` tool first.",
            file=sys.stderr,
        )
        return 2

    # Late import so the script remains usable when the wheel is installed
    # but not yet imported.
    try:
        from nexus_code_search.graph.affected import affected_tests
    except ImportError as exc:  # noqa: BLE001
        print(
            f"error: nexus-code-search package not installed ({exc}). "
            "Install with `pip install nexus-code-search`.",
            file=sys.stderr,
        )
        return 1

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        results = affected_tests(
            conn,
            repo_root=root,
            changed_files=files,
            depth=args.depth,
            test_glob=args.test_glob,
        )
    finally:
        conn.close()

    if args.json:
        payload = {
            "root": str(root),
            "changed_files": files,
            "depth": args.depth,
            "test_glob": args.test_glob,
            "affected_tests": results,
        }
        print(json.dumps(payload, indent=2))
    else:
        for path in results:
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
