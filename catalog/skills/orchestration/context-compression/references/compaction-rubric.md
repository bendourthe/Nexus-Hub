# Compaction Fire/Suppress Rubric

Compaction is irreversible: anything not preserved in the summary is gone. After compaction, the agent resumes from the governing instructions, the task, the summary, and the continuation prompt, not from the discarded trajectory.

Evaluate all four conditions against the current trajectory. Every YES answer requires a verbatim quotation from the trajectory. An answer without a quotation defaults to NO because a self-assessment with no evidence requirement can be satisfied by assertion alone.

| Condition | Question | YES evidence |
|---|---|---|
| CLOSED-UNIT | Did the latest operation reach an observable boundary, with its result recorded and no announced action still in flight? | Quote the completed tool, test, task, commit, or verification result and the recorded outcome. Mid-sentence intent such as "Let me now check..." is NO. |
| SUMMARIZABLE | Can the work resume without losing eliminating evidence? | Quote the decisions, state, and constraints that capture the live path. If value is dispersed across dead-end queries or negative results needed to avoid retries, answer NO. |
| PROGRESS | Did the latest completed unit create a new observation, change test state, eliminate a hypothesis, or advance the deliverable? | Quote the before/after result or newly established fact. |
| STUCK | Does the same failure signature appear in at least three of the last four attempts without a new observation or test-state change? | Quote the matching signature from each qualifying attempt and show that no intervening attempt changed the observation or test state. |

## Fire rule

Compact only when CLOSED-UNIT, SUMMARIZABLE, and PROGRESS are all YES, and STUCK is NO. Otherwise suppress compaction and continue, change approach, or surface the blocker. In particular, compacting while STUCK masks the stuck state instead of resolving it.

Both timing extremes fail. Reactive compaction waits until the context is already saturated with stale tokens. Periodic compaction discards indiscriminately and can interrupt a live subgoal. The evidence gate selects a completed, resumable boundary between those extremes.

The source study measured 1,009 correct-to-wrong transitions and 1,486 wrong-to-correct transitions across 12 fixed-interval summarization calls, so 40.4 percent of those transitions degraded. This is a cited source result, not a Nexus-Hub measurement. See insights S14 and S16 in the [v4.10.1 comparison](../../../../../docs/archives/v4/v4.10/comparisons/v4.10.1-comparison-eval-isolation-and-adaptive-compaction.md#section-4---evidence-and-insights).

## Summary preservation rules

1. **Carry verification debt forward.** If a result was found but not verified, say explicitly that verification is still required. Dropping that marker turns an unverified claim into an apparently settled fact for every later turn; `[[verification-before-completion]]` remains the owner of whether evidence supports a claim.
2. **Do not infer.** Include only information explicitly present in the trajectory; omit missing or unclear information rather than reconstructing it from assumptions, guesses, or inference. An inferred statement in a summary is indistinguishable from an observed one.
3. **Preserve the resolved result verbatim.** When the trajectory reaches a concrete result, copy that result exactly instead of paraphrasing it. Paraphrase can change the value the resumed agent is meant to use.

The verification-debt rule concerns what crosses the claim boundary. It does not decide whether an agent must re-check its own reasoning mid-turn; that separate question remains WN-2 in the v4.9 known-gap ledger.

## Staged evaluation order

Apply these stages in order:

1. **Cheap deterministic preconditions.** Consult the judgment rubric only after iteration 3, when the running prompt is at least 40,000 tokens, when no summary has yet been created, and when at least 2 rounds have elapsed since the last probe. These are the source study's values, not Nexus-Hub-validated thresholds: the iteration and token floors avoid spending a judgment call when the answer is obviously no, the summary cap prevents repeated lossy rewrites, and the round interval prevents probe churn.
2. **Evidence-gated rubric.** If every precondition passes, evaluate CLOSED-UNIT, SUMMARIZABLE, PROGRESS, and STUCK using the quoted-evidence rule above.
3. **Hard backstop.** Force compaction once the running prompt crosses 0.30 times the context window, regardless of the rubric verdict. This is the source study's override, not a Nexus-Hub-validated threshold; a judgment gate that may decline forever otherwise declines into overflow. `[[context-degradation]]` owns the separate severity thresholds, so use its table by reference rather than copying it here.

## Probe hygiene

The self-assessment must not remain in the trajectory it judges. Append the probe to a copy of the trajectory, or remove both probe and verdict after a CONTINUE decision, so the rolling context is unchanged when no compaction occurs. This is mandatory whenever the fire/suppress rubric is used: without it, every declined probe adds self-assessment text, the context grows because the agent checked whether it was too large, and the next probe judges a trajectory partly composed of previous probes.

The staged values, backstop, preservation rules, and probe procedure are source-derived. See insights S7-S13 in the [v4.10.1 comparison](../../../../../docs/archives/v4/v4.10/comparisons/v4.10.1-comparison-eval-isolation-and-adaptive-compaction.md#section-4---evidence-and-insights).
