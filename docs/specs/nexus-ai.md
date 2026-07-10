# Nexus-AI Capability Spec

**Integration key**: `nexus-ai`
**Distribution tier**: Full file-tree (extended, registry)
**Instruction merge mode**: `dedicated` (Nexus-Hub owns the whole instruction file)
**Hooks**: supported
**Permissions template**: `configs/permissions/claude-permissions.json`

Nexus-AI is the local-first desktop AI Studio that consumes this catalog (see `https://github.com/bendourthe/Nexus-AI`). It receives the full catalog as separate files and a fully Nexus-Hub-owned instruction file.

Nexus-AI reads its catalog from a single standardized, fixed-layout root with a machine-readable version manifest, the same way Claude Code reads `~/.claude/` and Codex reads `~/.codex/`, so the desktop app can display the installed version and detect when a newer release is published upstream. Nexus-AI should not maintain its own separate fetch path or version-scoped skill store; it reads this one location.

### Isolation boundary (why `catalog/`)

The catalog is installed into an isolated subtree -- `~/.nexus-ai/catalog/` -- never at the `~/.nexus-ai/` root. The root is the Nexus-AI app's own home (settings, MCP config, model weights, session artifacts, credentials vault); `catalog/` is the Nexus-Hub catalog the app pulls. Both populators -- this installer and Nexus-AI's own syncer -- write ONLY under `catalog/`, and a catalog refresh may wholesale wipe-and-refetch `catalog/` without any chance of touching irreplaceable app data. The version manifest lives inside `catalog/`, so a catalog wipe correctly resets the sync state.

## Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| App home (owned by Nexus-AI) | `~/.nexus-ai/` | `<project>/.nexus-ai/` |
| Catalog root (owned by Nexus-Hub) | `~/.nexus-ai/catalog/` | `<project>/.nexus-ai/catalog/` |
| Instruction file | `~/.nexus-ai/catalog/NEXUS_AI.md` | `<project>/.nexus-ai/catalog/NEXUS_AI.md` |

## Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | Full mirror including per-skill bundles. |
| `catalog/commands/` | `commands/` | Command surface. |
| `catalog/agents/` | `agents/` | Agent definitions. |
| `catalog/rules/` | `rules/` | Code-style and security rules. |
| `catalog/hooks/` | `hooks/` | Hook scripts. |
| `catalog/mcp-configs/` | `mcp-configs/` | MCP server registry (global scope only). |
| `templates/` | `templates/` | Documentation and AI-instruction templates (global scope only). |

## Version manifest

The install writes `~/.nexus-ai/catalog/nexus-hub-version.json` (and `<project>/.nexus-ai/catalog/nexus-hub-version.json` at workspace scope). It is the app's update-detection contract:

```json
{
  "product": "Nexus-Hub",
  "version": "3.11.3",
  "source_repo": "bendourthe/Nexus-Hub",
  "releases_url": "https://github.com/bendourthe/Nexus-Hub/releases",
  "latest_release_api": "https://api.github.com/repos/bendourthe/Nexus-Hub/releases/latest",
  "layout": {
    "skills": "skills",
    "commands": "commands",
    "agents": "agents",
    "rules": "rules",
    "hooks": "hooks",
    "mcp_configs": "mcp-configs",
    "templates": "templates",
    "instructions": "NEXUS_AI.md"
  }
}
```

- `version` is the installed catalog version, read from the single canonical source `.claude-plugin/plugin.json` (the same source `scripts/check_version_sync.py` enforces everywhere else).
- The desktop app compares `version` against the latest published release (via `latest_release_api`) to decide whether to prompt the user to update from inside the app.
- `layout` paths are relative to the manifest's own directory (the catalog root), so the app resolves each surface without hardcoding folder names.
- The file is deterministic (no timestamps, no absolute paths), so a re-install is a byte-identical no-op, and it is manifest-tracked so an uninstall removes it. Its absence at the catalog root is the "never synced" signal the app uses to drive the offline "not yet synced" state.

## Instruction file

- Template: `templates/ai-instructions/base-claude.md` (Nexus-AI reuses the Claude instruction template).
- Mode: `dedicated` -- unlike every other platform, Nexus-Hub owns `NEXUS_AI.md` end-to-end and rewrites it in full on install (it is not marker-merged). A re-install overwrites the file only when `overwrite` is set; otherwise an identical render is a no-op and a differing render is kept.
- Global file is `~/.nexus-ai/catalog/NEXUS_AI.md`; workspace file is `<project>/.nexus-ai/catalog/NEXUS_AI.md`.

## Quirks and notes

- Slash surface: yes (`commands/`).
- Hooks: supported (`hooks_supported = True`), reusing the Claude permissions template.
- `dedicated` mode is the key difference from Claude Code: because Nexus-AI is a Nexus-Hub-aligned studio, Nexus-Hub manages the whole instruction file rather than merging into a marker block.

## Source of truth

Mirrors `scripts/lib/integrations/nexus_ai.py` (`NexusAiIntegration`) and the `AGENTS.md` platform-coverage section (Nexus-AI is in the extended v2.2.0+ integration set).
