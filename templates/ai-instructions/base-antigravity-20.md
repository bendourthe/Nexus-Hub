@base-google-shared.md

## Surface: Antigravity 2.0 + CLI (Google) -- canonical post-2026-06-18 Google surface

This file is consumed by BOTH the Antigravity 2.0 desktop IDE and the Antigravity CLI (`agy`) that replaces Gemini CLI for non-enterprise users on 2026-06-18. The CLI shares the Antigravity 2.0 backend and on-disk conventions; a single integration covers both surfaces. On-disk conventions verified 2026-05-29 against Google's public Antigravity CLI docs + codelabs.

- Binary / invocation: `agy --help`, `agy -p '<prompt>'` (for the CLI surface); in-IDE chat panel (for the desktop surface). The CLI installs as `agy` (in `~/.local/bin/agy`), not `antigravity`.
- Instruction file: `agy` reads a project-root `AGENTS.md` (the open standard the Codex/AGENTS.md surface already manages). Nexus-Hub keeps its surface-specific copy at `.agents/AGENTS.md` to avoid clobbering that shared root block.
- Skills: `.agents/skills/*.md` (workspace) and `~/.gemini/antigravity-cli/skills/` (global) -- the Nexus-Hub installer mirrors `catalog/skills/` here automatically
- Workflows: `.agents/workflows/*.md` -- the Nexus-Hub installer mirrors `catalog/commands/` here automatically (Markdown; a workflow's name derives from its filename)
- Subagents: `.agents/subagents/` -- the Nexus-Hub installer mirrors `catalog/agents/` here automatically
- Hooks: supported (pre-commit, pre-tool-use, etc.) -- see the Antigravity hook docs
- Permissions: `configs/permissions/gemini-permissions.json` (shared with the Gemini surfaces -- the same trusted-domain allowlist applies)
