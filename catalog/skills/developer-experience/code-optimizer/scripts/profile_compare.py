#!/usr/bin/env python3
"""
profile_compare.py - Diff two JSON profiles produced by profile_run.py, for the
code-optimizer skill's bundled profiling harness.

Tier-3 bundled resource. Reports which functions grew or shrank between a BEFORE
and an AFTER profile (by cumulative time), and which functions are new to or gone
from the after profile, sorted by the magnitude of the cumulative-time delta. It
is an informational report (always exits 0) - the pass/fail gate is the separate
performance-regression-gate skill.

STDLIB-ONLY and ZERO-NETWORK: argparse, json, sys.

Usage:
    python profile_compare.py before.json after.json --top 20
"""

from __future__ import annotations

import argparse
import json
import sys


def _load(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {fn["name"]: fn for fn in data.get("functions", [])}


def compare(before: dict[str, dict], after: dict[str, dict], top: int) -> list[dict]:
    rows = []
    for name in set(before) | set(after):
        b = before.get(name)
        a = after.get(name)
        b_ct = float(b["cumtime"]) if b else 0.0
        a_ct = float(a["cumtime"]) if a else 0.0
        delta = a_ct - b_ct
        if b is None:
            status = "NEW"
        elif a is None:
            status = "GONE"
        elif delta < 0:
            status = "faster"
        elif delta > 0:
            status = "slower"
        else:
            status = "same"
        rows.append(
            {
                "name": name,
                "before": b_ct,
                "after": a_ct,
                "delta": delta,
                "status": status,
            }
        )
    rows.sort(key=lambda r: abs(r["delta"]), reverse=True)
    return rows[:top]


def _print_table(rows: list[dict]) -> None:
    headers = ("status", "delta-cumtime", "before", "after", "function")
    cells = [
        (
            r["status"],
            f"{r['delta']:+.6f}",
            f"{r['before']:.6f}",
            f"{r['after']:.6f}",
            r["name"],
        )
        for r in rows
    ]
    widths = [len(h) for h in headers]
    for row in cells:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(row: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(fmt(headers))
    print("  ".join("-" * w for w in widths))
    for row in cells:
        print(fmt(row))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare two profile_run.py JSON profiles."
    )
    parser.add_argument("before", help="baseline profile JSON")
    parser.add_argument("after", help="current profile JSON")
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="show the top-N functions by absolute cumtime delta (default 20)",
    )
    args = parser.parse_args(argv)

    try:
        before = _load(args.before)
        after = _load(args.after)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error reading profile: {exc}", file=sys.stderr)
        return 2

    _print_table(compare(before, after, args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
