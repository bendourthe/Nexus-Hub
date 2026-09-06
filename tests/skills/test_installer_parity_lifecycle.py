"""Contract tests for the standing multi-installer parity gate."""

from __future__ import annotations

import re
from pathlib import Path

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py for why greping the
# YAML would be both wrong and dangerous to "fix".
from tests.validators._ci_reachability import assert_wired_into_ci

ROOT = Path(__file__).resolve().parents[2]
UPDATE = ROOT / "catalog" / "commands" / "update.md"
PLAN = ROOT / "catalog" / "skills" / "workflow" / "implementation-plan" / "SKILL.md"
# v4.0.0 Phase 3: the mandatory-final-phase TEMPLATE moved out of SKILL.md into a
# Tier 3 reference when the body crossed the 500-line soft cap. The parity language
# rides that template, so the planning contract is now the two files together.
# Reading only SKILL.md would report the gate as missing when it merely moved.
PLAN_FINAL_PHASE = (
    ROOT / "catalog" / "skills" / "workflow" / "implementation-plan"
    / "references" / "mandatory-final-phase.md"
)
IMPLEMENT = ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "SKILL.md"
RUNBOOK = ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "references" / "implement-phase-runbook.md"
MAKEFILE = ROOT / "Makefile"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_release_entry_points_declare_a_hard_installer_parity_gate() -> None:
    update = _read(UPDATE)
    runbook = _read(RUNBOOK)
    for label, body in (("update", update), ("implement runbook", runbook)):
        assert "installer parity" in body.lower(), label
        assert "HARD gate" in body, label
        assert "[[platform-contract-verification]]" in body, label


def test_future_and_historical_plans_self_gate_on_multiple_installers() -> None:
    plan = _read(PLAN) + _read(PLAN_FINAL_PHASE)
    implement = _read(IMPLEMENT)
    for label, body in (("implementation plan", plan), ("implement phase", implement)):
        assert "more than one installer" in body, label
        assert "silent no-op" in body, label


def test_planning_contract_requires_real_os_smoke_with_shared_postconditions() -> None:
    plan = _read(PLAN) + _read(PLAN_FINAL_PHASE)
    assert "execute the real installers on their target operating systems" in plan
    assert "identical postconditions" in plan


def test_plan_and_implementation_terminal_contracts_require_the_same_deep_pass_evidence() -> None:
    plan = _read(PLAN_FINAL_PHASE)
    implement = _read(IMPLEMENT) + _read(RUNBOOK)
    for label, body in (("implementation plan", plan), ("implement phase", implement)):
        assert "[[functional-verification]]" in body, label
        assert "references/deep-pass.md" in body, label
        assert "<version_dir>/development/last-phase-evidence.md" in body, label
        assert "`## Tier 3 deep pass`" in body, label


def test_parity_checker_is_wired_into_local_and_remote_validation() -> None:
    assert "python scripts/check_installer_parity.py" in _read(MAKEFILE), "Makefile"
    assert_wired_into_ci("check_installer_parity.py")


def test_ci_uses_one_shared_smoke_assertion_script() -> None:
    ci = _read(CI)
    assert "installer-smoke:" in ci
    assert ci.count("python scripts/check_installer_smoke.py") == 1
    assert ci.count("python scripts\\check_installer_smoke.py") == 1


def test_windows_installer_smoke_does_not_assign_reserved_home_variable() -> None:
    ci = _read(CI)
    assert re.search(r"(?im)^\s*\$home\s*=", ci) is None
    assert "$smokeHome = Join-Path $smokeRoot 'home'" in ci
