"""Repo-level integration tests for the skill-security scanner CLI.

These exercise the actual ``scripts/scan_skill_security.py`` launcher end to
end as a subprocess (the path-resolution + package-import + gate logic users
run), and dogfood the catalog gate: the scanner over ``catalog/skills`` and
``catalog/mcp-configs`` must produce no HIGH/CRITICAL finding.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "scan_skill_security.py"
FIXTURES = REPO_ROOT / "extensions" / "nexus-skill-scanner" / "tests" / "fixtures"


def run_scanner(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LAUNCHER), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_launcher_exists() -> None:
    assert LAUNCHER.is_file()


def test_malicious_fixture_fails_high_gate() -> None:
    result = run_scanner(str(FIXTURES / "malicious-skill"), "--fail-on", "high", "--format", "json")
    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert payload["band"] in ("high", "critical")


def test_clean_fixture_passes_high_gate() -> None:
    result = run_scanner(str(FIXTURES / "clean-skill"), "--fail-on", "high", "--format", "json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["band"] == "low"
    assert payload["findings"] == []


def test_catalog_gate_is_clean() -> None:
    # Dogfood: the distributed catalog must have no HIGH/CRITICAL finding.
    result = run_scanner(
        "catalog/skills", "catalog/mcp-configs", "--fail-on", "high", "--format", "json"
    )
    assert result.returncode == 0, (
        "catalog gate produced a HIGH/CRITICAL finding:\n" + result.stderr
    )
    payload = json.loads(result.stdout)
    high = [f for f in payload["findings"] if f["severity"] in ("high", "critical")]
    assert high == [], f"unexpected HIGH/CRITICAL findings: {high}"


def test_sarif_output_is_valid() -> None:
    result = run_scanner(str(FIXTURES / "malicious-skill"), "--format", "sarif")
    assert result.returncode == 0
    sarif = json.loads(result.stdout)
    assert sarif["version"] == "2.1.0"
    assert sarif["runs"][0]["results"]


def test_missing_target_exits_2() -> None:
    result = run_scanner("definitely-not-a-real-path-xyz", "--format", "json")
    assert result.returncode == 2
