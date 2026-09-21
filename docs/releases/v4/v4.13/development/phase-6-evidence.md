# Phase 6 Evidence -- Bounded skill-trigger and context-loading pilot

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A3
**Phase**: 6 of 7
**Prior phase commit**: `dea58528` (verified ancestor of HEAD)

This is the one phase of the plan that invoked live models. 96 calls were made against two model tiers at a measured cost of USD 20.6709. The outcome is `MEASURED_NO_CHANGE`: the candidate failed its frozen criteria and nothing was promoted.

## Artifacts

| File | SHA-256 (first 16) | Bytes |
|---|---|---|
| `scripts/run_trigger_pilot.py` | `b216de4c8af1452f` | 13311 |
| `development/pilot-prompts.json` | `085c8b6ae5afed42` | 5054 |
| `development/pilot-variant-b.json` | `5ae5f526415e761a` | 3122 |
| `development/trigger-pilot-results.json` | `3ac205d12b6eebd2` | 68890 |

The frozen protocol is `development/trigger-pilot-protocol.md` (with amendment 1); the narrative result is `development/trigger-pilot-results.md`. Neither is re-stated here.

## Entry gate: resolved on capability

The plan held T001 until a native execution path supplied five controls at once, and Phase 1 recorded `NOT QUALIFIED` after inspecting two repository scripts. That inspection had not examined the `claude` CLI's structured output or its budget flag. Both do supply the missing controls, so the disposition is now **resolved on capability**, and the residual constraint turned out to be cost.

| Control | Mechanism | Demonstrated by |
|---|---|---|
| Two accessible model tiers | `--model`; `init` event echoes the resolved model | every result record carries `model_id` |
| Observed selection | `init` enumerates loaded skills; invocation appears as a tool call | `selected` and `tools_used` per record |
| Bounded subprocess time | `subprocess(timeout=180)` plus `--max-budget-usd 0.50` | 0 timeouts across 96 calls |
| Aggregate spend ceiling | runner sums `result.total_cost_usd` and refuses a call that would breach | `total_spend_usd` 20.6709 under a 35.00 ceiling |
| Isolation | `--setting-sources project`, `--add-dir <fixture>`, `--strict-mcp-config` | fixture-scoped corpus; `skills_available` 17, not the full catalog |

## Commands run

Scored run, from the plan worktree (a sibling directory outside the repository and outside any vendor directory):

```
$ python scripts/run_trigger_pilot.py \
    --protocol docs/releases/v4/v4.13/development/trigger-pilot-protocol.md \
    --out docs/releases/v4/v4.13/development/trigger-pilot-results.json
```

Summary read back from the written results file:

```
calls: 96/96   spend: $20.6709   complete=True   evidence-missing: 0
```

Phase gate checks, all from the plan worktree (a sibling directory outside the repository and outside any vendor directory):

```
$ python scripts/validate_skills.py --bundles-only
Scanned 337 skills under catalog\skills (bundle audit)
RESULT: PASS (0 errors, 66 warnings)
exit 0

$ python scripts/validate_unicode_safety.py --strict --verbose --path docs/releases/v4/v4.13/development
Scanning 16 text file(s) under <worktree root>...
validate_unicode_safety: clean (16 file(s) scanned, 0 warning(s), 0 errors).
exit 0

$ python -m pytest tests/skills/test_evidence_driven_improvement.py -q --no-cov
161 passed in 1.36s

$ python scripts/ci/run.py --profile fast --quiet
PASS: 15 passed, 0 failed, 0 skipped, 0 advisory in 145.9s
exit 0
```

Regression check across both suites that reference this plan's artifacts, run to completion rather than inferred from an absence of failures:

```
$ python -m pytest tests/skills/ tests/validators/ -q --no-cov
3772 passed, 32 skipped in 1670.67s (0:27:50)
exit 0
```

The 66 bundle warnings are the pre-existing catalog-wide count, unchanged by this phase; no skill file was edited.

### Two corrections the fast profile forced

`validate_no_personal_paths` failed on the first run with 11 findings, and both causes were mine.

The first was in **this phase's own documents**: the worktree's absolute path appeared in the evidence and session-history files. It is redacted.

The second was **pre-existing and more interesting**. Phase 5's evidence file described fixing a synthetic sentinel that looked like a real home path, and quoted the offending value verbatim in its diagnosis. Quoting a guard finding back into the tree re-creates exactly the condition the guard exists to catch, so `validate_no_personal_paths` was still failing while that file claimed it now exited 0. Both quotes are redacted and the correction is recorded in place rather than silently amended.

After both corrections the profile is clean.

## Tests added, and why these

Phase 6 changed no catalog behavior, so there was no skill wording to assert. What it produced is a **measurement**, and a measurement rots in two specific ways that prose cannot catch.

**A results document can claim numbers its own raw data does not support.** `TestTriggerPilotDocumentMatchesItsData` recomputes every headline count from `trigger-pilot-results.json` and compares it with the figure the document prints. The disposition itself is derived rather than trusted: `test_criterion_one_failure_is_derivable_not_asserted` checks that variant B genuinely selects fewer positives than A on both models, so `MEASURED_NO_CHANGE` is a conclusion from the data and not a sentence someone typed.

**A "promote nothing" disposition can be quietly contradicted later.** `TestNothingWasPromoted` asserts that none of the four candidate descriptions appears in its shipped `SKILL.md`.

