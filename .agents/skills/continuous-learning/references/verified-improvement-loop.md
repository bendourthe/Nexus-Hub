# Verified Improvement Loop

How a confirmed local observation becomes a candidate change, gets checked by something other than itself, and ends as either a permanent regression case or a byte-exact rollback. Read this cold: it assumes no other part of the learning skill is in context.

This file connects existing owners. It defines no new optimizer, trains nothing, and schedules nothing. Each step names the skill that owns it; where a step is owned elsewhere, follow the link rather than re-deriving the method here.

## What this loop is not

Stated first, because every one of these is a plausible next step that this loop deliberately does not take:

- **No automatic base-instruction edits.** The immutable base stays immutable. A candidate proposes a change to the learned layer; a human accepts it.
- **No model training or fine-tuning.** The artifact is a text change, not a weight update.
- **No background observer.** The only observer is the agent in this session, per the owning skill's hard constraint.
- **No scheduler and no provider routing change.** The loop runs when a human runs it.

## The chain

Seven links. The point of the loop is that they are connected by stable identifiers, so a reviewer can walk from "why did we change this" to "what proved it" without trusting a summary.

| # | Link | Identifier | Owner |
|---|---|---|---|
| 1 | Confirmed observation | `observation_id` | this skill |
| 2 | Minimized regression | `regression_id` | `[[ai-output-evaluation]]` (`references/error-analysis.md`) |
| 3 | Rubric and split version | `rubric_version`, `split_manifest` | `[[ai-output-evaluation]]` (`references/evaluator-validation.md`) |
| 4 | Candidate diff | `candidate_id` | this skill |
| 5 | Replay result | `replay_id` | `[[skill-eval-loop]]` |
| 6 | Disposition | `approved` or `rejected` | the user |
| 7 | Rollback target | `rollback_ref` | this skill |

A link with no identifier is a claim. The record below is the minimum that makes each one checkable.

## Step 1: Start from a labeled observation, not a hunch

The loop begins only from an observation already carrying an explicit `success` or `failure` label with its evidence, per the outcome-labeling rule in the owning `SKILL.md`. An unlabeled observation does not enter this loop, and a label is never inferred from tone or from the fact that an event was captured.

Scope the candidate to the **approved learned layer**. If closing the observation would require editing the immutable base, that is a proposal for a human to consider separately, not a candidate this loop can carry.

## Step 2: Minimize before you generalize

Reduce the failure to the smallest input that still reproduces it, using the minimization procedure in `[[ai-output-evaluation]]`'s `references/error-analysis.md`. Record it as `regression_id`.

Minimization is what separates a fix from a coincidence. A candidate validated against the full original scenario may be passing for a reason nobody isolated, and the resulting regression case then guards a scenario rather than a behavior.

The minimized case belongs to the **train or development pool**. It never enters the held-out split; the graduation rule in `evaluator-validation.md` owns that boundary and the reason for it.

## Step 3: Freeze what you are measuring against

Record `rubric_version` and the `split_manifest` before scoring the candidate. A rubric edited between the baseline run and the candidate run produces two numbers that are not comparable, and nothing in the output says so.

Where the checker is a model judge, its sensitivity is a precondition, not a detail: see Step 6 of `evaluator-validation.md`. An uncalibrated judge accepting a candidate is the loop validating itself.

## Step 4: Produce the smallest candidate

Apply the smallest-relevant-edit and plan/apply disciplines the owning `SKILL.md` already sets. One candidate closes one observation. Record `candidate_id` and the exact diff.

Before applying anything, record `rollback_ref`: the precise prior state, by content hash, of every file the candidate touches. Capture it **before** the edit. A rollback target derived after the fact is a reconstruction.

## Step 5: Replay against an independent checker

Run the paired comparison through `[[skill-eval-loop]]`, which owns paired runs and graduation. Record `replay_id`.

**The checker must be independent of the candidate.** Reusing the candidate's own score as evidence that the candidate worked is circular, and it is the single easiest mistake to make here because the number is already sitting there. Independence means a deterministic oracle, a separate rubric, or a human label that did not see the candidate's self-report.

