# Harness Feedback Cadence

This guide defines an offline protocol for comparing when test feedback reaches a coding harness: during construction or only at the final gate. It is for maintainers who plan a future live study and for agents running the synthetic matrix under `tests/fixtures/harness_pairings/v4.15.3-cadence/`. Key topics: contract inheritance, cadence definitions, frozen inputs, retained records, uncertainty, named dependency gap, claims this release makes, requirements for a live study.

## Contract Inheritance

The protocol runs on the shared pairing evaluator, `scripts/evaluate_harness_pairings.py`, and inherits its contract: serial trials, disposable workspaces, trusted adapters, workload-owned grading, immutable per-trial receipts, one aggregate receipt, and refusal to run live without an isolation backend and a hard spend limit. The evaluator's code and its contract test, `tests/integrations/test_harness_pairing_contract.py`, are the authority; this guide adds no second engine and changes none of its rules.

The evaluator code and contract test used to build the matrix are the ones on `develop` at commit `c76edae2b` (v4.15.2). Their sha256 prefixes at admission were `2f9e773b5fd2dbef` for `scripts/evaluate_harness_pairings.py` and `c8d13432fdf4055d` for the contract test.

## Cadence Definitions

- **Construction-time feedback:** the harness runs the project's checks while it works, can see a failing result, and may repair before it declares the work finished.
- **Final-gate feedback:** the harness sees check results only after it declares the work finished, and may not repair afterward.

Both cadences face the same final acceptance: one independent, workload-owned evaluator, bound by `workload.evaluator_hash`, that sees only the files the trial left behind. A harness's own claim of success is never an input. Feedback during a trial may come from the harness's own checks; it never replaces the final evaluator.

## Frozen Inputs

Freeze every item below in the manifest before any future live study starts. The synthetic manifest records them under `cadence_protocol.frozen`.

- Requirements and examples for the workload.
- The grader and its hash.
- Effort and settings for the harness and model.
- Memory and skill state, with the same state for both cadences.
- Paired order, set by the manifest's `order_policy` and `seed`.
- Budgets for time, turns and spend.
- Repeat minimum, at least the evaluator's `MIN_REPEATS` of 3.
- Repair policy: at most one repair per trial, and only after delivered feedback.
- Stopping rules: a timeout is a rankable failure and is never retried; a trial id is immutable; a rerun of a run id is refused.

Pairings that differ in any comparability field of the evaluator's environment identity, such as retry policy or concurrency, are incomparable and get no recommendation.

## Retained Records

For every trial, keep:

- Initial acceptance, meaning the first delivered feedback result, and post-repair acceptance, meaning the last one. Keep both even when they agree.
- Every failure, including trials that time out, with the evaluator's failure fingerprint.
- The count and step position of feedback deliveries and of repairs.
- Elapsed time.
- Tokens and spend with their provenance. A spend figure that is unavailable stays unavailable and never becomes zero. Missing authoring and maintenance labor stays missing.

Spend per accepted artifact is undefined when no artifact is accepted. It is a descriptive ratio, not a prediction of retry cost.

## Uncertainty

Use the evaluator's methods unchanged: Wilson 95 percent intervals for success rates and bootstrap intervals for the other measures. A comparison with fewer than three rankable repeats, or whose intervals overlap on the tie-break, yields no recommendation.

## Named Dependency Gap

The evaluator runs one adapter and one final evaluator per trial. Its receipt has no field for feedback timing, initial versus post-repair acceptance, feedback or repair counts, tokens, or spend provenance beyond cost, and its adapter protocol allows only a fixed set of fields. This plan does not modify the engine, so the synthetic matrix works around the gap in two ways:

- The two cadences are two adapter profiles inside one manifest, with the same workload and evaluator hashes.
- The fake adapter performs a real check against its workspace at the steps its schedule permits and writes a sidecar history. The tests read that sidecar and refuse a trial with no history, a prewritten result that never delivered feedback, a construction trial whose first feedback came after finish, and a final-gate trial whose feedback came before finish.

A live study needs the evaluator contract to carry these records in its own receipts. Until then the sidecar is scaffolding, and no live result may rely on it.

## Claims

This release claims no live reliability, no savings, no ranking and no default change. The fixture's outcomes are authored per trial index and are labeled synthetic. They show that the protocol executes and rejects invalid comparisons, nothing about any model or harness.

## Running The Synthetic Matrix

From the repository root:

```powershell
python -m pytest tests/skills/test_harness_cadence_protocol.py -q
```

Expected: all tests pass with no network call, credential, or paid runner.

## Future Live Study

A live study needs its own approval and all of the following, separately stated:

- Exact models and workloads.
- An enforced spend limit that the provider or adapter applies before spend, not after.
- Credentials injected only through an isolation backend.
- Containment proven by that backend.
- Authority from the maintainer.

The evaluator already refuses a live manifest that lacks the backend or the limit.
