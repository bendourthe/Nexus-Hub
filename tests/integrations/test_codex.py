"""Tests for the Codex / new ChatGPT desktop app integration (v3.12.0 Phase 2).

Covers the corrected read-contract from docs/policy/platform-read-contracts.md:
  - skills flattened one level into the documented ~/.agents/skills root
  - every catalog command emitted as a skill ($name) in that root
  - every command kept as a legacy top-level prompt (~/.codex/prompts, /prompts:name)
  - the repo-root AGENTS.md instruction file (workspace) with the SKILL_INDEX block
  - NO category folder ever leaks into skills/ (the flattening-bug regression guard)
"""

from __future__ import annotations

from dataclasses import replace

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext

_CATEGORY_NAMES = ("ai-development", "workflow", "security", "orchestration", "code-review")


def test_codex_workspace_flattens_skills(install_ctx: InstallContext):
    """Workspace install lays flattened skills under the shared .agents/skills root."""
    integ = get("codex")
    integ.install(install_ctx)
    root = install_ctx.target_root

    skills_dir = root / ".agents" / "skills"
    assert skills_dir.is_dir(), f"{skills_dir} should exist"
    assert not (root / ".codex" / "skills").exists()
    for category in _CATEGORY_NAMES:
        assert not (skills_dir / category).is_dir(), (
            f"category folder {category!r} leaked into {skills_dir} -- skills not flattened"
        )
    skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir()]
    assert len(skill_dirs) >= 50, f"expected the full flat catalog; got {len(skill_dirs)}"
    for skill in skill_dirs[:10]:
        assert (skill / "SKILL.md").exists(), f"{skill.name}/ must contain SKILL.md directly"


def test_codex_workspace_commands_as_skills_and_prompts(install_ctx: InstallContext):
    """Every command surfaces as a shared skill ($name) and a legacy prompt."""
    integ = get("codex")
    integ.install(install_ctx)
    root = install_ctx.target_root

    # presentify is a command with no colliding skill folder, so it becomes a skill.
    skills_dir = root / ".agents" / "skills"
    skill_md = skills_dir / "presentify" / "SKILL.md"
    assert skill_md.exists(), f"command-skill missing at {skill_md}"
    text = skill_md.read_text(encoding="utf-8")
    assert "name: presentify" in text
    assert "/presentify" in text, "command-skill description should carry the slash lead-in"
    assert "disable-model-invocation: true" in text, (
        "command-skills must not be model-auto-invoked"
    )
    sidecar = skills_dir / "presentify" / "agents" / "openai.yaml"
    assert sidecar.is_file(), f"Codex sidecar missing for command-skill at {sidecar}"
    sidecar_text = sidecar.read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" in sidecar_text
    assert "allow_implicit_invocation: true" not in sidecar_text

    # Catalog skills stay model-invoked: no sidecar unless they declare the field.
    catalog_skill = root / ".agents" / "skills" / "loop-engineering"
    if catalog_skill.is_dir():
        assert not (catalog_skill / "agents" / "openai.yaml").exists()

    # And the legacy top-level prompt is present for /prompts:presentify.
    prompt = root / ".codex" / "prompts" / "presentify.md"
    assert prompt.exists(), "legacy prompt missing"
    assert not (root / ".codex" / "prompts" / "presentify").is_dir(), "prompts must stay top-level"


def test_codex_workspace_writes_root_agents_md(install_ctx: InstallContext):
    """The instruction file lands at the project root as AGENTS.md, not under .codex/."""
    integ = get("codex")
    integ.install(install_ctx)
    agents_md = install_ctx.target_root / "AGENTS.md"
    assert agents_md.exists(), "repo-root AGENTS.md not written"


def test_codex_global_targets_codex_and_agents_roots(install_ctx: InstallContext):
    """Global install writes Codex prompts/instructions and shared skills.
    """
    integ = get("codex")
    global_ctx = replace(install_ctx, scope="global")
    result = integ.dry_run(global_ctx)
    joined = " ".join(fa.path.replace("\\", "/") for fa in result.files)

    assert "/.codex/skills/" not in joined
    assert "/.agents/skills/" in joined, "global install must write ~/.agents/skills"
    assert "/.codex/prompts/" in joined, "global install must write legacy prompts"
    assert "/.codex/AGENTS.md" in joined, "global install must render ~/.codex/AGENTS.md"


def test_codex_idempotent_workspace_install(install_ctx: InstallContext):
    """Second install on the same target should mark at least one file unchanged."""
    integ = get("codex")
    integ.install(install_ctx)
    result = integ.install(install_ctx)
    actions = {a.action for a in result.files}
    assert "unchanged" in actions, f"second install should produce 'unchanged'; got {actions}"
