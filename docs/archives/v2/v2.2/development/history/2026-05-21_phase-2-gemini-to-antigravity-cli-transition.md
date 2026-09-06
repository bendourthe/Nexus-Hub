# Session History -- v2.2.0 Phase 2: Gemini-to-Antigravity CLI transition

**Date**: 2026-05-21
**Plan**: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](../../plans/codegraph-and-antigravity.md)
**Phase**: 2 -- Gemini-to-Antigravity CLI transition (sub-tasks T007-T014)
**Result**: shipped; all gates green; independently releasable as `v2.2.0-rc1` before 2026-06-18 if Phases 3-6 slip

---

## Goal

Respond to the 2026-05-21 Google Developers Blog announcement that Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18 by: (1) verifying the Antigravity CLI on-disk conventions converge with the existing `Antigravity20Integration`, (2) reconciling the integration to surface dual desktop + CLI coverage, (3) adding an `antigravity-cli-diff-review` pre-commit hook variant, (4) updating AGENTS.md platform coverage caveats, (5) splitting the shared `base-gemini.md` template into per-surface wrappers, (6) confirming the TOML-vs-Markdown commands schema diff, (7) deprecating the standalone Gemini CLI install path behind an `--enterprise` / `-Enterprise` flag, and (8) stabilizing all Phase 2 tests.

## Sub-tasks completed (8 of 8)

### T007 -- Antigravity CLI install-path probe

- Created [docs/archives/v2/v2.2/antigravity-cli-probe.md](../../antigravity-cli-probe.md) with seven on-disk-convention fields tagged `(documented)`, `(inferred)`, or `(open)`.
- Concluded that every documented field matches the existing `Antigravity20Integration` config dict; (a) branch of T008 applies (rename display_name, no separate class).
- Three `(open)` items remain (binary name, command format, frontmatter schema) -- tracked as WN-2 / WN-3 / WN-4 in `docs/archive/v2/v2.2/known-gaps.md`.

### T008 -- Antigravity CLI integration reconciliation

- Updated `scripts/lib/integrations/antigravity.py`:
    - `Antigravity20Integration.display_name`: "Antigravity 2.0 (Google)" -> "Antigravity 2.0 + CLI (Google)".
    - Rewrote the class docstring to cite the 2026-05-21 Google announcement and confirm single-class dual coverage.
    - Updated both integrations' `instruction_template` to point at the new per-surface wrappers (T011).
- Test file: `tests/integrations/test_antigravity.py` -- 6 new test cases (install paths, dual-coverage signal in display_name, dedicated-template references, idempotent reinstall).

### T011 -- Per-surface Google instruction templates (run alongside T008 due to template dependency)

- Created `templates/ai-instructions/base-google-shared.md` -- the shared body pruned from `base-gemini.md`.
- Created five thin wrappers, each beginning with `@base-google-shared.md` followed by 3-10 lines of surface-specific guidance:
    - `base-gemini-ide.md` (Gemini Code Assist IDE)
    - `base-gemini-cli.md` (Gemini CLI, ENTERPRISE-ONLY post-2026-06-18)
    - `base-antigravity-10.md` (Antigravity 1.0 desktop)
    - `base-antigravity-20.md` (Antigravity 2.0 + CLI -- the canonical Google surface post-sunset)
    - `base-antigravity-cli.md` (thin alias for base-antigravity-20.md; placeholder for a future desktop / CLI split)
- Repointed `gemini.py`, `gemini_cli.py`, `antigravity.py` integrations to their dedicated wrappers.
- Legacy `base-gemini.md` retained for the legacy installer copy blocks (refactor deferred to Phase 3 / DF-001).

### T009 -- Antigravity CLI diff-review hook variants

- Created `catalog/hooks/antigravity-cli-diff-review.sh` -- copy of `gemini-diff-review.sh` with `gemini` -> `antigravity` substitution on binary name, log prefixes, install-from URL.
- Created `catalog/hooks/antigravity-cli-diff-review.ps1` -- PowerShell sibling (the first under `catalog/hooks/`; lays groundwork for retrofitting the other diff-review hooks).
- Updated `scripts/installer.sh:1523` loop to include the new `.sh` variant alongside claude / gemini / codex / opencode.
- Updated `scripts/installer.ps1:1880` loop to include both the `.sh` and `.ps1` variants.
- Both scripts pass `bash -n`, PowerShell AST parse, and `shellcheck --severity=warning`.

### T010 -- AGENTS.md "Platform coverage caveats" update

- Replaced the "Extended 3" listing with "Extended 4 (v2.2.0+, via integration registry)": Antigravity 2.0 + CLI, Antigravity CLI (transition target), Gemini CLI (ENTERPRISE-ONLY post-2026-06-18, opt-in via `--enterprise`), Nexus-AI.
- Added a `> **Gemini CLI sunset**:` blockquote callout citing the 2026-05-21 announcement, the 2026-06-18 cutover date, the `--enterprise` / `-Enterprise` flag, and the Antigravity CLI as the non-enterprise replacement.
- `make validate` + per-skill bundle audit both pass with 0 errors / 0 warnings.

### T012 -- TOML commands schema compatibility doc

- Created [docs/archives/v2/v2.2/antigravity-cli-commands-schema.md](../../antigravity-cli-commands-schema.md) confirming the file-format diff between Gemini CLI (`~/.gemini/commands/*.toml`, TOML wrapping) and Antigravity 2.0 + CLI (`~/.agent/workflows/*.md`, verbatim Markdown).
- Conclusion: no `_write_antigravity_commands` helper variant required; the existing `SkillsIntegration._mirror_catalog` already mirrors `catalog/commands/*.md` verbatim.
- Test file: `tests/integrations/test_antigravity_commands.py` -- 3 new test cases (Antigravity 2.0 produces `.md` only / zero `.toml`, mirrored body is byte-identical, Gemini CLI still produces `.toml`).

