# Known Gaps - v3.20

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-23

## v3.20.1

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

#### Not Implemented

None.

#### Deferred

None.

#### Bugs / Regressions

None.

#### Warnings

##### WN-1 - Thirteen SKILL.md descriptions exceed the agentskills.io 1024-character cap

- **Source phase**: Phase 1 - Framework and conformance tooling
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.1-adoption-cybersecurity-skills.md` (sub-task 1.3)
- **Reason**: Nexus-Hub's pushy-description convention (verbatim trigger phrases plus a SKIP clause) predates the conformance guard. Enforcing 1024 as a hard error on the current catalog would fail `make validate` on 13 existing skills, contradicting the phase acceptance criterion that the guard exits 0 on the current catalog. Those names are grandfathered in `OVERLONG_DESCRIPTION_ALLOWLIST`; a new over-long description is still a hard error.
- **Suggested next step**: Trim the 13 descriptions under 1024 characters (without dropping trigger phrases or SKIP clauses), then remove each name from the allowlist.

#### Missing Tests / Coverage Gaps

None.

#### Quality-Gate Gaps

None.

### Resolved

None.

## v3.20.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

None.

#### Bugs / Regressions

None.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None.

#### Quality-Gate Gaps

None.

### Resolved

##### DF-census - Plan census 271 -> 272 was stale

- **Source phase**: Phase 3
- **Resolved**: 2026-08-23. Live catalog was 274 before Phase 1 and 275 after. Plan success metric and registry prompt updated to 275 / 274 -> 275. No product gap.
