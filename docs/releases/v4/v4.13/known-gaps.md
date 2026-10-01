# Known gaps - v4.13

**Project**: Nexus-Hub
**Status**: released; PR #230 merged the complete 34-task plan and tag `v4.13.0` was published on 2026-09-21. Two bounded warning-class findings remain owned for future measurement work. GitHub branch protection passed a live pull-request gate test; the second trigger pilot stopped on an unproven spend bound.
**Last updated**: 2026-10-01

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

### Actionable historical inventory

This table is the single-file working inventory of residual v4.0-v4.12 items as reviewed on 2026-09-27. A source version plus its original ID identifies each item; repeated IDs in different versions are not renumbered. "Accepted limit" means the original plan or release was closed with a narrower claim, not that the capability has been implemented. Later source-ledger closure notes prevail over earlier open snapshots. Human and external-system checks remain open until their own evidence exists. The source ledgers and hashes below remain the audit record; this table is a routing aid, not a replacement for them.

| Source item | Current disposition | Owner and next action |
|---|---|---|
| [v4.0 MT-1](../../../archives/v4/v4.0/known-gaps.md) | Open measurement limit: no runtime check proves a live reply follows the communication contract. | Agent-communication owner: retain human review or define a tested observable subset; do not claim prose compliance from static checks. |
| [v4.1.0 DF-1](../../../archives/v4/v4.1/known-gaps.md) | Open live Codex roster qualification; overlaps v4.7 DF-2 and v4.9 MT-1. | Prompting-profile owner: use the source-backed calibration workflow when the host roster is available; keep unverified models explicit. |
| [v4.1.1 DF-1](../../../archives/v4/v4.1/known-gaps.md) | Open optional host-scanner exercise, not a required CI gate. | Security-audit owner on a host with the tools: retain `security-audit` receipts with none, some, and all applicable scanners. |
| [v4.2.2/v4.2.3 DF-2](../../../archives/v4/v4.2/known-gaps.md) | Open five-person Training workshop; repeated across patches, counted once. | Guide owner and five participants: run the eight-step walkthrough and record stalls. |
| [v4.3 DF-4](../../../archives/v4/v4.3/known-gaps.md) | Accepted implementation limit: OpenClaw interception needs a typed plugin and remains not covered. | OpenClaw integration owner: implement and test the typed boundary only in a separately scoped plan. |
| [v4.3 WN-3](../../../archives/v4/v4.3/known-gaps.md) | Open optional-platform read-back; the 2026-09-27 Antigravity CLI list was empty and its interactive path stopped at sign-in and invalid existing settings, so discovery was not proved. | Platform-contract owner: coordinate an authenticated host read-back, Cursor UI check, dated workflow decision, and remaining project-local paths. |
| [v4.4 HT-1 / HT-4 / MT-446-1](../../../archives/v4/v4.4/known-gaps.md) | Open human comprehension and final visual review, one carried obligation; the rejected v4.4.6 redesign is not revived. | Guide owner and representative readers: use the retained unassisted exercise and record actual answers and corrections. |
| [v4.4 HT-2](../../../archives/v4/v4.4/known-gaps.md) | Accepted unmet real-host installer duty; later isolated installer proof does not certify the user's installation. | Installation owner: first inspect the current host and repair only if needed; obtain separate approval before a real-host reinstall. |
| [v4.4 HT-3](../../../archives/v4/v4.4/known-gaps.md) | Closed for current refs on 2026-09-27: the historical 17 candidates are absent; only protected branches and unrelated PR #222 remain on `origin`. | Repository owner: retain the dated source-ledger audit; do not delete PR #222 or other-session worktrees as part of this historical cleanup. |
| [v4.4 GA-1](../../../archives/v4/v4.4/known-gaps.md) | Open stylesheet dead-selector coverage; the rejected guide redesign did not perform a global sweep. | Guide owner: run a bounded selector-to-markup audit on the retained guide and verify any removal visually. |
| [v4.4 MT-446-2](../../../archives/v4/v4.4/known-gaps.md) | Open native zoom, visual scrolling, and OS occlusion delivery; 200% reflow evidence is narrower. | Guide owner on the target browser and OS: retain native observations and correct only reproduced failures. |
| [v4.4 CQ-1](../../../archives/v4/v4.4/known-gaps.md) | Accepted historical PR-ref alert #236; current `develop` rescan closed WN-446-2, not GitHub's retained PR ref. | Security owner: do not treat the old PR ref as a current-code defect; recheck only if its input boundary changes. |
| [v4.4 WN-3](../../../archives/v4/v4.4/known-gaps.md) | Accepted historical CodeQL false-positive dispositions; automatic `main` baseline refresh was suggested but not established here. | CI owner: decide whether a `main` push analysis is warranted in the next pipeline change; recheck the guide alert if its input boundary changes. |
| [v4.5 DF-1 / MT-1](../../../archives/v4/v4.5/known-gaps.md) | Open human judgement of Writing Discipline on two platforms; MT-1 also names separate manual checks. | Writing Discipline owner: compare live responses and record benefit versus stiffness; retain the separate installer and false-positive checks in MT-1. |
| [v4.5 DF-2 / MT-1](../../../archives/v4/v4.5/known-gaps.md) | Open agent isolation: bounded service/reachability inventories exist, but the shared checkout fails the isolation minimum and egress closure is unproven. | Agent-isolation owner: isolate sessions, enumerate shared writable services and transitive reachability, and test the controls on the real surface. |
| [v4.5 MT-1, tests 1 and 3](../../../archives/v4/v4.5/known-gaps.md) | Open manual distribution read-path and prose false-positive exercises, separate from DF-1 and DF-2. | Installation and writing owners: use throwaway installs on three non-Claude platforms and judge samples of the maintainer's own writing; retain observations. |
| [v4.7 DF-2](../../../archives/v4/v4.7/known-gaps.md) | Open Codex CLI model-picker mismatch; related to v4.1.0 DF-1 and v4.9 MT-1, not a second profile implementation task. | Prompting-profile owner: recheck the live picker and reconcile the model map with official evidence. |
| [v4.7 DF-4 / DF-5](../../../archives/v4/v4.7/known-gaps.md) | Accepted exclusions: reusable CI workflow factoring and per-skill presentation metadata have no authorized implementation in this release. | CI and catalog owners: reconsider only with an actual consumer and a separate scoped decision. |
| [v4.7 WN-2](../../../archives/v4/v4.7/known-gaps.md) | Open `main` supply-chain result: the released workflow pins patched setuptools, but two 2026-09-28 dispatches stopped on PyPI lookups for editable Nexus projects before an advisory verdict. | CI/release owner: integrate the `--skip-editable` correction, then observe a passing `main` run after its protected release; preserve every failed run. |
| [v4.8 WN-F](../../../archives/v4/v4.8/known-gaps.md) | Manual per-release obligation, not an unimplemented regex: the 24 mappings passed the 2026-09-23 source/body audit. | Framework-mapping owner: repeat the source-to-body review at release time and record drift. |
| [v4.8 WN-K](../../../archives/v4/v4.8/known-gaps.md) | Installer staging mode is now owner-only in the current tree; the old release CodeQL baseline and required-context policy are separate decisions. | Security/CI owner: verify the relevant alert on the next `main` scan and decide any CodeQL gate change explicitly. |
| [v4.9 MT-1](../../../archives/v4/v4.9/known-gaps.md) | Open live Claude prompting-roster completeness; the account-backed picker offers Opus 5.5, but exposes display names rather than a complete canonical ID roster. | Prompting-profile owner: obtain a complete live model-ID enumeration, then calibrate only available models through the deterministic writer; keep the old roster date until then. |
| [v4.9 MT-3](../../../archives/v4/v4.9/known-gaps.md) | Open real-artifact slide-check coverage: the pre-rule LVEDP deck has zero static stages and three `unchecked` checks. A [runtime render](../../../archives/v4/v4.9/development/runtime-deck-render-2026-09-27/verification.md) reached 15 real slides; its viewport-floor failures were invalidated by the [stage-height correction](../../../archives/v4/v4.9/development/runtime-deck-stage-floor-correction-2026-09-27/verification.md). The [four-viewport build-state follow-up](../../../archives/v4/v4.9/development/runtime-deck-four-viewport-build-state-2026-09-27/verification.md) sampled 292 fragment completions and found slides 2 and 6 over the eight-fragment budget. The [all-state text and SVG-box follow-up](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/verification.md) ran three times over 352 states, checking 8,527-8,584 text-node instances and 456-461 visible SVG-box instances without floor or outer-box failures, with both mutations rejected in every run. The [semantic flow-order follow-up](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/semantic-order-verification.md) checked 14 nodes and 13 connectors on three authored flow slides at four viewports, with both order and geometry mutations rejected. The [chart-layout probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/figure-layout-verification.md) found no extra SVG scale in 14 model-backed slide charts and rejected a half-scale mutation at four viewports, but the reading page has no corresponding chart instances for a source-aspect comparison. The [flow paint probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/flow-paint-verification.md) qualified 52 settled connector-body observations and 12 invisible controls. Other build semantics, the known fragment-budget failures, other internal SVG rendering, and true figure re-layout remain unqualified. | Handbook-validation owner: use a preserved `.slide-stage` deck or verify a runtime path for structure, builds, figure scaling, and rendered states with negative controls. |
| [v4.10 EV-1 / EV-2](../../../archives/v4/v4.10/known-gaps.md) | Accepted fail-closed eval limits for Gemini CLI and OpenCode: no proven all-configuration isolation. | Eval-pipeline owner: enable either provider only after documented, tested exclusion of every configuration layer. |
| [v4.11 SEC-1](../../../archives/v4/v4.11/known-gaps.md) | Closed for the eight original alerts: the 2026-09-28 `main` CodeQL run passed and GitHub marked 278-285 `fixed` without dismissal. | Security/release owner: retain the hosted closure record; triage any new alert independently. |
| [v4.11 QG-2](../../../archives/v4/v4.11/known-gaps.md) | Closed as unmet: each family passed separately, but three simultaneous bounded passes were not established. | Future qualification owner: improve per-family reliability before proposing a new joint gate; do not restamp the old six rounds. |
| [v4.12 QG-1](../../../archives/v4/v4.12/known-gaps.md) | Accepted GitHub boundary: read-only `refs/pull/*` remain outside writable-ref publication. | Repository owner: request a supported GitHub disposition only if erasing those refs becomes a requirement. |
| [v4.12 QG-2](../../../archives/v4/v4.12/known-gaps.md) | Open public Code-sidebar discrepancy; the API and Insights evidence do not prove the rendered sidebar is corrected. | Repository owner: use the prepared GitHub Support handoff or obtain a fresh rendered correction; no history rewrite is justified. |
| [v4.12 DF-1](../../../archives/v4/v4.12/known-gaps.md) | Open dated Antigravity workflow retirement check, due after 2026-11-01. | Antigravity integration owner: verify the vendor date, then retire workflow emission and rerun the platform contract if it has taken effect. |

The v4.4 `RV-1` through `RV-5` visual choices belong to the user-rejected guide composition and are superseded in that ledger; its `QG-446-1` default-host interpreter gate closed in PR #319. v4.5 `WN-2` and v4.7 `WN-1` record surfaced model-effort deviations, not present-tree defects. v4.8 `WN-K` is retained above for hosted-security disposition even though its installer mode is repaired. v4.11 `MT-9` closed for the declared-control method in PR #298 after a complete retained-pilot control census; arbitrary future controls without an inventory remain `unchecked`, not a reopened implementation gap. No source gap is marked resolved merely because it appears in this inventory. The archived unchecked plan boxes below remain evidence requiring case-by-case interpretation, not a second implementation queue.

The v4.9 MT-3 [chart-line paint follow-up](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/chart-line-paint-verification.md) checked all 31 settled SVG line paths across 14 real-deck charts at four viewports with invisible-line and null-stroke controls. It narrows internal SVG evidence but does not close MT-3 or change the other-mark, build-budget, static-stage, or figure-map limits in the inventory row.

**Archive relocation, 2026-09-28**: all 12 source ledgers matched the hashes previously recorded below at pre-move `develop` commit `42490dca`. They then moved to `docs/archives/v4/<minor>/known-gaps.md`; relative links inside and into them were repaired without changing any gap status or ID. The hashes below now bind the archived, link-repaired bytes. The pre-move hashes and files remain recoverable from `42490dca`; v4.13 gaps were not transferred or moved. **Re-binding, 2026-09-29**: the whole-minor archive of v3 and the remaining v4.0-v4.11 content rewrote links and path mentions inside ten of the bound files (nine ledgers and the v4.4.6 plan) so they resolve to `docs/archives/`; no gap status, ID, or task box changed. The affected hashes below were recomputed to bind those repaired bytes.

| Minor | Source ledger | Normalized SHA-256 |
|---|---|---|
| v4.0 | [ledger](../../../archives/v4/v4.0/known-gaps.md) | `6c5e0e0b004962e069b6e64d64a4d798040c41af6dfbf68649baa65120c5cece` |
| v4.1 | [ledger](../../../archives/v4/v4.1/known-gaps.md) | `88d897f04f39fccd2d9f8510eb2e2087eef002c6e0105567471b6ad8220ae92f` |
| v4.2 | [ledger](../../../archives/v4/v4.2/known-gaps.md) | `a4d0a59eda36b082658eba9e487fad2e814e67abfc03ba5cf8e97e5dd895be5c` |
| v4.3 | [ledger](../../../archives/v4/v4.3/known-gaps.md) | `5b1938c1fc8c82d8ac3ed9d336f67bb4fda837613a56862eca72f3d1049d5bfe` |
| v4.4 | [ledger](../../../archives/v4/v4.4/known-gaps.md) | `61eb0551a28455c05278b5e2ac8f9537d7d345290a7d776abd92cff788f9ebee` |
| v4.5 | [ledger](../../../archives/v4/v4.5/known-gaps.md) | `e710101fc0703f881213a3878db25bb90fee00d3ecd42cbb1f3d87baba8e0821` |
| v4.7 | [ledger](../../../archives/v4/v4.7/known-gaps.md) | `c2784033a6af2f4732dba11faade29f7d15ca2d169f6a680f4ed6919438cb1e9` |
| v4.8 | [ledger](../../../archives/v4/v4.8/known-gaps.md) | `2cfc2e926c7c047e196912380f5b3f2a84fba1a1a81d2deda435312b12344145` |
| v4.9 | [ledger](../../../archives/v4/v4.9/known-gaps.md) | `d8ad404447d2781b2ee004a965a9a64abde6ce73463ec5fda12bb60934f04e73` |
| v4.10 | [ledger](../../../archives/v4/v4.10/known-gaps.md) | `2f401dcaddcee1152ac8496b0b43f181d2d8ef5503be3b3db03bf34bd03cd8f6` |
| v4.11 | [ledger](../../../archives/v4/v4.11/known-gaps.md) | `4477c11bbfafe6417c219c2a6da5571b6745c06077b9b6e7f9d0bc419bd8b54c` |
| v4.12 | [ledger](../../../archives/v4/v4.12/known-gaps.md) | `b33b58bf6c5083728bd52b0be944f9afef927a0076b2f03d43ebb9a5bf5264c2` |

