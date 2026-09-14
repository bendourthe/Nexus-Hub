# Known gaps - v4.12

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-09-14

Release-scoped gaps for the sole-contributor-attribution plan. Planned future-phase work is tracked in the plan rather than reported as completed here.

## v4.12.0

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

#### WN-1: Existing CI-profile lint findings

**Owner**: CI profile maintainer. **Status**: open. **Next step**: address UP035 at the existing typing imports and FLY002 in `_PS_AST_PARSE` during the next CI-profile maintenance change.

Phase 3 confirmed both findings against the parent commit before its one-command change. No new checker or test-module lint finding remains. Evidence: external `phase3-baseline-lint.json`; this does not waive the final functional validation gate.

### Resolved

None.
