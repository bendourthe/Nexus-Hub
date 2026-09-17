# Known gaps - v4.13

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-09-16

Release-scoped gaps for the evidence-driven agent improvement plan. Planned future-phase work is tracked in the plan rather than reported as completed here.

## v4.13.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 6 |
| Warnings (WN) | 5 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 2 | 1 |

### Open Items

#### WN-2: Tool-span attributes unverified at the pinned revision

**Source phase**: Phase 2. **Plan reference**: T005. **Reason**: the `gen_ai.tool.*` attribute table could not be retrieved at pinned revision `5ca9052bc796ef1e497200b1d558fd87a201f335`. The containing document truncates before that section and the standalone tool-spans path returns HTTP 404 at that revision. The `execute_tool` operation name itself is confirmed.

**Owner**: `ai-agent-development` maintainer. **Status**: open. **Suggested next step**: the first consumer needing a `gen_ai.tool.*` attribute verifies it against the sibling inference/tool specification and adds it to `references/agent-span-contract.md` with its requirement level. Until then the contract marks those attributes unverified, and no requirement level was invented to fill the gap.

#### WN-3: The shipped catalog under-triggers on its own positive prompts

**Source phase**: Phase 6. **Plan reference**: T022, T023. **Reason**: the pilot's control arm is the currently shipped corpus. Across four sampled skills and eight positive prompts it selected the skill on **1/8** with the fast model and **3/8** with the strong model, while producing **zero** irrelevant selections across all 32 near-miss and trivial-edit prompts. The catalog's measured failure mode is under-triggering, not over-triggering.

**Evidence**: `development/trigger-pilot-results.md` and the raw `trigger-pilot-results.json` (96/96 calls, 0 failures, 0 evidence-missing). The regression is concentrated in `skill-description-authoring` on the strong model, 2/2 to 0/2 under the candidate wording.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: this finding is recorded, not acted on. `AGENTS.md` prescribes pushier descriptions with explicit SKIP clauses as the remedy, and the pilot measured that remedy making selection **worse** on both models, so the prescribed fix is now evidence-contradicted. Changing the authoring guidance needs its own frozen pilot with a candidate designed against this data; nothing in this release may change a description on the strength of the finding alone.

#### WN-4: Acceptance criterion 3 was unreachable by construction

**Source phase**: Phase 6. **Plan reference**: T021. **Reason**: the frozen protocol requires "at least one strict reduction in irrelevant loading or unnecessary pauses". The control arm produced zero irrelevant loads, so no reduction was available to any candidate and the criterion could not be satisfied regardless of the candidate's quality. The criterion assumed a baseline of over-triggering that the measurement then contradicted (see WN-3).

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: a future trigger pilot states its criteria relative to a measured baseline rather than an assumed one, or measures the baseline in a calibration slice before the criteria are frozen. The criterion is recorded as a defect in the protocol, not as a property of variant B; variant B independently failed criterion 1, which is what actually decided the disposition.

#### WN-5: The recorded pilot run cannot be re-audited for the loose selection matcher

**Source phase**: Phase 7. **Plan reference**: T030 (Tier 3 deep pass, adversarial step). **Reason**: the runner scored a selection with a substring test over the whole serialized `Skill` tool input, so a call invoking a different skill while mentioning the target would have counted. The matcher is fixed and covered by tests, but the recorded 96-call run did not retain tool-call payloads, so its five positive rows cannot be re-checked directly.

**What is known**: the `Skill` tool was invoked exactly 5 times across all 96 calls; those 5 are exactly the 5 rows scored as selected; each falls on a positive prompt for the skill under test; no row shows a `Skill` invocation without a scored selection. The defect can only inflate a positive, never hide one, so all reported counts are upper bounds and control arm A could only be equal or lower.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: retain the `Skill` tool input alongside `tools_used` in any future run so the question is answerable from the data. Do not re-run the pilot for this alone; the disposition `MEASURED_NO_CHANGE` does not turn on it, because a lower A would narrow the gap criterion 1 already failed on.

#### WN-6: Symlink refusal is unproven on Windows without developer mode

**Source phase**: Phase 7. **Plan reference**: T030. **Reason**: two new tests covering the trace script's symlinked-target refusal and its redirected-ancestor disclosure `skip` on a Windows host that does not permit creating a symlink. They run on the Linux and macOS CI legs.

**Owner**: `ai-agent-development`. **Status**: open. **Suggested next step**: confirm the two tests execute rather than skip in the CI `tests` job; if the Windows leg must cover them, the runner needs developer mode or an elevated step, which is a CI change outside this plan.

#### QG-2: A timed-out CI step reports nothing at all

**Source phase**: Phase 7. **Plan reference**: T029, T033. **Reason**: in `scripts/ci/run.py`, the `subprocess.TimeoutExpired` handler returns at line 100, before the `[ok ] / [FAIL]` rendering block at line 122. A step killed by its timeout therefore increments the failed count while naming neither itself nor its reason. The entire output of a two-step failure is `FAIL: 0 passed, 2 failed, 0 skipped, 0 advisory in 6300.2s`.

**Cost observed**: diagnosing two unnamed failures took two full profile runs and two standalone suite runs, roughly four hours, to establish something the runner already knows. It constructs `status="timeout"` and `reason=f"exceeded {cmd.timeout}s"` and never prints either.

**Owner**: repository maintainer, via `[[cicd-architect]]`. **Status**: open. **Suggested next step**: print the timeout the same way a failure is printed, for example `[TIME] <name> (<duration>s) exceeded <cap>s`. Proposed and deliberately NOT applied in this phase: `scripts/ci/run.py` is pipeline infrastructure, and this phase's own rule is that a pipeline change requires explicit per-change approval, which was not given.

