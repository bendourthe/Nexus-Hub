# Gemini Capability Spec

**Integration keys**: `gemini` (IDE / Antigravity 1.0 backend), `gemini-cli` (standalone CLI)
**Distribution tier**: `gemini` is original 4 (legacy copy block + registry subclass); `gemini-cli` is extended and ENTERPRISE-ONLY post-2026-06-18
**Instruction merge mode**: `shared` (marker-merged)
**Hooks**: not supported
**Permissions template**: `configs/permissions/gemini-permissions.json`

Gemini (Google) is covered by two integration keys: the mainline `gemini` integration and the standalone `gemini-cli` integration. They share the `~/.gemini/` root and the `GEMINI.md` instruction filename but render from different templates.

## `gemini` (mainline)

### Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | `~/.gemini/` | `<project>/.gemini/` |
| Instruction file | `~/.gemini/GEMINI.md` | `<project>/.gemini/GEMINI.md` |

### Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | Full mirror. |
| `catalog/commands/` | `workflows/` | Surfaces as Gemini workflows (the slash surface). |
| `catalog/agents/` | `agents/` | Agent definitions. |
| `catalog/rules/` | `rules/` | Code-style and security rules. |

- Template: `templates/ai-instructions/base-gemini.md`; mode `shared`.

## `gemini-cli` (standalone CLI)

The standalone Gemini CLI integration is opt-in via the installer's `--enterprise` flag (Bash: `scripts/installer.sh --enterprise`; PowerShell: `scripts/installer.ps1 -Enterprise`).

### Install surface and content

| Aspect | Value |
|--------|-------|
| Catalog root (global / workspace) | `~/.gemini/` / `<project>/.gemini/` |
| Instruction file | `GEMINI.md` |
| Template | `templates/ai-instructions/base-gemini-cli.md` |
| Skills | `skills/` |
| Agents | `subagents/` is NOT used here; agents mirror to `agents/` |
| Rules | `rules/` |

The `gemini-cli` config declares no `commands_subdir`, so it does not install a slash-command surface of its own.

## Quirks and notes

- **Gemini CLI sunset**: per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18. After that date `gemini-cli` installs only when the user passes `--enterprise` (requires a paid Gemini API key). Non-enterprise users transition to Antigravity CLI (see [antigravity.md](antigravity.md)).
- Slash surface: yes for `gemini` (`workflows/`); `gemini-cli` ships no command surface.
- Hooks: not supported for either key.

## Source of truth

Mirrors `scripts/lib/integrations/gemini.py` (`GeminiIntegration`) and `scripts/lib/integrations/gemini_cli.py` (`GeminiCliIntegration`), plus the Gemini CLI sunset note in the `AGENTS.md` platform-coverage section.
