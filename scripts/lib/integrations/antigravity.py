"""Google Antigravity integrations (1.0 IDE and 2.0 desktop + CLI).

Antigravity 1.0 (the original IDE released ahead of I/O 2026): customizations
live under the IDE's Customizations menu and on disk under
`~/.gemini/antigravity/`. Rules + Workflows.

Antigravity 2.0 + CLI (announced at Google I/O 2026; CLI transition announced
2026-05-21): standalone agent-first platform that ships a desktop IDE, a CLI
(`agy`), and an SDK against a shared backend. The surfaces use a `.agents/`
directory convention -- `.agents/` per-project for skills/workflows, `AGENTS.md`
as the project-root instruction file -- with the global CLI footprint under the
shared `~/.gemini/` family (CLI settings + global skills under
`~/.gemini/antigravity-cli/`).

These on-disk conventions were verified against Google's public Antigravity CLI
documentation and codelabs on 2026-05-29 (binary name `agy`; `.agents/skills/`
and `.agents/workflows/` as Markdown; project-root `AGENTS.md`); a single
`Antigravity20Integration` class still covers both the desktop and the CLI. See
docs/archive/v2/v2.2.0/antigravity-cli-probe.md for the full probe, the 2026-05-29 verified
findings, and the residual items still pending a live-VM smoke.
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
    """Covers both the Antigravity 2.0 desktop IDE and the Antigravity CLI (`agy`).

    The Antigravity CLI (transitioned from Gemini CLI ahead of the 2026-06-18
    sunset) shares the Antigravity 2.0 backend and on-disk conventions. Verified
    against Google's public Antigravity CLI docs + codelabs on 2026-05-29:

      - Binary: `agy` (installs to `~/.local/bin/agy`), not the inferred
        `antigravity`.
      - Per-project skills/workflows live under `.agents/` (`.agents/skills/`,
        `.agents/workflows/`) as Markdown files; a workflow's name derives from
        its filename and YAML frontmatter is honored.
      - The project-root instruction file is `AGENTS.md` -- the open standard the
        `codex` integration already manages, which `agy` reads. To avoid
        clobbering that shared root block (both integrations use the single
        `## Nexus-Hub` marker), this integration keeps its surface-specific copy
        under `.agents/AGENTS.md` rather than at the root.
      - Global CLI footprint is under `~/.gemini/antigravity-cli/`.

    Residual items still pending a live-VM `agy` smoke (recorded in
    docs/archive/v2/v2.2.0/antigravity-cli-probe.md and v2.3.0 known-gaps): one official
    codelab shows `.agent/` (singular); the exact global subpath varies across
    sources; the `subagents/` / `rules/` subdirs are unconfirmed; and whether
    `agy` requires the instruction file specifically at the project root (vs.
    also reading `.agents/AGENTS.md`) needs a per-marker scheme decision. No
    separate `AntigravityCliIntegration` class is required.
    """

    key = "antigravity2"
    display_name = "Antigravity 2.0 + CLI (Google)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.gemini/antigravity-cli",
        "workspace_dir": ".agents",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-antigravity-20.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "agents_subdir": "subagents",
        "rules_subdir": "rules",
        "hooks_supported": True,
        "permissions_file": "configs/permissions/gemini-permissions.json",
    }
