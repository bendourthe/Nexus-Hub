"""Eval-runner smoke tests (T033).

These tests assert the harness runs and emits a Markdown report. They do NOT
assert specific score thresholds - those live in docs/v2.3.0/eval-baseline.md
and are guarded by `make eval` in CI - except the per-fixture recall gate
(>= 80%), which is asserted here so a new extractor cannot silently regress.
"""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.eval.runner import (
    EvalResult,
    _parse_fixture_yaml,
    _score,
    render_report,
    run_eval,
)

FIXTURES_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "nexus_code_search"
    / "eval"
    / "fixtures"
)


def test_fixture_yaml_parser_handles_inline_lists() -> None:
    spec = _parse_fixture_yaml(
        "name: demo\n"
        "description: test\n"
        "questions:\n"
        "  - tool: code_search\n"
        "    query: helper\n"
        "    expect: [helper, main]\n"
    )
    assert spec["name"] == "demo"
    assert spec["description"] == "test"
    assert len(spec["questions"]) == 1
    q = spec["questions"][0]
    assert q["tool"] == "code_search"
    assert q["query"] == "helper"
    assert q["expect"] == ["helper", "main"]


def test_score_returns_recall_and_precision() -> None:
    # Perfect match.
    assert _score(["a", "b"], ["a", "b"]) == (1.0, 1.0)
    # Half recall, perfect precision.
    assert _score(["a", "b"], ["a"]) == (0.5, 1.0)
    # Perfect recall, half precision (extra noise).
    recall, precision = _score(["a"], ["a", "b"])
    assert recall == 1.0
    assert precision == 0.5
    # No expectation: both 1.0 when found is empty.
    assert _score([], []) == (1.0, 1.0)
    # No expectation, but something found: precision drops to 0.
    assert _score([], ["a"]) == (1.0, 0.0)


def test_eval_runner_produces_results_for_minimal_fixture(tmp_path: Path) -> None:
    minimal = FIXTURES_ROOT / "minimal"
    assert minimal.exists(), "minimal fixture must ship under eval/fixtures/"
    work = tmp_path / "work"
    work.mkdir()
    result = run_eval(minimal.parent, work)
    assert isinstance(result, EvalResult)
    assert len(result.fixtures) >= 1
    minimal_result = next(
        f for f in result.fixtures if f.name in ("minimal", "minimal_app")
    )
    assert len(minimal_result.questions) == 5
    # Aggregate recall should be at least 0.5 on the minimal fixture - the
    # graph extractor must at least find symbol names for the bundled code.
    assert minimal_result.aggregate_recall >= 0.5


def test_render_report_emits_markdown_with_expected_sections(tmp_path: Path) -> None:
    result = run_eval(FIXTURES_ROOT, tmp_path)
    report = render_report(result)
    assert "# nexus-code-search eval report" in report
    assert "Aggregate recall:" in report
    assert "## Per-fixture" in report
    # Every fixture should appear as a section header.
    for fix in result.fixtures:
        assert f"## {fix.name}" in report


def test_eval_runner_runs_against_all_shipped_fixtures(tmp_path: Path) -> None:
    result = run_eval(FIXTURES_ROOT, tmp_path)
    # All shipped fixtures should be present and produce at least one question
    # each. The original four, the v2.3.0 (T030) language fixtures, the
    # v2.4.0 (DF-v23-4) batch (Ruby, PHP, C, C++), and the v3.0.0 (DF-v24-7)
    # mobile batch (Swift, Kotlin).
    names = {f.name for f in result.fixtures}
    assert names == {
        "minimal",
        "python_app",
        "fastapi_app",
        "ts_express",
        "go_app",
        "rust_app",
        "java_app",
        "csharp_app",
        "ruby_app",
        "php_app",
        "c_app",
        "cpp_app",
        "swift_app",
        "kotlin_app",
    }
    for fix in result.fixtures:
        assert fix.questions, f"{fix.name} produced no questions"


def test_every_fixture_clears_recall_gate(tmp_path: Path) -> None:
    # The v2.3.0 exit gate is >= 80% per-fixture recall (DF-002 / T030).
    result = run_eval(FIXTURES_ROOT, tmp_path)
    for fix in result.fixtures:
        assert fix.aggregate_recall >= 0.8, (
            f"{fix.name} recall {fix.aggregate_recall:.0%} is below the 80% gate"
        )
