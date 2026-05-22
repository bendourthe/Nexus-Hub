"""Eval-runner for nexus-code-search graph queries.

Walks every fixture directory under `eval/fixtures/`, loads its
`fixtures.yaml`, indexes the fixture codebase, runs each question against
the appropriate MCP tool, and scores recall + precision against the answer
key. Emits a Markdown report.

Fixture format (`<fixture>/fixtures.yaml`):

    name: minimal
    description: One-line summary.
    questions:
      - tool: code_search
        query: "compute_total"
        expect: ["compute_total"]            # node names
      - tool: code_callers
        symbol: helper
        expect_callers: ["main"]
      - tool: code_callees
        symbol: main
        expect_callees: ["helper"]
      - tool: code_impact
        symbol: helper
        depth: 2
        expect_in_radius: ["main"]
      - tool: code_context
        symbol: helper
        expect_callers: ["main"]
        expect_callees: []

Scores are reported per-fixture and aggregated. The runner intentionally
ships without an external YAML dependency: it uses a tiny in-tree YAML
subset parser that handles only the constructs the fixtures need.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.graph import GraphQueryManager


@dataclass
class QuestionResult:
    """One scored question."""

    tool: str
    query: str
    expected: list[str]
    found: list[str]
    recall: float
    precision: float

    @property
    def correct(self) -> bool:
        return self.recall >= 1.0


@dataclass
class FixtureResult:
    """All scored questions for one fixture."""

    name: str
    questions: list[QuestionResult] = field(default_factory=list)

    @property
    def aggregate_recall(self) -> float:
        if not self.questions:
            return 0.0
        return sum(q.recall for q in self.questions) / len(self.questions)

    @property
    def aggregate_precision(self) -> float:
        if not self.questions:
            return 0.0
        return sum(q.precision for q in self.questions) / len(self.questions)


@dataclass
class EvalResult:
    """Top-level eval run summary."""

    fixtures: list[FixtureResult] = field(default_factory=list)

    @property
    def aggregate_recall(self) -> float:
        if not self.fixtures:
            return 0.0
        return sum(f.aggregate_recall for f in self.fixtures) / len(self.fixtures)

    @property
    def aggregate_precision(self) -> float:
        if not self.fixtures:
            return 0.0
        return sum(f.aggregate_precision for f in self.fixtures) / len(self.fixtures)


# ---------------------------------------------------------------------------
# YAML loader (tiny in-tree subset; no external dependency required for eval).
# ---------------------------------------------------------------------------


def _parse_fixture_yaml(text: str) -> dict[str, Any]:
    """Parse a single fixture YAML file.

    Supported constructs (deliberately narrow):
      - `key: scalar` at the top level (strings, ints, floats, true/false)
      - `key: "quoted string"` for quoted strings
      - `questions:` followed by a list of `-` entries
      - Each list entry is a block-mapping (`tool: code_search`, `expect: [a, b]`)
      - Inline-list syntax for `expect[*]` values: `[item1, item2, "item 3"]`
    """
    lines = text.splitlines()
    root: dict[str, Any] = {}
    current_list: list[dict[str, Any]] | None = None
    current_item: dict[str, Any] | None = None
    pending_key: str | None = None  # for top-level lists

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            i += 1
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if indent == 0:
            # Top-level key.
            if ":" not in stripped:
                i += 1
                continue
            key, _, rest = stripped.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest == "":
                # List or block follows.
                pending_key = key
                root[key] = []
                current_list = root[key]
                current_item = None
            else:
                root[key] = _parse_scalar(rest)
                pending_key = None
                current_list = None
        else:
            # Indented under the most recent top-level list key.
            if stripped.startswith("- "):
                current_item = {}
                if current_list is None:
                    current_list = []
                    if pending_key is not None:
                        root[pending_key] = current_list
                current_list.append(current_item)
                stripped = stripped[2:]
                if ":" in stripped:
                    key, _, rest = stripped.partition(":")
                    current_item[key.strip()] = _parse_value(rest.strip())
                else:
                    # Pure list-of-scalars - rare for our fixtures but valid.
                    current_list[-1] = _parse_scalar(stripped)
            elif current_item is not None and ":" in stripped:
                key, _, rest = stripped.partition(":")
                current_item[key.strip()] = _parse_value(rest.strip())
        i += 1
    return root


def _parse_value(text: str) -> Any:
    if text.startswith("[") and text.endswith("]"):
        # Inline list.
        body = text[1:-1].strip()
        if not body:
            return []
        # Split on commas not inside quotes.
        parts: list[str] = []
        current = ""
        in_quote: str | None = None
        for ch in body:
            if in_quote is not None:
                current += ch
                if ch == in_quote:
                    in_quote = None
            elif ch in ("'", '"'):
                current += ch
                in_quote = ch
            elif ch == ",":
                parts.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            parts.append(current.strip())
        return [_parse_scalar(p) for p in parts]
    return _parse_scalar(text)


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    lower = text.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "~", "none"):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score(expected: list[str], found: list[str]) -> tuple[float, float]:
    """Return (recall, precision)."""
    if not expected:
        # No-expectation question; treat as pass when nothing extra was found.
        return 1.0, 1.0 if not found else 0.0
    expected_set = set(expected)
    found_set = set(found)
    hits = expected_set & found_set
    recall = len(hits) / len(expected_set)
    precision = len(hits) / len(found_set) if found_set else 0.0
    return recall, precision


def _node_names(results: list[dict]) -> list[str]:
    return [r.get("name", "") for r in results if r.get("name")]


def _ask_question(qm: GraphQueryManager, question: dict[str, Any]) -> QuestionResult:
    tool = question.get("tool", "")
    expected: list[str] = []
    found: list[str] = []
    query_label = ""

    if tool == "code_search":
        query = question.get("query", "")
        query_label = query
        expected = list(question.get("expect", []) or [])
        results = qm.search(query)
        found = _node_names(results)
    elif tool == "code_callers":
        symbol = question.get("symbol", "")
        query_label = symbol
        expected = list(question.get("expect_callers", []) or [])
        payload = qm.callers_of(symbol)
        found = [r["caller"]["name"] for r in payload.get("results", [])]
    elif tool == "code_callees":
        symbol = question.get("symbol", "")
        query_label = symbol
        expected = list(question.get("expect_callees", []) or [])
        payload = qm.callees_of(symbol)
        found = [r["callee"]["name"] for r in payload.get("results", [])]
    elif tool == "code_impact":
        symbol = question.get("symbol", "")
        depth = int(question.get("depth", 2))
        query_label = symbol
        expected = list(question.get("expect_in_radius", []) or [])
        payload = qm.impact_of(symbol, depth=depth)
        for entry in payload.get("results", []):
            for hit in entry.get("impact", []):
                found.append(hit["name"])
    elif tool == "code_context":
        symbol = question.get("symbol", "")
        query_label = symbol
        expected = list(question.get("expect_callers", []) or []) + list(
            question.get("expect_callees", []) or []
        )
        payload = qm.context_for(symbol)
        for ctx in payload.get("results", []):
            for c in ctx.get("callers", []):
                found.append(c["name"])
            for c in ctx.get("callees", []):
                found.append(c["name"])
    else:
        # Unknown tool - score as zero recall.
        return QuestionResult(
            tool=tool,
            query=str(question),
            expected=[],
            found=[],
            recall=0.0,
            precision=0.0,
        )

    recall, precision = _score(expected, found)
    return QuestionResult(
        tool=tool,
        query=query_label,
        expected=expected,
        found=found,
        recall=recall,
        precision=precision,
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _list_fixtures(fixtures_root: Path) -> list[Path]:
    return sorted(
        [p for p in fixtures_root.iterdir() if p.is_dir() and (p / "fixtures.yaml").exists()]
    )


def _run_fixture(
    fixture_dir: Path,
    work_dir: Path,
) -> FixtureResult:
    spec = _parse_fixture_yaml((fixture_dir / "fixtures.yaml").read_text(encoding="utf-8"))
    name = spec.get("name", fixture_dir.name)
    questions = spec.get("questions", []) or []
    config = CodeSearchConfig(hub_root=None)
    index_dir = work_dir / ".nexus" / "code-index"
    code_dir = fixture_dir / "code"
    if not code_dir.exists():
        # Fall back to the whole fixture dir minus fixtures.yaml.
        code_dir = fixture_dir
    # Copy source into a workdir so the on-disk db lives next to it.
    work_code = work_dir / "code"
    work_code.mkdir(parents=True, exist_ok=True)
    _mirror_tree(code_dir, work_code)
    with ExtractionOrchestrator(work_code, config, index_dir) as orch:
        orch.run(force=True)
    conn = open_database(index_dir)
    try:
        qm = GraphQueryManager(conn)
        results = [_ask_question(qm, q) for q in questions]
    finally:
        conn.close()
    return FixtureResult(name=name, questions=results)


def _mirror_tree(src: Path, dst: Path) -> None:
    for p in src.rglob("*"):
        if p.name == "fixtures.yaml":
            continue
        if p.is_file():
            target = dst / p.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())


def run_eval(fixtures_root: Path, work_dir: Path) -> EvalResult:
    fixtures = _list_fixtures(fixtures_root)
    result = EvalResult()
    for fixture in fixtures:
        per_fixture_dir = work_dir / fixture.name
        per_fixture_dir.mkdir(parents=True, exist_ok=True)
        result.fixtures.append(_run_fixture(fixture, per_fixture_dir))
    return result


def render_report(result: EvalResult) -> str:
    lines: list[str] = []
    lines.append("# nexus-code-search eval report")
    lines.append("")
    lines.append(
        f"Aggregate recall: **{result.aggregate_recall:.1%}** "
        f"Aggregate precision: **{result.aggregate_precision:.1%}**"
    )
    lines.append("")
    lines.append("## Per-fixture")
    lines.append("")
    lines.append("| Fixture | Questions | Recall | Precision |")
    lines.append("|---------|-----------|--------|-----------|")
    for fix in result.fixtures:
        lines.append(
            f"| {fix.name} | {len(fix.questions)} | "
            f"{fix.aggregate_recall:.1%} | {fix.aggregate_precision:.1%} |"
        )
    lines.append("")
    for fix in result.fixtures:
        lines.append(f"## {fix.name}")
        lines.append("")
        lines.append("| Tool | Query | Expected | Found | Recall | Precision |")
        lines.append("|------|-------|----------|-------|--------|-----------|")
        for q in fix.questions:
            lines.append(
                f"| {q.tool} | `{q.query}` | "
                f"{', '.join(q.expected) or '(none)'} | "
                f"{', '.join(q.found) or '(none)'} | "
                f"{q.recall:.1%} | {q.precision:.1%} |"
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    default_fixtures = here / "fixtures"

    parser = argparse.ArgumentParser(
        prog="nexus-code-search-eval",
        description="Run the synthetic-codebase eval harness.",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=default_fixtures,
        help=f"Fixture root (default: {default_fixtures}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the Markdown report to this path (default: stdout).",
    )
    parser.add_argument(
        "--work",
        type=Path,
        default=None,
        help="Working directory for the indexed copies (default: temp).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown.",
    )
    args = parser.parse_args(argv)

    if not args.fixtures.exists():
        print(f"error: fixtures dir {args.fixtures} not found", file=sys.stderr)
        return 1

    import tempfile

    if args.work is None:
        work_ctx = tempfile.TemporaryDirectory(prefix="nexus-eval-")
        work_dir = Path(work_ctx.name)
    else:
        work_ctx = None
        work_dir = args.work
        work_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = run_eval(args.fixtures, work_dir)
    finally:
        if work_ctx is not None:
            work_ctx.cleanup()

    if args.json:
        payload = {
            "aggregate_recall": result.aggregate_recall,
            "aggregate_precision": result.aggregate_precision,
            "fixtures": [
                {
                    "name": f.name,
                    "recall": f.aggregate_recall,
                    "precision": f.aggregate_precision,
                    "questions": [
                        {
                            "tool": q.tool,
                            "query": q.query,
                            "expected": q.expected,
                            "found": q.found,
                            "recall": q.recall,
                            "precision": q.precision,
                        }
                        for q in f.questions
                    ],
                }
                for f in result.fixtures
            ],
        }
        body = json.dumps(payload, indent=2)
    else:
        body = render_report(result)

    if args.out is not None:
        args.out.write_text(body, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
