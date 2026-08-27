# Session History - v3.14.0 Phase 6: terminal refactor, known-gaps, CI/CD, release readiness

**Date**: 2026-07-16
**Branch**: `feat/codex-lb-adoption` (off `develop`)
**Plan**: [docs/releases/v3/v3.14/plans/v3.14.0-codex-lb-adoption.md](../../plans/v3.14.0-codex-lb-adoption.md), Phase 6 of 6 (**final phase**)
**Scope**: `test_installer_smoke.py` (BG-1), a new CI workflow, the v3.14 ledger/devlog/history docs. No catalog skill or metadata change.

## Goal

The mandatory terminal phase: repo-wide refactor over all additions, known-gaps reconciliation, CI/CD create/update, full validation, a throwaway dry-run install (HO-1), and the release-readiness handoff to `/update release`.

## Sub-tasks completed

1. **6.1 - Terminal refactor / consistency pass.** No drift across all Phase 1-5 additions (no empty dirs, no orphaned bundle files, consistent structure/cross-links, all validators green). A clean bill; no fixes to apply.
2. **6.3 - CI/CD.** BG-1 resolved: `verify_platform_contracts.py` declared dev-only in `test_installer_smoke.py`'s `DEV_ONLY_SCRIPTS` (a repo-internal validator like `check_base_template_parity.py`). QG-1 resolved: added `.github/workflows/claude-usage-monitor.yml` (path-filtered, concurrency-cancelled; `npm ci` + compile + Vitest). The new `test_skill_activation.py` already runs under `ci.yml`'s `catalog/hooks/tests/` glob.
3. **6.4 - Full validation + dry-run install.** All green (see below); HO-1 verified clean.
4. **9A - Known-gaps reconciliation.** BG-1 / QG-1 / HO-1 -> RESOLVED; DF-1 / DF-2 / MT-1 kept; DF-3 (P1) added; ledger status RELEASE-READY.

## Validation results (make unavailable on this Windows host; ran the validate/test commands directly)

- Catalog validators (bundle audit, quality, unicode): 0 errors.
- `validate_workflow_security.py`, `verify_platform_contracts.py`, `check_base_template_parity.py`: PASS (exit 0).
- Full pytest hook suite (`catalog/hooks/tests/`): **459 passed, 36 skipped, 0 failed** (BG-1 fixed; was 458 + 1).
- Extension: `npm run compile` clean; 35 Vitest tests pass.
- `check_version_sync.py`: consistent at 3.13.0 (bumps to 3.14.0 at `/update release`).

## Dry-run install (HO-1)

A throwaway global install via `scripts/lib/integrations/runner.py` into a temp HOME (integrations claude, codex, gemini, antigravity2, opencode). `verify` PASS on every platform (the single NEEDS-ACTION is the standard project-scoped `.agents/` note, not a regression). `review-trapdoors` lands flattened at `skills/review-trapdoors/SKILL.md` across all seven platform skill paths with NO nested `skills/code-review/review-trapdoors/` variant -> HO-1 clean. The C1 hooks + `skill-rules.example.json` landed at `.claude/hooks/` and are registered in the installed `settings.json`.

## Decisions

- **Release as v3.14.0.** The user resolved the v3.14.0 numbering collision in favor of codex-lb; the held `agentic-setup-adoption` plan renumbers on its own branch (owner's decision there).
- **BG-1 fixed here** (not deferred to the v3.14.1-installer-hotfix plan), at the user's direction, as the correct one-line dev-only-allowlist fix.

## Release-readiness handoff (9C-9E)

Phase 6 hands off to `/update release` for the version bump (3.13.0 -> 3.14.0 across all surfaces, guarded by `check_version_sync.py`), CHANGELOG `[Unreleased]` -> `[3.14.0]` promotion, commit, merge to `main`, tag `v3.14.0`, push, and GitHub Release - all under `/update release`'s own confirmation gates. Sequencing note: the five phase commits + this Phase 6 commit are on `feat/codex-lb-adoption` and must reach `develop` before the develop -> main release merge; the branch has not been pushed yet.

## Deviations

- None. The terminal-phase gate (9.0 refactor + known-gaps + CI/CD) ran even though the plan's Phase 6 predates the v3.11.0 explicit-gate convention.

## Definition of Done status

All seven selected candidates (U1, C4, C3, C6, C5, C1, C2) are adopted and validated; `make`-equivalent validate/lint/test green; extension compiles/packages/tests; orphan-bundle audit clean; no flat/nested skill-name collision on install; CHANGELOG `[Unreleased]` complete and ready for `/update release`; P1 deferred to DF-3.
