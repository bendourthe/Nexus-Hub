# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: in development (Phase 1 of 8 complete)
**Last updated**: 2026-07-13 (Phase 1: false-confidence-test-audit + commit-sweep skills)

## v3.15.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Warnings

##### WN-1 - New pushy skill descriptions exceed the 250-char full-mode length check

- **Source phase**: Phase 1 (1.1, 1.2)
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.0-agentic-setup-adoption.md` sub-tasks 1.1-1.2
- **Reason**: `false-confidence-test-audit` and `commit-sweep` carry pushy descriptions (verbatim trigger phrases plus a SKIP clause) well over 250 characters, so `validate_skills.py` FULL mode would flag them. This is the known catalog-wide pushy-description-vs-250-char tension (the WN-v3121 family); `make validate` does not run full mode and is clean. Intentional per the AGENTS.md description-style rule (combat under-triggering).
- **Suggested next step**: None required. Track with the catalog-wide description-length decision; do not shorten at the cost of trigger coverage.

##### WN-2 - Catalog skill-count prose in marketplace.json is stale

- **Source phase**: Phase 1 (1.3)
- **Plan reference**: sub-task 1.3
- **Reason**: `data/marketplace.json` `plugin.description` prose still reads "265 curated skills" while the true count is now 268 (`skills.json` and the `SKILL_INDEX.md` total were both corrected to 268 this phase). The prose count was already stale by one before this phase (265 stated vs 266 actual at presentify Phase 5) and bundles the command and hook counts plus the version, which are reconciled together at release.
- **Suggested next step**: `/update release` reconciles the marketplace `plugin.description` counts (skills / commands / hooks) and the version bump atomically; no mid-version action is needed.

### Notes

- Phase 1 added two Markdown skills. Skills have no pytest surface by design (they are validated structurally by `validate_skills.py`, not unit-tested), so the absence of unit tests is not an MT gap.
- The plan was renumbered from v3.13.0 to v3.15.0 during Phase 1: v3.13.0 is the committed presentify-universal-ingestion version and an untracked v3.14.0-codex-lb-adoption draft already exists.
