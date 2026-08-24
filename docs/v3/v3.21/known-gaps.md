# Known Gaps - v3.21

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-24

## v3.21.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

##### DF-1 - Nexus-Hub catalog has no product atlas HTML

- **Source phase**: Phase 5 - Living docs, git hygiene, CI/CD, Goal review
- **Plan reference**: `docs/v3/v3.21/plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md` (sub-task 5.3)
- **Reason**: Last-phase scan found `docs/handbooks/` scaffolded (README, empty `markdown/` and `html/` with `.gitkeep`) and `atlas/companion html count: 0`. This repo is the upstream catalog, not an application with a user-facing walkthrough. Inventing a fake atlas would violate the plan's honesty rule.
- **Suggested next step**: If maintainers want a catalog atlas, author real markdown under `docs/handbooks/markdown/` and generate HTML via `/presentify`. Until then `/update release` regenerate-and-fail-on-stale is a no-op.

##### DF-2 - `docs/todos.md` still describes an old feature branch

- **Source phase**: Phase 5 - Living docs, git hygiene, CI/CD, Goal review
- **Plan reference**: `docs/v3/v3.21/plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md` (sub-task 5.3)
- **Reason**: The living dashboard opens on `feat/presentify-slide-navigation` and scores from earlier minors. Rewriting it in this last phase would be a separate product-surface edit, not the Goal (fail-closed last phase, implement drivers, handbook wiring).
- **Suggested next step**: Refresh `docs/todos.md` in a dedicated pass against current `develop` / the active plan, or replace it with a thin pointer to the roadmap.

Prior v3.20 items (DF-1 invocation levers, DF-2 marketplace form, WN-3 personal-paths scan) stay in `docs/v3/v3.20/known-gaps.md`. They were reviewed this last phase and remain out of this plan's scope per Phase B.5.

#### Bugs / Regressions

None.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None. Phase 1 added `tests/skills/test_last_phase_fail_closed.py`. Phase 2 added `tests/skills/test_implement_driver_modes.py`. Phase 3-4 added `tests/skills/test_living_docs_architecture.py` (including v4.0 consumption). The ubuntu `tests` job already runs `tests/skills`.

#### Quality-Gate Gaps

None. Existing `ci.yml` already covers `catalog/skills/**`, `catalog/commands/**`, and `tests/skills` with job-level classification and no workflow-level `paths:` filter. Concurrency cancel-in-progress and pip cache are unchanged. `python scripts/check_installer_parity.py` PASS.

### Resolved

None yet.
