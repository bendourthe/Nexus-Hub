"""Contract tests for the standing multi-installer parity gate."""

from __future__ import annotations

import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.ci import profiles, verify_scenarios

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

    assert "real-installer proof for affected delivery boundaries" in plan

    assert "Required broad target-OS coverage runs in the integration matrix" in plan

    assert "recorded acceptance criterion requires that local proof" in plan

    assert "identical postconditions" in plan


def test_plan_and_implementation_terminal_contracts_require_the_same_deep_pass_evidence() -> None:
    plan = _read(PLAN_FINAL_PHASE)
    implement = _read(IMPLEMENT) + _read(RUNBOOK)
    for label, body in (("implementation plan", plan), ("implement phase", implement)):
        assert "[[functional-verification]]" in body, label
        assert "references/deep-pass.md" in body, label
        assert "<version_dir>/development/<version>-last-phase-evidence.md" in body, label
        assert "`## Tier 3 deep pass`" in body, label


def test_parity_checker_is_wired_into_local_and_remote_validation() -> None:
    assert "python scripts/check_installer_parity.py" in _read(MAKEFILE), "Makefile"
    assert_wired_into_ci("check_installer_parity.py")


@pytest.mark.parametrize("host", ["nt", "posix"])
def test_ci_uses_one_shared_smoke_assertion_script(tmp_path, monkeypatch, host) -> None:
    job = yaml.safe_load(_read(CI))["jobs"]["installer-smoke"]
    assert set(job["strategy"]["matrix"]["os"]) == {"ubuntu-latest", "macos-latest", "windows-latest"}
    commands = [step["run"] for step in job["steps"] if "run" in step]
    assert any("scripts/ci/run.py --profile platform --only workspace-smoke" in command for command in commands)
    groups = [group for group in profiles.PROFILES["platform"] if group.name == "workspace-smoke"]
    assert len(groups) == 1 and len(groups[0].commands) == 1
    assert list(groups[0].commands[0].argv[1:]) == ["scripts/ci/verify_scenarios.py", "workspace"]
    calls = []
    monkeypatch.setattr(verify_scenarios, "os", SimpleNamespace(name=host))
    monkeypatch.setattr(verify_scenarios, "run", lambda argv, **kwargs: calls.append((argv, kwargs)))
    env = {"HOME": str(tmp_path / "private-home")}
    verify_scenarios.workspace(ROOT, tmp_path, env)
    expected = ROOT / "scripts" / ("installer.ps1" if host == "nt" else "installer.sh")
    installer = calls[1][0]
    assert str(expected) in installer
    assert installer[0] == ("powershell" if host == "nt" else "bash")
    assert str(tmp_path / "workspace") in installer
    checkers = [(argv, kwargs) for argv, kwargs in calls if str(ROOT / "scripts/check_installer_smoke.py") in argv]
    assert len(checkers) == 1
    argv, kwargs = checkers[0]
    assert argv[2:] == ["--home", env["HOME"], "--workspace", str(tmp_path / "workspace")]
    assert kwargs["env"] is env


def test_windows_installer_smoke_does_not_assign_reserved_home_variable(tmp_path) -> None:
    ci = _read(CI)
    assert re.search(r"(?im)^\s*\$home\s*=", ci) is None
    original = {key: os.environ.get(key) for key in ("HOME", "USERPROFILE")}
    env = verify_scenarios.isolated_environment(tmp_path)
    assert env["HOME"] == env["USERPROFILE"] == str(tmp_path / "home")
    assert Path(env["HOME"]).is_dir()
    assert {key: os.environ.get(key) for key in original} == original
