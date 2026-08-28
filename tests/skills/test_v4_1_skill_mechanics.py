"""Semantic contract tests for the v4.1.0 skill-mechanics adoption plan."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
SKILL_CREATE = (
    ROOT / "catalog" / "skills" / "workflow" / "skill-create" / "SKILL.md"
).read_text(encoding="utf-8")
SKILL_STOCKTAKE = (
    ROOT / "catalog" / "skills" / "workflow" / "skill-stocktake" / "SKILL.md"
).read_text(encoding="utf-8")


def test_agents_declares_skill_bodies_are_operational_runbooks():
    assert "Treat every SKILL.md body as an operational runbook" in AGENTS
    assert "supporting knowledge belongs in Tier-3 `references/`" in AGENTS


def test_skill_create_requires_runbook_instructions_and_tier_three_pedagogy():
    assert "Instructions as an operational runbook" in SKILL_CREATE
    assert "This domain needs a tutorial first" in SKILL_CREATE
    assert "supporting pedagogy in Tier-3 `references/`" in SKILL_CREATE


def test_stocktake_reports_expert_tutorials_as_advisory_backlog():
    assert "label it `runbook-backlog` in the report" in SKILL_STOCKTAKE
    assert "do not rewrite the expert skill during the stocktake" in SKILL_STOCKTAKE
    assert "do not turn this advisory label into a `make validate` failure" in SKILL_STOCKTAKE
