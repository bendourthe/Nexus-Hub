# Known Gaps - v4.7

**Project**: Nexus-Hub
**Status**: v4.7.0 in progress on `feat/v4.7.0-model-behavior-and-distribution-integrity`; Phase 1 complete locally, not published
**Last updated**: 2026-09-05 (v4.7.0 Phase 1)

## v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)

**Plans**: [v4.7.0-adoption-model-behavior-and-distribution-integrity.md](plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md), [v4.7.0-adoption-gpt-6-astra-prompting.md](plans/v4.7.0-adoption-gpt-6-astra-prompting.md)
**Base**: `develop` at `76bcf614` (post v4.5.0 back-merge and the v4.7 to v4.9 plans migration)

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

##### DF-1 - The v4.4.6 guide plan's model map was not reconciled from this branch

- **Source phase**: Phase 1 (amendment sub-task 1.2, T038).
- **Plan reference**: `v4.7.0-adoption-gpt-6-astra-prompting.md` sub-task 1.2.
- **Reason**: `docs/releases/v4/v4.4/plans/v4.4.6-guide-learning-experience.md` exists only on the concurrent `feat/v4.4.3-guide-illustration-rebuild` branch, where another session is still committing; editing it here would guarantee a merge conflict when that branch lands. Its map already places `gpt-6-astra` at frontier, which agrees with the 2026-09-05 decision, so the substantive disagreement the sub-task targeted no longer exists; only the one-line citation of the decision note is missing.
- **Suggested next step**: When the guide branch is merged into `develop`, add one sentence under that plan's `## Current model map` citing `docs/releases/v4/v4.7/development/astra-routing-decision.md`, or close this item as superseded if the map is treated as a historical record.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|

### Notes (not gaps)

- The plan's Phase 1 stability gate "no file in the repository names `claude-fable-5` as a frontier tier value" is scoped in the test to live routing surfaces; twelve historical plans under `docs/releases/v3/` keep that id in their dated maps as records. Recorded in the Phase 1 history as a Plan delta.
- The prompting profile layer (`model-prompting-research/assets/profiles-index.json`) still lists `claude-fable-5` in its Claude roster (v4.5 `WN-3`); refreshing that roster is `/tune-prompting` work and is not this plan's scope. Amendment Phase 3 adds the first OpenAI profile beside it under a multi-platform schema and does not rewrite the Claude roster.
