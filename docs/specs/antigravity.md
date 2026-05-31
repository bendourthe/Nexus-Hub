# Antigravity Capability Spec

**Integration keys**: `antigravity` (Antigravity 1.0), `antigravity2` (Antigravity 2.0 + CLI)
**Distribution tier**: 1.0 is original 4 (Gemini / Antigravity 1.0 legacy block); 2.0 + CLI is extended (registry)
**Instruction merge mode**: `shared` (marker-merged) for both
**Hooks**: 1.0 not supported; 2.0 supported
**Permissions template (2.0)**: `configs/permissions/gemini-permissions.json`

Antigravity (Google) is covered by two integration keys spanning two product generations. Both live under the `~/.gemini/` family of roots.

## `antigravity` (Antigravity 1.0)

### Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | `~/.gemini/antigravity/` | `<project>/.gemini/antigravity/` |
| Instruction file | `rules.md` | `rules.md` |

### Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | Full mirror. |
| `catalog/commands/` | `global_workflows/` | Workflow surface. |
| `catalog/rules/` | `rules_library/` | Code-style and security rules. |

- Template: `templates/ai-instructions/base-antigravity-10.md`; mode `shared`.
- No `agents_subdir` and `hooks_supported = False`.

## `antigravity2` (Antigravity 2.0 + CLI)

The 2.0 integration covers both the desktop IDE and the `agy` CLI (they share a backend per the 2026-05-21 announcement).

### Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | `~/.gemini/antigravity-cli/` | `<project>/.agents/` |
| Instruction file | `AGENTS.md` | `AGENTS.md` |

### Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | Full mirror. |
| `catalog/commands/` | `workflows/` | Markdown workflows. |
| `catalog/agents/` | `subagents/` | Agent definitions land under `subagents/`. |
| `catalog/rules/` | `rules/` | Code-style and security rules. |

- Template: `templates/ai-instructions/base-antigravity-20.md`; mode `shared`.
- `hooks_supported = True`; permissions template `configs/permissions/gemini-permissions.json`.

## Quirks and notes

- The CLI binary is `agy` and uses the `.agents/` per-project convention with global content under `~/.gemini/antigravity-cli/`, verified 2026-05-29 against Google's public Antigravity CLI docs.
- Antigravity CLI is the transition target for Gemini CLI users before the 2026-06-18 sunset (see [gemini.md](gemini.md)).
- Four documentation-verified-but-not-live-verified residuals remain (the `.agent/` vs `.agents/` codelab dissent, the exact global subpath, the `subagents/` / `rules/` subdirs, and whether `agy` requires a root `AGENTS.md`); they are tracked in `docs/v2.2.0/antigravity-cli-probe.md` and v2.3.0 known-gaps WN-v23-5.

## Source of truth

Mirrors `scripts/lib/integrations/antigravity.py` (`Antigravity10Integration`, `Antigravity20Integration`), the `AGENTS.md` platform-coverage section, and `docs/v2.2.0/antigravity-cli-probe.md`.
