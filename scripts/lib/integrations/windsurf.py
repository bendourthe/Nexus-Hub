"""Windsurf (Codeium) integration.

Windsurf uses .windsurf/rules/<name>.md for project rules and
.windsurf/workflows/<name>.md for saved prompts (workflows). The instruction
file is .windsurf/rules/nexus-hub-rules.md.
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class WindsurfIntegration(MarkdownIntegration, SkillsIntegration):
    key = "windsurf"
    display_name = "Windsurf (Codeium)"
    config = {
        "global_dir": None,
        "workspace_dir": ".windsurf",
        "instruction_file": "rules/nexus-hub-rules.md",
        "instruction_template": "templates/ai-instructions/base-claude.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "rules_subdir": "rules/library",
        "hooks_supported": False,
    }
