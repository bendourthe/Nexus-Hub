"""Guard that the three spec artifacts stay in agreement (v3.15.14 MT-1).

The v3.15.14 defect these tests exist to prevent was a silent disagreement
between three prose files that no validator could see:

* ``catalog/templates/spec-template.md`` had no section expressing a scope
  boundary, while
* ``catalog/templates/spec-quality-checklist.md`` asked whether "Scope is
  clearly bounded" and ``catalog/agents/scope-guardian-reviewer.md`` flagged a
  missing out-of-scope section, so every reviewer run on a template-conformant
  spec raised a finding the template itself caused; and
* ``spec-driven-development``'s Verification checklist validated a *rival*
  inline template's areas rather than the canonical template's sections, so
  "spec complete" was checked against an artifact the workflow never produces.

Prose artifacts have no compiler. A schema reference to a missing column
errors; a checklist item referencing a missing heading just fails forever in
silence. These assertions are that missing compiler.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE = _ROOT / "catalog" / "templates" / "spec-template.md"
_CHECKLIST = _ROOT / "catalog" / "templates" / "spec-quality-checklist.md"
_SKILL = (
    _ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "spec-driven-development"
    / "SKILL.md"
)
_REVIEWER = _ROOT / "catalog" / "agents" / "scope-guardian-reviewer.md"

# The canonical template's mandatory sections, in document order. Adding a
# mandatory section to the template means adding it here AND naming it in the
# skill's Verification checklist; that coupling is the point of this module.
MANDATORY_SECTIONS = (
    "Problem Statement",
    "User Scenarios & Testing",
    "Requirements",
    "Success Criteria",
    "Non-Goals",
)

# Conditional sections: present in the template, required only in some specs.
CONDITIONAL_SECTIONS = ("Assumptions", "Invariants")


def _read(path: Path) -> str:
    assert path.is_file(), f"expected artifact is missing: {path}"
    return path.read_text(encoding="utf-8")


def _verification_block(skill_text: str) -> str:
    """Return the skill's ``## Verification`` section body."""
    marker = "\n## Verification\n"
    start = skill_text.find(marker)
    assert start != -1, "spec-driven-development SKILL.md has no ## Verification section"
    rest = skill_text[start + len(marker) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


@pytest.mark.parametrize("section", MANDATORY_SECTIONS + CONDITIONAL_SECTIONS)
def test_template_carries_every_declared_section(section: str) -> None:
    """Every section this module declares must exist as a heading in the template."""
    assert f"\n## {section}" in _read(_TEMPLATE), (
        f"spec-template.md is missing the '## {section}' heading. Either restore it "
        f"or remove it from this module's section lists."
    )


@pytest.mark.parametrize("section", MANDATORY_SECTIONS)
def test_mandatory_sections_are_marked_mandatory(section: str) -> None:
    """A mandatory section must be labelled as such at its heading."""
    assert f"## {section} *(mandatory)*" in _read(_TEMPLATE), (
        f"'## {section}' is declared mandatory here but is not marked "
        f"*(mandatory)* in spec-template.md."
    )


@pytest.mark.parametrize("section", MANDATORY_SECTIONS)
def test_verification_checklist_names_every_mandatory_section(section: str) -> None:
    """The completion gate must validate the canonical template, not a rival one.

    This is the assertion that would have caught the original defect: the
    Verification list named "Objective, Commands, Structure, Style, Testing,
    Boundaries", which are an inline template's areas, not these.
    """
    assert section in _verification_block(_read(_SKILL)), (
        f"spec-driven-development's Verification checklist does not mention "
        f"'{section}', so the completion gate no longer validates the canonical "
        f"template's sections."
    )


def test_skill_names_exactly_one_canonical_template() -> None:
    """No second spec skeleton may reappear in the skill body."""
    skill = _read(_SKILL)
    assert "catalog/templates/spec-template.md" in skill
    assert "single canonical spec skeleton" in skill, (
        "spec-driven-development must declare spec-template.md the single "
        "canonical skeleton unambiguously."
    )
    # The rival inline template was headed by these two adjacent sections.
    assert "\n## Tech Stack\n" not in skill, (
        "A rival inline spec template appears to have returned to the skill body."
    )


def test_checklist_binds_scope_bounding_to_non_goals() -> None:
    """The checklist's scope item must be satisfiable from the template alone.

    Asserts the *binding*, not the mere presence of the words "Non-Goals"
    somewhere in the file. An earlier draft of this test checked presence and
    consequently passed against a mutation that unbound the item, because the
    heading is also named in the Content Quality section. Assert relationships,
    not tokens.
    """
    checklist = _read(_CHECKLIST)
    scope_lines = [ln for ln in checklist.splitlines() if "Scope is clearly bounded" in ln]
    assert scope_lines, "spec-quality-checklist.md lost its 'Scope is clearly bounded' item"
    assert any("Non-Goals" in ln for ln in scope_lines), (
        "The 'Scope is clearly bounded' item no longer names the template's "
        "## Non-Goals section on its own line, so it is once again an assertion "
        "with no artifact behind it. This is the exact v3.15.14 defect."
    )
    assert any(
        "Non-Goals" in ln and "reason" in ln.lower()
        for ln in checklist.splitlines()
        if ln.lstrip().startswith("- [ ]")
    ), (
        "spec-quality-checklist.md no longer has a checklist item requiring a "
        "reason per Non-Goals entry, which the template mandates."
    )


def test_reviewer_agrees_with_the_template_heading() -> None:
    """scope-guardian-reviewer must not assert a heading no artifact produces."""
    assert "Non-Goals" in _read(_REVIEWER), (
        "scope-guardian-reviewer no longer names the template's ## Non-Goals "
        "heading, so its missing-cut-line finding is unsatisfiable again."
    )


def test_non_goals_requires_a_reason_per_entry() -> None:
    """The reason-per-entry discipline is what makes a Non-Goal reviewable."""
    template = _read(_TEMPLATE)
    non_goals = template[template.index("\n## Non-Goals") :]
    non_goals = non_goals[: non_goals.index("\n## Invariants")]
    assert "MUST carry a reason" in non_goals, (
        "spec-template.md's Non-Goals section no longer requires a reason per "
        "entry; spec-quality-checklist.md still checks for one."
    )