v4.6.0 was never cut. Its unimplemented plan was retargeted through v4.8.0 and completed as the [v4.9.0 adoption plan](../../../archives/v4/v4.9/plans/v4.9.0-adoption-visa-vulnerability-agentic-harness.md); the [v4.8 ledger](../../../archives/v4/v4.8/known-gaps.md) preserves the retargeting history. There is no v4.6 ledger or plan directory to archive. The v4.13.0 entries above already live in this file. v4.13.1 through v4.13.3 are released and excluded from this historical transfer; v4.13.4 remains in flight in a separate worktree.

Two older plans retain unchecked strict task lines for historical reasons. Their boxes are not silently marked complete or imported as new implementation work; the cited evidence supplies their disposition. The normalized plan hashes bind these exceptions to the exact reviewed documents.

| Historical plan | Normalized SHA-256 | Disposition | Evidence |
|---|---|---|---|
| [plan](../../../archives/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md) | `dd60b8ac2b1c8def0615e28f54420bb2480f93dbd7afeabf0081a45b89d7e8e0` | implemented-evidence; 62 retained boxes | [task reconciliation](../../../archives/v4/v4.0/development/ci-cd-task-reconciliation.md) |
| [plan](../../../archives/v4/v4.4/plans/v4.4.6-guide-learning-experience.md) | `62adff744844a699ba8318412e21e176b2ec0ed9f1d8ed02b135d33dc125f997` | superseded-by-user; 3 retained boxes | [restoration verification](../../../archives/v4/v4.4/development/guide-learning-experience/restoration/verification.md) |

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

## Migrated from archived minors (v3.x, v4.0-v4.11) - 2026-09-29

On 2026-09-29 every v3 minor and the remaining active content of v4.0, v4.1, v4.3, v4.4, v4.5, v4.9, v4.10, and v4.11 moved to `docs/archives/`. Before the move, each open item in the v3.0-v3.21 ledgers was audited against the tree: items with concrete evidence were marked resolved in their source file, items made moot by a removal or a recorded decision were closed there with the reason, and the items below are the ones still genuinely open. Duplicates recorded by several minors are merged into one entry. Each source ledger now states `**Open items**: 0` and ends with an `Archive reconciliation - 2026-09-29` table naming every disposition. The v4.0-v4.11 ledgers were already archived and routed by the historical inventory above; their open items stay there and are not repeated here. v3.5 had no known-gaps register; its only plan has no unchecked boxes and tag `v3.5.0` exists.

**Migrated items**: 58 open (2 resolved: AR-01 and AR-02 in v4.13.6 Phase 8): 57 from 137 source rows, plus AR-58 raised by the archive pass itself, plus AR-59 and AR-60 recovered on 2026-09-30 from an unmerged local ledger draft. Migration transfers tracking only: each entry below stays open until its own evidence closes it.

### Security-relevant

#### AR-02: `secret-scan.sh` allows every write on a host without `jq` - RESOLVED 2026-09-30

- **Current state**: `catalog/hooks/secret-scan.sh` exits 0 when `jq` is missing, so the secret scan silently does nothing there.
- **Owner and next step**: hooks maintainer; reuse the Python fallback already used by `old-version-docs-guard.sh` (v4.0 BG-5), with a test that removes `jq` from PATH.
- **Migrated from**: v3.16.2#BG-2 on 2026-09-29 (reason: still open; verified by reading the hook on 2026-09-29).
- **Resolution** (v4.13.6 Phase 8): root cause was the `else exit 0` branch taken whenever `jq` was missing. The hook now reads the payload with jq, falls back to Python 3 (the same fallback `old-version-docs-guard.sh` uses), and fails closed (exit 2, "cannot be scanned") with neither; a malformed payload is still allowed on every path, as in the `.ps1`. The new parity suite also exposed an older defect on every host: the four private-key patterns start with `-----`, so `grep -qE "$PATTERN"` read them as options and never matched; the hook now passes `-e`. Tests: `catalog/hooks/tests/test_secret_scan.py` (each case parametrized over `sh-jq`, `sh-python` with a PATH that holds no jq, and `ps1`: `test_a_secret_is_blocked`, `test_a_secret_in_an_edit_new_string_is_blocked`, `test_clean_content_is_allowed`, `test_a_payload_without_content_is_allowed`, `test_the_report_names_the_category_not_the_secret`, plus `test_the_sh_fails_closed_with_neither_jq_nor_python`) and `test_hook_sibling_parity.py::test_secret_scan_blocks_a_real_secret`, which previously asserted the fail-open exit 0.

#### AR-03: The presentify repository walk has no secret redaction

- **Current state**: the extractor copies repository text into the generated site; the extraction runbook only warns about secrets.
- **Owner and next step**: presentify owner; route repository-walk text through `egress-redaction` rules before it reaches the output.
- **Migrated from**: v3.13#DF-3 on 2026-09-29 (reason: still open).

### Installer and CLI

#### AR-01: `nexus-hub init` is unreachable through the launcher - RESOLVED 2026-09-30

- **Current state**: `python scripts/nexus_hub_cli.py init --help` exits with "invalid choice: 'init'" (observed 2026-09-29). The installer tells users to run `nexus-hub init`, and `nexus-hub-autoseed.sh` calls it and ignores the failure. `init` exists only in `scripts/lib/integrations/runner.py` and as an installer subcommand; the monorepo `--target` support (spec-kit S8) is therefore unreachable too.
- **Owner and next step**: installer/CLI maintainer; add an `init` passthrough to `nexus_hub_cli.py` with a launcher-level test, then close S8 once `nexus-hub init --target <subdir>` works end to end.
- **Migrated from**: v3.11#DF-1 (launcher part) and v3.11#DF-v311-speckit-S8 on 2026-09-29 (reason: live defect found during the audit).
- **Resolution** (v4.13.6 Phase 8): root cause was that `scripts/nexus_hub_cli.py`, which both launchers call, never registered `init`; only `installer.sh init` / `installer.ps1 init` reached the runner. The CLI now forwards `init` and every token verbatim to `scripts/lib/integrations/runner.py init`, with the same `NEXUS_HUB_INIT=1` marker the installers set, from the first tree that holds both the runner and `catalog/` (`NEXUS_HUB_SRC`, the checkout the CLI runs from, then `~/.nexus-hub/src`); the installed `scripts/` tree has no catalog, so with no source tree it exits 2 with a remedy instead of an argparse error. No installer or hook edit was needed. Observed: `python scripts/nexus_hub_cli.py init --help` prints the runner's usage, and `init --target <dir> --dry-run` lists the Antigravity, Cursor, and Claude surfaces. Tests: `tests/installer/test_init_cli.py` (`test_init_forwards_every_token_and_the_intent_marker`, `test_init_returns_the_runner_exit_code`, `test_nexus_hub_src_takes_precedence_over_the_bootstrap_tree`, `test_a_runner_without_a_catalog_is_not_a_source_tree`, `test_init_is_no_longer_an_invalid_choice_from_the_checkout`, `test_init_is_listed_in_the_top_level_help`, `test_the_real_runner_seeds_a_monorepo_subdirectory_through_the_cli`, which also closes the spec-kit S8 `--target <subdir>` half, `test_the_posix_launcher_reaches_init`, `test_the_windows_launcher_reaches_init`).

#### AR-05: Hermes is registered but not wired into either installer

- **Current state**: registered in `scripts/lib/integrations/__init__.py`; zero references in `scripts/installer.sh` and `scripts/installer.ps1`.
- **Owner and next step**: installer maintainer; wire both installer arms and their smoke tests in one change, or record Hermes as registry-only by decision.
- **Migrated from**: v3.15.2#DF-2, v3.16.0#NI-6, and v3.17.0#DF-4 on 2026-09-29 (reason: one obligation recorded three times, still open).

#### AR-10: A PowerShell early-exit path leaks the selection staging directory

- **Current state**: documented as a residual in `scripts/installer.ps1`.
- **Owner and next step**: installer maintainer; wrap the post-`Resolve-Selection` flow in try/finally.
- **Migrated from**: v3.16.1#NI-6 on 2026-09-29 (reason: still open).

#### AR-11: Antigravity skill seeding can exceed the Windows path limit in a deep repository

- **Current state**: `scripts/lib/integrations/base.py` copies skill trees with plain `shutil.copytree`. The same limit broke a plain Python move of the v4.9 benchmark evidence during this archive pass.
- **Owner and next step**: installer maintainer; use extended-length paths on Windows or shorten the deepest bundled paths.
- **Migrated from**: v3.11#WN-2 on 2026-09-29 (reason: still open).

#### AR-20: Workspace-scope install output is not grouped like the global install

- **Current state**: `install_workspace` and `Install-Workspace` never call the undetected-platform grouping and still print the verbose Claude block.
- **Owner and next step**: installer maintainer; apply the global checklist and grouping to the workspace path in both installers.
- **Migrated from**: v3.14.5#DF-1 on 2026-09-29 (reason: still open).

#### AR-21: `nexus-hub verify` does not cover `extensions/`

- **Current state**: `scripts/generate_manifest.py` `COVERED_ROOTS` is still `catalog`, `templates`, `scripts`, `data`.
- **Owner and next step**: installer maintainer; extend the manifest to the distributed MCP-server sources or record the exclusion by decision.
- **Migrated from**: v3.10#DF-v310-ruflo-P4-extensions (also carried in v3.11) on 2026-09-29 (reason: still open).

#### AR-26: No live macOS installer smoke has been recorded

- **Current state**: every step in the v3.7 `development/mac-smoke-test.md` is still pending; CI covers the tarball bootstrap only.
- **Owner and next step**: installation owner on a macOS host; run `curl | bash` and a `--branch` install and record results. Related to v4.4 HT-2 in the inventory above.
- **Migrated from**: v3.0#DF-v30-8 and v3.7, v3.8, v3.9#WN-v37-1 on 2026-09-29 (reason: one obligation recorded four times, still open).

#### AR-30: `configs/` is not distributed to installed trees

- **Current state**: `scripts/lib/integrations/platform_defaults.py` falls back when the source file is absent; AGENTS.md calls the file repo-internal but no decision closes this item.
- **Owner and next step**: maintainer; record "maintainer surface only" by decision, or add a copy step to both installers.
- **Migrated from**: v3.16.0#NI-1 on 2026-09-29 (reason: still open).

#### AR-40: Two installer tests fail intermittently in long local runs

- **Current state**: possibly the real-home leak that v4.13.1 BG-2 fixed for `test_selection_parity.py` (commit `ad768ca9`); unproven, and `test_org_cli.py` is not covered by that fix.
- **Owner and next step**: installer/test maintainer; close after v4.13.1 BG-2 is verified in hosted CI and a full local installer run is clean.
- **Migrated from**: v3.18.2#BG-2 on 2026-09-29 (reason: still open).

### Permissions and platform contracts

#### AR-16: Permission-matcher behaviors remain unprobed

- **Current state**: output redirection under an explicit allow rule, whether Gemini splits compound commands, and a Gemini PowerShell / `cmd.exe` read-only set are all still UNVERIFIED in the v3.17 `development/permission-matcher-findings.md` and `configs/permissions/gemini-permissions.json`.
- **Owner and next step**: `platform-contract-verification` owner; run the recorded probes against current builds.
- **Migrated from**: v3.17.0#NI-1, v3.17.0#NI-2, and v3.17.0#DF-1 on 2026-09-29 (reason: still open).

#### AR-17: Permission distribution covers few platforms and scopes

- **Current state**: only Claude is wired at workspace scope; `Install-Nexus-Hub-Permissions.ps1` has no cross-platform equivalent; `configs/permissions/` covers 4 of 16 integrations.
- **Owner and next step**: installer maintainer; research Gemini and Codex project paths, decide Copilot `.vscode/settings.json`, and add a `nexus-hub` permissions command.
- **Migrated from**: v3.17.0#DF-2, v3.17.0#DF-3, and v3.17.0#DF-5 on 2026-09-29 (reason: still open).

#### AR-36: Unverified platform read-path residuals

- **Current state**: Antigravity CLI agent/workflow directories, Cursor global commands, and the Gemini Code Assist skill directory are still residuals in `docs/policy/platform-read-contracts.md`. The Antigravity part is also tracked as v4.3 WN-3 and v4.12 DF-1 above.
- **Owner and next step**: platform-contract owner; resolve at the next authenticated read-back.
- **Migrated from**: v3.11#DF-1 (D5, D7), v3.12.1#DF-v3121-agy-cli-workflows, and v3.12.1#DF-v3121-gemini-ide-skill-dir on 2026-09-29 (reason: still open).

#### AR-38: No invocation-policy lever on five platforms

- **Current state**: `docs/policy/skill-invocation-policy-levers.md` still documents none for Antigravity, OpenCode, Kimi, Hermes, and Nexus-AI.
- **Owner and next step**: platform-contract owner; re-check each release and close when a first-party vendor document names a field.
- **Migrated from**: v3.20.3#DF-1 on 2026-09-29 (reason: vendor-dependent, still open).

#### AR-45: Completion notification is undelivered or unverified on Qwen, Gemini CLI, and Kimi

- **Current state**: `docs/policy/platform-read-contracts.json` records Qwen and Gemini as expressible but undelivered and does not list Kimi's events. The shared Stop-hook registration may reach those platforms without `_notify_common` shipping there.
- **Owner and next step**: installer/platform maintainer; deliver or explicitly exclude trigger B, confirm the shared module ships, and enumerate Kimi's events.
- **Migrated from**: v3.15.10#DF-14 on 2026-09-29 (reason: still open).

#### AR-47: The legacy Cursor global commands write is unverified and redundant

- **Current state**: `scripts/lib/integrations/cursor.py` still writes both command directories and labels the global one UNVERIFIED.
- **Owner and next step**: installer maintainer; confirm at the next Cursor contract pass, then remove the redundant write with a test.
- **Migrated from**: v3.15.0#DF-1(a) and v3.15.10#DF-17 on 2026-09-29 (reason: still open).

#### AR-51: OpenCode writes a `rules` folder the read contract does not record

- **Current state**: `scripts/lib/integrations/opencode.py` sets `rules_subdir`.
- **Owner and next step**: platform-contract owner; review against the OpenCode rules documentation and keep or drop.
- **Migrated from**: v3.15.0 (OpenCode `rules_subdir` residual) on 2026-09-29 (reason: still open).

#### AR-54: The strict Claude permissions overlay has no `defaultMode` decision

- **Current state**: `configs/permissions/claude-permissions-strict.json` omits `defaultMode`, pending enum verification that was never closed.
- **Owner and next step**: permissions owner; decide, then add or document the omission with a test.
- **Migrated from**: v3.15.6#DF-3 on 2026-09-29 (reason: still open).

