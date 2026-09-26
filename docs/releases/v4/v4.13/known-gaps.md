# Known gaps - v4.13

**Project**: Nexus-Hub
**Status**: released; PR #230 merged the complete 34-task plan and tag `v4.13.0` was published on 2026-09-21. Two bounded warning-class findings remain owned for future measurement work. GitHub branch protection passed a live pull-request gate test; the second trigger pilot stopped on an unproven spend bound.
**Last updated**: 2026-09-24

Release-scoped gaps for the evidence-driven agent improvement plan. Planned future-phase work is tracked in the plan rather than reported as completed here.

## v4.13.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 1 | 6 |
| Warnings (WN) | 2 | 4 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 4 |

### Open Items

#### BG-7: The second pilot's per-call budget did not bound reported cost

**Source phase**: 2026-09-23 post-release trigger follow-up. **Plan reference**: [`trigger-pilot-2/protocol.md`](../../../archives/v4/v4.13/development/trigger-pilot-2/protocol.md). **Reason**: the first two strong-tier calls reported USD 0.6540 and USD 0.6292, each above the runner's USD 0.50 per-call reservation, and both had unknown selector evidence. The process was interrupted; no complete result file exists. The aggregate check cannot guarantee the approved hard USD 35 ceiling when a call can exceed the amount reserved for it.

**Owner**: catalog maintainer. **Status**: open; the second pilot is `UNMEASURED`. **Suggested next step**: establish a provider-enforced ceiling or proven per-call upper bound, fix and test pre-call reservation and crash-safe per-call receipts, then freeze a new protocol before spending again. Preserve the [aborted attempt](../../../archives/v4/v4.13/development/trigger-pilot-2/attempt.md) and the original 96-call evidence unchanged.

**Local safety candidate, 2026-09-23**: The runner now rejects non-finite or negative reported cost, records an atomic in-flight receipt before each call and a completed receipt after it, refuses to overwrite an existing receipt, and stops before a second call when reported cost exceeds the per-call reservation. These controls preserve partial evidence and prevent further calls after an observed overrun; they do not retroactively bound the overrun or make USD 35 a hard ceiling. The pilot remains `UNMEASURED`, and no further paid call is authorized by this candidate alone.

**Provider-cap preflight, 2026-09-24**: The installed Claude Code 2.1.280 currently authenticates as `claude.ai` on a Team subscription, not as a Claude Console workspace API key. The [archived preflight](../../../archives/v4/v4.13/development/trigger-pilot-2/provider-cap-preflight-2026-09-24.md) distinguishes Team usage-credit limits from a dedicated Console workspace cap and records the account, key-binding, and limit-refusal evidence required before another paid call. BG-7 remains open and the second pilot remains `UNMEASURED`.

#### WN-2: Tool-span attributes unverified at the pinned revision - RESOLVED 2026-09-22

**Source phase**: Phase 2. **Plan reference**: T005. **Reason**: the `gen_ai.tool.*` attribute table could not be retrieved at pinned revision `5ca9052bc796ef1e497200b1d558fd87a201f335`. The containing document truncates before that section and the standalone tool-spans path returns HTTP 404 at that revision. The `execute_tool` operation name itself is confirmed.

**Resolution**: the agent-spans page links to `docs/gen-ai/gen-ai-spans.md#execute-tool-span` at the same pinned revision. That sibling table verifies `gen_ai.tool.name` as Required, call ID, description, and type as Recommended if available, and arguments and result as Opt-In. The contract now names those levels, keeps arguments, results, and descriptions absent from default traces, and has a regression assertion for the pinned sibling link and field levels. The original retrieval failure above remains historical evidence.

#### WN-3: The shipped catalog under-triggers on its own positive prompts

**Source phase**: Phase 6. **Plan reference**: T022, T023. **Reason**: the pilot's control arm is the currently shipped corpus. Across four sampled skills and eight positive prompts it selected the skill on **1/8** with the fast model and **3/8** with the strong model, while producing **zero** irrelevant selections across all 32 near-miss and trivial-edit prompts. The catalog's measured failure mode is under-triggering, not over-triggering.

