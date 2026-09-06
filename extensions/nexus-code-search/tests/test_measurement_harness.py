"""Deterministic cost and retrieval-quality benchmark contracts."""

from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest

EXTENSION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXTENSION_ROOT))

from benchmarks.harness import (
    compare_quality,
    load_goldset,
    run_benchmark,
    score_ranked,
    write_reports,
)

GOLDSET = EXTENSION_ROOT / "benchmarks" / "goldset.json"


def test_ranked_scoring_handles_perfect_empty_and_wrong_results() -> None:
    perfect = score_ranked(["helper", "run_task"], ["helper", "run_task"])
    assert perfect.precision == 1.0
    assert perfect.recall == 1.0
    assert perfect.reciprocal_rank == 1.0

    empty = score_ranked([], [])
    assert empty.precision == 1.0
    assert empty.recall == 1.0
    assert empty.reciprocal_rank == 1.0

    wrong = score_ranked(["helper"], ["unrelated", "noise"])
    assert wrong.precision == 0.0
    assert wrong.recall == 0.0
    assert wrong.reciprocal_rank == 0.0


def test_goldset_validates_and_covers_required_task_shapes() -> None:
    goldset = load_goldset(GOLDSET)
    assert goldset.version == 1
    assert {task.shape for task in goldset.tasks} == {
        "locate_symbol",
        "find_callers",
        "identify_unused",
        "trace_impact",
    }
    assert all(task.expected for task in goldset.tasks)


def test_goldset_rejects_unknown_tools(tmp_path: Path) -> None:
    (tmp_path / "corpus").mkdir()
    invalid = tmp_path / "invalid.json"
    invalid.write_text(
        json.dumps(
            {
                "version": 1,
                "corpus": "corpus",
                "tasks": [
                    {
                        "id": "bad",
                        "shape": "locate_symbol",
                        "tool": "fetch_the_internet",
                        "profile": "minimal",
                        "arguments": {"query": "helper"},
                        "expected": ["helper"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported tool"):
        load_goldset(invalid)


def test_harness_runs_offline_without_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in list(__import__("os").environ):
        monkeypatch.delenv(key, raising=False)

    def reject_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("benchmark attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", reject_connection)
    report = run_benchmark(GOLDSET, tmp_path / "work")

    assert len(report.tasks) == 4
    assert report.quality.recall == 1.0
    assert report.quality.precision == 1.0
    assert report.quality.mean_reciprocal_rank == 1.0
    assert report.cost.byte_savings == (
        report.cost.all_tools_json_bytes - report.cost.profiled_compact_bytes
    )
    assert report.cost.byte_savings_pct == pytest.approx(
        report.cost.byte_savings / report.cost.all_tools_json_bytes * 100.0
    )


def test_reports_are_human_and_machine_readable(tmp_path: Path) -> None:
    report = run_benchmark(GOLDSET, tmp_path / "work")
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"
    write_reports(report, json_path=json_path, markdown_path=markdown_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert payload["quality"]["recall"] == 1.0
    assert payload["cost"]["byte_savings"] == (
        payload["cost"]["all_tools_json_bytes"]
        - payload["cost"]["profiled_compact_bytes"]
    )
    assert "# nexus-code-search deterministic benchmark" in markdown
    assert "| Task | Tool | Precision | Recall | MRR |" in markdown
    assert "| All tools + JSON |" in markdown


def test_repeated_runs_share_a_work_root_without_corpus_collision(tmp_path: Path) -> None:
    work = tmp_path / "work"
    first = run_benchmark(GOLDSET, work)
    second = run_benchmark(GOLDSET, work)
    assert first.quality == second.quality


def test_quality_regression_mode_honors_tolerance(tmp_path: Path) -> None:
    report = run_benchmark(GOLDSET, tmp_path / "work")
    baseline = {
        "precision": 1.0,
        "recall": 1.0,
        "mean_reciprocal_rank": 1.0,
    }
    assert compare_quality(report, baseline, tolerance=0.0) == []

    degraded = {
        "precision": 0.8,
        "recall": 0.75,
        "mean_reciprocal_rank": 0.5,
    }
    failures = compare_quality(degraded, baseline, tolerance=0.1)
    assert len(failures) == 3
    assert all("dropped" in failure for failure in failures)


def test_harness_has_no_network_or_credential_surface() -> None:
    source = (EXTENSION_ROOT / "benchmarks" / "harness.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "import requests",
        "import httpx",
        "import urllib",
        "from urllib",
        "api_key",
        "credential",
        "os.environ",
        "getenv(",
    )
    assert not any(token in source.lower() for token in forbidden)


def test_installers_exclude_benchmark_artifacts() -> None:
    bash = (EXTENSION_ROOT.parents[1] / "scripts" / "installer.sh").read_text(
        encoding="utf-8"
    )
    powershell = (
        EXTENSION_ROOT.parents[1] / "scripts" / "installer.ps1"
    ).read_text(encoding="utf-8")
    assert 'rm -rf "$code_search_dest/benchmarks"' in bash
    assert 'Join-Path $codeSearchDest "benchmarks"' in powershell
