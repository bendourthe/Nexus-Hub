"""Offline cost and retrieval-quality benchmark for nexus-code-search."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.contextmap.tokens import estimate_tokens_offline
from nexus_code_search.response_codec import encode_response
from nexus_code_search.server import (
    _dispatch_tool,
    tool_definition_token_count,
)

SUPPORTED_TOOLS = frozenset(
    {"code_search", "code_callers", "code_delete_safety", "code_impact"}
)
SUPPORTED_PROFILES = frozenset({"minimal", "standard", "full"})
SUPPORTED_SHAPES = frozenset(
    {"locate_symbol", "find_callers", "identify_unused", "trace_impact"}
)


@dataclass(frozen=True)
class GoldTask:
    id: str
    shape: str
    tool: str
    profile: str
    arguments: dict[str, Any]
    expected: list[str]


@dataclass(frozen=True)
class Goldset:
    version: int
    corpus: Path
    tasks: list[GoldTask]


@dataclass(frozen=True)
class RankedScore:
    precision: float
    recall: float
    reciprocal_rank: float


@dataclass(frozen=True)
class TaskMeasurement:
    id: str
    shape: str
    tool: str
    profile: str
    expected: list[str]
    found: list[str]
    precision: float
    recall: float
    reciprocal_rank: float
    json_bytes: int
    compact_bytes: int
    json_tokens: int
    compact_tokens: int
    all_tools_definition_tokens: int
    profiled_definition_tokens: int
    latency_ms: float


@dataclass(frozen=True)
class QualitySummary:
    precision: float
    recall: float
    mean_reciprocal_rank: float


@dataclass(frozen=True)
class CostSummary:
    all_tools_json_bytes: int
    profiled_compact_bytes: int
    byte_savings: int
    byte_savings_pct: float
    json_tokens: int
    compact_tokens: int
    all_tools_definition_tokens: int
    profiled_definition_tokens: int


@dataclass(frozen=True)
class BenchmarkReport:
    schema_version: int
    goldset_version: int
    tasks: list[TaskMeasurement]
    quality: QualitySummary
    cost: CostSummary

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_goldset(path: Path) -> Goldset:
    """Load and strictly validate a versioned benchmark goldset."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid goldset: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ValueError("goldset version must be 1")
    corpus_name = raw.get("corpus")
    if not isinstance(corpus_name, str) or not corpus_name:
        raise ValueError("goldset corpus must be a non-empty relative path")
    corpus = (path.parent / corpus_name).resolve()
    try:
        corpus.relative_to(path.parent.resolve())
    except ValueError as exc:
        raise ValueError("goldset corpus must stay under the benchmark directory") from exc
    if not corpus.is_dir():
        raise ValueError(f"goldset corpus does not exist: {corpus}")

    raw_tasks = raw.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError("goldset tasks must be a non-empty list")
    tasks: list[GoldTask] = []
    seen_ids: set[str] = set()
    for raw_task in raw_tasks:
        if not isinstance(raw_task, dict):
            raise TypeError("each goldset task must be an object")
        task_id = raw_task.get("id")
        shape = raw_task.get("shape")
        tool = raw_task.get("tool")
        profile = raw_task.get("profile")
        arguments = raw_task.get("arguments")
        expected = raw_task.get("expected")
        if not isinstance(task_id, str) or not task_id or task_id in seen_ids:
            raise ValueError("task ids must be non-empty and unique")
        if shape not in SUPPORTED_SHAPES:
            raise ValueError(f"unsupported task shape: {shape}")
        if tool not in SUPPORTED_TOOLS:
            raise ValueError(f"unsupported tool: {tool}")
        if profile not in SUPPORTED_PROFILES:
            raise ValueError(f"unsupported profile: {profile}")
        if not isinstance(arguments, dict):
            raise TypeError(f"task {task_id} arguments must be an object")
        if not isinstance(expected, list) or not all(
            isinstance(item, str) and item for item in expected
        ):
            raise ValueError(f"task {task_id} expected must be a string list")
        seen_ids.add(task_id)
        tasks.append(GoldTask(task_id, shape, tool, profile, arguments, expected))
    return Goldset(version=1, corpus=corpus, tasks=tasks)


