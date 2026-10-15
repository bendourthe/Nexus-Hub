# Improvement heuristics (step 9)

After each iteration's viewer review, `feedback.json` plus `benchmark.json` plus `analyzer.md` (the analyzer sub-agent's report) are the structured input to skill improvement. Apply these five heuristics in priority order; stop at the first one that fits the failure pattern observed.

## H1: Pushy descriptions (under-trigger fix)

**Symptom**: at least one `should_trigger: true` eval failed because the skill did not trigger (the `with_skill` run output looks identical to the `without_skill` run; the agent never loaded the skill body).

**Fix**: apply the AGENTS.md A14 rule. The description is too narrow. Rewrite to:

1. Lead with the action ("Drive a structured evaluation loop ...").
2. List trigger phrases verbatim ("Use whenever the user wants to evaluate a skill, benchmark a skill, A/B test a skill, optimize a skill description, run an eval set ...").
3. Cover synonyms and adjacent intents (not just "evaluate" - also "score", "benchmark", "iterate", "regression").
4. End with an explicit `SKIP:` clause for the look-alike intents the skill should NOT handle.

**Worked example**: a `should_trigger: true` eval with `query: "score this skill against my prompts"` did not trigger because the description used "evaluate" but not "score". Adding "score a skill against test prompts" verbatim to the description fixed the under-trigger on the next iteration.

**Validate**: re-run the same iteration's `evals.json` after the rewrite. Trigger rate on the previously-failing eval should jump to 1.0. If it does not, the issue is upstream of the description (the CLI's skill-loading mechanism may be the bottleneck) and H1 is not the right heuristic.

## H2: Explain the why (mechanical-output fix)

**Symptom**: outputs technically pass assertions but the user marked the eval `wrong-direction` in `feedback.json`. The skill is being followed mechanically without the underlying reasoning.

**Fix**: every numbered step in `## Instructions` should answer **why** before **what**. Replace:

```
3. Spawn paired runs.
```

with:

```
3. Spawn paired runs. The marginal-value question - "did the skill help?" - can only be answered when the with-skill run has a same-prompt baseline to compare against. Without the baseline, you have a demo, not an eval.
```

The "why" sentence should cite the failure mode the step prevents. Generic "this is best practice" framing does not improve outputs.

**Worked example**: a skill body listed "Step 4: Capture timing and tokens" with no rationale. Outputs followed the step but omitted the field whenever the CLI did not natively report tokens. Adding "without these the analyzer cannot detect time/token regressions" to step 4 produced outputs that estimated tokens with a `tokens_estimated: true` flag instead of skipping the field.

**Validate**: outputs on the next iteration should show explicit reasoning ("I estimated tokens because ..." rather than just doing or not doing the step).

## H3: Repeated-work elimination (variance fix)

**Symptom**: the analyzer reports high `time_ms_stddev` or `tokens_stddev` on a specific eval, AND the eval's outputs differ in length / structure run-to-run despite the skill being followed.

**Fix**: the skill is doing the same lookup or transformation more than once. Find the deterministic step in `## Instructions` that the agent is re-deriving each run, and ship it as a tier-3 `scripts/<step>.py` resource per the AGENTS.md A13 / A17 conventions. The agent then EXECUTES the script (deterministic, low-token) instead of re-reasoning the step from scratch (high-variance, high-token).

**Worked example**: a skill instructed the agent to "compute the trigger rate from `evals.json`" - in iteration 1 the agent wrote 40 lines of inline Python; in iteration 2 it wrote 52 lines doing the same thing slightly differently. Bundling `scripts/trigger_rate.py` and changing the instruction to "run `scripts/trigger_rate.py <evals.json>`" cut tokens 60% and dropped duration variance to near zero.

**Validate**: re-run the iteration. `tokens_stddev` should drop noticeably; `tokens_mean` should drop too because the script execution does not consume context tokens (per A17's tier-3 affordance).

## H4: Negative-space coverage (over-trigger fix)

**Symptom**: at least one `should_trigger: false` eval triggered anyway. The skill loaded on a query it should not have answered.

**Fix**: expand the description's `SKIP:` clause. The current `SKIP:` covers the obvious negatives but missed an adjacent look-alike. Add the over-triggered query's intent to the skip list verbatim.

**Worked example**: a `should_trigger: false` eval with `query: "explain the eval results to me"` triggered the skill because the description matched on "eval". Adding `"SKIP: explaining a finished evaluation, summarizing prior results"` to the description prevented the over-trigger on the next iteration.

**Validate**: trigger rate on the negative eval should drop to 0. If positive evals also stop triggering after the SKIP expansion, the SKIP clause swallowed real positives - back off and use a more specific phrase.

## H5: Assertion calibration (no-discrimination fix)

**Symptom**: every assertion passes on every run (with_skill AND without_skill), so `pass_rate_delta` is near zero. The skill might be helping or might not be - the assertions cannot tell.

**Fix**: the assertions are too loose. Replace at least one with a sharper invariant that the without-skill baseline can plausibly fail. Examples of sharp assertions:

- "Output cites at least one trigger phrase from the description" (only the with-skill run has the description loaded)
- "Output produces a structured artifact (JSON, table, or numbered list) instead of a paragraph"
- "Output mentions at least one of the skill's named sub-stages"

Avoid loose assertions like "Output is helpful" or "Output is correct" - the grader sub-agent cannot evaluate those reliably.

**Worked example**: an iteration showed `with_skill_pass_rate: 0.95` and `without_skill_pass_rate: 0.93` - the skill appeared to help by 2%, well within noise. Replacing the loosest assertion ("Output addresses the user's question") with a sharp one ("Output uses the three-stage structure with explicit stage labels") opened a real gap: 0.85 vs 0.20 in the next iteration.

**Validate**: `pass_rate_delta` should grow on the next iteration. If it stays flat, the skill genuinely is not adding value - which is a useful finding, not a failure of the heuristic.

## Priority order and stop condition

Apply heuristics in this order: **H1 -> H4 -> H2 -> H5 -> H3**. Trigger fixes (H1, H4) unblock everything downstream; output-quality fixes (H2, H5) need triggering to work first; variance fixes (H3) need stable outputs first. Apply at most ONE heuristic per iteration so the next iteration's metrics can attribute the change. Bundling two fixes in one iteration produces a confounded result.
