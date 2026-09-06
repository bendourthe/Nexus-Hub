# Session History -- v3.4.0 adoption-nessie-and-agency-agents Phase 2: Aider + Windsurf integrations

**Date**: 2026-06-14
**Plan**: [`docs/releases/v3/v3.4/plans/adoption-nessie-and-agency-agents.md`](../../plans/adoption-nessie-and-agency-agents.md)
**Phase**: 2 of 5 -- Aider + Windsurf integrations (A3, re-full)
**Branch**: `develop` (integration branch; no version tag cut this phase)
**Outcome**: complete; all Phase 2 sub-tasks closed and the Phase 2 exit checklist is satisfied.

## Goal

Extend Nexus-Hub's platform reach to Aider and Windsurf by adding two `IntegrationBase` subclasses, registered, installer-wired, and dry-run-verified. `re-full`, local file emission only: no new outbound call, dependency, credential, or third-party processor. The upstream `agency-agents` converter is named only in the reverse-engineering matrix, never in shipped code/comments/docs.

## Subtasks completed

1. **2.1 -- Study the registry pattern and define the two transforms.** Read `__init__.py::_register_builtins()`, `runner.py`, `result.py` (the `WriteResult` contract), `base.py` (`MarkdownIntegration` / `SkillsIntegration` / shared marker-merge), and the model subclasses `cursor.py` / `opencode.py` / `copilot.py` / `claude.py` / `codex.py` / `nexus_ai.py` / `gemini_cli.py` / `antigravity.py`. Wrote the design note [`docs/releases/v3/v3.4/development/2026-06-14_aider-windsurf-integration-design.md`](../2026-06-14_aider-windsurf-integration-design.md): both platforms are behavioral-guardrails surfaces modeled on `copilot.py` (a `MarkdownIntegration`, NOT `SkillsIntegration` -- they embed the `{{SKILL_INDEX}}` block rather than mirror the catalog tree), with the instruction file at the project root (`instruction_workspace_dir = ""`, the claude/codex pattern). Aider -> `CONVENTIONS.md` (no global Markdown surface); Windsurf -> `.windsurfrules` (workspace) + `~/.codeium/windsurf/memories/global_rules.md` (global, detect-then-skip).
2. **2.2 -- Implement and register Aider.** Created `scripts/lib/integrations/aider.py` (`AiderIntegration`, shared mode), writing project-root `CONVENTIONS.md` via the base `MarkdownIntegration.install_workspace`; `install_global` is overridden to a no-op-with-note (Aider has no standard global Markdown instruction file). Registered in `_register_builtins()`.
3. **2.3 -- Implement and register Windsurf.** Created `scripts/lib/integrations/windsurf.py` (`WindsurfIntegration`, shared mode), writing project-root `.windsurfrules` at workspace scope; `install_global` is overridden to write `~/.codeium/windsurf/memories/global_rules.md` via `merge_marker_section` when `~/.codeium` exists, and to skip-with-note when it does not (mirroring Copilot's VS-Code-dir detection). Registered in `_register_builtins()`.
4. **Installer wiring (full, per the Phase 2 decision).** Created `templates/ai-instructions/base-aider.md` and `base-windsurf.md` (modeled on `base-codex.md`; new platform templates, NOT edits to the core five, so the base-`*`.md lockstep rule does not apply). Wired both integrations into `scripts/installer.sh` (AIDER/WINDSURF sections in the global + workspace blocks, modeled on the `antigravity2` / `nexus-ai` blocks) and `scripts/installer.ps1` (provider-menu options 8/9, `Get-ProviderColor` entries, and the global + workspace `Invoke-RegistryPlatform` blocks).
5. **2.4 -- Docs + provenance.** Updated the `AGENTS.md` platform-coverage "Behavioral-guardrails only" bullet (added Aider + Windsurf with their surfaces); added a `re-full` platform-integration row to `docs/policy/mcp-reverse-engineering-matrix.md` (the only place `agency-agents` is named); added a CHANGELOG `[Unreleased]` "Added" entry.
6. **2.5 -- Testing and stabilization.** Added `tests/integrations/test_aider_windsurf.py` (8 cases: registration, behavioral-guardrails-not-skills-mirror classification, Aider workspace root write + global no-op-with-note, Windsurf workspace root write + global detect/skip). All gates green (see Test results).

## Key decisions

- **Full installer wiring (user-confirmed).** Registration in `_register_builtins()` alone would make the integrations reachable via `runner.py` and the dry-run `--check` (which auto-discovers all registered keys), but a normal `install` run would not deploy them (both installers use explicit per-key `invoke_registry_platform` / `Invoke-RegistryPlatform` calls, not a loop). The user chose full wiring so a normal install actually writes `CONVENTIONS.md` / `.windsurfrules`. Editing the installers is an AGENTS.md "ask first" surface, so the decision was confirmed before implementing.
- **Behavioral-guardrails, not a catalog mirror.** Both subclasses are `MarkdownIntegration` only (the `copilot.py` shape), embedding the `{{SKILL_INDEX}}` block in the single instruction file. Skills are discoverable through that index, matching how the comparison framed these as behavioral-guidance (not slash-command) surfaces.
- **Project-root instruction file via `instruction_workspace_dir = ""`.** `CONVENTIONS.md` and `.windsurfrules` are read from the repo root, so both reuse the claude/codex root-placement pattern; the base `MarkdownIntegration.install_workspace` handles it with no override.
- **Asymmetric global scope, reflecting reality.** Windsurf has a documented global-rules path (`~/.codeium/windsurf/memories/global_rules.md`), so its global install is meaningful (detect-then-skip on `~/.codeium`). Aider has no standard global Markdown surface (its global config is YAML, which Nexus-Hub does not touch), so its global install is an explicit no-op-with-note. Both decisions are documented in the design note and AGENTS.md.
- **Dedicated templates, not template reuse.** New `base-aider.md` / `base-windsurf.md` rather than reusing `base-opencode.md`, matching the established per-platform-template pattern (`gemini-cli`, the antigravity variants) and avoiding coupling to opencode's `skills/`-subdir footer.

## Test results

`make` is not on PATH on this Windows host (WN-v33-1), so the gate was emulated by invoking the validators, scanner, and pytest directly, and ShellCheck (also absent locally) was substituted with parser checks. All green:

- `tests/integrations/` (full): 231 passed in ~6m22s. Includes the parameterized contract suite (`test_contract.py`) auto-covering both new keys across all five lifecycle invariants (idempotent install, uninstall reverses install, sibling preservation, partial-state recovery, dry-run matches install) -- 10 cases for aider + windsurf, all pass.
- `tests/integrations/test_aider_windsurf.py` (new): 8 passed.
- `catalog/hooks/tests/` (hook suite): 439 passed, 7 skipped (no installer-edit regression).
- Dry-run install (`runner.py check --target <tmp>`, the command `installer.sh --check` invokes): all 12 integrations run with no `[error:...]`; `[check:aider] -> created:1` (project-root `CONVENTIONS.md`) and `[check:windsurf] -> created:1` (project-root `.windsurfrules`). "drift detected" is expected against a fresh dir.
- JSON integrity: `skills.json` 256 skills (catalog unchanged this phase). Orphan-bundle audit PASS, 0 errors (+ 1 pre-existing WN-v33-2 `.pyc` warning).
- `validate_no_personal_paths.py`: clean. `validate_unicode_safety.py`: 0 errors (the 1051 warnings are pre-existing legacy files; all six new/edited Phase 2 files scanned ASCII-clean). `check_version_sync.py`: all surfaces match canonical 3.3.4.
- Installer parse checks: `bash -n scripts/installer.sh` clean; `[System.Management.Automation.Language.Parser]::ParseFile` on `scripts/installer.ps1` reports 0 errors.

## CI/CD edits

Modified both installer scripts (`scripts/installer.sh`, `scripts/installer.ps1`) to wire the two integrations into the global + workspace install blocks (an AGENTS.md "ask first" surface; the change was user-confirmed and modeled on the existing extended-platform blocks). No GitHub Actions workflow change. ShellCheck is not on the local PATH (WN-v33-1); CI ShellChecks `installer.sh` on the ubuntu runner, and the bash/PowerShell edits were verified locally via `bash -n` and the PowerShell AST parser.

## Deviations

- **Installer edits beyond the literal sub-task text.** Sub-tasks 2.2/2.3 emphasize `_register_builtins()` registration and a dry-run `--check`; they do not explicitly enumerate installer install-block edits. Full wiring was added because the plan's GOAL ("extend platform reach") requires a normal install to actually deploy the files, and because the established extended-platform pattern (antigravity2/nexus-ai) wires each integration into both installers. Confirmed with the user first (the "ask first" installer surface).
- **Windsurf global path is bespoke.** Rather than a home-relative `global_dir` config (the generic `MarkdownIntegration.install_global` path), Windsurf overrides `install_global` to target `~/.codeium/windsurf/memories/global_rules.md` with detection, because that is the vendor-documented location and is not a simple instruction-dir.

## Known gaps

See [`docs/releases/v3/v3.4/known-gaps.md`](../../known-gaps.md). No new gaps introduced this phase. WN-v33-1 re-confirmed and updated to record that Phase 2 shipped `.sh`/`.ps1` edits verified by `bash -n` + the PowerShell AST parser (ShellCheck unavailable locally; CI runs it). DF-v34-1 and WN-v33-2 carried forward, untouched.

## Next steps

- **Phase 3 -- Extend session-query to Obsidian + exported history (A4, re-full)**: extend the `session-query` skill's bundled discovery + extraction helpers to parse Obsidian vaults and exported ChatGPT/Gemini history locally (with `.ps1` parity), preserving the zero-outbound invariant, then update SKILL.md + CHANGELOG and validate.
