"""Cross-platform skill-flattening sweep (v3.12.0 Phase 4; Cursor added v3.15.0 Phase 2).

Every SKILL.md-open-standard platform that ships a skills folder discovers skills
one level deep (skills/<name>/SKILL.md). This suite asserts that the generic-mirror
platforms AND Cursor flatten the catalog's <category>/<name>/ layer and add a skill
per command. Cursor gained its native skills surface in v3.15.0 Phase 2 (Cursor
parity), so it is now part of the sweep rather than the no-skills exception it was.
"""

from __future__ import annotations

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext

_CATEGORY_NAMES = ("ai-development", "workflow", "security", "orchestration", "code-review")

# (integration key, workspace skills dir relative to target_root)
_FLATTENED = [
    ("claude", ".claude/skills"),
    ("gemini", ".gemini/skills"),
    ("gemini-cli", ".gemini/skills"),
    ("opencode", ".opencode/skills"),
    # nexus-ai isolates the catalog under a catalog/ subtree (v3.11.4).
    ("nexus-ai", ".nexus-ai/catalog/skills"),
    # Cursor gained a native flattened skills surface in v3.15.0 Phase 2.
    ("cursor", ".cursor/skills"),
]


@pytest.mark.parametrize("key,skills_rel", _FLATTENED)
def test_platform_flattens_skills_one_level(install_ctx: InstallContext, key: str, skills_rel: str):
    integ = get(key)
    integ.install(install_ctx)
    skills_dir = install_ctx.target_root / skills_rel
    assert skills_dir.is_dir(), f"{key}: {skills_dir} should exist"

    # The category layer must be gone.
    for category in _CATEGORY_NAMES:
        assert not (skills_dir / category).is_dir(), (
            f"{key}: category folder {category!r} leaked into {skills_rel} -- not flattened"
        )

    skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir()]
    assert len(skill_dirs) >= 50, f"{key}: expected the flat catalog; got {len(skill_dirs)}"
    for skill in skill_dirs[:10]:
        assert (skill / "SKILL.md").exists(), f"{key}: {skill.name}/ must hold SKILL.md directly"


@pytest.mark.parametrize("key,skills_rel", _FLATTENED)
def test_platform_adds_command_skills(install_ctx: InstallContext, key: str, skills_rel: str):
    """Every command surfaces as a skill in each flattened platform's skills dir."""
    integ = get(key)
    integ.install(install_ctx)
    skill_md = install_ctx.target_root / skills_rel / "presentify" / "SKILL.md"
    assert skill_md.exists(), f"{key}: command-skill missing at {skill_md}"
    text = skill_md.read_text(encoding="utf-8")
    assert "name: presentify" in text
    assert "disable-model-invocation: true" in text, (
        f"{key}: command-skill must not be model-auto-invoked"
    )


def test_cursor_flattens_skills_and_keeps_rules(install_ctx: InstallContext):
    """v3.15.0 Phase 2: Cursor now writes a flattened skills surface AND still
    produces its .mdc rules (the two coexist; skills did not displace rules).
    """
    integ = get("cursor")
    integ.install(install_ctx)
    skills_dir = install_ctx.target_root / ".cursor" / "skills"
    assert skills_dir.is_dir(), "Cursor must now write a .cursor/skills surface (Phase 2)"
    for category in _CATEGORY_NAMES:
        assert not (skills_dir / category).is_dir(), (
            f"category folder {category!r} leaked into .cursor/skills -- not flattened"
        )
    mdc = list((install_ctx.target_root / ".cursor" / "rules").glob("*.mdc"))
    assert mdc, "Cursor .mdc rules must still be produced alongside skills"
