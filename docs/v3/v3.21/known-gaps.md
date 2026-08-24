# Known Gaps - v3.21

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-24

## v3.21.0

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

#### Not Implemented

None.

#### Deferred

None. Prior v3.20 items (DF-1 invocation levers, DF-2 marketplace form, WN-3 personal-paths scan) stay out of this plan's scope per Phase B.5 grounding.

#### Bugs / Regressions

None.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None. Phase 1 added `tests/skills/test_last_phase_fail_closed.py`. Phase 2 added `tests/skills/test_implement_driver_modes.py`. The ubuntu `tests` job already runs `tests/skills`.

#### Quality-Gate Gaps

None. Existing `ci.yml` already covers `catalog/skills/**`, `catalog/commands/**`, and `tests/skills` with job-level classification and no workflow-level `paths:` filter. Concurrency cancel-in-progress and pip cache are unchanged.

### Resolved

None yet.
