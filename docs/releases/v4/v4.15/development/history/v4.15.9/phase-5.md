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