**Evidence**: `development/trigger-pilot-results.md` and the raw `trigger-pilot-results.json` (96/96 calls, 0 failures, 0 evidence-missing). The regression is concentrated in `skill-description-authoring` on the strong model, 2/2 to 0/2 under the candidate wording.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: this finding is recorded, not acted on. `AGENTS.md` prescribes pushier descriptions with explicit SKIP clauses as the remedy, and the pilot measured that remedy making selection **worse** on both models, so the prescribed fix is now evidence-contradicted. Changing the authoring guidance needs its own frozen pilot with a candidate designed against this data; nothing in this release may change a description on the strength of the finding alone.

#### WN-5: The recorded pilot run cannot be re-audited for the loose selection matcher

**Source phase**: Phase 7. **Plan reference**: T030 (Tier 3 deep pass, adversarial step). **Reason**: the runner scored a selection with a substring test over the whole serialized `Skill` tool input, so a call invoking a different skill while mentioning the target would have counted. The matcher is fixed and covered by tests, but the recorded 96-call run did not retain tool-call payloads, so its five positive rows cannot be re-checked directly.

**What is known**: the `Skill` tool was invoked exactly 5 times across all 96 calls; those 5 are exactly the 5 rows scored as selected; each falls on a positive prompt for the skill under test; no row shows a `Skill` invocation without a scored selection. The defect can only inflate a positive, never hide one, so all reported counts are upper bounds and control arm A could only be equal or lower.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: retain the `Skill` tool input alongside `tools_used` in any future run so the question is answerable from the data. Do not re-run the pilot for this alone; the disposition `MEASURED_NO_CHANGE` does not turn on it, because a lower A would narrow the gap criterion 1 already failed on.

**Follow-up, 2026-09-22**: Future runner rows now retain `skill_selectors`, a bounded record of only the `command`, `skill`, and `name` selector fields from each `Skill` call. Scoring reads the same normalized values; non-skill values become `<invalid>`, and prompt or other tool arguments are never copied into results. Tests prove a different skill mentioning the target stays negative, a valid target stays positive, private non-selector text is absent, and normal and timed-out rows retain the observed selector. This mitigates future re-audit failure but cannot recover the 96 historical tool inputs, so this historical evidence gap remains open.

#### WN-6: Symlink refusal is unproven on Windows without developer mode

**Status**: RESOLVED 2026-09-22 for the declared cross-platform contract. PR #230's Ubuntu `tests` job passed, and a direct WSL2 Ubuntu standard-library probe executed the same two cases: the script returned exit 2 without overwriting a symlink target, and `describe_destination` disclosed the redirected ancestor. Windows developer mode is not required to prove the Linux/macOS path; Windows retains its native junction coverage.

**Source phase**: Phase 7. **Plan reference**: T030. **Reason**: two new tests covering the trace script's symlinked-target refusal and its redirected-ancestor disclosure `skip` on a Windows host that does not permit creating a symlink. They run on the Linux and macOS CI legs.

**Owner**: `ai-agent-development`. **Status**: resolved 2026-09-22 by the Linux proof recorded above. Windows continues to exercise its native junction path and does not need developer mode for the cross-platform contract to be complete.

### Resolved Items

#### QG-4: Integration and release branch protection - RESOLVED 2026-09-23

**Original observation, 2026-09-22**: GitHub's branch-protection API returned "Branch not protected" for both `develop` and `main`, and the repository rulesets API returned no rulesets. PR #234 had merged while its Linux and Windows jobs were still running. No earlier unprotected merge is reclassified as protected.

