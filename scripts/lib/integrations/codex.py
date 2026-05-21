"""OpenAI Codex integration.

Codex consumes the AGENTS.md open-standard instruction file, plus a skills/
directory and a prompts/ directory (the Codex equivalent of slash commands).
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class CodexIntegration(MarkdownIntegration, SkillsIntegration):
    key = "codex"
    display_name = "Codex (OpenAI)"
    config = {
        "global_dir": "~/.codex",
        "workspace_dir": ".codex",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-codex.md",
        "skills_subdir": "skills",
        "commands_subdir": "prompts",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/codex-permissions.json",
    }
