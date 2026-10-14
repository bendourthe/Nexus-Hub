# Session History -- Phase 6: bounded skill-trigger pilot

**Date**: 2026-09-16
**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Phase**: 6 of 7 (T021-T024)
**Branch**: `feat/v4.13.0-evidence-driven-agent-improvement`
**Worktree**: the plan worktree (a sibling directory outside the repository and outside any vendor directory)
**Evidence**: [phase-6-evidence.md](../phase-6-evidence.md)

## What this phase was for

The plan's central claim is that agent guidance should change only on measured evidence. Phase 6 is where that claim is tested against the plan's own catalog: four skills, two instruction-bundle variants, two model tiers, 24 frozen prompts, and a per-model acceptance rule fixed before any model output was seen.

Phases 1 to 5 could be verified deterministically. This one could not, which is why it had been sitting deferred since 2026-09-08.

## Steps taken

1. **Re-examined the entry gate.** The Phase 1 inspection had concluded `NOT QUALIFIED` after reading two repository scripts. It had never examined the `claude` CLI's `stream-json` output or `--max-budget-usd`. Both supply the controls that were recorded as missing, so the gate resolved on capability.
2. **Froze the protocol** (T021): four skills with hashes, two variants, 24 prompts in three fixed classes, two model tiers, caps, isolation controls, four acceptance criteria.
3. **Built the runner.** `scripts/run_trigger_pilot.py` wraps the CLI, enforces the aggregate ceiling from `result.total_cost_usd`, and records `selected=None` for evidence-missing separately from `False` for an observed non-selection.
4. **Calibrated cost.** Three probe calls established the real per-call price. The frozen USD 10 ceiling was under a third of what the frozen matrix costs, so the run would have stopped partway and recorded UNMEASURED.
5. **Amended two caps with authorization** and recorded amendment 1 in the protocol.
6. **Ran the full 96-call matrix** (T022). 96/96 complete, 0 failures, 0 evidence-missing, USD 20.6709.
7. **Recorded `MEASURED_NO_CHANGE`** (T023) and promoted nothing.
8. **Wrote tests, evidence, and gaps** (T024).

## Troubleshooting

### The runner compared A against A

The runner staged one corpus and pointed both arms at it. Variant B existed as a frozen definition and as prose, but not as code. Left alone it would have spent the full budget and returned a confident null result measuring nothing, and the null would have looked exactly like a real one.

Caught by checking that the two staged corpora actually differed, before any scored call. `stage_variant()` was added; both arms were verified to differ in exactly one line per skill, the `description:` field. The permanent form is `test_the_two_arms_differ_only_in_the_sampled_corpus`, which reads the corpus hashes recorded with every result.

### A cheaper model was more expensive

Swapping the strong tier for `claude-sonnet-5` was proposed to cut cost, and measured **higher**: USD 0.6554 against `claude-opus-5` at USD 0.5850. Cost here is dominated by roughly 77,000 cache-creation tokens per invocation, not by the model's token rate, so the usual reasoning does not apply. The strong tier stayed as frozen.

### A synthetic sentinel tripped a real guard

A sentinel written as a POSIX home-directory path ending in an SSH private key is shaped exactly like real personal data, which is what the repository's personal-path guard exists to catch. The guard was right. The sentinel was changed to `/srv/secrets/SENTINEL-private-key.pem`, which keeps its purpose without resembling personal data. The guard was not suppressed. (Carried over from Phase 5; recorded here because it shaped how the pilot fixture was written.)

## Result

| Model | Variant | Positive selections | Irrelevant loads |
|---|---|---|---|
| fast | A (control) | 1 / 8 | 0 / 16 |
| fast | B (candidate) | 0 / 8 | 0 / 16 |
| strong | A (control) | 3 / 8 | 0 / 16 |
| strong | B (candidate) | 1 / 8 | 0 / 16 |

Criteria 1 and 3 fail on both models. Variant B is not promoted. Disposition `MEASURED_NO_CHANGE`.

## Plan delta

**Disposition: Incomplete, non-blocking.**

The plan's entry prerequisite recorded the pilot as unqualified on capability. That was wrong in a recoverable way: the inspection behind it was incomplete, having read two repository scripts without examining the CLI's own structured output or budget flag. The real constraint was cost, which is a different and better-evidenced finding than the plan began with.

**Evidence**: `development/phase-1-evidence.md` names `run_trigger_evals.py` and `optimize_skill_description.py` as the two paths inspected. Neither the `stream-json` output shape nor `--max-budget-usd` appears in that record.

**Consequence for remaining phases**: none blocking. Phase 7's known-gaps reconciliation (T026) must pick up DF-1 and QG-1 as **resolved**, not carry them forward as open, and must treat WN-3 and WN-4 as new open items from this phase. The plan's own statement that "building an adapter ... is outside this plan" was honoured: the runner wraps an existing authenticated CLI and introduces no new credential, provider, or account.

**A second delta, recorded rather than fixed**: the plan's acceptance criterion 3 assumed a baseline of over-triggering. The measurement contradicts that assumption, and the criterion was therefore unsatisfiable by any candidate. This is WN-4. It did not change the outcome, because variant B independently failed criterion 1.

## What the result means

The interesting finding is in the control arm, not the candidate. The shipped catalog fires on roughly one in eight to three in eight prompts that sit squarely in its own territory, with zero false positives across 32 look-alike prompts. `AGENTS.md` already asserts that under-triggering is the catalog's failure mode; this is the first measured evidence for it.

It is also evidence against the remedy the same document prescribes. The pushier candidate, with verbatim trigger phrases and explicit SKIP clauses, made selection worse on both models. Shipping that on intuition would have degraded the four skills it was meant to improve.

Both halves are recorded as WN-3 and neither is acted on here. Changing the authoring guidance needs its own pilot, designed against this data.

## Next steps

- Phase 7 (T025-T034): architecture refactor, known-gaps reconciliation, living docs, git hygiene, CI/CD reconciliation, the Tier 3 deep pass, the Goal-vs-codebase review, human-testing suggestions, full-suite stabilization, then publication and integration.
- WN-3 and WN-4 are carried into Phase 7's reconciliation as open items owned by the catalog maintainer.
