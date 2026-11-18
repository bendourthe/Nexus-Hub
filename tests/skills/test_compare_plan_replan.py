"""/compare and /plan call the shared minor re-plan analysis after resolving the target version."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "catalog/skills/workflow/plan-queue-assessment/SKILL.md"
SCRIPT = ROOT / "catalog/skills/workflow/plan-queue-assessment/scripts/replan_minor.py"

CALLERS = {
    "compare command": ("catalog/commands/compare.md", "Step 6.5b"),
    "plan command": ("catalog/commands/plan.md", "Step 4.7"),
    "comparison skill": ("catalog/skills/workflow/cross-project-comparison/SKILL.md", "Step 6.5b"),
    "plan skill": ("catalog/skills/workflow/implementation-plan/SKILL.md", "Step 4.7"),
}


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shared_script_exists() -> None:
    assert SCRIPT.is_file()


@pytest.mark.parametrize("name", sorted(CALLERS))
def test_surface_references_replan_step_and_owner(name: str) -> None:
    rel, step = CALLERS[name]
    text = read(rel)
    assert step in text
    assert "[[plan-queue-assessment]]" in text
    assert "replan_minor.py" in text
    assert "approval" in text or "approves" in text


def test_owner_defines_plan_time_procedure() -> None:
    text = OWNER.read_text(encoding="utf-8")
    assert "### Plan-time use by `/compare` and `/plan`" in text
    section = text.split("### Plan-time use by `/compare` and `/plan`", 1)[1].split("\n## ", 1)[0]
    assert "never edit the prose of an existing member plan" in section
    assert "scripts/replan_minor.py" in section


@pytest.mark.parametrize("rel", ["catalog/commands/compare.md", "catalog/commands/plan.md"])
def test_command_states_guarantee_without_restating_procedure(rel: str) -> None:
    text = read(rel)
    assert "## Minor re-plan analysis (guarantee)" in text
    assert "never edited" in text or "no existing plan is edited" in text
