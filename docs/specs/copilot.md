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
| Catalog root | VS Code user-profile `prompts/` (slash surface) | `<project>/.github/` |
| Instruction file | not applicable (`global_dir = None`) | `<project>/.github/copilot-instructions.md` |
| Slash commands | `<vscode-user>/prompts/<name>.prompt.md` -> `/<name>` in Copilot Chat (any repo) | not applicable |

Copilot has no global INSTRUCTION file (`global_dir` is `None`), so the per-project `.github/copilot-instructions.md` carries the behavioral layer. It DOES have a global slash surface (v3.3.4+): a global install mirrors the catalog's commands into the VS Code user-profile `prompts/` dir as `<name>.prompt.md`, offered as `/<name>` in Copilot Chat from any repo.

## Distributed content

The workspace instruction file surfaces the catalog via the embedded `{{SKILL_INDEX}}` block (there is no `skills_subdir` / `commands_subdir` / `agents_subdir` / `rules_subdir` / `hooks_subdir` per-file copy). Additionally, a GLOBAL install mirrors the catalog's commands into the VS Code user-profile `prompts/` dir as `<name>.prompt.md` slash commands (v3.3.4+).

## Instruction file

- Template: `templates/ai-instructions/base-codex.md` (Copilot reuses the Codex instruction template).
- Mode: `shared` (marker-merged via `merge_marker_section`).
- Location: `<project>/.github/copilot-instructions.md`.

## Quirks and notes

- Slash surface: YES (global). A global install mirrors catalog commands into the VS Code user-profile `prompts/` dir as `<name>.prompt.md`, invoked as `/<name>` in Copilot Chat from any repo (requires the `chat.promptFiles` setting, on by default). The per-project `.github/copilot-instructions.md` is the behavioral layer, not a slash surface.
- Hooks: not supported.
- Because Copilot reuses `base-codex.md`, any edit to that template affects both Codex and Copilot -- keep it platform-agnostic.

## Source of truth

Mirrors `scripts/lib/integrations/copilot.py` (`CopilotIntegration`) and the `AGENTS.md` platform-coverage section (Copilot receives behavioral guardrails via `.github/copilot-instructions.md` rather than a full file-tree copy).