#### AR-56: Upstream-blocked hook surfaces

- **Current state**: the Gemini CLI extension-packaged hook path is unused, and Kimi has no project-scoped hook path.
- **Owner and next step**: platform-contract owner; re-check vendor docs at the next pass.
- **Migrated from**: v3.15.8#DF-12 and v3.15.8#DF-13 on 2026-09-29 (reason: vendor-dependent, still open).

#### AR-57: Agent and hook delivery never observed on real Codex, Gemini CLI, Qwen, and Kimi installs

- **Current state**: the v3.15.8 consolidated live pass has no recorded result.
- **Owner and next step**: maintainer on a host with those tools; one live pass recorded in the read-contract verification block.
- **Migrated from**: v3.15.8#MT-6, v3.15.8#MT-7, and v3.15.8#MT-8 on 2026-09-29 (reason: still open).

### Catalog, validators, and tests

#### AR-04: The skill-description eval harness builds CLI flags that do not exist

- **Current state**: `scripts/optimize_skill_description.py` still adds `--skill` and `--prompt` (verified 2026-09-29), so live trigger runs and technique checks cannot run through it. `scripts/run_trigger_pilot.py` has a working `stream-json` path.
- **Owner and next step**: eval-pipeline owner; port the pilot's invocation, then run the recorded live checks.
- **Migrated from**: v3.0#BG-v30-1, v3.0#DF-v30-6, and v3.0#DF-v30-7 on 2026-09-29 (reason: live defect, still open).

#### AR-06: The 250-character description cap conflicts with the trigger-rich description rule

- **Current state**: `scripts/validate_skills.py` `DESCRIPTION_MAX_CHARS = 250`; many descriptions exceed it by design, and `--allow-existing` fails. Related to v4.8 WN-1.
- **Owner and next step**: catalog maintainer; decide the cap (for example the 1024 agentskills.io limit) or the allowlist, then gate CI on it.
- **Migrated from**: v3.1#WN-v31cr-1, v3.2#WN-v32-1, and v3.14.2#WN-1 on 2026-09-29 (reason: one obligation recorded three times, still open).

#### AR-07: Many SKILL.md bodies exceed the 500-line target

- **Current state**: 68 of 338 exceed 500 lines including frontmatter on 2026-09-29 (for example observability-setup and multi-agent-coordinator).
- **Owner and next step**: catalog maintainer; move long sections into `references/` whenever a skill is next edited.
- **Migrated from**: v3.16.2#NI-2 and v3.20.1#WN-2 on 2026-09-29 (reason: still open).

#### AR-08: Missing direct tests

- **Current state**: no test covers `validate_frontmatter_strict_yaml`, `detect-platform.sh` / `enumerate-models.sh`, `benchmark --update-baseline`, the `nexus-hub map` dispatch, or the model-prompting `DEFAULT_GUARDS` suite end to end.
- **Owner and next step**: owners of each surface; add one focused test per item.
- **Migrated from**: v3.4#DF-v34-1 (residual), v3.14.3#MT-1, v3.15.1#MT-1, v3.15.1#MT-2, and v3.15.5#MT-4 on 2026-09-29 (reason: still open).

#### AR-09: Most skills lack trigger-case evals

- **Current state**: 88 of 338 skills have `evals/trigger-cases.json`. Related to v4.13.0 WN-3.
- **Owner and next step**: catalog maintainer; add cases as skills are rewritten.
- **Migrated from**: v3.15.2#MT-1 and v3.20.1#MT-1 on 2026-09-29 (reason: still open).

#### AR-12: loop-engineering lacks a re-entrancy guard and schema assertions

- **Current state**: no nested-invocation guard, no optional context-compression cross-link, and the gate-type table parity and `ship-pr-until-green` duplicate-block check are still unasserted (partial coverage in `tests/validators/test_loop_engineering_bundle.py`).
- **Owner and next step**: loop-engineering maintainer.
- **Migrated from**: v3.16#CD-1, v3.16#CD-3, and v3.16.2#MT-1 on 2026-09-29 (reason: still open).

#### AR-13: egress-redaction covers only the egress boundary

- **Current state**: local persistence and error surfaces are out of scope in the skill.
- **Owner and next step**: security skills owner; extend the scope.
- **Migrated from**: v3.16#CD-2 on 2026-09-29 (reason: still open).

#### AR-14: The spec template's A1 example phrases a Non-Goal as an Assumption

- **Current state**: `catalog/templates/spec-template.md` A1 is unchanged.
- **Owner and next step**: next spec-template edit; rewrite A1 and move the scope clause to Non-Goals.
- **Migrated from**: v3.16#TR-1 (originally v3.15.14#NI-2) on 2026-09-29 (reason: still open).

#### AR-15: v3.11 spec-kit items S5, S6, and S8 carry no status claim

- **Current state**: no later record states their status; S8's functional half is AR-01.
- **Owner and next step**: next spec-kit delta pass; re-verify and record.
- **Migrated from**: v3.16#TR-2 on 2026-09-29 (reason: still open).

#### AR-22: `make build-catalog` would overwrite hand-curated registry files

- **Current state**: `build_skills_catalog.py` is unchanged since v2.0.0 and the target still exists, while hand-editing checked by `check_registry_entries.py --check --strict` is the convention.
- **Owner and next step**: catalog maintainer; remove or guard the target and its AGENTS.md mention.
- **Migrated from**: v3.0#WN-v30-2 on 2026-09-29 (reason: still open).

#### AR-23: The hook rewrite field `updatedInput` is undocumented

- **Current state**: no mention in `guides/`.
- **Owner and next step**: docs owner; document it in the settings reference.
- **Migrated from**: v3.2#WN-v32hr-1 on 2026-09-29 (reason: still open).

#### AR-28: Retired slash-command names remain in skill bodies

- **Current state**: 134 mentions such as `/generate-plan` and `/tasks-to-issues`.
- **Owner and next step**: catalog maintainer; one modernization sweep.
- **Migrated from**: v3.2#DF-v32cmd-1 on 2026-09-29 (reason: still open).

#### AR-33: Subprocess-driven validator tests have no coverage measurement

- **Current state**: no coverage configuration or `COVERAGE_PROCESS_START` anywhere.
- **Owner and next step**: CI/test infrastructure owner; add subprocess coverage plumbing and a threshold.
- **Migrated from**: v3.15.5#MT-2 and v3.17.6#MT-2 on 2026-09-29 (reason: still open).

#### AR-34: No repository-wide Ruff baseline

- **Current state**: `ruff check` still reports findings (for example F401 and F841 in `graph/affected.py`, and findings in `scripts/lib/integrations/`); Ruff runs only in `presentify-extractor.yml`.
- **Owner and next step**: CI owner; set a baseline, fix the small findings, and gate new ones.
- **Migrated from**: v3.15.1#WN-2, v3.15.10 (Ruff advisory), and v3.17.0#WN-2 on 2026-09-29 (reason: still open).

#### AR-50: The template parity guard covers only the five lockstep templates

- **Current state**: `scripts/check_base_template_parity.py` guards the lockstep five; companion validators cover only named blocks on the other templates.
- **Owner and next step**: template maintainer; extend the guard or record the scope by decision.
- **Migrated from**: v3.15.10 (parity-guard advisory) on 2026-09-29 (reason: still open).

#### AR-53: No reusable self-check eval-loop authoring convention

- **Current state**: only the Markdown style self-check exists.
- **Owner and next step**: catalog maintainer; write the convention and an optional reference template.
- **Migrated from**: v3.15.3#DF-1 on 2026-09-29 (reason: still open).

#### AR-55: `ai-agent-governance` has no reciprocal SKIP clause

- **Current state**: its description still lacks one.
- **Owner and next step**: catalog maintainer; add a SKIP pointing to `agentic-endpoint-hardening` and sync `data/skills.json`.
- **Migrated from**: v3.15.6#DF-1 on 2026-09-29 (reason: still open).

### Presentify

#### AR-18: Presentify builder and extractor limits

- **Current state**: approximate PDF text/figure interleaving, duplicated caption text, geometry-only OCR tables, best-effort `.gitignore` matching, a minimal Markdown parser, no video/audio embedding, no brand web-font embedding, no Coverr/Mixkit fetch, no image gallery grouping, null PDF raster `page_fraction` on bbox mismatch, and overlay-annotation over-capture. Most are recorded as limits in `extraction-runbook.md`.
- **Owner and next step**: presentify owner; accept each explicitly by decision or schedule the ones with user value (font embedding, gallery grouping).
- **Migrated from**: v3.9#DF-v39-presentify-4, v3.9#DF-v39-presentify-5, v3.12#DF-1 to DF-5, v3.13#DF-1, DF-2, DF-4, DF-5, DF-6, and v3.15.4#DF-1, DF-2, DF-3 on 2026-09-29 (reason: still open; duplicates merged).

#### AR-19: Presentify verification residuals

- **Current state**: no rendered QA of the v3.13 samples is recorded; no live or scheduled media-fetch smoke; a sample-deck scorer smoke in the render job is unconfirmed; the scorer cannot see runtime-injected palettes; Gates A, B, and E and the composition probes have no checker or helper.
- **Owner and next step**: presentify owner; add the smoke to the render job and accept or build each checker.
- **Migrated from**: v3.13#WN-1, v3.13#MT-2, v3.15.4#MT-3, v3.16.5#WN-2, v3.16.7#NI-2, and v3.16.7#NI-3 on 2026-09-29 (reason: still open).

### Extensions

#### AR-24: nexus-context-compressor deferred refinements

- **Current state**: near-duplicate detection, auto-sized keep budget, explicit error preservation, automatic store cleanup (`prune` has no caller), JSON arrays in prose, fallback parser limits, optional spaCy pass, CacheAligner and the ML token-dropper outside the runtime path, sub-word dropping, no live semantic benchmark, no token-reduction floor, no `[ml]` CI lane, and a short reformatter handler list. The `smart_crusher.py` docstring still marks them deferred.
- **Owner and next step**: compressor maintainer; take each only when a real fixture or benchmark shows the need.
- **Migrated from**: v3.2#DF-v32hr-1 to DF-v32hr-6, DF-v32hr-8, DF-v32hr-9, DF-v32hr-12 to DF-v32hr-15, MT-v32hr-1, and v3.19.2#DF-3 on 2026-09-29 (reason: still open).

#### AR-25: Skill-scanner coverage limits

- **Current state**: a thin pattern set per class, module-level taint tracking, and 12 starter `.yar` rules with 5 offline OSV advisories.
- **Owner and next step**: scanner owner; expand or accept as a documented limit.
- **Migrated from**: v3.0#DF-v30-1, DF-v30-2, and DF-v30-3 on 2026-09-29 (reason: still open).

#### AR-27: Code-search covers 12 languages

- **Current state**: `extensions/nexus-code-search` still has 12 extractors.
- **Owner and next step**: code-search owner; add languages on demand.
- **Migrated from**: v3.0#DF-v30-5 on 2026-09-29 (reason: still open).

#### AR-32: Usage-monitor extension test coverage

- **Current state**: Claude `recommendations.ts`, `warningView`, and `extension.ts` lack tests; `claude-usage-monitor` has no coverage threshold while the Codex and Cursor monitors do; no live render check of the theme icon; the Codex `icon.png` is still the reconstructed 512x512 asset.
- **Owner and next step**: extensions owner; add the tests and threshold, reuse the installed-VSIX method that closed v4.10 MT-2, and swap or accept the icon.
- **Migrated from**: v3.14.0#MT-1, v3.14.4#MT-1, v3.14.4#DF-1, v3.14.5#MT-1, and v3.17.0#MT-1 on 2026-09-29 (reason: still open).

#### AR-44: The Cursor usage-monitor live visual smoke was never run

- **Current state**: `cursor-usage-live-smoke.md` has no recorded result.
- **Owner and next step**: maintainer on a live Cursor host; run status bar, three bars, and three themes and record the result.
- **Migrated from**: v3.15.9#QG-5 and v3.15.12#QG-4 (Cursor half) on 2026-09-29 (reason: still open).

#### AR-49: `@vscode/vsce` transitive deprecation warnings

- **Current state**: still present in all three extension lockfiles; `npm audit` is clean.
- **Owner and next step**: extensions owner; re-check at the next toolchain bump or accept as upstream-bounded.
- **Migrated from**: v3.15.9#WN-4 on 2026-09-29 (reason: upstream, still open).

#### AR-52: contextmap detectors deferred

- **Current state**: TypeORM, Drizzle, ActiveRecord, GORM, Vue, and Svelte are still listed as deferred.
- **Owner and next step**: code-search owner; one detector plus fixture per target, on demand.
- **Migrated from**: v3.15.1#DF-3 on 2026-09-29 (reason: still open).

#### AR-58: The installers still cite the pre-archive path of the install-selection contract

- **Current state**: comments in `scripts/installer.sh` and `scripts/installer.ps1` (three lines) still name `docs/releases/v3/v3.16/development/install-selection-contract.md`, which now lives at `docs/archives/v3/v3.16/development/install-selection-contract.md`. They were deliberately not repointed: the `distribution` handbook binds the installers' bytes in `docs/handbooks/_sources/distribution/evidence.json`, so any edit makes `check_handbooks.py` report stale evidence until a content, build, and rendered review is re-run.
- **Owner and next step**: handbook owner; repoint the three comments at the next distribution-handbook refresh and record new evidence.
- **Migrated from**: raised by the 2026-09-29 archive pass (reason: repointing requires a handbook evidence refresh outside this change).

#### AR-59: Extension devDependencies are declared as caret ranges

- **Current state**: the three usage-monitor extensions (`claude-usage-monitor`, `codex-usage-monitor`, `cursor-usage-monitor`) declare 11, 11, and 7 devDependencies as caret ranges (re-counted on `develop` on 2026-09-30). The immediate risk is bounded: all three have a `package-lock.json`, CI installs with `npm ci`, which resolves from the lock and not from the ranges, and each `.npmrc` sets `save-exact=true` and `min-release-age=2`, so new dependencies are recorded exactly and the range surface does not grow. Pinning the existing ranges was deliberately not done when the supply-chain hardening landed, because it changes what a fresh resolve installs, and an unverified pin breaks builds for reasons unrelated to the change that caused it.
- **Owner and next step**: extensions owner; pin each manifest to the version its lockfile already resolves, one extension at a time, running that extension's build and Vitest suite before moving to the next.
- **Migrated from**: recovered on 2026-09-30 from an unmerged local draft of the v4.1.0 Pi-adoption ledger (source: comparison item A3, supply-chain install hardening). The archived v4.1 ledger does not carry it (reason: still open; the manifest, lockfile, and `.npmrc` facts were re-verified on `develop` on 2026-09-30).

#### AR-60: Extension build workflows install with lifecycle scripts enabled

