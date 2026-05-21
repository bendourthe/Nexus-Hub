"""OpenCode integration.

OpenCode consumes AGENTS.md as its instruction surface (open-standard) and a
.opencode/ workspace folder for skills/commands mirroring.
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class OpenCodeIntegration(MarkdownIntegration, SkillsIntegration):
    key = "opencode"
    display_name = "OpenCode"
    config = {
        "global_dir": "~/.opencode",
        "workspace_dir": ".opencode",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-opencode.md",
        "skills_subdir": "skills",
        "commands_subdir": "commands",
        "rules_subdir": "rules",
        "hooks_supported": False,
    }
