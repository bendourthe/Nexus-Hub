#!/usr/bin/env python3
"""
profile_run.py - Run a Python target under cProfile and emit a structured JSON
profile, for the code-optimizer skill's bundled profiling harness.

Tier-3 bundled resource: invoked via the shell; the source is never read into the
context window. It runs the target script under cProfile and writes a JSON
profile of the top-N functions by cumulative time (name, ncalls, tottime,
cumtime), so a before/after pair can be diffed with profile_compare.py.

STDLIB-ONLY and ZERO-NETWORK: argparse, cProfile, json, pstats, runpy, sys.

Usage:
    python profile_run.py target.py --out before.json --top 30
    python profile_run.py target.py --out after.json -- arg1 arg2   # args after -- go to the target
"""

from __future__ import annotations

import argparse
import cProfile
import json
import pstats
import runpy
import sys


def run_profile(target: str, target_args: list[str], top: int) -> dict:
    """Run `target` under cProfile and return the top-N functions by cumulative time."""
    argv_backup = sys.argv[:]
    sys.argv = [target, *target_args]
    profiler = cProfile.Profile()
    try:
        profiler.enable()
        try:
            runpy.run_path(target, run_name="__main__")
        except SystemExit:
            pass  # the target called sys.exit(); the profile is still captured
        finally:
            profiler.disable()
    finally:
        sys.argv = argv_backup

    stats = pstats.Stats(profiler)
    functions = []
    for (filename, lineno, func_name), (
        _cc,
        nc,
        tt,
        ct,
        _callers,
    ) in stats.stats.items():
        functions.append(
            {
                "name": f"{filename}:{lineno}({func_name})",
                "ncalls": nc,
                "tottime": round(tt, 6),
                "cumtime": round(ct, 6),
            }
        )
    functions.sort(key=lambda fn: fn["cumtime"], reverse=True)
    return {"target": target, "functions": functions[:top]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Profile a Python target under cProfile."
    )
    parser.add_argument("target", help="Python script to run under the profiler")
    parser.add_argument(
        "--out", required=True, metavar="JSON", help="output profile JSON path"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="keep the top-N functions by cumulative time (default 30)",
    )
    parser.add_argument(
        "target_args",
        nargs="*",
        help="args passed to the target (place them after --)",
    )
    args = parser.parse_args(argv)

    target_args = args.target_args
    if target_args and target_args[0] == "--":
        target_args = target_args[1:]

    try:
        profile = run_profile(args.target, target_args, args.top)
    except FileNotFoundError:
        print(f"error: target not found: {args.target}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - the arbitrary target may raise anything; report, do not crash the profiler
        print(f"error: target raised during profiling: {exc}", file=sys.stderr)
        return 2

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
        f.write("\n")
    print(f"wrote {len(profile['functions'])} function(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
