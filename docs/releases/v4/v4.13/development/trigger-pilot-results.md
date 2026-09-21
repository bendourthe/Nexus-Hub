# Trigger pilot results

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A3
**Phase**: 6 (T022, T023)
**Protocol**: [trigger-pilot-protocol.md](trigger-pilot-protocol.md) (frozen 2026-09-16, amendment 1 recorded)
**Run date**: 2026-09-16
**Raw data**: [trigger-pilot-results.json](trigger-pilot-results.json)

## Disposition: MEASURED_NO_CHANGE

The pilot ran to completion. Variant B failed its frozen acceptance criteria on **both** models and is **not promoted**. No description or pointer change is applied to any sampled skill. No cosmetic edit is made in place of the measured result.

This is a valid answer to the question the phase asked, not a failure to answer it.

## Run integrity

| Property | Value |
|---|---|
| Calls planned | 96 |
| Calls made | **96** |
| Failures / timeouts | **0** |
| Evidence-missing (selection unknown) | **0** |
| Stopped early | no |
| Aggregate spend | **USD 20.6709** of USD 35.00 authorized |
| Seed (call order) | 4131 |

Every call produced a terminal `result` event, so every selection value is an observation rather than an inference. The runner records absent evidence as `null`, distinct from `false`; that case did not arise.

### Cost

| Tier | Model | Calls | Total | Mean |
|---|---|---|---|---|
| fast | `claude-haiku-4-5-20251001` | 48 | USD 3.1715 | USD 0.0661 |
| strong | `claude-opus-5` | 48 | USD 17.4994 | USD 0.3646 |

The strong tier came in below the USD 0.585 calibration estimate, which is why the run finished at USD 20.67 rather than the projected USD 32.7.

## Result against the frozen criteria

Correct behavior is defined by the frozen prompt classes: a **positive** prompt should select the skill; **near-miss** and **trivial-edit** prompts should not.

| Model | Variant | Positive selections | Irrelevant loads |
|---|---|---|---|
| fast | A (control) | **1 / 8** | 0 / 16 |
| fast | B (candidate) | **0 / 8** | 0 / 16 |
| strong | A (control) | **3 / 8** | 0 / 16 |
| strong | B (candidate) | **1 / 8** | 0 / 16 |

| Criterion | fast | strong |
|---|---|---|
| 1. No loss of positive selections | **FAIL** (1 to 0) | **FAIL** (3 to 1) |
| 2. No increase in irrelevant loads | pass (0 to 0) | pass (0 to 0) |
| 3. At least one strict reduction in irrelevant loading or pauses | **FAIL** | **FAIL** |
| 4. No trust-boundary or verification loss | pass | pass |

Two criteria fail on both models, so B is rejected per model and in aggregate. Results are reported per model and are not averaged; there is no direction in which averaging would rescue this one.

Criterion 3 could not have been met by any variant: control A already produced **zero** irrelevant loads across all 32 of its near-miss and trivial-edit prompts, leaving no reduction available. That is a defect in the criterion's assumption rather than in variant B, and it is recorded as such.

### Per skill

Positive selections, control to candidate:

| Skill | fast | strong |
|---|---|---|
| `context-engineering` | 1/2 -> 0/2 | 1/2 -> 1/2 |
| `html-output-conventions` | 0/2 -> 0/2 | 0/2 -> 0/2 |
| `plan-before-code` | 0/2 -> 0/2 | 0/2 -> 0/2 |
| `skill-description-authoring` | 0/2 -> 0/2 | **2/2 -> 0/2** |

The largest single regression is `skill-description-authoring` on the strong model: the control selected it on both of its positive prompts, and the candidate on neither.

## What the candidate assumed, and what the data says

Variant B rewrote each description to lead with the action, carry explicit verbatim trigger phrases, and close with a `SKIP:` clause fencing off the look-alike prompts. That is the house style `AGENTS.md` prescribes, and the expectation was fewer irrelevant loads at unchanged positive selection.

The measurement contradicts it. Irrelevant loading was already zero and could not improve; positive selection **fell** on both models. Pushier descriptions with explicit SKIP clauses made selection worse. Shipping this on intuition would have degraded the skills it was meant to improve, which is the outcome the whole phase exists to prevent.

