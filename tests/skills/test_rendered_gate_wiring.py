"""Every surface that produces a document actually calls the rendered gate.

A gate nothing invokes is decorative. These assertions are deliberately about
WIRING rather than prose: each names a surface and the helper it must reference,
so a refactor that drops one fails here instead of silently unwiring the gate
and leaving the documentation claiming otherwise.

That is not hypothetical. `check_handbooks.py` was written in v4.11.0, wired
into no CI profile at all, and consequently never ran against the repository's
own handbooks until Phase 7 of that plan noticed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"

AUDIT = BUNDLE / "scripts/geometric_audit.py"
ATTEST = BUNDLE / "scripts/check_attestation.py"
RULE = ROOT / "catalog/rules/html/visual-self-verification.md"

# surface -> the references it must carry
WIRING = {
    ROOT / "catalog/commands/presentify.md": ("geometric_audit.py", "check_attestation.py"),
    BUNDLE / "SKILL.md": ("geometric_audit.py", "check_attestation.py"),
    ROOT / "catalog/commands/update.md": ("geometric_audit.py",),
    ROOT / "catalog/skills/orchestration/quality-gate-definitions/SKILL.md": (
        "rendered-artifact-verified",
        "geometric_audit.py",
    ),
    ROOT / "catalog/skills/workflow/verification-before-completion/SKILL.md": (
        "visual-self-verification.md",
    ),
}


def test_both_gate_scripts_exist_and_are_executable_python() -> None:
    for script in (AUDIT, ATTEST):
        assert script.is_file(), f"{script.name} is missing"
        assert script.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3")


@pytest.mark.parametrize("surface", sorted(WIRING, key=str))
def test_each_surface_references_the_gate(surface: Path) -> None:
    assert surface.is_file(), f"{surface} is missing"
    text = surface.read_text(encoding="utf-8")
    for needle in WIRING[surface]:
        assert needle in text, (
            f"{surface.relative_to(ROOT).as_posix()} no longer references "
            f"{needle!r}; the gate is unwired on that surface"
        )


def test_the_global_rule_exists_beside_its_sibling() -> None:
    assert RULE.is_file()
    assert (RULE.parent / "responsive-layout.md").is_file(), (
        "the rule is meant to sit beside responsive-layout.md in the html family"
    )


def test_the_rule_states_the_three_non_obvious_constraints() -> None:
    """The three that are counter-intuitive enough to be dropped in a rewrite."""
    text = RULE.read_text(encoding="utf-8")
    assert "present and unique" in text, "anchor assertion rule missing"
    assert "1500" in text, "capture size cap missing"
    assert "computed" in text.lower(), "computed-DOM rule missing"


def test_exit_two_is_documented_as_unverified_on_every_calling_surface() -> None:
    """The rule that makes an unavailable renderer honest rather than green."""
    for surface in (ROOT / "catalog/commands/presentify.md", BUNDLE / "SKILL.md"):
        text = surface.read_text(encoding="utf-8")
        assert "unverified" in text.lower(), (
            f"{surface.name} does not say what an unverifiable run means; "
            f"reporting unverified as success is the failure the gate prevents"
        )
