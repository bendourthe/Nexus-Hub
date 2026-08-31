"""Gemini (Google) integration -- the original Gemini Code Assist / Gemini IDE
extension flow that consumes GEMINI.md plus a .gemini/ workspace.

Note: this is distinct from the Gemini CLI (see gemini_cli.py) and from
Antigravity 1.0 / 2.0 (see antigravity.py). The IDE instruction surface is
verified at GEMINI.md. The extra .gemini skills, workflows, agents, and rules
mirrors are compatibility writes whose IDE discovery remains UNVERIFIED; do not
use their presence as release evidence.
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
        # AGENTS.md). An earlier static @-import stub diverged from the bash
        # output and has since been removed; using base-gemini.md closes the
        # template-divergence half of DF-001.
        "instruction_file": "GEMINI.md",
        "instruction_template": "templates/ai-instructions/base-gemini.md",
        # Skills are discovered one level deep (SKILL.md open standard); flatten
        # the <category>/ layer and add command-skills (v3.12.0 Phase 4).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "commands_subdir": "workflows",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_supported": False,
    }
