"""Tests for the OpenCode integration parity surfaces (v3.15.0 Phase 3).

Covers the read-contract verified 2026-07-21 (https://opencode.ai/docs):
  - agents copied verbatim to .opencode/agents (global ~/.config/opencode/agents):
    catalog/agents/*.md load as-is (mode defaults to `all`; name/tools ignored)
  - the pre-existing skills (flattened) + commands + rules surfaces still install
  - hooks are NOT delivered (OpenCode's plugins/ is a JS/TS Bun runtime, DF-4):
    hooks_supported is False and no hooks surface is written
"""

from __future__ import annotations

from dataclasses import replace

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext

_CATEGORY_NAMES = ("ai-development", "workflow", "security", "orchestration", "code-review")


def test_opencode_workspace_writes_agents(install_ctx: InstallContext):
    """Subagents land at .opencode/agents as verbatim catalog .md files (Phase 3)."""
    get("opencode").install(install_ctx)
    agents_dir = install_ctx.target_root / ".opencode" / "agents"
    assert agents_dir.is_dir(), "OpenCode must write a .opencode/agents surface (Phase 3)"
    md_files = list(agents_dir.glob("*.md"))
    assert len(md_files) >= 5, f"expected catalog agents copied; got {len(md_files)}"


def test_opencode_agents_are_catalog_md_verbatim(install_ctx: InstallContext):
    """A known catalog agent is copied verbatim (frontmatter body preserved)."""
    get("opencode").install(install_ctx)
    agent = install_ctx.target_root / ".opencode" / "agents" / "adversarial-reviewer.md"
    assert agent.exists(), f"catalog agent missing at {agent}"
    text = agent.read_text(encoding="utf-8")
    assert "description:" in text, "agent frontmatter (description) must survive the copy"


def test_opencode_preserves_skills_commands_rules(install_ctx: InstallContext):
    """Adding agents did not displace the pre-existing skills/commands/rules surfaces."""
    get("opencode").install(install_ctx)
    root = install_ctx.target_root / ".opencode"

    skills_dir = root / "skills"
    assert skills_dir.is_dir(), "skills surface missing"
    for category in _CATEGORY_NAMES:
        assert not (skills_dir / category).is_dir(), (
            f"category folder {category!r} leaked into skills -- not flattened"
        )
    assert (root / "commands").is_dir() and list((root / "commands").glob("*.md")), "commands missing"
    assert (root / "rules").is_dir() and list((root / "rules").rglob("*.md")), "rules missing"


def test_opencode_no_hooks_surface(install_ctx: InstallContext):
    """OpenCode ships no hooks (plugins/ is a JS/TS Bun runtime; hooks_supported False, DF-4)."""
    result = get("opencode").install(install_ctx)
    assert not (install_ctx.target_root / ".opencode" / "hooks").exists(), (
        "OpenCode must not write a hooks surface (its plugin model is a different runtime)"
    )
    assert not any(
        "/.opencode/hooks" in fa.path.replace("\\", "/") for fa in result.files
    ), "no hooks FileAction should be produced for OpenCode"


def test_opencode_global_writes_agents(install_ctx: InstallContext):
    """Global install writes agents under ~/.config/opencode/agents (dry-run)."""
    result = get("opencode").dry_run(replace(install_ctx, scope="global"))
    joined = " ".join(fa.path.replace("\\", "/") for fa in result.files)
    assert "/.config/opencode/agents" in joined, (
        "global install must write ~/.config/opencode/agents"
    )


def test_opencode_idempotent_workspace_install(install_ctx: InstallContext):
    """Second install marks at least one file unchanged."""
    get("opencode").install(install_ctx)
    result = get("opencode").install(install_ctx)
    actions = {a.action for a in result.files}
    assert "unchanged" in actions, f"second install should produce 'unchanged'; got {actions}"
