"""Gemini (Google) integration -- the original Gemini Code Assist / Gemini IDE
extension flow that consumes GEMINI.md plus a .gemini/ workspace.

Note: this is distinct from the Gemini CLI (see gemini_cli.py) and from
Antigravity 1.0 / 2.0 (see antigravity.py). The three share the .gemini/ root
but write to different subdirectories.
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class GeminiIntegration(MarkdownIntegration, SkillsIntegration):
    key = "gemini"
    display_name = "Gemini (Google)"
    # `~/.gemini/GEMINI.md` is shared with Gemini CLI (gemini_cli.py); use
    # shared marker mode so both integrations can coexist without clobbering.
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.gemini",
        "workspace_dir": ".gemini",
        # base-gemini.md is the canonical, fully-templated GEMINI.md the legacy
        # bash installer renders (and one of the five lock-step base templates in
        # AGENTS.md). The earlier base-gemini-ide.md was a static @-import stub
        # that diverged from the bash output; using base-gemini.md closes the
        # template-divergence half of DF-001.
        "instruction_file": "GEMINI.md",
        "instruction_template": "templates/ai-instructions/base-gemini.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/gemini-permissions.json",
    }
