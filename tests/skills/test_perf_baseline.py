"""
Tests for the performance-regression-gate skill's bundled scripts/perf_baseline.py.

Run from the repo root:
    python -m pytest tests/skills/test_perf_baseline.py -v

Pure Python (no bash), so these run on every platform including the Windows dev
host. They subprocess the bundled script against throwaway metrics/baseline files
and assert on exit codes and output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "tests-generation"
    / "performance-regression-gate"
    / "scripts"
    / "perf_baseline.py"
)


def _write(path: Path, obj: object) -> str:
    path.write_text(json.dumps(obj), encoding="utf-8")
    return str(path)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_script_exists() -> None:
    assert _SCRIPT.is_file(), f"bundled script missing at {_SCRIPT}"


def test_record_then_check_same_metrics_passes(tmp_path: Path) -> None:
    metrics = _write(tmp_path / "m.json", {"latency_ms": 100, "throughput_rps": 2000})
    baseline = str(tmp_path / "base.json")

    rec = _run(
        "--record",
        baseline,
        "--metrics",
        metrics,
        "--higher-is-better",
        "throughput_rps",
    )
    assert rec.returncode == 0, rec.stderr

    chk = _run("--check", baseline, "--metrics", metrics)
    assert chk.returncode == 0, chk.stderr
    assert "PASS" in chk.stdout


def test_lower_is_better_regression_fails(tmp_path: Path) -> None:
    base_metrics = _write(tmp_path / "b.json", {"latency_ms": 100})
    baseline = str(tmp_path / "base.json")
    _run("--record", baseline, "--metrics", base_metrics, "--threshold", "0.10")

    worse = _write(tmp_path / "w.json", {"latency_ms": 130})  # +30% > 10%
    chk = _run("--check", baseline, "--metrics", worse)
    assert chk.returncode == 1
    assert "REGRESSED" in chk.stdout
    assert "FAIL" in chk.stderr


def test_lower_is_better_within_threshold_passes(tmp_path: Path) -> None:
    base_metrics = _write(tmp_path / "b.json", {"latency_ms": 100})
    baseline = str(tmp_path / "base.json")
    _run("--record", baseline, "--metrics", base_metrics, "--threshold", "0.10")

    within = _write(tmp_path / "w.json", {"latency_ms": 109})  # +9% < 10%
    chk = _run("--check", baseline, "--metrics", within)
    assert chk.returncode == 0
    assert "PASS" in chk.stdout


def test_higher_is_better_drop_fails(tmp_path: Path) -> None:
    base_metrics = _write(tmp_path / "b.json", {"throughput_rps": 2000})
    baseline = str(tmp_path / "base.json")
    _run(
        "--record",
        baseline,
        "--metrics",
        base_metrics,
        "--threshold",
        "0.10",
        "--higher-is-better",
        "throughput_rps",
    )

    dropped = _write(
        tmp_path / "w.json", {"throughput_rps": 1500}
    )  # -25% for a higher-is-better metric
    chk = _run("--check", baseline, "--metrics", dropped)
    assert chk.returncode == 1
    assert "REGRESSED" in chk.stdout


def test_higher_is_better_gain_passes(tmp_path: Path) -> None:
    base_metrics = _write(tmp_path / "b.json", {"throughput_rps": 2000})
    baseline = str(tmp_path / "base.json")
    _run(
        "--record",
        baseline,
        "--metrics",
        base_metrics,
        "--higher-is-better",
        "throughput_rps",
    )

    gained = _write(tmp_path / "w.json", {"throughput_rps": 2500})
    chk = _run("--check", baseline, "--metrics", gained)
    assert chk.returncode == 0


def test_new_and_missing_metrics_do_not_fail(tmp_path: Path) -> None:
    base_metrics = _write(tmp_path / "b.json", {"latency_ms": 100, "retired_ms": 50})
    baseline = str(tmp_path / "base.json")
    _run("--record", baseline, "--metrics", base_metrics)

    # retired_ms missing (MISSING), added_ms new (NEW); latency within threshold.
    current = _write(tmp_path / "c.json", {"latency_ms": 101, "added_ms": 5})
    chk = _run("--check", baseline, "--metrics", current)
    assert chk.returncode == 0
    assert "MISSING" in chk.stdout
    assert "NEW" in chk.stdout


def test_bad_metrics_input_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    baseline = _write(tmp_path / "base.json", {"metrics": {"latency_ms": 100}})
    chk = _run("--check", baseline, "--metrics", str(bad))
    assert chk.returncode == 2