- **Current state**: `.github/workflows/claude-usage-monitor.yml` (line 46), `codex-usage-monitor.yml` (line 46), and `cursor-usage-monitor.yml` (line 52) run plain `npm ci`, not `npm ci --ignore-scripts` (line numbers as of 2026-09-30). The flag was held back for a specific reason: `ttf2woff2` is a native module that commonly relies on an install-time build step, so disabling lifecycle scripts could break icon generation in a way that only surfaces in CI. It is declared in all three manifests (the original draft said two of three; re-counted 2026-09-30). `.github/workflows/npm-audit.yml` does use `--ignore-scripts`, safely, because it installs only to read the dependency tree and never builds.
- **Owner and next step**: extensions owner; run each extension's full build locally with `npm ci --ignore-scripts` and confirm the VSIX is byte-comparable. Where a native module genuinely needs its install step, add an explicit lifecycle-script allowlist rather than dropping the flag for the whole tree.
- **Migrated from**: recovered on 2026-09-30 from the same unmerged draft as AR-59 (source: comparison item A3) (reason: still open; the workflow lines and manifest facts were re-verified on `develop` on 2026-09-30).

### Hooks and notifications

#### AR-46: The Windows notification linger was never measured

- **Current state**: the default is still 5500 ms in `catalog/hooks/_notify_common.sh` and its `.ps1` sibling.
- **Owner and next step**: maintainer on a live Windows 10/11 desktop; measure the shortest safe `NEXUS_NOTIFY_LINGER_MS`.
- **Migrated from**: v3.15.10#DF-16 on 2026-09-29 (reason: still open).

#### AR-48: `session-summary.sh` labels projects by the working directory

- **Current state**: still `basename "$(pwd)"`.
- **Owner and next step**: hooks maintainer; derive the name from the git top-level, as the notify hooks do, in both siblings.
- **Migrated from**: v3.15.10 (session-summary advisory) on 2026-09-29 (reason: still open).

### Documentation

#### AR-29: `README_zh.md` needs a full re-translation

- **Current state**: 271 lines against the English README's 792.
- **Owner and next step**: docs owner.
- **Migrated from**: v3.8#WN-v38-1 on 2026-09-29 (reason: still open).

#### AR-31: `docs/specs/README.md` still describes "legacy installer copy blocks"

- **Current state**: the stale framing moved there from AGENTS.md.
- **Owner and next step**: docs owner; say that Claude has the one custom installer block and every other platform goes through the integration registry.
- **Migrated from**: v3.14.5#DF-3 on 2026-09-29 (reason: still open).

#### AR-35: Optional provider failover and settlement reference for `multi-provider-ai`

- **Current state**: never written.
- **Owner and next step**: catalog maintainer; write it or close as won't-do.
- **Migrated from**: v3.14.0#DF-3 on 2026-09-29 (reason: optional, still open).

#### AR-39: The official Claude plugin directory submission was never made

- **Current state**: README still says "If Anthropic later lists..."; the submission draft is `docs/archives/v3/v3.20/development/claude-marketplace-submission.md`.
- **Owner and next step**: maintainer (manual form); submit, then add the install line to the README.
- **Migrated from**: v3.20.3#DF-2 on 2026-09-29 (reason: still open).

### Maintainer decisions pending

#### AR-37: Conditional adoption candidates awaiting build-or-decline

- **Current state**: visual-brainstorming server, portable YAML orchestration engine, after-the-fact intent recovery in `session-query`, the quality-gate naming note, remaining worker-check hooks, and a durable prior-cycle review-signal store. None was built; none has a decline record.
- **Owner and next step**: maintainer; record a decline (for example a reverse-engineering-matrix row) or scope a plan.
- **Migrated from**: v3.0#DF-v30-9, v3.6 to v3.9#DF-v36-2, v3.9#DF-v39-nomistakes-1, v3.10#DF-v310-ruflo-A6, v3.10#DF-v310-ruflo-A10-rest, and v3.15.7#DF-6 on 2026-09-29 (reason: conditional, still open).

#### AR-41: Product atlas

- **Current state**: `docs/handbooks/overview.html` (commit `0b164f06`) may satisfy it, but `docs/README.md` still says no atlas exists.
- **Owner and next step**: maintainer; confirm the overview handbook counts, then close and correct `docs/README.md`.
- **Migrated from**: v3.21.0#DF-1 on 2026-09-29 (reason: decision pending).

#### AR-42: The docs-convention checker scans only the active minor

- **Current state**: `scripts/check_docs_conventions.py` still scans only the active minor, and its docstring is stale.
- **Owner and next step**: maintainer; record the grandfathering decision, then close and fix the docstring.
- **Migrated from**: v3.19.2#DF-2 on 2026-09-29 (reason: decision pending).

#### AR-43: Signed execution contracts remain a design study

- **Current state**: no decision record exists.
- **Owner and next step**: maintainer; promote the study's deferral recommendation to a decision record, then close.
- **Migrated from**: v3.19.2#DF-4 on 2026-09-29 (reason: decision pending).

## v4.13.1

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 1 | 1 |
| Warnings (WN) | 7 | 1 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### BG-2: A test in the full profile writes into the real user's `~/.nexus-hub`

**Source phase**: Phase 9 (full local profile, 2026-09-26). **Plan reference**: T028. **Reason**: during `python scripts/ci/run.py --profile full` (17:46 to 19:53 local time), the real `~/.nexus-hub/scripts/nexus_git_attribution.py` was overwritten at 18:22 with this branch's version, and `~/.nexus-hub/VERSION` and `~/.nexus-hub/permissions-manifest.json` were rewritten at 18:36. Some test ran the real installer against the machine's own home folder instead of a throwaway one (a PowerShell run resolves the home from `USERPROFILE`, so redirecting `HOME` alone does not isolate it). The overwrite made `nexus-hub attribution check` fail with "Attribution guard version differs"; the file was restored from the durable guard (`~/.nexus-hub/git-hooks/guard.py`, which matches `develop`), a backup of the overwritten copy was kept outside the repository, and the check passes again. `VERSION` kept its value (4.13.0). This is most likely pre-existing: earlier runs from `develop` would have copied an identical file and gone unnoticed; it surfaced because this branch changed the script. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: in a disposable Windows account or container, snapshot the home folder, run the full profile group by group, and diff after each to find the test; then isolate it with both `HOME` and `USERPROFILE` (and `APPDATA`, `LOCALAPPDATA`), and add a guard that fails the profile when the real home changes. **Full inventory (2026-09-26)**: a scan of `~/.nexus-hub`, `~/.claude`, `~/.codex`, `~/.gemini`, `~/.cursor`, and the VS Code user settings for files modified during the run found only the three files above plus, in `~/.nexus-hub/state/`, lock files and backups of test fixtures (instruction files headed `# org-test` and `# org-lifecycle`), written by the organization-layer tests. The user's real instruction files (`~/.claude/CLAUDE.md` last changed 2026-09-23, the Codex, Gemini, OpenCode, and Qwen files 2026-09-15) and platform settings were not touched. The leftover fixture backups and locks contain no user data and are safe to delete. So at least two tests leak into the real home: one runs the real installer (the attribution script, `VERSION`, and the permissions manifest), and the organization tests write their backups and locks to the real state folder.

