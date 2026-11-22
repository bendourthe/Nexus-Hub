# v4.15.9 Phase 5 (reduced): measured run not executed

Started 2026-11-18T00:04Z.

## Done

- T026: the observable signal was chosen without spending anything. Transcripts carry per-subagent token counts and an effort key; recorded in `v4.15.9-measured-effort-run.md`.

## Not done

- T027: both arms are unrun (spend cap USD 0, and T003 is deferred). The measurement file says so and claims no delta.

## Verification

- `validate_unicode_safety.py --strict` on the measurement file and the fast profile passed (see below).
- The Verification Expectation (two arms, delta, spend at or under USD 10) is not met by design; the file records the gap.

## CI impact

No new commands, dependencies, or test paths.

## Completion pass (2026-11-21)

- T003 landed in `0e74c9d99`, so both arms are now runnable. T027 is still not run: it spends real usage (bound USD 10, 6 subagent spawns), and this lane spends nothing without a recorded budget. The measurement file names the spend approval as the only blocker.
- T027 is must-ship, so Phase 5 is not complete. Its exit items for "All sub-tasks", the Verification Expectation, and "Ready to advance" stay unticked. Phase 6 runs anyway and records the blocker.

## Plan delta

Incomplete, blocking for the full Goal: the cost claim has no measurement until the spend is approved. Recorded as a proposed QG gap in `v4.15.9-coordinator-deltas.md`. Consequence for Phase 6: the Goal review reports the claim as unmeasured.

## Verification (completion pass)

- `python -B scripts/validate_unicode_safety.py --strict --root . --path docs/releases/v4/v4.15/development/v4.15.9-measured-effort-run.md`: exit 0.

## CI impact (completion pass)

No new commands, dependencies, or test paths.