def score_ranked(expected: list[str], found: list[str]) -> RankedScore:
    """Score unique ranked answers with explicit empty-set semantics."""

    expected_set = set(expected)
    unique_found = list(dict.fromkeys(found))
    found_set = set(unique_found)
    if not expected_set:
        value = 1.0 if not found_set else 0.0
        return RankedScore(value, 1.0, value)
    hits = expected_set & found_set
    precision = len(hits) / len(found_set) if found_set else 0.0
    recall = len(hits) / len(expected_set)
    first_rank = next(
        (index for index, item in enumerate(unique_found, start=1) if item in expected_set),
        None,
    )
    reciprocal_rank = 0.0 if first_rank is None else 1.0 / first_rank
    return RankedScore(precision, recall, reciprocal_rank)


def _ranked_answers(tool: str, payload: dict[str, Any]) -> list[str]:
    if tool == "code_search":
        return [row["name"] for row in payload.get("results", []) if row.get("name")]
    if tool == "code_callers":
        return [
            row["caller"]["name"]
            for row in payload.get("results", [])
            if row.get("caller", {}).get("name")
        ]
    if tool == "code_impact":
        return [
            node["name"]
            for row in payload.get("results", [])
            for node in row.get("impact", [])
            if node.get("name")
        ]
    if tool == "code_delete_safety":
        verdict = payload.get("verdict", {})
        tier = verdict.get("tier") if isinstance(verdict, dict) else None
        return [tier] if isinstance(tier, str) else []
    raise ValueError(f"unsupported tool: {tool}")


def _measure_task(
    task: GoldTask, corpus: Path, config: CodeSearchConfig
) -> TaskMeasurement:
    arguments = {"root": str(corpus), **task.arguments}
    started = time.perf_counter()
    contents = _dispatch_tool(task.tool, arguments, config)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    json_text = contents[0].text
    payload = json.loads(json_text)
    compact_text = encode_response(payload, response_format="compact")
    found = _ranked_answers(task.tool, payload)
    score = score_ranked(task.expected, found)
    return TaskMeasurement(
        id=task.id,
        shape=task.shape,
        tool=task.tool,
        profile=task.profile,
        expected=task.expected,
        found=found,
        precision=score.precision,
        recall=score.recall,
        reciprocal_rank=score.reciprocal_rank,
        json_bytes=len(json_text.encode("utf-8")),
        compact_bytes=len(compact_text.encode("utf-8")),
        json_tokens=estimate_tokens_offline(json_text),
        compact_tokens=estimate_tokens_offline(compact_text),
        all_tools_definition_tokens=tool_definition_token_count("full"),
        profiled_definition_tokens=tool_definition_token_count(task.profile),
        latency_ms=elapsed_ms,
    )


def run_benchmark(goldset_path: Path, work_dir: Path) -> BenchmarkReport:
    """Run all gold tasks against a fresh local copy of the corpus."""

    goldset = load_goldset(goldset_path)
    work_dir.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=work_dir))
    corpus = run_dir / "corpus"
    try:
        shutil.copytree(goldset.corpus, corpus)
        config = CodeSearchConfig(hub_root=None)
        _dispatch_tool("index_graph", {"root": str(corpus), "force": True}, config)
        tasks = [_measure_task(task, corpus, config) for task in goldset.tasks]
        count = len(tasks)
        quality = QualitySummary(
            precision=sum(task.precision for task in tasks) / count,
            recall=sum(task.recall for task in tasks) / count,
            mean_reciprocal_rank=sum(task.reciprocal_rank for task in tasks) / count,
        )
        json_bytes = sum(task.json_bytes for task in tasks)
        compact_bytes = sum(task.compact_bytes for task in tasks)
        byte_savings = json_bytes - compact_bytes
        cost = CostSummary(
            all_tools_json_bytes=json_bytes,
            profiled_compact_bytes=compact_bytes,
            byte_savings=byte_savings,
            byte_savings_pct=(byte_savings / json_bytes * 100.0) if json_bytes else 0.0,
            json_tokens=sum(task.json_tokens for task in tasks),
            compact_tokens=sum(task.compact_tokens for task in tasks),
            all_tools_definition_tokens=sum(
                task.all_tools_definition_tokens for task in tasks
            ),
            profiled_definition_tokens=sum(
                task.profiled_definition_tokens for task in tasks
            ),
        )
        return BenchmarkReport(1, goldset.version, tasks, quality, cost)
    finally:
        # OneDrive and antivirus scanners can briefly retain SQLite handles on
        # Windows. Unique runs avoid collisions when cleanup cannot remove one.
        shutil.rmtree(run_dir, ignore_errors=True)