#### QG-3: The `full` profile's test budgets are exceeded on a loaded workstation

**Source phase**: Phase 7. **Plan reference**: T033. **Reason**: `hook-tests` (cap 1800s) measured 1961.5s and `repo-tests` (cap 4500s) measured 5970.3s on the development host, so the `tests` group cannot pass there even though every assertion passes. `scripts/ci/profiles.py` records a measured Windows baseline of 3341.7s for `repo-tests`; this host ran 79 percent above it while other workloads were resident.

**Evidence**: 1319 passed / 35 skipped and 5805 passed / 101 skipped / 0 failed when the two suites are run directly.

**Owner**: repository maintainer, via `[[cicd-architect]]`. **Status**: open. **Suggested next step**: decide deliberately whether the caps describe CI runners only, in which case document that a contended workstation is expected to exceed them, or whether local runs are meant to fit, in which case the budget needs re-measuring on a quiet machine. Do NOT raise the cap from a contended host's timing: that tunes a shared guard to the slowest observation and removes the protection the cap exists to provide. Not caused by this plan, which added roughly 180 tests running in about one second against a 2600-second overshoot.

### Resolved Items

#### DF-1: Phase 6 trigger pilot deferred as UNMEASURED -- RESOLVED (measured)

**Source phase**: Implementation entry (recorded at Phase 1). **Resolved at**: Phase 6, 2026-09-16.

The entry gate held implementation until a native execution path supplied five controls at once. Read-only inspection at Phase 1 found two of the five absent and recorded the deferral. That inspection had examined two repository scripts and neither the `claude` CLI's structured output nor its budget flag.

**How it was resolved**: `scripts/run_trigger_pilot.py` wraps the CLI's `stream-json` output and supplies all five controls (two model tiers via `--model`; observed selection from the `init` event and the tool-call stream; bounded subprocess time; an aggregate spend ceiling summed from `result.total_cost_usd` across calls; isolation via `--setting-sources`, `--add-dir`, `--strict-mcp-config`). The residual constraint was **cost**, not capability: the frozen 96-call matrix costs roughly USD 33 against an original USD 10 ceiling. That ceiling was raised to USD 35 with explicit maintainer authorization and recorded as amendment 1 to the frozen protocol. The scored run completed at **USD 20.6709**.

**Outcome**: the pilot ran to completion and no candidate qualified. Disposition `MEASURED_NO_CHANGE`; nothing was promoted. See `development/trigger-pilot-results.md`.

#### QG-1: Phase 6 acceptance criteria unexercised -- RESOLVED (evaluated)

**Source phase**: Implementation entry (recorded at Phase 1). **Resolved at**: Phase 6, 2026-09-16.

All four frozen criteria were evaluated per model against the measured data. Criteria 1 and 3 failed on both models; criteria 2 and 4 passed. Variant B is not promoted for either model.

Criterion 3's failure is carried forward as **WN-4**, because it was unreachable by construction rather than by any property of the candidate.

#### WN-1: Pre-existing commit-attribution findings -- RESOLVED

**Source phase**: Phase 1. **Resolved at**: Phase 6, 2026-09-16.

Phase 1 recorded `check_commit_attribution` failing with 3186 findings across 3377 scanned commits, all predating this plan. The condition has since been corrected in local history.

```
$ python scripts/check_commit_attribution.py --all-refs
Attribution: 1740 commits scanned; 0 findings; 0 errors
exit 0
```

The scanned-commit count fell from 3377 to 1740 because the earlier figure included commits reachable only through stale refs and two worktrees left on detached pre-rewrite heads, not because history was truncated. `python scripts/ci/run.py --profile fast --quiet` now reports `PASS: 15 passed, 0 failed`.

#### BG-1 to BG-6: Defects found by the Phase 7 adversarial pass -- RESOLVED

**Source phase**: Phase 7 (T030). **Resolved at**: Phase 7, 2026-09-16. Each was confirmed by reproduction before being fixed, and each fix carries a regression test.

| ID | Defect | Fix |
|---|---|---|
| BG-1 | `trace-example.py` ancestry guard missed a Windows junction (`is_symlink()` is False for a reparse point) and only ever inspected the immediate parent | Redirection is now detected via the reparse-point attribute and DISCLOSED in the output. A blanket refusal was tried and rejected: `/tmp` and `$TMPDIR` are symlinks on macOS, so it would have broken the script's own documented use. |
| BG-2 | `trace-example.py` wrote with `"w"`, leaving a window between the existence check and the write | Writes with `"x"` (O_EXCL). Measured consequence, not assumed: an exclusive create through a junction fails on Windows even when nothing is there, so that case is reported as a clean refusal rather than a traceback. |
| BG-3 | `run_trigger_pilot.py` scored a selection by substring over the serialized tool input | Matches the field that names the skill. See WN-5 for the effect on the already-recorded run. |
| BG-4 | An errored or budget-truncated result was recorded as a measured non-selection | Only a cleanly terminated result licenses `False`; otherwise the row stays evidence-missing. |
| BG-5 | `--ceiling` was unclamped, and a non-finite value disabled the spend check entirely, because every comparison against `nan` is False | Clamped to the frozen `MAX_SPEND_USD` and non-finite values refused at argument time. A timed-out call is now charged its observed cost, or the per-call budget when unknown, never zero. |
| BG-6 | `stage_variant` could silently substitute nothing, producing two identical arms and a confident null result; and its `rmtree` would delete a real project's `.claude/skills` if `--fixture` pointed at one | The substitution count is asserted, and the directory is cleared only when it carries a runner-owned marker file. |
