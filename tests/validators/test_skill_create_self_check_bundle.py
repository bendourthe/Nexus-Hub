"""Contracts for the optional authoring self-check rubric bundled with skill-create.

The rubric is text guidance, not a runtime, so its value lives in three links
that fail silently when broken: SKILL.md must link the reference (or it is an
orphan), the reference must delegate prose checks to anti-slop-editing rather
than restate them, and it must keep the budget, not-covered, and
independent-verification wording that stops a self-grade from posing as proof.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "catalog" / "skills" / "workflow" / "skill-create"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCE = SKILL_DIR / "references" / "authoring-self-check.md"
DELEGATE = (
    ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "anti-slop-editing"
    / "references"
    / "self-check.md"
)


def _reference() -> str:
    return REFERENCE.read_text(encoding="utf-8")


def test_reference_is_linked_from_skill_body() -> None:
    assert REFERENCE.is_file()
    assert "references/authoring-self-check.md" in SKILL_MD.read_text(encoding="utf-8")


def test_delegate_target_exists() -> None:
    assert DELEGATE.is_file(), "anti-slop-editing self-check moved; update the link"


def test_reference_links_delegate_instead_of_restating() -> None:
    text = _reference()
    assert "anti-slop-editing/references/self-check.md" in text
    # Restating the owner's checks would fork the rule; their names stay out.
    assert "Proportional cutting" not in text
    assert "Voice preserved" not in text


@pytest.mark.parametrize(
    "phrase",
    [
        "evaluate/fix/recheck",
        "budget",
        "owned finding",
        "Missing delegate",
        "not covered",
        "INCONCLUSIVE",
        "verification-before-completion",
        "skill-eval-loop",
        "no rubric engine",
    ],
)
def test_reference_keeps_contract_wording(phrase: str) -> None:
    assert phrase in _reference(), f"rubric reference lost required wording: {phrase}"


def test_reference_is_ascii() -> None:
    _reference().encode("ascii")