**Local repair (2026-09-27)**: the Bash and PowerShell selection-parity installer tests now provide a disposable `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `NEXUS_HUB_HOME`, and Git global-config path; both real installer tests passed, and the PowerShell test confirmed the attribution script landed under the disposable Nexus home. The instruction merger's state root now honors `NEXUS_HUB_HOME` for workspace installs while retaining explicit global-target precedence; a red-then-green root test and 42 organization/merger tests passed. The local full profile was not rerun against the real account. **Status**: open until protected hosted integration verifies this repair; audit any remaining full-profile home writers separately.

#### WN-7: A generated-with footer followed by a long clause passes the attribution hook

**Source phase**: Phase 9 (adversarial pass). **Plan reference**: T014. **Reason**: to let descriptive sentences pass, a footer counts only when it ends at the agent's name, a link, or a clause of at most four words after `-`, `:`, `,`, or `|`. "Generated with Claude Code, then reviewed and edited by hand before merge" therefore passes on `gh` routes; the Git commit-msg hook still blocks it on commits. **Owner**: catalog maintainer. **Status**: open, accepted trade-off. **Suggested next step**: collect real footers from harness defaults and tune the clause limit against them.

#### WN-1: A user edit made between sessions is preserved but not reported

**Source phase**: Phase 8. **Plan reference**: T019, [`v4.13.1-incident-replay.md`](development/v4.13.1-incident-replay.md). **Reason**: in scenario B the revision request arrives in a new session. All six Claude runs edited the deck in place (so the edit survived) but none named the edit: the new session does not treat the deck as a file it wrote, and its in-place save runs as inline `python -c`, which `user-edit-guard` does not read (it reads script files). **Owner**: catalog maintainer. **Status**: open. **Update (Phase 9 deep pass)**: the hook now also reads inline `python -c`, `node -e`, and `pwsh -Command` code for document paths (`test_deep_pass_writer_routes_are_blocked`), which removes the cause observed in the replay; this is covered by tests but not re-measured. **Suggested next step**: measure scenario B again (with WN-2 and WN-5).

#### WN-2: A moved picture was never named in the agent's report

**Source phase**: Phase 8. **Plan reference**: T019. **Reason**: in scenario C, eight of eight runs named the user's new speaker note but none the moved picture; the helper listed the picture move only as a changed part name. The diff now prints "non-text change on slide N ...: tell the user about it", covered by tests but not re-measured by a paid run. **Owner**: catalog maintainer. **Status**: open until measured. **Suggested next step**: re-run scenario C (three Claude trials per condition) with the current helper.

#### WN-3: Codex replay runs can see the machine's real user skills

**Source phase**: Phase 8. **Plan reference**: T018. **Reason**: Codex resolves the home folder through the Windows known-folder API, not `HOME`, so replay runs also load `~/.agents/skills` from the real profile. One Codex run did not find `edit_guard.py` and edited without the helper. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: run Codex replays under a separate Windows user or in a container, and check whether Codex prefers the workspace `.agents/skills` over the global one.

#### WN-4: Antigravity 2.0 and Windsurf do not receive the guard hooks

**Source phase**: Phase 9 (implementation convergence). **Plan reference**: Definition of Done 3 ("on hook-capable platforms"). **Reason**: both adapters register a curated hook list with their own tool names and event names (`scripts/lib/integrations/antigravity.py` `_hook_registration`, `scripts/lib/integrations/windsurf.py` `_CASCADE_HOOKS`), so neither installs `user-edit-guard` or `attribution-guard`. The new hooks read Claude-style `tool_input.file_path` and `tool_input.command`; registering them where the payload fields are unverified would install hooks that silently pass everything. The always-loaded rule and the skill still reach both platforms. **Owner**: catalog maintainer, with [[platform-contract-verification]]. **Status**: open. **Suggested next step**: verify each platform's hook payload from a fetched vendor document, map its field names in `edit_guard.py hook` and the attribution scan, then add both hooks to the curated lists with a test per platform.

#### WN-5: Scenario D (deck left open) was not re-measured on Claude after the fixes

**Source phase**: Phase 9 (implementation convergence). **Plan reference**: T019. **Reason**: the final replay round covered scenarios A, B, and C on Claude by the maintainer's reduced design; scenario D ran on Claude only in rounds 1 and 2 (before the second fix cycle) and on Codex in round 3, and every run preserved the edit. The post-fix Claude result for D is unmeasured. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: include scenario D in the WN-1 and WN-2 re-measurement.

#### WN-6: Accepted blind spots of `user-edit-guard`

**Source phase**: Phase 9 (adversarial pass). **Plan reference**: T013. **Reason**: the hook cannot see a destination computed at run time inside a script (for example `'deck' + '.pptx'`), a destination held in a shell variable (`cp x "$OUT"`), or a user edit saved within 5 seconds of the agent's own write (the settle window that absorbs parallel formatter hooks). Two more are accepted by design after the Phase 9 deep pass: without hooks, a user edit that lands inside an agent's command-line check-write-record sequence (at most 120 seconds after the check) is recorded as the agent's, because the helper cannot tell who changed the file; and inside a git work tree an unrecorded or tracked file only warns, so an agent that runs `git init` around an unrecorded file gets a warning instead of a block (blocking unrecorded files stalled build logs and ignored outputs). Deliberate timestamp forgery by an agent evading the rule is outside the threat model. The always-loaded rule and the skill's `check` are the protection there. **Owner**: catalog maintainer. **Status**: open, accepted risk. **Suggested next step**: treat a `$`-bearing destination outside a worktree as "cannot verify" once its false-block rate is measured.

#### MT-1: No paid measurement of the rule on a platform other than Claude and Codex

**Source phase**: Phase 8. **Plan reference**: T018. **Reason**: the replay measured Claude Code (with and without the hook) and Codex. Copilot, Cursor, Gemini, and the rule-only platforms receive the same always-loaded rule and skill but were not measured. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: add one rule-only platform to the next replay.

### Resolved Items

#### BG-1: A PowerShell script that only reads a user's file can re-record it as the agent's

**Source phase**: Phase 9 (adversarial pass, final re-probe after fix cycle 3). **Plan reference**: T013. **Original defect**: `edit_guard.py` treated `-Path` and `-LiteralPath` as write destinations for every cmdlet, including `Get-Content` and the source of `Copy-Item` or `Move-Item`. **Resolution**: PowerShell script literals now use the existing shell-command destination parser; the broad parameter-only write pattern was removed. Four source variants failed before the fix and pass afterward on both hook implementations; a `Set-Content` script remains a positive writer control. The focused guard suite passed 144 tests with one host skip. Variable and computed destinations remain bounded by WN-6. **Owner**: catalog maintainer. **Status**: merged through [PR #341](https://github.com/bendourthe/Nexus-Hub/pull/341); [post-merge run 36304945996](https://github.com/bendourthe/Nexus-Hub/actions/runs/36304945996) passed at `1efa46d9`.

#### WN-8: A UTF-16 body file passes without a warning

**Source phase**: Phase 9 (adversarial pass). **Plan reference**: T014. **Original defect**: a UTF-16 `--body-file` decoded as replacement-filled UTF-8 text and matched no attribution pattern without warning. **Resolution**: a body containing NUL bytes now follows the existing "cannot verify body" warning path; normal UTF-8 decoding is unchanged. The two NUL-body cases failed before the fix and passed afterward on both hook implementations. The distribution handbook's claim review and retained-output check passed without changing its HTML bytes. **Owner**: catalog maintainer. **Status**: merged through [PR #345](https://github.com/bendourthe/Nexus-Hub/pull/345); 24 PR checks passed with one expected skip, and [post-merge run 36332865916](https://github.com/bendourthe/Nexus-Hub/actions/runs/36332865916) passed at `2c37eebf`.

## v4.13.2

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 7 | 0 |
| Bugs / regressions (BG) | 0 | 10 |
| Warnings (WN) | 7 | 6 |
| Missing tests / coverage gaps (MT) | 2 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### WN-4: A headless OpenCode run cannot create a run record, so it cannot reach `PLAN COMPLETE`

**Source phase**: Phase 8 (T017), OpenCode pilot 3. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `record create` accepts an approval only from a captured prompt or from `yes` typed on the terminal device, and fails closed otherwise. OpenCode documents no prompt-submit lever (`docs/policy/completion-levers.json`, checked 2026-09-25), and `opencode run` attaches no terminal, so a scripted headless first turn can never be recorded. The plan's condition C assumed it could. The pilot showed the consequence before the runbook rule existed: the agent restated the approvals in a table and pushed, tagged, and released without a record.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: measure OpenCode interactively (the user answers `yes` at the terminal), or capture approvals through a documented OpenCode event once one exists; never infer a prompt-submit lever from `message.*` events.

#### WN-7: On OpenCode a full run proceeds on in-prompt approvals without a run record

**Source phase**: Phase 8 (T017), condition C runs C4 to C6. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: with no record possible (WN-4), OpenCode 1.18.32 running Claude Sonnet 4.6 restated the approvals as a table, called them recorded, never ran `record create` or `record path`, and pushed, merged, tagged, and released. Every action matched the approval the prompt contained, and the completion gate and runner took no action without a record, but the run did not stop at the first approval point as the runbook requires. Two instruction changes (the Phase 0a rule and the point-of-use `record path` check) did not change the behavior. With the user's decision of 2026-09-27, v4.13.2 ships full-by-default on every platform with this gap recorded; OpenCode is reported as not verified.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: enforce the rule rather than state it: an OpenCode plugin on the documented `tool.execute.before` event could refuse `git push`, `gh pr merge`, and `gh release create` while an `/implement` run holds no record, once a reliable signal for such a run exists.

#### MT-1: Condition B (Codex) has one passing end-to-end run

**Source phase**: Phase 8 (T018). **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: after B7 reached `PLAN COMPLETE`, the OpenAI pilot key returned `Quota exceeded. Check your plan and billing details.` before any turn, so the planned second run did not happen; one run shows the chain works on Codex but bounds no failure rate.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: rerun condition B in WSL (`tests/e2e/implement_full/run_e2e.py --agent codex`) once the OpenAI limit allows, and record the result in the e2e evidence.

#### WN-8: The run record's signature does not cover `pause` or `blockers`

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `approvals_hmac` now covers `start_head`, `nonce`, and `created` (fixed in this phase), but `pause` and `blockers` are rewritten by several writers (`record pause`, `record block`, the capture hook), so an edit that clears the user's pause or closes an open blocker is not reported as `record-tampered`.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: have every writer re-sign through one checker function, then add both fields to the signed payload.

#### WN-9: Approval capture binds typed text, not the approval class - PARTIALLY RESOLVED 2026-09-29

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Original defect**: `approval-capture` stores a digest of every submitted prompt line, and `record create` accepts an approval whose text matches any captured line. A short reply such as `ok`, a pasted issue body containing "I approve release", or the agent piping a fabricated payload into `completion_gate.py capture` can therefore back an approval class the user never approved. Severity high: this is the threat the contract names.

**Resolved part**: [v4.13.6 Phase 1](plans/v4.13.6-minor-scope-implement-and-verified-cleanup.md) binds every user-origin record write (`record create`, `record answer`, `record pause`, `record resume`) to the exact line the checker generated. `record render` builds the canonical page data, draws a fresh 128-bit round nonce, derives an 8-character single-use code from `HMAC-SHA256(runs secret, page and nonce)`, and writes an owner-only pending round sealed by an HMAC over every field. The write then requires the seal and the live page's code to verify, the bound session (and, for a mid-run answer, pause, or resume, the run record's session), exactly one captured whole prompt equal to the line, and an earlier prompt in that session from before the render, and consumes the round. The capture hook stores only whole-prompt digests with a capture time and skips sessions marked `NEXUS_RUNNER_LAUNCH=1`, which `run_plan.py` sets for every session it launches. The terminal fallback was removed: a missing capture file now refuses, because a process that owns the console or a pty can type into it. So a lone "ok", a quoted code, a pasted body, a replayed or superseded line, a runner-launched prompt, an edited pending round, a fresh headless session opened only to submit the line, and an answer captured in another session never record. The rule is owned by the completion contract's Approval origin section.

**Still open**: the third bypass this item names, an approval the agent itself originates. The agent can pipe a fabricated payload into `completion_gate.py capture`, append a line to the capture file, or pre-seed a nested headless session (`claude -p` with `--session-id`, then resume it with the line), and the capture is indistinguishable from the user's paste. `tests/e2e/implement_full/stub_agent.py` does exactly the first of these to stand in for the user, and the harness passes. The original suggested step "refuse a capture the agent's own tool call produced" is not done; no signal the agent cannot also set (environment, session id, process tree) was found in this pass. Two related limits: the round expires 30 minutes after render, not when the session ends, so a later session can record a line pasted in an earlier one (bound to the session where it was captured); and on a platform with no prompt-submit capture no approval can be recorded at all, so the run asks at each approval point (see WN-4 and DF-5).

**Evidence**: `tests/validators/test_approval_binding.py` (29 passed, 1 POSIX-only skip on Windows): `test_exact_line_records_once_then_reads_code_used`, `test_a_prompt_that_is_not_the_whole_line_never_records[lone-ok|quoted-code|pasted-body|line-plus-text]`, `test_a_line_replayed_from_an_earlier_consumed_round_is_refused`, `test_a_newer_render_invalidates_the_older_code`, `test_a_runner_launched_prompt_is_never_captured`, `test_record_create_refuses_inside_a_runner_launched_session`, `test_a_plan_edit_after_render_reads_page_changed`, `test_an_expired_code_is_refused`, `test_a_mid_run_answer_needs_its_own_exact_line`, `test_a_fresh_session_that_only_carries_the_line_is_refused[auto|nested-agent]`, `test_an_edited_pending_round_is_refused[paste_digests|paste_lines|expires_at|rendered_at|session]`, `test_a_mid_run_answer_captured_in_another_session_is_refused`, `test_a_session_with_no_capture_file_refuses_without_a_terminal_fallback`, `test_pending_file_is_owner_only_on_posix`; plus `test_capture_skips_a_runner_launched_session` and `test_runner_launched_capture_drains_a_large_payload` (both hook implementations) and `test_every_launched_session_is_marked_runner_launched`.

**Owner**: catalog maintainer. **Status**: open (agent-originated capture); the resolved part is local in v4.13.6 Phase 1 and not yet integrated. **Suggested next step**: find a capture signal the agent's own tool calls cannot produce (for example a host-issued per-prompt attestation, if a platform documents one); until then, keep the threat model's statement that a deliberately forged user origin is not detected.

#### WN-11: `run-plan` checks only global settings for an approval bypass

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `bypass_configured` reads the platform's global config with regular expressions. A committed project `.claude/settings.json` with `defaultMode: bypassPermissions`, a single-quoted `approval_policy = 'never'`, or the Cursor, Copilot, OpenCode, and Kimi rows (no check at all) pass unnoticed.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: parse JSON and TOML instead of matching text, include the project-scoped settings under the launch directory, and refuse a row with no check unless `unattended-with-bypass` is approved; confirm first which platforms honor project-level bypass settings.

#### WN-12: `integration.checks` and `release.version-sync` read the working tree

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the checker reads `docs/policy/required-checks.json` and runs the project's version-sync script from the working tree, so an edit to either changes what "required" means or what runs at every turn end.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: read the manifest from `origin/<target>` and run version sync from the record's `start_head` tree, or keep version sync out of the turn-end gate.

#### WN-13: Record lifetime and environment edge cases

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: three low-severity cases. A pull request opened moments ago may answer `no checks reported on the '<branch>' branch`, which is not in the not-found list and reads as `cannot-verify` (text reasoned from `gh`'s source, not reproduced). A record bound to the same session never expires, so a session resumed weeks later still carries its approvals. A home directory that is itself a git working tree, or a `GIT_DIR` in the environment, makes every record read as tampered.

**Owner**: catalog maintainer. **Status**: open, partially repaired and integrated through [PR #374](https://github.com/bendourthe/Nexus-Hub/pull/374) at `510fd987`; its required checks passed with one expected skip, and [post-merge run 36455108200](https://github.com/bendourthe/Nexus-Hub/actions/runs/36455108200) passed smoke and provenance. Same-session and unspecified-session records older than 72 hours are now ignored, and inherited Git repository selectors no longer misclassify an untracked private record inside a home Git tree; a tracked record still blocks as tampered. The 104 focused checker and runner tests passed, including negative controls for an extra `gh` error and a tracked record. The fresh-PR `no checks reported` text is handled in the checker and stub tests, but the exact stderr remains unverified: `gh pr checks 374` already showed pending jobs immediately after PR creation. **Suggested next step**: capture the live no-checks response on a future newly opened PR and compare it to the guarded pattern before closing this item; keep malformed or additional errors as `cannot-verify`.

#### DF-5: Approval capture is missing on Pi, OpenClaw, Hermes, and Windsurf

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `docs/policy/completion-levers.json` records a VERIFIED prompt-submit lever for these four platforms, but only Claude-format registrations and Cursor carry `approval-capture`, so on them `record create` cannot record an approval (the same effect as WN-4 on OpenCode). **Update (v4.13.6 Phase 1)**: the terminal fallback was removed, so on these platforms `record create` now refuses with `approval-not-captured` even in an interactive session until capture is added.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: add capture on each platform's documented prompt event in its plugin or hook adapter, with a parity test.

#### DF-6: Copilot CLI gets no goal at all

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: Copilot CLI's documented headless goal needs `--autopilot --yolo`, which the runner's denylist forbids, and the runbook prints an interactive goal line only for platforms whose goal is interactive-only, which the levers matrix does not mark Copilot CLI as.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: classify Copilot CLI's goal as interactive-only in the levers matrix and document why.

#### DF-7: Recorded design deltas from Phases 2, 4, and 6

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: accepted deviations recorded only in phase histories until now: the per-run spend cap became `--max-cycles` (Phase 6); the gate infers its output format from the payload instead of `NEXUS_GATE_FORMAT`, reuses the existing handler ownership check instead of exact-identity manifest entries, and never marks degraded enforcement in the record (Phase 4); and the Phase 2 throwaway install check could not finish on Windows and was confirmed by the Phase 3 seven-platform install instead.

**Owner**: catalog maintainer. **Status**: open (accepted). **Suggested next step**: revisit the degraded-enforcement mark and a spend cap when a platform documents per-run spend reporting; no other change is needed.

#### MT-2: No real CLI run exercised a gate refusal or a runner resume

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: every passing Phase 8 run on Claude Code and Codex reached `PLAN COMPLETE` in its first turn, so the turn-end gate's refusal and the runner's resume are proven by stub tests (`test_harness.py`, `test_completion_gate.py`) and never by a paid session.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: run one paid condition with a fixture that cannot finish in one turn (for example a phase whose test only passes after a second commit) and record the gate and runner cycles. **Update (v4.13.6 Phase 1)**: under exact binding, the paid conditions in `tests/e2e/implement_full/run_e2e.py` (`--agent claude|codex|opencode`) cannot record: their first turn states the approvals verbatim in the prompt, which never equals a line `record render` generates, so `record create` refuses (`approval-not-captured` or `session-too-new`) and the run cannot reach `PLAN COMPLETE`. Owner: v4.13.6 Phase 7. The paid first turn needs a render step whose printed line is then fed as a second scripted user turn in the same session, before any paid run is spent on this item.

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

#### WN-1: The approved repository is not bound to the remote a push goes to - RESOLVED 2026-09-28

**Source phase**: Phase 8 (T017), end-to-end pilot 6. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the run record freezes the approved `owner/repo`, and every hosting call is pinned to it with `--repo`, but `git push` goes to whatever `origin` resolves to and the checker never compares the two. In pilot 6 the approval named `acme/demo` while `origin` was a local bare repository; the agent noticed and stopped, but `record block --category approval-not-covered` was refused because a push-merge approval exists, so it had to file the stop as `platform-unavailable` with the mismatch in the evidence. A less careful agent could push to an unapproved remote under a valid approval.

**Owner**: catalog maintainer. **Status**: resolved and integrated through [PR #372](https://github.com/bendourthe/Nexus-Hub/pull/372); 24 hosted checks passed with one expected skip, and [post-merge run 36437678274](https://github.com/bendourthe/Nexus-Hub/actions/runs/36437678274) passed smoke and provenance at `1d39f75a`. `record create` now requires exactly one GitHub push URL naming the approved `owner/repo` and signs that URL; the checker reports `approval.remote` from every push URL, so a changed or additional destination blocks completion. The runbook requires the check immediately before every push, and `record block --category approval-not-covered --approval-class push-merge` accepts a remote mismatch. A planted local destination, lookalike host, wrong repository, post-approval URL change, second destination, and signed-field tampering were each exercised; 123 affected tests and the 17-check fast gate passed locally. A direct hosted push-safety replay remains unmeasured.

#### WN-2: Codex refuses to load the grandfathered skills whose descriptions exceed 1024 characters - RESOLVED LOCALLY 2026-09-28

**Source phase**: Phase 8 (T017), Codex pilot 1. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Original defect**: Codex CLI 0.136.0 logged `failed to load skill ... invalid description: exceeds maximum length of 1024 characters` for the grandfathered over-long descriptions, so those skills were absent on Codex while the conformance guard reported only information. **Resolution**: the twelve descriptions still over the cap were shortened to 250 characters or fewer with trigger phrases and SKIP clauses; the stale thirteenth allowlist name was already under the cap. The allowlist is removed, so every future over-1024 description fails the guard. The real-catalog scan passed for 338 skills with zero grandfathered entries, 11 focused conformance tests passed, strict registry mirrors passed, and the whole-catalog routing gate passed 520 cases with zero failures and zero unallowlisted collisions; the fast profile passed 17/17. [PR #371](https://github.com/bendourthe/Nexus-Hub/pull/371) merged at `3393ed19`, and [post-merge run 36427536393](https://github.com/bendourthe/Nexus-Hub/actions/runs/36427536393) passed. This verifies the file-length cause and routing fixtures, not a new live Codex skill-load session. **Owner**: catalog maintainer. **Status**: resolved and integrated.

#### WN-5: An unattended Codex run needs setup that Nexus-Hub did not document - RESOLVED 2026-09-28

**Source phase**: Phase 8 (T017), Codex pilots B4 to B7. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Original defect**: a fresh Codex install skips hooks until the user trusts them through `/hooks`, starts read-only, and keeps `.git` read-only even when the project root is writable. **Resolution**: `docs/permissions-setup.md` now states the one-time hook trust and the project and `.git` write entries, while the Codex installer summary points to those steps. Nine focused Codex integration tests and the 17-check fast profile passed. This is a setup-documentation repair; a new live Codex pilot is not claimed. **Owner**: catalog maintainer. **Status**: resolved and integrated through [PR #373](https://github.com/bendourthe/Nexus-Hub/pull/373) at `e0dcdcd3`; the required checks passed with one expected skip, and [post-merge run 36449066391](https://github.com/bendourthe/Nexus-Hub/actions/runs/36449066391) passed smoke and provenance.

#### WN-6: A failed extension build aborts `installer.sh` - RESOLVED 2026-09-28

**Source phase**: Phase 8 (T017), Codex run in WSL. **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Original defect**: under `set -euo pipefail`, an optional usage-monitor `npm install` failure aborted the whole installer; the pilot observed this when a Windows-built `node_modules` tree was shared through `/mnt/c`. **Resolution**: both optional extension builds now warn and continue on install or build failure, while successful builds still install normally. The 23 focused build tests, Bash syntax and ShellCheck checks, installer parity checks, and the 17-check fast profile passed. **Owner**: catalog maintainer. **Status**: resolved and integrated through [PR #373](https://github.com/bendourthe/Nexus-Hub/pull/373) at `e0dcdcd3`; the required checks passed with one expected skip, and [post-merge run 36449066391](https://github.com/bendourthe/Nexus-Hub/actions/runs/36449066391) passed smoke and provenance.

#### WN-10: Completion plugins start Python by bare name - RESOLVED 2026-09-28

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Original defect**: the OpenCode, OpenClaw, and Pi plugins called `spawn("python" | "python3", ...)`, and Node on Windows searched the working directory first, so a planted `python.exe` could run at every turn end. Hermes already used `sys.executable`; the checker and runner already resolved executables from PATH's absolute entries only.

**Owner**: catalog maintainer. **Resolution**: the three TypeScript plugins now pass absolute interpreter paths resolved from absolute PATH entries with `shell: false`. The planted-executable reproduction and all 25 focused plugin tests passed after the fix. [PR #368](https://github.com/bendourthe/Nexus-Hub/pull/368) passed its Linux and Windows test jobs and required checks, merged into `develop` at `ebe2f0d4`, and [post-merge run 36414815780](https://github.com/bendourthe/Nexus-Hub/actions/runs/36414815780) passed smoke and provenance. This closes implicit working-directory search; trust in explicitly configured PATH directories remains a separate environment boundary. The merged worktree and local and remote topic branches were removed.

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

#### BG-7: Tier 3 adversarial findings fixed in this phase - RESOLVED 2026-09-28

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: five defects in the checker and runner: an executable planted in the working directory resolved first on Windows (`shutil.which` searches it even with an explicit path); a titled version heading (`## v4.3.0 - ...`, used in this repository) and a title containing "Unresolved" both read open gaps as met; a quoted run reporting failures counted as passing test evidence; deleting `start_head` from the record turned every ticked task `met` unnoticed; and a runner past the lock's stale window could delete a second runner's lock.

