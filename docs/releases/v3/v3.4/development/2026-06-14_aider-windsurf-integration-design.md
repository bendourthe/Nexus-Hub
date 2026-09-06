# Design Note - Aider + Windsurf integrations (v3.4.0 Phase 2, sub-task 2.1)

**Date**: 2026-06-14
**Plan**: [`../plans/adoption-nessie-and-agency-agents.md`](../plans/adoption-nessie-and-agency-agents.md) Phase 2 (A3, re-full)
**Scope**: Two new `IntegrationBase` subclasses extending Nexus-Hub's platform reach to Aider and Windsurf. Pure local file emission, zero new outbound call / dependency / credential. The upstream comparison source is named only in the reverse-engineering matrix, never in shipped code/comments/docs (Reverse-Engineering Attribution Rule).

## Pattern study (existing subclasses)

- `scripts/lib/integrations/base.py` - `MarkdownIntegration` renders an instruction template, substitutes `{{TOKEN}}` placeholders (including the multi-line `{{SKILL_INDEX}}` loaded from `data/SKILL_INDEX.md`), and writes it. In `shared` mode it routes the write through `merge_marker_section`, so user content above/below the Nexus-Hub marker block survives a re-install; teardown calls `remove_marker_section`, which deletes a file whose only content was the block (so a freshly-created instruction file fully reverses on uninstall - the contract suite's `test_uninstall_reverses_install` invariant).
- `instruction_workspace_dir` defaults to `workspace_dir`; `claude`/`codex` set it to `""` so the instruction file lands at the project root (where those tools read it). Aider's `CONVENTIONS.md` and Windsurf's `.windsurfrules` are both project-root files, so both set `instruction_workspace_dir = ""`.
- Closest model: `copilot.py` - a `MarkdownIntegration` (NOT `SkillsIntegration`): behavioral-guardrails surface, one rendered instruction file with the `{{SKILL_INDEX}}` block embedded, no catalog file-tree mirror, and a bespoke `install_global` that detects the tool's user dir and skips-with-note when absent.

## Transform per platform

### Aider -> `CONVENTIONS.md` (project root)

- **Surface type**: behavioral-guidance file (NOT a slash-command surface). Aider reads a project-root `CONVENTIONS.md` when the user references it from `.aider.conf.yml` (`read: CONVENTIONS.md`).
- **Workspace (project-local) path**: `<project>/CONVENTIONS.md` via `instruction_workspace_dir = ""`.
- **Global path**: none. Aider has no standard global Markdown instruction file (its global surface is the YAML `~/.aider.conf.yml`, which Nexus-Hub does not generate/modify). `global_dir = None`; `install_global` returns an explanatory note and writes nothing.
- **Content emitted**: rendered `templates/ai-instructions/base-aider.md` (Nexus-Hub instruction content + `{{SKILL_INDEX}}` block), `shared` mode (marker-merged so user edits survive).
- **Closest model to copy**: `copilot.py` (MarkdownIntegration-only) + `codex.py` (`instruction_workspace_dir = ""` root placement).

### Windsurf -> `.windsurfrules` (project root) + global rules

- **Surface type**: behavioral-guidance file (NOT a slash-command surface).
- **Workspace (project-local) path**: `<project>/.windsurfrules` via `instruction_workspace_dir = ""`.
- **Global path**: `~/.codeium/windsurf/memories/global_rules.md` (Windsurf's documented global-rules location). `global_dir = None` (the path is bespoke, not a simple home-relative instruction dir), so `install_global` is overridden to write `global_rules.md` when `~/.codeium` exists and skip-with-note when it does not (Windsurf not detected), mirroring Copilot's VS-Code-dir detection.
- **Content emitted**: rendered `templates/ai-instructions/base-windsurf.md` (Nexus-Hub instruction content + `{{SKILL_INDEX}}` block), `shared` mode.
- **Closest model to copy**: `copilot.py` (bespoke detect-then-skip `install_global`) + `codex.py` (root instruction file).

## Templates

New dedicated templates `templates/ai-instructions/base-aider.md` and `templates/ai-instructions/base-windsurf.md`, modeled on `base-codex.md` / `base-opencode.md`. These are NEW platform templates, not edits to the core five (`claude`/`codex`/`cursor`/`gemini`/`opencode`), so the AGENTS.md base-`*`.md lockstep rule does not apply (the same precedent that gave `gemini-cli` and the antigravity variants their own templates). The `templates/` tree is copied recursively by both installers, so no installer copy-block edit is needed for the templates themselves.

## Registration + installer wiring

- Both subclasses are registered in `scripts/lib/integrations/__init__.py::_register_builtins()` (the mandatory step; the file alone does nothing without it). Registration auto-enrolls them in the parameterized contract suite (`tests/integrations/test_contract.py`) and in `runner.py check` (so `installer.sh --check` / `installer.ps1 -Check` dry-runs them).
- Per the Phase 2 decision (full wiring), explicit `invoke_registry_platform` (bash) / `Invoke-RegistryPlatform` (PowerShell) calls are added to BOTH installers' global and workspace blocks, modeled on the existing `antigravity2` / `nexus-ai` blocks, so a normal install actually deploys the files.

## Constraints honored

- Zero outbound calls, zero new dependencies, zero credentials - both subclasses are pure stdlib `pathlib`/`shutil` file emission via the existing base helpers.
- ASCII-only across code, templates, and docs.
- No upstream repo named in any shipped artifact; provenance recorded only in `docs/policy/mcp-reverse-engineering-matrix.md`.
