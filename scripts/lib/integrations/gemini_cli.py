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
from .result import WriteResult


class GeminiCliIntegration(MarkdownIntegration, SkillsIntegration, TomlIntegration):
    key = "gemini-cli"
    display_name = "Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.gemini",
        "workspace_dir": ".gemini",
        "instruction_file": "GEMINI.md",
        "instruction_template": "templates/ai-instructions/base-gemini-cli.md",
        "skills_subdir": "skills",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/gemini-permissions.json",
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = super().install_global(ctx)
        commands_dst = (Path.home() / ".gemini" / "commands").resolve()
        result.files.extend(self._write_toml_commands(commands_dst, ctx))
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = super().install_workspace(ctx)
        commands_dst = (ctx.target_root / ".gemini" / "commands").resolve()
        result.files.extend(self._write_toml_commands(commands_dst, ctx))
        return result