**Resolution**: the owner approved protection. GitHub's classic branch-protection API now reports a required pull request, strict required checks, administrator enforcement, conversation resolution, and force-push/deletion blocks on both branches. Each requires `validate`, `shellcheck`, `ci-required`, `colocation`, and `verify`, matching `docs/policy/required-checks.json`. On docs-only PR #252 at head `8f43e08d`, GitHub reported `mergeStateStatus=BLOCKED` while the checks were queued, then `CLEAN` only after all five required contexts reported `SUCCESS`. No bypass was used in this gate test. This proves the live `develop` gate; `main` has the same API configuration but no separate test PR in this follow-up.

#### WN-6: Symlink refusal on a host that permits symlinks - RESOLVED

The exact target-refusal and redirected-ancestor assertions passed on WSL2 Ubuntu against the shipped `trace-example.py`; PR #230's Ubuntu repository test job also passed. The earlier Windows skip remains honest host-specific accounting rather than missing product coverage.

#### WN-4: Acceptance criterion 3 was unreachable by construction - RESOLVED

**Source phase**: Phase 6. **Plan reference**: T021. **Original reason**: the first frozen protocol required "at least one strict reduction in irrelevant loading or unnecessary pauses". The control arm produced zero irrelevant loads, so no candidate could satisfy that criterion. The original measured failure and variant B's independent criterion-1 failure remain unchanged.

**Resolution, 2026-09-24**: The [frozen second protocol](../../../archives/v4/v4.13/development/trigger-pilot-2/protocol.md) requires a strict positive-selection gain and no increase in irrelevant selections relative to its contemporaneous control. Both conditions are attainable when the control has zero irrelevant selections, so the construction defect is repaired for that protocol. Its two-call attempt was aborted and remains `UNMEASURED`; this disposition neither qualifies a candidate nor closes BG-7's unproven USD 35 hard ceiling, WN-3's under-triggering, or WN-5's unauditable original selectors.

#### QG-2: A timed-out CI step reports nothing at all - RESOLVED

**Source phase**: Phase 7. **Plan reference**: T029, T033. **Reason**: in `scripts/ci/run.py`, the `subprocess.TimeoutExpired` handler returns at line 100, before the `[ok ] / [FAIL]` rendering block at line 122. A step killed by its timeout therefore increments the failed count while naming neither itself nor its reason. The entire output of a two-step failure is `FAIL: 0 passed, 2 failed, 0 skipped, 0 advisory in 6300.2s`.

**Cost observed**: diagnosing two unnamed failures took two full profile runs and two standalone suite runs, roughly four hours, to establish something the runner already knows. It constructs `status="timeout"` and `reason=f"exceeded {cmd.timeout}s"` and never prints either.

**Wider than first recorded**: reading the code found FOUR early-return paths that all skip the rendering block at line 122, not one. Working directory not found (line 65), executable not on PATH (line 73), timeout (line 100), and `OSError` on launch (line 109). All four satisfy `counts_as_failure`, so any of them fails the run silently. The missing-executable case is arguably worse than the timeout, because an environment problem is then indistinguishable from a test problem.

**Owner**: repository maintainer, via `[[cicd-architect]]`. **Status**: resolved 2026-09-21.

**Resolution evidence**: `scripts/ci/run.py` now renders every `CommandResult` from the single production caller, `run_group`, so missing working directories, missing executables, launch errors, ordinary failures and timeouts all name the step and reason. `tests/ci/test_ci_engine.py` covers each formerly silent early return through that caller.

**Agreed solution (maintainer, 2026-09-17)**: move rendering out of `run_command` into `run_group`, driven by the `CommandResult`, so one renderer covers every status including all four early returns; and capture `TimeoutExpired.stdout`/`.stderr` so a killed step still shows its last lines. Chosen over patching each early return individually, because that fixes four instances of a class while this removes the class. Risk is low: `run_command` has one production caller, and the nine test call sites in `tests/ci/test_ci_engine.py` assert on the returned object rather than on stdout.

**Deliberately not applied in v4.13.0**: the release is finished and validated, and touching the gate engine would require re-running a 2.4-hour gate to prove the gate still works. Scheduled as its own focused change against `develop` after v4.13.0 merges, with a regression test asserting that each of the four statuses prints its name and reason.

