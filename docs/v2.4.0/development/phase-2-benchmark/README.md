# Phase 2 Benchmark - Multi-Agent Code Review Pipeline

Verification record for the `multi-agent-code-review` review pipeline (Phase 2 / T012, Stability Gate). This is an LLM-judged benchmark, not a unit test: it confirms that persona reviewers, dispatched over a seeded fixture and constrained to the findings-schema contract, surface the planted findings, stay in their lane, and leave the clean control untouched.

## Fixture

[seeded_diff.py](seeded_diff.py) contains three deliberately-planted cases:

| Function | Planted defect | Owning persona |
|---|---|---|
| `paginate()` | Correctness: off-by-one (`page * size` skips the first page for 1-based pages) | correctness |
| `find_user()` | Security: SQL injection (user input concatenated into the query) | security |
| `clamp()` | None (false-positive control) | (none should flag it) |

## Method

Two personas were dispatched in parallel over the fixture, each told to review only its lens and return ONLY a JSON array per the [findings-schema](../../../../catalog/skills/code-review/multi-agent-code-review/references/findings-schema.md):

- correctness persona -> the `code-reviewer` agent (always-on correctness lens).
- security persona -> the `security-reviewer` agent (conditional security lens, selected because the fixture touches a SQL query).

## Result: PASS

| Check | Expected | Actual |
|---|---|---|
| Correctness finds the `paginate` off-by-one | 1 finding, P0/P1, on the offset line | 1 finding, P1, confidence 100, on the offset line |
| Security finds the `find_user` SQL injection | 1 finding, P0, on the query line | 1 finding, P0, confidence 100, on the query line |
| Personas stay in lane | correctness ignores SQLi; security ignores off-by-one | correctness reported only the off-by-one; security reported only the SQLi (explicitly deferred the off-by-one to another persona) |
| Clean control `clamp()` | no substantiated finding from either persona | zero findings on `clamp()` from both |
| Findings-schema contract | all required fields; `confidence` a discrete anchor | both findings valid; `confidence` = 100 (discrete) |
| Late confidence gate | both seeded findings >= anchor 75 -> surface | both at 100 -> surface |

### Observations

- Per-diff persona selection worked: the security lens was the right conditional choice for a query-touching change, and it found the injection while the correctness lens did not stray into it.
- The discrete confidence anchors were respected (both 100 = proven, backed by an unambiguous contract violation / exploit).
- Both personas marked the findings `pre_existing: true` because the benchmark passed a whole file with no diff base; in a real run the resolved base ref distinguishes new vs pre-existing lines. This is a fixture artifact, not a pipeline defect.

## Not covered here (deferred)

- A full end-to-end run of all stages (intent discovery, all conditional personas, the independent validation pass, model tiering) with the complete dedicated persona-agent set was not run, because the dedicated `*-reviewer` persona agents ship as catalog templates and are not registered as dispatchable subagent types in the authoring harness. The two reused agents (`code-reviewer`, `security-reviewer`) that ARE dispatchable were used to validate the contract and the lens-discipline end to end.
- Cross-reviewer agreement promotion was not exercised (the two seeded findings are on different files/lines, so they do not share a fingerprint). The promotion rule is specified and deterministic in [confidence-anchored-scoring](../../../../catalog/skills/code-review/code-quality/references/confidence-anchored-scoring.md) section 3.
- Live `skill-eval-loop` trigger runs are deferred consistent with v2.4.0 DF-v24-1 (no model CLI on PATH in the authoring environment); a static trigger-surface check was done instead (see the Phase 2 session history).