**Owner**: catalog maintainer. **Status**: resolved in fix cycle 1 of 3: executables resolve from PATH's absolute entries only, the version heading may carry a title, only a `- RESOLVED` or `-- RESOLVED` marker resolves an item, a nonzero `failed` or `errors` count rejects the evidence, `start_head`, `nonce`, and `created` are signed, and the lock is refreshed each cycle and removed only by its owner. Six regression tests fail on the previous code and pass now.

#### BG-8: CI never collected three of this plan's test sets - RESOLVED 2026-09-28

**Source phase**: Phase 9 (T023), terminal CI/CD reconciliation. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.5](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `tests/integrations/test_completion_gate_registration.py`, `tests/integrations/test_completion_plugins.py`, and `tests/e2e/` were in no `scripts/ci/profiles.py` partition, so CI would never have run them.

**Owner**: catalog maintainer. **Status**: resolved: the two integration files join `repo-tests-integrations-install` and `tests/e2e` joins `repo-tests-governance`; `pytest tests/ci` passes (107) and the three sets pass (42).

#### BG-9: The Windows completion hooks did nothing under a UTF-8 console input encoding - RESOLVED 2026-09-28

**Source phase**: Phase 9 (T028), integration pull request #365, round 2 (`tests-windows`). **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.10](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `completion-gate.ps1` and `approval-capture.ps1` read the payload through `[Console]::In`; with a UTF-8 console input encoding a byte-order mark reached `completion_gate.py`, `json.loads` failed, the payload read as empty, and the hooks exited 0 silently. Reproduced locally by forcing `[Console]::InputEncoding` to UTF-8 with a byte-order mark: the gate printed nothing, where the plain console printed its refusal.

**Owner**: catalog maintainer. **Status**: resolved: the adapters pass raw bytes (with the guard hooks' `[Console]::In` fallback) and close the raw stream, the core strips `\ufeff`, and Python is resolved as the guard hooks do. `test_ps1_hooks_work_under_a_utf8_console_input_encoding` fails on the previous adapters and passes now.


#### BG-10: The completion checker could not resolve an SSH-alias remote - RESOLVED 2026-09-28

**Source**: the v4.13.1-v4.13.3 release on 2026-09-28. **Reason**: `check_plan_completion.py` parsed `owner/repo` with a regex that accepted only a host literally named `github.com`. This repository's origin is `git@github-bendourthe:bendourthe/Nexus-Hub.git`, so the default repository was empty and `integration.merged`, `integration.checks`, and `release.github` were `cannot-verify` on every shipped plan; a full run could not reach `PLAN COMPLETE` here. **Resolution**: [v4.13.5](plans/v4.13.5-completion-checker-remote-resolution.md) adds `scripts/repo_host.py`, which accepts a path only from `github.com` or `GH_HOST`, resolves an SSH alias through `ssh -G`, and cross-checks `gh repo view` when no run record exists. On this plan the fixed checker reports every integration, release, and cleanup predicate `met`, which closed T029.

## v4.13.3

Gaps from the truthful-session-context and measured-instruction-size plan ([`v4.13.3-adoption-agent-practice-and-harness-token-efficiency`](plans/v4.13.3-adoption-agent-practice-and-harness-token-efficiency.md)). Items DF-1 to DF-5 are the plan's own parked handoffs; the rest were found while implementing it.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 7 | 1 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 4 | 2 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### DF-1 (v4.13.3): Flip the skill-index pointer on by default, and decide todos-on-demand

**Plan reference**: Resolved decisions 1 and 4. **Reason**: the pointer ships opt-in. Flipping it needs organic-selection evidence that skills the model saw in the table are still chosen when it sees only a pointer; the todos-on-demand question needs the same instruction-size evidence. **Evidence**: [`rendered-context-baseline.md`](development/rendered-context-baseline.md) (the index is 81-84% of each rendered file; the pointer removes 99.5% of it). **Owner**: `v4.17.3-adoption-harness-economics-and-portable-engineering-system` (moved from `v4.16.0-instruction-necessity-review` on 2026-09-28: the organic-selection evidence comes from the v4.17.3 pairing evaluator, and the v4.16.0 plan never took the item on; see [`v4.17.3-comparison-harness-economics-delta.md`](../v4.17/comparisons/v4.17.3-comparison-harness-economics-delta.md) D4). **Suggested next step**: run the evaluator's required `NEXUS_HUB_SKILL_INDEX=full` against `pointer` variant pair, recording organic skill selection including guard skills, then decide the default.

#### DF-2 (v4.13.3): Pilot variant mode for instruction-file comparisons

**Plan reference**: Resolved decision 6. **Reason**: `scripts/run_trigger_pilot.py` varies only SKILL.md description lines and runs with `--setting-sources project`, so it cannot compare an instruction file with the full index against one with the pointer. Spend cap for this plan: 0. **Owner**: v4.16.0. **Suggested next step**: add a variant mode that stages instruction files per arm.

#### DF-3 (v4.13.3): Plan state in the session digest

**Plan reference**: Resolved decision 3. **Reason**: no plan-status contract exists that `/implement` writes, so a digest detector would report "none detected" almost always. **Owner**: the first plan that defines a plan-status contract. **Suggested next step**: once that contract exists, add one digest line read from it.

#### DF-4 (v4.13.3): Static-measurement ownership split for v4.17.3

**Plan reference**: Phase 6.2 handoff. **Reason**: `scripts/measure_rendered_context.py` owns rendered instruction-file measurement; v4.17.3's static measurement must reuse its estimator and detector rather than add a second definition of an estimated token or a candidate span. **Owner**: v4.17.3. **Suggested next step**: import `estimate_tokens` and `legacy_instruction_block.detect` from their current owners.

#### DF-5 (v4.13.3): Shared cleanup-aware merge requirement for v4.17.3

**Plan reference**: Phase 6.2 handoff. **Reason**: every marker-merged instruction write now goes through `instruction_merge.merge_instruction`, guarded by `test_no_integration_calls_the_primitive_directly`. Any v4.17.3 writer of a shared instruction file must route through the same owner so consent, backups, and byte preservation hold. **Owner**: v4.17.3. **Suggested next step**: cite this requirement in the v4.17.3 plan's writer tasks.

#### DF-6 (v4.13.3): Pointer consumer installed before its shared-path provider across installer runner calls

**Source phase**: Phase 5. **Reason**: the installers run the Python runner once per platform, and the runner's pointer-mode second pass only sees integrations in the same call. A consumer installed before the platform that writes its path would get the full index until the next install (fail closed, never open). **Current state (2026-09-25)**: the only such dependency among VERIFIED paths is Copilot reading Codex's `~/.agents/skills`. Both installers run Codex before Copilot at both scopes, pinned by `test_installers_run_the_shared_path_provider_before_copilot`. A simulation of the installers' exact per-platform global order on a fresh home gave the same eligible set as a single combined run (Claude, Codex, OpenCode, Copilot, Qwen). The second pass now also runs for a single integration, so an integration that renders before copying its own skills is covered. **Residual**: a future VERIFIED shared path whose provider runs later would need a new order pin. **Owner**: v4.16.0 (with DF-1). **Suggested next step**: derive the order check from the facts when a second shared-path dependency appears.

#### DF-7 (v4.13.3): Move the legacy-removal decision record to `implemented` - RESOLVED 2026-09-28

**Source phase**: Phase 4. **Reason**: `docs/decisions/implemented/tooling/2026-09-24-legacy-instruction-block-removal.md` describes shipped behavior once v4.13.3 is released. The record format requires a rewrite (Decision in present tense, Consequences) and a move, not a Status edit. **Owner**: `/update release` for v4.13.3. **Status**: resolved at the v4.13.3 release: the record moved to `docs/decisions/implemented/tooling/` with a Decision section and a Consequences section, and the capability-usage entry ships in the release notes.

#### DF-8 (v4.13.3): Per-agent `omitClaudeMd` for catalog agents

**Source**: [`v4.17.3-comparison-harness-economics-delta.md`](../v4.17/comparisons/v4.17.3-comparison-harness-economics-delta.md) D5, recorded 2026-09-28. **Reason**: Claude Code 2.1.271 added agent frontmatter `omitClaudeMd`, which lets a subagent run without user, project and local `CLAUDE.md` files (managed policy still loads). Each catalog agent now inherits the full rendered instruction files, measured at about 29k estimated tokens on the maintainer machine. **Owner**: `v4.16.2-adoption-agent-tooling-and-subagent-cost`. **Constraints**: decide agent by agent; exclude `project-standards-reviewer` and any agent that enforces repository conventions; confirm the Gemini and Codex agent loaders ignore an unknown frontmatter key, or emit the key only in the Claude copy. **Suggested next step**: accept a change only with a v4.17.3 pairing receipt showing lower cost at an unchanged pass rate.

#### WN-1 (v4.13.3): An uncooperative writer can race the final hash check

**Source phase**: Phase 4. **Reason**: cooperating installers serialize on a per-target lock, and the file is re-hashed immediately before the atomic replacement, but a program that ignores the lock can still write between that check and the rename; no portable primitive closes the window. **Mitigation**: a verified content-addressed backup of the pre-write bytes is always kept under `~/.nexus-hub/state/backups/`, and the report names it. **Owner**: installer maintainer. **Status**: accepted risk, documented in the decision record.

#### WN-2 (v4.13.3): Copilot host-scope mismatch - RESOLVED 2026-09-28 UTC

**Source phase**: Phase 5. **Original gap (2026-09-27)**: the [VS Code Agent Skills page](https://code.visualstudio.com/docs/agent-customization/agent-skills) documents `~/.claude/skills` for GitHub Copilot in VS Code, but the [Copilot CLI skill-location reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) omits that personal path. One `copilot` read-path fact governed pointer eligibility for both hosts, so it remained UNVERIFIED to prevent a CLI install from replacing its full index based only on VS Code evidence. **Owner**: Copilot integration maintainer. **Required resolution**: separate host-specific eligibility or obtain first-party CLI evidence before promoting the shared fact; preserve the full index for the unproved case.

**Local host-scope qualification, 2026-09-27**: The candidate recorded `~/.claude/skills` as VERIFIED for VS Code only and excluded host-only facts from the shared Copilot personal instruction's pointer eligibility. A redirected-home runner install with only that tree present retained the full index, while the existing common-path test still permitted a pointer. The [archived verification](../../../archives/v4/v4.13/development/copilot-host-scoped-skill-path-2026-09-27/verification.md) records the official-source boundary, red/green controls, 42 focused passes, and the contract check. WN-2 remained open pending protected integration and post-merge verification; Copilot CLI discovery of that path was not verified.

**Protected closure, 2026-09-28 UTC**: [PR #361](https://github.com/bendourthe/Nexus-Hub/pull/361) passed 24 hosted checks with one expected skip after correcting the historical v4.9 ledger hash exposed by its first full-profile run, merged as `6d9e4c39`, and [post-merge run 36361813686](https://github.com/bendourthe/Nexus-Hub/actions/runs/36361813686) passed smoke and provenance. The VS Code fact is host-scoped; shared and CLI pointer eligibility still excludes that path, so Copilot CLI discovery is not claimed. WN-2 is closed for the host-scope mismatch, not for a CLI discovery claim.

#### MT-1 (v4.13.3): The full installers were not run end to end on a disposable machine

**Source phase**: Phases 4 and 5. **Reason**: the full PowerShell installer also installs VS Code extensions through the real `code` CLI and writes the real `%APPDATA%` settings, which a redirected HOME does not isolate, so the Phase 4 and 5 verification drove the installer's own engine (per-platform runner calls plus `legacy-report`) instead. The installers' flag parsing, forwarding, and report wiring are unit-tested, and CI runs both installers on their native hosts. **Owner**: release maintainer. **Suggested next step**: the last-phase human testing suggestions include a real install on a machine that carries a legacy block.

#### WN-5 (v4.13.3): Read-path drift found by the release contract pass

**Source phase**: `/update release` platform-contract verification, 2026-09-28. **Reason**: the pass found no broken install path, but four documented changes the adapters do not yet model: Gemini CLI documents a root `GEMINI.md` for the workspace and no rules directory (the contract lists `<project>/.gemini/GEMINI.md` and `.gemini/rules/`); OpenClaw adds a named-profile workspace (`~/.openclaw-<profile>/workspace` under `OPENCLAW_PROFILE`) and a per-agent `agents.entries.*.workspace`, whose precedence against `agents.defaults.workspace` the docs do not fully state; and VS Code prompt files, Copilot's global slash surface, are deprecated for Agent Host sessions while the Local agent still loads them. Windsurf's preferred workspace hooks file is v4.13.2 DF-1. Sources are in `docs/policy/platform-read-contracts.json` `meta.verified_for_version_note`.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: change each adapter and its contract row in lockstep (Gemini CLI workspace file and rules; OpenClaw profile workspace once the precedence is confirmed), and migrate Copilot's global slash surface to skills before the Local agent is removed.

#### WN-6 (v4.13.3): Behavioral-lever drift found by the release contract pass

**Source phase**: `/update release` platform-contract verification, 2026-09-28. **Reason**: advisory lever changes (logged in `docs/policy/platform-defaults-levers.md`): Claude Code ignores a user-scope `effortLevel` on Opus 5.5 and later, so that seed no longer reaches the default model (the seeded `env.CLAUDE_CODE_EFFORT_LEVEL` still does); Codex's documented `model_reasoning_effort` and `approval_policy` value lists changed, and the page no longer names those keys as user-only; and Antigravity's `agentMode` values now describe different behavior. Every seeded value remains valid.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: seed Claude's effort under `modelSettings` for the default model, refresh the Codex and Antigravity lever rows and `configs/platform-defaults.json`, then run `python scripts/sync_platform_defaults.py --check`.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-3 | `context-manager` frontmatter advertised delegated concerns | v4.13.3 metadata follow-up | Description, summary, overview, index, registry, and OpenAI wrapper now advertise file relationships and change-impact mapping; strict registry, whole-catalog routing, and 106 validator tests pass. |
| WN-4 | Legacy-candidate diff files accumulated across file states | v4.13.3 diff-retention follow-up | A resolved-path hash scopes each diff filename. A successful report retains every current span and prunes only that file's prior states, including after consented removal; a failed write preserves prior reports. Pre-change consent-only filenames have no safe owner mapping and are left untouched. The current local profile had no historical `legacy-candidates` directory. |
| BG-8 | Historical Windows legacy backups retained inherited read access | 2026-09-28 local ACL read-back | Phase 4 post-merge follow-up to the [v4.13.3 plan](plans/v4.13.3-adoption-agent-practice-and-harness-token-efficiency.md). The 2026-09-26 audit found the directory and 21 files readable by another principal; [PR #335](https://github.com/bendourthe/Nexus-Hub/pull/335) secured new backups but did not sweep historical ones. After the user's approval for a targeted repair, a fresh read-only audit of `~/.nexus-hub/state/backups/` found the directory and all 53 current files owned by the user's account, with no allow rule except `OWNER RIGHTS` (SID `S-1-3-4`); 18 inherited rules were also owner-only. Because the full current set already meets the requested ACL boundary, no ACL was changed, no rollback export was needed, and no backup contents were read. This proves the current host state, not when or how it changed. |
| BG-9 | Legacy-candidate diffs could inherit Windows read access | v4.13.3 diff-retention follow-up | The diff directory and staged file now require owner-only permissions before atomic publication; ACL failure yields no report. Windows ACL read-back and failure-path tests pass. |

### Reconciliation across other registers (2026-09-25)

All 45 `docs/**/known-gaps.md` files were searched for open items in the areas this plan changed (session hooks, the skill index, legacy or duplicated instruction blocks, instruction-merge behavior, CRLF handling). None is closed by v4.13.3; the only instruction-merge item found, v3.15 WN-3, was already resolved in v3.15. Every other open item stays with its existing owner, unchanged by this plan.

## v4.13.4

Gaps from the Training rebuild ([`v4.13.4-guide-training-rebuild`](plans/v4.13.4-guide-training-rebuild.md)). Both open items were found by the final-phase visual sweep and reproduce unchanged on the pre-rebuild guide, so neither is a regression; evidence is in [`v4.13.4-last-phase-evidence.md`](development/v4.13.4-last-phase-evidence.md).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 6 |
| Warnings (WN) | 2 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### WN-1 (v4.13.4): The header navigation overflows under the matrix's 200% CSS zoom at 1280x720

**Evidence**: `tests/guides/tools/browser_matrix.py --groups zoom` fails four cases (`zoom200-describe-review-*` and `zoom200-presentify-*` at 1280x720) on `horizontalOverflow` alone, with no page error, missing region, or overlap. The overflowing elements are `#navLinks` and `#themeToggle` (document `scrollWidth` 1324 against a 1280 viewport). The pre-rebuild guide on `develop` measures the same 1324 with 28 overflowing elements instead of 6, and a real 640x720 viewport, which is what 200% of 1280 represents, has no overflow on either revision. **Reason**: `document.documentElement.style.zoom` does not change the width that CSS media queries see, so the header never switches to its narrow layout under this emulation; native browser zoom does change that width but is not measured here. **Owner**: guide owner, together with the open [v4.4 MT-446-2](../../../archives/v4/v4.4/known-gaps.md) native-zoom item. **Suggested next step**: measure native 200% zoom on a real browser; if the header overflows there, collapse it by container width rather than viewport width, otherwise change the matrix's zoom cases to emulate native zoom.

#### WN-2 (v4.13.4): An idle game labels its toggle "Pause game"

**Evidence**: before a game starts, its primary control reads "Pause game" while the HUD state reads `idle` (1440 px and 420 px section captures). `syncHud` derives the label only from the manual and pointer pause reasons, and the v4.4.x baseline uses the same expression. **Owner**: guide owner. **Suggested next step**: label the idle control from the lifecycle ("Start game" when idle, "Pause game" while running, "Resume game" when paused) and assert all three labels in `tests/guides/test_arcade_shooter_game.py`.

### Resolved Items

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-1 | The no-canvas fallback described every game as buggy | Phase 7 | The fallback text is rebuilt from each instance's damage and movement settings whenever they change; a browser test forces canvas unavailability on all three games. |
| BG-2 | Clicking the current section link scrolled to the page top | Phase 7 | A same-hash click or keypress calls the section router instead of the page-top routine; regression-tested. |
| BG-3 | Without `IntersectionObserver`, a game started through the API kept running on a hidden page | Phase 7 | A `page-hidden` pause reason follows Training page visibility independently of viewport observation; the tick is asserted to stop after navigating away. |
| BG-4 | Long commands were clipped against the Run button at desktop width | Phase 7 | Training command text wraps at every width. |
| BG-5 | The retained browser matrix clicked the removed presentation control and used an ambiguous game selector | Phase 8 | Its Training groups now target the seven section routes, section-scoped geometry, and the `buggy` instance; `tests/guides/test_v4134_browser_matrix.py` guards the mapping. |
| BG-6 | Seven browser tests failed on a runner without Playwright | Phase 8, PR #382 | The first hosted `tests` job (Linux, no Playwright) failed seven v4.13.4 tests that imported Playwright directly instead of skipping like their module fixtures. Reproduced locally by hiding Playwright; each module now routes its fixture and standalone tests through one `_sync_playwright()` helper, which skips, or fails under `NEXUS_REQUIRE_RENDER=1`. |
| WN-3 | An agent could not select the `/review` simulation through `window.NexusTraining` | Phase 7 | `selectAction(sectionId, commandOrIndex)` shares the button path and is documented in `guides/website/README.md`. |
| MT-1 | The browser flow stopped after `/review`, and section headings could drift from the scene source | Phase 7 | A browser test runs every later command and asserts section output and cumulative files; a parity test binds each `h2` to its scene record. |

## v4.13.5

Gaps from the completion-checker remote-resolution fix ([`v4.13.5-completion-checker-remote-resolution`](plans/v4.13.5-completion-checker-remote-resolution.md)); evidence is in [`v4.13.5-last-phase-evidence.md`](development/v4.13.5-last-phase-evidence.md).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 5 |
| Warnings (WN) | 0 | 3 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

None.

### Resolved Items

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-1 | An authority trick could read as a GitHub host | Phase 2 | The final-phase adversarial probe found that `https://evil.com#@github.com/acme/demo` parsed as host `github.com`, although git ends the authority at `#`. `parse_remote` now rejects any remote containing `#`, `?`, or a backslash; four regression cases cover the `#`, `?`, backslash, and `ssh://` forms. |
| BG-2 | A Windows drive-relative path read as an SSH host | Phase 2 | git treats `C:owner/repo` as a local directory on Windows, but the parser read host `c`; one `Host c` entry mapping to github.com would have shown `approval.remote met` for a push to a local folder. Single-letter scp hosts are now rejected on every OS. |
| BG-3 | An SSH alias routed through a proxy counted as verified | Phase 2 | Only the `hostname` line of `ssh -G` was read, so a `ProxyCommand` or `ProxyJump` to another server passed. Either setting other than `none` now leaves the alias unverified. |
| BG-4 | With `GH_HOST` set, a github.com remote was checked against the enterprise host | Phase 2 | Both `github.com` and `GH_HOST` were accepted, but `gh --repo owner/repo` queries only one of them. The accepted host is now exactly the one `gh` queries: `GH_HOST` when set, otherwise `github.com`. |
| BG-5 | CodeQL flagged a no-effect statement in `repo_host.py` | Phase 2, PR #387 | The `...` body of the `Budget` protocol method raised "Statement has no effect" (alert 328), and the unresolved review thread blocked the merge under `develop`'s conversation-resolution rule. The body is now a docstring. |
| WN-1 | A stray scratch script has shipped at the repository root since v4.11.2 | v4.13.6 Phase 8 | `scratch_p6cmd.py` (a one-off v4.11.2 edit script that rewrites files under a hard-coded absolute path to a developer working copy) was deleted after `git grep` found no reader in any installer, test, script, or workflow; only historical docs mention it. `check_python_floor.py` and the full local profile pass without it. |
| WN-2 | Git transport overrides could redirect a push the checker verified | v4.13.6 Phase 2 | `repo_host.verify_push_route` makes `approval.remote` `cannot-verify` for `GIT_SSH`, `GIT_SSH_COMMAND`, and `core.sshCommand` (SSH); for HTTPS, anything that weakens or replaces TLS verification (`http.sslVerify` false, `GIT_SSL_NO_VERIFY`, a CA bundle from the environment or from a user-writable config scope) and `http.curloptResolve`; and for any remote `remote.origin.vcs`, a `<transport>::` URL, `GIT_EXEC_PATH`, config injected through `GIT_CONFIG_PARAMETERS` or `GIT_CONFIG_COUNT`, an `insteadOf` rule that changes which verified repository is named, and an ssh config block (including `Match user` and port-specific blocks, probed as `ssh -G [-p port] user@host`) that changes the hostname or adds a proxy. A proxy with TLS verification intact is deliberately not an override, since it cannot present github.com's certificate. SSH hosts are resolved with the ssh git itself runs, and an undeterminable ssh is `cannot-verify`. Tests in `tests/validators/test_completion_minor_record.py`: `test_an_environment_override_is_cannot_verify`, `test_a_config_override_is_cannot_verify`, `test_a_remote_helper_url_is_never_met`, `test_a_proxy_with_tls_verification_intact_is_met`, `test_a_system_scope_ca_bundle_is_not_an_override`, `test_a_rewrite_to_the_same_repository_is_met`, `test_a_rewrite_to_another_repository_is_cannot_verify`, `test_an_ssh_config_host_override_is_cannot_verify`, `test_a_match_user_block_is_probed_with_the_user_git_sends`, `test_a_port_specific_block_is_probed_with_the_port_git_sends`, `test_an_alias_is_resolved_with_the_ssh_git_runs`, `test_an_undeterminable_git_ssh_is_cannot_verify`, `test_a_git_cmd_wrapper_does_not_break_the_route_check`, `test_the_checker_reports_a_redirected_push_on_approval_remote`. The rule is owned by the completion contract's Push route subsection. |
| WN-3 | `approval.remote` checked origin while a push could use another remote | v4.13.6 Phase 2 | The effective push remote for the source branch is resolved in git's order (`branch.<b>.pushRemote`, `remote.pushDefault`, `branch.<b>.remote`, then `origin`) and must be `origin`, otherwise `approval.remote` is `unmet` with the notice `push-remote-not-verified-remote`. Tests: `test_a_push_remote_other_than_origin_is_unmet`, `test_a_push_remote_set_to_origin_is_met`, `test_the_checker_reports_a_redirected_push_on_approval_remote`. |

## v4.13.6

Gaps from the minor-scope implement plan ([`v4.13.6-minor-scope-implement-and-verified-cleanup`](plans/v4.13.6-minor-scope-implement-and-verified-cleanup.md)). v4.13.5 WN-2 and WN-3 named this plan as owner; Phase 2 closed both, and they are recorded under v4.13.5's Resolved Items.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 10 |
| Warnings (WN) | 5 | 1 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 2 | 0 |

### Open Items

#### WN-1 (v4.13.6): Claude Code interactive `/goal` capture is observed only headless

**Evidence**: the Phase 1 probe (Claude Code 2.1.283, 2026-09-29) ran `claude -p "/goal test condition"`: the `UserPromptSubmit` payload's `prompt` field was exactly `/goal test condition` and the transcript shows `Goal set: test condition`. A person typing `/goal` in the interactive terminal was not exercised, so the `claude` row of `docs/policy/completion-levers.json` stays `goal_capture: unverified` with `probe_mode: headless`, and the validator accepts `verbatim` only from an interactive probe. **Owner**: catalog maintainer. **Suggested next step**: type `/goal test condition` in an interactive session of a scratch project whose `UserPromptSubmit` hook logs its payload, and set the row to `verbatim` with `probe_mode: interactive` if the logged prompt matches.

#### WN-2 (v4.13.6): Most older known-gaps ledgers read cannot-verify for a minor-scope run

**Evidence**: a read-only `python scripts/minor_close.py status --minor v4.13` on 2026-09-29 reads `gaps.minor unmet`, with 369 open item headings; 30 of the 41 ledgers in scope read `cannot-verify` (663 rows that look like item ids but are not items, and 11 header `**Open items**` counts that disagree with the parsed count). The stricter Phase 4 parser is correct to refuse them: a looser reader would let open work pass as closed. **Owner**: catalog maintainer, before the first real minor-scope run (v4.17). **Suggested next step**: normalize those ledgers to the known-gaps-tracker format (one heading per item, a terminal RESOLVED, CLOSED, or MIGRATED marker, and a matching header count) in a docs-only change, then re-run the status command until every ledger parses. The 2026-09-30 re-run (Phase 8, after AR-01, AR-02, and v4.13.5 WN-1 were resolved) reads 368 open headings and 674 unparsed rows; it also shows that this file restarts ids in each patch section, so `v4.13#WN-1` names four items. `minor_close.py migrate` refuses such an id with `gap-ambiguous`, which is safe, but the normalization must also make ids unique per minor file.

#### MT-1 (v4.13.6): The guide's scope-matching test checks no scope

**Evidence**: `test_rendered_scopes_match_their_command_files` in `tests/guides/test_nexus_hub_guide.py` searches for a bare `<code>` tag, but every Cheatsheets scope is rendered as `<code data-ty="code">`, so the test passes without comparing any scope with its command file. Found while adding `tests/guides/test_cheatsheet_command_sync.py`, which covers the `/implement` card only. **Owner**: catalog maintainer. **Suggested next step**: match the attribute form and extend the comparison to every command card, then confirm it fails on a deliberately stale card.

#### WN-4 (v4.13.6): The whole website guide reports 100 detector findings on views this plan did not touch

**Evidence**: `detect_visual_defects.py guides/website/nexus-hub-guide.html` (default viewports 420, 900, 1440; light and dark) reports the capped 100 findings, 10 `parent-padding-escape` (the first is the landing view's `h1 > b`) and 90 `svg-viewbox-overflow`, with the same distribution at base `7067df15`, so none comes from this plan. The Cheatsheets view this plan edited passes with 0 findings in both themes at base and head. **Owner**: guide maintainer. **Suggested next step**: run the detector per view with `--fragment`, fix or allowlist each finding with a recorded reason, and add the whole-page run to the guide render gate.

#### WN-5 (v4.13.6): v4.13.2 WN-9 is only partly closed

**Evidence**: Definition of Done 3 says it closes v4.13.2 WN-9 for every record type. Every bypass it names (a lone "ok", a quoted code, a pasted issue body, a runner-launched prompt) is refused by `tests/validators/test_approval_binding.py`, but the agent can still originate its own capture (pipe a payload into `completion_gate.py capture`, append to the capture file, or pre-seed a nested session), which is why that entry reads PARTIALLY RESOLVED. This pointer keeps the remainder visible in this plan's section; the item itself stays tracked under v4.13.2 WN-9. **Owner**: catalog maintainer. **Suggested next step**: bind a capture to a platform-authenticated user-turn signal where one exists, and record `cannot-verify` otherwise.

#### DF-1 (v4.13.6): Copilot CLI sets no native goal headlessly

**Evidence**: `scripts/run_plan.py` keeps `copilot/cli` in `INTERACTIVE_GOAL_ROWS` because its headless path is `copilot --autopilot -p` with a bypass flag, not `/goal`; the plan's cut-line allowed this slip (sub-task 6.3, T051). Claude, Qwen, and Kimi launch the goal headlessly. **Owner**: catalog maintainer. **Target version**: v4.17, with v4.13.2 DF-6. **Suggested next step**: re-check the Copilot CLI documentation for a headless goal entry point and add the row when one is documented.

#### QG-1 (v4.13.6): The non-engineer read-back of the approval page is pending

**Evidence**: Definition of Done 6 requires one non-engineer read-back recorded in the final phase. **Read-back result, 2026-09-30**: the user read the ten-section page rendered from the two-plan fixture (`approval_page.py` at `219513b3`) and found it too wordy, noting that many users will not read it. That result led to the redesign: a results table (released, fixed, archived, cleaned up, and permission prompts when they are turned off), two bold limits, and the paste line, all within 80 words, with the technical sections moved under "Details (optional)". The redesigned page has not been read back yet, so this item stays open. The automated half (jargon list, sentence ceiling, risk order, paste line without paths) passes in `tests/validators/test_approval_page.py`. **Owner**: the user, via the orchestrator. **Suggested next step**: have a non-engineer read the redesigned page (the two-plan fixture render, saved beside the first read-back as `readback-page-v2.md`), then record pass or fail with the page version in `development/v4.13.6-last-phase-evidence.md`.

#### QG-2 (v4.13.6): The edited guide card had no full accessibility or design audit

**Evidence**: the Tier 3 pass covered the edited Cheatsheets `/implement` card with the visual-defect detector (0 findings), clipped captures at 1440 and 420 px (no horizontal overflow, inspected), and a control probe (both copy buttons named "Copy to clipboard" and focusable; scope text 16 px). The full `[[accessibility-engineering]]` and `[[hallmark-design]]` audits were not run in this phase. **Owner**: guide maintainer. **Suggested next step**: run both audits on the Cheatsheets view before the next guide release and record the result here.

#### WN-6 (v4.13.6): Unusual branch, surface, and vendor names reach the approval page as written

**Evidence**: Tier 3 adversarial finding ADV-5 (P3). `render_page` with source branch `feat/refs/heads/check_plan_completion.py`, class `ask-first:hmac-nonce-schema`, and spend vendor `predicate` put every banned-list term and a script name above the paste line; the paste line itself stayed clean, and the allowed character sets rule out spaces, so no sentence can be injected. The plain-language guarantee is enforced by tests on fixture inputs, not at render time. **Owner**: catalog maintainer. **Suggested next step**: run the banned-term and path or script checks inside `render_page` (raising `PageError`), or move these values into the quoted details block.

### Resolved Items

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-3 | One approval-page sentence reads as engineering shorthand | 2026-09-30 (page redesign after the QG-1 read-back) | The `minor-close-pr` sentence now reads "Open one final pull request that closes v0.5 and merge it once its checks pass, then copy any newer main changes into develop. If a required check fails, it may push a fix up to 3 times." The bound's meaning comes from the runbook's Minor close step 7 (re-push "within the recorded `minor-close-pr` repush bound"), so the page no longer reports an undefined number. `tests/validators/test_approval_page.py::test_the_minor_close_sentence_says_what_its_bound_counts`. |
| BG-1 | `secret-scan.sh` never matched a private key | Phase 8 | Found by the new `test_secret_scan.py` parity cases: the four private-key patterns start with `-----`, so `grep -qE "$PATTERN"` read each one as an option, exited 2 silently, and never matched, on every host, while the `.ps1` blocked. The hook now passes `-e`; `test_a_secret_is_blocked[sh-python-private-key-on-a-later-line]` failed before the fix and passes after it. Pre-existing, not introduced by this plan. |
| BG-5 | `secret-scan.sh` allowed a large write whose secret sat near the start | Phase 8 (Tier 3 cycle 1) | ADV-1 (P1, pre-existing): under `set -o pipefail`, `echo "$CONTENT" \| grep -q` exited on the first match, `echo` took SIGPIPE, and the `if` read a real match as no match, so a key on line 1 of a 20000-line write was allowed (rc 0) while the `.ps1` blocked. The scans now read a here-string (`grep ... <<<"$CONTENT"`, `grep -m1` for the matched line). `test_a_secret_at_the_start_of_a_large_write_is_blocked` fails on the old hook and passes on the fix. |
| BG-6 | A Python 2 `python` counted as the secret-scan parser | Phase 8 (Tier 3 cycle 1) | ADV-8: the probe `-c 'import json'` passes on Python 2, whose `sys.stdin.buffer` then fails inside the field reader, leaving no content and allowing the write. The probe now requires Python 3. `test_a_python2_named_python3_is_not_a_parser` fails on the old probe and passes on the fix. |
| BG-7 | An invalid `NEXUS_HUB_SRC` was ignored silently | Phase 8 (Tier 3 cycle 1) | ADV-9: `nexus-hub init` fell back to another tree when the override did not qualify. A set override is now the only candidate, and one that is not a source tree exits 2 with a message. `test_an_invalid_nexus_hub_src_is_refused_not_ignored`. |
| BG-8 | Scope and code tokens accepted a trailing newline and non-ASCII digits | Phase 8 (Tier 3 cycle 1) | ADV-4 (P3): `$` matched before a trailing newline and `\d` matched any Unicode digit, so `v4.13\n` or `v4.1` with an Arabic-Indic three validated as a minor and could key a second record. The validators in `completion_minor.py`, `approval_page.py`, `approval_binding.py`, and `minor_close.py` now use `\Z` and `re.ASCII`. `tests/validators/test_canonical_tokens.py` (15 cases). |
| BG-9 | Cleanup never removed anything once a repository had 1000 merged pull requests | Phase 8 (Tier 3 cycle 1) | ADV-3 (P2): a full `gh pr list --limit 1000` page made every item `gh-unavailable`, so `cleanup.merged` could never be met. A truncated bulk list now falls back to one `--head=<branch>` query per candidate branch. `test_a_truncated_pull_request_list_falls_back_to_per_branch_queries`. |
| BG-10 | Four existing tests still pinned text that Phases 2-7 rewrote | Phase 8 (full-suite stabilization) | The first full local profile found them; the phase-level runs had not included these groups. `tests/skills/test_implement_driver_modes.py::test_full_is_canonical_and_in_full_is_the_compatibility_alias` pinned the old `/implement` card row (now `<plan> full`, "Accepted alias for the default (also in-full)."); `tests/validators/test_docs_layout_prescription.py::test_catalog_has_only_exactly_allowlisted_legacy_layout_lines` flagged two completion-contract lines that list the legacy layouts the minor checker reads, now allowlisted as read-only descriptions; and two `test_plan_worktree_isolation.py::test_cleanup_step_is_fail_closed` cases looked for the pre-`cleanup_merged.py` prose, now repointed at the step's no-override and no-force sentences, with the clean-tree proof owned by `test_cleanup_merged.py`'s `dirty` and `untracked` cases. |
| BG-2 | A security gap could migrate without being named on the approval page | Phase 8 (coordinator follow-up) | ADV-2 (P2, security). One gate, `completion_minor.migration_gate`, now decides every write and verify path: `minor_close.py migrate`, `verify_migration` (the minor verdict), and a member's deferral of a frozen gap (`_pending_migration`). It requires the id in the frozen list, the item present, open, and unambiguous at the record's `start_head`, and `named` whenever the item is security or high-severity either now or at `start_head`, so editing `**Severity**: high` down during the run cannot lift the naming. `record render` and `create --minor` also refuse a frozen id whose ledger entry is not open, or a sensitive one not in `named` (`check_migratable`); an id no ledger holds yet renders but can never migrate. Tests: `test_gap_migration_and_archive.py::test_lowering_the_severity_after_approval_does_not_lift_naming`, `::test_the_verify_path_uses_the_same_baseline`, `::test_a_gap_resolved_at_the_start_never_migrates` (the first and third fail on the pre-fix scripts), and `test_completion_minor_record.py::test_a_frozen_security_gap_must_be_named_before_the_page_renders`. |
| BG-3 | `MINOR COMPLETE` was reachable with no archive, closing pull request, or final cleanup | Phase 8 (coordinator follow-up) | ADV-6. Decision: a minor run requires `cleanup-merged`, `archive-minor`, and `minor-close-pr`, matching Definition of Done 2 ("the final cleanup pass has run after the last merge, the closing pull request is merged, and the minor is archived"). `minor_spec` refuses a spec without all three, so `record render` and `create --minor` cannot approve one; `check-minor` reads a missing class as `unmet` with a notice, never `n/a`; and `minor.close-pr` is never `n/a`, because the close always carries the archive (with nothing to migrate it carries only the archive). The completion contract, the runbook's Minor close, and `/update` now say the same. Tests: `test_completion_minor_verdict.py::test_a_minor_record_without_the_closing_classes_never_completes`, `::test_a_minor_spec_without_a_closing_class_is_refused` (three cases), `::test_a_frozen_id_fixed_instead_of_migrated_still_needs_the_close`, and `test_gap_migration_and_archive.py::test_archive_minor_predicate_reads_the_integration_branch`. |
| BG-4 | Naming another session's scope lifted its owned-by-run protection | Phase 8 (coordinator follow-up) | ADV-7, reproduced first: with session s1's live record owning the merged, idle `feat/plan`, `cleanup_merged.py --dry-run --plan <plan>` from another caller printed `REMOVE branch:feat/plan`. `cleanup_merged.py` gained `--session`: the named `--plan` or `--minor` record is exempt from the owned-by-run scan only when it loads verified and is bound to that session (otherwise it stays in the scan, with the notice `scope-record-not-own`), and `--receipt` needs the record's own session (`BLOCKED: approval-not-covered`, reason `session-required` or `record-bound-to-another-session`). `/update`, the runbook, the contract, and the e2e stub pass `--session`. Tests: `test_cleanup_merged.py::test_naming_another_sessions_plan_keeps_its_owned_items` (failed before the fix) and `::test_a_receipt_needs_the_records_own_session`. |

## v4.13.7

Gaps from the Copilot usage monitor and usage-limit handoff plan ([`v4.13.7-copilot-usage-monitor-and-usage-limit-handoff`](plans/v4.13.7-copilot-usage-monitor-and-usage-limit-handoff.md)). Recorded by sub-task 4.1; Phase 4 ran before Phases 1-3, which wait on the maintainer's live Copilot readings.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 1 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### BG-1 (v4.13.7): `/usage` dispatches to a `check-usage` skill that does not exist

**Evidence**: `catalog/commands/usage.md` delegates every invocation to `check-usage` ("(any invocation) -> check-usage"), and no `catalog/skills/*/check-usage/` directory exists on `feat/v4.13.7-copilot-usage-monitor-and-usage-limit-handoff` after the 2026-10-01 merge of `develop` at `81d7e544`. The command therefore has no procedure behind it on any platform. Pre-existing; out of scope for this plan (plan Overview, "Out of scope"). **Owner**: catalog maintainer. **Suggested next step**: back `/usage` with `catalog/hooks/_usage_probe.py` (built in Phase 6) in a later release, either as a restored `check-usage` skill or by pointing the dispatcher at a skill that calls the probe.

#### WN-1 (v4.13.7): `skill-activation-suggest.py` silently loses `_skill_rules` on adapters that copy only registered scripts

**Evidence**: `catalog/hooks/skill-activation-suggest.py` wraps `from _skill_rules import ...` in a `try` that degrades to a no-op on `ImportError`. The Codex, Copilot, Antigravity, and Windsurf adapters copy registered scripts plus `sourced_modules()` from `scripts/lib/integrations/_hooks_common.py`, which collects only `_*.sh` and `_*.ps1` helpers (`p.suffix in (".sh", ".ps1")`), so `_skill_rules.py` is never delivered beside the hook there and the suggestion hook does nothing without saying so. **Owner**: this plan, sub-task 6.1. **Suggested next step**: resolved by the `sourced_modules` extension in 6.1 (collect `_*.py` modules a registered `.py` hook imports); verify `_skill_rules.py` lands in an installed Codex hook directory and close.

#### WN-1 (v4.13.7): The all-refs attribution scan fails on fetched Dependabot branches

**Evidence**: `python scripts/check_commit_attribution.py --all-refs`, run by the fast profile, uses `git log --all` and allows only approved identities, so the three `origin/dependabot/*` branches fetched into this repository on 2026-10-01 produce three `dependabot[bot]` author findings and fail the step. Commits still succeed, because the commit hook runs only the message and pending-identity checks. Merging a Dependabot pull request would put bot-authored commits into history and fail the scan permanently. **Owner**: catalog maintainer (attribution policy decision). **Suggested next step**: scope the all-refs scan to local branches, `origin/main`, `origin/develop`, and the current pull request head, and decide separately whether `dependabot[bot]` is an allowed author.

### Resolved Items

None yet.
