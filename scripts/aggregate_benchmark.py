#!/usr/bin/env python3
"""Aggregate skill-eval-loop runs into a per-iteration benchmark.

Reads an iteration directory produced by the skill-eval-loop:

    <workspace>/iteration-N/
      eval-001/
        with_skill/    outputs/run_metadata.json   grading.json
        without_skill/ outputs/run_metadata.json   grading.json
        raw_memory/    outputs/run_metadata.json   grading.json  # optional
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
_OPTIONAL_RUN_CONDITION = "raw_memory"


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
    """Aggregate one run condition for one eval."""
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

    # Premature-action flag (T014): the runner/grader records whether the agent
    # invoked another tool before loading the Skill (see optimize_skill_
    # description.detect_premature_action). Surfaced here so the benchmark output
    # carries the trigger-discipline signal alongside pass-rate. Defaults to
    # False when the run predates the field or the condition has no skill to load.
    premature_action = bool(
        (grading or {}).get("premature_action", (metadata or {}).get("premature_action", False))
    )

    return {
        "pass_rate": round(pass_rate, 3),
        "duration_ms_mean": round(duration_mean, 1),
        "duration_ms_stddev": round(duration_stddev, 1),
        "tokens_mean": round(tokens_mean, 1),
        "tokens_stddev": round(tokens_stddev, 1),
        "premature_action": premature_action,
        "graded": grading is not None,
        "metadata_present": metadata is not None,
    }


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _aggregate_raw_memory_condition(eval_dir: Path) -> dict[str, Any]:
    """Validate and aggregate the optional arm without scoring partial artifacts."""
    run_dir = eval_dir / _OPTIONAL_RUN_CONDITION
    grading = _read_json(run_dir / "grading.json")
    metadata = _read_json(run_dir / "outputs" / "run_metadata.json")
    errors: list[str] = []

    if metadata is None:
        errors.append("missing or invalid outputs/run_metadata.json")
    else:
        if metadata.get("skill_loaded") is not False:
            errors.append("skill_loaded must be false")
        if metadata.get("memory_injected") is not True:
            errors.append("memory_injected must be true")
        if not _is_number(metadata.get("duration_ms")):
            errors.append("duration_ms must be numeric")
        if not _is_number(metadata.get("total_tokens")):
            errors.append("total_tokens must be numeric")
        if metadata.get("exit_code") != 0:
            errors.append("exit_code must be 0")

        paired_clis: set[str] = set()
        for condition in _RUN_CONDITIONS:
            paired = _read_json(eval_dir / condition / "outputs" / "run_metadata.json")
            if paired is None or not isinstance(paired.get("cli"), str):
                errors.append(f"{condition} CLI metadata is missing")
            else:
                paired_clis.add(paired["cli"])
        raw_cli = metadata.get("cli")
        if not isinstance(raw_cli, str):
            errors.append("cli must be a string")
        elif len(paired_clis) != 1 or raw_cli not in paired_clis:
            errors.append("cli must match both paired runs")

    if grading is None:
        errors.append("missing or invalid grading.json")
    elif not _is_number(grading.get("pass_rate")):
        errors.append("grading pass_rate must be numeric")

    if errors:
        return {"status": "invalid", "errors": errors}

    metrics = _aggregate_run_condition(eval_dir, _OPTIONAL_RUN_CONDITION)
    return {"status": "run", **metrics}


def _aggregate_eval(eval_dir: Path) -> dict[str, Any]:
    by_condition = {cond: _aggregate_run_condition(eval_dir, cond) for cond in _RUN_CONDITIONS}
    raw_memory_dir = eval_dir / _OPTIONAL_RUN_CONDITION
    raw_memory: dict[str, Any] | str = (
        _aggregate_raw_memory_condition(eval_dir)
        if raw_memory_dir.is_dir()
        else "not_run"
    )
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
    # Premature action is a with_skill-only property (the baseline run has no
    # skill to load before), so the eval-level flag mirrors the with_skill run.
    premature_action = bool(by_condition["with_skill"].get("premature_action", False))
    return {
        **by_condition,
        _OPTIONAL_RUN_CONDITION: raw_memory,
        "delta": delta,
        "premature_action": premature_action,
    }


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

    raw_memory_runs = [
        value[_OPTIONAL_RUN_CONDITION]
        for value in by_eval.values()
        if isinstance(value[_OPTIONAL_RUN_CONDITION], dict)
        and value[_OPTIONAL_RUN_CONDITION].get("status") == "run"
    ]
    invalid_raw_memory = [
        eval_id
        for eval_id, value in by_eval.items()
        if isinstance(value[_OPTIONAL_RUN_CONDITION], dict)
        and value[_OPTIONAL_RUN_CONDITION].get("status") == "invalid"
    ]
    if raw_memory_runs:
        raw_pass_rate, _ = _safe_stats([run["pass_rate"] for run in raw_memory_runs])
        raw_duration, _ = _safe_stats([run["duration_ms_mean"] for run in raw_memory_runs])
        raw_tokens, _ = _safe_stats([run["tokens_mean"] for run in raw_memory_runs])
        overall[_OPTIONAL_RUN_CONDITION] = {
            "status": "partial" if invalid_raw_memory else "run",
            "n_evals": len(raw_memory_runs),
            "pass_rate": round(raw_pass_rate, 3),
            "duration_ms_mean": round(raw_duration, 1),
            "tokens_mean": round(raw_tokens, 1),
        }
        if invalid_raw_memory:
            overall[_OPTIONAL_RUN_CONDITION]["invalid_evals"] = invalid_raw_memory
    elif invalid_raw_memory:
        overall[_OPTIONAL_RUN_CONDITION] = {
            "status": "invalid",
            "n_evals": 0,
            "invalid_evals": invalid_raw_memory,
        }
    else:
        overall[_OPTIONAL_RUN_CONDITION] = "not_run"

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
    raw_memory = o["raw_memory"]
    lines.append("## Raw memory arm")
    lines.append("")
    if raw_memory == "not_run":
        lines.append("Status: not_run")
    elif raw_memory["status"] == "invalid":
        lines.append(f"Status: invalid ({', '.join(raw_memory['invalid_evals'])})")
    else:
        lines.append(f"Status: {raw_memory['status']}")
        if raw_memory.get("invalid_evals"):
            lines.append(f"Invalid evals: {', '.join(raw_memory['invalid_evals'])}")
        lines.append("")
        lines.append("| Evals run | Pass rate | Duration mean (ms) | Tokens mean |")
        lines.append("|---|---|---|---|")
        lines.append(
            f"| {raw_memory['n_evals']} | {raw_memory['pass_rate']:.3f} | "
            f"{raw_memory['duration_ms_mean']:.0f} | {raw_memory['tokens_mean']:.0f} |"
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
