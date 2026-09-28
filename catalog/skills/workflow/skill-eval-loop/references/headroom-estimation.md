# Oracle headroom estimation

Use this method before investing in a new eval gate or a materially more complex gate. It estimates the gate's ceiling: the best result available if the policy could make the ideal decision at every opportunity using information unavailable to the real policy.

## Procedure

1. Define the current policy, its decision opportunities, its inputs, and the metric the proposed gate is meant to improve. Freeze the cases, model, trials, and scoring method before comparing policies.
2. Construct a perfect-information oracle for the narrow decision the gate would control. For every opportunity, inspect the completed outcome and choose the action that would have produced the ideal decision. State exactly what information the oracle uses that the deployable policy cannot know at decision time.
3. Replay the same cases and fixed opportunities with only the oracle decision substituted. Do not give the oracle a different model, more trials, a changed schedule, or a different rubric.
4. Measure `oracle_gain = oracle_score - current_policy_score`. The oracle score is the proposed gate's measured ceiling under those fixed opportunities; `oracle_gain` is the maximum available improvement for that decision surface.
5. Compare the ceiling with implementation cost, operational risk, and measurement uncertainty. A small or uncertain ceiling is evidence to stop or simplify the gate, not a reason to tune against the held-out set.
6. Preserve the current-policy and oracle receipts, the opportunity list, the oracle rule, and the recompute command. Label the result preliminary when the sample is too small for a meaningful interval.

## Worked evidence and qualification

The adoption comparison's source S15 (section 4.1, Table 3) reported an oracle that suppressed summarization whenever the current answer was already correct and otherwise followed the same fixed-interval schedule. It scored 11.5 points above the fixed-interval policy.

That result is a lower bound on a more capable adaptive policy, not a universal 11.5-point promise. The oracle decided only whether to act at an already fixed opportunity; it did not choose when an opportunity should occur. A fully adaptive policy could control both timing and action, so its theoretical ceiling is wider than the measured subset.

## Relationship to regression gates

Locked regression sets and per-slice floors answer whether an existing gate became worse on protected behavior. Oracle headroom answers whether a proposed gate has enough possible gain to justify building. Keep both: a large ceiling does not prove the implementation is safe, and a green regression floor does not prove further gate complexity is worthwhile.

## Verification

- [ ] Current and oracle policies use the same cases, model, trials, schedule of opportunities, and scoring method.
- [ ] The oracle's unavailable information and ideal-decision rule are written explicitly.
- [ ] Current score, oracle score, oracle gain, receipts, and recompute command are recorded.
- [ ] The report distinguishes a fixed-opportunity oracle from a fully adaptive policy.
- [ ] The decision to build, simplify, or stop follows the measured ceiling rather than an assumed upside.
