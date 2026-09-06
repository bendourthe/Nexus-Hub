"""Tests that each integration's install_workspace lays files at the expected paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext


@pytest.mark.parametrize(
    "key,expected_paths",
    [
        # v2.3.0 / DF-001: claude/codex render the instruction file at the
        # project root (where the tools read it); skills/ still mirror nested.
        ("claude", ["CLAUDE.md", ".claude/skills", ".claude/commands"]),
        ("codex", ["AGENTS.md", ".agents/skills", ".codex/prompts"]),
        ("gemini", [".gemini/GEMINI.md", ".gemini/skills", ".gemini/workflows"]),
        ("opencode", ["AGENTS.md", ".opencode/skills", ".opencode/commands"]),
        ("antigravity", [".gemini/antigravity/rules.md", ".gemini/antigravity/skills"]),
        ("antigravity2", ["AGENTS.md", ".agents/skills", ".agents/workflows"]),
        ("nexus-ai", [".nexus-ai/catalog/NEXUS_AI.md", ".nexus-ai/catalog/skills", ".nexus-ai/catalog/commands"]),
    ],
)
def test_workspace_install_lays_expected_paths(
    install_ctx: InstallContext,
    key: str,
    expected_paths: list[str],
):
    integ = get(key)
    integ.install(install_ctx)
    for rel in expected_paths:
        full = install_ctx.target_root / rel
        assert full.exists(), f"{key}: missing expected path {full}"


def test_cursor_writes_agents_md_and_mdc_rules(install_ctx: InstallContext):
    integ = get("cursor")
    integ.install(install_ctx)
    assert (install_ctx.target_root / "AGENTS.md").exists()
    rules_dir = install_ctx.target_root / ".cursor" / "rules"
    assert rules_dir.exists()
    mdc_files = list(rules_dir.glob("*.mdc"))
    assert len(mdc_files) >= 1, "Cursor should produce at least one .mdc rule file"
    sample = mdc_files[0].read_text(encoding="utf-8")
    assert sample.startswith("---\n"), "Cursor .mdc files must start with YAML frontmatter"


def test_copilot_writes_github_instruction(install_ctx: InstallContext):
    integ = get("copilot")
    integ.install(install_ctx)
    assert (install_ctx.target_root / ".github" / "copilot-instructions.md").exists()


def test_gemini_cli_writes_toml_commands(install_ctx: InstallContext):
    integ = get("gemini-cli")
    integ.install(install_ctx)
    commands_dir = install_ctx.target_root / ".gemini" / "commands"
    assert commands_dir.exists()
    toml_files = list(commands_dir.glob("*.toml"))
    assert len(toml_files) >= 1, "Gemini CLI should produce at least one .toml command file"
    sample = toml_files[0].read_text(encoding="utf-8")
    assert "prompt = " in sample
    assert "description = " in sample


def test_manifest_tracks_created_files(install_ctx: InstallContext):
    integ = get("nexus-ai")
    integ.install(install_ctx)
    tracked = install_ctx.manifest.files_for("nexus-ai")
    assert len(tracked) >= 4, f"nexus-ai install should track multiple files, got {len(tracked)}"
