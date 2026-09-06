# Session History -- v2.3.0 Phase 7: Installer instruction-file parity

**Date**: 2026-05-29
**Plan**: [docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md](../../plans/adoption-ecc-cybersec-skills.md)
**Phase**: 7 of 9 -- [known-gaps] Installer instruction-file parity
**Sub-tasks**: T022 (DF-001), T023 (MT-2), T024 (MT-1), T025 (stabilization)
**Outcome**: All three v2.2.0 carryover items (DF-001, MT-1, MT-2) closed; the registry runner is now the single instruction-file renderer shared by both installers.

## Goal

Close the v2.2.0 installer-parity carryover gaps so the legacy bash / PowerShell instruction-file rendering blocks can be removed in favor of the Python integration registry runner, without changing end-user output.

## Pre-implementation findings (why this was bigger than a placeholder fix)

The Phase 1 review compared the legacy bash `render_template` (the end-user output today) against the Python registry runner and found three divergences, not one:

1. **Placeholders**: the bash path filled 15 `{{...}}` tokens + `{{SKILL_INDEX}}` + per-language coding snippets; the registry runner substituted only `{{PROJECT_NAME}}`, leaving 14+ tokens literal. This is the core DF-001 gap.
2. **Workspace path**: bash wrote claude / codex workspace instruction files at the PROJECT ROOT (`<ws>/CLAUDE.md`, `<ws>/AGENTS.md`); the registry wrote them nested under `.claude/` / `.codex/` -- where the tools do not read them.
3. **Gemini template**: bash rendered `base-gemini.md` (full instruction file); the registry pointed at `base-gemini-ide.md` (a static `@base-google-shared.md` import + 6-line IDE stub).

