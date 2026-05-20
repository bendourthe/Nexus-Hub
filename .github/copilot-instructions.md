# GitHub Copilot Instructions — Nexus-Hub

This repository uses `AGENTS.md` at the repo root as the canonical source of project-specific AI agent guidance. Read it in full before proposing changes. Copilot cannot auto-import other files, so the essential rules are repeated below; the full workflow is in AGENTS.md.

## Golden rule: installer-aware changes

Nexus-Hub is a **template repository**. Nothing is "live" until a user runs `scripts/installer.sh` (macOS/Linux) or `scripts/installer.ps1` (Windows). The installer is what distributes changes to every supported platform (Claude Code, Cursor, Codex, Gemini/Antigravity, OpenCode, Copilot).

**Every change must be shaped so that after the next installer run, it reaches every supported platform on Windows, macOS, and Linux without any manual step on the user's part.**

## Quick reference

1. **New file under `scripts/<name>.{py,js}`**: MUST be registered in BOTH `scripts/installer.sh` (around line 1395, next to `generate_report.py`) AND `scripts/installer.ps1` (around line 1656). The installer copies scripts by explicit name, never by folder. Copy the pattern used for `generate_report.py`.

2. **New skill** (`catalog/skills/<cat>/<name>/SKILL.md`): update three registry files — `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`. The folder itself is auto-copied by the installer.

3. **New command** (`catalog/commands/<name>.md`): no registry update needed; the folder is auto-copied. If the command needs a style-guide reference, place it at `catalog/style-guides/<name>.md` (NOT in `catalog/commands/`, otherwise it surfaces as a slash command). The installer copies `catalog/style-guides/` to `~/.nexus-hub/style-guides/`.

4. **New hook** (`catalog/hooks/<name>.{sh,py}`): register in `catalog/hooks/settings.json`; write tests in `catalog/hooks/tests/`.

5. **Platform instruction templates** (`templates/ai-instructions/base-*.md`): edit all five (claude/codex/cursor/gemini/opencode) in lockstep. Any change must be platform-agnostic.

6. **Document template** (`templates/documentation/<name>.{docx,pptx,xlsx,...}`): folder auto-copied; no installer change needed.

7. **Never edit `data/*.json` manually** except the three registry files in rule 2.

8. **Never commit secrets.** The `secret-scan.sh` hook enforces this.

9. **Validate** after any change: `make validate` (JSON integrity), `make lint` (ShellCheck), `make test` (hook test suite). Run a dry-run installer when you touch installer code.

10. **Document** every user-visible change under `## [Unreleased]` in `CHANGELOG.md`.

## MCP Registry Policy

Nexus-Hub's MCP registry (`catalog/mcp-configs/mcp-servers.json`) is governed by a strict decision tree. When proposing a new entry, walk it in order and stop at the first bucket that fits:

1. **Local-only** (internal Nexus-Hub servers or zero-outbound Anthropic-official servers) - always allowed.
2. **LLM-native skill** (capability achievable by instructing the agent directly) - ship a skill, not an MCP.
3. **Reverse-engineer into a local internal MCP** - if the external project's logic can run locally, build the internal equivalent under `extensions/`. Strip external-source attribution; use generic descriptive names.
4. **Trusted vendor wrapper (your-own-account)** - acceptable only when the vendor is the intrinsic data destination, reverse-engineering isn't viable, AND the feature is extremely worth it. Justify all three in the `_comment`.
5. **Otherwise** - drop.

Hard no: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service. Full policy + 5-question audit in `AGENTS.md`. Matrix at `docs/v1.0.0/mcp-reverse-engineering-matrix.md`.

## Platform coverage caveat

The installer deploys skills, commands, agents, hooks, and rules as per-file trees only to Claude Code, Gemini/Antigravity, and Codex. Cursor, OpenCode, and Copilot receive behavioral guardrails only via their respective instruction files. New slash commands are not reachable as `/...` on those three platforms - note that explicitly in the CHANGELOG when adding one.

These rules apply only to work inside this repo.