#### QG-3: The `tests` group has no enforceable time bound when a step spawns a process tree - RESOLVED

**Source phase**: Phase 7. **Plan reference**: T033. **Corrected 2026-09-20**: this entry originally recorded a slow host. Two different problems were being read as one, and the second is worse than the first.

**The budget overrun is real.** `hook-tests` (cap 1800s) measured 1961.5s and `repo-tests` (cap 4500s) measured 5970.3s on the development host, against the measured Windows baseline of 3341.7s for `repo-tests` that `scripts/ci/profiles.py` records; this host ran 79 percent above it while other workloads were resident. Every assertion passed: 1319 passed / 35 skipped and 5805 passed / 101 skipped / 0 failed when the two suites run directly.

**The cap cannot fire at all for a tree-spawning step.** This rests on the repro below, not on local wall-clock timings. Two `--only tests` runs overlapped on this host after the first was misread as dead, and the survivor was then terminated by hand, so every duration from that session is contaminated and none of it is offered as evidence. A cap that is never reached is not a cap being exceeded, which is why the original wording would send a reader to re-measure on a quiet machine and find nothing wrong.

**Two facts from the completed run are clean and worth keeping.** `hook-tests` passed at 1701.8s against its 1800s cap, which is 94 percent of budget with no contention yet in play, so the budget pressure in the first paragraph is real and not an artifact. And the step that followed it failed while printing NO line naming itself: the run emitted `[ok] hook-tests`, then jumped straight to a summary reading `1 passed, 1 failed`. That is QG-2 observed on the real gate rather than argued from the source, and it is why diagnosing this took a full session.

**Root cause**: `scripts/ci/run.py` bounds each step with `subprocess.run(capture_output=True, timeout=cmd.timeout)`. On timeout, `subprocess.run` kills the direct child and then calls `communicate()` a SECOND time with no timeout to reap it. Killing a child does not kill its descendants on Windows, so a grandchild holding the inherited stdout pipe keeps it open, EOF never arrives, and that second call blocks permanently. The installer tests spawn real installers; the process observed at the 340-minute mark was `test_real_workspace_installer_3`. CI survives this only because the job-level limit kills the runner instead, so the defect is invisible there.

**Evidence**: [`development/repro/ci-runner-timeout-hang.py`](development/repro/ci-runner-timeout-hang.py) reduces it to the part that matters and prints a verdict. Observed: a 5-second timeout did not return after 30 seconds. This is the load-bearing evidence precisely because it is uncontaminated, deterministic, and runs in half a minute on any host.

**Owner**: repository maintainer, via `[[cicd-architect]]`. **Status**: resolved 2026-09-21.

**Resolution evidence**: command output now goes to temporary files rather than inherited pipes, each command starts in its own process group, and timeout handling terminates the process tree before reading partial output. `test_timeout_kills_process_tree_and_preserves_partial_output` fails on the old implementation and now proves prompt return, `timeout` status, retained partial output, named rendering and no surviving child. The timeout-policy question is also settled in `scripts/ci/profiles.py`: the caps are CI safety bounds calibrated from quiet runner measurements, not local performance SLOs, and a contended workstation is not a reason to raise them.

**Suggested next step**: fix this together with QG-2 in ONE change, because both live in `run_command`'s result handling and fixing them separately touches the same function twice. Give the subprocess temp files instead of pipes: with no inherited pipe there is nothing to block on, `TimeoutExpired` returns promptly, the kill is effective, and the partial output stays readable from the file, which is exactly the output QG-2 says a killed step must print. Add a regression test asserting that a tree-spawning step is killed, reports `timeout`, and prints its partial output. Separately, and still open, decide whether the caps describe CI runners only, in which case document that a contended workstation is expected to exceed them, or whether local runs are meant to fit, in which case re-measure on a quiet machine. Do NOT raise the cap from a contended host's timing: that tunes a shared guard to the slowest observation and removes the protection the cap exists to provide. Neither problem is caused by this plan, which added roughly 180 tests running in about one second.

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

