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

The source study measured 1,009 correct-to-wrong transitions and 1,486 wrong-to-correct transitions across 12 fixed-interval summarization calls, so 40.4 percent of those transitions degraded. This is a cited source result, not a Nexus-Hub measurement. See insights S14 and S16 in the [v4.10.1 comparison](../../../../../docs/releases/v4/v4.10/comparisons/v4.10.1-comparison-eval-isolation-and-adaptive-compaction.md#section-4---evidence-and-insights).
