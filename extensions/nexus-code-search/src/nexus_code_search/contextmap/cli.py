"""One-shot CLI for the context-map generator (`nexus-hub map`).

The top-level ``nexus-hub`` launcher forwards ``map`` here (see
``scripts/nexus_hub_cli.py``), so all of the logic lives in the extension
package and needs no installer change. It can also be run directly:

    python -m nexus_code_search.contextmap.cli [root] [--force] [--json]

Exit codes:
    0 -> generated (or a content-hash no-op skip)
    1 -> bad arguments / missing root
    2 -> no graph index found at <root>/.nexus/code-index/codegraph.db
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nexus_code_search.config import index_dir_for, resolve_config
from nexus_code_search.contextmap.generator import generate_context_map
from nexus_code_search.db.schema import DB_FILENAME


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-hub map",
        description=(
            "Compile a committed .nexus/CONTEXT-MAP.md from the local code "
            "graph. Run the index_graph tool first to build the graph."
        ),
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root (default: current working directory).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even when the graph is unchanged.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON instead of a human summary.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: root {root} does not exist", file=sys.stderr)
        return 1

    config = resolve_config()
    index_dir = index_dir_for(root, config)
    db_path = index_dir / DB_FILENAME
    if not db_path.exists():
        print(
            f"error: no graph index found at {db_path}. "
            "Run the `index_graph` tool for this repository first.",
            file=sys.stderr,
        )
        return 2

    result = generate_context_map(root, index_dir, force=args.force)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    action = "unchanged (no-op)" if result.skipped else "generated"
    print(f"Context map {action}: {result.map_path}")
    print(
        f"  files: {result.files_indexed} | symbols: {result.symbols} | "
        f"modules: {result.modules}"
    )
    print(
        f"  map tokens: {result.map_tokens} | total tokens "
        f"(map + articles): {result.total_tokens}"
    )
    print(f"  articles: {len(result.article_paths)} under {result.context_dir}")
    if result.files_indexed == 0:
        print(
            "  note: the graph is empty; run the `index_graph` tool first "
            "for a useful map.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
