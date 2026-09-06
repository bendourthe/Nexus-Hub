"""Deterministic token-savings benchmark for the compiled context map.

Patterned on `extensions/nexus-context-compressor/evals`: a runner plus a
committed `benchmark_baseline.json` gate. It measures the compiled map's token
cost against a SIMULATED manual-exploration cost - what an AI would spend
reading files to discover the same routes / models / components / env vars if it
had no map. The reduction ratio is the measured half of the plan's definition
of done.

Manual-exploration model (the estimation constants are the tool's own):

    manual_cost = (sum of per-file tokens) * REVISIT_MULTIPLIER
                  + routes     * TOKENS_PER_ROUTE
                  + models     * TOKENS_PER_MODEL
                  + components * TOKENS_PER_COMPONENT
                  + env_vars   * TOKENS_PER_ENV

The per-file term grounds the estimate in real file sizes (an AI must read the
files to discover their contents), scaled by a revisit multiplier because
exploration re-reads files; the per-entity terms add the reasoning overhead of
noting each discovered surface. `map_cost` is the compiled map + article tokens.
`reduction_ratio = 1 - map_cost / manual_cost`.

The map cost is computed WITHOUT writing `.nexus/` (via estimate_map_tokens),
and each repo is indexed into a throwaway directory, so a benchmark run never
mutates the repo it measures.

Run it:

    python -m nexus_code_search.contextmap.benchmark --check
    python -m nexus_code_search.contextmap.benchmark --repo /path/to/repo --json
    python -m nexus_code_search.contextmap.benchmark --update-baseline
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.contextmap.generator import estimate_map_tokens
from nexus_code_search.contextmap.tokens import count_tokens
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction import ExtractionOrchestrator

# Manual-exploration cost model constants (the tool's own heuristic, not
# attributed to any external source).
REVISIT_MULTIPLIER = 2.5
TOKENS_PER_ROUTE = 40
TOKENS_PER_MODEL = 60
TOKENS_PER_COMPONENT = 40
TOKENS_PER_ENV = 15

# Floor sits this far below the measured ratio on --update-baseline, so a
# legitimate small improvement never trips the gate.
_RATIO_MARGIN = 0.05

BASELINE_PATH = Path(__file__).resolve().parent / "benchmark_baseline.json"
# The committed regression corpus: realistic, adequately-sized sample repos
# (the tiny per-framework contextmap fixtures are too small to show savings -
# a map isn't worth its overhead on a 2-file repo).
DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "benchmark"
)


@dataclass(frozen=True)
class RepoBenchmark:
    """Token-savings measurement for one repository."""

    label: str
    map_tokens: int
    manual_cost: int
    reduction_ratio: float
    files: int
    routes: int
    models: int
    components: int
    env_vars: int

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "map_tokens": self.map_tokens,
            "manual_cost": self.manual_cost,
            "reduction_ratio": self.reduction_ratio,
            "files": self.files,
            "routes": self.routes,
            "models": self.models,
            "components": self.components,
            "env_vars": self.env_vars,
        }


@dataclass
class BenchmarkReport:
    """Aggregate benchmark result across repos."""

    repos: list[RepoBenchmark] = field(default_factory=list)

    @property
    def aggregate_ratio(self) -> float:
        total_map = sum(r.map_tokens for r in self.repos)
        total_manual = sum(r.manual_cost for r in self.repos)
        if total_manual <= 0:
            return 0.0
        return round(1.0 - total_map / total_manual, 4)

    def to_dict(self) -> dict:
        return {
            "aggregate_reduction_ratio": self.aggregate_ratio,
            "repos": [r.to_dict() for r in self.repos],
        }


def benchmark_repo(root: Path, label: str | None = None) -> RepoBenchmark:
    """Index ``root`` into a throwaway index and measure its token savings."""
    root = Path(root).resolve()
    label = label or root.name
    cfg = CodeSearchConfig(hub_root=None)
    with tempfile.TemporaryDirectory(prefix="nexus-bench-") as tmp:
        index_dir = Path(tmp) / "idx"
        with ExtractionOrchestrator(root, cfg, index_dir) as orch:
            orch.run()
        estimate = estimate_map_tokens(root, index_dir)
        file_tokens = _file_tokens(root, index_dir)

    manual = (
        file_tokens * REVISIT_MULTIPLIER
        + estimate.routes_count * TOKENS_PER_ROUTE
        + estimate.models_count * TOKENS_PER_MODEL
        + estimate.components_count * TOKENS_PER_COMPONENT
        + estimate.env_count * TOKENS_PER_ENV
    )
    ratio = 0.0 if manual <= 0 else max(0.0, 1.0 - estimate.total_tokens / manual)
    return RepoBenchmark(
        label=label,
        map_tokens=estimate.total_tokens,
        manual_cost=round(manual),
        reduction_ratio=round(ratio, 4),
        files=estimate.files_indexed,
        routes=estimate.routes_count,
        models=estimate.models_count,
        components=estimate.components_count,
        env_vars=estimate.env_count,
    )


def _file_tokens(root: Path, index_dir: Path) -> int:
    conn = open_database(index_dir)
    try:
        paths = [row[0] for row in conn.execute("SELECT path FROM files")]
    finally:
        conn.close()
    total = 0
    for rel in paths:
        try:
            total += count_tokens(
                (root / rel).read_text(encoding="utf-8", errors="replace")
            )
        except OSError:
            continue
    return total


def run_benchmark(corpus: Path) -> BenchmarkReport:
    """Benchmark every immediate subdirectory of ``corpus`` (one repo each)."""
    report = BenchmarkReport()
    for repo in sorted(p for p in corpus.iterdir() if p.is_dir()):
        report.repos.append(benchmark_repo(repo, label=repo.name))
    return report


# --- Gate -------------------------------------------------------------------


def load_baseline(path: Path = BASELINE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_baseline(report: BenchmarkReport, baseline: dict) -> list[str]:
    """Return regression messages (empty = PASS).

    A regression is a reduction ratio dropping below its recorded floor (the map
    stopped saving as much). Per-repo floors + an aggregate floor.
    """
    failures: list[str] = []
    repo_floors = baseline.get("repos", {})
    for repo in report.repos:
        floor = repo_floors.get(repo.label, {}).get("min_reduction_ratio")
        if floor is not None and repo.reduction_ratio < float(floor):
            failures.append(
                f"{repo.label}: token reduction {repo.reduction_ratio:.4f} "
                f"< floor {float(floor):.4f}"
            )
    agg_floor = baseline.get("min_aggregate_reduction")
    if agg_floor is not None and report.aggregate_ratio < float(agg_floor):
        failures.append(
            f"aggregate token reduction {report.aggregate_ratio:.4f} "
            f"< floor {float(agg_floor):.4f}"
        )
    return failures


def measured_baseline(report: BenchmarkReport) -> dict:
    return {
        "_comment": (
            "Token-savings benchmark baseline (v3.15.0 adoption-codesight Phase 5). "
            "Each 'min_reduction_ratio' is a floor a safety margin below the measured "
            "map-vs-manual token reduction; the gate fails if the map stops saving "
            "that much. The manual-exploration cost model + constants live in "
            "benchmark.py. Re-baseline with 'python -m nexus_code_search.contextmap."
            "benchmark --update-baseline' and review the diff."
        ),
        "repos": {
            r.label: {
                "min_reduction_ratio": max(
                    0.0, round(r.reduction_ratio - _RATIO_MARGIN, 2)
                )
            }
            for r in report.repos
        },
        "min_aggregate_reduction": max(
            0.0, round(report.aggregate_ratio - _RATIO_MARGIN, 2)
        ),
    }


def render_report(report: BenchmarkReport) -> str:
    lines = ["# Context-map token-savings benchmark", ""]
    lines.append(f"- Aggregate token reduction: **{report.aggregate_ratio:.1%}**")
    lines.append("")
    lines.append("| Repo | Files | Map tokens | Manual cost | Reduction |")
    lines.append("| --- | --- | --- | --- | --- |")
    for r in report.repos:
        lines.append(
            f"| {r.label} | {r.files} | {r.map_tokens} | {r.manual_cost} | "
            f"{r.reduction_ratio:.1%} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m nexus_code_search.contextmap.benchmark",
        description="Deterministic token-savings benchmark + regression gate.",
    )
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument(
        "--repo", type=Path, default=None, help="Benchmark a single repo (no gate)."
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true", help="Fail on a regression.")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args(argv)

    if args.repo is not None:
        report = BenchmarkReport(repos=[benchmark_repo(args.repo)])
    else:
        if not args.corpus.is_dir():
            print(f"error: corpus dir {args.corpus} not found", file=sys.stderr)
            return 2
        report = run_benchmark(args.corpus)

    if args.update_baseline:
        BASELINE_PATH.write_text(
            json.dumps(measured_baseline(report), indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote baseline {BASELINE_PATH}", file=sys.stderr)
        return 0

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_report(report))

    if args.check:
        if not BASELINE_PATH.exists():
            print("error: --check requires benchmark_baseline.json", file=sys.stderr)
            return 2
        failures = check_baseline(report, load_baseline())
        if failures:
            print("\nToken-savings benchmark FAILED:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print(
            f"Token-savings benchmark PASSED "
            f"(aggregate reduction {report.aggregate_ratio:.1%}).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
