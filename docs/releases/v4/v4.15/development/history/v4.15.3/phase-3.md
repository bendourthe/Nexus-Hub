# Behavioral Harness Phase 3

**Version**: v4.15.3
**Phase**: 3, Cadence protocol
**Started**: 2026-11-16T23:48:44-08:00
**Ended**: see the commit time of this phase (local host time)
**Base**: Phase 2 commit `47765a016`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.3`

## Subtasks

| Task | Outcome |
|---|---|
| T015 | `guides/reference/HARNESS_FEEDBACK_CADENCE.md` defines the protocol on the landed pairing contract. |
| T016 | Frozen credential-free manifest and fake adapter data under `tests/fixtures/harness_pairings/v4.15.3-cadence/`. |
| T017 | `test_harness_cadence_protocol.py`: 12 tests driving the real evaluator, including grader, binding, incomparability, zero-accepted, unknown-spend, timeout and immutable-id controls. |
| T018 | Verified locally; one local commit. |

## Deviations

The evaluator cannot express feedback timing in its receipts. The plan allows a named dependency gap instead of an engine change, so the matrix uses a sidecar history and the gap is named in the guide and the evidence file. The adapter code is embedded in the test file because the admitted claims name only the manifest and the fake-adapter data file under the fixture folder.

## CI impact

None. See `v4.15.3-phase-3-evidence.md`.