**Correction made in Phase 7.** The sentence that stood here claimed each of those checks was "paired with a mutation control that plants the candidate text into a copy and confirms the check trips, so a predicate that could never match is itself caught". That claim was false. The control asserted `candidate in (shipped + candidate)`, which is true regardless of what the real check does, and the same tautology ran in six other places as `needle not in text.replace(needle, "")` -- a property of `str.replace` that holds whether or not the needle was ever in the file. An independent review found it. The controls now call the predicate under test against both the real and the planted text, and `assert_has_teeth` asserts the needle IS present before asserting it is gone. Recorded here rather than silently rewritten, because a false confidence claim inside an evidence file is the specific failure this plan exists to prevent.

`TestTriggerPilotRunIntegrity` guards the distinction the runner was built around: `selected` is `None` for evidence-missing and `False` for an observed non-selection, and `test_no_selection_is_evidence_missing` fails if any record ever conflates them. `test_the_two_arms_differ_only_in_the_sampled_corpus` is the regression test for the defect described below.

24 tests were added; the module now holds 161.

## The defect that would have voided the spend

The runner initially had **no implementation of variant B**. It staged a single corpus and pointed both arms at it, which would have compared A against A across all 96 calls and returned a confident null result measuring nothing. Variant B existed as a frozen definition in `pilot-variant-b.json` and as prose in the protocol, but not as code.

This was caught before any scored call, by checking that the two staged corpora actually differed. `stage_variant()` was added: variant A is copied verbatim, variant B replaces only the `description:` line of each sampled skill. Both arms were then verified to differ, and to differ in exactly one line per skill.

`test_the_two_arms_differ_only_in_the_sampled_corpus` is the permanent form of that check. It reads the corpus hashes recorded with every result and fails if the control and candidate hash sets are equal. A null result from two identical arms is indistinguishable from a null result from a real comparison, which is why this check runs on the data rather than on the runner.

## Cost, and a rejected optimization

| Tier | Model | Calls | Total | Mean |
|---|---|---|---|---|
| fast | `claude-haiku-4-5-20251001` | 48 | USD 3.1715 | USD 0.0661 |
| strong | `claude-opus-5` | 48 | USD 17.4994 | USD 0.3646 |

Cost is dominated by roughly 77,000 cache-creation tokens per invocation, not by output or by the model's token rate. `cache_read_input_tokens` was 0 on every call, so each invocation paid full context creation.

Substituting a cheaper second tier was proposed and **failed on measurement**: `claude-sonnet-5` cost USD 0.6554 per calibration call against `claude-opus-5` at USD 0.5850. The saving that proposal assumed does not exist. This is recorded because the reasoning behind it ("a cheaper model costs less per call") is correct in general and wrong here, and the only way to know which applies is to measure.

## CI impact

No pipeline file was edited; CI/CD is not this phase's deliverable.

| Added | Covered by current profiles? |
|---|---|
| `tests/skills/test_evidence_driven_improvement.py` (24 new tests, same module) | Yes. Already collected by the existing `pytest tests/` step in the `full` profile. |
| `scripts/run_trigger_pilot.py` | Partially. It is a maintainer tool that spends money and makes network calls, so it must **not** run in CI. It is not referenced by any profile and needs no step. |
| `development/*.json`, `development/*.md` | Yes, by the Markdown and Unicode checks already in the profiles. |

No new dependency, environment variable, or CI secret is introduced.

`scripts/run_trigger_pilot.py` is a repository-internal tool and must not reach `~/.nexus-hub/scripts/`, because a distributed copy would put a spend-incurring runner on a user's machine. The repository's rule is that every new `scripts/*.py` is registered in both installers unless it is explicitly allowlisted, and `test_installer_smoke.py` enforces that in both directions. The runner was therefore added to `DEV_ONLY_SCRIPTS` with its reason, rather than left to fail the guard or, worse, copied to satisfy it:

```
$ python -m pytest catalog/hooks/tests/test_installer_smoke.py -q --no-cov
33 passed in 0.55s
```

## Limitations

- 24 synthetic prompts, two models, one host, one session configuration. Not a general claim about description style and not a claim about other providers.
- Selection is measured; answer quality is not. A model that handles a request well without invoking the skill records as a non-selection.
- Grading was mechanical but not blinded: the runner labels each record with its variant.
- The missing-delegate prompt (`sda-n1`) discriminated nothing between variants, since all four cells correctly declined to select. It did confirm that no arm fabricated coverage for a skill that does not exist.
- Two frozen caps (aggregate spend, total wall clock) were amended on measured evidence before the scored run, with explicit authorization, and are recorded in the protocol as amendment 1. No criterion, prompt, skill, variant, or model was changed.

## Gaps recorded

| Gap | What it records |
|---|---|
| DF-1 | **Resolved.** The entry prerequisite is satisfied; the pilot ran to completion. |
| QG-1 | **Resolved.** All four criteria were evaluated per model. |
| WN-3 | The shipped catalog under-triggers (1/8 fast, 3/8 strong on its own positive prompts) with zero false positives, and the remedy `AGENTS.md` prescribes measured **worse** on both models. Recorded, not acted on. |
| WN-4 | Criterion 3 was unreachable by construction, because the control produced no irrelevant loads to reduce. A defect in the protocol's assumption, not a property of the candidate. |
