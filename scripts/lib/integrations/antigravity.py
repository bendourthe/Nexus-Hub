"""Google Antigravity integrations (1.0 IDE and 2.0 desktop + CLI).

Antigravity 1.0 (the original IDE released ahead of I/O 2026): customizations
live under the IDE's Customizations menu and on disk under
`~/.gemini/antigravity/`. Rules + Workflows.

Antigravity 2.0 + CLI (announced at Google I/O 2026; CLI transition announced
2026-05-21): standalone agent-first platform that ships a desktop IDE, a CLI,
and an SDK against a shared backend. All three surfaces use a `.agent/`
directory convention -- `~/.agent/` for global, `.agent/` for per-project --
with `AGENT.md` as the instruction file and `workflows/` for saved prompts.

The 2026-05-21 Google Developers Blog announcement transitioning Gemini CLI to
Antigravity CLI confirmed the CLI inherits the Antigravity 2.0 on-disk
conventions; therefore a single `Antigravity20Integration` class covers both
the desktop and the CLI. See docs/v2.2.0/antigravity-cli-probe.md for the full
probe and divergence analysis.
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
        "instruction_template": "templates/ai-instructions/base-antigravity-10.md",
        "skills_subdir": "skills",
        "commands_subdir": "global_workflows",
        "rules_subdir": "rules_library",
        "hooks_supported": False,
    }


class Antigravity20Integration(MarkdownIntegration, SkillsIntegration):
    """Covers both the Antigravity 2.0 desktop IDE and the Antigravity CLI.

    Per the 2026-05-21 Google Developers Blog announcement, the Antigravity CLI
    (transitioned from Gemini CLI ahead of the 2026-06-18 sunset) shares the
    Antigravity 2.0 backend and on-disk conventions: same `~/.agent/` global
    config dir, same `AGENT.md` instruction file, same `workflows/` / `skills/`
    / `subagents/` / `rules/` subdirectories. The probe at
    docs/v2.2.0/antigravity-cli-probe.md documents the convergence; no separate
    `AntigravityCliIntegration` class is required.
    """

    key = "antigravity2"
    display_name = "Antigravity 2.0 + CLI (Google)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.agent",
        "workspace_dir": ".agent",
        "instruction_file": "AGENT.md",
        "instruction_template": "templates/ai-instructions/base-antigravity-20.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "agents_subdir": "subagents",
        "rules_subdir": "rules",
        "hooks_supported": True,
        "permissions_file": "configs/permissions/gemini-permissions.json",
    }
