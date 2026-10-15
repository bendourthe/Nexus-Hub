#!/usr/bin/env python3
"""
perf_baseline.py - Deterministic performance-baseline record/compare gate for the
performance-regression-gate skill.

Tier-3 bundled resource: the agent (or CI) invokes it via the shell and consumes
its exit code and table output; the source is never read into the context window.
It has two modes:

    --record <baseline.json> --metrics <current.json>
        Store the current metrics as the committed baseline (with the threshold
        and the higher-is-better direction), to be committed alongside the
        benchmarks.

    --check <baseline.json> --metrics <current.json>
        Compare current metrics against the baseline and EXIT NON-ZERO if any
        metric regressed beyond its threshold. Prints a human-readable diff table.

STDLIB-ONLY and ZERO-NETWORK: argparse, json, sys only. It imports no socket /
urllib / http / requests module and opens no connection; nothing leaves the
machine.

Metrics format (JSON object of name -> number), read from a file or '-' (stdin):
    {"latency_p95_ms": 123.4, "bundle_kb": 512, "throughput_rps": 2100}

Baseline format (written by --record, read by --check):
    {
      "threshold": 0.10,
      "higher_is_better": ["throughput_rps"],
      "metrics": {"latency_p95_ms": 120.0, "bundle_kb": 500, "throughput_rps": 2200}
    }

Regression rule (per metric, baseline B, current C, threshold T):
    lower-is-better  (default): regressed if C > B * (1 + T)
    higher-is-better (flagged): regressed if C < B * (1 - T)
A metric present in current but absent from the baseline is reported NEW
(informational). A baseline metric absent from current is reported MISSING (a
warning, not a failure - it may have been intentionally retired).

Usage:
    python perf_baseline.py --record baseline.json --metrics current.json \
        --threshold 0.10 --higher-is-better throughput_rps
    python perf_baseline.py --check baseline.json --metrics current.json
"""

from __future__ import annotations

import argparse
import json
import sys


def _load_metrics(path: str) -> dict[str, float]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("metrics must be a JSON object of name -> number")
    out: dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"metric {key!r} is not a number: {value!r}")
        out[str(key)] = float(value)
    return out


def _record(
    baseline_path: str, metrics: dict[str, float], threshold: float, higher: list[str]
) -> int:
    payload = {
        "threshold": threshold,
        "higher_is_better": sorted(higher),
        "metrics": metrics,
    }
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    print(
        f"recorded {len(metrics)} metric(s) to {baseline_path} (threshold {threshold:.0%})"
    )
    return 0


def _check(baseline_path: str, current: dict[str, float]) -> int:
    with open(baseline_path, encoding="utf-8") as f:
        baseline = json.load(f)
    threshold = float(baseline.get("threshold", 0.10))
    higher = set(baseline.get("higher_is_better", []))
    base_metrics = baseline.get("metrics", {})

    rows: list[tuple[str, str, str, str, str]] = []
    regressions = 0

    for name in sorted(base_metrics):
        b = float(base_metrics[name])
        if name not in current:
            rows.append((name, f"{b:g}", "-", "MISSING", ""))
            continue
        c = current[name]
        higher_is_better = name in higher
        delta = (c - b) / b if b != 0 else (0.0 if c == 0 else float("inf"))
        if higher_is_better:
            regressed = c < b * (1 - threshold)
        else:
            regressed = c > b * (1 + threshold)
        if regressed:
            regressions += 1
        direction = "higher=better" if higher_is_better else "lower=better"
        rows.append(
            (
                name,
                f"{b:g}",
                f"{c:g}",
                "REGRESSED" if regressed else "ok",
                f"{delta:+.1%} ({direction})",
            )
        )

    for name in sorted(set(current) - set(base_metrics)):
        rows.append((name, "-", f"{current[name]:g}", "NEW", ""))

    _print_table(rows)
    if regressions:
        print(
            f"\nFAIL: {regressions} metric(s) regressed beyond the {threshold:.0%} threshold.",
            file=sys.stderr,
        )
        return 1
    print(f"\nPASS: no metric regressed beyond the {threshold:.0%} threshold.")
    return 0


def _print_table(rows: list[tuple[str, str, str, str, str]]) -> None:
    headers = ("metric", "baseline", "current", "status", "delta")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(row: tuple[str, ...]) -> str:
        return "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))

    print(fmt(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record or check a performance baseline."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--record",
        metavar="BASELINE_JSON",
        help="write current metrics as the baseline",
    )
    mode.add_argument(
        "--check",
        metavar="BASELINE_JSON",
        help="compare current metrics against the baseline; non-zero exit on regression",
    )
    parser.add_argument(
        "--metrics",
        required=True,
        metavar="FILE",
        help="current metrics JSON (name -> number), or '-' for stdin",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="allowed fractional change before a regression (default 0.10 = 10%%)",
    )
    parser.add_argument(
        "--higher-is-better",
        default="",
        help="comma-separated metric names where a higher value is better",
    )
    args = parser.parse_args(argv)

    try:
        metrics = _load_metrics(args.metrics)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error reading metrics: {exc}", file=sys.stderr)
        return 2

    higher = [s.strip() for s in args.higher_is_better.split(",") if s.strip()]

    try:
        if args.record:
            return _record(args.record, metrics, args.threshold, higher)
        return _check(args.check, metrics)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
