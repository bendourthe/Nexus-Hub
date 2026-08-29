# Known Gaps - v4.2

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-29

## v4.2.0 - interactive-guide-redesign

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |

### Open Items

#### Deferred

##### DF-1 - Phase 1 guide baseline has no rendered browser screenshots

- **Source phase**: Phase 1 - Baseline, content model, and UX contract
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md` T001
- **Reason**: This implementation session had no browser tools. The plan says not to block: capture a static source audit and a hallmark-from-markup table, then record a known-gap that last-phase human testing must fill.
- **Suggested next step**: After merge, open `guides/website/nexus-hub-guide.html` in a browser and capture full-page and key-section screenshots at 1440x900, 1024x768, 390x844, and 1920x1080 (light and dark), plus Lighthouse Accessibility, keyboard, reduced-motion, and a workshop 4-of-5 note if participants are available.

#### Quality-Gate Gaps

##### QG-1 - Local full repo pytest suite did not finish in the last-phase session

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md` T033
- **Reason**: `python -m pytest --collect-only -q tests` collected 3526 tests. CI budgets `repo-tests` at 4500s. A local run reached about 16 percent after 11 minutes (within that budget) and was interrupted; a restart was still running when the evidence file was written. Focused `tests/guides/test_nexus_hub_guide.py` (30 passed, 1 skipped) and `python scripts/ci/run.py --profile fast` (12 passed) are green.
- **Suggested next step**: Treat the integration pull request `pytest tests` job as the full-suite proof. Do not merge on a red `ci-required`.

### Resolved

None yet.

### Inherited Ledger Review

- v4.1.0 DF-1 / WN-1 / QG-1 and v4.1.1 DF-1 stay on `docs/releases/v4/v4.1/known-gaps.md`. This plan does not absorb them.
- v4.0 DF-1 stays on `docs/releases/v4/v4.0/known-gaps.md`.
- No `## v3.20.0` section is appended to v3.16 or v3.20 ledgers.

## v4.2.1 - guide-visual-education

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

None yet. v4.2.0 DF-1 and QG-1 stay under `## v4.2.0` until Phase 7 closes or re-homes them. This patch does not absorb v4.1 or v4.0 gaps.

### Resolved

None yet.
