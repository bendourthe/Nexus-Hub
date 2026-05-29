"""OpenAI Codex integration.

Codex consumes the AGENTS.md open-standard instruction file, plus a skills/
directory and a prompts/ directory (the Codex equivalent of slash commands).
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class CodexIntegration(MarkdownIntegration, SkillsIntegration):
    key = "codex"
    display_name = "Codex (OpenAI)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.codex",
        "workspace_dir": ".codex",
        # Workspace AGENTS.md lands at the project root (the open-standard
        # location Codex / Cursor / OpenCode read), not under .codex/; skills/
        # and prompts/ still mirror under .codex/. Matches the legacy bash
        # installer (DF-001). When both Codex and Cursor are installed they
        # share the root AGENTS.md marker block (near-identical templates), which
        # is cleaner than the legacy bash path that duplicated both bodies.
        "instruction_workspace_dir": "",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-codex.md",
        "skills_subdir": "skills",
        "commands_subdir": "prompts",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/codex-permissions.json",
    }
