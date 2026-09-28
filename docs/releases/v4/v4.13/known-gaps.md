# Known gaps - v4.13

**Project**: Nexus-Hub
**Status**: released; PR #230 merged the complete 34-task plan and tag `v4.13.0` was published on 2026-09-21. Two bounded warning-class findings remain owned for future measurement work. GitHub branch protection passed a live pull-request gate test; the second trigger pilot stopped on an unproven spend bound.
**Last updated**: 2026-09-25

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

## v4.13.2

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 0 |
| Bugs / regressions (BG) | 0 | 6 |
| Warnings (WN) | 6 | 1 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### WN-1: The approved repository is not bound to the remote a push goes to

**Source phase**: Phase 8 (T017), end-to-end pilot 6. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the run record freezes the approved `owner/repo`, and every hosting call is pinned to it with `--repo`, but `git push` goes to whatever `origin` resolves to and the checker never compares the two. In pilot 6 the approval named `acme/demo` while `origin` was a local bare repository; the agent noticed and stopped, but `record block --category approval-not-covered` was refused because a push-merge approval exists, so it had to file the stop as `platform-unavailable` with the mismatch in the evidence. A less careful agent could push to an unapproved remote under a valid approval.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: record the approved remote URL alongside `owner/repo` at `record create`, have the checker report an `approval.remote` predicate from `git remote get-url --push origin`, and accept `approval-not-covered` when they differ.

#### WN-2: Codex refuses to load the grandfathered skills whose descriptions exceed 1024 characters

**Source phase**: Phase 8 (T017), Codex pilot 1. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: Codex CLI 0.136.0 logged `failed to load skill ... invalid description: exceeds maximum length of 1024 characters` for each such skill, so every grandfathered over-long description (`check_agentskills_conformance.py` lists them by name) is silently absent on Codex. The conformance guard grandfathers them as information, not as a failure; the platform enforces the limit.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: shorten each grandfathered description to 1024 characters or fewer, keeping its trigger phrases and SKIP clause, then remove the grandfather list so the guard fails on any new over-long description.

#### WN-4: A headless OpenCode run cannot create a run record, so it cannot reach `PLAN COMPLETE`

**Source phase**: Phase 8 (T017), OpenCode pilot 3. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `record create` accepts an approval only from a captured prompt or from `yes` typed on the terminal device, and fails closed otherwise. OpenCode documents no prompt-submit lever (`docs/policy/completion-levers.json`, checked 2026-09-25), and `opencode run` attaches no terminal, so a scripted headless first turn can never be recorded. The plan's condition C assumed it could. The pilot showed the consequence before the runbook rule existed: the agent restated the approvals in a table and pushed, tagged, and released without a record.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: measure OpenCode interactively (the user answers `yes` at the terminal), or capture approvals through a documented OpenCode event once one exists; never infer a prompt-submit lever from `message.*` events.

#### WN-5: An unattended Codex run needs setup that Nexus-Hub does not document

