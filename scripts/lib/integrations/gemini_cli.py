"""Gemini CLI integration.

Gemini CLI consumes:
  - ~/.gemini/GEMINI.md as the global instruction file (shared with Gemini IDE)
  - ~/.gemini/commands/<name>.toml as custom slash-command definitions
  - ~/.gemini/extensions/ for extensions
  - Project .gemini/ for project-scoped overrides

This subclass mirrors catalog/commands/*.md to ~/.gemini/commands/*.toml via the
TomlIntegration helper, while still rendering GEMINI.md from the base template.
"""

from __future__ import annotations

from pathlib import Path

from .base import (
    InstallContext,
    MarkdownIntegration,
    SkillsIntegration,
    TomlIntegration,
)


class GeminiCliIntegration(MarkdownIntegration, SkillsIntegration, TomlIntegration):
    key = "gemini-cli"
    display_name = "Gemini CLI (Google)"
    config = {
        "global_dir": "~/.gemini",
        "workspace_dir": ".gemini",
        "instruction_file": "GEMINI.md",
        "instruction_template": "templates/ai-instructions/base-gemini.md",
        "skills_subdir": "skills",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/gemini-permissions.json",
    }

    def install_global(self, ctx: InstallContext) -> None:
        super().install_global(ctx)
        commands_dst = (Path.home() / ".gemini" / "commands").resolve()
        self._write_toml_commands(commands_dst, ctx)

    def install_workspace(self, ctx: InstallContext) -> None:
        super().install_workspace(ctx)
        commands_dst = (ctx.target_root / ".gemini" / "commands").resolve()
        self._write_toml_commands(commands_dst, ctx)
