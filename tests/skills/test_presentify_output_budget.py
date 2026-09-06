"""v4.7.0 Phase 3: long-output budget, base64-in-context rule, and safeguard phrasing guidance.

Four durable contracts, each asserted on a short stable phrase rather than the full prose:

1. Both large-deliverable surfaces (the skill and the /presentify command) state the
   single-limit output-budget rule and reconcile it with Output Minimization.
2. The skill states the base64-payload rule (inspect the model through a projection,
   never read the generated HTML back wholesale) and pins it in Verification.
3. Both security skills carry the two safeguard phrasings and the permitted-work note.
4. The base64 decision note exists and names option (b).
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SKILL = (
    _ROOT
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "SKILL.md"
)
_COMMAND = _ROOT / "catalog" / "commands" / "presentify.md"
_SECURITY = [
    _ROOT / "catalog" / "skills" / "code-review" / "security-review" / "SKILL.md",
    _ROOT / "catalog" / "skills" / "security" / "security-patch-advisor" / "SKILL.md",
]
_DECISION = (
    _ROOT
    / "docs"
    / "releases"
    / "v4"
    / "v4.7"
    / "development"
    / "base64-context-decision.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("path", [_SKILL, _COMMAND], ids=["skill", "command"])
def test_large_deliverable_surfaces_state_the_output_budget_rule(path: Path):
    text = _read(path)
    assert "counts toward a single limit" in text
    assert "Output Minimization" in text
    assert "documented default effort" in text


def test_skill_keeps_base64_payloads_out_of_context():
    text = _read(_SKILL)
    assert "Base64 payloads stay out of context" in text
    assert "never read the generated `.html` back wholesale" in text
    assert "No `data_uri` payload entered the agent's context" in text


@pytest.mark.parametrize("path", _SECURITY, ids=lambda p: p.parent.name)
def test_security_skills_carry_the_safeguard_phrasing_guidance(path: Path):
    text = _read(path)
    assert "are there any bugs in this program" in text
    assert "language's documentation" in text
    assert "false positive to work around by rephrasing" in text


def test_base64_decision_note_records_option_b():
    text = _read(_DECISION)
    assert "Option (b) holds" in text
    assert "extract_content.py" in text and "build_presentation.py" in text
