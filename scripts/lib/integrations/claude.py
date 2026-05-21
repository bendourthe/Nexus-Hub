"""Claude Code (Anthropic) integration."""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class ClaudeIntegration(MarkdownIntegration, SkillsIntegration):
    key = "claude"
    display_name = "Claude Code (Anthropic)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.claude",
        "workspace_dir": ".claude",
        "instruction_file": "CLAUDE.md",
        "instruction_template": "templates/ai-instructions/base-claude.md",
        "skills_subdir": "skills",
        "commands_subdir": "commands",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
        "permissions_file": "configs/permissions/claude-permissions.json",
    }