**Source phase**: Phase 8 (T017), Codex pilots B4 to B7. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: three Codex behaviors each stop a full run on a fresh install. Codex skips every hook until the user trusts it through `/hooks` ([learn.chatgpt.com/docs/hooks](https://learn.chatgpt.com/docs/hooks), fetched 2026-09-27), so approval capture and the completion gate do not run; the shipped profile is read-only, so the user must grant writes; and Codex keeps `.git` read-only inside a writable root, so the project's `.git` needs its own write entry (measured with Codex CLI 0.157.1: no commit without it).

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: document the one-time `/hooks` trust and the per-project write entries (`"<project>" = "write"`, `"<project>/.git" = "write"`) in the Codex section of the platform guide, and have the installer's Codex summary point to it.

#### WN-6: A failed extension build aborts `installer.sh`

**Source phase**: Phase 8 (T017), Codex run in WSL. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the usage-monitor build runs `npm install` inside the checkout under `set -euo pipefail`; when npm could not replace a `node_modules` tree built by Windows over `/mnt/c` (`rm: cannot remove node_modules/handlebars`), the whole install exited 1. Seen only with one checkout shared between Windows and WSL, but any build failure has the same effect.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: make each extension build fail soft with a warning, as the MCP server venv step now does (BG-4).

#### WN-7: On OpenCode a full run proceeds on in-prompt approvals without a run record

**Source phase**: Phase 8 (T017), condition C runs C4 to C6. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: with no record possible (WN-4), OpenCode 1.18.32 running Claude Sonnet 4.6 restated the approvals as a table, called them recorded, never ran `record create` or `record path`, and pushed, merged, tagged, and released. Every action matched the approval the prompt contained, and the completion gate and runner took no action without a record, but the run did not stop at the first approval point as the runbook requires. Two instruction changes (the Phase 0a rule and the point-of-use `record path` check) did not change the behavior. With the user's decision of 2026-09-27, v4.13.2 ships full-by-default on every platform with this gap recorded; OpenCode is reported as not verified.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: enforce the rule rather than state it: an OpenCode plugin on the documented `tool.execute.before` event could refuse `git push`, `gh pr merge`, and `gh release create` while an `/implement` run holds no record, once a reliable signal for such a run exists.

#### MT-1: Condition B (Codex) has one passing end-to-end run

**Source phase**: Phase 8 (T018). **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: after B7 reached `PLAN COMPLETE`, the OpenAI pilot key returned `Quota exceeded. Check your plan and billing details.` before any turn, so the planned second run did not happen; one run shows the chain works on Codex but bounds no failure rate.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: rerun condition B in WSL (`tests/e2e/implement_full/run_e2e.py --agent codex`) once the OpenAI limit allows, and record the result in the e2e evidence.

#### DF-1: Devin Desktop reads `.devin/hooks.json`, which the Windsurf integration does not model

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the Cascade hooks page (fetched 2026-09-25, [docs.devin.ai/desktop/cascade/hooks](https://docs.devin.ai/desktop/cascade/hooks)) lists `~/.codeium/windsurf/hooks.json` (user), `.devin/hooks.json` (workspace), and a system file. The `windsurf` integration writes native hooks but its read contract predates the `.devin/hooks.json` workspace path. No continuation lever exists on this surface either way (`post_cascade_response` is asynchronous), so the completion gate is unaffected; the drift matters for the guardrail hooks.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: at the next `/update release` platform pass, re-verify the Cascade workspace hook path and update `docs/policy/platform-read-contracts.json` and `scripts/lib/integrations/windsurf.py` together.

#### DF-2: Antigravity 1.0 hook support is unconfirmed while the integration declares none

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `scripts/lib/integrations/antigravity.py:75` sets `hooks_supported: False` for Antigravity 1.0. The hooks page ([antigravity.google/docs/hooks](https://antigravity.google/docs/hooks/), fetched 2026-09-25) says hooks work across "Antigravity 2.0, Antigravity CLI, and Antigravity IDE" without stating whether that IDE is the 1.0 product. The plan's premise that 1.0 supports hooks is therefore not confirmed; `completion-levers.json` records every 1.0 lever as "none documented".

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: confirm against a first-party page scoped to Antigravity 1.0, or by observing a registered hook fire in a 1.0 install; change `hooks_supported` only on that evidence.

#### DF-3: Devin CLI reads Claude Code's hook files, so Claude registrations also reach it

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the Devin CLI hooks overview ([docs.devin.ai/cli/extensibility/hooks/overview](https://docs.devin.ai/cli/extensibility/hooks/overview), fetched 2026-09-25) lists `.claude/settings(.local).json`, `~/.claude.json`, and `~/.claude/settings(.local).json` among its configuration sources. Every Claude hook Nexus-Hub registers therefore also runs under Devin CLI, which the read contract does not state. The completion gate relies on this deliberately (the `top-level-block` shape matches); other hooks may meet payload shapes they were not tested against.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: record the shared read in `docs/policy/platform-read-contracts.md` and add a Devin-CLI payload case to the hook parity tests for any hook that inspects payload fields.

#### DF-4: OpenClaw and Hermes completion plugins need a manual enable step

**Source phase**: Phase 5 (T011). **Plan reference**: [v4.13.2 plan, sub-task 5.1](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: OpenClaw loads a user plugin only when `plugins.entries.<id>.enabled` is set and its conversation hook is allowed (`hooks.allowConversationAccess`); Hermes loads one only when its name is in `plugins.enabled` in `~/.hermes/config.yaml`. The research on 2026-09-25 verified both requirements but not the exact config file locations and shapes verbatim, so the installer places the plugin files and reports NEEDS SETUP with each platform's documented enable command (`openclaw plugins enable nexus-completion-gate`, `hermes plugins enable nexus-completion-gate`) instead of editing an unverified config path. Until the user runs it, a full run on those two platforms continues only through `nexus-hub run-plan`.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: verify both config locations against first-party pages, then either write the enablement through the platform's own CLI when it is detected or seed the config key under the platform-defaults do-not-invent rule.

### Resolved Items

#### BG-1: Both installers copy `plan_status.py` over the installed `generate_report.py` - RESOLVED 2026-09-27

**Source phase**: found during Phase 2 (T005); introduced by `71eaec1f` on 2026-09-13, before this plan. **Plan reference**: [v4.13.2 plan, sub-task 2.1](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `scripts/installer.sh:2584-2585` and `scripts/installer.ps1:2742-2743` assign the report generator's source path and then immediately reassign it to `scripts/plan_status.py`, while the destination stays `generate_report.py`. Every install since v4.12 therefore writes the plan-status script under the report generator's name, so `generate_report.py` is not installed and `plan_status.py` is not installed under its own name. The installer parity test passes because it checks that each basename is mentioned in both installers, not what is copied where.

**Owner**: catalog maintainer. **Status**: resolved in Phase 8 at the user's direction (2026-09-27), after an end-to-end pilot showed the full run needs `plan_status.py` installed. Each installer now copies `generate_report.py` and `plan_status.py` in separate blocks under their own names. `test_installers_copy_every_script_to_its_own_name` asserts every user-facing script is a copy destination under its own basename in both installers; it fails on the previous installers. Existing installs are repaired by the next `nexus-hub upgrade`.

#### BG-2: A Windows install without Claude Code skipped every registry platform - RESOLVED 2026-09-27

**Source phase**: Phase 8 (T017), Codex pilot 1; pre-existing. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `installer.ps1` set the project name only in the Claude Code branch and passed `--project-name` and its value as separate arguments; Windows PowerShell 5.1 drops an empty-string native argument, so the registry runner exited 2 (`argument --project-name: expected one argument`) and the installer continued with `install reported a non-zero exit`. The Codex pilot therefore ran with no Nexus-Hub skills and read the user's real, older `~/.agents/skills`, which Codex resolves from the Windows profile rather than `HOME` or `USERPROFILE`.

**Owner**: catalog maintainer. **Status**: resolved: the name travels as one `--project-name=<value>` token, guarded by `test_installer_ps1_passes_the_project_name_as_one_token`, and an isolated `-Platforms codex` install then placed the skills (see the e2e evidence).

#### BG-3: OpenCode refused to start with the installed Nexus-Hub agents - RESOLVED 2026-09-27

**Source phase**: Phase 8 (T017), OpenCode pilot 2; pre-existing platform drift. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `scripts/lib/integrations/opencode.py` copied `catalog/agents/*.md` verbatim, relying on OpenCode ignoring the Claude-style `tools:` string (verified 2026-07-21). OpenCode 1.18.32 validates the deprecated `tools` field as an object ([opencode.ai/docs/agents](https://opencode.ai/docs/agents/), fetched 2026-09-27), and one invalid agent file fails the whole configuration, so every OpenCode user with a global install could not start OpenCode.

**Owner**: catalog maintainer. **Status**: resolved: agents are installed with the `tools` line removed through the `agents_drop_frontmatter` integration setting. `opencode debug config` then loads all 23 agents; guarded by `test_opencode_agents_drop_the_claude_tools_line_and_keep_the_body` (fails without the setting) and `test_drop_frontmatter_keys_touches_only_the_frontmatter_block`.

#### BG-4: `installer.sh` aborted on a Linux host without `python3-venv` - RESOLVED 2026-09-27

**Source phase**: Phase 8 (T017), Codex run in WSL Ubuntu 24.04; pre-existing. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `install_skill_discovery` ran `python3 -m venv` for the local MCP servers under `set -euo pipefail`; on a stock Debian/Ubuntu host the venv module is a separate package, so the installer exited 1 after the platform surfaces and before the later steps.

**Owner**: catalog maintainer. **Status**: resolved: a venv that cannot be built skips only the MCP servers, with the `apt install python3-venv` hint.

#### BG-5: A full run proceeded on approvals that were never recorded - RESOLVED 2026-09-27

**Source phase**: Phase 8 (T017), OpenCode pilot 3. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the runbook's upfront round said to record the answers with `record create` but not what to do when that fails, so the agent treated its own table of the approvals as the record and went on to push, tag, and release.

**Owner**: catalog maintainer. **Status**: resolved in `implement-phase-runbook.md` Phase 0a step 3: approvals are in force only after `RECORDED`; otherwise the run asks at the first approval point.

#### WN-3: The shipped Codex permissions profile uses `:project_roots`, which the current reference does not document - RESOLVED 2026-09-27

**Source phase**: Phase 8 (T017), Codex pilot 1. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the installed `~/.codex/config.toml` grants `":project_roots" = "read"` in `[permissions.default.filesystem]`. The Codex configuration reference (fetched 2026-09-27, [learn.chatgpt.com/docs/config-file/config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)) documents `:minimal` and `:workspace_roots` as special keys, plus absolute paths and globs. If `:project_roots` is not recognized, the read grant is inert. A default install is read-only either way, so a full `/implement` run on Codex needs the user to grant writes; the harness does so with absolute-path `"write"` entries.

**Owner**: catalog maintainer. **Status**: resolved with the user's approval (a permissions change): measured in WSL Ubuntu 24.04 with Codex CLI 0.157.1, the shipped profile left the Linux sandbox without `/bin/sh`, so every command failed; with `":minimal" = "read"` and the documented `":workspace_roots" = "read"` commands run and writes stay blocked. Recorded as BG-6.

#### BG-6: Codex could not run any command on Linux with the shipped permissions profile - RESOLVED 2026-09-27

**Source phase**: Phase 8 (T017), Codex run in WSL Ubuntu 24.04; pre-existing. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `configs/permissions/codex-permissions.toml` (merged into `~/.codex/config.toml`) selects a `default_permissions` profile whose filesystem table held only `":project_roots" = "read"`. A profile lists what the sandbox can read, and without `:minimal` it lists no system directory, so `codex sandbox -- sh` failed with `Failed to execvp sh` and every Codex command on Linux failed with it.

**Owner**: catalog maintainer. **Status**: resolved: the profile grants `":minimal" = "read"` and `":workspace_roots" = "read"`; `codex sandbox` then runs `sh` and `/usr/bin/git` and still blocks writes outside a granted path.
