# Centralized Worktrees Phase 5

**Version**: v4.15.6
**Phase**: 5, Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
**Base**: Phase 5 local commit `c1746f538`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.6`

## Subtasks

| Task | Outcome |
|---|---|
| T017-T024 | Done in `c1746f538`. Evidence: `../../v4.15.6-last-phase-evidence.md`. |
| Scope addition 1 | Idle-lane warning (approved, Decision 2 option A, 2026-11-21). `lane_health.py` classifies idle members (`unadmitted`, `resumable`, `needs-user`), `status_snapshot.py --record` measures them, the progress report shows an Idle lanes section, and both session-start siblings print one notice line for a live minor record of the repository. |
| T025 | Open until a green full run. |
| T026 | Open: publication and integration belong to the coordinator. |

## Evidence

- Live v4.15 record: `lane_health.py notice --repo .` printed 7 idle members in 0.6 s (v4.15.7 `needs-user`, v4.15.9 `resumable`, v4.15.8 and v4.15.10 to v4.15.13 `unadmitted`), the three blind spots that let the run sit idle.
- Focused suites: `tests/test_lane_idle.py` 8 passed; `tests/test_lane_health.py` 15 passed; the status report, snapshot, reporting and command-contract suites 121 passed; `catalog/hooks/tests/test_session_start_lane_notice.py` plus `test_session_start.py` 44 passed on bash and Windows PowerShell; the CI partition and engine guards 126 passed.

## Full-profile failure triage

- `repo-tests-integrations-map` (`ModuleNotFoundError: No module named 'tree_sitter'`): a local environment gap, not a branch defect. CI installs `extensions/nexus-code-search[dev]`, whose `pyproject.toml` requires `tree-sitter>=0.24,<0.26`, before that step; this workstation's Python lacks it. No change.
- `repo-tests-integrations-install` (24 failures in the 23-minute full run): the shard's 17 files run alone pass on this branch at `1a9076e7f` (353 passed, 2 skipped, 12 min) and on a clean `origin/develop` `b3c678a95` worktree (353 passed, 2 skipped, 11 min). The failures do not reproduce in isolation on either tree, so they came from contention in the long full run, not from this branch. No change.

## Plan delta

Disposition: Approved scope additions. Evidence: during the v4.15 minor run, v4.15.9, v4.15.11 and v4.15.12 sat idle because the coordinator never dispatched them, `lane_health.py check` showed only admitted lanes and reported `stalled: []`, and v4.15.7 waited four days on a user-only grant with no decision raised. The maintainer approved Decision 2 option A (idle-lane warning, 2026-11-21) and, on 2026-11-22, Decision 1 option A and Decision 2 option A again together with four more items: the checker names the dispatch or decision action, a machine-readable blocked heartbeat, a minor-entry re-plan step, and a supported grant route for an already-started member. Consequence for remaining phases: each item lands as its own local commit before T025's full run; frozen plan prose is unchanged.

## CI impact

`tests/test_lane_idle.py` is listed in both governance shards in `scripts/ci/profiles.py` and in the pinned lists of `tests/ci/test_ci_engine.py` and `tests/validators/test_ci_partition_proof.py`. The new hook test falls into the catch-all `hook-tests-rest` shard. No workflow file changes.

## Deviations

None.

## Next steps

- Finish the approved scope additions, then rerun the affected full-profile steps.
- T025 full run and T026 publication by the coordinator.
