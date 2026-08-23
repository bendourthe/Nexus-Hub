"""Command surface for the memory store (Phase 3: append/get/repair/config).

Phase 4 adds read, merge, search, zoom, and forget. Printed recovery
commands use a resolved self-named path when the Phase 1 helper is
importable, otherwise ``python -m nexus_memory``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

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