## The larger finding: the catalog under-triggers

The control arm is the more consequential result.

| Model | Control positive selection rate |
|---|---|
| fast | **1 / 8 (12.5%)** |
| strong | **3 / 8 (37.5%)** |

The **currently shipped** descriptions fire on roughly one in eight to three in eight prompts that sit squarely in their own territory, while producing **zero** false positives across 32 near-miss and trivial-edit prompts.

The catalog's real problem is therefore **under-triggering, not over-triggering**. `AGENTS.md` already asserts this ("Claude has a measurable tendency to under-trigger when the description is narrow, clean, or implicit") and prescribes pushier descriptions as the fix. This pilot is the first measured evidence for the diagnosis, and simultaneously evidence **against** that prescribed remedy: the pushier variant made it worse.

Both halves matter. The diagnosis is confirmed; the remedy is not, so the mechanism is something other than description wording alone.

Folded into this phase as a recorded finding rather than acted on: changing the authoring guidance would need its own measured pilot, and this run produced no candidate that earned promotion.

## Limitations

These bound what may be claimed from the numbers above.

- **Synthetic prompts on one host.** 24 prompts, two models, one machine, one session configuration. Not a general claim about description style, and not a claim about other models or providers.
- **Selection is measured, not answer quality.** The signal is a `Skill` tool call naming the skill under test. A model that handles a request correctly *without* invoking the skill records as a non-selection. That is the right measure for "did the skill trigger" and the wrong measure for "was the answer good".
- **Variant order was seeded and shuffled, but grading was not blinded.** The runner labels each result with its variant. The scoring is mechanical (a tool call either names the skill or does not), so the exposure is low, but it is not a blinded comparison.
- **The missing-delegate prompt was uninformative.** `sda-n1` names a skill that does not exist; all four cells correctly declined to select, so the case discriminated nothing between variants. It did confirm no arm fabricated coverage.
- **The selection matcher was looser than the claim it supported, and the recorded run cannot be re-audited for it.** An adversarial review in Phase 7 found that the runner scored a selection with `skill in json.dumps(tool_input)`, a substring test over the whole serialized `Skill` call. A call that invoked a DIFFERENT skill while merely mentioning this one in a prompt argument would have been counted. The matcher now compares the field that names the skill, and a regression test covers both directions.

  The defect can only ever produce a false POSITIVE, never hide a real selection, so every count above is an **upper bound**. What can be checked in the recorded data was checked: the `Skill` tool was invoked exactly **5 times across all 96 calls**, those 5 are precisely the 5 rows scored as selected, every one falls on a positive prompt for the skill under test, and there is no row where `Skill` was invoked without a selection being scored. A mis-scored row would have to be one of those five invoking some other skill while naming this one. The tool-call payloads were not retained, so this is a bounded argument rather than proof, and it is recorded as an open gap rather than waved away.

  Direction of any residual error: control arm A could only be equal or lower than reported, which would narrow rather than widen the gap that criterion 1 failed on. The zero irrelevant loads across 32 near-miss and trivial-edit prompts is the other side of the same evidence, since a trigger-happy matcher would have inflated exactly those.

- **Two frozen caps were amended before the scored run** (spend USD 10 to 35, wall clock 60 to 120 minutes), on measured cost evidence and with explicit authorization. Both are recorded in the protocol's amendment 1. No acceptance criterion, prompt, skill, variant, or model was changed.

## What was built to make this measurable

The plan recorded Phase 6 as `NOT QUALIFIED` because no available path supplied five controls at once. That disposition is now **resolved on capability**: `scripts/run_trigger_pilot.py` wraps the CLI's structured output to provide all five, and the residual constraint was cost rather than capability.

One defect found before the run is worth recording, because it would have invalidated the entire spend: the runner initially had **no implementation of variant B**. It staged one corpus and ran both arms against it, which would have compared A with A and returned a confident null result measuring nothing. Variant B existed as a definition and not as code. Staging was added and verified before any scored call: both arms differ, and they differ in exactly one line, the `description:` field.
