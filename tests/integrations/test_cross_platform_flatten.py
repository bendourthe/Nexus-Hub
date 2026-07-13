"""Cross-platform skill-flattening sweep (v3.12.0 Phase 4).

Every SKILL.md-open-standard platform that ships a skills folder discovers skills
one level deep (skills/<name>/SKILL.md). This suite asserts that the five
generic-mirror platforms flatten the catalog's <category>/<name>/ layer and add a
skill per command, and that Cursor (which has no skills surface) is unaffected.
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
    assert "name: presentify" in skill_md.read_text(encoding="utf-8")


def test_cursor_has_no_skills_surface(install_ctx: InstallContext):
    """Regression guard: Cursor has no skills folder (rules only), and the flatten
    change must not introduce one. Cursor's .mdc rules must still be produced.
    """
    integ = get("cursor")
    integ.install(install_ctx)
    assert not (install_ctx.target_root / ".cursor" / "skills").exists(), (
        "Cursor must not gain a skills/ surface"
    )
    mdc = list((install_ctx.target_root / ".cursor" / "rules").glob("*.mdc"))
    assert mdc, "Cursor .mdc rules must still be produced"
