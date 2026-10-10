"""Phase 5 tests: token-savings benchmark + map-health lint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig, index_dir_for
from nexus_code_search.contextmap import generate_context_map
from nexus_code_search.contextmap import benchmark as bench
from nexus_code_search.contextmap.cli import main as map_cli_main
from nexus_code_search.contextmap.maphealth import lint_context_map
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.server import _handle_map_health


def _cfg() -> CodeSearchConfig:
    return CodeSearchConfig(hub_root=None)


def _index_dir(root: Path) -> Path:
    return index_dir_for(root, _cfg())


# --- Benchmark --------------------------------------------------------------


def test_benchmark_repo_positive_reduction() -> None:
    repo = bench.DEFAULT_CORPUS / "shop_api"
    result = bench.benchmark_repo(repo)
    assert result.reduction_ratio > 0.4  # a real repo's map beats manual exploration
    assert result.map_tokens > 0 and result.manual_cost > result.map_tokens
    assert result.routes >= 1 and result.models >= 1


def test_benchmark_does_not_write_nexus() -> None:
    repo = bench.DEFAULT_CORPUS / "shop_api"
    bench.benchmark_repo(repo)
    assert not (repo / ".nexus").exists()  # benchmarking is side-effect-free


def test_benchmark_corpus_meets_committed_baseline() -> None:
    report = bench.run_benchmark(bench.DEFAULT_CORPUS)
    assert len(report.repos) >= 3
    failures = bench.check_baseline(report, bench.load_baseline())
    assert failures == [], failures


def test_benchmark_gate_catches_regression() -> None:
    report = bench.run_benchmark(bench.DEFAULT_CORPUS)
    # An impossibly-high floor simulates the map losing its savings.
    inflated = {
        "repos": {r.label: {"min_reduction_ratio": 0.999} for r in report.repos},
        "min_aggregate_reduction": 0.999,
    }
    failures = bench.check_baseline(report, inflated)
    assert failures  # the gate must flag the regression


def test_benchmark_aggregate_ratio() -> None:
    report = bench.run_benchmark(bench.DEFAULT_CORPUS)
    assert report.aggregate_ratio > 0.4


def test_measured_baseline_floors_below_measured() -> None:
    report = bench.run_benchmark(bench.DEFAULT_CORPUS)
    baseline = bench.measured_baseline(report)
    for repo in report.repos:
        floor = baseline["repos"][repo.label]["min_reduction_ratio"]
        assert floor <= repo.reduction_ratio  # floor sits below the measured ratio
    assert baseline["min_aggregate_reduction"] <= report.aggregate_ratio


def test_render_report_contains_repos() -> None:
    report = bench.run_benchmark(bench.DEFAULT_CORPUS)
    text = bench.render_report(report)
    assert "token-savings benchmark" in text
    assert "shop_api" in text


def test_benchmark_cli_json(capsys: pytest.CaptureFixture) -> None:
    rc = bench.main(["--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["aggregate_reduction_ratio"] > 0.4
    assert len(payload["repos"]) >= 3


def test_benchmark_cli_check_passes() -> None:
    assert bench.main(["--check"]) == 0


def test_benchmark_cli_repo_mode(capsys: pytest.CaptureFixture) -> None:
    rc = bench.main(["--repo", str(bench.DEFAULT_CORPUS / "shop_api"), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["repos"][0]["label"] == "shop_api"


def test_benchmark_cli_missing_corpus(tmp_path: Path) -> None:
    assert bench.main(["--corpus", str(tmp_path / "nope")]) == 2


def test_benchmark_cli_update_writes_only_temporary_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    committed_path = bench.BASELINE_PATH
    committed_hash = hashlib.sha256(committed_path.read_bytes()).hexdigest()
    destination = tmp_path / "temporary baseline.json"
    report = bench.BenchmarkReport(
        repos=[
            bench.RepoBenchmark("first", 200, 1000, 0.8, 2, 1, 0, 0, 0),
            bench.RepoBenchmark("second", 300, 1000, 0.7, 3, 0, 1, 0, 0),
        ]
    )
    expected = {
        "_comment": bench.load_baseline(committed_path)["_comment"],
        "repos": {
            "first": {"min_reduction_ratio": 0.75},
            "second": {"min_reduction_ratio": 0.65},
        },
        "min_aggregate_reduction": 0.7,
    }
    monkeypatch.setattr(bench, "BASELINE_PATH", destination)
    monkeypatch.setattr(bench, "run_benchmark", lambda corpus: report)

    assert bench.main(["--update-baseline"]) == 0

    written = destination.read_text(encoding="utf-8")
    assert written == json.dumps(expected, indent=2) + "\n"
    assert json.loads(written) == expected
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"wrote baseline {destination}\n"
    assert hashlib.sha256(committed_path.read_bytes()).hexdigest() == committed_hash


def test_benchmark_cli_unwritable_destination_preserves_committed_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    committed_path = bench.BASELINE_PATH
    committed_bytes = committed_path.read_bytes()
    destination = tmp_path / "baseline directory"
    destination.mkdir()
    monkeypatch.setattr(bench, "BASELINE_PATH", destination)
    monkeypatch.setattr(bench, "run_benchmark", lambda corpus: bench.BenchmarkReport())

    with pytest.raises(OSError):
        bench.main(["--update-baseline"])

    assert list(destination.iterdir()) == []
    assert committed_path.read_bytes() == committed_bytes


def test_benchmark_load_rejects_malformed_baseline_without_writing(tmp_path: Path) -> None:
    committed_path = bench.BASELINE_PATH
    committed_bytes = committed_path.read_bytes()
    malformed = tmp_path / "malformed baseline.json"
    malformed.write_text("{not json}\n", encoding="utf-8")
    original = malformed.read_bytes()

    with pytest.raises(json.JSONDecodeError):
        bench.load_baseline(malformed)

    assert malformed.read_bytes() == original
    assert committed_path.read_bytes() == committed_bytes


# --- Map-health lint --------------------------------------------------------


@pytest.fixture
def mapped_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (tmp_path / "src" / "b.py").write_text("import a\n", encoding="utf-8")
    with ExtractionOrchestrator(tmp_path, _cfg(), _index_dir(tmp_path)) as orch:
        orch.run()
    generate_context_map(tmp_path, _index_dir(tmp_path))
    return tmp_path


def test_lint_healthy_map(mapped_repo: Path) -> None:
    report = lint_context_map(mapped_repo, _index_dir(mapped_repo))
    assert report.map_present and report.healthy


def test_lint_detects_orphan(mapped_repo: Path) -> None:
    (mapped_repo / ".nexus" / "context" / "orphan.md").write_text(
        "# Orphan\n\nBack to the [context map](../CONTEXT-MAP.md).\n", encoding="utf-8"
    )
    report = lint_context_map(mapped_repo, _index_dir(mapped_repo))
    assert "orphan.md" in report.orphans
    assert not report.healthy


def test_lint_detects_missing_backlink(mapped_repo: Path) -> None:
    (mapped_repo / ".nexus" / "context" / "src.md").write_text(
        "# Module: src\n\nno backlink here\n", encoding="utf-8"
    )
    report = lint_context_map(mapped_repo, _index_dir(mapped_repo))
    assert "src.md" in report.missing_backlinks


def test_lint_detects_staleness(mapped_repo: Path) -> None:
    assert lint_context_map(mapped_repo, _index_dir(mapped_repo)).healthy
    (mapped_repo / "src" / "a.py").write_text(
        "def f():\n    return 999\n", encoding="utf-8"
    )
    with ExtractionOrchestrator(mapped_repo, _cfg(), _index_dir(mapped_repo)) as orch:
        orch.run()
    report = lint_context_map(mapped_repo, _index_dir(mapped_repo))
    assert report.stale and not report.healthy


def test_lint_no_map_present(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    with ExtractionOrchestrator(tmp_path, _cfg(), _index_dir(tmp_path)) as orch:
        orch.run()
    report = lint_context_map(tmp_path, _index_dir(tmp_path))
    assert not report.map_present
    assert not report.healthy


def test_cli_lint_healthy(mapped_repo: Path) -> None:
    assert map_cli_main([str(mapped_repo), "--lint"]) == 0


def test_cli_lint_unhealthy_exit_1(mapped_repo: Path) -> None:
    (mapped_repo / ".nexus" / "context" / "orphan.md").write_text(
        "# Orphan\n", encoding="utf-8"
    )
    assert map_cli_main([str(mapped_repo), "--lint"]) == 1


def test_mcp_map_health_handler(mapped_repo: Path) -> None:
    res = _handle_map_health({"root": str(mapped_repo)}, _cfg())
    payload = json.loads(res[0].text)
    assert payload["map_present"] is True
    assert payload["healthy"] is True
