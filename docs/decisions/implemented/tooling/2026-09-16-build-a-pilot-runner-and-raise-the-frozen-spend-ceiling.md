# Decision: Build a pilot runner, and raise the frozen spend ceiling to the measured cost

Status: implemented - `scripts/run_trigger_pilot.py` wraps the already-authenticated `claude` CLI to supply the five controls the v4.13.0 Phase 6 entry gate required, and the frozen aggregate ceiling rose from USD 10 to USD 35 on measured per-call cost with explicit maintainer authorization

## Problem

The v4.13.0 plan's Phase 6 asks a question only a live model can answer: does rewriting a skill's description change whether an agent selects it? The plan guarded that phase with a fail-closed entry gate requiring five controls at once (two model tiers, observed organic selection, bounded subprocess time, an enforceable aggregate spend ceiling, and isolation), and recorded `NOT QUALIFIED` after inspecting two repository scripts.

The plan also drew a boundary around itself, twice. Its implementation entry prerequisite states:

> A generic CLI adapter is not assumed to add missing observability or accounting. [...] **Building an adapter** or changing the two-model/cost/evidence contract **requires a separately scoped decision; it is outside this plan.**

and its construction-debt ceiling permits only "one standard-library trace demo, small synthetic fixtures, and focused extensions to existing tests".

Phase 6 then did both excluded things: it built a roughly 350-line runner and raised the frozen aggregate spend ceiling. No task line in the plan created the decision record that its own prerequisite demanded, so none was written. An independent Goal-vs-codebase review in Phase 7 found the omission. This record is that decision, written late and saying so.

## Decision

Build the runner, and raise the ceiling to the measured cost of the frozen matrix.

Two facts drove it.

**The `NOT QUALIFIED` disposition rested on an incomplete inspection.** It examined `run_trigger_evals.py` and `optimize_skill_description.py` and never examined the `claude` CLI's own `stream-json` output or its `--max-budget-usd` flag. Both supply the controls recorded as missing: the `init` event echoes the resolved model and enumerates loaded skills, a skill invocation appears as a tool call, `result.total_cost_usd` is summable against a running ceiling, and `--setting-sources` / `--add-dir` / `--strict-mcp-config` isolate the run. The CLI, not a new backend, is the qualified native path; the runner is a wrapper that introduces no credential, provider, or account.

**The residual constraint was cost, not capability**, which is a different and better-evidenced finding than the plan started with. Three calibration calls measured the real per-call price, and the frozen 96-call matrix projected to roughly USD 33 against a USD 10 ceiling. The run would have stopped a third of the way through and recorded `UNMEASURED`. A ceiling set before anyone measured anything is not a safety property; it is a guess that would have converted a fully funded experiment into no experiment at all.

The raise was authorized explicitly by the maintainer after the measured projection was presented, and recorded as Amendment 1 to the frozen protocol. The scored run finished at USD 20.6709.

## Alternatives considered

**Record Phase 6 as UNMEASURED and ship the plan without it.** Honest, cheap, and what the entry gate literally said to do. Rejected because the gate's premise was factually wrong: a capability the plan called absent was present and unexamined. Declaring an outcome unmeasurable when the measurement is available and affordable is not caution, it is an unchecked assumption wearing caution's clothes. The plan's whole thesis is that guidance changes on measured evidence; shipping it with its one measurable claim unmeasured would have undercut the thesis.

**Keep the USD 10 ceiling and shrink the matrix to fit.** Two skills instead of four, or one model tier instead of two. Rejected on statistical power: the control arm turned out to select on 1/8 and 3/8 of its own positive prompts, so a quarter-size matrix would have produced counts indistinguishable from noise, and a single tier would have hidden the per-model split the acceptance criteria explicitly forbid averaging away.

**Substitute a cheaper model for the strong tier.** Proposed and failed on measurement: `claude-sonnet-5` cost USD 0.6554 per calibration call against `claude-opus-5` at USD 0.5850. Cost is dominated by roughly 77,000 cache-creation tokens per invocation, not by the model's token rate, so the assumed saving does not exist. Recorded because the reasoning behind it is correct in general and wrong here, and only measurement distinguishes the two cases.

**Raise the ceiling quietly.** Rejected, and worth naming because it is the easy path. A budget raised without a record is indistinguishable from a budget that was never enforced. The amendment states the old value, the new value, the measured evidence, the authorization, and the rejected alternative.

**Extend one of the two existing scripts instead of writing a new one.** Rejected because both are wrong at the contract level rather than merely incomplete. `run_trigger_evals.py` is model-free by design. `optimize_skill_description.py` passes `--skill <path>`, which forces the skill to load and so destroys the exact signal the pilot measures; adding a timeout and a ledger to it would have produced a tool that still could not answer the question.

## Consequences

The runner spends real money and makes network calls, so it must never reach an end-user install. It is registered in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` with that reason recorded inline. That allowlist is the one legitimate answer to the repository's rule that every new `scripts/*.py` is registered in both installers.

A Phase 7 adversarial pass then found six defects in the two scripts this decision authorized, each confirmed by reproduction and fixed with a regression test (`BG-1` to `BG-6` in the v4.13 known-gaps ledger). One generalizes beyond this tool: the runner's selection matcher was a substring test over the whole serialized tool call, so it could have counted a different skill's invocation as a selection. A measurement tool's own defects are indistinguishable from the phenomenon it measures unless something attacks it, and that attack happened in the deep pass rather than before the money was spent. The recorded run's auditability limit is carried as `WN-5`.

The boundary the plan drew was right in spirit and this record does not retire it. What the plan should have said is that crossing it requires evidence and a decision record, not that it can never be crossed. A plan that states a requirement in prose but creates no task for it will not produce the artifact.
