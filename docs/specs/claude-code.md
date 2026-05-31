# Claude Code Capability Spec

**Integration key**: `claude`
**Distribution tier**: Full file-tree (original 4, legacy copy block + registry subclass)
**Instruction merge mode**: `shared` (marker-merged; user content preserved across re-installs)
**Hooks**: supported
**Permissions template**: `configs/permissions/claude-permissions.json`

Claude Code (Anthropic) is the reference platform. It receives the full catalog as separate files plus a marker-merged instruction file.

## Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | `~/.claude/` | `<project>/.claude/` |
| Instruction file | `~/.claude/CLAUDE.md` | `<project>/CLAUDE.md` (project root) |

The workspace instruction file lands at the project root (not under `.claude/`) because `instruction_workspace_dir` is set to `""` -- that is the path Claude Code actually reads. The catalog subtrees still mirror under `.claude/`.

## Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | All 244 skills mirror verbatim, including per-skill `scripts/`, `references/`, `assets/`. |
| `catalog/commands/` | `commands/` | Surfaces as `/<name>` slash commands. |
| `catalog/agents/` | `agents/` | Agent definitions. |
| `catalog/rules/` | `rules/` | Code-style and security rules. |
| `catalog/hooks/` | `hooks/` | Hook scripts; honored via `settings.json` event wiring. |

## Instruction file

- Template: `templates/ai-instructions/base-claude.md`
- Mode: `shared` -- the render is merged into a Nexus-Hub marker block via `merge_marker_section`, so user edits above and below the block survive a re-install.
- Global file is `~/.claude/CLAUDE.md`; workspace file is `<project>/CLAUDE.md`.

## Project-local surfaces (`nexus-hub init`)

`ClaudeIntegration.wire_project_surfaces` writes a `.claude/settings.json` permissions stub when none exists, so a project picks up the recommended permission allowlist without a full workspace install.

## Quirks and notes

- Slash surface: yes (`commands/`).
- Hooks: supported -- `catalog/hooks/settings.json` drives `SessionStart` / `PreToolUse` / `PostToolUse` / `Stop` events.
- The instruction file is the only `shared` artifact; the catalog subtrees are tracked in the install manifest for clean teardown.

## Source of truth

Mirrors `scripts/lib/integrations/claude.py` (`ClaudeIntegration`) and the `AGENTS.md` platform-coverage table. Update this spec when that subclass's `config` changes.
