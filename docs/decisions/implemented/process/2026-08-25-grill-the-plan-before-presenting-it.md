# Decision: Critique and grill every generated plan before presenting it

Status: implemented - shipped as `implementation-plan` Step 4.5 for v4.1.0.

## Problem

Nexus-Hub generated plans and presented them. Between writing the draft and asking "does this phase breakdown look right?", nothing challenged the plan.

The pieces to challenge it already existed and were not wired together:

- `plan-review` runs seven persona lenses over a written plan and returns severity-tagged findings, and nothing invoked it from the planning path.
- `design-interview` is a full interview engine whose description already listed `"grill me"` as a trigger phrase. `implementation-plan` referenced it in **Related Skills only**, which is prose, not a call site.

So the practical state was: a plan was interrogated exactly when the user thought to ask, and most plans were never interrogated at all. The first real challenge arrived during implementation, which is the most expensive place to discover that phase 3 assumed something phase 1 did not build.

A second problem sat underneath. The request that prompted this work asked for a `grill-me` command that "automatically runs to challenge the plan". That sentence contains a conflict: grilling is **interactive** and waits for the user, while challenging a plan for robustness wants to happen whether or not anyone is at the keyboard. Treating them as one thing produces either a gate that stalls unattended runs with nothing accomplished, or a "grill" that asks speculative questions because it never looked at the document.

## Decision

`implementation-plan` gains **Step 4.5**, between writing the draft and confirming it. Two stages, in order, both automatic:

1. **Critique (autonomous).** Invoke `plan-review` on the just-written file. Needs no user input, so it completes on an unattended run.
2. **Grill (interactive).** Invoke `design-interview` with the stage-1 findings as its **seeded first round**. Findings needing a human choice become numbered questions with recommended answers. Findings the draft already answers do not become questions.

Results are folded back into the plan before Step 5. A declined finding is recorded as a parked branch or a known gap, never dropped silently. If either delegate is unavailable, the gate says which stage is uncovered rather than improvising the missing one.

Seeding is the load-bearing part. An unseeded grill asks what the agent imagines might be missing. A seeded grill asks about gaps seven independent lenses found in this specific document, which the user can usually answer from knowledge they already hold.

## Alternatives considered

**Offer the grill instead of running it, with the critique automatic.** This was the recommendation put to the user, because it degrades cleanly: an unattended plan is still fully critiqued and never blocks. The user chose fully automatic on both stages, accepting the stall. Recorded here because the trade-off is real and may be revisited: the cost is that a plan generated while nobody is present stops at the gate until someone returns. The gate states this in the skill body rather than hiding it, and ordinary interview steering ("enough on this branch", "park that") shortens a grill without skipping it.

**Ship a standalone `grill-me` skill.** Rejected; see [`../../rejected/process/2026-08-25-standalone-grill-me-skill.md`](../../rejected/process/2026-08-25-standalone-grill-me-skill.md). It would have been a fourth owner of one concern.

**Run only the autonomous critique and skip the interview.** Cheaper and never stalls, but findings and decisions are different things. A plan can be internally coherent and still leave the vendor, the failure mode, or the cut-line undecided. The lenses cannot decide anything; they can only report. Skipping the interview leaves every decision-shaped finding open while the plan looks reviewed.

**Run only the interview and skip the critique.** This is what the upstream pattern does, and it is what the original request described. It produces speculative questions, and it makes the agent's blind spots and the draft's blind spots the same blind spots, since the same model wrote both. The critique is what makes the questions evidence-backed.

**Put the gate in the `/plan` dispatcher rather than the skill.** Rejected as a layering violation. `catalog/commands/plan.md` is a thin dispatcher by contract; duties belong in the retained skill. The dispatcher states the guarantee and links.

**Add a lifecycle check to `plan-review` for "was this plan grilled?".** Rejected as circular: `plan-review` is one of the two stages, so it cannot also be the auditor of whether the pair ran. The Verification checklist in `implementation-plan` owns that assertion.

## Consequences

- Every generated plan is critiqued, and its open decisions are resolved, before the user is asked to approve a phase breakdown.
- A plan generated unattended stops at stage 2. This is the accepted cost of the chosen configuration, stated in the skill body and in the `/plan` guarantee section.
- `design-interview` gained the frontier-round algorithm in the same change, so a seeded round of twelve independent findings costs one round rather than twelve turns.
- Step 5 now reports what the gate changed, so a reader can tell a scrutinized plan from an unscrutinized one.
- `plan-review` stays read-only. It finds; the interview decides; the planning step applies.