## Historical carry-forward from v4.0 through v4.12

This is the forward entry point for every known gap and unfinished task recorded before v4.13. It transfers tracking, not implementation or verification: an item open in its source ledger remains open, and a later resolution note remains part of that source record. Read each linked ledger in full before scoping a new plan; the v4.13.0 Summary above counts only findings introduced in v4.13.0 and does not claim that the older ledgers have zero open items. Each SHA-256 covers the source ledger's UTF-8 bytes with CRLF normalized to LF, so a later source edit requires a fresh transfer review rather than silently inheriting an outdated index.

| Minor | Source ledger | Normalized SHA-256 |
|---|---|---|
| v4.0 | [ledger](../v4.0/known-gaps.md) | `32215e6611307137e442645114c59fa49addb1b37b9ffda7eba53ba6d5dfcd88` |
| v4.1 | [ledger](../v4.1/known-gaps.md) | `40f451ff14a0efff8e9d339f87787298eca9d07ac2394e34facab7349c30eeab` |
| v4.2 | [ledger](../v4.2/known-gaps.md) | `fc4e4cff09baa649522c40aab2979a07e66361985a5c84e6b7a8837baeb26fbc` |
| v4.3 | [ledger](../v4.3/known-gaps.md) | `1fe77192a9dd94591eb44da263bbed22b7d25e8a58bc1f3c23898c1ae68a7bb2` |
| v4.4 | [ledger](../v4.4/known-gaps.md) | `34af58f0cb6cbbbab2d2e0767393e1ff18a18740e7cb6f0f2c569c60fd744b56` |
| v4.5 | [ledger](../v4.5/known-gaps.md) | `e793ab381025b760eaa6cf35c41e57749bb73ec6c2828b1369bcccad129ea24c` |
| v4.7 | [ledger](../v4.7/known-gaps.md) | `52c01a05534b203bf8b2901c24a6b69e6aaa85a75c78140d3371469ef26b6e1d` |
| v4.8 | [ledger](../v4.8/known-gaps.md) | `0dd85eddc8f04c1e85c2d72357674b627288fb23bdd1a3b9f4f039585c95cab2` |
| v4.9 | [ledger](../v4.9/known-gaps.md) | `fdb22a32c5a46310255fa124e2b018fef67d4c0449f540eb517e6499ea4043f3` |
| v4.10 | [ledger](../v4.10/known-gaps.md) | `f8e1d71999b90c0d06499fa6e1517169935ddd27b21d521032886e701ab84f94` |
| v4.11 | [ledger](../v4.11/known-gaps.md) | `e03f73d0327c193527a53ba50501762522b40e999d9bd483abe092ee9735df9b` |
| v4.12 | [ledger](../v4.12/known-gaps.md) | `8b10c0ed3060a293a0efae38fe403bffd5c57c43c0a06a4b253bfddd211f84e5` |

v4.6.0 was never cut. Its unimplemented plan was retargeted through v4.8.0 and completed as the [v4.9.0 adoption plan](../../../archives/v4/v4.9/plans/v4.9.0-adoption-visa-vulnerability-agentic-harness.md); the [v4.8 ledger](../v4.8/known-gaps.md) preserves the retargeting history. There is no v4.6 ledger or plan directory to archive. The v4.13.0 entries above already live in this file. The v4.13.1 through v4.13.4 plans are excluded from this historical transfer and remain active in their own worktrees.

Two older plans retain unchecked strict task lines for historical reasons. Their boxes are not silently marked complete or imported as new implementation work; the cited evidence supplies their disposition. The normalized plan hashes bind these exceptions to the exact reviewed documents.

