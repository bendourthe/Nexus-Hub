"""One-shot CLI for the context-map generator (`nexus-hub map`).

The top-level ``nexus-hub`` launcher forwards ``map`` here (see
``scripts/nexus_hub_cli.py``), so all of the logic lives in the extension
package and needs no installer change. It can also be run directly:

    python -m nexus_code_search.contextmap.cli [root] [--force] [--json]
    python -m nexus_code_search.contextmap.cli [root] --since <git-ref> [--json]

Exit codes:
    0 -> generated (or a content-hash no-op skip / change map printed)
    1 -> bad arguments / missing root / git diff failed
    2 -> no graph index found at <root>/.nexus/code-index/codegraph.db
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nexus_code_search.config import index_dir_for, resolve_config
from nexus_code_search.contextmap.changemap import compute_change_map
from nexus_code_search.contextmap.generator import generate_context_map
from nexus_code_search.contextmap.knowledge import generate_knowledge_map
from nexus_code_search.contextmap.maphealth import lint_context_map
from nexus_code_search.db.schema import DB_FILENAME, open_database


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
    parser.add_argument(
        "--since",
        metavar="GIT_REF",
        default=None,
        help=(
            "Print a change-scoped view (affected routes / models / symbols / "
            "tests) for what changed since GIT_REF, instead of the full map."
        ),
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help=(
            "Lint the existing compiled map (orphan articles, missing backlinks, "
            "staleness) instead of generating. Exit 1 if unhealthy."
        ),
    )
    parser.add_argument(
        "--knowledge",
        nargs="?",
        const="",
        default=None,
        metavar="NOTES_PATH",
        help=(
            "Compile .nexus/KNOWLEDGE.md from the Markdown notes under NOTES_PATH "
            "(default: root). Graph-independent; classifies decisions / meetings / "
            "retros / specs / research and extracts decisions + open questions."
        ),
    )
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: root {root} does not exist", file=sys.stderr)
        return 1

    # Knowledge extraction reads Markdown, not the code graph, so it runs before
    # the graph-index check below.
    if args.knowledge is not None:
        return _run_knowledge(root, args.knowledge or None, as_json=args.json)

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

    if args.since is not None:
        return _run_change_map(root, index_dir, args.since, as_json=args.json)

    if args.lint:
        return _run_lint(root, index_dir, as_json=args.json)

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


def _run_change_map(root: Path, index_dir: Path, ref: str, *, as_json: bool) -> int:
    conn = open_database(index_dir)
    try:
        change = compute_change_map(conn, root, ref)
    finally:
        conn.close()

    if change is None:
        print(
            f"error: could not compute a git diff for '{ref}' (not a git "
            "repository, or an invalid ref).",
            file=sys.stderr,
        )
        return 1

    if as_json:
        print(json.dumps(change.to_dict(), indent=2))
        return 0

    print(f"Change map since {ref}:")
    print(f"  changed files: {len(change.changed_files)}")
    _print_list("affected routes", change.affected_routes)
    _print_list("affected models", change.affected_models)
    _print_list("affected symbols", change.affected_symbols)
    _print_list("affected tests", change.affected_tests)
    return 0


def _run_knowledge(root: Path, notes_path: str | None, *, as_json: bool) -> int:
    resolved = Path(notes_path).expanduser().resolve() if notes_path else None
    if resolved is not None and not resolved.exists():
        print(f"error: notes path {resolved} does not exist", file=sys.stderr)
        return 1
    result = generate_knowledge_map(root, resolved)
    if as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    action = "unchanged (no-op)" if result.skipped else "generated"
    print(f"Knowledge map {action}: {result.knowledge_path}")
    print(
        f"  notes: {result.note_count} | decisions: {result.decision_count} | "
        f"open questions: {result.open_question_count}"
    )
    if result.categories:
        summary = ", ".join(f"{k}: {v}" for k, v in result.categories.items())
        print(f"  by category: {summary}")
    return 0


def _run_lint(root: Path, index_dir: Path, *, as_json: bool) -> int:
    report = lint_context_map(root, index_dir)
    if as_json:
        print(json.dumps(report.to_dict(), indent=2))
    elif not report.map_present:
        print("no context map found; run `nexus-hub map` first.", file=sys.stderr)
    elif report.healthy:
        print("Context map is healthy (no orphans, backlinks OK, not stale).")
    else:
        print("Context map health issues:")
        if report.orphans:
            print(f"  orphan articles: {', '.join(report.orphans)}")
        if report.missing_backlinks:
            print(f"  missing backlinks: {', '.join(report.missing_backlinks)}")
        if report.stale:
            print("  stale: source files changed since the map was generated")
    return 0 if (report.map_present and report.healthy) else 1


def _print_list(label: str, items: list[str], cap: int = 25) -> None:
    print(f"  {label}: {len(items)}")
    for item in items[:cap]:
        print(f"    - {item}")
    if len(items) > cap:
        print(f"    ... {len(items) - cap} more")


if __name__ == "__main__":
    sys.exit(main())
