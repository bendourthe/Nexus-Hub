# Known Gaps - v4.1

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-28

## v4.1.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |

### Open Items

All Not Implemented, Bug / Regression, and Missing Test categories have no open v4.1.0 items.

#### Deferred

##### DF-1 - Prompting profile layer does not match the live Codex roster

- **Source phase**: v4.1.0 release preparation
- **Evidence**: `python scripts/check_model_prompting_freshness.py --advisory` reported `DRIFTED` against the routing helper's live Codex roster: six live Codex entries are unprofiled and four recorded Claude entries are absent from that host roster.
- **Reason deferred**: The advisory is intentionally not a release or CI gate, and a conformant refresh requires the separate calibrated `/tune-prompting` research and adversarial-verification workflow rather than a release-time hand edit.
- **Next action**: Run `/tune-prompting` after v4.1.0 publication, calibrate on one live model before widening, and retain any unverified models as explicit gaps.

#### Warnings

##### WN-1 - GitHub repository description advertises 324 skills

- **Source phase**: Phase 6 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Evidence**: The release flow confirmed the remote description says 324 skills while the repository catalog and README say 326.
- **Next action**: Apply the approved 324-to-326 GitHub description correction during the authorized publication step, then rerun `python scripts/check_release_preconditions.py --branches --repo-settings` before marking this warning resolved.

#### Quality-Gate Gaps

##### QG-1 - Additional local full profile did not complete within the release-prep window

- **Source phase**: v4.1.0 release preparation
- **Evidence**: The canonical `release` profile passed 3 of 3 checks, and all targeted release validators passed. An additional `python scripts/ci/run.py --profile full --quiet --json` run completed the Windows hook-parity group and continued actively in `pytest tests -q`, but was interrupted after an extended bounded wait without a final profile report.
- **Impact**: The local full-profile result is incomplete, not failed or passed. The feature integration on `develop` remains green, but the release-preparation diff still requires its own remote full-suite result before merge.
- **Next action**: Push the release-preparation branch only after authorization, open the integration PR, and require the complete remote suite to pass before merging it into `develop`.

### Resolved

#### Warnings

##### WN-2 - Claude plugin description advertised 325 skills

- **Source phase**: v4.1.0 release preparation
- **Evidence**: The release docs reconciliation found `.claude-plugin/plugin.json` still said 325 curated skills while `data/skills.json`, README, AGENTS.md, and `data/marketplace.json` said 326.
- **Resolution**: Updated the plugin description to 326 in the v4.1.0 release commit; catalog validation and the final release profile verify the synchronized result.

> Finalized on 2026-08-28 at the 4.1.0 bump. Open items will be ingested by `/plan` when the next version's plan is created.

### Inherited Ledger Review

- v3.20 DF-1 and DF-2 remain on `docs/releases/v3/v3.20/known-gaps.md`; this adoption plan did not absorb or relabel them.
- v3.21 DF-1 remains on `docs/releases/v3/v3.21/known-gaps.md` because Nexus-Hub still has no authored catalog atlas.
- v3.21 DF-2 is resolved on its original ledger by the v4.1.0 Phase 1 refresh of `docs/todos.md`.

## v4.1.1

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

All Not Implemented, Deferred, Bug / Regression, Warning, Missing Test, and Quality-Gate categories have no open v4.1.1 items after Phase 1.

### Resolved

None.
