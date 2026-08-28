# Known Gaps - v3.21

**Project**: Nexus-Hub
**Status**: finalized
**Last updated**: 2026-08-25

## v3.21.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 1 |
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
- **Plan reference**: `docs/releases/v3/v3.21/plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md` (sub-task 5.3)
- **Reason**: Last-phase scan found `docs/handbooks/` scaffolded (README, empty `markdown/` and `html/` with `.gitkeep`) and `atlas/companion html count: 0`. This repo is the upstream catalog, not an application with a user-facing walkthrough. Inventing a fake atlas would violate the plan's honesty rule.
- **Suggested next step**: If maintainers want a catalog atlas, author real markdown under `docs/handbooks/markdown/` and generate HTML via `/presentify`. Until then `/update release` regenerate-and-fail-on-stale is a no-op.

Prior v3.20 items (DF-1 invocation levers, DF-2 marketplace form, WN-3 personal-paths scan) stay in `docs/releases/v3/v3.20/known-gaps.md`. They were reviewed this last phase and remain out of this plan's scope per Phase B.5.

#### Bugs / Regressions

None.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None. Phase 1 added `tests/skills/test_last_phase_fail_closed.py`. Phase 2 added `tests/skills/test_implement_driver_modes.py`. Phase 3-4 added `tests/skills/test_living_docs_architecture.py` (including v4.0 consumption). The ubuntu `tests` job already runs `tests/skills`.

#### Quality-Gate Gaps

None. Existing `ci.yml` already covers `catalog/skills/**`, `catalog/commands/**`, and `tests/skills` with job-level classification and no workflow-level `paths:` filter. Concurrency cancel-in-progress and pip cache are unchanged. `python scripts/check_installer_parity.py` PASS.

### Resolved

#### DF-2 - `docs/todos.md` described an old feature branch

- **Resolved in**: v4.1.0 Phase 1 on 2026-08-27
- **Evidence**: `docs/todos.md` now names `feat/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts`, links the active v4.1 plan, reports current catalog counts, and uses the short replace-rather-than-append dashboard contract.
- **Resolution**: The stale `feat/presentify-slide-navigation` dashboard and earlier-minor scores were replaced; no historical ledger was deleted.
