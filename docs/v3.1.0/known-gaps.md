# Known Gaps -- v3.1.0

**Status**: in progress (Phases 1-2 of 3 of the `adoption-dynamic-workflows` plan closed). Catalog green: orphan-bundle audit 0 errors (1 pre-existing warning unrelated to these phases), all JSON catalogs valid, no-personal-paths / unicode-safety / supply-chain / workflow-security / check_version_sync all exit 0; the skill-security scanner reports 0 findings (0 HIGH/CRITICAL) on both pilot bundles.
**Last updated**: 2026-06-05 (Phase 2 / adoption-dynamic-workflows)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for the v3.1.0 `adoption-dynamic-workflows` plan. The next version's `/generate-plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 1 | 0 |
| QG | 0 | 0 |
| **Total** | **1** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v31-1 | WN | Phase 1-2 | T003, T006 (stabilization) | Local verification on the Windows dev host is partial: `make` is not on PATH, so `make validate` is emulated by invoking each validator directly (all green: orphan-bundle audit 0 errors with 1 pre-existing `demo-capture` `.pyc` warning unrelated to these phases, all four JSON catalogs valid, no-personal-paths / unicode-safety / supply-chain / workflow-security / check_version_sync all exit 0). Phase 2 additionally ran the skill-security scanner against both pilot bundles (7 files, 0 findings, 0 HIGH/CRITICAL), confirming the cross-branch claude-red scanner-allowlist gate is moot for these read-only `.js` templates. Phases 1-2 made no shell/installer/Python changes (three `.js` templates + markdown edits only), so there is no ShellCheck or new-code pytest surface; the `tests/validators` suite (134 tests) passes. | Confirm the CI `validate` + scanner jobs are green for this commit on the ubuntu runner; no code change expected. | Low (covered by CI; matches the cross-version local-make pattern from WN-v30-4 / WN-v30-7) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none) | -- | -- | -- | No prior open items to resolve (this is the first phase of the plan). |
