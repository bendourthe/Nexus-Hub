@base-google-shared.md

## Surface: Antigravity 2.0 + CLI (Google) -- canonical post-2026-06-18 Google surface

This file deploys to `~/.agent/AGENT.md` (global) or `<project>/.agent/AGENT.md` (workspace) and is consumed by BOTH the Antigravity 2.0 desktop IDE and the Antigravity CLI binary that replaces Gemini CLI for non-enterprise users on 2026-06-18. Per the 2026-05-21 Google Developers Blog announcement, the CLI shares the Antigravity 2.0 backend and on-disk conventions; a single integration covers both surfaces.

- Binary / invocation: `antigravity --help`, `antigravity -p '<prompt>'`, `antigravity init` (for the CLI surface); in-IDE chat panel (for the desktop surface)
- Subagents: `~/.agent/subagents/` -- the Nexus-Hub installer mirrors `catalog/agents/` here automatically
- Workflows: `~/.agent/workflows/` -- the Nexus-Hub installer mirrors `catalog/commands/` here automatically
- Hooks: supported (pre-commit, pre-tool-use, etc.) -- see `~/.agent/hooks/` and the Antigravity 2.0 hook docs
- Permissions: `configs/permissions/gemini-permissions.json` (shared with the Gemini surfaces -- the same trusted-domain allowlist applies)
