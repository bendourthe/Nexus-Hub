# Codex Capability Spec

**Integration key**: `codex`
**Distribution tier**: Full file-tree (original 4, legacy copy block + registry subclass)
**Instruction merge mode**: `shared` (marker-merged)
**Hooks**: not supported
**Permissions template**: `configs/permissions/codex-permissions.json`

Codex (OpenAI) receives the full catalog as separate files plus a marker-merged `AGENTS.md`.

## Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | `~/.codex/` | `<project>/.codex/` |
| Instruction file | `~/.codex/AGENTS.md` | `<project>/AGENTS.md` (project root) |

As with Claude Code, the workspace instruction file lands at the project root (`instruction_workspace_dir = ""`) because that is where Codex reads `AGENTS.md`; the catalog subtrees mirror under `.codex/`.

## Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | Full mirror including per-skill bundles. |
| `catalog/commands/` | `prompts/` | Surfaces as Codex prompts (the slash surface). |
| `catalog/agents/` | `agents/` | Agent definitions. |
| `catalog/rules/` | `rules/` | Code-style and security rules. |

There is no `hooks_subdir`: Codex does not honor Claude-style hooks.

## Instruction file

- Template: `templates/ai-instructions/base-codex.md`
- Mode: `shared` (marker-merged via `merge_marker_section`).
- Global file is `~/.codex/AGENTS.md`; workspace file is `<project>/AGENTS.md`.

## Quirks and notes

- Slash surface: yes, but commands install under `prompts/` (Codex's prompt convention), not `commands/`.
- Hooks: not supported (`hooks_supported = False`); no hook tree is copied.
- The `base-codex.md` template is shared verbatim with GitHub Copilot (Copilot reuses it as its instruction template).

## Source of truth

Mirrors `scripts/lib/integrations/codex.py` (`CodexIntegration`) and the `AGENTS.md` platform-coverage table.
