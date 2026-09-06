"""The release scope must engage the docs-tree canonicalize path (v4.0.1).

`update.md` promised since v3.11.0 that `/update refactor` "and, at release,
`/update release`" canonicalizes a repository's whole docs tree. The wiring
never delivered it: the skill canonicalizes only when `--canonicalize-layout`
is set, and nothing in the release scope set it. A repository on a legacy
layout therefore carried its drift silently through every release, receiving
only the passive "Continuing in place" notice.

These tests pin BOTH halves of the fix, because each fails differently:
engaging the flag, and NOT bypassing the confirmation gate while doing it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
UPDATE = ROOT / "catalog" / "commands" / "update.md"
LAYOUT_SKILL = (
    ROOT / "catalog" / "skills" / "code-cleanup" / "docs-layout-refactor" / "SKILL.md"
)


@pytest.fixture(scope="module")
def update_text() -> str:
    return UPDATE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def skill_text() -> str:
    return LAYOUT_SKILL.read_text(encoding="utf-8")


def test_release_delegation_map_names_the_canonicalize_flag(update_text: str) -> None:
    """The delegation map must show release passing the flag, not bare refactor."""
    release_lines = [
        line for line in update_text.splitlines() if line.strip().startswith("release   ->")
    ]

    assert release_lines, "the delegation map has no `release ->` row"
    assert any("--canonicalize-layout" in line for line in release_lines), (
        "the release row must pass --canonicalize-layout; without it the skill's "
        "Step 8 canonicalize branch cannot run and structural drift ships silently"
    )


def test_refactor_scope_states_the_release_rule(update_text: str) -> None:
    assert "the canonicalize path is ALWAYS engaged" in update_text, (
        "the refactor scope must state that release always engages canonicalization"
    )


def test_engaging_the_path_does_not_bypass_the_confirmation_gate(update_text: str) -> None:
    """Engaging the flag must not be described as auto-applying.

    The v4.0.0 capability gate published the promise that nothing moves without
    approval. If a later edit turns this into a silent auto-migration, that
    published promise becomes false, so the guarantee is pinned here too.
    """
    assert "does NOT move files" in update_text, (
        "the refactor scope must state that engaging the path does not move files"
    )
    assert "nothing moves until the user approves" in update_text


def test_skill_agrees_that_release_sets_the_flag(skill_text: str) -> None:
    """Both artifacts must state the same rule; drift between them caused this bug."""
    assert "`/update release` ALWAYS invokes this skill with `--canonicalize-layout`" in skill_text
    assert "it does not bypass Step 7" in skill_text


def test_skill_still_refuses_to_migrate_outside_the_explicit_path(skill_text: str) -> None:
    """The narrow default is the safety property; it must survive this change."""
    assert (
        "Never move or rename existing legacy directories during plan generation "
        "or a normal audit." in skill_text
    )
