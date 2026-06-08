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


# A synthetic high-confidence Bearer token (>= 50 token chars), assembled at
# runtime so this test source carries no credential literal. The secret
# analyzer flags it HIGH even inside a Markdown fence.
_BEARER = "Bearer " + "A" * 64

_SECURITY_BODY = f"""---
name: jwt-attack-methodology
description: Authorized JWT/OAuth attack methodology for defensive review. SKIP unauthorized use.
summary_l0: "Attacker-perspective JWT/OAuth methodology for authorized review"
overview_l1: "Shows fenced example tokens for recognition only."
---

# JWT Attack Methodology

A forged Authorization header to recognize:

```text
{_BEARER}
```
"""


def _make_skill(root: Path, category: str) -> Path:
    skill = root / "catalog" / "skills" / category / "jwt-attack-methodology"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(_SECURITY_BODY, encoding="utf-8")
    return skill


def test_allowlist_passes_high_gate_for_security_skill(tmp_path: Path) -> None:
    # Authorized payload in catalog/skills/security/ is capped to MEDIUM, so the
    # HIGH gate passes (exit 0) even though the secret is still detected.
    skill = _make_skill(tmp_path, "security")
    result = run_scanner(
        str(skill), "--repo-root", str(tmp_path), "--fail-on", "high", "--format", "json"
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    severities = [f["severity"] for f in payload["findings"]]
    assert severities, "the fenced token should still be detected"
    assert "high" not in severities and "critical" not in severities


def test_allowlist_does_not_apply_to_non_security_skill(tmp_path: Path) -> None:
    # The SAME payload in a non-security category is not allowlisted: the secret
    # stays HIGH and the gate fails (exit 1).
    skill = _make_skill(tmp_path, "developer-experience")
    result = run_scanner(
        str(skill), "--repo-root", str(tmp_path), "--fail-on", "high", "--format", "json"
    )
    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert any(f["severity"] == "high" for f in payload["findings"])


def test_sarif_output_is_valid() -> None:
    result = run_scanner(str(FIXTURES / "malicious-skill"), "--format", "sarif")
    assert result.returncode == 0
    sarif = json.loads(result.stdout)
    assert sarif["version"] == "2.1.0"
    assert sarif["runs"][0]["results"]


def test_missing_target_exits_2() -> None:
    result = run_scanner("definitely-not-a-real-path-xyz", "--format", "json")
    assert result.returncode == 2
