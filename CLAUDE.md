# Claude Code Instructions -- Nexus-Hub

This repository uses `AGENTS.md` at the repo root as the canonical source of project-specific AI agent guidance. The `@` import below inlines that file so it is always in context; read it in full before proposing changes.

@AGENTS.md

## Quick reference for Claude Code

Highest-priority rules when working inside this repo (these all trace back to the full rules in AGENTS.md):

1. **Installer-aware changes**: every new file under `scripts/<name>.py` MUST be registered in BOTH `scripts/installer.sh` and `scripts/installer.ps1`. The installer copies scripts by explicit name, never by folder. Model after the existing `generate_report.py` copy block. See the "Installer-Aware Changes (Cross-Platform)" section in AGENTS.md.
2. **New skill** (`catalog/skills/<cat>/<name>/SKILL.md`): must update `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`.
3. **New command** (`catalog/commands/<name>.md`): no registry update needed. If the command needs a style-guide reference, place it at `catalog/style-guides/<name>.md` (NOT in `catalog/commands/`, otherwise it surfaces as a slash command). The installer copies `catalog/style-guides/` to `~/.nexus-hub/style-guides/`.
4. **Platform templates** (`templates/ai-instructions/base-*.md`): edit all five (claude/codex/cursor/gemini/opencode) in lockstep -- changes must be platform-agnostic. Seven more substantive templates exist; a companion validator covers them.
5. **Never edit `data/` files manually** except the three registry files in rule 2.
6. **Validate** after edits: `make validate`, `make lint`, and (for hooks) `make test`.
7. **Plan lifecycle**: every phase ends with one LOCAL commit; only a plan's final phase pushes, opens the integration PR, and reconciles CI/CD. See the AGENTS.md branching section.

These rules apply **only to work inside this repo**. They do not override any global CLAUDE.md instructions for other projects.
