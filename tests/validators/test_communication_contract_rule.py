"""v4.7.0 Phase 4: the progress-update half of the communication contract and the worked quoting examples.

The roster is derived from the templates directory (the same approach as
``test_autonomy_block_rule.py``), so a new template fails until it carries the contract
additions. Body identity across the twelve is owned by
``test_communication_contract_rollout.py`` and is not restated here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO_ROOT / "templates" / "ai-instructions"
_STYLE_GUIDE = _REPO_ROOT / "catalog" / "style-guides" / "agent-communication.md"
_SKILL = (
    _REPO_ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "agent-communication"
    / "SKILL.md"
)
_RESEARCH = [
    _REPO_ROOT
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "deep-research-compilation"
    / "SKILL.md",
    _REPO_ROOT / "catalog" / "skills" / "research" / "trend-research" / "SKILL.md",
]

_NARRATION_MARKER = "Say in one line what you are about to do"
_FORMATTING_MARKER = "keep conversational or emotional exchanges in plain prose"
_MINIMIZATION_MARKER = "Output Minimization still applies"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _substantive() -> list[Path]:
    out: list[Path] = []
    for path in sorted(_TEMPLATES.glob("*.md")):
        first = next((ln.strip() for ln in _read(path).split("\n") if ln.strip()), "")
        if not first.startswith("@"):
            out.append(path)
    return out


SUBSTANTIVE = _substantive()


def test_roster_has_twelve_substantive_templates():
    assert len(SUBSTANTIVE) == 12, [p.name for p in SUBSTANTIVE]


@pytest.mark.parametrize("path", SUBSTANTIVE, ids=lambda p: p.name)
def test_contract_carries_the_progress_and_formatting_rules(path: Path):
    text = _read(path)
    start = text.index("## Communication Contract")
    end = text.find("\n## ", start + 1)
    section = text[start:end]
    assert _NARRATION_MARKER in section
    assert _FORMATTING_MARKER in section
    assert _MINIMIZATION_MARKER in section


def test_style_guide_owns_the_rule_and_the_harness_note():
    text = _read(_STYLE_GUIDE)
    assert "## 8. Progress narration and formatting" in text
    assert "collapses or hides tool output" in text
    assert "does not loosen `## Output Minimization`" in text


def test_skill_mirrors_the_rule_and_reconciles_with_no_process_narration():
    text = _read(_SKILL)
    assert "### 8. Narrate the start and the middle" in text
    assert "past process" in text, (
        "step 2.5 must scope its rule to the retrospective account"
    )
    assert "collapses or hides tool output" in text


@pytest.mark.parametrize("path", _RESEARCH, ids=lambda p: p.parent.name)
def test_research_skill_carries_a_complete_worked_quoting_example(path: Path):
    text = _read(path)
    start = text.index("### Worked example")
    section = text[start : text.find("\n## ", start + 1)]
    assert "**Request**" in section
    assert "**Response**" in section
    assert "**Rationale**" in section
    assert section.count('"') >= 2, "the example must show exactly one marked quotation"
    assert "agree" in section and "differ" in section