def _quality_values(report: BenchmarkReport | dict[str, float]) -> dict[str, float]:
    if isinstance(report, BenchmarkReport):
        return asdict(report.quality)
    return report


def compare_quality(
    report: BenchmarkReport | dict[str, float],
    baseline: dict[str, float],
    *,
    tolerance: float,
) -> list[str]:
    """Return deterministic quality regressions beyond ``tolerance``."""

    current = _quality_values(report)
    failures: list[str] = []
    for metric in ("precision", "recall", "mean_reciprocal_rank"):
        before = float(baseline[metric])
        after = float(current[metric])
        if before - after > tolerance:
            failures.append(
                f"{metric} dropped from {before:.4f} to {after:.4f} "
                f"(tolerance {tolerance:.4f})"
            )
    return failures


def render_markdown(report: BenchmarkReport) -> str:
    """Render one human-readable report from the machine-readable receipt."""

    cost = report.cost
    lines = [
        "# nexus-code-search deterministic benchmark",
        "",
        "Preliminary small-sample regression evidence. See `METHODOLOGY.md`.",
        "",
        "## Quality",
        "",
        "| Task | Tool | Precision | Recall | MRR |",
        "|---|---|---:|---:|---:|",
    ]
    for task in report.tasks:
        lines.append(
            f"| {task.id} | `{task.tool}` | {task.precision:.1%} | "
            f"{task.recall:.1%} | {task.reciprocal_rank:.3f} |"
        )
    lines.extend(
        [
            "",
            (
                f"Macro precision: **{report.quality.precision:.1%}**; "
                f"macro recall: **{report.quality.recall:.1%}**; "
                f"mean reciprocal rank: **{report.quality.mean_reciprocal_rank:.3f}**."
            ),
            "",
            "## Cost",
            "",
            "| Configuration | Response bytes | Response tokens | Definition tokens |",
            "|---|---:|---:|---:|",
            (
                f"| All tools + JSON | {cost.all_tools_json_bytes} | "
                f"{cost.json_tokens} | {cost.all_tools_definition_tokens} |"
            ),
            (
                f"| Profiled + JSON | {cost.all_tools_json_bytes} | "
                f"{cost.json_tokens} | {cost.profiled_definition_tokens} |"
            ),
            (
                f"| All tools + compact | {cost.profiled_compact_bytes} | "
                f"{cost.compact_tokens} | {cost.all_tools_definition_tokens} |"
            ),
            (
                f"| Profiled + compact | {cost.profiled_compact_bytes} | "
                f"{cost.compact_tokens} | {cost.profiled_definition_tokens} |"
            ),
            "",
            (
                f"Aggregate response-byte savings: **{cost.byte_savings} bytes "
                f"({cost.byte_savings_pct:.1f}%)**."
            ),
            "",
            "## Latency",
            "",
            "| Task | Wall-clock latency (ms) |",
            "|---|---:|",
        ]
    )
    for task in report.tasks:
        lines.append(f"| {task.id} | {task.latency_ms:.3f} |")
    lines.append("")
    return "\n".join(lines)


def write_reports(
    report: BenchmarkReport, *, json_path: Path, markdown_path: Path
) -> None:
    """Write reproducible JSON and human-readable Markdown receipts."""

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Run the offline nexus-code-search cost and quality benchmark."
    )
    parser.add_argument("--goldset", type=Path, default=here / "goldset.json")
    parser.add_argument("--work", type=Path, default=here / ".work")
    parser.add_argument("--json-out", type=Path, default=here / "report.json")
    parser.add_argument("--markdown-out", type=Path, default=here / "report.md")
    parser.add_argument("--baseline", type=Path, default=here / "baseline.json")
    parser.add_argument("--tolerance", type=float, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    report = run_benchmark(args.goldset, args.work)
    write_reports(report, json_path=args.json_out, markdown_path=args.markdown_out)
    if not args.check:
        print(render_markdown(report))
        return 0

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    tolerance = (
        float(args.tolerance)
        if args.tolerance is not None
        else float(baseline.get("tolerance", 0.0))
    )
    failures = compare_quality(report, baseline["quality"], tolerance=tolerance)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("PASS: deterministic retrieval quality matches the stored baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