| Historical plan | Normalized SHA-256 | Disposition | Evidence |
|---|---|---|---|
| [plan](../../../archives/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md) | `dd60b8ac2b1c8def0615e28f54420bb2480f93dbd7afeabf0081a45b89d7e8e0` | implemented-evidence; 62 retained boxes | [task reconciliation](../../../archives/v4/v4.0/development/ci-cd-task-reconciliation.md) |
| [plan](../../../archives/v4/v4.4/plans/v4.4.6-guide-learning-experience.md) | `11f2c8648c8526cceba37ed67e10cd22efc8c2b7ff3dece8890bb43a7ed1d990` | superseded-by-user; 3 retained boxes | [restoration verification](../v4.4/development/guide-learning-experience/restoration/verification.md) |

### Historical unchecked checklist inventory

Twenty-two archived plans retain 384 lines beginning `- [ ]`, including the 65 strict `T###` task lines above. The remaining lines include phase, release, and verification gates, and some may be instructional templates. Their unchecked syntax is preserved as historical evidence, not accepted as proof that the work is unfinished or complete. Before creating new scope from them, read the linked plan, its source known-gaps ledger, and later disposition evidence; record a fresh decision for any still-actionable item. This inventory is separate from the v4.13.0 Summary counts.

| Archived plan | Retained `- [ ]` lines | Strict `T###` lines |
|---|---:|---:|
| [v4.0.0 agent communication](../../../archives/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md) | 4 | 0 |
| [v4.0.0 CI/CD](../../../archives/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md) | 130 | 62 |
| [v4.0.0 docs lifespan](../../../archives/v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md) | 7 | 0 |
| [v4.1.0 Pi adoption](../../../archives/v4/v4.1/plans/v4.1.0-adoption-pi-and-grill-me.md) | 16 | 0 |
| [v4.1.1 security refinement](../../../archives/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md) | 18 | 0 |
| [v4.1.2 minimal construction](../../../archives/v4/v4.1/plans/v4.1.2-adoption-minimal-construction.md) | 10 | 0 |
| [v4.2.0 interactive guide](../../../archives/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md) | 20 | 0 |
| [v4.2.1 visual education](../../../archives/v4/v4.2/plans/v4.2.1-guide-visual-education.md) | 1 | 0 |
| [v4.2.2 cinematic guide](../../../archives/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md) | 25 | 0 |
| [v4.2.3 guide refinement](../../../archives/v4/v4.2/plans/v4.2.3-guide-refinement.md) | 27 | 0 |
| [v4.3.0 verification discipline](../../../archives/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md) | 1 | 0 |
| [v4.4.1 visual and arcade](../../../archives/v4/v4.4/plans/v4.4.1-guide-visual-and-arcade-rebuild.md) | 5 | 0 |
| [v4.4.2 production-ready guide](../../../archives/v4/v4.4/plans/v4.4.2-guide-production-ready-rebuild.md) | 4 | 0 |
| [v4.4.6 learning experience](../../../archives/v4/v4.4/plans/v4.4.6-guide-learning-experience.md) | 9 | 3 |
| [v4.7.0 model behavior](../../../archives/v4/v4.7/plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md) | 15 | 0 |
| [v4.7.0 Astra prompting](../../../archives/v4/v4.7/plans/v4.7.0-adoption-gpt-6-astra-prompting.md) | 32 | 0 |
| [v4.8.0 agentic loops](../../../archives/v4/v4.8/plans/v4.8.0-adoption-agentic-loops-and-coding-agent-practice.md) | 2 | 0 |
| [v4.9.2 slide contract](../../../archives/v4/v4.9/plans/v4.9.2-slide-build-contract-and-projection-floors.md) | 25 | 0 |
| [v4.10.0 plan queue](../../../archives/v4/v4.10/plans/v4.10.0-plan-queue-continuity.md) | 18 | 0 |
| [v4.11.0 interactive authoring](../../../archives/v4/v4.11/plans/v4.11.0-interactive-handbooks-and-presentation-default.md) | 9 | 0 |
| [v4.11.2 document and deck](../../../archives/v4/v4.11/plans/v4.11.2-adoption-document-and-deck-quality.md) | 1 | 0 |
| [v4.12.0 attribution](../../../archives/v4/v4.12/plans/v4.12.0-sole-contributor-attribution.md) | 5 | 0 |
