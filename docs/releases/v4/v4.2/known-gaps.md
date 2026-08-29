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
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - Phase 1 guide baseline has no rendered browser screenshots

- **Source phase**: Phase 1 - Baseline, content model, and UX contract
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md` T001
- **Reason**: This implementation session had no browser tools. The plan says not to block: capture a static source audit and a hallmark-from-markup table, then record a known-gap that last-phase human testing must fill.
- **Suggested next step**: In Phase 7 human testing, capture full-page and key-section screenshots at 1440x900, 1024x768, 390x844, and 1920x1080 (light and dark), plus console, network, keyboard, and reduced-motion evidence. Store them under `docs/releases/v4/v4.2/development/guide-redesign-baseline/` or the last-phase evidence folder.

### Resolved

None yet.

### Inherited Ledger Review

- v4.1.0 DF-1 / WN-1 / QG-1 and v4.1.1 DF-1 stay on `docs/releases/v4/v4.1/known-gaps.md`. This plan does not absorb them.
- v4.0 DF-1 stays on `docs/releases/v4/v4.0/known-gaps.md`.
- No `## v3.20.0` section is appended to v3.16 or v3.20 ledgers.