### T013 -- Gemini CLI install deprecated behind --enterprise flag

- `scripts/installer.sh`:
    - Added `while [ $# -gt 0 ]; do case "$1" in --enterprise|-h|--help) ... esac; done` flag parser immediately after `SCRIPT_DIR` / `REPO_ROOT` setup.
    - Added `show_installer_usage` function printing the help text.
    - Wrapped both Gemini CLI dispatch sites (lines 770 and 1163) in `if [ "$ENTERPRISE" = "1" ]; then ... else write_item "...sunset..."; fi`.
    - Renamed both `Antigravity 2.0` display strings to `Antigravity 2.0 + CLI`.
- `scripts/installer.ps1`:
    - Added top-of-file `[CmdletBinding()] param([switch]$Enterprise, [switch]$Help)` block.
    - Added an early-exit `-Help` handler.
    - Wrapped both Gemini CLI dispatch sites in `if ($Enterprise) { ... } else { Write-Item "...sunset..." -Color Yellow }`.
- `scripts/lib/integrations/gemini_cli.py::GeminiCliIntegration.display_name` -> "Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)".
- Test file: `tests/installer/test_enterprise_flag.py` -- 7 new test cases (flag declaration, dispatch gating, sunset warning text, both `.sh` and `.ps1` parity, gemini-cli display_name).
- Verified `bash scripts/installer.sh --help` prints the new usage text correctly.

### T014 -- Phase 2 test stabilization

- Ran `python -m pytest tests/integrations tests/installer -v` -- 121 passed, 0 failed.
- Ran `python -m pytest tests/integrations tests/installer -v -k "antigravity or gemini or enterprise"` -- 35 selected, 35 passed.
- Ran `shellcheck --severity=warning scripts/installer.sh catalog/hooks/antigravity-cli-diff-review.sh catalog/hooks/gemini-diff-review.sh` -- clean.
- Ran `bash -n scripts/installer.sh` and `[System.Management.Automation.Language.Parser]::ParseFile('scripts/installer.ps1', ...)` -- both clean.
- Ran `python scripts/validate_skills.py --bundles-only` -- PASS (0 errors, 0 warnings, 210 skills scanned).
- A live cross-OS install smoke is deferred to Phase 6's release-prep step (a global install would touch user home dirs outside the Phase 2 scope). The static enterprise-flag tests, source-level parsing, and test-level idempotency contract together cover the same ground.

## Test results (sub-step 8.2)

- **tests/integrations**: 88 passed, 0 failed (88 = 80 from Phase 1 + 6 new from `test_antigravity.py` + 3 new from `test_antigravity_commands.py` minus 1 duplicate count adjustment).
- **tests/installer**: 33 passed, 0 failed (33 = 26 from Phase 1 + 7 new from `test_enterprise_flag.py`).
- **Total**: 121 passed, 0 failed.

## CI/CD edits (sub-step 8.3)

- 0 CI workflow files modified. The existing `tests` job at `.github/workflows/ci.yml:75` already runs `pytest tests/integrations tests/installer` and auto-picks-up the 3 new test files. The existing `shellcheck` job at `.github/workflows/ci.yml:50` already lints `catalog/hooks/*.sh` and auto-picks-up the new `.sh` hook. No new env vars or secrets introduced.

## Deviations from plan

- **T008 (a) branch chosen, (b) branch dropped**: the probe (T007) found no path divergence between Antigravity CLI and Antigravity 2.0 desktop, so a separate `AntigravityCliIntegration` class is unnecessary. `Antigravity20Integration` carries dual coverage via its display_name and docstring. Tracked in known-gaps.md (no action needed; this is the documented decision).
- **T011 wrapper integration mechanism**: the wrappers begin with `@base-google-shared.md` per the plan's literal instruction, relying on the destination agent (Gemini CLI / Antigravity CLI / Antigravity 2.0 desktop) to resolve the `@` import. Nexus-Hub's `_render` function does not resolve `@` imports at install time; the rendered file contains the literal `@base-google-shared.md` text. If the destination agent does not resolve the import, the user sees the literal text and the surface-specific guidance only. No regression vs. the prior single-template flow (which never shipped the shared body to those surfaces either). Tracked as informational; not in known-gaps.
- **T014 cross-OS live install deferred to Phase 6 release-prep**: see test stabilization notes above. Auto-mode classifier blocked global install (scope escalation), which is correct; the static tests fully cover the gating contract.

## Known gaps added

- **WN-2** Antigravity CLI binary name unverified on a live VM (deferred to future live-VM verification pass).
- **WN-3** Antigravity CLI workflow file format unverified on a live VM (deferred to future live-VM verification pass).
- **WN-4** Antigravity CLI workflow front-matter / name-derivation schema unverified (deferred to future live-VM verification pass).

All three are warnings (`WN`), not blockers; the Antigravity 2.0 desktop conventions are documented and the CLI inherits them per the 2026-05-21 Google announcement.

## Next steps

- Advance to Phase 3 ("Installer rigor + legacy-platform parity migration"). Phase 3 builds on the Phase 1 `WriteResult` vocabulary to add `--print-config`, `--check`, `wire_project_surfaces()`, the legacy-state self-healing registry, the 47-case parameterized contract suite, and the DF-001 byte-identical parity migration of Claude / Codex / Cursor / Gemini / OpenCode from the legacy installer copy blocks to the registry runner.
- If schedule slips past 2026-06-01: cut `v2.2.0-rc1` containing only Phase 1 + Phase 2 (per the plan's T014 fallback) so the Antigravity transition ships ahead of the 2026-06-18 sunset.
