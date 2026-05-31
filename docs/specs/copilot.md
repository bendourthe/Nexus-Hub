# GitHub Copilot Capability Spec

**Integration key**: `copilot`
**Distribution tier**: Behavioral guardrails only (original 4)
**Instruction merge mode**: `shared` (marker-merged)
**Hooks**: not supported
**Permissions template**: `configs/permissions/copilot-permissions.json`

GitHub Copilot (Microsoft) does not receive a full per-file catalog copy. It is configured through a single behavioral-guardrails instruction file; the Nexus-Hub skill catalog reaches Copilot via the `{{SKILL_INDEX}}` block embedded in that file rather than as separate skill files.

## Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | not applicable (`global_dir = None`) | `<project>/.github/` |
| Instruction file | not applicable | `<project>/.github/copilot-instructions.md` |

Copilot has no global install: `global_dir` is `None`, so it is configured per-project under `.github/`.

## Distributed content

None as separate files. There is no `skills_subdir` / `commands_subdir` / `agents_subdir` / `rules_subdir` / `hooks_subdir`: the catalog is surfaced only through the embedded skill index in `copilot-instructions.md`.

## Instruction file

- Template: `templates/ai-instructions/base-codex.md` (Copilot reuses the Codex instruction template).
- Mode: `shared` (marker-merged via `merge_marker_section`).
- Location: `<project>/.github/copilot-instructions.md`.

## Quirks and notes

- Slash surface: no. Copilot has no slash-command surface; users invoke a command only by pasting its body.
- Hooks: not supported.
- Because Copilot reuses `base-codex.md`, any edit to that template affects both Codex and Copilot -- keep it platform-agnostic.

## Source of truth

Mirrors `scripts/lib/integrations/copilot.py` (`CopilotIntegration`) and the `AGENTS.md` platform-coverage section (Copilot receives behavioral guardrails via `.github/copilot-instructions.md` rather than a full file-tree copy).
