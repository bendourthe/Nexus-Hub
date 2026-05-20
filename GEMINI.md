# Gemini CLI Instructions — Nexus-Hub

This repository uses `AGENTS.md` at the repo root as the canonical source of project-specific AI agent guidance. The `@` import below inlines that file; read it in full before proposing changes.

@AGENTS.md

## Quick reference for Gemini / Antigravity

The highest-priority rules when working inside this repo (all detailed in AGENTS.md):

1. **Installer-aware changes**: every new file under `scripts/<name>.py` MUST be registered in BOTH `scripts/installer.sh` and `scripts/installer.ps1`. The installer copies scripts by explicit name, never by folder. Pattern to follow: the existing `generate_report.py` copy block.
2. **New skill** (`catalog/skills/<cat>/<name>/SKILL.md`): update `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`.
3. **New command** (`catalog/commands/<name>.md`): no registry update needed.
4. **Platform templates** (`templates/ai-instructions/base-*.md`): edit all five (claude/codex/cursor/gemini/opencode) in lockstep.
5. **Never edit `data/` files manually** except the three registry files in rule 2.
6. **Validate** after edits: `make validate`, `make lint`, and (for hooks) `make test`.

These rules apply only to work inside this repo.
