#!/usr/bin/env python3
"""Aggregate paired with_skill / without_skill runs into a per-iteration benchmark.

Reads an iteration directory produced by the skill-eval-loop:

    <workspace>/iteration-N/
      eval-001/
        with_skill/    outputs/run_metadata.json   grading.json
        without_skill/ outputs/run_metadata.json   grading.json
      eval-002/
        ...

Emits two artifacts in the same directory:
    benchmark.json   structured per-eval and overall metrics
    benchmark.md     same data formatted for human review

Schema is documented at:
    catalog/skills/workflow/skill-eval-loop/references/schemas.md

Cross-platform: stdlib-only (json, statistics, pathlib, argparse, datetime).
No CLI invocation here. The aggregator is run AFTER the paired runs and
their grading.json files have been written by the runner / grader.

Usage:
    python scripts/aggregate_benchmark.py <iteration_dir>
    python scripts/aggregate_benchmark.py <iteration_dir> --output-dir <other>
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_RUN_CONDITIONS = ("with_skill", "without_skill")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _safe_stats(values: list[float]) -> tuple[float, float]:
    """Return (mean, stddev). Stddev is 0 for a single sample. Empty -> (0.0, 0.0)."""
    if not values:
        return 0.0, 0.0
    mean = statistics.fmean(values)
    if len(values) < 2:
        return mean, 0.0
    return mean, statistics.pstdev(values)


def _aggregate_run_condition(eval_dir: Path, condition: str) -> dict[str, Any]:
    """Aggregate one run condition (with_skill or without_skill) for one eval."""
    run_dir = eval_dir / condition
    grading = _read_json(run_dir / "grading.json")
    metadata = _read_json(run_dir / "outputs" / "run_metadata.json")

    pass_rate = float(grading["pass_rate"]) if grading and "pass_rate" in grading else 0.0
    durations = []
    tokens = []
    if metadata:
        if "duration_ms" in metadata:
            durations.append(float(metadata["duration_ms"]))
        if "total_tokens" in metadata:
            tokens.append(float(metadata["total_tokens"]))

    duration_mean, duration_stddev = _safe_stats(durations)
    tokens_mean, tokens_stddev = _safe_stats(tokens)

    return {
        "pass_rate": round(pass_rate, 3),
        "duration_ms_mean": round(duration_mean, 1),
        "duration_ms_stddev": round(duration_stddev, 1),
        "tokens_mean": round(tokens_mean, 1),
        "tokens_stddev": round(tokens_stddev, 1),
        "graded": grading is not None,
        "metadata_present": metadata is not None,
    }


def _aggregate_eval(eval_dir: Path) -> dict[str, Any]:
    by_condition = {cond: _aggregate_run_condition(eval_dir, cond) for cond in _RUN_CONDITIONS}
    delta = {
        "pass_rate": round(
            by_condition["with_skill"]["pass_rate"]
            - by_condition["without_skill"]["pass_rate"],
            3,
        ),
        "duration_ms": round(
            by_condition["with_skill"]["duration_ms_mean"]
            - by_condition["without_skill"]["duration_ms_mean"],
            1,
        ),
        "tokens": round(
            by_condition["with_skill"]["tokens_mean"]
            - by_condition["without_skill"]["tokens_mean"],
            1,
        ),
    }
    return {**by_condition, "delta": delta}


def aggregate(iteration_dir: Path) -> dict[str, Any]:
    """Aggregate every eval-XXX subdirectory under `iteration_dir`."""
    if not iteration_dir.is_dir():
        raise FileNotFoundError(f"iteration directory does not exist: {iteration_dir}")

    eval_dirs = sorted(d for d in iteration_dir.iterdir() if d.is_dir() and d.name.startswith("eval-"))
    by_eval: dict[str, Any] = {}
    for eval_dir in eval_dirs:
        by_eval[eval_dir.name] = _aggregate_eval(eval_dir)

    # Overall metrics: simple means across evals (one sample per eval per condition).
    overall: dict[str, Any] = {}
    for cond in _RUN_CONDITIONS:
        pass_rates = [v[cond]["pass_rate"] for v in by_eval.values()]
        durations = [v[cond]["duration_ms_mean"] for v in by_eval.values()]
        tokens = [v[cond]["tokens_mean"] for v in by_eval.values()]
        pr_mean, _ = _safe_stats(pass_rates)
        dur_mean, _ = _safe_stats(durations)
        tok_mean, _ = _safe_stats(tokens)
        overall[f"{cond}_pass_rate"] = round(pr_mean, 3)
        overall[f"{cond}_duration_ms_mean"] = round(dur_mean, 1)
        overall[f"{cond}_tokens_mean"] = round(tok_mean, 1)

    overall["pass_rate_delta"] = round(
        overall["with_skill_pass_rate"] - overall["without_skill_pass_rate"], 3
    )

    iteration = _parse_iteration_number(iteration_dir.name)

    return {
        "iteration": iteration,
        "n_evals": len(by_eval),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "by_eval": by_eval,
        "overall": overall,
    }


def _parse_iteration_number(name: str) -> int:
    if name.startswith("iteration-"):
        try:
            return int(name.split("-", 1)[1])
        except (ValueError, IndexError):
            return 0
    return 0


def render_markdown(benchmark: dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Benchmark - iteration {benchmark['iteration']}")
    lines.append("")
    lines.append(f"Generated: {benchmark['generated_at']}")
    lines.append(f"Evals: {benchmark['n_evals']}")
    lines.append("")
    lines.append("## Overall")
    lines.append("")
    o = benchmark["overall"]
    lines.append("| Metric | with_skill | without_skill | Delta |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| Pass rate | {o['with_skill_pass_rate']:.3f} | "
        f"{o['without_skill_pass_rate']:.3f} | {o['pass_rate_delta']:+.3f} |"
    )
    lines.append(
        f"| Duration mean (ms) | {o['with_skill_duration_ms_mean']:.0f} | "
        f"{o['without_skill_duration_ms_mean']:.0f} | "
        f"{o['with_skill_duration_ms_mean'] - o['without_skill_duration_ms_mean']:+.0f} |"
    )
    lines.append(
        f"| Tokens mean | {o['with_skill_tokens_mean']:.0f} | "
        f"{o['without_skill_tokens_mean']:.0f} | "
        f"{o['with_skill_tokens_mean'] - o['without_skill_tokens_mean']:+.0f} |"
    )
    lines.append("")
    lines.append("## Per-eval")
    lines.append("")
    lines.append("| Eval | with_skill pass | without_skill pass | Delta | with_skill ms | without_skill ms |")
    lines.append("|---|---|---|---|---|---|")
    for eval_id, data in benchmark["by_eval"].items():
        ws = data["with_skill"]
        wos = data["without_skill"]
        delta = data["delta"]
        lines.append(
            f"| {eval_id} | {ws['pass_rate']:.3f} | {wos['pass_rate']:.3f} | "
            f"{delta['pass_rate']:+.3f} | {ws['duration_ms_mean']:.0f} | "
            f"{wos['duration_ms_mean']:.0f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "iteration_dir",
        type=Path,
        help="Path to the iteration directory (e.g., my-skill-workspace/iteration-1)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Where to write benchmark.json and benchmark.md (default: iteration_dir)",
    )
    args = parser.parse_args()

    output_dir = args.output_dir or args.iteration_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        benchmark = aggregate(args.iteration_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    json_path = output_dir / "benchmark.json"
    md_path = output_dir / "benchmark.md"
    json_path.write_text(json.dumps(benchmark, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(benchmark), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(
        f"Overall: with_skill pass={benchmark['overall']['with_skill_pass_rate']:.3f} "
        f"vs without_skill pass={benchmark['overall']['without_skill_pass_rate']:.3f} "
        f"(delta={benchmark['overall']['pass_rate_delta']:+.3f})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
