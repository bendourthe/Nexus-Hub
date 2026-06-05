# Known Gaps -- v3.1.0

**Status**: in progress (Phase 1 of 3 of the `adoption-dynamic-workflows` plan closed). Catalog green: orphan-bundle audit 0 errors (1 pre-existing warning unrelated to this phase), all JSON catalogs valid, no-personal-paths / unicode-safety / supply-chain / workflow-security / check_version_sync all exit 0.
**Last updated**: 2026-06-05 (Phase 1 / adoption-dynamic-workflows)

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
| WN-v31-1 | WN | Phase 1 | T003 (stabilization) | Local verification on the Windows dev host was partial: `make` is not on PATH, so `make validate` was emulated by invoking each validator directly (all green: orphan-bundle audit 0 errors with 1 pre-existing `demo-capture` `.pyc` warning unrelated to this phase, all four JSON catalogs valid, no-personal-paths / unicode-safety / supply-chain / workflow-security / check_version_sync all exit 0). Phase 1 made no shell/installer/Python changes (one `.js` template + two markdown edits only), so there is no ShellCheck or new-code pytest surface this phase. | Confirm the CI `validate` job is green for this commit on the ubuntu runner; no code change expected. | Low (covered by CI; matches the cross-version local-make pattern from WN-v30-4 / WN-v30-7) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none) | -- | -- | -- | No prior open items to resolve (this is the first phase of the plan). |
