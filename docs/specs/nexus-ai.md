# Nexus-AI Capability Spec

**Integration key**: `nexus-ai`
**Distribution tier**: Full file-tree (extended, registry)
**Instruction merge mode**: `dedicated` (Nexus-Hub owns the whole instruction file)
**Hooks**: supported
**Permissions template**: `configs/permissions/claude-permissions.json`

Nexus-AI is the local-first desktop AI Studio that consumes this catalog (see `https://github.com/bendourthe/Nexus-AI`). It receives the full catalog as separate files and a fully Nexus-Hub-owned instruction file.

## Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | `~/.nexus-ai/` | `<project>/.nexus-ai/` |
| Instruction file | `~/.nexus-ai/NEXUS_AI.md` | `<project>/.nexus-ai/NEXUS_AI.md` |

## Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | Full mirror including per-skill bundles. |
| `catalog/commands/` | `commands/` | Command surface. |
| `catalog/agents/` | `agents/` | Agent definitions. |
| `catalog/rules/` | `rules/` | Code-style and security rules. |
| `catalog/hooks/` | `hooks/` | Hook scripts. |

## Instruction file

- Template: `templates/ai-instructions/base-claude.md` (Nexus-AI reuses the Claude instruction template).
- Mode: `dedicated` -- unlike every other platform, Nexus-Hub owns `NEXUS_AI.md` end-to-end and rewrites it in full on install (it is not marker-merged). A re-install overwrites the file only when `overwrite` is set; otherwise an identical render is a no-op and a differing render is kept.
- Global file is `~/.nexus-ai/NEXUS_AI.md`; workspace file is `<project>/.nexus-ai/NEXUS_AI.md`.

## Quirks and notes

- Slash surface: yes (`commands/`).
- Hooks: supported (`hooks_supported = True`), reusing the Claude permissions template.
- `dedicated` mode is the key difference from Claude Code: because Nexus-AI is a Nexus-Hub-aligned studio, Nexus-Hub manages the whole instruction file rather than merging into a marker block.

## Source of truth

Mirrors `scripts/lib/integrations/nexus_ai.py` (`NexusAiIntegration`) and the `AGENTS.md` platform-coverage section (Nexus-AI is in the extended v2.2.0+ integration set).