A literal "swap the calls" would have regressed end-user output (workspace instruction files would move out of the root; Gemini's full instructions would be replaced by a stub). The user chose the **reconcile-then-remove** path: fix the registry to match end-user output, prove parity with a test, then remove the legacy blocks.

A fourth divergence (the shared-marker block: the registry wraps the body in `<!-- NEXUS_HUB_START/END -->` for user-edit preservation, bash wrote raw) is the deliberate v2.2.0 improvement, so parity is asserted at the managed-body level, not the whole-file level.

## What was implemented

### T022 -- placeholder threading + path/template reconciliation

- `scripts/lib/integrations/base.py`:
    - `InstallContext` gained `languages: List[str]` and `instruction_only: bool`.
    - `MarkdownIntegration` gained `_DEFAULT_TEMPLATE_VARS` (the bash constant `sed` values), `_load_skill_index` (auto-loads `data/SKILL_INDEX.md`), `_effective_template_vars` (defaults <- skill index <- caller vars), and `_append_language_snippets` (mirrors the bash snippet-append loop). `_render` now substitutes the full merged map, leaves unknown tokens literal, and appends snippets.
    - `install_workspace` now resolves the instruction file under `instruction_workspace_dir` (default = `workspace_dir`); `SkillsIntegration.install_global` / `install_workspace` skip the catalog mirror when `ctx.instruction_only` is set.
- `scripts/lib/integrations/runner.py`: `install` gained `--var KEY=VALUE` (repeatable), `--languages`, `--instruction-only`; `print-config` gained `--var` / `--languages`; both build the context via shared `_template_vars_from_args` / `_languages_from_args` helpers.
- `claude.py` / `codex.py`: added `instruction_workspace_dir: ""` (project root).
- `gemini.py`: repointed `instruction_template` to `base-gemini.md`.
- `scripts/installer.sh::invoke_registry_platform` and `scripts/installer.ps1::Invoke-RegistryPlatform`: gained `languages` + `instruction_only` parameters and now thread the detected globals (PROJECT_NAME, PRIMARY_LANGUAGE, BUILD_CMD, OS_CONTEXT, ...) to the runner as `--var` pairs.

### T024 -- Copilot marker-merge (MT-1)

`CopilotIntegration.install_workspace` was rewritten to call `merge_marker_section(dst, rendered, legacy_header="## Nexus-Hub Harness")` and `track_shared`, replacing the bespoke append-after-heading flow. Re-installs now settle to `unchanged`; teardown removes only the marker block.

### Removal -- legacy block deletion

All six `render_template` (installer.sh) and `Render-Template` (installer.ps1) instruction-file calls for claude / codex / gemini, in both global and workspace scopes, were replaced by `invoke_registry_platform ... --instruction-only` / `Invoke-RegistryPlatform ... -InstructionOnly` (the surrounding `safe_folder_copy` / `Safe-Folder-Copy` catalog blocks were kept, since `--instruction-only` leaves the catalog mirror to them). Both dead render functions were deleted.

### T023 -- body-parity test (MT-2)

`tests/integrations/test_parity_with_legacy_installer.py` gained `test_instruction_body_parity_with_legacy_render`, parameterized over claude / codex / gemini x global + workspace. It installs each integration in isolation with the full placeholder set, extracts the marker-delimited body, and asserts byte equality against an INDEPENDENT naive-`str.replace` reference render (the bash-semantics oracle), plus a no-literal-placeholder completeness check. The independent oracle gives the test teeth: a regex bug, a missing `{{SKILL_INDEX}}` load, or a snippet-append whitespace drift in production would diverge from it.

## Deviations from a naive plan reading (all intended, user-approved)

- **Beneficial side effect**: threading vars through the shared `invoke_registry_platform` helper also fixed a latent literal-placeholder bug for the already-registry-driven platforms (cursor / opencode / antigravity / nexus-ai), whose instruction files previously shipped literal `{{...}}` tokens.
- **Multi-platform root AGENTS.md**: when both codex and cursor are installed to one workspace, they now share the root AGENTS.md marker block (last-writer-wins). The two templates (`base-codex.md`, `base-cursor.md`) differ by 2 lines, so this is cleaner than the prior bash behavior (which duplicated both near-identical bodies). The body-parity test installs each integration in isolation, so the collision never affects the assertion.
- **Marker format unchanged**: deliberately kept the default `<!-- NEXUS_HUB_START/END -->` markers (no per-platform markers) to preserve re-install idempotency for existing user installations.

## Testing results

- `tests/integrations` + `tests/installer` + `tests/validators`: **304 passed, 0 failed** (the one initial failure, `test_copilot_marker_block_settles_after_two_installs`, was a TEST-class issue -- it asserted Copilot's old bespoke `kept` behavior and was updated to the canonical `unchanged`).
- `catalog/hooks/tests`: 392 passed, 3 skipped.
- `make validate` equivalent: JSON catalogs + bundle audit (0 orphans) + quality pass (0 new warnings) + 4 CI validators (rc=0) all green.
- `make lint` (ShellCheck `--severity=warning` on installer.sh / install.sh): clean.
- `bash -n scripts/installer.sh` and PowerShell `Parser::ParseFile` on installer.ps1: both OK.

## CI/CD

GitHub Actions runs `pytest tests/integrations tests/installer` and `pytest tests/validators` (ubuntu-latest), which cover every changed Python module and the new parity test. No new test path, environment variable, or dependency was introduced, so no CI workflow edit was required.

## Known gaps

- Resolved this phase: DF-001, MT-1, MT-2 (see [known-gaps.md](../../known-gaps.md) Resolved table).
- New (low priority): DF-v23-3 -- `templates/ai-instructions/base-gemini-ide.md` is now orphaned as an instruction template (the gemini integration uses `base-gemini.md`); harmless, optional future cleanup.

## Next steps

- Phase 8 -- [known-gaps] Code-graph quality & extractor expansion (WN-1 / WN-5 / WN-6 / WN-7 / DF-002), under `extensions/nexus-code-search/`.
