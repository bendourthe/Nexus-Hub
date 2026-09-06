"""Command surface for the memory store.

Phase 3: append, get, count, repair, config.
Phase 4: read, record, merge, search, zoom, drop. Printed recovery
commands use a resolved self-named path when the Phase 1 helper is
importable, otherwise ``python -m nexus_memory``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .commands import cmd_drop, cmd_merge, cmd_read, cmd_record, cmd_search, cmd_zoom
from .config import StoreConfig, default_store_root, load_config, save_config
from .store import MemoryStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-memory",
        description="Persistent agent-memory store (stdlib only, zero outbound).",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Store root (default: NEXUS_MEMORY_ROOT or ~/.nexus-hub/memory).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append", help="Append one entry.")
    p_append.add_argument("text", help="Entry text (UTF-8).")

    p_get = sub.add_parser("get", help="Read one entry by index.")
    p_get.add_argument("index", type=int)

    sub.add_parser("count", help="Print the number of complete entries.")
    sub.add_parser("repair", help="Truncate an incomplete trailing record.")

    p_cfg = sub.add_parser("config", help="Show or set per-store tunables.")
    cfg_sub = p_cfg.add_subparsers(dest="cfg_cmd", required=True)
    cfg_sub.add_parser("show")
    p_set = cfg_sub.add_parser("set")
    p_set.add_argument(
        "key",
        choices=[
            "record_width",
            "max_entry_length",
            "read_budget",
            "page_max_bytes",
            "page_max_lines",
        ],
    )
    p_set.add_argument("value", type=int)

    p_read = sub.add_parser("read", help="Read the store within the line budget.")
    p_read.add_argument("--part", type=int, default=1)

    p_record = sub.add_parser("record", help="Append one lasting entry.")
    p_record.add_argument("--text", required=True)
    p_record.add_argument(
        "--source",
        default=None,
        help="Origin of the fact (conversation, file, decision). Required.",
    )
    p_record.add_argument(
        "--tier",
        default="working",
        choices=["session", "working", "durable"],
    )
    p_record.add_argument(
        "--derived-from",
        default="",
        help="Comma-separated lineage ids or indexes.",
    )
    p_record.add_argument("--supersedes", type=int, default=None)

    p_merge = sub.add_parser("merge", help="Return a summary for one due range.")
    p_merge.add_argument("--lo", type=int, required=True)
    p_merge.add_argument("--hi", type=int, required=True)
    p_merge.add_argument("--text", required=True)

    p_search = sub.add_parser("search", help="Search entries by regular expression.")
    p_search.add_argument("--pattern", required=True)

    p_zoom = sub.add_parser("zoom", help="Open a summarized range into its two halves.")
    p_zoom.add_argument("--lo", type=int, required=True)
    p_zoom.add_argument("--hi", type=int, required=True)

    p_drop = sub.add_parser("drop", help="Discard a bad summary so it can be rebuilt.")
    p_drop.add_argument("--lo", type=int, required=True)
    p_drop.add_argument("--hi", type=int, required=True)

    p_maint = sub.add_parser(
        "maintain",
        help="Preview or apply session-tier archival (never deletes entries).",
    )
    p_maint.add_argument(
        "--apply",
        action="store_true",
        help="Copy a backup and append changelog rows. Default is preview-only.",
    )

    args = parser.parse_args(argv)
    root = Path(args.root) if args.root else default_store_root()

    try:
        if args.cmd == "append":
            store = MemoryStore(root)
            index = store.append(args.text)
            print(index)
            return 0
        if args.cmd == "get":
            store = MemoryStore(root)
            print(store.get(args.index))
            return 0
        if args.cmd == "count":
            store = MemoryStore(root)
            print(store.count())
            return 0
        if args.cmd == "repair":
            store = MemoryStore(root)
            removed = store.repair()
            print(removed)
            return 0
        if args.cmd == "config":
            return _config_cmd(root, args)
        store = MemoryStore(root)
        if args.cmd == "read":
            print(cmd_read(store, part=args.part), end="")
            return 0
        if args.cmd == "record":
            derived = tuple(
                part.strip()
                for part in (args.derived_from or "").split(",")
                if part.strip()
            )
            print(
                cmd_record(
                    store,
                    args.text,
                    source=args.source,
                    tier=args.tier,
                    derived_from=derived,
                    supersedes=args.supersedes,
                ),
                end="",
            )
            return 0
        if args.cmd == "maintain":
            from .lifecycle import apply_maintain, preview_maintain

            out = (
                apply_maintain(store)
                if args.apply
                else preview_maintain(store)
            )
            print(out, end="")
            return 0
        if args.cmd == "merge":
            print(cmd_merge(store, args.lo, args.hi, args.text), end="")
            return 0
        if args.cmd == "search":
            print(cmd_search(store, args.pattern), end="")
            return 0
        if args.cmd == "zoom":
            print(cmd_zoom(store, args.lo, args.hi), end="")
            return 0
        if args.cmd == "drop":
            print(cmd_drop(store, args.lo, args.hi), end="")
            return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 1


def _config_cmd(root: Path, args: argparse.Namespace) -> int:
    if args.cfg_cmd == "show":
        cfg = load_config(root)
        print(json.dumps(asdict(cfg), indent=2, sort_keys=True))
        print(f"root: {root}")
        return 0
    current = load_config(root)
    updates = {args.key: args.value}
    new = StoreConfig(
        record_width=updates.get("record_width", current.record_width),
        max_entry_length=updates.get("max_entry_length", current.max_entry_length),
        read_budget=updates.get("read_budget", current.read_budget),
        page_max_bytes=updates.get("page_max_bytes", current.page_max_bytes),
        page_max_lines=updates.get("page_max_lines", current.page_max_lines),
    )
    log = root / "entries.log"
    if (
        args.key == "record_width"
        and log.is_file()
        and log.stat().st_size > 0
        and new.record_width != current.record_width
    ):
        print(
            "record_width cannot change on a non-empty store; existing "
            "records are never rewritten",
            file=sys.stderr,
        )
        return 1
    save_config(root, new)
    print(json.dumps(asdict(new), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
