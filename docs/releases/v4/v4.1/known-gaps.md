# Known Gaps - v4.1

**Project**: Nexus-Hub
**Status**: finalized
**Last updated**: 2026-08-28

## v4.1.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Warnings

##### WN-1 - GitHub repository description advertises 324 skills

- **Source phase**: Phase 6 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Evidence**: `python scripts/check_release_preconditions.py --branches --repo-settings` reported that the remote GitHub description says 324 skills while the repository catalog and README say 326.
- **Impact**: This does not affect installed artifacts, tests, or release contents, but the public repository summary will remain stale until publication updates it.
- **Suggested next step**: During the approved `/update release` publication flow, update the GitHub repository description to 326 skills and rerun the release-precondition report.

All Not Implemented, Deferred, Bug / Regression, Missing Test, and Quality-Gate categories have no open v4.1.0 items.

### Resolved

No resolved items.

### Inherited Ledger Review

- v3.20 DF-1 and DF-2 remain on `docs/releases/v3/v3.20/known-gaps.md`; this adoption plan did not absorb or relabel them.
- v3.21 DF-1 remains on `docs/releases/v3/v3.21/known-gaps.md` because Nexus-Hub still has no authored catalog atlas.
- v3.21 DF-2 is resolved on its original ledger by the v4.1.0 Phase 1 refresh of `docs/todos.md`.