Three results must be distinguishable:

| Result | Meaning |
|---|---|
| The seeded failure now passes **and** existing regression cases still pass | candidate is supported |
| The seeded failure passes but an existing case broke | candidate traded one failure for another; not an improvement |
| The seeded failure still fails | candidate did not do what it claimed |

Budget and iteration caps for the replay belong to `[[loop-engineering]]`. Do not invent a second cap here.

## Step 6: Dispose explicitly

The user approves or rejects. Silence is not approval.

- **Approved.** The minimized case graduates into the permanent regression set, within the pool it already belonged to. The instinct records `regression_id` and `replay_id` as its supporting evidence.
- **Rejected.** Restore `rollback_ref` exactly. Byte-exact restoration is the requirement, not "revert the intent": a rejected candidate that leaves reformatted whitespace behind has changed the file, and the next diff attributes that change to whoever touches it next.

Record the rejection. A rejected candidate is a result about the hypothesis, and a loop that only records its successes reads as though every idea worked.

## Step 7: Fail closed on conflicts

Three conditions stop the loop rather than resolving themselves:

- **Duplicate identifier.** The same `observation_id`, `regression_id`, or `candidate_id` used twice fails closed. Do not overwrite the earlier record.
- **Conflicting disposition.** One candidate recorded both approved and rejected is a contradiction, not a later decision winning. Resolve it with the user.
- **Missing owner.** If a step's owning skill is unavailable, record the coverage gap by name and stop. Do not reconstruct that owner's rules from memory, and do not mint a promoted learning on partial coverage.

## Worked record

One synthetic example of the complete chain. Identifiers are stable and every field is checkable.

```yaml
observation_id: OBS-2026-0914-001
label: failure
evidence: "failure | 2026-09-14T10:22Z: gate reported pass while the suite had not run"
learned_layer_scope: approved
immutable_base_touched: false

regression_id: REG-0031
regression_pool: development        # never held_out
minimized_from: OBS-2026-0914-001

rubric_version: rubric-v4
split_manifest: split-2026-09-14    # frozen before scoring
judge_sensitivity: measured          # see evaluator-validation.md Step 6

candidate_id: CAND-0044
candidate_scope: "one instinct file"
rollback_ref:
  - path: .nexus/instincts/verify-before-claiming.yaml
    sha256_before: 9f2c...           # captured BEFORE the edit

replay_id: RPL-0091
checker: deterministic_oracle        # independent of the candidate
seeded_failure_now_passes: true
existing_regressions_still_pass: true

disposition: approved
approved_by: user
graduated_to: regression_set
```

The rejected path differs in three fields and nothing else:

```yaml
candidate_id: CAND-0045
replay_id: RPL-0092
seeded_failure_now_passes: false
disposition: rejected
rollback_applied: true
sha256_after_restore: 9f2c...        # equals sha256_before, byte for byte
```

That last line is the one worth checking. If the post-rollback hash does not equal the pre-edit hash, the rollback did not happen, whatever the disposition says.

## Verification

- [ ] Every entering observation carries an explicit `success` or `failure` label with evidence
- [ ] The candidate touches only the approved learned layer; the immutable base is unchanged
- [ ] A minimized regression exists, with an id, in the train or development pool and never the held-out split
- [ ] `rubric_version` and the split were frozen before the candidate was scored
- [ ] `rollback_ref` hashes were captured before the edit, not reconstructed after
- [ ] The replay checker is independent of the candidate, not the candidate's own score
- [ ] The three replay outcomes are distinguishable in the record
- [ ] An approved candidate graduated within its existing pool; a rejected one restored byte-exact prior content
- [ ] Rejections are recorded, not discarded
- [ ] Duplicate identifiers, conflicting dispositions, and unavailable owners failed closed

## Related

- `[[ai-output-evaluation]]` -- owns minimization (`error-analysis.md`) and judge calibration (`evaluator-validation.md`)
- `[[skill-eval-loop]]` -- owns paired runs and graduation
- `[[loop-engineering]]` -- owns iteration and budget caps
- `[[verification-before-completion]]` -- owns the fresh-evidence rule behind every claim in this loop
