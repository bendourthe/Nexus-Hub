"""Google Antigravity integrations (1.0 IDE and 2.0 multi-surface).

Antigravity 1.0 (the original IDE released ahead of I/O 2026): customizations
live under the IDE's Customizations menu and on disk under
`~/.gemini/antigravity/`. Rules + Workflows.

Antigravity 2.0 (announced at Google I/O 2026): standalone agent-first platform
with a desktop IDE, CLI, and SDK. The CLI uses a `.agent/` directory convention
for skills and `~/.agent/workflows/` for saved prompts. The Gemini CLI was
transitioned into the Antigravity CLI per the Google Developers Blog announcement.
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class Antigravity10Integration(MarkdownIntegration, SkillsIntegration):
    key = "antigravity"
    display_name = "Antigravity 1.0 (Google)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.gemini/antigravity",
        "workspace_dir": ".gemini/antigravity",
        "instruction_file": "rules.md",
        "instruction_template": "templates/ai-instructions/base-gemini.md",
        "skills_subdir": "skills",
        "commands_subdir": "global_workflows",
        "rules_subdir": "rules_library",
        "hooks_supported": False,
    }


class Antigravity20Integration(MarkdownIntegration, SkillsIntegration):
    key = "antigravity2"
    display_name = "Antigravity 2.0 (Google)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.agent",
        "workspace_dir": ".agent",
        "instruction_file": "AGENT.md",
        "instruction_template": "templates/ai-instructions/base-gemini.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "agents_subdir": "subagents",
        "rules_subdir": "rules",
        "hooks_supported": True,
        "permissions_file": "configs/permissions/gemini-permissions.json",
    }
