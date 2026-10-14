# Session history - v4.13.0 Phase 3: Approved lessons to regression evidence

**Date**: 2026-09-15
**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Phase**: 3 of 7 (candidate A2)
**Branch**: `feat/v4.13.0-evidence-driven-agent-improvement`

## What was implemented

| Task | Artifact | Outcome |
|---|---|---|
| T009 | `continuous-learning/references/verified-improvement-loop.md` | Seven-link chain connecting existing owners by stable identifier; explicit non-goals (no base-instruction edit, training, observer, scheduler) |
| T010 | `tests/fixtures/agent-improvement/improvement-lifecycle.json` | Original, repaired and two rejected cases, plus duplicate-id and conflicting-disposition fail-closed cases |
| T011 | `skill-eval-loop/SKILL.md` | Graduation stays in its original pool; held-out never becomes tuning input; chain identifiers carried onto eval records; missing owner blocks promotion |
| T012 | `test_evidence_driven_improvement.py` | Extended to 88 tests with a deterministic disposable-file replay |

## Test results

```
$ python -m pytest -q tests/skills/test_evidence_driven_improvement.py --no-cov
88 passed in 0.60s

$ python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 66 warnings)
```

## Troubleshooting

One failure during the phase, classified **fixture defect** rather than IMPL or TEST. `CAND-0046` was declared `expected_existing_checks_pass: true`, but its content contains `Assume the suite passed`, which trips `CHK-3`. The oracle derived `existing_ok = False` and the assertion failed.

The fixture was corrected, not the oracle. This is the intended behavior of an independent checker, and it is worth recording as positive evidence: had the oracle read the candidate's declared expectation instead of deriving the result, the error would have passed silently, which is exactly the circularity the recipe warns about.

## Plan delta

**Disposition: No delta.**

**Evidence considered**: sub-task 3.1 names four owners to reuse by reference (`error-analysis.md` for minimization, `evaluator-validation.md` for calibration, `skill-eval-loop` for paired runs, `loop-engineering` for caps). All four exist at the stated paths and carry the rules the recipe defers to, so no reconstruction from memory was needed and no coverage gap had to be recorded. Sub-task 3.3's requirement that existing user-approval, immutable-base and verifier-independence gates be preserved was satisfied by adding to the graduation section rather than rewriting it; a test asserts each of the three original gates is still present.

Sub-task 3.2's constraint that checker evidence be "an independent deterministic oracle, not a copied candidate score" turned out to be load-bearing rather than cautionary, as the troubleshooting note above shows.

**Consequence for remaining phases**: none. Phases 4 and 5 touch different owners.

## Deviations

None. All four sub-tasks were implemented in their stated scope. No skill was retired, per the phase constraint.

## Next steps

Phase 4: smallest useful visual explanation (T013-T016).
