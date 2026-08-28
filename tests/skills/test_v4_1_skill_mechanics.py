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
TYPED_BOUNDARY = (
    ROOT
    / "catalog"
    / "skills"
    / "language-specialists"
    / "typed-boundary-hygiene"
    / "SKILL.md"
).read_text(encoding="utf-8")
TYPESCRIPT_EXPERT = (
    ROOT / "catalog" / "skills" / "language-specialists" / "typescript-expert" / "SKILL.md"
).read_text(encoding="utf-8")
JAVASCRIPT_CLEANUP = (
    ROOT / "catalog" / "skills" / "code-cleanup" / "javascript-cleanup" / "SKILL.md"
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


def test_typed_boundary_skill_declares_single_rule_owner_per_concern():
    assert "## Rule Ownership" in TYPED_BOUNDARY
    assert "Function-contract `unknown` / `object` / unsafe dictionaries" in TYPED_BOUNDARY
    assert "Type-system design, generics, and discriminated unions" in TYPED_BOUNDARY
    assert "Boundary parsing of unknown I/O with Zod or `safeParse`" in TYPED_BOUNDARY


def test_typed_boundary_skill_covers_the_required_low_evidence_patterns():
    for required in (
        "as unknown as",
        "conditional empty object spreads",
        "`vi.mock` or `jest.mock`",
        "`Reflect.get` or `Reflect.apply`",
        "Record<string, unknown>",
        "widen-then-assert",
        "SAFETY:",
    ):
        assert required in TYPED_BOUNDARY


def test_non_owners_hand_contract_hygiene_to_typed_boundary_skill():
    assert "replace with `unknown` and narrow" not in TYPESCRIPT_EXPERT
    assert "hand contract cleanup to [[typed-boundary-hygiene]]" in TYPESCRIPT_EXPERT
    assert "[[typed-boundary-hygiene]] -- owns low-evidence" in JAVASCRIPT_CLEANUP
