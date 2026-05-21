"""Nexus-AI integration -- the local-first desktop AI Studio consumer of Nexus-Hub.

Nexus-AI lives in a separate repository (https://github.com/bendourthe/Nexus-AI).
It is the primary downstream consumer of Nexus-Hub's catalog and expects:

  - ~/.nexus-ai/skills/             mirror of catalog/skills/
  - ~/.nexus-ai/commands/           mirror of catalog/commands/
  - ~/.nexus-ai/agents/             mirror of catalog/agents/
  - ~/.nexus-ai/rules/              mirror of catalog/rules/
  - ~/.nexus-ai/hooks/              mirror of catalog/hooks/
  - ~/.nexus-ai/mcp-configs/        mirror of catalog/mcp-configs/
  - ~/.nexus-ai/templates/          mirror of templates/
  - ~/.nexus-ai/NEXUS_AI.md         instruction file (rendered from base-claude.md)

The workspace scope ($PROJECT/.nexus-ai/) is read by Nexus-AI when the user
opens a project directory.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, MarkdownIntegration, SkillsIntegration


class NexusAiIntegration(MarkdownIntegration, SkillsIntegration):
    key = "nexus-ai"
    display_name = "Nexus-AI (Local Desktop Studio)"
    config = {
        "global_dir": "~/.nexus-ai",
        "workspace_dir": ".nexus-ai",
        "instruction_file": "NEXUS_AI.md",
        "instruction_template": "templates/ai-instructions/base-claude.md",
        "skills_subdir": "skills",
        "commands_subdir": "commands",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
        "permissions_file": "configs/permissions/claude-permissions.json",
    }

    def install_global(self, ctx: InstallContext) -> None:
        super().install_global(ctx)
        target = (Path.home() / ".nexus-ai").resolve()
        mcp_src = ctx.repo_root / "catalog" / "mcp-configs"
        mcp_dst = target / "mcp-configs"
        self._copy_tree(mcp_src, mcp_dst, ctx, self.key)
        tpl_src = ctx.repo_root / "templates"
        tpl_dst = target / "templates"
        self._copy_tree(tpl_src, tpl_dst, ctx, self.key)
