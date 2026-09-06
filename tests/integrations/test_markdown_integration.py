"""Tests for the shared-mode merge integration on MarkdownIntegration (T004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.installer.instruction_merge import (
    DEFAULT_END_MARKER,
    DEFAULT_START_MARKER,
)
from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext

START = DEFAULT_START_MARKER
END = DEFAULT_END_MARKER


def test_reinstall_preserves_user_content_around_marker(install_ctx: InstallContext) -> None:
    """Pre-seed a user-edited Claude file with content above and below the
    marker block; verify reinstall keeps the user content intact and only
    rewrites the Nexus-Hub block.
    """
    integ = get("claude")
    # v2.3.0 / DF-001: workspace CLAUDE.md lives at the project root.
    install_ctx.target_root.mkdir(parents=True, exist_ok=True)
    claude_md = install_ctx.target_root / "CLAUDE.md"

    user_preamble = "# My personal CLAUDE notes\n\nSome user wisdom.\n"
    user_appendix = "\n## My TODOs\n\n- ship the auth flow\n- write more tests\n"
    claude_md.write_text(
        f"{user_preamble}\n{START}\nold-nexus-content\n{END}\n{user_appendix}",
        encoding="utf-8",
    )

    integ.install(install_ctx)

    text = claude_md.read_text(encoding="utf-8")
    assert "# My personal CLAUDE notes" in text
    assert "Some user wisdom." in text
    assert "## My TODOs" in text
    assert "- ship the auth flow" in text
    assert "old-nexus-content" not in text
    assert START in text
    assert END in text


def test_reinstall_with_no_change_returns_unchanged(install_ctx: InstallContext) -> None:
    integ = get("claude")
    integ.install(install_ctx)
    result = integ.install(install_ctx)
    claude_actions = [
        fa for fa in result.files if fa.path.endswith("CLAUDE.md")
    ]
    assert claude_actions, "expected at least one action for CLAUDE.md on reinstall"
    assert claude_actions[0].action == "unchanged"


def test_dedicated_mode_overwrites_full_file(install_ctx: InstallContext) -> None:
    """Nexus-AI is marked dedicated; its NEXUS_AI.md is fully owned by
    Nexus-Hub and should NOT contain marker comments.
    """
    integ = get("nexus-ai")
    integ.install(install_ctx)
    nexus_md = install_ctx.target_root / ".nexus-ai" / "catalog" / "NEXUS_AI.md"
    assert nexus_md.exists()
    text = nexus_md.read_text(encoding="utf-8")
    assert START not in text
    assert END not in text


def test_teardown_removes_only_marker_block(install_ctx: InstallContext) -> None:
    integ = get("opencode")
    # Derive the path from the config rather than hardcoding it: OpenCode reads the
    # workspace-ROOT AGENTS.md (the .opencode/AGENTS.md claim was removed once the
    # vendor docs were re-verified), and the config is what declares that.
    _iwd = integ.config.get("instruction_workspace_dir", integ.config["workspace_dir"])
    workspace_agents = install_ctx.target_root / _iwd / integ.config["instruction_file"]
    integ.install(install_ctx)
    # Add user content around the marker block.
    text = workspace_agents.read_text(encoding="utf-8")
    augmented = "# user heading\n\nuser body before.\n\n" + text + "\nuser body after.\n"
    workspace_agents.write_text(augmented, encoding="utf-8")

    integ.teardown(install_ctx)

    if workspace_agents.exists():
        final = workspace_agents.read_text(encoding="utf-8")
        assert "# user heading" in final
        assert "user body before." in final
        assert "user body after." in final
        assert START not in final
        assert END not in final


def test_legacy_header_migrated_inline(install_ctx: InstallContext) -> None:
    """Pre-seed a file with the v2.1 legacy `## Nexus-Hub` header (no markers);
    verify the install migrates it to a marker-delimited block.
    """
    integ = get("codex")
    # v2.3.0 / DF-001: workspace AGENTS.md lives at the project root.
    install_ctx.target_root.mkdir(parents=True, exist_ok=True)
    agents_md = install_ctx.target_root / "AGENTS.md"
    agents_md.write_text(
        "# Project AGENTS\n\nUser notes.\n\n## Nexus-Hub\n\nOld unmanaged body.\n",
        encoding="utf-8",
    )

    integ.install(install_ctx)

    text = agents_md.read_text(encoding="utf-8")
    assert "## Nexus-Hub" not in text
    assert "Old unmanaged body." not in text
    assert START in text
    assert END in text
    assert "User notes." in text


@pytest.mark.parametrize(
    "key",
    ["claude", "codex", "gemini", "opencode", "antigravity", "antigravity2", "gemini-cli"],
)
def test_shared_mode_writes_with_markers(install_ctx: InstallContext, key: str) -> None:
    integ = get(key)
    integ.install(install_ctx)
    instruction_file = integ.config["instruction_file"]
    # v2.3.0 / DF-001: the instruction file may live at the project root
    # (claude/codex set instruction_workspace_dir="") or nested under the
    # workspace dir (gemini/opencode/antigravity/...).
    iwd = integ.config.get("instruction_workspace_dir", integ.config["workspace_dir"])
    dst = install_ctx.target_root / iwd / instruction_file
    assert dst.exists(), f"{key}: expected instruction file at {dst}"
    text = dst.read_text(encoding="utf-8")
    assert START in text, f"{key}: instruction file should contain start marker"
    assert END in text, f"{key}: instruction file should contain end marker"
