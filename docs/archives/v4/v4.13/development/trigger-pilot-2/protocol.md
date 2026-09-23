# Trigger pilot 2 protocol (frozen before scoring)

**Date**: 2026-09-23
**Owner**: catalog maintainer
**Purpose**: Test whether an explicit named-skill invocation cue repairs the under-triggering measured in the first v4.13 pilot.
**Status**: frozen before the first scored call; run aborted after the second reported call. Any later change to prompts, candidate text, model ids, caps, or criteria invalidates the comparison.

## Inputs and isolation

The four sampled skills, 24 prompt texts and classes, two model tiers, seeded order, and isolated Claude CLI runner are the same as the first pilot. The 24 prompt records in `pilot-prompts.json` equal the first pilot's prompt records; JSON formatting and the freeze date differ. Control A stages the current `SKILL.md` files from this commit. Candidate B changes only the four `description:` lines to put a direct instruction to invoke the named skill on a matching task before the existing purpose and boundary language. The result is attributed to that full description change, not to any single phrase.

The runner's `--setting-sources project`, `--strict-mcp-config`, fixture scope, observed `Skill` selectors, 180-second per-call timeout, USD 0.50 per-call limit, pre-call aggregate reservation, 96-call maximum, and 120-minute wall-clock limit remain in force. This run has one aggregate USD 35.00 ceiling. No separate paid calibration is authorized. A partial run is `UNMEASURED` and cannot promote B. The runner preserves a partial result if the ceiling or time limit stops it.

## Acceptance criteria

Score each model separately from its own contemporaneous A and B arms. A positive prompt should invoke the target skill; a near-miss or trivial-edit prompt should not. B qualifies on a model only if all conditions hold:

1. B retains every target-skill selection that A made on a positive prompt.
2. B gains at least one additional positive target-skill selection among that model's eight positives.
3. B makes no more target-skill selections than A among that model's 16 near-miss and trivial-edit prompts.
4. Every scored row terminates cleanly with an observed selector, and no B response loses a trust boundary or required verification step relative to A.

These criteria are possible even when A has zero false positives. If a model fails any condition, no description is promoted for that model. A fully observed no-win run is `MEASURED_NO_CHANGE`; it is a valid measurement but not a catalog edit. The original 2026-09-16 raw data remains immutable and is not used as a concurrent control.

## Limits

This is a one-host synthetic trigger test, not a claim about answer quality, general catalog behavior, or other models. The recorded `Skill` selector proves invocation only; it does not prove the model used the skill well. Missing selector evidence, model errors, and budget-truncated responses remain unknown rather than being counted as negative selections.

## Run disposition

The 2026-09-23 attempt stopped after the first two printed strong-tier rows. Both returned `selected=None`; their reported costs were USD 0.6540 and USD 0.6292 despite the USD 0.50 per-call limit. The runner was interrupted immediately after that discrepancy was observed. It did not write a results JSON file before interruption. See `attempt.md` for the bounded receipt. No candidate was measured or promoted.
