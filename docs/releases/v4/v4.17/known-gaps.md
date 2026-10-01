# Known Gaps - v4.17

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-09-30
**Open items**: 1

Release-scoped gaps for the v4.17 minor. The first entry is a follow-up acceptance measure recorded by the v4.13.6 final phase, not a defect: it names what the first real minor-scope run must show.

## v4.17.0

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

#### DF-1: The first real minor-scope run has not happened yet

- **Source phase**: v4.13.6 Phase 8 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Plan reference**: `docs/releases/v4/v4.13/plans/v4.13.6-minor-scope-implement-and-verified-cleanup.md` (sub-task 8.2, plan-specific notes)
- **Reason**: v4.13.6 proved a two-plan minor only on stand-ins (`tests/e2e/implement_full/test_minor_run.py`). Whether the flow works for a person is measured by the first real `/implement v4.17` run.
- **Acceptance measure**: the run reaches `MINOR COMPLETE v4.17 <head> <nonce>` from `check_plan_completion.py check-minor v4.17` after exactly one approval paste; no branch, worktree, or file removed by the cleanup pass has to be restored afterwards; and the user did not need to ask what the approval page meant before pasting.
- **Owner**: catalog maintainer, at the v4.17 minor-scope run.
- **Suggested next step**: before that run, normalize the older ledgers (v4.13.6 WN-2) so the gap scope parses; record the three observations above in this entry, then mark it RESOLVED or open a BG item for each miss.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
