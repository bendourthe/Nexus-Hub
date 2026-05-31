# Cursor Capability Spec

**Integration key**: `cursor`
**Distribution tier**: Behavioral guardrails only
**Instruction merge mode**: `shared` (marker-merged)
**Hooks**: not supported

Cursor is configured through a behavioral-guardrails instruction file plus a project-local `.mdc` rule. It does not receive the full per-file catalog tree (no skills / commands / agents / hooks mirror); rules are the one catalog subtree it carries.

## Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | not applicable (`global_dir = None`) | `<project>/.cursor/` |
| Instruction file | not applicable | `<project>/.cursor/AGENTS.md` |

Cursor has no global install (`global_dir = None`); it is configured per-project under `.cursor/`.

## Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/rules/` | `rules/` | Code-style and security rules (the only mirrored subtree). |

There is no `skills_subdir` / `commands_subdir` / `agents_subdir` / `hooks_subdir`: the skill catalog reaches Cursor via the embedded skill index in its instruction file.

## Instruction file

- Template: `templates/ai-instructions/base-cursor.md`
- Mode: `shared` (marker-merged).
- Location: `<project>/.cursor/AGENTS.md`.

## Project-local surfaces (`nexus-hub init`)

`CursorIntegration.wire_project_surfaces` writes `.cursor/rules/nexus-hub.mdc` (a Markdown-plus-YAML-frontmatter rule built by the `YamlIntegration` `.mdc` convention), so a project picks up the Nexus-Hub Cursor rule without a full workspace install.

## Quirks and notes

- Slash surface: no.
- Hooks: not supported.
- Cursor reads both the repo-root `AGENTS.md` and `.cursor/rules/*.mdc`; the integration writes the `.cursor/AGENTS.md` instruction file and the `.mdc` rule.

## Source of truth

Mirrors `scripts/lib/integrations/cursor.py` (`CursorIntegration`) and the `AGENTS.md` platform-coverage section (Cursor: `.cursor/rules/*.mdc` + repo-root `AGENTS.md`).
