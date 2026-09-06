"""Contracts for functional-verification ownership links and HTML rule adoption."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

VERIFICATION_BEFORE_COMPLETION = (
    ROOT
    / "catalog"
    / "skills"
    / "workflow"
    / "verification-before-completion"
    / "SKILL.md"
)

RECIPROCAL_SKILLS = (
    ROOT
    / "catalog"
    / "skills"
    / "orchestration"
    / "adversarial-verifier"
    / "SKILL.md",
    ROOT
    / "catalog"
    / "skills"
    / "testing"
    / "e2e-testing-automation"
    / "SKILL.md",
    ROOT
    / "catalog"
    / "skills"
    / "testing"
    / "browser-testing-with-devtools"
    / "SKILL.md",
    ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "interface-review"
    / "SKILL.md",
    ROOT / "catalog" / "skills" / "code-review" / "testing-review" / "SKILL.md",
    ROOT
    / "catalog"
    / "skills"
    / "orchestration"
    / "quality-gate-definitions"
    / "SKILL.md",
)

HTML_SURFACES = (
    ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "html-output-conventions"
    / "SKILL.md",
    ROOT
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "SKILL.md",
    ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "frontend-ui-engineering"
    / "SKILL.md",
    ROOT / "catalog" / "commands" / "presentify.md",
)

RESPONSIVE_RULE = "catalog/rules/html/responsive-layout.md"
DEEP_PASS = (
    ROOT
    / "catalog"
    / "skills"
    / "testing"
    / "functional-verification"
    / "references"
    / "deep-pass.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_completion_gate_requires_fresh_behavioral_and_rendered_evidence() -> None:
    text = _read(VERIFICATION_BEFORE_COMPLETION)
    evidence_table = text.split("## Claim-to-Evidence Table", 1)[1].split(
        "## Smallest Sufficient Evidence Set", 1
    )[0]
    rationalizations = text.split("## Common Rationalizations", 1)[1].split(
        "## Loop Anti-Patterns", 1
    )[0]

    assert "| Behavioral output is correct |" in evidence_table
    assert "| Rendered output is correct |" in evidence_table
    assert evidence_table.count("[[functional-verification]]") >= 2
    assert '"the screenshots looked fine"' in rationalizations
    assert "Eyeballing is not evidence" in rationalizations
    assert (
        "the exact mechanism by which every defect in this project reached the maintainer"
        in rationalizations
    )


@pytest.mark.parametrize(
    "path", RECIPROCAL_SKILLS, ids=lambda path: path.parent.name
)
def test_adjacent_owner_has_one_reciprocal_functional_verification_link(path: Path) -> None:
    related = _read(path).split("## Related Skills", 1)[1]
    assert related.count("[[functional-verification]]") == 1


@pytest.mark.parametrize("path", HTML_SURFACES, ids=lambda path: path.parent.name)
def test_html_producer_cites_the_canonical_responsive_rule(path: Path) -> None:
    assert RESPONSIVE_RULE in _read(path)


def test_html_guidance_scopes_fixed_caps_to_the_canonical_rule() -> None:
    frontend = _read(
        ROOT
        / "catalog"
        / "skills"
        / "developer-experience"
        / "frontend-ui-engineering"
        / "SKILL.md"
    )
    responsive_rule = _read(ROOT / RESPONSIVE_RULE)
    assert "Keep fixed `px` or `ch` caps off text-bearing elements" in frontend
    assert "independent media bounds" in frontend
    assert "Images, video, canvas, SVG, and other media may be bounded" in responsive_rule

    frontend = _read(
        ROOT
        / "catalog"
        / "skills"
        / "developer-experience"
        / "frontend-ui-engineering"
        / "SKILL.md"
    )
    document = _read(
        ROOT
        / "catalog"
        / "skills"
        / "specialized-domains"
        / "document-to-interactive-html"
        / "SKILL.md"
    )
    assert ".page-shell { max-width: 1200px;" in frontend
    assert ".card { max-width:" not in frontend
    assert "45-85ch measure is scoped per prose element" not in document
    assert "measure-capped prose" not in document


def test_project_guidance_names_the_new_rule_and_verification_trees() -> None:
    agents = _read(ROOT / "AGENTS.md")
    assert "catalog/rules/html/" in agents
    assert "tests/verification/" in agents
    assert "Language, security, and artifact rules" in agents
    assert "Code style/security rules (4 languages)" not in agents


def test_deep_pass_has_no_pre_counter_repair_window() -> None:
    text = _read(DEEP_PASS)

    assert "initial evidence-collection pass does not increment the counter" in text
    assert "Every tree-changing correction caused by this deep pass consumes a cycle" in text
    assert "there is no pre-counter repair window" in text
