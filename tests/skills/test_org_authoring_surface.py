"""Contract tests for the Phase 4 organization authoring surface."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "catalog" / "skills" / "workflow" / "org-standards-authoring"
SKILL = SKILL_DIR / "SKILL.md"
COMMAND = ROOT / "catalog" / "commands" / "org.md"
REFERENCE = SKILL_DIR / "references" / "enforcement-escalation.md"
EVALS = SKILL_DIR / "evals" / "trigger-cases.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _json(path: Path) -> dict:
    return json.loads(_read(path))


def test_authoring_skill_contains_required_contract_and_bundle_links() -> None:
    text = _read(SKILL)

    for phrase in (
        "connect our company standards",
        "organization coding standards",
        "internal conventions",
        "company style guide",
        "org knowledge",
        "team standards for the AI",
    ):
        assert phrase in text

    assert "SKIP:" in text
    assert "project-constitution" in text
    assert "agent-access-policy" in text
    assert "writing-editing" in text
    assert "technical-writer" in text
    assert "fewer than 200 lines" in text
    assert "configs/org-bundle.schema.json" in text
    assert "enforcement-escalation.md" in text

    headings = [
        "## When to Use This Skill",
        "## Instructions",
        "## Common Rationalizations",
        "## Verification",
        "## Related Skills",
    ]
    assert [text.index(heading) for heading in headings] == sorted(
        text.index(heading) for heading in headings
    )


def test_enforcement_reference_keeps_native_controls_platform_owned() -> None:
    text = _read(REFERENCE)

    assert "Managed policy `CLAUDE.md`" in text
    assert "Cursor" in text and "Team Rules" in text
    assert "GitHub Copilot" in text and "Organization custom instructions" in text
    assert "does not create vendor-managed policy" in text
    assert "org-knowledge-layer-research.md" in text


def test_trigger_evals_cover_positive_and_near_miss_cases() -> None:
    payload = _json(EVALS)
    cases = payload["cases"]
    positives = [case for case in cases if case["should_trigger"]]
    negatives = [case for case in cases if not case["should_trigger"]]

    assert payload["skill"] == "org-standards-authoring"
    assert len(positives) >= 3
    assert len(negatives) >= 3
    assert all(case.get("lexical") is True for case in cases)


def test_org_command_dispatches_each_scope_without_heavy_logic() -> None:
    text = _read(COMMAND)

    assert not text.startswith("---")
    assert "Recognized scopes are `connect`, `sync`, `status`, and `author`" in text
    assert "status  -> nexus-hub org status" in text
    assert "connect -> nexus-hub org connect <remaining arguments>" in text
    assert "sync    -> nexus-hub org sync" in text
    assert "author  -> org-standards-authoring" in text
    assert "[[org-standards-authoring]]" in text
    for platform_surface in (
        "Claude `commands/`",
        "Gemini `workflows/`",
        "Codex `prompts/`",
        "Cursor global and project",
        "Copilot `prompts/`",
        "Antigravity project `workflows/`",
    ):
        assert platform_surface in text


def test_org_authoring_registration_is_consistent_and_selectable() -> None:
    skills = _json(ROOT / "data" / "skills.json")
    marketplace = _json(ROOT / "data" / "marketplace.json")
    bundles = _json(ROOT / "data" / "bundles.json")
    index = _read(ROOT / "data" / "SKILL_INDEX.md")

    matches = [
        entry
        for entry in skills["skills"]
        if entry["name"] == "org-standards-authoring"
    ]
    assert len(matches) == 1
    assert matches[0]["security"] == {
        "structural": 100,
        "integrity": 100,
        "semantic": 95,
        "validated": True,
    }
    # The catalog TOTAL is derived, never frozen here. This test owns one
    # skill's registration; hardcoding the whole-catalog count made every
    # future skill addition break it (v3.17.5 Phase 2 took the catalog to 273
    # and broke exactly this line). The count invariant itself is owned by
    # tests/validators/test_registry_consistency.py, which derives it from
    # disk in both directions.
    total = len(skills["skills"])
    assert skills["statistics"]["total_skills"] == total
    assert skills["statistics"]["categories"]["workflow"] == sum(
        1 for entry in skills["skills"] if entry["category"] == "workflow"
    )
    n_categories = len(skills["statistics"]["categories"])
    assert f"**Total: {total} skills across {n_categories} categories**" in index
    assert "| org-standards-authoring | workflow |" in index
    assert f"{total} curated skills, 18 commands" in marketplace["plugin"]["description"]

    workflow = next(
        module for module in bundles["modules"] if module["id"] == "workflow"
    )
    assert "org-standards-authoring" in workflow["skills"]
