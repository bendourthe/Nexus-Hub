@base-google-shared.md

## Surface: Antigravity 2.0 + CLI (Google) -- canonical post-2026-06-18 Google surface

This file is consumed by BOTH the Antigravity 2.0 desktop IDE and the Antigravity CLI (`agy`) that replaces Gemini CLI for non-enterprise users on 2026-06-18. The CLI shares the Antigravity 2.0 backend and on-disk conventions; a single integration covers both surfaces. On-disk conventions verified 2026-05-29 against Google's public Antigravity CLI docs + codelabs.

- Binary / invocation: `agy --help`, `agy -p '<prompt>'` (for the CLI surface); in-IDE chat panel (for the desktop surface). The CLI installs as `agy` (in `~/.local/bin/agy`), not `antigravity`.
- Instruction file: `agy` reads a project-root `AGENTS.md` (the open standard the Codex/AGENTS.md surface already manages). Nexus-Hub keeps its surface-specific copy at `.agents/AGENTS.md` to avoid clobbering that shared root block.
- Skills: flat folder-per-skill `.agents/skills/<skill-name>/SKILL.md` (workspace). Global install writes to BOTH `~/.gemini/antigravity/skills/` (the IDE root) and `~/.gemini/antigravity-cli/skills/` (the `agy` CLI root). The Nexus-Hub installer flattens `catalog/skills/<category>/<name>/` to the flat `skills/<name>/` layout Antigravity discovers (a category-nested copy is invisible to the IDE).
- Workflows: `.agents/workflows/<name>.md` (and the same under both global roots) -- the Nexus-Hub installer mirrors `catalog/commands/` here verbatim. A workflow is invoked as the slash command `/<name>` (name derives from the filename).
- Subagents: `.agents/subagents/` (and both global roots) -- the Nexus-Hub installer mirrors `catalog/agents/` here automatically.
- Hooks: `.agents/hooks.json` registers a curated, platform-agnostic set (secret-scan, large-file-guard, git-guardrails, and the opt-in context-compressor) whose scripts the installer places under `.agents/hooks/`. The schema is keyed by named hook groups (each with an `enabled` flag) using Claude-compatible events (PreToolUse/PostToolUse/SessionStart/Stop) and `matcher` regexes. On Windows the `.sh` hooks need a Unix shell (git-bash), same as the Claude hooks.
- Permissions: `configs/permissions/gemini-permissions.json` (shared with the Gemini surfaces -- the same trusted-domain allowlist applies)
