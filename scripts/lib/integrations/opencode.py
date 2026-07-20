"""OpenCode integration.

OpenCode consumes AGENTS.md as its instruction surface (open-standard) and a
.opencode/ workspace folder for skills/commands mirroring.
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class OpenCodeIntegration(MarkdownIntegration, SkillsIntegration):
    key = "opencode"
    display_name = "OpenCode"
    instruction_mode = "shared"
    config = {
        # v3.14.5: OpenCode's canonical GLOBAL config dir is ~/.config/opencode
        # (XDG), not ~/.opencode -- the latter was a dead global path (the
        # instruction file + commands never reached OpenCode there). Re-verified
        # 2026-07-19 against https://opencode.ai/docs/config/ + /rules/ + /commands/.
        # Skills still reached OpenCode via its ~/.claude/skills + ~/.agents/skills
        # aliases even before this fix; the instruction file + commands did not.
        "global_dir": "~/.config/opencode",
        "workspace_dir": ".opencode",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-opencode.md",
        # OpenCode discovers skills one level deep (skills/<name>/SKILL.md) and
        # also reads the ~/.claude/skills and ~/.agents/skills aliases; flatten the
        # <category>/ layer and add command-skills (v3.12.0 Phase 4).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "commands_subdir": "commands",
        "rules_subdir": "rules",
        "hooks_supported": False,
    }
