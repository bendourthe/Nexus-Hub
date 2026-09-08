"""Aggregate coverage for the v4.0.0 cross-platform template contracts.

`scripts/check_base_template_parity.py` byte-locks invariant contracts across the five
lockstep templates only. The other seven substantive templates (the guardrails
five, `base-google-shared.md`, and `generic-instructions.md`) are outside that
guard's roster by design, so nothing else would notice if the rollout skipped
one. This is the exact defect class AGENTS.md warns about for the non-lockstep
seven, and it is why this file exists.

Per the test-retention policy in AGENTS.md, the non-lockstep templates are
covered by ONE data-driven aggregate test rather than seven near-identical
per-file tests. The four antigravity / gemini-cli surface-note stubs are
deliberately excluded: they carry no behavioral rules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "templates" / "ai-instructions"

COMMUNICATION_HEADING = "## Communication Contract"
COMMUNICATION_DEEP_LINK = "~/.nexus-hub/style-guides/agent-communication.md"
DOCS_LAYOUT_HEADING = "## Documentation Layout"
DOCS_LAYOUT_SKILL = "`docs-layout-refactor`"

LOCKSTEP = [
    "base-claude.md",
    "base-codex.md",
    "base-cursor.md",
    "base-gemini.md",
    "base-opencode.md",
]
GUARDRAILS = [
    "base-aider.md",
    "base-kimi.md",
    "base-openclaw.md",
    "base-qwen.md",
    "base-windsurf.md",
]
OTHER_SUBSTANTIVE = [
    "base-google-shared.md",
    "generic-instructions.md",
    "base-pi.md",
]
SUBSTANTIVE = LOCKSTEP + GUARDRAILS + OTHER_SUBSTANTIVE

# Surface-note stubs: no behavioral rules, deliberately out of scope.
STUBS = [
    "base-antigravity-10.md",
    "base-antigravity-20.md",
    "base-antigravity-cli.md",
    "base-gemini-cli.md",
]


def _read(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def _section_body(name: str, heading: str) -> str:
    text = _read(name)
    start = text.index(heading)
    rest = text[start + len(heading):]
    end = rest.find("\n## ")
    return (rest if end == -1 else rest[:end]).strip()


def test_substantive_roster_matches_the_template_directory() -> None:
    """The roster is complete: every template file is classified exactly once.

    Without this, adding a new template would silently escape the rollout check
    below, because that check only iterates the names listed here.
    """
    on_disk = {p.name for p in TEMPLATE_DIR.glob("*.md")}
    classified = set(SUBSTANTIVE) | set(STUBS)
    assert on_disk == classified, (
        "templates/ai-instructions/ changed. Classify each new file as "
        "substantive (it carries behavioral rules) or a surface-note stub, "
        f"then update this roster. Unclassified: {sorted(on_disk - classified)}; "
        f"listed but missing: {sorted(classified - on_disk)}"
    )


@pytest.mark.parametrize("name", SUBSTANTIVE)
def test_substantive_template_carries_the_contract(name: str) -> None:
    text = _read(name)
    assert COMMUNICATION_HEADING in text, f"{name} is missing the {COMMUNICATION_HEADING!r} section"
    assert COMMUNICATION_DEEP_LINK in text, f"{name} is missing the deep link to the full contract"


@pytest.mark.parametrize("name", SUBSTANTIVE)
def test_substantive_template_carries_documentation_layout(name: str) -> None:
    text = _read(name)
    assert DOCS_LAYOUT_HEADING in text, f"{name} is missing the {DOCS_LAYOUT_HEADING!r} section"
    assert DOCS_LAYOUT_SKILL in text, f"{name} is missing the docs-layout-refactor handoff"


def test_all_thirteen_substantive_templates_are_covered() -> None:
    """Guard the count itself, so a roster edit cannot quietly shrink coverage."""
    assert len(SUBSTANTIVE) == 13


@pytest.mark.parametrize("name", STUBS)
def test_surface_note_stubs_are_left_alone(name: str) -> None:
    text = _read(name)
    assert COMMUNICATION_HEADING not in text, f"{name} is a surface-note stub and must not duplicate the communication contract"
    assert DOCS_LAYOUT_HEADING not in text, f"{name} is a surface-note stub and must inherit the documentation contract"


def test_contract_body_is_identical_across_every_substantive_template() -> None:
    """Stronger than the parity gate: all 12, not just the lockstep five.

    The parity gate cannot be widened to 12 (the guardrails templates
    legitimately differ elsewhere), but the contract section itself has no valid
    per-platform variation, so wording drift is checkable here.
    """
    bodies = {}
    for name in SUBSTANTIVE:
        bodies[name] = _section_body(name, COMMUNICATION_HEADING)

    reference_name = SUBSTANTIVE[0]
    reference = bodies[reference_name].strip()
    drifted = [n for n, b in bodies.items() if b.strip() != reference]
    assert not drifted, (
        "Communication Contract body drifted from "
        f"{reference_name} in: {drifted}. The section is identical by intent."
    )


def test_documentation_layout_body_is_identical_across_every_substantive_template() -> None:
    bodies = {name: _section_body(name, DOCS_LAYOUT_HEADING) for name in SUBSTANTIVE}
    reference_name = SUBSTANTIVE[0]
    reference = bodies[reference_name]
    drifted = [name for name, body in bodies.items() if body != reference]
    assert not drifted, (
        "Documentation Layout body drifted from "
        f"{reference_name} in: {drifted}. The section is identical by intent."
    )


def test_end_of_task_summary_uses_the_labeled_parts() -> None:
    """The report shape reaches every template that carries the summary block."""
    for name in SUBSTANTIVE:
        text = _read(name)
        if "## End-of-Task Summary" not in text:
            continue
        assert "Use the labeled parts" in text, f"{name} keeps the pre-v4.0.0 summary bullets"
        for part in ("**Completed**", "**Verified**", "**Open**", "**Next**"):
            assert part in text, f"{name} is missing the {part} label"


def test_style_guide_is_the_single_source_of_truth() -> None:
    """The deep-link target exists in the catalog and is installer-reachable."""
    guide = REPO_ROOT / "catalog" / "style-guides" / "agent-communication.md"
    assert guide.is_file(), "the contract's deep-link target does not exist"
    text = guide.read_text(encoding="utf-8")
    for heading in (
        "## 1. Response structure",
        "## 2. Plain language",
        "## 3. Placeholder discipline in commands",
        "## 4. Guided steps protocol",
        "## 5. End-of-task report shape",
        "## 6. Docs deep-link rule",
        "## 7. Waiting-state and interim updates",
        "## Verification",
    ):
        assert heading in text, f"style guide is missing {heading!r}"
