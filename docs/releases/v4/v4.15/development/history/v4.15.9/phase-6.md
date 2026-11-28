# v4.15.9 Phase 6 (reduced lane): local evidence

Started 2026-11-18T00:07Z.

## Done

- Wrote `v4.15.9-last-phase-evidence.md` with one section per duty. Architecture scan, git-tree hygiene output, docs retention output, the bounded deep pass, the Goal review, and manual testing suggestions are recorded.

## Not done

- Pipeline reconciliation (sensitive paths), known-gaps file edits (coordinator-owned), and publication. This lane never pushes.
- The Goal review records a partial landing: `effort: high`, the Claude-only key list, and the measured run are deferred.

## CI impact

No new commands, dependencies, or test paths.

## Completion pass (2026-11-21 to 2026-11-22)

- Rewrote `v4.15.9-last-phase-evidence.md` for the whole plan, with every duty section quoted, and added `v4.15.9-coordinator-deltas.md` (agent counts, CHANGELOG, todos, seven proposed known gaps).
- The full profile found three failures this plan caused: stale handbook evidence hashes and two integration tests that asserted the old agent pass-through. All were fixed and rerun green. The remaining failures are pre-existing or environmental; the evidence file lists each with its reason.
- Ticked: T029, T031, T032, T034 to T037. Left for the coordinator: T030 (apply the proposed gaps to `known-gaps.md`), T033 (pipeline reconciliation), T038 (publication).

## Plan delta

Incomplete, blocking for the full Goal: the measured run (T027) waits on spend approval. No other delta.

## Verification

- `python -B scripts/ci/run.py --profile full --quiet`: "FAIL: 63 passed, 12 failed, 4 skipped" (dispositions in the evidence file). `tests/validators` rerun alone: "5 failed, 4541 passed, 10 skipped", all 5 in one pre-existing Windows process-tree test.
- Fast profile after the fixes: 18 passed, 0 failed. `check_handbooks.py`: exit 0.

## CI impact

No pipeline change. No new command or dependency.
