"""Tests for the OpenCode integration parity surfaces (v3.15.0 Phase 3).

Covers the read-contract verified 2026-07-21 (https://opencode.ai/docs):
  - agents copied verbatim to .opencode/agents (global ~/.config/opencode/agents):
    catalog/agents/*.md load with the Claude-style `tools` line removed (v4.13.2)
  - the pre-existing skills (flattened) + commands + rules surfaces still install
  - hooks are NOT delivered (OpenCode's plugins/ is a JS/TS Bun runtime, DF-4):
    hooks_supported is False and no hooks surface is written
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations._catalog_adapters import _drop_frontmatter_keys


@pytest.fixture(autouse=True)
def _isolated_nexus_state(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the instruction-merge lock and backup state out of the real profile.

    A reinstall finds an existing instruction file and takes a per-target lock under
    the Nexus state root, which falls back to the real home unless NEXUS_HUB_HOME is
    set. The directory sits outside tmp_path so tests that snapshot tmp_path see no
    extra entries.
    """
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path_factory.mktemp("nexus-home")))


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


def test_opencode_agents_drop_the_claude_tools_line_and_keep_the_body(install_ctx: InstallContext):
    """OpenCode 1.18 rejects the whole config on a string `tools` key, so it must not ship.

    Found by the v4.13.2 end-to-end run: `tools: Read, Glob, Grep, Bash` made OpenCode
    exit with "Configuration is invalid ... Expected object | undefined" before any turn.
    """
    get("opencode").install(install_ctx)
    agents_dir = install_ctx.target_root / ".opencode" / "agents"
    catalog = Path(__file__).resolve().parents[2] / "catalog" / "agents"
    sources = sorted(catalog.glob("*.md"))
    assert sources
    for source in sources:
        installed = (agents_dir / source.name).read_text(encoding="utf-8")
        front, body = installed.split("\n---", 1)
        assert "\ntools:" not in front, source.name
        assert body == source.read_text(encoding="utf-8").split("\n---", 1)[1], source.name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b"---\nname: a\ntools: Read\n---\nbody tools: kept\n", b"---\nname: a\n---\nbody tools: kept\n"),
        (b"---\r\ntools: Read\r\ndescription: d\r\n---\r\nb\r\n", b"---\r\ndescription: d\r\n---\r\nb\r\n"),
        (b"no frontmatter\ntools: x\n", b"no frontmatter\ntools: x\n"),
        (b"---\ntools: x\nunterminated\n", b"---\ntools: x\nunterminated\n"),
    ],
)
def test_drop_frontmatter_keys_touches_only_the_frontmatter_block(raw: bytes, expected: bytes) -> None:
    assert _drop_frontmatter_keys(raw, ("tools",)) == expected


def test_opencode_preserves_skills_commands(install_ctx: InstallContext):
    """Adding agents did not displace the pre-existing skills/commands surfaces."""
    get("opencode").install(install_ctx)
    root = install_ctx.target_root / ".opencode"

    skills_dir = root / "skills"
    assert skills_dir.is_dir(), "skills surface missing"
    for category in _CATEGORY_NAMES:
        assert not (skills_dir / category).is_dir(), (
            f"category folder {category!r} leaked into skills -- not flattened"
        )
    assert (root / "commands").is_dir() and list((root / "commands").glob("*.md")), "commands missing"


@pytest.mark.parametrize("scope", ["workspace", "global"])
def test_opencode_writes_no_unread_rules_dir(install_ctx: InstallContext, scope: str):
    """AR-51: OpenCode reads AGENTS.md plus the `instructions` array, never rules/.

    https://opencode.ai/docs/rules/ (fetched 2026-10-10) lists project AGENTS.md,
    upward AGENTS.md/CLAUDE.md, ~/.config/opencode/AGENTS.md, and
    ~/.claude/CLAUDE.md, with no rules/ directory. A mirror there is dead weight.
    """
    if scope == "global":
        (install_ctx.target_root / ".config" / "opencode").mkdir(parents=True)
        ctx = replace(install_ctx, scope="global", explicit_target=True)
        get("opencode").install(ctx)
        root = install_ctx.target_root / ".config" / "opencode"
    else:
        get("opencode").install(install_ctx)
        root = install_ctx.target_root / ".opencode"
    assert (root / "skills").is_dir(), f"{scope}: install did not run"
    assert not (root / "rules").exists(), f"{scope}: unread rules/ mirror written"


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
