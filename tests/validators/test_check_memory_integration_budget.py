"""Tests for scripts/check_memory_integration_budget.py (v3.19.1 Phase 2).

The guard exists so the always-loaded memory integration prose cannot grow
unmeasured. A budget gate proven only on the happy path is worthless, so these
tests assert failure in both directions: an under-budget file passes, an
over-budget file exits non-zero, and a missing file is MISS rather than OK.

They also pin the two wiring contracts: ``make validate`` invokes the guard,
and the subagent write-exclusion clause is present in multi-agent-coordinator.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py for why greping the
# YAML would be both wrong and dangerous to "fix".
from tests.validators._ci_reachability import assert_wired_into_ci

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_memory_integration_budget.py"
MAKEFILE = REPO_ROOT / "Makefile"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
COORDINATOR = (
    REPO_ROOT
    / "catalog"
    / "skills"
    / "orchestration"
    / "multi-agent-coordinator"
    / "SKILL.md"
)
CONTRACT = REPO_ROOT / "docs" / "policy" / "memory-substrate-contract.md"
EXCLUSION_LINE = (
    "Do not write to persistent agent memory. You are a spawned subagent; "
    "only the parent session may record memory."
)


def run(*extra: str, root: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT)]
    if root is not None:
        cmd.extend(["--root", str(root)])
    cmd.extend(extra)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def test_shipped_prose_is_under_budget() -> None:
    proc = run()
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_under_budget_fixture_passes(tmp_path: Path) -> None:
    prose = tmp_path / "small.md"
    prose.write_text("Read memory at startup. Record lasting facts.\n", encoding="utf-8")

    proc = run("--text", str(prose), "--budget", "50")
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_over_budget_fixture_fails(tmp_path: Path) -> None:
    prose = tmp_path / "huge.md"
    prose.write_text("word " * 200, encoding="utf-8")

    proc = run("--text", str(prose), "--budget", "20")
    assert proc.returncode == 1
    assert "OVER" in proc.stderr
    assert "20" in proc.stderr


def test_missing_file_fails(tmp_path: Path) -> None:
    proc = run("--root", str(tmp_path), "--path", "no-such.md", "--budget", "50")
    assert proc.returncode == 1
    assert "MISS" in proc.stderr


def test_invalid_budget_fails(tmp_path: Path) -> None:
    prose = tmp_path / "ok.md"
    prose.write_text("ok\n", encoding="utf-8")
    proc = run("--text", str(prose), "--budget", "0")
    assert proc.returncode == 1
    assert "BAD" in proc.stderr


def test_make_validate_invokes_the_guard() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert "scripts/check_memory_integration_budget.py" in makefile
    assert_wired_into_ci("check_memory_integration_budget.py")


def test_subagent_exclusion_clause_is_in_the_coordinator() -> None:
    body = COORDINATOR.read_text(encoding="utf-8")
    assert EXCLUSION_LINE in body
    contract = CONTRACT.read_text(encoding="utf-8")
    assert EXCLUSION_LINE in contract


def test_contract_declares_the_500_token_budget() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert "500 tokens" in text
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import check_memory_integration_budget as guard

    assert guard.DEFAULT_BUDGET == 500
    assert guard.DEFAULT_PATH == "docs/policy/memory-integration-prose.md"
