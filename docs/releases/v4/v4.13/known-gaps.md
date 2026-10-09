# Known gaps - v4.13

**Project**: Nexus-Hub
**Status**: released; PR #230 merged the complete 34-task plan and tag `v4.13.0` was published on 2026-09-21. Two bounded warning-class findings remain owned for future measurement work. GitHub branch protection passed a live pull-request gate test; the second trigger pilot stopped on an unproven spend bound.
**Last updated**: 2026-10-09
**Open items**: 157
**Accounting, 2026-10-09 (v4.13.11 T006-T007)**: The Open items header is derived from current parsed state, including canonical historical owners. Patch Summary tables preserve their release-time snapshots; they do not replace the current header count. Original patch/ID identities remain in the source bodies and the reconciliation manifest.

Release-scoped gaps for the evidence-driven agent improvement plan. Planned future-phase work is tracked in the plan rather than reported as completed here.

## v4.13.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 1 | 6 |
| Warnings (WN) | 3 | 4 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 4 |

### Open Items

#### BG-7-v4130: The second pilot's per-call budget did not bound reported cost

**Source phase**: 2026-09-23 post-release trigger follow-up. **Plan reference**: [`trigger-pilot-2/protocol.md`](../../../archives/v4/v4.13/development/trigger-pilot-2/protocol.md). **Reason**: the first two strong-tier calls reported USD 0.6540 and USD 0.6292, each above the runner's USD 0.50 per-call reservation, and both had unknown selector evidence. The process was interrupted; no complete result file exists. The aggregate check cannot guarantee the approved hard USD 35 ceiling when a call can exceed the amount reserved for it.

**Owner**: catalog maintainer. **Status**: open; the second pilot is `UNMEASURED`. **Suggested next step**: establish a provider-enforced ceiling or proven per-call upper bound, fix and test pre-call reservation and crash-safe per-call receipts, then freeze a new protocol before spending again. Preserve the [aborted attempt](../../../archives/v4/v4.13/development/trigger-pilot-2/attempt.md) and the original 96-call evidence unchanged.

**Local safety candidate, 2026-09-23**: The runner now rejects non-finite or negative reported cost, records an atomic in-flight receipt before each call and a completed receipt after it, refuses to overwrite an existing receipt, and stops before a second call when reported cost exceeds the per-call reservation. These controls preserve partial evidence and prevent further calls after an observed overrun; they do not retroactively bound the overrun or make USD 35 a hard ceiling. The pilot remains `UNMEASURED`, and no further paid call is authorized by this candidate alone.

**Provider-cap preflight, 2026-09-24**: The installed Claude Code 2.1.280 currently authenticates as `claude.ai` on a Team subscription, not as a Claude Console workspace API key. The [archived preflight](../../../archives/v4/v4.13/development/trigger-pilot-2/provider-cap-preflight-2026-09-24.md) distinguishes Team usage-credit limits from a dedicated Console workspace cap and records the account, key-binding, and limit-refusal evidence required before another paid call. BG-7 remains open and the second pilot remains `UNMEASURED`.

**Original source identity**: `v4.13.0#BG-7`; stable ID `BG-7-v4130` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-2: Tool-span attributes unverified at the pinned revision - RESOLVED 2026-09-22

**Source phase**: Phase 2. **Plan reference**: T005. **Reason**: the `gen_ai.tool.*` attribute table could not be retrieved at pinned revision `5ca9052bc796ef1e497200b1d558fd87a201f335`. The containing document truncates before that section and the standalone tool-spans path returns HTTP 404 at that revision. The `execute_tool` operation name itself is confirmed.

**Resolution**: the agent-spans page links to `docs/gen-ai/gen-ai-spans.md#execute-tool-span` at the same pinned revision. That sibling table verifies `gen_ai.tool.name` as Required, call ID, description, and type as Recommended if available, and arguments and result as Opt-In. The contract now names those levels, keeps arguments, results, and descriptions absent from default traces, and has a regression assertion for the pinned sibling link and field levels. The original retrieval failure above remains historical evidence.

#### WN-3-v4130: The shipped catalog under-triggers on its own positive prompts

**Source phase**: Phase 6. **Plan reference**: T022, T023. **Reason**: the pilot's control arm is the currently shipped corpus. Across four sampled skills and eight positive prompts it selected the skill on **1/8** with the fast model and **3/8** with the strong model, while producing **zero** irrelevant selections across all 32 near-miss and trivial-edit prompts. The catalog's measured failure mode is under-triggering, not over-triggering.

**Evidence**: `development/trigger-pilot-results.md` and the raw `trigger-pilot-results.json` (96/96 calls, 0 failures, 0 evidence-missing). The regression is concentrated in `skill-description-authoring` on the strong model, 2/2 to 0/2 under the candidate wording.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: this finding is recorded, not acted on. `AGENTS.md` prescribes pushier descriptions with explicit SKIP clauses as the remedy, and the pilot measured that remedy making selection **worse** on both models, so the prescribed fix is now evidence-contradicted. Changing the authoring guidance needs its own frozen pilot with a candidate designed against this data; nothing in this release may change a description on the strength of the finding alone.

**Original source identity**: `v4.13.0#WN-3`; stable ID `WN-3-v4130` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-5-v4130: The recorded pilot run cannot be re-audited for the loose selection matcher

**Source phase**: Phase 7. **Plan reference**: T030 (Tier 3 deep pass, adversarial step). **Reason**: the runner scored a selection with a substring test over the whole serialized `Skill` tool input, so a call invoking a different skill while mentioning the target would have counted. The matcher is fixed and covered by tests, but the recorded 96-call run did not retain tool-call payloads, so its five positive rows cannot be re-checked directly.

**What is known**: the `Skill` tool was invoked exactly 5 times across all 96 calls; those 5 are exactly the 5 rows scored as selected; each falls on a positive prompt for the skill under test; no row shows a `Skill` invocation without a scored selection. The defect can only inflate a positive, never hide one, so all reported counts are upper bounds and control arm A could only be equal or lower.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: retain the `Skill` tool input alongside `tools_used` in any future run so the question is answerable from the data. Do not re-run the pilot for this alone; the disposition `MEASURED_NO_CHANGE` does not turn on it, because a lower A would narrow the gap criterion 1 already failed on.

**Follow-up, 2026-09-22**: Future runner rows now retain `skill_selectors`, a bounded record of only the `command`, `skill`, and `name` selector fields from each `Skill` call. Scoring reads the same normalized values; non-skill values become `<invalid>`, and prompt or other tool arguments are never copied into results. Tests prove a different skill mentioning the target stays negative, a valid target stays positive, private non-selector text is absent, and normal and timed-out rows retain the observed selector. This mitigates future re-audit failure but cannot recover the 96 historical tool inputs, so this historical evidence gap remains open.

**Original source identity**: `v4.13.0#WN-5`; stable ID `WN-5-v4130` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-6: Symlink refusal is unproven on Windows without developer mode - RESOLVED

**Status**: RESOLVED 2026-09-22 for the declared cross-platform contract. PR #230's Ubuntu `tests` job passed, and a direct WSL2 Ubuntu standard-library probe executed the same two cases: the script returned exit 2 without overwriting a symlink target, and `describe_destination` disclosed the redirected ancestor. Windows developer mode is not required to prove the Linux/macOS path; Windows retains its native junction coverage.

**Source phase**: Phase 7. **Plan reference**: T030. **Reason**: two new tests covering the trace script's symlinked-target refusal and its redirected-ancestor disclosure `skip` on a Windows host that does not permit creating a symlink. They run on the Linux and macOS CI legs.

**Owner**: `ai-agent-development`. **Status**: resolved 2026-09-22 by the Linux proof recorded above. Windows continues to exercise its native junction path and does not need developer mode for the cross-platform contract to be complete.

**Normalization, 2026-10-09 (v4.13.11 T006)**: Parsed RESOLVED marker records the already evidenced disposition retained above. No new runtime or historical capture is claimed.

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

### Historical carry-forward from v4.0 through v4.12

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

**Re-binding, 2026-10-09 (v4.13.11 T008)**: The twelve ledger bindings below were recomputed after terminal/structural normalization and complete item-level transfers. The before/after manifest preserves all prior bindings and the two separate historical plan hashes; no signed approval was edited.

**Archive relocation, 2026-09-28**: all 12 source ledgers matched the hashes previously recorded below at pre-move `develop` commit `42490dca`. They then moved to `docs/archives/v4/<minor>/known-gaps.md`; relative links inside and into them were repaired without changing any gap status or ID. The hashes below now bind the archived, link-repaired bytes. The pre-move hashes and files remain recoverable from `42490dca`; v4.13 gaps were not transferred or moved. **Re-binding, 2026-09-29**: the whole-minor archive of v3 and the remaining v4.0-v4.11 content rewrote links and path mentions inside ten of the bound files (nine ledgers and the v4.4.6 plan) so they resolve to `docs/archives/`; no gap status, ID, or task box changed. The affected hashes below were recomputed to bind those repaired bytes.

| Minor | Source ledger | Normalized SHA-256 |
|---|---|---|
| v4.0 | [ledger](../../../archives/v4/v4.0/known-gaps.md) | `3074de96b2fbf26e0ecb2a711c9c39b5ac138249a4639114c4099199eab790ad` |
| v4.1 | [ledger](../../../archives/v4/v4.1/known-gaps.md) | `ce21dcab5cd5ac09ee7270cc6e61ccb5c78ba48f7e40af0afe4807f28e2c2089` |
| v4.2 | [ledger](../../../archives/v4/v4.2/known-gaps.md) | `1e203adeb10e056443731ae2ebc192b4424e1d8c48819afae3740d6c5bbefb81` |
| v4.3 | [ledger](../../../archives/v4/v4.3/known-gaps.md) | `8496eeee6f6eb75241eef268fb4164a9773c8c5f3bd83cc2fb0fba08c5ddcb9b` |
| v4.4 | [ledger](../../../archives/v4/v4.4/known-gaps.md) | `c4c814de8c499aaa309c6fcbaa83ec85397866447a4074badf344de25953b04e` |
| v4.5 | [ledger](../../../archives/v4/v4.5/known-gaps.md) | `8c33648e2da252fee7da7092495b01fdd9f2936962c311691da4bc144466c707` |
| v4.7 | [ledger](../../../archives/v4/v4.7/known-gaps.md) | `edac574e067bb4c4ee5f6f4af68642b5037572a4cd07df5b162926f901ba41de` |
| v4.8 | [ledger](../../../archives/v4/v4.8/known-gaps.md) | `4863069afaa200d07911965c20e44c54a054c99c784d7f159f8ef7ad379de411` |
| v4.9 | [ledger](../../../archives/v4/v4.9/known-gaps.md) | `f9d8e18d9d17fe0e8754eff7e3c47ce4cf1ef5106071797bc75c1afdf8b4d0dd` |
| v4.10 | [ledger](../../../archives/v4/v4.10/known-gaps.md) | `0868e77b545ff386a731870b8045921ae9d495aaf056cfa1204443ccf7c40dbb` |
| v4.11 | [ledger](../../../archives/v4/v4.11/known-gaps.md) | `5a0455c17769d9f25e52b9decd7133c74c50fcc9fed9d7bf4f68cfb989d408e6` |
| v4.12 | [ledger](../../../archives/v4/v4.12/known-gaps.md) | `a012c6bf7816fb7a29cb10d9ca2b1a14f5b3c1101ee122e397d6df421377d86a` |

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

### Migrated from archived minors (v3.x, v4.0-v4.11) - 2026-09-29

On 2026-09-29 every v3 minor and the remaining active content of v4.0, v4.1, v4.3, v4.4, v4.5, v4.9, v4.10, and v4.11 moved to `docs/archives/`. Before the move, each open item in the v3.0-v3.21 ledgers was audited against the tree: items with concrete evidence were marked resolved in their source file, items made moot by a removal or a recorded decision were closed there with the reason, and the items below are the ones still genuinely open. Duplicates recorded by several minors are merged into one entry. After the 2026-10-09 item-level normalization, each source ledger states `**Open items**: 0` and ends with an `Archive reconciliation - 2026-09-29` table naming every disposition. The 2026-10-09 sweep brings every remaining historical origin into a complete canonical copy below, including the v4.0-v4.12 sources previously represented only by the inventory. v3.5 had no known-gaps register; its only plan has no unchecked boxes and tag `v3.5.0` exists.

**Migrated items**: 58 open (2 resolved: AR-01 and AR-02 in v4.13.6 Phase 8): 57 from 137 source rows, plus AR-58 raised by the archive pass itself, plus AR-59 and AR-60 recovered on 2026-09-30 from an unmerged local ledger draft. Migration transfers tracking only: each entry below stays open until its own evidence closes it.

### Security-relevant

### AR-02: `secret-scan.sh` allows every write on a host without `jq` - RESOLVED 2026-09-30

- **Current state**: `catalog/hooks/secret-scan.sh` exits 0 when `jq` is missing, so the secret scan silently does nothing there.
- **Owner and next step**: hooks maintainer; reuse the Python fallback already used by `old-version-docs-guard.sh` (v4.0 BG-5), with a test that removes `jq` from PATH.
- **Historical transfer note**: v3.16.2#BG-2 on 2026-09-29 (reason: still open; verified by reading the hook on 2026-09-29).
- **Resolution** (v4.13.6 Phase 8): root cause was the `else exit 0` branch taken whenever `jq` was missing. The hook now reads the payload with jq, falls back to Python 3 (the same fallback `old-version-docs-guard.sh` uses), and fails closed (exit 2, "cannot be scanned") with neither; a malformed payload is still allowed on every path, as in the `.ps1`. The new parity suite also exposed an older defect on every host: the four private-key patterns start with `-----`, so `grep -qE "$PATTERN"` read them as options and never matched; the hook now passes `-e`. Tests: `catalog/hooks/tests/test_secret_scan.py` (each case parametrized over `sh-jq`, `sh-python` with a PATH that holds no jq, and `ps1`: `test_a_secret_is_blocked`, `test_a_secret_in_an_edit_new_string_is_blocked`, `test_clean_content_is_allowed`, `test_a_payload_without_content_is_allowed`, `test_the_report_names_the_category_not_the_secret`, plus `test_the_sh_fails_closed_with_neither_jq_nor_python`) and `test_hook_sibling_parity.py::test_secret_scan_blocks_a_real_secret`, which previously asserted the fail-open exit 0.

### AR-03: The presentify repository walk has no secret redaction

- **Current state**: the extractor copies repository text into the generated site; the extraction runbook only warns about secrets.
- **Owner and next step**: presentify owner; route repository-walk text through `egress-redaction` rules before it reaches the output.
- **Historical transfer note**: v3.13#DF-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.13#DF-3 (reason: user-deferred); original `v3.13.0#DF-3`, section `v3.13.0`.

#### Original source: DF-3 - No secret redaction on the repository walk - MIGRATED to v4.13 (AR-03)

- **Source phase**: Phase 1 (1.2)
- **Reason**: The walk ingests text / config files by extension; dotfiles with no recognized extension (`.env`) are not ingested, but a file such as `secrets.yaml` would be. There is no content-based secret detection.
- **Suggested next step**: Users should not point `/presentify` at a repository holding plaintext secrets; a future pass could integrate the `egress-redaction` skill's typed policy before ingestion.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-03`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `DF-3`.

### Installer and CLI

### AR-01: `nexus-hub init` is unreachable through the launcher - RESOLVED 2026-09-30

- **Current state**: `python scripts/nexus_hub_cli.py init --help` exits with "invalid choice: 'init'" (observed 2026-09-29). The installer tells users to run `nexus-hub init`, and `nexus-hub-autoseed.sh` calls it and ignores the failure. `init` exists only in `scripts/lib/integrations/runner.py` and as an installer subcommand; the monorepo `--target` support (spec-kit S8) is therefore unreachable too.
- **Owner and next step**: installer/CLI maintainer; add an `init` passthrough to `nexus_hub_cli.py` with a launcher-level test, then close S8 once `nexus-hub init --target <subdir>` works end to end.
- **Historical transfer note**: v3.11#DF-1 (launcher part) and v3.11#DF-v311-speckit-S8 on 2026-09-29 (reason: live defect found during the audit).
- **Resolution** (v4.13.6 Phase 8): root cause was that `scripts/nexus_hub_cli.py`, which both launchers call, never registered `init`; only `installer.sh init` / `installer.ps1 init` reached the runner. The CLI now forwards `init` and every token verbatim to `scripts/lib/integrations/runner.py init`, with the same `NEXUS_HUB_INIT=1` marker the installers set, from the first tree that holds both the runner and `catalog/` (`NEXUS_HUB_SRC`, the checkout the CLI runs from, then `~/.nexus-hub/src`); the installed `scripts/` tree has no catalog, so with no source tree it exits 2 with a remedy instead of an argparse error. No installer or hook edit was needed. Observed: `python scripts/nexus_hub_cli.py init --help` prints the runner's usage, and `init --target <dir> --dry-run` lists the Antigravity, Cursor, and Claude surfaces. Tests: `tests/installer/test_init_cli.py` (`test_init_forwards_every_token_and_the_intent_marker`, `test_init_returns_the_runner_exit_code`, `test_nexus_hub_src_takes_precedence_over_the_bootstrap_tree`, `test_a_runner_without_a_catalog_is_not_a_source_tree`, `test_init_is_no_longer_an_invalid_choice_from_the_checkout`, `test_init_is_listed_in_the_top_level_help`, `test_the_real_runner_seeds_a_monorepo_subdirectory_through_the_cli`, which also closes the spec-kit S8 `--target <subdir>` half, `test_the_posix_launcher_reaches_init`, `test_the_windows_launcher_reaches_init`).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Historical resolved origin**: v3.11#DF-v311-speckit-S8 (reason: user-deferred); original `v3.11.0#DF-v311-speckit-S8`, section `adoption-spec-kit third cycle (2026-07-08)`.

#### Original source: DF-v311-speckit-S8 - monorepo member-project targeting for `nexus-hub init` - MIGRATED to v4.13 (AR-01)

**v4.13.11 structural audit, 2026-10-09**: Converted this historical list obligation into a supported item heading. The complete source line is retained below; prior transfer wording alone does not prove a migration.

**Original list entry**: - **DF-v311-speckit-S8 - monorepo member-project targeting for `nexus-hub init`** (Low). The source supports targeting a specific member project inside a monorepo; Nexus-Hub's `nexus-hub init` seeds the current repo root. Deferred for lack of demand while `--workspace` already covers non-root targets. Next step (from the comparison): add an optional path argument to `nexus-hub init` that scopes seeding to a sub-project directory, only if monorepo users request it. - MIGRATED to v4.13 (AR-01)

**Resolution, 2026-10-09 (v4.13.11 T006)**: AR-01 already records the repaired init forwarding and optional monorepo target. Fresh `python -m pytest -q tests/installer/test_init_cli.py::test_the_real_runner_seeds_a_monorepo_subdirectory_through_the_cli` passed 1 test in 5.42 seconds, exit 0. That real installed-home CLI subprocess invokes the actual runner with `--target <temporary>/monorepo/packages/app` and verifies the target Cursor rule exists; the optional path obligation is satisfied. The full source remains below its heading and in AR-01 historical evidence.

### AR-05: Hermes is registered but not wired into either installer

- **Current state**: registered in `scripts/lib/integrations/__init__.py`; zero references in `scripts/installer.sh` and `scripts/installer.ps1`.
- **Owner and next step**: installer maintainer; wire both installer arms and their smoke tests in one change, or record Hermes as registry-only by decision.
- **Historical transfer note**: v3.15.2#DF-2, v3.16.0#NI-6, and v3.17.0#DF-4 on 2026-09-29 (reason: one obligation recorded three times, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#DF-4 (reason: user-deferred); original `v3.17.0#DF-4`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-4 - OPEN (carried from v3.15.2): Hermes is registered but not installer-wired - MIGRATED to v4.13 (AR-05)

- **Target files**: `scripts/lib/integrations/hermes.py`, `scripts/installer.sh`, `scripts/installer.ps1`
- **Source phase**: v3.15.2 DF-2, rechecked in v3.17.0 Phases 2 and 6
- **Reason it is open**: Hermes exists in the 16-platform integration registry but is absent from both installers' 14-platform delivery roster. Hermes is currently UNVERIFIED for autonomy, so the omission does not suppress a descriptor in this release; it would become user-visible immediately if its contract later verifies.
- **Suggested next step**: add Hermes to both installer manifests and real-installer smoke coverage in the same change that makes any Hermes integration artifact user-facing. Do not add one installer arm without the other.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-05`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-4`.

- **Migrated from**: v3.15#DF-2-v3152 (reason: user-deferred); original `v3.15.2#DF-2`, section `v3.15.2 - adoption-awesome-llm-apps`.

#### Original source: DF-2-v3152 - Hermes not yet first-class installer-wired (registry-only) - MIGRATED to v4.13 (AR-05)

- **Source phase**: v3.15.2 Phase 5.1 / 5.2.
- **Plan reference**: Phase 5.1 ("no installer copy-step edit is needed because the runner is invoked automatically").
- **Reason**: `hermes` is registered in `_register_builtins()` and installable on demand via `runner.py install --integrations hermes` (detection-gated), but the installers drive extended platforms through explicit `should_install <key>` / `invoke_registry_platform` blocks + a `known_platform_keys` list, and Hermes is intentionally NOT added to those yet (nor to the JSON `contract_checks`, which would then REQUIRE the installer reference and fail `verify_platform_contracts`). Editing the installers is an AGENTS.md "ask first" action and outside this phase's stated scope. Hermes therefore sits in the same tier as aider/windsurf/openclaw: registered + documented + runner-installable.
- **Suggested next step**: if Hermes adoption warrants it, promote it to a default-installed platform in a follow-on - add `should_install hermes` / `invoke_registry_platform` blocks to both installers, add `hermes` to `known_platform_keys`, and add a `contract_checks` entry (with the required installer reference).

**Original source identity**: `v3.15.2#DF-2` in `v3.15.2 - adoption-awesome-llm-apps`; normalized stable ID `DF-2-v3152` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-05`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.2`, section `v3.15.2 - adoption-awesome-llm-apps`, and original ID `DF-2`.

- **Migrated from**: v3.16#NI-6-v3160 (reason: user-deferred); original `v3.16.0#NI-6`, section `v3.16.0 - platform-defaults-config`.

#### Original source: NI-6-v3160 - OPEN: hermes is seedable but not installed by default - MIGRATED to v4.13 (AR-05)

- **Source phase**: Phase 3, sub-task 3.2.
- **Finding**: `hermes` is VERIFIED, has Exact surface alignment, and is declared writable, but it appears in neither installer's platform list (`invoke_registry_platform` / `Invoke-RegistryPlatform`). Its seeded default therefore reaches only an explicit `runner.py install --integrations hermes` run.
- **Why it is open**: promoting Hermes to a first-class default-installed platform is a tracked follow-on already recorded in AGENTS.md, and doing it here would have expanded this plan into platform onboarding.
- **Suggested next step**: fold into whichever cycle promotes Hermes. The seeding side needs no further work; it starts reaching users the moment the platform is installed by default.

**Original source identity**: `v3.16.0#NI-6` in `v3.16.0 - platform-defaults-config`; normalized stable ID `NI-6-v3160` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-05`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.0`, section `v3.16.0 - platform-defaults-config`, and original ID `NI-6`.

### AR-10: A PowerShell early-exit path leaks the selection staging directory

- **Current state**: documented as a residual in `scripts/installer.ps1`.
- **Owner and next step**: installer maintainer; wrap the post-`Resolve-Selection` flow in try/finally.
- **Historical transfer note**: v3.16.1#NI-6 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.16#NI-6-v3161 (reason: user-deferred); original `v3.16.1#NI-6`, section `v3.16.1 - evals-and-selective-installation`.

#### Original source: NI-6-v3161 - OPEN (documented, bounded): one PowerShell early-exit path still leaks a stage - MIGRATED to v4.13 (AR-10)

- **What remains**: an exit taken after `Resolve-Selection` but before completion (observed via the "Workspace path not found" validation) leaves its staging directory behind.
- **Why it is not fixed**: a `Register-EngineEvent PowerShell.Exiting` handler was written and then deliberately removed. Engine-event actions run in a separate scope where the `$script:`-scoped stage path is not reliably visible, so the cleanup could not be verified to run. An unverifiable cleanup is worse than a documented gap: it reads as covered while doing nothing.
- **Bound**: the residual is one directory under `%TEMP%` on an aborted install, not on the normal path. An earlier draft of the in-file comment claimed no such path existed; that claim was wrong and is corrected to describe the measured path.

**Original source identity**: `v3.16.1#NI-6` in `v3.16.1 - evals-and-selective-installation`; normalized stable ID `NI-6-v3161` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-10`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.1`, section `v3.16.1 - evals-and-selective-installation`, and original ID `NI-6`.

### AR-11: Antigravity skill seeding can exceed the Windows path limit in a deep repository

- **Current state**: `scripts/lib/integrations/base.py` copies skill trees with plain `shutil.copytree`. The same limit broke a plain Python move of the v4.9 benchmark evidence during this archive pass.
- **Owner and next step**: installer maintainer; use extended-length paths on Windows or shorten the deepest bundled paths.
- **Historical transfer note**: v3.11#WN-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.11#WN-2 (reason: user-deferred); original `v3.11.0#WN-2`, section `v3.11.0`.

#### Original source: WN-2 - Windows MAX_PATH risk when seeding Antigravity `.agents/skills/` into a deep target - MIGRATED to v4.13 (AR-11)

- **Source phase**: Phase 7 (7.3 auto-seed / 7.4 verify smoke)
- **Plan reference**: 7.3
- **Reason**: The Antigravity `.agents/skills/<name>/references/examples/...` flattened copy can exceed the Windows 260-char MAX_PATH when the target repo lives at a very deep path (observed with the OneDrive + deep-temp scratch dir during the 7.3 smoke; `shutil.copytree` raised WinError 3). A normal-depth repo is well under the limit.
- **Suggested next step**: Consider enabling Windows long-path support in the copytree (prefix `\\?\`) or shortening the deepest bundled skill paths; low severity - most repos are far under 260 chars, and the auto-seed is fail-open.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-11`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.11.0`, section `v3.11.0`, and original ID `WN-2`.

### AR-20: Workspace-scope install output is not grouped like the global install

- **Current state**: `install_workspace` and `Install-Workspace` never call the undetected-platform grouping and still print the verbose Claude block.
- **Owner and next step**: installer maintainer; apply the global checklist and grouping to the workspace path in both installers.
- **Historical transfer note**: v3.14.5#DF-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.14#DF-1-v3145 (reason: user-deferred); original `v3.14.5#DF-1`, section `v3.14.5`.

#### Original source: DF-1-v3145 - Workspace-scope Claude checklist + workspace undetected grouping deferred - MIGRATED to v4.13 (AR-20)

- **Source phase**: v3.14.5 Phase 2
- **Plan reference**: Phase 2 (2.1/2.3 - the plan's stability gate is a global side-by-side install)
- **Reason**: Phase 2 scoped the checklist + grouping to the GLOBAL install (`Install-Global` / `install_global`), which is what every screenshot showed. Workspace-scope registry platforms already get the checklist automatically via the shared `Invoke-RegistryPlatform` / `invoke_registry_platform` (the rewrite is scope-agnostic), but the workspace-scope Claude block still prints its bespoke verbose output, and workspace undetected platforms print an inline `(reason)` note rather than being collected into a grouped section (the grouping is gated on the `-Provider` arg, which only the global caller passes).
- **Suggested next step**: apply the same `6>$null`/`>/dev/null` + checklist treatment to the workspace Claude block and add `reset_undetected_platforms`/`write_undetected_group` (+ pass provider) to `Install-Workspace` / `install_workspace`. Low risk (mirrors the global rewrite); out of scope for the global-focused Phase 2.

**Original source identity**: `v3.14.5#DF-1` in `v3.14.5`; normalized stable ID `DF-1-v3145` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-20`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.5`, section `v3.14.5`, and original ID `DF-1`.

### AR-21: `nexus-hub verify` does not cover `extensions/`

- **Current state**: `scripts/generate_manifest.py` `COVERED_ROOTS` is still `catalog`, `templates`, `scripts`, `data`.
- **Owner and next step**: installer maintainer; extend the manifest to the distributed MCP-server sources or record the exclusion by decision.
- **Historical transfer note**: v3.10#DF-v310-ruflo-P4-extensions (also carried in v3.11) on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.10#DF-v310-ruflo-P4-extensions (reason: user-deferred); original `v3.10#DF-v310-ruflo-P4-extensions`, section `Open Items`.

#### Original source: DF-v310-ruflo-P4-extensions - MIGRATED to v4.13 (AR-21)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v310-ruflo-P4-extensions - MIGRATED to v4.13 (AR-21)

**Category**: DF

**Source**: adoption-ruflo Phase 4.1 (manifest scope)

**Reason**: The `nexus-hub verify` supply-chain manifest covers the core distributed catalog subtrees (`catalog/`, `templates/`, `scripts/`, `data/`) but intentionally excludes `extensions/` (the internal MCP-server sources: `nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`, `nexus-skill-scanner`, `nexus-context-compressor`). Those are pip-installed into a venv at install time rather than copied verbatim, and including their source trees would pull in build output / venv churn that destabilizes the deterministic manifest. So a tampered MCP-server source file is not currently caught by `verify`.

**Suggested next step**: Extend `COVERED_ROOTS` in `scripts/generate_manifest.py` to include `extensions/` with robust exclusions (`node_modules`, `out`, `dist`, `*.vsix`, `.venv`, `__pycache__`, `*.egg-info`) if MCP-server source integrity coverage is wanted; re-confirm determinism and that `verify` stays clean on a fresh install.

**Severity**: Low (the MCP-server install path has its own pip integrity, and the highest-value tamper surface -- skills, commands, hooks, scripts -- is already covered).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-21`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.10`, section `Open Items`, and original ID `DF-v310-ruflo-P4-extensions`.

- **Migrated from**: v3.11#DF-v310-ruflo-P4-extensions (reason: user-deferred); original `v3.11.0#DF-v310-ruflo-P4-extensions`, section `adoption-spec-kit third cycle (2026-07-08)`.

#### Original source: DF-v310-ruflo-P4-extensions (Low) - `nexus-hub verify` manifest excludes `extensions/` MCP-server sources (their pip install has its own integrity). - MIGRATED to v4.13 (AR-21)

**v4.13.11 structural audit, 2026-10-09**: Converted this historical list obligation into a supported item heading. The complete source line is retained below; prior transfer wording alone does not prove a migration.

**Original list entry**: - **DF-v310-ruflo-P4-extensions** (Low) - `nexus-hub verify` manifest excludes `extensions/` MCP-server sources (their pip install has its own integrity). - MIGRATED to v4.13 (AR-21)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-21`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.11.0`, section `adoption-spec-kit third cycle (2026-07-08)`, and original ID `DF-v310-ruflo-P4-extensions`.

### AR-26: No live macOS installer smoke has been recorded

- **Current state**: every step in the v3.7 `development/mac-smoke-test.md` is still pending; CI covers the tarball bootstrap only.
- **Owner and next step**: installation owner on a macOS host; run `curl | bash` and a `--branch` install and record results. Related to v4.4 HT-2 in the inventory above.
- **Historical transfer note**: v3.0#DF-v30-8 and v3.7, v3.8, v3.9#WN-v37-1 on 2026-09-29 (reason: one obligation recorded four times, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.0#DF-v30-8 (reason: user-deferred); original `v3.0#DF-v30-8`, section `Open Items`.

#### Original source: DF-v30-8 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-8 - MIGRATED to v4.13 (AR-26)

**Category**: DF

**Source phase**: Phase 10

**Plan reference**: T046 (cross-OS installer smoke + live --branch)

**Reason**: Re-deferred. The implementation host is Windows-only (no macOS / Linux host available, verified 2026-06-04), so the full macOS 14 installer smoke (sub-steps 1a-1l of `docs/archive/v2/v2.3/installer-smoke-post.txt`) and the Ubuntu installer-probe + `make eval` could not be run, and the live `--branch <pushed-branch>` clone+install (bash + PowerShell) was not exercised end-to-end. Windows is empirically green this version (full pytest 1160 passed / 4 skipped / 0 failed; ShellCheck 0.11.0 clean on installer.sh / install.sh; all validators + scan + version-sync green) and the Linux Python suite is green via CI (`.github/workflows/ci.yml` on ubuntu-latest). Carries DF-v24-10 (subsumes DF-v24-5; carries DF-v23-6).

**Suggested next step**: Before any packaged-binary release, run sub-steps 1a-1l on a macOS 14 host and the installer-probe/eval portion on an Ubuntu host (record in `docs/<version>/installer-smoke.txt`); while on those hosts, run the live `--branch` clone+install into a throwaway target and confirm the cache dir populates, the re-exec carries `NEXUS_HUB_BRANCH_RESOLVED=1` without re-cloning, the install completes from the cache, and the working copy is untouched.

**Severity**: Low (Windows empirically green; Linux green via CI; deferral acceptable for a source release)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-8`.

- **Migrated from**: v3.7#WN-v37-1 (reason: user-deferred); original `v3.7#WN-v37-1`, section `Open Items`.

#### Original source: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**Category**: WN

**Source phase**: install-ux-overhaul Phase 5

**Plan reference**: 5.1

**Reason**: The real `curl \| bash` one-liner against live GitHub cannot be exercised in CI (CI drives the bootstrap from a local `git archive` tarball with zero network) and cannot be run on the Windows dev host (WN-v36-1). A manual Mac smoke-test checklist is recorded at `docs/v3/v3.7/development/mac-smoke-test.md` with results marked `pending`. Steps 1-3 (install + `nexus-hub --version` + `nexus-hub upgrade` "up to date") also require the v3.7.0 tag to be live on `main` before they exercise the documented one-liner verbatim.

**Suggested next step**: After the v3.7.0 tag is pushed to `main`, run the checklist on a real Mac and record the results table; the new `macos-latest` CI bootstrap job covers the local-tarball path in the meantime.

**Severity**: Low (macOS bash path is auto-verified in CI; only the live-network one-liner is manual, and the bootstrap fetch logic is identical to the tarball path)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.7`, section `Open Items`, and original ID `WN-v37-1`.

- **Migrated from**: v3.8#WN-v37-1 (reason: user-deferred); original `v3.8#WN-v37-1`, section `Open Items`.

#### Original source: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**Category**: WN

**Source**: carried from v3.7.0

**Reason**: The live `curl \| bash` one-liner against GitHub cannot be exercised in CI or on the Windows dev host. The v3.7.0 tag is now live on `main`, so the documented one-liner can finally be exercised verbatim on a real Mac.

**Suggested next step**: Run the recorded macOS smoke-test checklist ([docs/archives/v3/v3.7/development/mac-smoke-test.md](../../../archives/v3/v3.7/development/mac-smoke-test.md)) on a real Mac and record the results.

**Severity**: Low (the macOS bash path is auto-verified in CI; only the live-network one-liner is manual).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.8`, section `Open Items`, and original ID `WN-v37-1`.

- **Migrated from**: v3.9#WN-v37-1 (reason: user-deferred); original `v3.9#WN-v37-1`, section `Open Items`.

#### Original source: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**Category**: WN

**Source**: carried from v3.7.0 / v3.8.0

**Reason**: The live `curl \| bash` one-liner against GitHub cannot be exercised in CI or on the Windows dev host. v3.9.0 made no installer change, so the v3.7.0 smoke-test checklist remains the verification path.

**Suggested next step**: Run the recorded macOS smoke-test checklist ([docs/archives/v3/v3.7/development/mac-smoke-test.md](../../../archives/v3/v3.7/development/mac-smoke-test.md)) on a real Mac if not yet done.

**Severity**: Low (the macOS bash path is auto-verified in CI; only the live-network one-liner is manual; unaffected by v3.9.0).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.9`, section `Open Items`, and original ID `WN-v37-1`.

### AR-30: `configs/` is not distributed to installed trees

- **Current state**: `scripts/lib/integrations/platform_defaults.py` falls back when the source file is absent; AGENTS.md calls the file repo-internal but no decision closes this item.
- **Owner and next step**: maintainer; record "maintainer surface only" by decision, or add a copy step to both installers.
- **Historical transfer note**: v3.16.0#NI-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.16#NI-1-v3160 (reason: user-deferred); original `v3.16.0#NI-1`, section `v3.16.0 - platform-defaults-config`.

#### Original source: NI-1-v3160 - OPEN: `configs/` is not distributed, so some installed trees use the fallback - MIGRATED to v4.13 (AR-30)

- **Source phase**: Phase 1, sub-task 1.3.
- **Reason it is open**: `configs/platform-defaults.json` is a repo-internal source. An installed tree with no bootstrap-materialized checkout under `~/.nexus-hub/src/` finds no candidate and uses the module's hardcoded fallback. The fallback cannot silently rot (the `--check` guard compares it to the declared values), so the values are always correct at ship time; what such a tree loses is the ability to change the default by editing one file locally.
- **Why it was not done in Phase 1**: the fix is an installer copy step, and modifying the installers is ask-first under AGENTS.md. The plan explicitly scopes the installers as untouched so this release adds no `jq` dependency and stays independent of the v3.17.0 `jq` removal.
- **Suggested next step**: decide deliberately in a later cycle whether `configs/platform-defaults.json` should become a distributed artifact. If yes, it needs a copy step in BOTH `scripts/installer.sh` and `scripts/installer.ps1` and a row in the AGENTS.md distribution table. If no, record that end users configure via their own `settings.json` and the source is a maintainer surface only.

**Original source identity**: `v3.16.0#NI-1` in `v3.16.0 - platform-defaults-config`; normalized stable ID `NI-1-v3160` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-30`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.0`, section `v3.16.0 - platform-defaults-config`, and original ID `NI-1`.

### AR-40: Two installer tests fail intermittently in long local runs

- **Current state**: possibly the real-home leak that v4.13.1 BG-2 fixed for `test_selection_parity.py` (commit `ad768ca9`); unproven, and `test_org_cli.py` is not covered by that fix.
- **Owner and next step**: installer/test maintainer; close after v4.13.1 BG-2 is verified in hosted CI and a full local installer run is clean.
- **Historical transfer note**: v3.18.2#BG-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.18#BG-2-v3182 (reason: user-deferred); original `v3.18.2#BG-2`, section `v3.18.2 - github-usage-monitor-withdrawal`.

#### Original source: BG-2-v3182 - OPEN, environment-only: two installer tests fail non-deterministically in long local runs on OneDrive - MIGRATED to v4.13 (AR-40)

- **Observed**: 2026-08-22, post-release, on this Windows working tree (an OneDrive-synced folder). Two separate long local runs each failed **one** test, and **a different one each time**: `tests/installer/test_org_cli.py::test_disconnect_requires_confirmation_and_yes_removes_state_and_cache` (1 failed / 3888 passed, full suite, 60 min) and `tests/installer/test_selection_parity.py::test_powershell_filtered_install_matches_bash` (1 failed / 417 passed, `tests/installer` only, 5 min).
- **Both pass in isolation** (5.1s and 7.1s respectively) and **both pass in CI**: `tests (ubuntu-latest)`, `installer-smoke` on ubuntu / macos / **windows**, and `install-smoke` were all green on the v3.18.2 PRs.
- **Assessment: environment, not product.** The failing assertion in the first is `org connect <git-uri>` returning exit 2 instead of 0 - a shell-out to `git` against a bare-repo fixture. This session independently hit `fatal: unable to write new index file` from `git checkout -b` in this same tree, which is the documented OneDrive file-locking hazard. A different test failing on each run is the signature of contention, not of a deterministic defect.
- **Explicitly NOT evidence of a regression in the v3.18.2 withdrawal.** `test_selection_parity` compares the PowerShell and bash installers, which the withdrawal edited on both sides, so it was the first candidate checked. It passes in isolation and `installer-smoke (windows-latest)` passed in CI, which is the job that exercises the retirement guard on the affected platform.
- **Disposition**: not a release blocker and not tracked as product flakiness. Recorded so the next person who sees a lone installer failure on a OneDrive tree does not spend the investigation again. **A local full-suite run on this tree is not a trustworthy signal**; CI on a clean checkout is. If either test ever fails **in CI**, treat it as a real defect and delete this entry.
- **Related process failure**: the first of these was reported to the user as a passing suite, because the run was piped (`pytest ... | tail`) and the pipeline's exit code is `tail`'s, not `pytest`'s. Never read `$?` through a pipe to judge a test run; capture the exit code directly or use `PIPESTATUS`.
- **New data point 2026-08-22 (v3.18.3 Phase 5), which does NOT close this item**: a full `tests/installer` run on this same OneDrive tree was clean (418 passed, 17 skipped, 0 failed), as was `tests/integrations` (661 passed, 1 skipped). A non-deterministic flake cannot be disproved by one green run, so the entry stays open on its stated terms. Recorded because the absence of a failure is still evidence about frequency, and because the next person needs to know a clean local run has happened rather than assuming the tests always fail here.

**Original source identity**: `v3.18.2#BG-2` in `v3.18.2 - github-usage-monitor-withdrawal`; normalized stable ID `BG-2-v3182` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-40`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.18.2`, section `v3.18.2 - github-usage-monitor-withdrawal`, and original ID `BG-2`.

### Permissions and platform contracts

### AR-16: Permission-matcher behaviors remain unprobed

- **Current state**: output redirection under an explicit allow rule, whether Gemini splits compound commands, and a Gemini PowerShell / `cmd.exe` read-only set are all still UNVERIFIED in the v3.17 `development/permission-matcher-findings.md` and `configs/permissions/gemini-permissions.json`.
- **Owner and next step**: `platform-contract-verification` owner; run the recorded probes against current builds.
- **Historical transfer note**: v3.17.0#NI-1, v3.17.0#NI-2, and v3.17.0#DF-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#NI-1-v3170 (reason: user-deferred); original `v3.17.0#NI-1`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: NI-1-v3170 - OPEN: output redirection under an explicit allow rule is UNVERIFIED - MIGRATED to v4.13 (AR-16)

- **Target file**: [development/permission-matcher-findings.md](../../../archives/v3/v3.17/development/permission-matcher-findings.md) (Finding 2), `scripts/validate_permission_baseline.py` (the `redirect` rule)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Plan reference**: 1.1 required determining empirically "whether Claude Code's matcher treats a redirected command as matching the bare pattern"
- **Reason it is open**: the official permissions documentation demonstrably models redirects, but states it only for the BUILT-IN read-only command set, never for explicit `allow` rules. Redirection operators are also absent from the enumerated command-separator list, so a redirected command is one subcommand rather than two, and a wildcard "matches any sequence of characters including spaces". Per this plan's evidence discipline, absence of a statement is recorded as UNVERIFIED rather than as absence of the behavior.
- **Why it is load-bearing**: `> file` truncates its target regardless of what the command emits (`Write-Host x > f` writes nothing to the file and still truncates it). If the native matcher admits redirects under allow rules, then EVERY baseline pattern carrying a trailing wildcard is a file-destruction primitive, and no per-entry rescoping repairs that. This is a global property of the matcher, not a defect of any individual entry, which is why Phase 1.1 did not attempt to fix it per-entry.
- **Suggested next step**: run the empirical probe named in Finding 2 against a throwaway project and a current Claude Code build: add one `Bash(echo *)` allow rule and observe whether `echo x > /tmp/probe` prompts. Phase 4 verified hook independence but did not execute this separate native-matcher probe, so the evidence remains UNVERIFIED.

**Original source identity**: `v3.17.0#NI-1` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `NI-1-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-16`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `NI-1`.

- **Migrated from**: v3.17#NI-2-v3170 (reason: user-deferred); original `v3.17.0#NI-2`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: NI-2-v3170 - OPEN: whether Gemini's matcher splits compound commands at all - MIGRATED to v4.13 (AR-16)

- **Target file**: `configs/permissions/gemini-permissions.json`, [development/permission-matcher-findings.md](../../../archives/v3/v3.17/development/permission-matcher-findings.md) (Finding 1)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Reason it is open**: Finding 1 VERIFIED compound-command splitting for Claude Code, quoted from its documentation, for both the Bash and the PowerShell matcher. No equivalent statement was located for Gemini's `run_shell_command`, and the file's own shipped comment records the opposite direction ("piped commands bypass allowlists (upstream issue)"). Gemini entries are therefore treated as PREFIX matches with no separator awareness, which is the conservative reading and is what `validate_permission_baseline.py` implements via its `prefix` match mode.
- **Why it matters**: under prefix semantics with no splitting, `run_shell_command(git status)` would admit `git status; rm -rf .`. The validator's conservative mode does not make that safe; it only stops Nexus-Hub from shipping patterns that depend on splitting.
- **Suggested next step**: run a dedicated Gemini CLI matcher probe and record a MATCH, DRIFT, or UNVERIFIED verdict beside the permission findings. Phase 2 verified autonomy levers, not compound-command matcher semantics. If splitting is absent, harden the Gemini baseline under prefix-without-splitting assumptions before expanding its Windows-shell coverage.

**Original source identity**: `v3.17.0#NI-2` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `NI-2-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-16`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `NI-2`.

- **Migrated from**: v3.17#DF-1-v3170 (reason: user-deferred); original `v3.17.0#DF-1`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-1-v3170 - OPEN: `gemini-permissions.json` ships no PowerShell or `cmd.exe` read-only set - MIGRATED to v4.13 (AR-16)

- **Target file**: `configs/permissions/gemini-permissions.json`, `docs/permissions-research.md`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1 (observation only, by instruction)
- **Plan reference**: 1.1 explicitly forbids adding one ("this sub-task rescopes existing entries and deliberately does not expand coverage") and hands the observation to sub-task 5.3
- **Reason it is open**: a Windows Gemini user receives a POSIX-shaped allowlist plus a bare `run_shell_command(dir)`, so their real shell is effectively uncovered. Expanding coverage is a different risk decision from rescoping and belongs with the platform-coverage work.
- **Suggested next step**: `docs/permissions-research.md` now documents the gap. Resolve NI-2 before designing a PowerShell or general `cmd.exe` baseline, because the safe pattern shape depends on whether the matcher splits compound commands.

**Original source identity**: `v3.17.0#DF-1` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `DF-1-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-16`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-1`.

### AR-17: Permission distribution covers few platforms and scopes

- **Current state**: only Claude is wired at workspace scope; `Install-Nexus-Hub-Permissions.ps1` has no cross-platform equivalent; `configs/permissions/` covers 4 of 16 integrations.
- **Owner and next step**: installer maintainer; research Gemini and Codex project paths, decide Copilot `.vscode/settings.json`, and add a `nexus-hub` permissions command.
- **Historical transfer note**: v3.17.0#DF-2, v3.17.0#DF-3, and v3.17.0#DF-5 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#DF-2-v3170 (reason: user-deferred); original `v3.17.0#DF-2`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-2-v3170 - OPEN: three of four platforms have no project-scoped permission target - MIGRATED to v4.13 (AR-17)

- **Target file**: `scripts/installer.sh` and `scripts/installer.ps1` (`install_permissions` / `Install-Permissions`, workspace branch)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2
- **Reason it is open**: workspace scope is now wired and load-bearing, but only Claude Code has a confirmed target (`.claude/settings.local.json`). The other three skip WITH A NOTE, each for a stated reason: **Gemini** and **Codex** have no project-scoped permission path documented well enough to write, and a guessed path is worse than none because it reads as configured; **Copilot**'s only surface is `.vscode/settings.json`, which is commit-visible and therefore forbidden here without an explicit maintainer decision (the same reasoning that made the v3.11.0 Copilot `.github/skills/` surface opt-in).
- **Suggested next step**: run a permission-path-specific contract sweep for Gemini and Codex; the Phase 2 autonomy sweep answered a different question. The Copilot half needs a maintainer decision about writing to a commit-visible file, not more research.

**Original source identity**: `v3.17.0#DF-2` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `DF-2-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-17`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-2`.

- **Migrated from**: v3.17#DF-3-v3170 (reason: user-deferred); original `v3.17.0#DF-3`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-3-v3170 - OPEN: `Install-Nexus-Hub-Permissions.ps1` still has no cross-platform equivalent - MIGRATED to v4.13 (AR-17)

- **Target file**: `scripts/Install-Nexus-Hub-Permissions.ps1`, `scripts/nexus_hub_cli.py`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2 (deferred by that sub-task's own instruction)
- **Reason it is open**: that helper provides install, uninstall, and backup-repair paths for all four platforms and has no bash sibling, so POSIX users have no equivalent repair route. Sub-task 1.2 forbids porting it to bash, and correctly: a second shell script would recreate exactly the dual-implementation drift this phase removed.
- **Suggested next step**: expose install / uninstall / repair through the cross-platform `nexus-hub` CLI, whose `scripts/nexus_hub_cli.py` now includes the Phase 5 `autonomy` subcommand. One implementation, three operating systems. Phase 5 shipped autonomy only, so this separate lifecycle gap carries forward.

**Original source identity**: `v3.17.0#DF-3` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `DF-3-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-17`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-3`.

- **Migrated from**: v3.17#DF-5 (reason: user-deferred); original `v3.17.0#DF-5`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-5 - OPEN by design: the read-only baseline covers only four of 16 integrations - MIGRATED to v4.13 (AR-17)

- **Target files**: `configs/permissions/`, `scripts/installer.sh`, `scripts/installer.ps1`, `docs/permissions-research.md`
- **Source phase**: v3.17.0 Phase 6 reconciliation of the Phase 1 and Phase 2 coverage boundaries
- **Disposition**: deliberate non-delivery. Claude Code, Codex, Gemini, and Copilot receive the existing baseline. Aider, Antigravity 1.0, Antigravity 2.0, Cursor, Gemini CLI, Hermes, Kimi, Nexus-AI, OpenClaw, OpenCode, Qwen, and Windsurf receive no Nexus-Hub read-only baseline.
- **Why it remains open**: autonomy coverage and read-only allowlist coverage are independent. This release widened the former and deliberately did not invent permission matchers for platforms whose safe read-only contracts were not researched.
- **Suggested next step**: handle one platform at a time through a permission-contract research and validator cycle. Do not infer baseline safety from the existence of an autonomy descriptor.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-17`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-5`.

### AR-36: Unverified platform read-path residuals

- **Current state**: Antigravity CLI agent/workflow directories, Cursor global commands, and the Gemini Code Assist skill directory are still residuals in `docs/policy/platform-read-contracts.md`. The Antigravity part is also tracked as v4.3 WN-3 and v4.12 DF-1 above.
- **Owner and next step**: platform-contract owner; resolve at the next authenticated read-back.
- **Historical transfer note**: v3.11#DF-1 (D5, D7), v3.12.1#DF-v3121-agy-cli-workflows, and v3.12.1#DF-v3121-gemini-ide-skill-dir on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

**Current residual from `v4.3.0#WN-3`**: Obtain authenticated Antigravity CLI custom-agent/workflow and Cursor command read-backs. Qualify Gemini Code Assist IDE surfaces beyond GEMINI.md. Resolve Nexus-AI project mirrors and remaining optional mirrors independently of the already source-qualified global skill reader. Retain a separate dated retirement clause/link for Antigravity legacy workflows rather than implying immediate deletion.

**Partial disposition**: Keep 2026-09-24 shared Antigravity global/workspace hook reference and Nexus-AI global-reader source qualification as historical partial closures. The 2026-09-27 unauthenticated Antigravity empty roster was inconclusive; Cursor 3.21.18 lacked the required command UI read-back.

- **Migrated from**: v3.11#DF-1 (reason: user-deferred); original `v3.11.0#DF-1`, section `v3.11.0`.

#### Original source: DF-1 - Residual live-verification gaps (external platform contracts) - MIGRATED to v4.13 (AR-01)

- **Source phase**: Phase 7 (7.1 audit, residual gaps D1-D7)
- **Plan reference**: `docs/v3/v3.11/platform-read-contracts.md` (Residual live-verification gaps)
- **Reason**: These contracts depend on the current external platform's behavior and cannot be confirmed from the repo alone. The 7.4 `verify` and 7.5 CI smoke now REPORT/CATCH the resulting surfacing gaps, but the underlying external contracts still want a live probe.
- **Suggested next step**: Live-probe per platform: Codex prompt read path + format (D1) and skills discovery (D2); Antigravity 2.0 root-vs-`.agents/` instruction file (D3), exact global subpath (D4), `subagents`/`rules` consumption (D5), `.agents` vs `.agent` (D6); Cursor/Copilot global slash surfaces (D7); and whether `nexus-hub init` (the launcher) passes the `init` subcommand through (the on-open hook calls it fail-open). Feed results back into codex.py / antigravity.py.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.11.0`, section `v3.11.0`, and original ID `DF-1`.

- **Migrated from**: v3.12#DF-v3121-agy-cli-workflows (reason: user-deferred); original `v3.12.1#DF-v3121-agy-cli-workflows`, section `v3.12.1`.

#### Original source: DF-v3121-agy-cli-workflows - MIGRATED to v4.13 (AR-36)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v3121-agy-cli-workflows - MIGRATED to v4.13 (AR-36)

**Source**: Phase 3 (Antigravity)

**Reason**: The `agy` CLI global SKILLS path is confirmed (`~/.gemini/antigravity-cli/skills/`); the CLI global WORKFLOW dir is undocumented and written best-effort. IDE global slash works via `~/.gemini/config/global_workflows/`.

**Severity**: Low

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.1`, section `v3.12.1`, and original ID `DF-v3121-agy-cli-workflows`.

- **Migrated from**: v3.12#DF-v3121-gemini-ide-skill-dir (reason: user-deferred); original `v3.12.1#DF-v3121-gemini-ide-skill-dir`, section `v3.12.1`.

#### Original source: DF-v3121-gemini-ide-skill-dir - MIGRATED to v4.13 (AR-36)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v3121-gemini-ide-skill-dir - MIGRATED to v4.13 (AR-36)

**Source**: Phase 4 (sweep)

**Reason**: `~/.gemini/skills` flattening is confirmed for Gemini CLI; the Gemini IDE (Code Assist) skill dir is applied on weight-of-evidence. The SKILL_INDEX in GEMINI.md covers Code Assist regardless.

**Severity**: Low

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.1`, section `v3.12.1`, and original ID `DF-v3121-gemini-ide-skill-dir`.

- **Migrated from**: v4.3#WN-3 (reason: user-deferred); original `v4.3.0#WN-3`, section `v4.3.0 - agentic-verification-discipline`.

#### Original source: WN-3 - Optional platform surfaces remain unverified

- **Source phase**: Phase 5 platform-contract verification
- **Plan reference**: `docs/archives/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T023
- **Evidence**: The current official audit did not prove Antigravity CLI loose workflow or hook destinations, Cursor legacy command directories, Gemini IDE surfaces beyond `GEMINI.md`, or Nexus AI read paths. The coupled bundle removes or avoids those claims instead of guessing.
- **Impact**: Verified platform destinations continue to install, while these optional surfaces are deliberately absent or marked `UNVERIFIED`; users do not receive a false discovery guarantee.
- **Owner**: Platform integration maintainer.
- **Next step**: Recheck each surface against dated official documentation or a live-host artifact before adding a destination, default, or verification gate.

**Targeted source recheck, 2026-09-24**: [Google's current hook reference](https://antigravity.google/docs/hooks?tab=cli) confirms that Antigravity CLI reads the shared global `~/.gemini/config/hooks.json` and workspace `.agents/hooks.json`; the existing adapter already emits both, and a global-install dry-run assertion now protects that path. [Nexus-AI source at `198ff9c8`](https://github.com/bendourthe/Nexus-AI/blob/198ff9c877f258c775092761e3c67a6bed56b1d2/desktop/sidecar/src/skills/hubSkillReader.ts) qualifies its global `~/.nexus-ai/catalog/skills` reader. The [archived bounded recheck](../../../archives/v4/v4.3/development/optional-platform-surface-recheck.md) keeps CLI loose workflows and agents, Cursor legacy command directories, Gemini Code Assist IDE add-on surfaces, and Nexus-AI's project-local mirror and other mirrored surfaces unverified. WN-3 remains open; no live Antigravity or Nexus-AI host behavior was claimed.

**Targeted source recheck, 2026-09-26**: [Current Google CLI and migration documentation](../../../archives/v4/v4.3/development/optional-platform-surface-recheck-2026-09-26.md) now source-qualifies the shared Antigravity custom-agent and legacy-workflow destinations already emitted by the adapter, but the latter retires on November 1, 2026. Cursor's global command path has a vendor-reported discovery bug, Gemini Code Assist's IDE custom commands and rules use IDE settings rather than a documented CLI-file mirror, and Nexus-AI's project-local mirror still lacks a read-path proof. WN-3 remains open for those live-host and project-local questions; this addendum does not convert source evidence into a runtime pass.

**Local host read-back attempt, 2026-09-27**: Installed Antigravity CLI 1.2.12 exposes `agy agents`, but it printed no agents from either this checkout or a disposable workspace containing a documented `.agents/agents/nexus-probe/agent.md`; the empty list is inconclusive without an authenticated interactive read-back. The interactive CLI reported that this host was not signed in and rejected the existing `agentMode: "default"` setting before opening an agent session; no settings were changed. Installed Cursor 3.21.18 exposes no agent-discovery list in `cursor --help`, and its UI read-back was not exercised. WN-3 remains open for authenticated Antigravity and Cursor observations, the dated workflow-retirement decision, Gemini Code Assist IDE behavior, and Nexus-AI's project-local mirror. The disposable agent fixture was removed after the test.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.3.0`, section `v4.3.0 - agentic-verification-discipline`, and original ID `WN-3`.

### AR-38: No invocation-policy lever on five platforms

- **Current state**: `docs/policy/skill-invocation-policy-levers.md` still documents none for Antigravity, OpenCode, Kimi, Hermes, and Nexus-AI.
- **Owner and next step**: platform-contract owner; re-check each release and close when a first-party vendor document names a field.
- **Historical transfer note**: v3.20.3#DF-1 on 2026-09-29 (reason: vendor-dependent, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.20#DF-1-v3203 (reason: user-deferred); original `v3.20.3#DF-1`, section `v3.20.3`.

#### Original source: DF-1-v3203 - No native invocation mapping for platforms with no vendor lever - MIGRATED to v4.13 (AR-38)

- **Source phase**: Phase 4 - Invocation-policy metadata
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md` (sub-task 4.1)
- **Reason**: Antigravity, OpenCode, Kimi, Hermes, and Nexus-AI document no per-skill invocation-policy field. Generated command-skills still carry `disable-model-invocation: true` in SKILL.md; those hosts ignore the unknown key. Inventing a sidecar would repeat the v3.15.0 fabricated-companion failure.
- **Suggested next step**: Revisit when a first-party vendor document names a lever. Until then keep the honest gap note in `docs/policy/skill-invocation-policy-levers.md`.

**Original source identity**: `v3.20.3#DF-1` in `v3.20.3`; normalized stable ID `DF-1-v3203` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-38`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.20.3`, section `v3.20.3`, and original ID `DF-1`.

### AR-45: Completion notification is undelivered or unverified on Qwen, Gemini CLI, and Kimi

- **Current state**: `docs/policy/platform-read-contracts.json` records Qwen and Gemini as expressible but undelivered and does not list Kimi's events. The shared Stop-hook registration may reach those platforms without `_notify_common` shipping there.
- **Owner and next step**: installer/platform maintainer; deliver or explicitly exclude trigger B, confirm the shared module ships, and enumerate Kimi's events.
- **Historical transfer note**: v3.15.10#DF-14 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-14 (reason: user-deferred); original `v3.15.10#DF-14`, section `v3.15.10 - end-of-task-agent-behavior`.

#### Original source: DF-14 - Completion notification trigger B remains undelivered or unverified on three platforms

- **DF-14 - trigger B deferred on four platforms.** Qwen (`Stop`, verified) and Gemini CLI (`AfterAgent`, verified) each need a writer for their own `settings.json` layout plus a test surface; Gemini CLI is additionally enterprise-only opt-in, making it the lowest-value target. Codex (`Stop` likely) and Kimi have event sets that reachable first-party docs never enumerate, so nothing was delivered for them. Deferring is the honest output of a verification-gated phase. - MIGRATED to v4.13 (AR-45)

**Normalization, 2026-10-09 (v4.13.11 T006)**: Converted the authoritative bullet to a supported gap heading. The complete original source paragraph is retained above. The residual belongs to AR-45; the canonical copy must be verified before a parsed forward-migration marker is added. The v3.15.11 follow-up removes Codex from this residual after delivery; Qwen, Gemini CLI, and Kimi retain the unperformed or unverified trigger-B obligation.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-45`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.10`, section `v3.15.10 - end-of-task-agent-behavior`, and original ID `DF-14`.

### AR-47: The legacy Cursor global commands write is unverified and redundant

- **Current state**: `scripts/lib/integrations/cursor.py` still writes both command directories and labels the global one UNVERIFIED.
- **Owner and next step**: installer maintainer; confirm at the next Cursor contract pass, then remove the redundant write with a test.
- **Historical transfer note**: v3.15.0#DF-1(a) and v3.15.10#DF-17 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-17 (reason: user-deferred); original `v3.15.10#DF-17`, section `v3.15.10 - end-of-task-agent-behavior`.

#### Original source: DF-17 - Legacy Cursor global commands write remains unverified

- **DF-17 - DF-1 commands residual.** The global `~/.cursor/commands` write is now documented as redundant (Cursor no longer documents a commands directory, Cursor 2.4 migrates commands into skills, and Nexus-Hub already ships each command as a command-skill). Retained deliberately because the risk is asymmetric: writing a directory Cursor ignores is harmless, removing one it does read silently drops coverage. Remove deliberately in a later release. - MIGRATED to v4.13 (AR-47)

**Normalization, 2026-10-09 (v4.13.11 T006)**: Converted the authoritative bullet to a supported gap heading. The complete original source paragraph is retained above. The residual belongs to AR-47; the canonical copy must be verified before a parsed forward-migration marker is added.


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-47`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.10`, section `v3.15.10 - end-of-task-agent-behavior`, and original ID `DF-17`.

- **Migrated from**: v3.15#DF-1-v3150 (reason: user-deferred); original `v3.15.0#DF-1`, section `v3.15.0 - platform-parity-all-gaps`.

#### Original source: DF-1-v3150 - Cursor global commands path UNVERIFIED (residual; hooks.json schema RESOLVED in Phase 2) - MIGRATED to v4.13 (AR-47)

- **Source phase**: v3.15.0 Phase 1.2; actioned in Phase 2 (2026-07-21)
- **Plan reference**: Phase 2 (Cursor parity - skills, hooks.json, agents, project commands)
- **Status**: PARTIALLY RESOLVED. **DF-1(b) hooks.json schema - RESOLVED**: [cursor.com/docs/hooks](https://cursor.com/docs/hooks) confirms `{version:1, hooks:{<event>:[{...}]}}` with the optional fields defaulted, so the integration's minimal `beforeShellExecution -> {command}` writer is schema-valid as-is (no code change). **DF-1(a) global `~/.cursor/commands/` - RESIDUAL (still UNVERIFIED)**: project `.cursor/commands/<name>.md` is officially documented (Cursor 1.6+) and confirmed, but the user-global `~/.cursor/commands/` dir has no reachable official doc and [forum.cursor.com](https://forum.cursor.com/t/personal-custom-slash-commands/133386) reports it as an open feature-request.
- **Decision**: the global write is RETAINED per plan sub-task 2.3 and the contract's negative-only-evidence caution; it is harmless if unread.
- **Suggested next step**: a future cycle with a reachable Cursor commands doc (or an empirical test) should confirm or drop the global `~/.cursor/commands/` write. Not blocking - the confirmed project `.cursor/commands/` surface is the load-bearing path.

**Original source identity**: `v3.15.0#DF-1` in `v3.15.0 - platform-parity-all-gaps`; normalized stable ID `DF-1-v3150` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-47`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.0`, section `v3.15.0 - platform-parity-all-gaps`, and original ID `DF-1`.

### AR-51: OpenCode writes a `rules` folder the read contract does not record

- **Current state**: `scripts/lib/integrations/opencode.py` sets `rules_subdir`.
- **Owner and next step**: platform-contract owner; review against the OpenCode rules documentation and keep or drop.
- **Historical transfer note**: v3.15.0 (OpenCode `rules_subdir` residual) on 2026-09-29 (reason: still open).

### AR-54: The strict Claude permissions overlay has no `defaultMode` decision

- **Current state**: `configs/permissions/claude-permissions-strict.json` omits `defaultMode`, pending enum verification that was never closed.
- **Owner and next step**: permissions owner; decide, then add or document the omission with a test.
- **Historical transfer note**: v3.15.6#DF-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-3-v3156 (reason: user-deferred); original `v3.15.6#DF-3`, section `v3.15.6 - adoption-sandbox-escapes`.

#### Original source: DF-3-v3156 - `defaultMode` deliberately omitted from the strict overlay pending enum verification - MIGRATED to v4.13 (AR-54)

- **Source phase**: v3.15.6 Phase 3.1.
- **Plan reference**: Phase 3.1 ("with `defaultMode` set to ask/deny rather than auto-approve").
- **Reason**: the instruction is not implementable as written (`ask` and `deny` are sibling array keys, not `defaultMode` values), and the key's valid value set is unverified in this repo: it appears nowhere in `guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md`, and `docs/v3/v3.16/plans/v3.17.0-agent-autonomy-toggle.md` Phase 2 schedules confirming it against official documentation. Writing an unverified enum into a user's `settings.json` risks breaking their config for no benefit, because the safest documented value (`default`) is already Claude Code's behavior. The overlay ships the verified `deny` and `ask` keys instead, and a test pins the omission so it cannot drift back in accidentally.
- **Suggested next step**: after v3.17.0 Phase 2 verifies the `defaultMode` enum against official docs, decide whether the strict overlay should also set it. If yes, add it plus a test; if no, keep the omission and record the reasoning there. Non-blocking: the deny/ask entries deliver the hardening on their own.

**Original source identity**: `v3.15.6#DF-3` in `v3.15.6 - adoption-sandbox-escapes`; normalized stable ID `DF-3-v3156` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-54`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.6`, section `v3.15.6 - adoption-sandbox-escapes`, and original ID `DF-3`.

### AR-56: Upstream-blocked hook surfaces

- **Current state**: the Gemini CLI extension-packaged hook path is unused, and Kimi has no project-scoped hook path.
- **Owner and next step**: platform-contract owner; re-check vendor docs at the next pass.
- **Historical transfer note**: v3.15.8#DF-12 and v3.15.8#DF-13 on 2026-09-29 (reason: vendor-dependent, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-12 (reason: user-deferred); original `v3.15.8#DF-12`, section `v3.15.8`.

#### Original source: DF-12 - Gemini CLI extension-packaged hooks are a cleaner write path left unused - MIGRATED to v4.13 (AR-56)

- **Source phase**: v3.15.8 Phase 6.1 - Map Gemini CLI Hooks.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 6.1).
- **Reason**: the [extension reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md) documents extensions as a fourth hook-precedence layer, reading `~/.gemini/extensions/<name>/hooks/hooks.json` with `${extensionPath}` and `${/}` substitution. That would give Nexus-Hub a fully-owned directory instead of a merge into the user's main config, and would solve the absolute-path and path-separator problems outright. It is not used because the reference documents only `gemini extensions install` for populating that directory, so writing it directly would be an inferred write path of exactly the kind sub-task 6.1 says to record rather than ship; it also has no project scope, where half of this phase's delivery lives. The maintainer chose settings.json now with this recorded as a follow-on.
- **Suggested next step**: if a later release can verify that a directly-written extension directory is loaded (or can shell out to `gemini extensions install` against a local path), migrate global-scope hooks there and keep the settings.json merge for workspace scope.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-56`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `DF-12`.

- **Migrated from**: v3.15#DF-13 (reason: user-deferred); original `v3.15.8#DF-13`, section `v3.15.8`.

#### Original source: DF-13 - Kimi has no project-scoped hook path, so workspace hooks are undeliverable - MIGRATED to v4.13 (AR-56)

- **Source phase**: v3.15.8 Phase 7.2 - Merge Kimi TOML Hooks.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 7.2).
- **Reason**: the matrix assumed a project `.kimi-code/config.toml`. That file does not exist -- Kimi's project-local configuration is `.kimi-code/local.toml`, which the [configuration reference](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/config-files) documents as holding only a `[workspace]` table with `additional_dir`, and `[[hooks]]` is documented exclusively in the user-level `~/.kimi-code/config.toml`. Sub-task 7.2 says to reject undocumented paths, so the workspace hook row stays finding-only with the reason recorded in the row itself rather than shipping an invented destination. The practical impact is bounded: hooks installed at global scope apply to every project, so a user loses per-project hook scoping, not the guardrails.
- **Suggested next step**: if Kimi later documents project-scoped hooks (in `local.toml` or elsewhere), deliver them through the same marker-block merge, which is scope-agnostic already.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-56`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `DF-13`.

### AR-57: Agent and hook delivery never observed on real Codex, Gemini CLI, Qwen, and Kimi installs

- **Current state**: the v3.15.8 consolidated live pass has no recorded result.
- **Owner and next step**: maintainer on a host with those tools; one live pass recorded in the read-contract verification block.
- **Historical transfer note**: v3.15.8#MT-6, v3.15.8#MT-7, and v3.15.8#MT-8 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#MT-6 (reason: user-deferred); original `v3.15.8#MT-6`, section `v3.15.8`.

#### Original source: MT-6 - Codex agent and hook delivery is not observed against a real Codex install - MIGRATED to v4.13 (AR-57)

- **Source phase**: v3.15.8 Phase 5.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 5.3).
- **Reason**: the suite proves the TOML schema, the merge algebra, ownership, idempotence, cross-shell parity, and teardown against a temporary filesystem, and the read contract asserts the surfaces exist after an install. What no test can prove from here is that a running Codex build loads the emitted TOML as an agent and fires the merged hooks, because that needs an authorized Codex session on a host that has the product installed.
- **Suggested next step**: fold a manual Codex load check into the same release-readiness pass that owns the other live verifications, then record the observed result in the read-contract verification block.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-57`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `MT-6`.

- **Migrated from**: v3.15#MT-7 (reason: user-deferred); original `v3.15.8#MT-7`, section `v3.15.8`.

#### Original source: MT-7 - Windows shell dispatch for these two platforms is asserted, not observed - MIGRATED to v4.13 (AR-57)

- **Source phase**: v3.15.8 Phase 6.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 6.3).
- **Reason**: the host-aware branch is fully tested in both directions, and CI runs the suite on a Windows runner, so what gets *written* on Windows is proven. What is not proven is which shell each CLI actually launches the command with. The workspace-scope command references `$env:GEMINI_PROJECT_DIR` / `$env:QWEN_PROJECT_DIR` in PowerShell syntax; if a Windows build dispatches through `cmd.exe` instead, the variable stays literal and the hook fails to find its script. Neither platform's documentation states the Windows shell, and the failure mode is bounded: Gemini CLI's exit-code contract makes any non-zero exit other than 2 a warning that lets the interaction proceed, so a wrong guess degrades to a warning rather than a block.
- **Suggested next step**: during release readiness, run one project-scope hook on a Windows host with each CLI installed and record the observed shell in the read contract; if it is `cmd.exe`, switch the workspace reference to `%VAR%` form behind the same host check.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-57`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `MT-7`.

- **Migrated from**: v3.15#MT-8 (reason: user-deferred); original `v3.15.8#MT-8`, section `v3.15.8`.

#### Original source: MT-8 - Kimi agent and hook delivery is not observed against a real Kimi install - MIGRATED to v4.13 (AR-57)

- **Source phase**: v3.15.8 Phase 7.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 7.3).
- **Reason**: the suite proves the verbatim copy, the four-field schema, comment and table preservation, rollback, duplicate suppression, host-selected commands, and teardown against a temporary filesystem, and CI runs it on Windows. What no test here can prove is that a running Kimi build lists the copied agents alongside its built-ins and fires the spliced hooks. This is the same boundary as MT-6 for Codex and MT-7 for the Gemini-CLI-class platforms.
- **Suggested next step**: fold a Kimi load check into the same release-readiness pass that owns MT-6 and MT-7, confirming `/hooks` lists the block's entries and the agents appear in Kimi's agent list.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-57`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `MT-8`.

### Catalog, validators, and tests

### AR-04: The skill-description eval harness builds CLI flags that do not exist

- **Current state**: `scripts/optimize_skill_description.py` still adds `--skill` and `--prompt` (verified 2026-09-29), so live trigger runs and technique checks cannot run through it. `scripts/run_trigger_pilot.py` has a working `stream-json` path.
- **Owner and next step**: eval-pipeline owner; port the pilot's invocation, then run the recorded live checks.
- **Historical transfer note**: v3.0#BG-v30-1, v3.0#DF-v30-6, and v3.0#DF-v30-7 on 2026-09-29 (reason: live defect, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.0#DF-v30-6 (reason: user-deferred); original `v3.0#DF-v30-6`, section `Open Items`.

#### Original source: DF-v30-6 - MIGRATED to v4.13 (AR-04)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-6 - MIGRATED to v4.13 (AR-04)

**Category**: DF

**Source phase**: Phase 10

**Plan reference**: T045 (live skill-eval-loop)

**Reason**: Re-deferred. A model CLI IS on PATH this version (`claude` + `codex`), so the prior "no CLI" reason no longer holds -- but a faithful with-skill-vs-baseline trigger run is still not achievable: the bundled harness (`scripts/optimize_skill_description.py`) builds `claude -p ... --skill <path>` / `codex exec ... --prompt <path>`, and both flags are rejected by the shipped CLIs (`error: unknown option '--skill'`; `codex exec` has no `--prompt`). After patching detection to the real CLI surface (install the skill into a temp `.claude/skills/`, run headless `claude -p --output-format stream-json`, parse the stream for a `Skill` tool_use), 3 live runs (haiku positive, sonnet positive, sonnet fenced-negative) for `agent-orchestration-primitives` showed the skill is discoverable and the `Skill` tool is available, yet neither model invoked it on a dead-on-topic prompt -- because in a Nexus-Hub environment the real trigger path is the `search_skills` MCP (per the global skill-discovery instruction), not the bare `Skill` tool, and a capable model answers an advisory prompt directly. Carries DF-v24-8 (subsumes DF-v24-1/2/3/4/6, carries DF-v23-7) for: `agent-orchestration-primitives`, `skill-security-scan`, `verification-before-completion`, `receiving-code-review`, `using-git-worktrees`, `solution-knowledge-base`, `solution-refresh`, `multi-agent-code-review`, `plan-review`, `product-strategy`, `session-query`, `product-pulse`, `demo-capture`. Static trigger-surface checks (verbatim trigger phrases + SKIP clauses + cross-fencing) already done at authoring for all.

**Suggested next step**: A faithful live eval requires replicating the `search_skills` MCP discovery path: wire `nexus-skill-server` into each nested run (no `--strict-mcp-config`) and detect trigger via the `search_skills` call plus the subsequent `Skill` load -- tracked by BG-v30-1. Pick up once BG-v30-1 fixes the harness; author a minimal `evals.json` per skill and confirm 1.0 positive / 0.0 fenced-negative.

**Severity**: Low (static surface verified; live confirmation blocked on BG-v30-1)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-04`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-6`.

- **Migrated from**: v3.0#DF-v30-7 (reason: user-deferred); original `v3.0#DF-v30-7`, section `Open Items`.

#### Original source: DF-v30-7 - MIGRATED to v4.13 (AR-04)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-7 - MIGRATED to v4.13 (AR-04)

**Category**: DF

**Source phase**: Phase 10

**Plan reference**: T045 (eval-harness trigger techniques)

**Reason**: Re-deferred for the same root cause as DF-v30-6. The three eval-harness trigger techniques (premature-action detection, multi-turn replay, cheap-model fragility) in `scripts/optimize_skill_description.py` cannot be exercised live because the harness's `build_cli_command` targets the non-existent `--skill` / `--prompt` flags. They remain validated at v2.3.0 via dry-run + pure-logic + fixture-stream tests (+23 pytest cases in `catalog/hooks/tests/test_eval_loop.py`, still green). The one live observation this phase: cheap-model fragility is real -- haiku did not load the skill on the positive prompt (consistent with what technique 3 is designed to surface). Carries DF-v24-9 (carries DF-v23-8).

**Suggested next step**: Fold into the same live-eval pass as DF-v30-6 once BG-v30-1 fixes the harness invocation: confirm `premature_action` flips on a planted pre-`Skill` tool use, a multi-turn eval triggers at its `trigger_turn`, and a description's trigger rate is compared across default and a cheaper `--model`.

**Severity**: Low (logic-tested; live confirmation blocked on BG-v30-1)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-04`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-7`.

- **Migrated from**: v3.0#BG-v30-1 (reason: user-deferred); original `v3.0#BG-v30-1`, section `Open Items`.

#### Original source: BG-v30-1 - MIGRATED to v4.13 (AR-04)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: BG-v30-1 - MIGRATED to v4.13 (AR-04)

**Category**: BG

**Source phase**: Phase 10

**Plan reference**: T045 (live evals; harness defect found)

**Reason**: Shipped catalog tooling constructs a CLI command the shipped CLI rejects. `scripts/optimize_skill_description.py::build_cli_command` builds `claude -p <prompt> --skill <path>`, `codex exec <prompt> --prompt <path>`, `gemini --workflow <prompt> --skill-file <path>`, and `opencode run <prompt> --skill <path>` -- but the installed Claude Code CLI returns `error: unknown option '--skill'` and `codex exec` has no `--prompt` flag (verified 2026-06-04). The harness was authored against an aspirational future "skill-load flag" surface (its own docstring says "Real CLIs will eventually surface a structured `skill_loaded` flag; until then this heuristic..."). The parity test (`catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter`) only asserts no cross-CLI binary bleed, so it never caught that the flags do not exist. Discovered while running T045 live.

**Suggested next step**: Patch `build_cli_command` (and `_detect_trigger`) to the real per-CLI surface: for `claude`, drop `--skill`, install the target skill into a temp project `.claude/skills/<name>/`, run from that cwd with `--output-format stream-json --verbose`, optionally wire `nexus-skill-server` via `--mcp-config` (no `--strict-mcp-config`) to exercise the real `search_skills` discovery path, and detect trigger from a `search_skills`/`Skill` tool_use in the stream rather than the description-phrase-echo heuristic. Update the parity test to assert each branch uses a flag the CLI actually accepts. Then DF-v30-6/-7 become runnable.

**Severity**: Medium (the bundled eval harness cannot perform a live run against any shipped CLI as written)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-04`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `BG-v30-1`.

**Tracking alias retained**: `v4.13.9#WN-24`; the following complete historical source has the same current obligation and is not a separate future task.

##### Tracking source: v4.13.9#WN-24 (v4.13.9): The skill-eval-loop Claude adapter command no longer matches the installed CLI

- **Source phase**: Phase 5. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T319 and T321.
- **Reason**: `catalog/skills/workflow/skill-eval-loop/references/cli-adapter.md` documents the Claude runner as `claude -p "<prompt>" --setting-sources "" --model <model> --skill <path/to/SKILL.md>` (verified 2026-09-21), and `scripts/optimize_skill_description.py` builds that command. Claude Code 2.1.283's `--help` (checked 2026-09-30) documents no `--skill` option. The pilot used `--append-system-prompt-file` instead, without changing the shared adapter. The same CLI also reports `claude-sonnet-5-5` as an unrecognized model (see DF-4).
- **Suggested next step**: owner `skill-eval-loop`. Re-verify the Claude runner against the current official Claude Code CLI reference. If `--skill` is gone, choose and document the replacement (for example `--bare` with `--append-system-prompt-file`, or `--add-dir` with skill resolution), update the adapter and the optimizer's command builder together, and keep `TestEvalLoopCLIAdapter` parity green.

- **Carried from**: v4.13.8#WN-4 on 2026-10-02

### AR-06: The 250-character description cap conflicts with the trigger-rich description rule

- **Current state**: `scripts/validate_skills.py` `DESCRIPTION_MAX_CHARS = 250`; many descriptions exceed it by design, and `--allow-existing` fails. Related to v4.8 WN-1.
- **Owner and next step**: catalog maintainer; decide the cap (for example the 1024 agentskills.io limit) or the allowlist, then gate CI on it.
- **Historical transfer note**: v3.1#WN-v31cr-1, v3.2#WN-v32-1, and v3.14.2#WN-1 on 2026-09-29 (reason: one obligation recorded three times, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.1#WN-v31cr-1 (reason: user-deferred); original `v3.1#WN-v31cr-1`, section `Open Items`.

#### Original source: WN-v31cr-1 - MIGRATED to v4.13 (AR-06)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v31cr-1 - MIGRATED to v4.13 (AR-06)

**Category**: WN

**Source phase**: claude-red Phase 1 (extended Phase 3, Phase 4)

**Plan reference**: T004 (validate the new skills); T007/T008/T010 (enriched skills)

**Reason**: `scripts/validate_skills.py` run with no flags (its default mode) reports description-length "errors" (description > 250 characters) across the catalog, including all five security skills the claude-red plan touched: the Phase 1 new skills (`ai-attack-patterns`, `pentest-reporting`), the Phase 3 enriched skills (`advanced-attack-patterns`, `business-logic-abuse`), and the Phase 4 enriched skill (`authentication-patterns`, now 732 chars), whose pushy descriptions gained trigger phrases + a `SKIP` clause. This is NOT a gate: `make validate` and the CI `validate` job run only `validate_skills.py --bundles-only` and `--quality` (both PASS), never the bare default; the strict `--allow-existing` path demotes the violation to a warning for files in `scripts/validate_skills.allowlist.json`, to which `authentication-patterns/SKILL.md` was added (mirroring the Phase 3 skills). The 250-char cap directly conflicts with the AGENTS.md mandatory pushy-description rule (which "trades 6 words for 60" with trigger phrases + a SKIP clause), and every shipped security skill already exceeds it (e.g. `skill-security-scan` at ~600 chars). The long descriptions are intentional and norm-consistent.

**Suggested next step**: Do not shorten the pushy descriptions to chase the default-mode cap. If the divergence is undesirable, reconcile `validate_skills.py` default-mode behavior with the pushy-description rule (raise/remove the 250-char cap or scope it to a non-`description` field) so the script does not contradict the authoring contract. Out of scope for this plan.

**Severity**: Low (not a CI/`make validate` gate; by-design per the authoring contract)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-06`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.1`, section `Open Items`, and original ID `WN-v31cr-1`.

- **Migrated from**: v3.2#WN-v32-1 (reason: user-deferred); original `v3.2#WN-v32-1`, section `Open Items`.

#### Original source: WN-v32-1 - MIGRATED to v4.13 (AR-06)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v32-1 - MIGRATED to v4.13 (AR-06)

**Category**: WN

**Source phase**: Phase 1 (grown in Phase 2)

**Plan reference**: T001 (write the core skill); T002 (register); T004 (teaching-mode trigger phrases)

**Reason**: `scripts/validate_skills.py` run with no flags (its default mode) reports a description-length error (description > 250 characters) for `session-teach-back` (923 chars after Phase 2's T004 added 2 more verbatim teaching-mode trigger phrases; 828 chars at Phase 1), whose pushy `description` carries 7 verbatim trigger phrases + a 3-way SKIP clause as the plan's T001/T004 mandate. This is NOT a gate: `make validate` and the CI `validate` job run only `validate_skills.py --bundles-only` and `--quality` (both PASS), never the bare default; the strict `--allow-existing` path demotes the violation to a warning for files in `scripts/validate_skills.allowlist.json`, to which `session-teach-back/SKILL.md` was added (mirroring its sibling `session-query` and the two most-recent skills, `skill-security-scan` and `agent-orchestration-primitives`). The 250-char cap directly conflicts with the AGENTS.md mandatory pushy-description rule and the plan's explicit T001 requirement. The long description is intentional and norm-consistent. (Same root class as v3.1.0 WN-v31cr-1; note that a few other catalog skills -- e.g. `ai-attack-patterns`, `pentest-reporting`, `git-branching-workflow` -- carry pushy descriptions not yet in the allowlist on `develop`, a separate pre-existing item, not introduced here.)

**Suggested next step**: Do not shorten the pushy description to chase the default-mode cap. If the divergence is undesirable catalog-wide, reconcile `validate_skills.py` default-mode behavior with the pushy-description rule (raise/remove the 250-char cap or scope it to a non-`description` field). Out of scope for this plan.

**Severity**: Low (not a CI/`make validate` gate; by-design per the authoring contract)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-06`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `WN-v32-1`.

- **Migrated from**: v3.14#WN-1-v3142 (reason: user-deferred); original `v3.14.2#WN-1`, section `v3.14.2`.

#### Original source: WN-1-v3142 - Pre-existing: 8 recent skills fail the strict `validate_skills.py` description-length check and are not allowlisted - MIGRATED to v4.13 (AR-06)

- **Source phase**: Phase 1 (1.3b, CI wiring); pre-existing on the branch, NOT introduced by this phase
- **Plan reference**: sub-task 1.3 ("Create or update the CI job so `python scripts/validate_skills.py` runs ... with a path filter")
- **Reason**: The strict `python scripts/validate_skills.py` enforces a 250-char single-line `description` budget. 165 skills exceed it; 157 are grandfathered via `scripts/validate_skills.allowlist.json` under `--allow-existing`, but 8 recent v3.x skills are neither trimmed nor allowlisted, so even `--allow-existing` fails with 8 errors: `implementation-convergence`, `review-trapdoors`, `analyze-codebase`, `label-gated-agent-pipelines`, `setup-project`, `document-to-interactive-html`, `implement-phase`, `platform-contract-verification`. None is the skill this phase edited (`cross-project-comparison` validates clean in strict mode). To avoid a red-on-arrival CI gate over pre-existing drift outside this phase's scope, the new CI step runs `--bundles-only` (the same mode `make validate` uses), which passes catalog-wide (0 errors). This is a warning, not a blocker: the AGENTS.md "pushy description" guidance and the 250-char cap are in tension, so the cap itself may warrant review.
- **Suggested next step**: In a dedicated cleanup (a separate patch), either top up `scripts/validate_skills.allowlist.json` with the 8 offenders (or trim them via `scripts/optimize_skill_description.py`), then upgrade the CI step from `--bundles-only` to the stricter `--allow-existing` so genuinely new frontmatter/description/secret violations are caught per-PR. Separately, reconcile the 250-char cap with the AGENTS.md long-description guidance.
- **Phase 4 disposition**: kept OPEN as a deferred follow-up. It is pre-existing, out of scope for the comparison-versioning fix, and NOT a release-blocker (CI is green on `--bundles-only`). Deliberately not fixed in v3.14.2, to avoid touching 8 unrelated skills or padding the grandfathering allowlist for them inside a focused patch; carried forward for a dedicated skills.json / description-cap cleanup (see also the Advisory above, same root).

**Original source identity**: `v3.14.2#WN-1` in `v3.14.2`; normalized stable ID `WN-1-v3142` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-06`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.2`, section `v3.14.2`, and original ID `WN-1`.

### AR-07: Many SKILL.md bodies exceed the 500-line target

- **Current state**: 68 of 338 exceed 500 lines including frontmatter on 2026-09-29 (for example observability-setup and multi-agent-coordinator).
- **Owner and next step**: catalog maintainer; move long sections into `references/` whenever a skill is next edited.
- **Historical transfer note**: v3.16.2#NI-2 and v3.20.1#WN-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.20#WN-2 (reason: user-deferred); original `v3.20.1#WN-2`, section `v3.20.1`.

#### Original source: WN-2 - Sixty-five SKILL.md bodies still exceed the 500-line warning tier - MIGRATED to v4.13 (AR-07)

- **Source phase**: Phase 3 - Size-norm remediation; recounted Phase 5
- **Plan reference**: same plan, Phase 3 (plan cited 107; live count after relocation is 65; none exceed the 800-line hard cap)
- **Reason**: The 800-line cap is an error; 500 is a grandfathered warning. Relocating the remaining 65 would be a separate docs-structure pass, not this plan's content expansion.
- **Suggested next step**: Relocate long-tail sections of the longest bodies into `references/` the next time those skills are substantially edited. Do not bulk-rewrite 65 skills in a patch.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-07`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.20.1`, section `v3.20.1`, and original ID `WN-2`.

- **Migrated from**: v3.16#NI-2-v3162 (reason: user-deferred); original `v3.16.2#NI-2`, section `v3.16.2 - loop-longevity-and-doctor-preflight`.

#### Original source: NI-2-v3162 - OPEN (pre-existing, surfaced in Phase 4): two edited skills are over the 500-line body target - MIGRATED to v4.13 (AR-07)

- **Target files**: `catalog/skills/infrastructure/observability-setup/SKILL.md` (763 lines), `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` (703 lines)
- **What is wrong, and what is not**: both were already over the 500-line target before this phase (742 and 685), so they are grandfathered under the AGENTS.md rule that the norm is forward-looking. Both remain under the 800-line hard cap. Phase 4.5's instruction to "confirm both edited skills stayed within the 500-line body target" therefore describes a check that could not pass, and the honest report is that the target was already exceeded rather than that the check passed.
- **Why the additions were made in the body anyway**: each of the two doctrine items is a short rule that belongs where the reader already is. Pushing a 25-line rule into a `references/` file to protect a line count would trade discoverability for a number, which is the opposite of what the norm exists to achieve.
- **Watch item**: `observability-setup` at 763 lines is within 37 lines of the hard cap. The next cycle that adds to it should split it into `references/` first rather than discovering the cap mid-edit.
- **Suggested next step**: Phase 6.1's refactor pass should decide whether to split `observability-setup`, which is the natural place for that call.

**Original source identity**: `v3.16.2#NI-2` in `v3.16.2 - loop-longevity-and-doctor-preflight`; normalized stable ID `NI-2-v3162` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-07`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.2`, section `v3.16.2 - loop-longevity-and-doctor-preflight`, and original ID `NI-2`.

### AR-08: Missing direct tests

- **Current state**: no test covers `validate_frontmatter_strict_yaml`, `detect-platform.sh` / `enumerate-models.sh`, `benchmark --update-baseline`, the `nexus-hub map` dispatch, or the model-prompting `DEFAULT_GUARDS` suite end to end.
- **Owner and next step**: owners of each surface; add one focused test per item.
- **Historical transfer note**: v3.4#DF-v34-1 (residual), v3.14.3#MT-1, v3.15.1#MT-1, v3.15.1#MT-2, and v3.15.5#MT-4 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

**Current residual from `v1.1#MT-001`**: Add a deterministic fake claude binary on PATH, run the optimizer for one iteration through run_iteration/invoke_cli, and assert iteration-1.json shape plus best_description chosen by test_trigger_rate. Exercise candidate generation and trigger detection at the subprocess boundary; stubbing scorer Python functions is insufficient.

**Partial disposition**: Retain open. Independent of AR04 real-provider eval-harness validity.

- **Migrated from**: v1.1#MT-001 (reason: user-deferred); original `v1.1#MT-001`, section `Open Items`.

#### Original source: MT-001 -- Real-CLI integration test for the optimizer is not exercised in CI

**Source phase**: Phase 5, sub-task 5.4 (description optimizer pytest coverage).
**Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../../archives/v1/v1.1/plans/adoption-skills.md) lines 367-374 (sub-task 5.4).
**Reason**: The pytest module `catalog/hooks/tests/test_eval_loop.py` covers three things in the optimizer: (a) the CLI-adapter parity invariant (per-CLI source-inspection across the four supported CLIs); (b) the dry-run schema (output shape, deterministic split under fixed seed, no-CLI-invocation under empty PATH); (c) the aggregator and viewer end-to-end on a fixture iteration directory. What the suite does NOT cover is a full optimizer run with a stub CLI binary on PATH. The dry-run gate exercises the train/test-split + prompt-template + selection-rule logic without calling out; the parity test exercises the dispatch surface; but `run_iteration()` -- the function that calls `invoke_cli` repeatedly to estimate trigger rates and then asks the CLI to PROPOSE candidates -- has no equivalent of the v1.1.3 hooks' "stub binary on PATH" smoke test. Adding such a stub would require a fake CLI that responds with deterministic JSON arrays of candidate strings, which is feasible but was not in scope for Phase 5's narrow A6/A7 goal.
**Suggested next step**: Add a new test class `TestOptimizerWithStubCLI` to `catalog/hooks/tests/test_eval_loop.py` that creates a fake `claude` binary on PATH (modeled on `test_diff_review_hooks.py::_make_stub_cli`) which returns `["candidate-1", "candidate-2", "candidate-3"]` for the candidate-generation prompt and an empty string for trigger-detection probes, then runs the optimizer for 1 iteration and asserts that `optimizer/iteration-1.json` has the right shape and that `best_description` was selected by `test_trigger_rate`. Out of scope for v1.1.5 if Phase 7 ships before this can be added; otherwise pick it up before v1.2.0 bump.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-08`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v1.1`, section `Open Items`, and original ID `MT-001`.

- **Migrated from**: v3.14#MT-1-v3143 (reason: user-deferred); original `v3.14.3#MT-1`, section `v3.14.3`.

#### Original source: MT-1-v3143 - No dedicated automated regression test for the new strict-YAML gate - MIGRATED to v4.13 (AR-08)

- **Source phase**: Phase 0 (0.3 validator gate)
- **Plan reference**: sub-task 0.3 ("Confirm the gate fails on a deliberately-broken fixture")
- **Reason**: The strict-YAML gate was validated by a manual broken-fixture run (fails as expected) and is effectively covered in CI by the existing `validate_skills.py --bundles-only` run against the real catalog (a reintroduced unquoted `description` would fail it). There is no dedicated unit test asserting the gate's behavior in isolation.
- **Suggested next step**: add a small `tests/validators/` regression test that feeds a broken and a good frontmatter block through `validate_frontmatter_strict_yaml`; low priority given the CI coverage.

**Original source identity**: `v3.14.3#MT-1` in `v3.14.3`; normalized stable ID `MT-1-v3143` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-08`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.3`, section `v3.14.3`, and original ID `MT-1`.

- **Migrated from**: v3.15#MT-2-v3151 (reason: user-deferred); original `v3.15.1#MT-2`, section `v3.15.1 - adoption-codesight`.

#### Original source: MT-2-v3151 - Benchmark `--update-baseline` write path not automated-tested - MIGRATED to v4.13 (AR-08)

- **Source phase**: v3.15.1 adoption-codesight Phase 5 (5.1)
- **Reason**: `measured_baseline()` is unit-tested, but the `benchmark --update-baseline` CLI branch that OVERWRITES the committed `benchmark_baseline.json` is deliberately not exercised (a test that ran it would clobber the committed baseline). The gate path (`--check`), JSON/report output, and `--repo` mode are all tested.
- **Suggested next step**: if desired, test `--update-baseline` against a monkeypatched `BASELINE_PATH` pointing at a temp file. Low value.

**Original source identity**: `v3.15.1#MT-2` in `v3.15.1 - adoption-codesight`; normalized stable ID `MT-2-v3151` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-08`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.1`, section `v3.15.1 - adoption-codesight`, and original ID `MT-2`.

- **Migrated from**: v3.15#MT-1-v3151 (reason: user-deferred); original `v3.15.1#MT-1`, section `v3.15.1 - adoption-codesight`.

#### Original source: MT-1-v3151 - Repo-level `nexus-hub map` dispatch has no automated test - MIGRATED to v4.13 (AR-08)

- **Source phase**: v3.15.1 adoption-codesight Phase 1 (1.2)
- **Reason**: the extension test suite fully covers the map surface (generator, model, tokens, the `generate_context_map` MCP handler, and `nexus_code_search.contextmap.cli`; tool-vs-CLI byte-identity is asserted). The thin dispatch in `scripts/nexus_hub_cli.py` (a 3-line verbatim forward) is verified only by a manual smoke run, not an automated repo-level test.
- **Suggested next step**: add a small repo-level dispatch test asserting `nexus_hub_cli.main(["map", ...])` forwards and returns the extension CLI's exit code.

**Original source identity**: `v3.15.1#MT-1` in `v3.15.1 - adoption-codesight`; normalized stable ID `MT-1-v3151` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-08`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.1`, section `v3.15.1 - adoption-codesight`, and original ID `MT-1`.

- **Migrated from**: v3.15#MT-4 (reason: user-deferred); original `v3.15.5#MT-4`, section `v3.15.5 - model-prompting-research`.

#### Original source: MT-4 - the apply loop's DEFAULT guard suite is not exercised end to end; tests inject fake guards - MIGRATED to v4.13 (AR-08)

- **Source phase**: v3.15.5 Phase 3.4.
- **Plan reference**: Phase 3.2 ("run the full guard suite") and 3.4 ("the per-edit guard loop with an injected guard failure").
- **Reason**: the loop's control flow (apply, guard, keep-or-revert, quarantine, continue) is fully tested with injected pass/fail guards, which is what keeps the tests fast and deterministic. Running the real five-gate suite once per edit takes minutes, so no test executes `DEFAULT_GUARDS` end to end. **The realistic half of this gap was closed in-phase**: `test_every_default_guard_points_at_a_script_that_exists` asserts each default guard names a `.py` script that is actually present, and `test_the_default_suite_covers_the_gates_the_plan_requires` pins the three gates the plan names. A renamed or moved gate now fails at test time instead of quarantining every edit on a live run.
- **Suggested next step**: what remains is a genuine end-to-end run of the real suite (one slow-marked test applying a trivial edit under `DEFAULT_GUARDS`). Phase 6.3 is the natural home. Non-blocking, and the failure direction is safe: a broken guard quarantines edits rather than letting them through.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-08`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.5`, section `v3.15.5 - model-prompting-research`, and original ID `MT-4`.

### AR-09: Most skills lack trigger-case evals

- **Current state**: 88 of 338 skills have `evals/trigger-cases.json`. Related to v4.13.0 WN-3.
- **Owner and next step**: catalog maintainer; add cases as skills are rewritten.
- **Historical transfer note**: v3.15.2#MT-1 and v3.20.1#MT-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.20#MT-1 (reason: user-deferred); original `v3.20.1#MT-1`, section `v3.20.1`.

#### Original source: MT-1 - Most catalog skills still lack `evals/trigger-cases.json` - MIGRATED to v4.13 (AR-09)

- **Source phase**: Phase 4 / Phase 5
- **Plan reference**: same plan, sub-task 4.3 (evals are optional; missing is WARN, never FAIL)
- **Reason**: 55 of 315 skills ship trigger cases (the 40 new security skills plus 15 pre-existing). The remaining 260 are uncovered. The gate is incremental by contract.
- **Suggested next step**: Add trigger cases when a skill is next rewritten, prioritizing dual-use and high-traffic routing collisions.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-09`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.20.1`, section `v3.20.1`, and original ID `MT-1`.

- **Migrated from**: v3.15#MT-1-v3152 (reason: user-deferred); original `v3.15.2#MT-1`, section `v3.15.2 - adoption-awesome-llm-apps`.

#### Original source: MT-1-v3152 - trigger-cases.json routing coverage is a first tranche (6/267 skills) - MIGRATED to v4.13 (AR-09)

- **Source phase**: v3.15.2 Phase 3.3.
- **Plan reference**: Phase 3.3 ("leave the rest of the catalog on the WARN path for incremental authoring in later releases") and Phase 6.2 ("Explicitly record the deferred incremental work ... skills still on the WARN path").
- **Reason**: routing cases were authored for 6 distinctive-noun skills; the remaining 261 skills have no `evals/trigger-cases.json` and are on the WARN path (never fails the gate). This is by design - lexical routing cases are only meaningful for skills with distinctive description vocabulary, and command-dispatcher skills (`/plan`, `/implement`, `/review`, `/compare`, `/update`) lexically overlap their sub-skills, so they need `lexical: false` reasoning-routed cases (deferred).
- **Suggested next step**: author further tranches incrementally in later releases; for the command dispatchers, add `lexical: false` cases covered by behavioral evals (ties into Phase 4 schema interop).

**Original source identity**: `v3.15.2#MT-1` in `v3.15.2 - adoption-awesome-llm-apps`; normalized stable ID `MT-1-v3152` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-09`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.2`, section `v3.15.2 - adoption-awesome-llm-apps`, and original ID `MT-1`.

### AR-12: loop-engineering lacks a re-entrancy guard and schema assertions

- **Current state**: no nested-invocation guard, no optional context-compression cross-link, and the gate-type table parity and `ship-pr-until-green` duplicate-block check are still unasserted (partial coverage in `tests/validators/test_loop_engineering_bundle.py`).
- **Owner and next step**: loop-engineering maintainer.
- **Historical transfer note**: v3.16#CD-1, v3.16#CD-3, and v3.16.2#MT-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.16#CD-1 (reason: user-deferred); original `v3.16#CD-1`, section `Comparison-Sourced Deferrals`.

#### Original source: CD-1 - nested-invocation (re-entrancy) guard for loop-engineering - MIGRATED to v4.13 (AR-12)

- **Source**: no-mistakes delta comparison, candidate M1 (upstream `v1.41.2` #567 "prevent recursive validation runs", plus the `NO_MISTAKES_GATE` environment marker and `nested_gate_context` error observed in the upstream agent skill).
- **Target**: `catalog/skills/workflow/loop-engineering/SKILL.md`, alongside the existing `iteration_cap`, exit-signal protocol, and stall/fault-detection material.
- **Reason**: `loop-engineering` bounds a loop's iterations but says nothing about a loop running *inside itself*. Iteration caps apply per level, so they do not bound the recursion: an agent operating inside a bounded loop or verification gate that triggers the same loop again can multiply its own budget without tripping any cap. A catalog-wide search found no re-entrancy or nested-invocation language in any skill body.
- **Suggested next step**: add a re-entrancy rule stating that an agent must detect it is already inside an instance of this loop or gate (via an environment marker set by the outer invocation) and refuse the inner instance rather than proceeding, reporting the nesting instead. State the cap-does-not-bound-recursion failure mode explicitly. Cross-link `[[ai-billing-safeguards]]` (nesting is a budget-multiplication path) and `[[using-git-worktrees]]` (isolation does not imply non-re-entrancy). **Phrase it as a guard against unintended re-entrancy into the same instance, NOT as a prohibition on depth**: deliberate nesting (a workflow spawning subagents that themselves loop) is legitimate, so cross-link `[[agent-orchestration-primitives]]` so fan-out is not discouraged. Per the reverse-engineering attribution rule, do not name the external project in the skill body; add the provenance row to `docs/policy/mcp-reverse-engineering-matrix.md` if the fold lands. Non-blocking; nothing is broken today.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-12`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16`, section `Comparison-Sourced Deferrals`, and original ID `CD-1`.

- **Migrated from**: v3.16#CD-3 (reason: user-deferred); original `v3.16#CD-3`, section `Comparison-Sourced Deferrals`.

#### Original source: CD-3 - repair-loop prompt-size cross-link (optional, lowest priority) - MIGRATED to v4.13 (AR-12)

- **Source**: no-mistakes delta comparison, candidate M3 (upstream `v1.40.2` #526 "handle oversized Claude repair prompts").
- **Target**: `catalog/skills/workflow/loop-engineering/SKILL.md`, cross-linking `[[context-compression]]` and `[[prompt-token-optimization]]`.
- **Reason**: a bounded repair loop can fail on accumulated prompt size before it reaches its iteration cap, as findings and fix history pile up across rounds. All three relevant skills exist; nothing connects them at this failure mode.
- **Suggested next step**: a one-line cross-link noting the failure mode and that inter-round compaction is the mitigation. Marked optional: drop this entry if the ledger is being trimmed. Non-blocking.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-12`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16`, section `Comparison-Sourced Deferrals`, and original ID `CD-3`.

- **Migrated from**: v3.16#MT-1-v3162 (reason: user-deferred); original `v3.16.2#MT-1`, section `v3.16.2 - loop-longevity-and-doctor-preflight`.

#### Original source: MT-1-v3162 - OPEN: the three new schema concepts carry no mechanical assertion - MIGRATED to v4.13 (AR-12)

- **Target files**: `catalog/skills/workflow/loop-engineering/references/loop-schema.md`, `catalog/skills/workflow/loop-engineering/references/loop-library.md`
- **What is missing**: `gates`, `evidence_freshness`, and the Instance State section are prose in a Tier-3 reference file. `validate_skills.py` audits bundle references and orphans, not reference-file content, and `run_trigger_evals.py` scores routing rather than schema shape. Nothing fails today if a later edit deletes a Fields-table row, renames a gate type, or lets the worked example drift out of step with the library entry. The drift risk is now concrete rather than hypothetical: the identical `gates` block for `ship-pr-until-green` exists in **two** files, because the schema's worked example and the library entry are the same loop.
- **Why it was not done in Phase 1**: the phase's Stability Gate is documentation-scoped, and the plan routes all test construction to Phase 5, which is where this cycle's pytest surface is created. Building a one-off test module here would have put a test directory in front of the phase that must name it in `ci.yml` (v3.15.8 QG-2).
- **Suggested next step**: when Phase 5 adds its test module, add two cheap assertions alongside it - that the four gate types in the Fields table match those in the Human-Judgment Gates table, and that the `ship-pr-until-green` `gates` block is byte-identical in `loop-schema.md` and `loop-library.md`.

**Original source identity**: `v3.16.2#MT-1` in `v3.16.2 - loop-longevity-and-doctor-preflight`; normalized stable ID `MT-1-v3162` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-12`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.2`, section `v3.16.2 - loop-longevity-and-doctor-preflight`, and original ID `MT-1`.

### AR-13: egress-redaction covers only the egress boundary

- **Current state**: local persistence and error surfaces are out of scope in the skill.
- **Owner and next step**: security skills owner; extend the scope.
- **Historical transfer note**: v3.16#CD-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.16#CD-2 (reason: user-deferred); original `v3.16#CD-2`, section `Comparison-Sourced Deferrals`.

#### Original source: CD-2 - extend egress-redaction beyond the egress boundary - MIGRATED to v4.13 (AR-13)

- **Source**: no-mistakes delta comparison, candidate M2 (upstream `v1.40.3` #469 "redact embedded credentials from stored upstream URLs and error surfaces").
- **Target**: `catalog/skills/security/egress-redaction/SKILL.md`, whose scope is currently stated as detecting credentials "in a prompt, file, or generated output before it leaves the host" (line 17).
- **Reason**: the skill is framed on a single boundary, egress. A credential embedded in a persisted remote URL (the `scheme://user:token@host/path` form, routinely written by clone and remote-add flows) or leaked into an error message, stack trace, or log line never crosses an egress boundary, yet still lands in plaintext on local disk. The data class and verdict already exist (Credentials are classified BLOCK at lines 57 and 89); only the boundary list is too narrow.
- **Suggested next step**: add two boundaries to the same existing policy. First, **local persistence**: redact before writing a credential into stored configuration or state, naming the embedded-credential URL form as the canonical example. Second, **error surfaces**: redact before a credential reaches an error message, stack trace, or log. State why this is a distinct gap (neither is an egress boundary, so an egress-framed skill does not cover them). **Do not add a parallel policy table** duplicating the data classes or the BLOCK verdict, which would create two sources of truth for one classification. Attribution and matrix handling as in CD-1. Non-blocking.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-13`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16`, section `Comparison-Sourced Deferrals`, and original ID `CD-2`.

### AR-14: The spec template's A1 example phrases a Non-Goal as an Assumption

- **Current state**: `catalog/templates/spec-template.md` A1 is unchanged.
- **Owner and next step**: next spec-template edit; rewrite A1 and move the scope clause to Non-Goals.
- **Historical transfer note**: v3.16#TR-1 (originally v3.15.14#NI-2) on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.16#TR-1 (reason: user-deferred); original `v3.16#TR-1`, section `Transferred in from v3.15.14 (spec-driven-development cycle)`.

#### Original source: TR-1 - OPEN: the `A1` example in `spec-template.md` phrases a Non-Goal as an Assumption - MIGRATED to v4.13 (AR-14)

- **Target file**: `catalog/templates/spec-template.md` (the `A1` bullet under `## Assumptions`)
- **Reason it is open**: `A1` reads "Authentication uses the existing session-cookie middleware; JWT is out of scope for this feature". The second clause is a Non-Goal under the boundary the new `## Non-Goals` authoring note defines, not an Assumption. The v3.15.14 plan instructed Phase 1.1 to leave `A1`'s text alone and instead document the boundary, which is what shipped: the Non-Goals note now names `A1` explicitly as the illustration of getting it wrong.
- **Suggested next step**: rewrite `A1` into a clean Assumption (keep the session-cookie default, drop the scope clause) and move the scope clause into the Non-Goals example, which already carries a reason. Roughly a two-line edit. Whichever cycle next touches the spec template should absorb it.
- **Why it was not done in v3.15.14**: teaching the distinction and then silently fixing the example would have removed the worked illustration the note points at. Fixing it is correct once the note has been read by real authors; doing both in one release removes the evidence.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-14`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16`, section `Transferred in from v3.15.14 (spec-driven-development cycle)`, and original ID `TR-1`.

### AR-15: v3.11 spec-kit items S5, S6, and S8 carry no status claim

- **Current state**: no later record states their status; S8's functional half is AR-01.
- **Owner and next step**: next spec-kit delta pass; re-verify and record.
- **Historical transfer note**: v3.16#TR-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.16#TR-2 (reason: user-deferred); original `v3.16#TR-2`, section `Transferred in from v3.15.14 (spec-driven-development cycle)`.

#### Original source: TR-2 - OPEN: v3.11.0 spec-kit items S5, S6, and S8 carry no status claim - MIGRATED to v4.13 (AR-15)

- **Target**: the v3.11.0 spec-kit adoption ledger
- **Reason it is open**: the v3.15.14 comparison was article-scoped, not a repository-delta pass against `github/spec-kit`, so S5, S6, and S8 were never re-examined. The honest position is that they carry **no status claim** from this cycle rather than an implied "still open" or "now closed".
- **Suggested next step**: a future repository-delta comparison against `github/spec-kit` should re-verify all three explicitly and record a verdict per item. Do not infer their state from the v3.15.14 cycle, which did not look.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-15`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16`, section `Transferred in from v3.15.14 (spec-driven-development cycle)`, and original ID `TR-2`.

### AR-22: `make build-catalog` would overwrite hand-curated registry files

- **Current state**: `build_skills_catalog.py` is unchanged since v2.0.0 and the target still exists, while hand-editing checked by `check_registry_entries.py --check --strict` is the convention.
- **Owner and next step**: catalog maintainer; remove or guard the target and its AGENTS.md mention.
- **Historical transfer note**: v3.0#WN-v30-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.0#WN-v30-2 (reason: user-deferred); original `v3.0#WN-v30-2`, section `Open Items`.

#### Original source: WN-v30-2 - MIGRATED to v4.13 (AR-22)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v30-2 - MIGRATED to v4.13 (AR-22)

**Category**: WN

**Source phase**: Phase 2

**Plan reference**: T008 (register both skills)

**Reason**: The T008 prompt prescribed regenerating `data/skills.json` + `data/SKILL_INDEX.md` via `infrastructure/tools/build_skills_catalog.py`. Running the generator produced a ~5,500-line diff that materially rewrote existing entries: it splits categories by raw frontmatter casing (e.g. `Developer Experience` vs `developer-experience`, `Research`, `Workflow`), recomputes `long_description`/`size` differently, and reorders entries -- indicating the committed `data/` files are maintained by a newer/different process than this generator. To keep the diff traceable, registration was done by hand (2 skill entries + recomputed `statistics` + 2 `SKILL_INDEX.md` rows + the `orchestration`/`security` `marketplace.json` counts), and the regeneration was reverted. Net effect: `make build-catalog` is currently unsafe to run -- it would clobber curated catalog data.

**Suggested next step**: Reconcile `build_skills_catalog.py` with the committed `data/skills.json` (normalize category casing in source SKILL.md frontmatter, align `long_description`/`size`/ordering, and category counting) so `make build-catalog` reproduces the committed catalog with a no-op diff; OR document that `data/` is hand-maintained and retire/replace the generator. Verify with a no-op regen diff.

**Severity**: Medium (a future `make build-catalog` or `/update` run could corrupt the catalog)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-22`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `WN-v30-2`.

### AR-23: The hook rewrite field `updatedInput` is undocumented

- **Current state**: no mention in `guides/`.
- **Owner and next step**: docs owner; document it in the settings reference.
- **Historical transfer note**: v3.2#WN-v32hr-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.2#WN-v32hr-1 (reason: user-deferred); original `v3.2#WN-v32hr-1`, section `Open Items`.

#### Original source: WN-v32hr-1 - MIGRATED to v4.13 (AR-23)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v32hr-1 - MIGRATED to v4.13 (AR-23)

**Category**: WN

**Source phase**: adoption-headroom Phase 4

**Plan reference**: T012 (hook)

**Reason**: The PreToolUse hook rewrites the Bash command via `hookSpecificOutput.updatedInput`, but the repo's authoritative `guides/CLAUDE_CODE_SETTINGS_REFERENCE.md` documents only the exit-code hook contract (0/2/other), not a command/input-rewrite mechanism. If a Claude Code version does not honor `updatedInput`, the hook is a safe no-op (the original command runs unmodified -- the emitted JSON is simply ignored). The hook is also opt-in/default-off (`NEXUS_CONTEXT_COMPRESS=1`) and jq-gated, so it never acts unless explicitly enabled. The pytest suite verifies the hook's transformation *logic* (emitted JSON shape), not live Claude honoring of it.

**Suggested next step**: If Claude Code's `updatedInput` support is confirmed/denied, note it in the settings reference; if denied, switch the integration to whatever output-rewrite mechanism the installed version supports (or rely on the Windows-style CLAUDE.md-instruction path on all platforms).

**Severity**: Low (fail-safe: no-op when unsupported; opt-in; output never lost)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-23`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `WN-v32hr-1`.

### AR-28: Retired slash-command names remain in skill bodies

- **Current state**: 134 mentions such as `/generate-plan` and `/tasks-to-issues`.
- **Owner and next step**: catalog maintainer; one modernization sweep.
- **Historical transfer note**: v3.2#DF-v32cmd-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.2#DF-v32cmd-1 (reason: user-deferred); original `v3.2#DF-v32cmd-1`, section `Open Items`.

#### Original source: DF-v32cmd-1 - MIGRATED to v4.13 (AR-28)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32cmd-1 - MIGRATED to v4.13 (AR-28)

**Category**: DF

**Source phase**: v3.2.0 deprecated-command removal

**Plan reference**: shim cull (post-Phase-7)

**Reason**: After deleting the 40 deprecated command shims, the hard breakages were all fixed (the installer smoke test, every dangling `catalog/commands/<old>.md` file/link reference, the installer/base.py/new-feature old-command MENTIONS, and the `using-nexus-hub` onboarding command table). A residual remains: ~134 old-command slash *mentions* in ~25 catalog skill bodies + style-guides still name removed commands (e.g. `implementation-plan`, `known-gaps-tracker`, `project-refactor`, `spec-driven-development`, `cross-artifact-analyzer`, `tasks-to-issues`, `project-constitution`, `pr-description-writer`, `deep-research-compilation`, `idea-refine`, `business-logic-abuse`, `advanced-attack-patterns`, `test-strategy-doc`, `cross-project-comparison`, `docx-generation`, `mcp-builder`, `docs-layout-refactor`, plus the `commands-cheatsheet` / `markdown` style-guides and the `tasks-to-issues` helper scripts -- naming `/generate-plan`, `/refactor-project`, `/analyze-spec`, `/run-penetration-test`, etc.). These are stale prose, not broken commands: no test, slash menu, or file link is affected (all fixed), and many sit in the retained skills the consolidated commands delegate to. The slash-menu noise that motivated the removal is fully resolved.

**Suggested next step**: Run a dedicated command-reference modernization sweep mapping each old `/name` to its consolidated form per `docs/v3/v3.0/command-migration.md`, handling retained-skill self-references and step-number pointers with care; ship as a non-breaking v3.2.1 patch or a develop commit.

**Severity**: Low (prose-only staleness; menu noise resolved, hard breakages fixed)


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-28`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32cmd-1`.

### AR-33: Subprocess-driven validator tests have no coverage measurement

- **Current state**: no coverage configuration or `COVERAGE_PROCESS_START` anywhere.
- **Owner and next step**: CI/test infrastructure owner; add subprocess coverage plumbing and a threshold.
- **Historical transfer note**: v3.15.5#MT-2 and v3.17.6#MT-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#MT-2-v3176 (reason: user-deferred); original `v3.17.6#MT-2`, section `v3.17.6 - ci-gate-and-branch-hygiene`.

#### Original source: MT-2-v3176 - DEFERRED to its own version (2026-08-21): the repository has no coverage instrumentation - MIGRATED to v4.13 (AR-33)

- **Target files**: `tests/validators/conftest.py`
- **What it is**: every validator test invokes its script as a subprocess, deliberately, so the test exercises the CLI a maintainer runs. `coverage` therefore records nothing without `--parallel-mode` plus a `COVERAGE_PROCESS_START` shim, and the repository defines no threshold, `[tool.coverage]` section, or `--cov` flag anywhere.
- **How the gate was satisfied**: 90% on `check_required_check_coverage.py`, measured with a one-off out-of-tree in-process probe replaying the suite's own fixtures. The probe is scratch tooling and deliberately NOT committed, since committing it would create a second, divergent way to exercise the same code.
- **Suggested next step**: if a future version wants an enforced number, the change belongs in `conftest.py` and CI once, for all validators, not per phase.

**Original source identity**: `v3.17.6#MT-2` in `v3.17.6 - ci-gate-and-branch-hygiene`; normalized stable ID `MT-2-v3176` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-33`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.6`, section `v3.17.6 - ci-gate-and-branch-hygiene`, and original ID `MT-2`.

- **Migrated from**: v3.15#MT-2-v3155 (reason: user-deferred); original `v3.15.5#MT-2`, section `v3.15.5 - model-prompting-research`.

#### Original source: MT-2-v3155 - subprocess-invoked validator tests need explicit coverage plumbing, so coverage is not measured in CI - MIGRATED to v4.13 (AR-33)

- **Source phase**: v3.15.5 Phase 1.5.
- **Plan reference**: Phase 1.5 (stabilization) and the implement-phase coverage gate.
- **Reason**: `tests/validators/conftest.py` runs each validator as a SUBPROCESS (deliberately, so the tests exercise the real CLI surface end users run), so a plain `pytest --cov` collects nothing from the scripts under test. Coverage for this phase was measured out-of-band with `COVERAGE_PROCESS_START` plus `coverage combine` (94% validator, 97% freshness checker, 97% combined, branch coverage on), but CI does not run coverage for `tests/validators` at all, so the number is enforced nowhere. This affects the entire pre-existing `tests/validators` suite, not only the two new scripts.
- **Suggested next step**: if coverage enforcement is wanted for this suite, add the `COVERAGE_PROCESS_START` plumbing to the CI `tests` job once, for the whole `tests/validators` tree. Non-blocking; behavioral coverage is strong, since every documented structural rule has a dedicated failing-case test.

**Original source identity**: `v3.15.5#MT-2` in `v3.15.5 - model-prompting-research`; normalized stable ID `MT-2-v3155` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-33`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.5`, section `v3.15.5 - model-prompting-research`, and original ID `MT-2`.

### AR-34: No repository-wide Ruff baseline

- **Current state**: `ruff check` still reports findings (for example F401 and F841 in `graph/affected.py`, and findings in `scripts/lib/integrations/`); Ruff runs only in `presentify-extractor.yml`.
- **Owner and next step**: CI owner; set a baseline, fix the small findings, and gate new ones.
- **Historical transfer note**: v3.15.1#WN-2, v3.15.10 (Ruff advisory), and v3.17.0#WN-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#WN-2 (reason: user-deferred); original `v3.17.0#WN-2`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: WN-2 - OPEN (pre-existing tooling debt): integration framework has no clean repository-wide Ruff baseline - MIGRATED to v4.13 (AR-34)

- **Target file**: `scripts/lib/integrations/`
- **Source phase**: v3.17.0 Phase 2, sub-task 2.4 (lint verification)
- **Reason it is open**: an exploratory `python -m ruff check scripts/lib/integrations tests/integrations/test_autonomy_descriptors.py` reported 180 existing modernization, import-order, mutable-class-config, and unused-code findings across the integration framework. The Phase 2 test file passes focused Ruff validation, and Phase 2 did not suppress or introduce a new lint rule; cleaning the framework would be an unrelated broad refactor.
- **Suggested next step**: establish a deliberate Ruff baseline or scoped rule set in a dedicated lint-maintenance cycle, then reduce the existing findings in reviewable batches rather than mixing them into a release architecture phase.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-34`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `WN-2`.

- **Migrated from**: v3.15#WN-2 (reason: user-deferred); original `v3.15.1#WN-2`, section `v3.15.1 - adoption-codesight`.

#### Original source: WN-2 - Pre-existing ruff findings in graph/affected.py - MIGRATED to v4.13 (AR-34)

- **Source phase**: v3.15.1 adoption-codesight Phase 4 (4.1)
- **Reason**: ruff flags an unused `EdgeKind` import (F401) and an unused `frontier` local (F841) in `graph/affected.py`. Both are PRE-EXISTING; Phase 4 only ADDED `most_imported_files` (ruff-clean). The extension `src/` is not ruff-gated in this repo's CI. Left untouched per the no-out-of-scope-cleanup rule.
- **Suggested next step**: remove both in a dedicated extension lint pass.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-34`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.1`, section `v3.15.1 - adoption-codesight`, and original ID `WN-2`.

### AR-50: The template parity guard covers only the five lockstep templates

- **Current state**: `scripts/check_base_template_parity.py` guards the lockstep five; companion validators cover only named blocks on the other templates.
- **Owner and next step**: template maintainer; extend the guard or record the scope by decision.
- **Historical transfer note**: v3.15.10 (parity-guard advisory) on 2026-09-29 (reason: still open).

### AR-53: No reusable self-check eval-loop authoring convention

- **Current state**: only the Markdown style self-check exists.
- **Owner and next step**: catalog maintainer; write the convention and an optional reference template.
- **Historical transfer note**: v3.15.3#DF-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-1-v3153 (reason: user-deferred); original `v3.15.3#DF-1`, section `v3.15.3 - adoption-no-ai-slop`.

#### Original source: DF-1-v3153 - promote the self-check eval-loop pattern into a reusable authoring convention - MIGRATED to v4.13 (AR-53)

- **Source phase**: v3.15.3 Phase 3.2 (deferred follow-up).
- **Plan reference**: Phase 3.2 ("Record any deferred anti-slop follow-ups, for example promoting the self-check eval pattern into a reusable authoring convention").
- **Reason**: `anti-slop-editing` ships a runtime self-check loop (the skill grades its own output against `references/self-check.md`, fixes, and re-checks before returning). This is a genuinely reusable authoring pattern - a skill that produces content could ship a rubric and self-grade against it - but generalizing it (a shared convention documented in AGENTS.md, or a `references/self-check.md` template other skills adopt) is out of scope for this single-skill plan.
- **Suggested next step**: in a future cycle, evaluate promoting the self-check-loop pattern into an authoring convention (AGENTS.md guidance + an optional shared rubric template), so other content-producing skills can adopt it. Non-blocking; the pattern works today inside `anti-slop-editing`.

**Original source identity**: `v3.15.3#DF-1` in `v3.15.3 - adoption-no-ai-slop`; normalized stable ID `DF-1-v3153` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-53`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.3`, section `v3.15.3 - adoption-no-ai-slop`, and original ID `DF-1`.

### AR-55: `ai-agent-governance` has no reciprocal SKIP clause

- **Current state**: its description still lacks one.
- **Owner and next step**: catalog maintainer; add a SKIP pointing to `agentic-endpoint-hardening` and sync `data/skills.json`.
- **Historical transfer note**: v3.15.6#DF-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-1-v3156 (reason: user-deferred); original `v3.15.6#DF-1`, section `v3.15.6 - adoption-sandbox-escapes`.

#### Original source: DF-1-v3156 - `ai-agent-governance` carries no SKIP clause (reciprocal carve-out not added) - MIGRATED to v4.13 (AR-55)

- **Source phase**: v3.15.6 Phase 1.1 / 1.4.
- **Plan reference**: Phase 1.1 (the description's SKIP clause fencing off deployed-service agent governance).
- **Reason**: the new skill's SKIP clause names `ai-agent-governance`'s territory in order to defer to it, which imports that skill's vocabulary into the new description's token set and produced a 50% near-collision on the pairwise detector. The pair was ALLOWLISTED (with a reason) rather than fixed in place, because routing is empirically correct in both directions: the `neg-service-governance` case routes away from the new skill, and all six positives outrank every competitor including `ai-agent-governance` (the runner's `_top_competitor` scores against every other skill). Adding a reciprocal SKIP clause to `ai-agent-governance` would be the higher-quality fix and matches the `technical-documentation` precedent, but that skill's missing SKIP clause is a PRE-EXISTING description-quality gap that this phase did not create, and editing it would also require syncing its `description` mirror in `data/skills.json`. Out of scope per the no-out-of-scope-cleanup rule.
- **Suggested next step**: in a future cycle, sharpen `ai-agent-governance`'s description with a SKIP clause deferring local coding-agent endpoint hardening to `agentic-endpoint-hardening` (and sync `data/skills.json`), making the pair mutually fenced like `oncall-runbook` / `runbook-writer`. The allowlist entry can stay either way. Non-blocking; routing is proven correct today.


**Original source identity**: `v3.15.6#DF-1` in `v3.15.6 - adoption-sandbox-escapes`; normalized stable ID `DF-1-v3156` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-55`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.6`, section `v3.15.6 - adoption-sandbox-escapes`, and original ID `DF-1`.

### Presentify

### AR-18: Presentify builder and extractor limits

- **Current state**: approximate PDF text/figure interleaving, duplicated caption text, geometry-only OCR tables, best-effort `.gitignore` matching, a minimal Markdown parser, no video/audio embedding, no brand web-font embedding, no Coverr/Mixkit fetch, no image gallery grouping, null PDF raster `page_fraction` on bbox mismatch, and overlay-annotation over-capture. Most are recorded as limits in `extraction-runbook.md`.
- **Owner and next step**: presentify owner; accept each explicitly by decision or schedule the ones with user value (font embedding, gallery grouping).
- **Historical transfer note**: v3.9#DF-v39-presentify-4, v3.9#DF-v39-presentify-5, v3.12#DF-1 to DF-5, v3.13#DF-1, DF-2, DF-4, DF-5, DF-6, and v3.15.4#DF-1, DF-2, DF-3 on 2026-09-29 (reason: still open; duplicates merged).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.9#DF-v39-presentify-4 (reason: user-deferred); original `v3.9#DF-v39-presentify-4`, section `Open Items`.

#### Original source: DF-v39-presentify-4 - MIGRATED to v4.13 (AR-18)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v39-presentify-4 - MIGRATED to v4.13 (AR-18)

**Category**: DF

**Source**: presentify-interactive-html Phase 1

**Reason**: Video / audio media embedded in any source format is ignored (the output is a single self-contained offline HTML deck; embedded media would break the offline / size guarantee).

**Suggested next step**: Revisit only if embedded media is a stated requirement; would need a size + offline strategy.

**Severity**: Low (out of scope by design for a self-contained deck).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.9`, section `Open Items`, and original ID `DF-v39-presentify-4`.

- **Migrated from**: v3.9#DF-v39-presentify-5 (reason: user-deferred); original `v3.9#DF-v39-presentify-5`, section `Open Items`.

#### Original source: DF-v39-presentify-5 - MIGRATED to v4.13 (AR-18)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v39-presentify-5 - MIGRATED to v4.13 (AR-18)

**Category**: DF

**Source**: presentify-interactive-html Phase 2

**Reason**: Custom brand-font embedding is not implemented in the builder: a theme / brand override supplies CSS font stacks, but a non-system custom font would need a base64 `@font-face` to stay self-contained. The builder keeps fonts as system stacks so the output never fetches a font.

**Suggested next step**: Add an opt-in base64 `@font-face` embed path (read the font file from the brand `assets_dir`, inline it) if a brand custom font becomes a requirement.

**Severity**: Low (documented in `references/interactive-features.md`; system-stack themes and brand palettes are fully supported).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.9`, section `Open Items`, and original ID `DF-v39-presentify-5`.

- **Migrated from**: v3.12#DF-1 (reason: user-deferred); original `v3.12.0#DF-1`, section `v3.12.0`.

#### Original source: DF-1 - PDF text/figure interleaving is approximate - MIGRATED to v4.13 (AR-18)

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md` sub-task 1.2
- **Reason**: Within a PDF page section, extracted figure images are placed after the page's text and tables (ordered among themselves by vertical position) rather than interleaved at their exact in-flow position; true interleaving would require full layout reflow, which is out of scope. Documented as a runbook gotcha.
- **Suggested next step**: The `page` + `caption` metadata is sufficient for the authoring stage to place figures sensibly (proven in the Phase 5 worked example); revisit only if authoring proves to need exact in-flow positions.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.0`, section `v3.12.0`, and original ID `DF-1`.

- **Migrated from**: v3.12#DF-2 (reason: user-deferred); original `v3.12.0#DF-2`, section `v3.12.0`.

#### Original source: DF-2 - Caption text remains duplicated in page paragraph text - MIGRATED to v4.13 (AR-18)

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: sub-task 1.2 (caption pairing)
- **Reason**: A detected caption is ATTACHED to its figure block, not moved: the same line also remains inside the page's paragraph text. Removing it from the text flow risks dropping content on false-positive matches, so the extractor keeps both. Documented as a runbook gotcha.
- **Suggested next step**: The authoring stage should prefer the block `caption` and drop the duplicate line; consider extractor-side dedup once caption matching has real-world mileage.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.0`, section `v3.12.0`, and original ID `DF-2`.

- **Migrated from**: v3.12#DF-3 (reason: user-deferred); original `v3.12.0#DF-3`, section `v3.12.0`.

#### Original source: DF-3 - OCR table recovery is geometry-based; pytesseract path recovers paragraphs only - MIGRATED to v4.13 (AR-18)

- **Source phase**: Phase 1 (1.5)
- **Plan reference**: sub-task 1.5 (two-tier OCR path)
- **Reason**: Tier-A table reconstruction clusters OCR boxes into aligned multi-cell rows, which works on well-separated columns (fixture-verified) but not on dense or borderless tables; the `pytesseract` fallback emits paragraphs only. The tier-B scanned-page image plus the figure-reconstruction protocol's transcription/verification pass are the accuracy backstop in all cases.
- **Suggested next step**: Revisit only if real scans show tier-A table recovery failing where it matters; the mandatory numeric verification already guards correctness.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.0`, section `v3.12.0`, and original ID `DF-3`.

- **Migrated from**: v3.12#DF-4 (reason: user-deferred); original `v3.12.0#DF-4`, section `v3.12.0`.

#### Original source: DF-4 - Video / audio media embedding (carried from v3.9, DF-v39-presentify-4) - MIGRATED to v4.13 (AR-18)

- **Source phase**: v3.9 presentify-interactive-html Phase 1; re-affirmed by v3.12 Phase 6
- **Plan reference**: v3.12 plan Phase 6 (6.2)
- **Reason**: Media in any source format is ignored: the output is a single self-contained offline HTML file, and embedded media would break the offline / size guarantee.
- **Suggested next step**: Revisit only if embedded media becomes a stated requirement; would need a size + offline strategy.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.0`, section `v3.12.0`, and original ID `DF-4`.

- **Migrated from**: v3.12#DF-5 (reason: user-deferred); original `v3.12.0#DF-5`, section `v3.12.0`.

#### Original source: DF-5 - Brand custom-font embedding in the baseline builder (carried from v3.9, DF-v39-presentify-5) - MIGRATED to v4.13 (AR-18)

- **Source phase**: v3.9 presentify-interactive-html Phase 2; re-affirmed by v3.12 Phase 6
- **Plan reference**: v3.12 plan Phase 6 (6.2)
- **Reason**: A theme / brand override supplies CSS font stacks; a non-system custom font would need an opt-in base64 `@font-face` embed to stay self-contained. System stacks and brand palettes are fully supported.
- **Suggested next step**: Add the opt-in base64 `@font-face` embed path (read the font file from the brand `assets_dir`, inline it) if a brand custom font becomes a requirement.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.0`, section `v3.12.0`, and original ID `DF-5`.

- **Migrated from**: v3.13#DF-1 (reason: user-deferred); original `v3.13.0#DF-1`, section `v3.13.0`.

#### Original source: DF-1 - `.gitignore` matching is best-effort - MIGRATED to v4.13 (AR-18)

- **Source phase**: Phase 1 (1.2)
- **Reason**: The walk reads the root `.gitignore` and supports leading-`/` anchoring plus basename / path globs via `fnmatch`, but does NOT implement negation (`!pattern`) or git's full `**` semantics. Documented as a runbook limit.
- **Suggested next step**: Adopt a vetted local `.gitignore`-spec library only if real repos show meaningful mismatch; the current matcher plus the ignore-dir list covers the common cases.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `DF-1`.

- **Migrated from**: v3.13#DF-2 (reason: user-deferred); original `v3.13.0#DF-2`, section `v3.13.0`.

#### Original source: DF-2 - Markdown parser is intentionally minimal - MIGRATED to v4.13 (AR-18)

- **Source phase**: Phase 1 (1.3)
- **Reason**: The in-house Markdown parser handles ATX / setext headings, fenced code, bullets, pipe tables, and standalone local images; it is not a full CommonMark implementation (reference-style links, footnotes, and HTML blocks pass through as prose). Standard-library-only by design (no Markdown dependency).
- **Suggested next step**: Revisit only if richer Markdown fidelity is needed; a lazy-imported CommonMark parser could be added behind the same lazy-import discipline.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `DF-2`.

- **Migrated from**: v3.13#DF-4 (reason: user-deferred); original `v3.13.0#DF-4`, section `v3.13.0`.

#### Original source: DF-4 - Video / audio media embedding (carried from v3.9 / v3.12) - MIGRATED to v4.13 (AR-18)

- **Reason**: Media in any source format is ignored; embedded media would break the single-file offline / size guarantee. Unchanged by this version.
- **Suggested next step**: Out of scope for the self-contained-HTML deliverable.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `DF-4`.

- **Migrated from**: v3.13#DF-5 (reason: user-deferred); original `v3.13.0#DF-5`, section `v3.13.0`.

#### Original source: DF-5 - Brand web-font embedding (carried from v3.9 / v3.12) - MIGRATED to v4.13 (AR-18)

- **Reason**: Fonts stay as system stacks or base64 `@font-face`; fetching a brand web font would break the offline guarantee. Unchanged by this version.
- **Suggested next step**: A base64 `@font-face` embed path could be added; never an external fetch.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `DF-5`.

- **Migrated from**: v3.13#DF-6 (reason: user-deferred); original `v3.13.0#DF-6`, section `v3.13.0`.

#### Original source: DF-6 - Tier 2 stock: Coverr / Mixkit sources and general video fetch not implemented - MIGRATED to v4.13 (AR-18)

- **Source phase**: Phase 2 (2.1)
- **Reason**: `fetch_stock_media.py` implements Openverse (default, keyless), Wikimedia Commons (keyless), and Pexels (API-key-gated) for images. Coverr / Mixkit are accepted on the CLI for interface parity but have no keyless search API in this helper, so they degrade with a note; video is supported only via a Pexels key. This keeps the helper honest rather than shipping unverified API integrations. Video also inherits the base64 size ceiling: any fetched asset is base64-embedded and rejected past `--max-bytes`, so a large video degrades rather than bloating the single-file output (video embedding at scale remains constrained by the offline single-file guarantee, per DF-4).
- **Suggested next step**: Add a Coverr / Mixkit (or a generic configured-endpoint) source and a broader video path only if a real need appears; document them as configured sources, and keep video within a sensible `--max-bytes` cap.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `DF-6`.

- **Migrated from**: v3.15#DF-3-v3154 (reason: user-deferred); original `v3.15.4#DF-3`, section `v3.15.4 - presentify-visual-fidelity`.

#### Original source: DF-3-v3154 - overlay-annotation detection is a geometric heuristic (full-slide-background text is captured) - MIGRATED to v4.13 (AR-18)

- **Source phase**: v3.15.4 Phase 3.3.
- **Plan reference**: Phase 3.3 (capture author-added overlay shapes over a picture).
- **Reason**: the extractor assigns a non-picture shape as an annotation when its CENTER lies inside a picture AND its area is smaller than the picture. This correctly captures region rectangles and callout labels over a figure, but a full-slide BACKGROUND picture with body text on top would capture that body text as annotations (the text is, arguably, overlaid on the image). The LLM-native path re-reads under the confidence gate and applies judgment; the deterministic builder renders whatever `annotations` carries. Documented in the `extraction-runbook.md` PPTX gotchas.
- **Suggested next step**: if this over-capture is observed in practice, tighten the heuristic (for example, skip pictures whose `page_fraction` is ~1.0 unless they are classified `map`/`diagram`/annotated, or require the annotation shape to carry a fill or a short label). Non-blocking; the primary consumer applies judgment.

**Original source identity**: `v3.15.4#DF-3` in `v3.15.4 - presentify-visual-fidelity`; normalized stable ID `DF-3-v3154` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.4`, section `v3.15.4 - presentify-visual-fidelity`, and original ID `DF-3`.

- **Migrated from**: v3.15#DF-1-v3154 (reason: user-deferred); original `v3.15.4#DF-1`, section `v3.15.4 - presentify-visual-fidelity`.

#### Original source: DF-1-v3154 - baseline builder does not group images into a `.gallery` (styles are latent) - MIGRATED to v4.13 (AR-18)

- **Source phase**: v3.15.4 Phase 2.3.
- **Plan reference**: Phase 2.3 (template image / gallery styles) and 2.1 (prominence rules; the primary target is the LLM-native authoring path).
- **Reason**: the Phase 2.3 template now carries a token-driven `.gallery` grid with a bounded per-tile cap, but the deterministic baseline builder (`build_presentation.py`) renders each image as its own stacked `<figure>` and does not emit a `.gallery` wrapper or classify hero-vs-secondary from `page_fraction`. So on the baseline path several small images stack (each bounded by `max-height: 80vh` + `max-width`, so none crops or distorts) rather than forming a grid. The prominence-aware hero/secondary sizing and the gallery grid are the LLM-native path's job per the reference; the baseline is the "plain draft to elevate".
- **Suggested next step**: if the baseline should render a true gallery, teach the builder to group a run of comparable-`page_fraction` images into a `.gallery` wrapper (and size a high-`page_fraction` image as a hero) in a later phase. Non-blocking.

**Original source identity**: `v3.15.4#DF-1` in `v3.15.4 - presentify-visual-fidelity`; normalized stable ID `DF-1-v3154` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.4`, section `v3.15.4 - presentify-visual-fidelity`, and original ID `DF-1`.

- **Migrated from**: v3.15#DF-2-v3154 (reason: user-deferred); original `v3.15.4#DF-2`, section `v3.15.4 - presentify-visual-fidelity`.

#### Original source: DF-2-v3154 - PDF embedded-raster `page_fraction` is null when the pdfplumber image-bbox count does not match the extracted raster count - MIGRATED to v4.13 (AR-18)

- **Source phase**: v3.15.4 Phase 2.2 (discovered while confirming the signals).
- **Plan reference**: Phase 2.2 ("If any is missing or frequently null, add it").
- **Reason**: the PDF path computes `page_fraction` for an embedded raster only when pdfplumber's per-page `images` bbox list length equals the extracted raster count (the extractor's intentional geometry-alignment guard, so a bbox is never mis-assigned to the wrong raster). When the counts differ the block still carries native `width`/`height` but `page_fraction` is absent. This is NOT "frequently null" for well-formed report PDFs (the confirmed embedded-raster test yields a populated fraction), so it is documented rather than fixed; PPTX pictures and PDF rasterized-regions always carry the fraction.
- **Suggested next step**: a later phase could add per-raster bbox matching (by size / order heuristics) to populate `page_fraction` even when the counts differ. Non-blocking; the native dimensions still provide a fallback ranking signal.

**Original source identity**: `v3.15.4#DF-2` in `v3.15.4 - presentify-visual-fidelity`; normalized stable ID `DF-2-v3154` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-18`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.4`, section `v3.15.4 - presentify-visual-fidelity`, and original ID `DF-2`.

### AR-19: Presentify verification residuals

- **Current state**: no rendered QA of the v3.13 samples is recorded; no live or scheduled media-fetch smoke; a sample-deck scorer smoke in the render job is unconfirmed; the scorer cannot see runtime-injected palettes; Gates A, B, and E and the composition probes have no checker or helper.
- **Owner and next step**: presentify owner; add the smoke to the render job and accept or build each checker.
- **Historical transfer note**: v3.13#WN-1, v3.13#MT-2, v3.15.4#MT-3, v3.16.5#WN-2, v3.16.7#NI-2, and v3.16.7#NI-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

**Current residual from `v4.9.0#MT-3`**: Resolve real-deck fragment budgets: slides2/6 declare9/16 versus maximum8. Implement or verify a runtime structural inspection path for the three legacy static-stage checks currently UNCHECKED. Establish a verified reading-figure-to-slide model mapping and prove actual re-layout plus tick/legend fidelity. Qualify uncovered SVG marks, arrowheads and animation frames separately from settled connector/chart-line pixel proof.

**Partial disposition**: Retain the pinned 15-slide,73-fragment,four-viewport,352-state follow-ups, the stage-relative floor correction, flow-order and chart-line partial closures. Bounded settled probes do not constitute full deck qualification.

- **Migrated from**: v3.13#WN-1 (reason: user-deferred); original `v3.13.0#WN-1`, section `v3.13.0`.

#### Original source: WN-1 - Full-repo validators and browser visual-QA unavailable on the Windows dev host - MIGRATED to v4.13 (AR-19)

- **Source phase**: Phases 1-5
- **Reason**: `validate_unicode_safety.py` / `validate_no_personal_paths.py` (full-repo scans) and the compression eval time out on the dev host, and no headless browser is installed, so the rendered visual-QA loop (screenshots) and the per-aspect / hero-vs-gallery rendered demonstrations could not run locally. Change-relevant validators were run directly (bundle audit, JSON integrity, version-sync, ASCII, ruff); edited files are ASCII-verified. The imagery-and-interactivity Phase 1 Tier-1 sample (`development/worked-example/tier1-imagery-sample.html`) was likewise reviewed statically (offline-refs grep clean, tag-balance and ASCII checked), not browser-rendered.
- **Suggested next step**: Rely on CI for the full validator chain; run the rendered visual-QA of the Tier-1 sample and the universal-ingestion worked example in a browser-capable session.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `WN-1`.

- **Migrated from**: v3.13#MT-2 (reason: user-deferred); original `v3.13.0#MT-2`, section `v3.13.0`.

#### Original source: MT-2 - Live Tier-2 fetch paths and Tier-3 generation not exercised in CI (residual) - MIGRATED to v4.13 (AR-19)

- **Source phase**: Phase 2 (2.1-2.3), Phase 3 (3.1-3.2), Phase 5 (5.3)
- **Status**: the committed automated verifier is DELIVERED - `docs/v3/v3.13/development/fixtures/verify_imagery.py` (34 offline checks: license filter incl. nc/nd rejection, CC-BY attribution builder, `accept_candidate`, the credits-manifest / asset shape via a stubbed download, the consent-default-offline invariant via a stubbed transport, and the Tier-3 model-license registry / `parse_size` / degrade / no-network-import invariants), wired into `presentify-extractor.yml`. It runs on a plain ubuntu runner with no extra dependency, network, or GPU.
- **Residual gap**: only the LIVE network / GPU paths remain un-CI'd - the Wikimedia and Pexels source paths were not live-exercised (Openverse was, returning verified CC-BY assets; Pexels needs a key), and the Tier-3 diffusers generation path needs a local GPU runtime + weights absent from the dev host and CI.
- **Suggested next step**: Optionally gate a live Openverse smoke test behind a manual / scheduled CI job; keep the Tier-3 GPU generation a documented manual step on a GPU-capable host. Neither blocks release (both degrade cleanly and the pure-function logic is CI-covered).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `MT-2`.

- **Migrated from**: v4.9#MT-3 (reason: user-deferred); original `v4.9.0#MT-3`, section `v4.9.0 - adoption-visa-vulnerability-agentic-harness`.

#### Original source: MT-3 - Pre-rule handbook does not exercise the slide-specific checks

- **Source phase**: v4.9.2 Task 6, real-artifact proof.
- **Plan reference**: [v4.9.2 Task 6 Step 1](../../../archives/v4/v4.9/plans/v4.9.2-slide-build-contract-and-projection-floors.md#7-task-6-prove-it-on-a-real-artifact).
- **Reason**: the previously missing real-artifact run is now recorded in the [2026-09-27 verification](../../../archives/v4/v4.9/development/real-deck-score-2026-09-27/verification.md). The historical `lvedp-algorithm.html` blob fails `presentation-declared` at high severity and reports `slide-mode: n/a`, so none of the three structural slide checks runs on that artifact. The rendered stage-type floor was not measured on that artifact. The existing compliant two-slide fixture passes the structural report, and the stage floor has separate fixture controls; those are narrower than real-deck coverage.
- **Status**: open coverage gap, not an implementation failure attributed to the scorer.
- **Suggested next step**: use a preserved real deck that exposes actual `.slide-stage` sections, or define and verify a separate runtime-deck inspection path, then run the structural scorer and rendered stage-floor probe with artifact hashes. Merely adding a slide declaration to the historical deck does not supply stages. Keep the original undeclared-deck failure as separate evidence; do not claim that a clean synthetic fixture proves a real deck passes.

**Fail-closed follow-up, 2026-09-27**: An in-memory copy of the same historical blob added only `data-nav="slides"` to `<body>`. It still contains zero static `.slide-stage` sections; before this repair, `slide-fragments`, `slide-type-variety`, and `slide-figure-scaled` each reported `pass` without inspecting a slide. Those three checks now report `unchecked`, while `slide-structure` remains a high-severity failure and `page_pass` remains false. A clean two-slide control still reports `pass` for all three checks. The [archived verification](../../../archives/v4/v4.9/development/empty-slide-stage-coverage-2026-09-27/verification.md) retains both deck hashes and the red/green result. MT-3 remains open for real-deck structural and rendered coverage.

**Runtime render follow-up, 2026-09-27**: Chromium opened the unchanged historical blob, reached all 15 `.dkslide` articles, and measured visible text nodes at four viewports. The 2%-of-viewport stage floor failed on slides 4 and 6 at 1366x768 and on all slides at 390x844; slide 4 also exceeded four rendered sizes. The [archived runtime evidence](../../../archives/v4/v4.9/development/runtime-deck-render-2026-09-27/verification.md) records the hash, method, counts, and limits. This is one settled state per slide, not a runtime structural scorer or full build-state qualification. MT-3 remains open; the three legacy static-stage checks remain `unchecked` on this deck.

**Stage-floor correction, 2026-09-27**: The preceding viewport-relative floor verdict was wrong for the deck's scaled 900-unit stage. Fresh browser stage measurements and the preserved text-node minima show that all four sampled viewport states pass the correct 2%-of-rendered-stage floor. An in-memory undersized-text control fails that comparison. The [append-only correction](../../../archives/v4/v4.9/development/runtime-deck-stage-floor-correction-2026-09-27/verification.md) preserves the original report and its error; slide 4's excessive size variety and MT-3's missing build-state and structural coverage remain open.

**Build-state probe, 2026-09-27**: A [read-only Chromium probe](../../../archives/v4/v4.9/development/runtime-deck-build-state-2026-09-27/verification.md) reached all 15 slides at desktop and mobile sizes and sampled declared fragment completions. Slides 2 and 6 declare 9 and 16 distinct fragments, exceeding the eight-fragment contract; a zero-index in-memory control is rejected. The probe does not establish semantic build order, all-state rendered typography, or figure re-layout, and the legacy static-stage checks remain `unchecked`. MT-3 stays open; this is a real-artifact finding and bounded coverage, not full qualification.

**Four-viewport follow-up, 2026-09-27**: The same pinned blob and [probe](../../../archives/v4/v4.9/development/runtime-deck-four-viewport-build-state-2026-09-27/verification.md) were exercised at 1366x768, 1024x768, 768x1024, and 390x844. All 15 slides and 73 declared fragment completions were reached at each size, for 292 sampled completions. Slides 2 and 6 remain over the eight-fragment budget; every sample has one active slide, no network request occurs, and the zero-index control is rejected. MT-3 remains open because semantic order, SVG stroke visibility, all-state typography, and figure re-layout were not qualified.

**All-state text and SVG-box follow-up, 2026-09-27**: A separate [runtime probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/verification.md) used ArrowRight navigation on the same pinned blob at four viewports. Three runs each sampled 352 initial-or-fragment states; 8,527-8,584 text-node instances passed the corrected 2%-of-rendered-stage floor and 456-461 visible outer SVG-box instances stayed inside the viewport. Counts vary with timed animation sampling; font-size and figure-shift negative controls both failed as intended in every run. A first dot-click run that reported 61 mobile SVG-box failures was rejected after proving that Playwright had scrolled the deck overlay horizontally. MT-3 remains open for semantic order, internal SVG rendering, true figure re-layout, and the static-stage checks, which are still `unchecked` on this deck.

**Semantic flow-order follow-up, 2026-09-27**: A [pinned Chromium probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/semantic-order-verification.md) matched the source and target node of all 13 connectors across the three authored flow slides at four viewports. All 14 nodes followed the written content-order manifests, each connector arrived with its target after its source, all settled elements revealed, and early-arrow and detached-endpoint mutations were rejected at every size. This qualifies those flow diagrams only, not every deck build. MT-3 remains open for the known fragment-budget failures on slides 2 and 6, internal SVG stroke visibility, figure re-layout, and the three static-stage checks that remain `unchecked`.

**Chart-layout boundary, 2026-09-27**: A [pinned browser probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/figure-layout-verification.md) inspected 14 model-backed slide charts at four viewports. Each used authored 21-unit chart text and had no extra SVG scale beyond the stage; an in-memory half-scale mutation was rejected every time. The pinned reading page has zero `figure.fig[id]` chart instances and no verified mapping from its separately authored `.drawn` SVGs to the slide models, so this does not prove source-to-slide re-layout, tick or legend fidelity, or internal paint. MT-3 remains open alongside the fragment-budget failures and `unchecked` static checks.

**Flow-connector paint boundary, 2026-09-27**: A [pinned rendered-pixel probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/flow-paint-verification.md) checked all 13 connector bodies on the three authored flow slides at four viewports. All 52 connector-view observations changed 19-70 midpoint-window pixels when hidden; 12 fully invisible controls changed zero pixels, with no external requests or page errors. This qualifies settled connector-body paint only, not every SVG path, chart stroke, arrowhead, animation frame, or reading-figure-to-slide re-layout. MT-3 remains open for those boundaries, the known fragment-budget failures, and three `unchecked` static checks.

**Chart-line paint boundary, 2026-09-27**: A [pinned rendered-pixel probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/chart-line-paint-verification.md) checked all 31 `path.c-line` elements across 14 model-backed charts at four viewports. All 124 line-viewport observations changed pixels when hidden, all 124 invisible-line controls changed zero pixels, and a forced null stroke was rejected at every viewport. Other SVG marks and animation frames are not covered. MT-3 remains open for those boundaries, the fragment-budget failures, the absent reading-figure map, and the three static checks still `unchecked` on this deck.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.9.0`, section `v4.9.0 - adoption-visa-vulnerability-agentic-harness`, and original ID `MT-3`.

- **Migrated from**: v3.15#MT-3-v3154 (reason: user-deferred); original `v3.15.4#MT-3`, section `v3.15.4 - presentify-visual-fidelity`.

#### Original source: MT-3-v3154 - the visual-QA loop's agent-vision grading, fan-out, and end-to-end sample-deck smoke are behavioral (the structural scorer is the unit-tested backbone) - MIGRATED to v4.13 (AR-19)

- **Source phase**: v3.15.4 Phase 5.5.
- **Plan reference**: Phase 5.5 ("a test that the workflow template degrades ... an end-to-end smoke test on the sample board deck fixture asserting the loop reaches the pass bar").
- **Reason**: the deterministic STRUCTURAL scorer (`scripts/visual_qa_score.py`) is fully unit-tested (per-criterion defect flagging, clean pass, CLI exit codes). The AGENT-VISION grading (crop, dead space, annotation placement vs source, imagery relevance, contrast), the Dynamic-Workflow fan-out, and the full render -> grade -> fix -> re-render loop are LLM-native + runtime + browser behavior, not deterministically unit-testable; the workflow template is an adapt-me artifact asserted structurally (it carries the three mandatory rules), not executed. There is no committed "sample board deck" fixture, and the loop is agent-driven, so the e2e smoke is a browser-gated / release-time verification (the Phase 7 exit checklist verifies the four observed defects on the sample deck), not a CI unit test.
- **Suggested next step**: when a headless-browser CI job is added (gated to merges/schedule, per the plan), wire an e2e smoke that runs the scorer against a built sample-deck fixture; the agent-vision grading stays a behavioral (non-unit) check. Non-blocking.

**Original source identity**: `v3.15.4#MT-3` in `v3.15.4 - presentify-visual-fidelity`; normalized stable ID `MT-3-v3154` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.4`, section `v3.15.4 - presentify-visual-fidelity`, and original ID `MT-3`.

- **Migrated from**: v3.16#WN-2-v3165 (reason: user-deferred); original `v3.16.5#WN-2`, section `v3.16.5 - presentify-visual-overhaul`.

#### Original source: WN-2-v3165 - OPEN: the scorer cannot see runtime-injected palette values - MIGRATED to v4.13 (AR-19)

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py` (`check_contrast`)
- **Source phase**: v3.16.5 Phase 2 (the checker gap behind BG-1)
- **Reason it is open**: `check_contrast` grades declared CSS custom properties. A page that assigns `--accent` from a `data-*` attribute in script, or paints canvas text with a literal, can pass the check and still render sub-AA text - which is exactly what BG-1 was. Statically resolving what a script assigns at runtime is not a job for a markup heuristic.
- **Suggested next step**: Phase 3 closes this by construction rather than by more parsing. A real screenshot shows the rendered color, so the AGENT-VISION half of rubric criterion 7 grades what the page actually paints. Do NOT attempt to interpret the script statically. A cheap partial guard is possible if it proves useful: collect hex literals from `data-accent`-style attributes and grade them alongside the declared tokens.

**Original source identity**: `v3.16.5#WN-2` in `v3.16.5 - presentify-visual-overhaul`; normalized stable ID `WN-2-v3165` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.5`, section `v3.16.5 - presentify-visual-overhaul`, and original ID `WN-2`.

- **Migrated from**: v3.16#NI-2-v3167 (reason: user-deferred); original `v3.16.7#NI-2`, section `v3.16.7 - presentify-first-shot-hardening`.

#### Original source: NI-2-v3167 - OPEN: Gates A, B, and E are agent behavior with no deterministic checker - MIGRATED to v4.13 (AR-19)

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/references/visual-qa-rubric.md`, `references/content-intent.md`
- **Source phase**: v3.16.7 Phase 3 (sub-tasks 3.1, 3.3, 3.6)
- **Reason it is open**: `scripts/visual_qa_score.py` can check a `content_intent` block's PRESENCE and shape, but not whether a `scope_class` is the right one, whether an assumption was genuinely accepted, or whether a visual explains its section. Those are judgments, and the same reasoning the maintainer applied to rubric criterion 10 in v3.16.5 applies here: a crude deterministic proxy produces false positives and trains the agent to satisfy the proxy. Enforcement is therefore record plus rubric, exactly as criterion 10 is.
- **Suggested next step**: consider a NARROW structural check for the mechanically-decidable half only, namely the `content_intent` block's presence and field completeness, and the `standalone` banned-phrase scan (a literal string search over visible text, which is decidable). Leave the judgments to the rubric. Do not attempt to score decision coverage.

**Original source identity**: `v3.16.7#NI-2` in `v3.16.7 - presentify-first-shot-hardening`; normalized stable ID `NI-2-v3167` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.7`, section `v3.16.7 - presentify-first-shot-hardening`, and original ID `NI-2`.

- **Migrated from**: v3.16#NI-3-v3167 (reason: user-deferred); original `v3.16.7#NI-3`, section `v3.16.7 - presentify-first-shot-hardening`.

#### Original source: NI-3-v3167 - OPEN: the composition probes are specified but not implemented in a helper - MIGRATED to v4.13 (AR-19)

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` Step 9
- **Source phase**: v3.16.7 Phase 3 (sub-task 3.5)
- **Reason it is open**: line count, width utilization, one-word orphan detection, rectangle intersection, and per-section density deltas are specified as `page.evaluate()` probes the grading agent writes inline, matching how the existing probes (root size, per-role smallest size, band fraction, `scrollWidth`, painted-canvas) are already specified. No bundled script computes them. That is consistent rather than a shortfall, and the `AGENTS.md` scope-fit gate declines a helper with no call site, but it does mean the probes are as reliable as the agent that writes them each run.
- **Suggested next step**: if a future session finds the probes being skipped or written inconsistently, extract all of them (existing and new) into one bundled `scripts/render_probes.js` the loop injects verbatim. Do that as ONE extraction covering the whole probe set, not a second partial layer.

**Original source identity**: `v3.16.7#NI-3` in `v3.16.7 - presentify-first-shot-hardening`; normalized stable ID `NI-3-v3167` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.7`, section `v3.16.7 - presentify-first-shot-hardening`, and original ID `NI-3`.

### Extensions

### AR-24: nexus-context-compressor deferred refinements

- **Current state**: near-duplicate detection, auto-sized keep budget, explicit error preservation, automatic store cleanup (`prune` has no caller), JSON arrays in prose, fallback parser limits, optional spaCy pass, CacheAligner and the ML token-dropper outside the runtime path, sub-word dropping, no live semantic benchmark, no token-reduction floor, no `[ml]` CI lane, and a short reformatter handler list. The `smart_crusher.py` docstring still marks them deferred.
- **Owner and next step**: compressor maintainer; take each only when a real fixture or benchmark shows the need.
- **Historical transfer note**: v3.2#DF-v32hr-1 to DF-v32hr-6, DF-v32hr-8, DF-v32hr-9, DF-v32hr-12 to DF-v32hr-15, MT-v32hr-1, and v3.19.2#DF-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.2#DF-v32hr-1 (reason: user-deferred); original `v3.2#DF-v32hr-1`, section `Open Items`.

#### Original source: DF-v32hr-1 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-1 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 1

**Plan reference**: T003 (SmartCrusher)

**Reason**: SmartCrusher dedups on EXACT canonical content: a record whose only difference from a neighbour is a volatile field (timestamp, request id) is treated as novel, and is collapsed only if its adjacent field-change count falls below `variance_threshold`. Fuzzy near-duplicate fingerprinting (the SimHash/MinHash-style detection production engines use to collapse records that differ only in noise) is intentionally out of scope for the v1 deterministic, dependency-free port. The SmartCrusher docstring points here.

**Suggested next step**: CacheAligner shipped in Phase 3 (T008) and now normalizes dynamic fields (dates/UUIDs/versions/hashes), removing most of the noise that defeats exact dedup; the pure-stdlib fingerprint near-dup pass itself is still deferred -- let the Phase 5 accuracy-regression harness (T016) measure whether it improves the ratio/accuracy trade-off before adding it.

**Severity**: Low (exact dedup is lossless and gate-passing; near-dup is an enhancement)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-1`.

- **Migrated from**: v3.2#DF-v32hr-2 (reason: user-deferred); original `v3.2#DF-v32hr-2`, section `Open Items`.

#### Original source: DF-v32hr-2 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-2 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 1

**Plan reference**: T003 (SmartCrusher)

**Reason**: The keep budget is a fixed `SmartCrusherConfig.max_items_after_crush` (default 15), per the plan's config contract. Information-theoretic auto-sizing (stop keeping items once additional ones add no new information, e.g. a knee/elbow on a coverage curve) -- the adaptive sizing production engines use -- is deferred; the plan deliberately scoped v1 to the fixed cap.

**Suggested next step**: Optional enhancement after the Phase 5 eval harness exists: the harness (T016) can measure whether adaptive sizing beats the fixed cap on the ratio/accuracy trade-off before any added complexity ships.

**Severity**: Low (fixed cap meets the stability gate; auto-sizing is an optimization)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-2`.

- **Migrated from**: v3.2#DF-v32hr-3 (reason: user-deferred); original `v3.2#DF-v32hr-3`, section `Open Items`.

#### Original source: DF-v32hr-3 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-3 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 1

**Plan reference**: T003 (SmartCrusher)

**Reason**: Anomalous records are preserved implicitly today: a record differing from its predecessor in >= `variance_threshold` fields is kept, and a one-off error line survives as novel content. Explicit error/outlier preservation (always retain `level=ERROR` / `status>=4xx` / statistical numeric outliers regardless of variance, as production string/number-array specializations do) is deferred to avoid shipping an error-detection heuristic that could misfire (false-keep junk, false-drop a genuine error) without the Phase 5 harness to measure it.

**Suggested next step**: Phase 3's ContentRouter (T009) was kept minimal per its prompt (log/text pass through untouched), so explicit error/outlier preservation was NOT added and remains deferred to Phase 5: fold type-specific preservation into per-content-type handling once the accuracy harness (T016) can measure it.

**Severity**: Low (distinct/novel records, including lone errors, already survive)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-3`.

- **Migrated from**: v3.2#DF-v32hr-4 (reason: user-deferred); original `v3.2#DF-v32hr-4`, section `Open Items`.

#### Original source: DF-v32hr-4 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-4 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 2

**Plan reference**: T005 (CCR store)

**Reason**: The CCR store ships an eviction *primitive* (`CCRStore.prune(max_entries=..., older_than_seconds=...)`, oldest-first by `created_at`) but no consumer invokes it automatically: `put` only inserts, so the default store at `~/.nexus-hub/cache/ccr-store.db` grows unbounded across sessions until something prunes it. This is deliberate -- auto-eviction on the hot path would add a clock/IO side effect to the per-drop write, and the *policy* (threshold, schedule, max size) belongs to the runtime that owns the store lifecycle, which does not exist until Phase 4 wires the PreToolUse hook + internal MCP.

**Suggested next step**: Still open after Phase 4: the runtime (PreToolUse hook + MCP server) now exists, but neither invokes `store.prune(...)` -- the compress path only `put`s. Wire a documented prune policy into a runtime owner (e.g. an MCP-server-startup TTL sweep, or a periodic max-entry cap), since the server process is the natural lifecycle owner. A pruned span's marker already resolves to `NOT_FOUND`, which the consumer handles, so eviction is safe. Defer the policy choice to a follow-up rather than guess a threshold.

**Severity**: Low (eviction primitive exists and is tested; only the auto-scheduling is deferred, and a cold store simply never prunes)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-4`.

- **Migrated from**: v3.2#DF-v32hr-5 (reason: user-deferred); original `v3.2#DF-v32hr-5`, section `Open Items`.

#### Original source: DF-v32hr-5 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-5 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 3

**Plan reference**: T009 (ContentRouter)

**Reason**: ContentRouter splits mixed content on fenced code blocks and classifies each whole non-fenced chunk; a JSON array embedded mid-paragraph *inside* prose (neither the whole chunk nor a fenced block) is left untouched rather than isolated and crushed. Deliberate: paragraph-level splitting of prose risks cutting non-code text, while the high-value shapes (a tool dump that *is* a JSON array, and fenced ` ```json ` / code blocks) are handled exactly.

**Suggested next step**: If real payloads show prose-embedded arrays worth compressing, add paragraph-level segmentation guarded by per-paragraph JSON validation; measure the ratio/accuracy effect with the Phase 5 harness (T016).

**Severity**: Low (common JSON shapes are routed; only prose-embedded arrays are skipped, never mangled)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-5`.

- **Migrated from**: v3.2#DF-v32hr-6 (reason: user-deferred); original `v3.2#DF-v32hr-6`, section `Open Items`.

#### Original source: DF-v32hr-6 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-6 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 3

**Plan reference**: T010 (CodeCompressor)

**Reason**: The dependency-free regex/structural fallback -- used only when the reused `nexus-code-search` AST infra is unavailable, or for a brace language it does not cover (e.g. `.js`/`.jsx`) -- is best-effort: it does not tokenize strings/comments while tracking brace depth, and it requires a brace function's body-opening `{` to share a line with the parameter list (multi-line signatures are not detected). The AST path -- the default whenever `nexus-code-search` is importable -- is string-aware via tree-sitter and has neither limitation.

**Suggested next step**: Optional: harden the brace fallback (string/comment-aware depth, multi-line-signature detection) only if a meaningful share of real inputs hit the fallback; otherwise rely on the AST path. The 232-252 sibling-path-discovery branch in `_load_ast` is uncovered because `nexus-code-search` is editable-installed in the dev/CI env (the direct import wins); it is the air-gapped-checkout fallback.

**Severity**: Low (AST path is primary and unaffected; the fallback degrades to under-compression, never a mis-cut)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-6`.

- **Migrated from**: v3.2#DF-v32hr-8 (reason: user-deferred); original `v3.2#DF-v32hr-8`, section `Open Items`.

#### Original source: DF-v32hr-8 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-8 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 3

**Plan reference**: T008 (CacheAligner)

**Reason**: The optional spaCy NER pass for richer dynamic-entity detection is default-off and not bundled: with spaCy (or its model) absent, CacheAligner uses the regex detector only and degrades silently (covered by a fake-spaCy test). The regex detector's epoch (10-13 digit) and semantic-version patterns can in rare cases flag a stable line that merely contains such a number, moving it to the tail and shrinking the cacheable prefix -- a conservative miss, never data loss.

**Suggested next step**: If prefix-stability regressions appear, ship the spaCy extra on a documented install path or tighten the epoch/version patterns with surrounding-context anchors; measure the prefix-hit rate.

**Severity**: Low (regex path is lossless and deterministic; NER is an opt-in enhancement)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-8`.

- **Migrated from**: v3.2#DF-v32hr-9 (reason: user-deferred); original `v3.2#DF-v32hr-9`, section `Open Items`.

#### Original source: DF-v32hr-9 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-9 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 4

**Plan reference**: T012/T013 (runtime) vs T008 (CacheAligner)

**Reason**: Phase 4 wired `compress(messages)` and `compress_output(text)` through ContentRouter, but CacheAligner (KV-cache system-prompt stabilization) is NOT applied anywhere in the runtime path: the hook compresses Bash *output* (not system prompts) and `compress(messages)` routes content without a CacheAligner pass over system messages. CacheAligner remains a standalone, individually-callable transform.

**Suggested next step**: Apply CacheAligner to system/leading messages inside `compress(messages)` (or a dedicated `align_system_prompt` seam) when a runtime that controls the system prompt exists; the PreToolUse-hook path legitimately does not touch system prompts, so this is a messages-API enhancement, not a hook gap.

**Severity**: Low (CacheAligner is complete and tested in isolation; the cache-hit benefit is unrealized until wired)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-9`.

- **Migrated from**: v3.2#DF-v32hr-12 (reason: user-deferred); original `v3.2#DF-v32hr-12`, section `Open Items`.

#### Original source: DF-v32hr-12 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-12 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 5

**Plan reference**: T016 (accuracy harness)

**Reason**: The harness proves "accuracy preserved" via deterministic STRUCTURAL fidelity (CCR round-trip completeness, code signature preservation) rather than a live-LLM semantic benchmark (headroom's `eval.yml` runs GSM8K / TruthfulQA / SQuAD / BFCL through a model). This is a deliberate scope choice: a live model call is non-deterministic, slow, and an outbound call this repo refuses to add, and the plan's T016 explicitly specifies deterministic structural-fidelity checks. The trade-off: the gate proves compression is lossless/reversible and structure-preserving, but does not measure whether a model *answers* as well on compressed context.

**Suggested next step**: A true semantic accuracy benchmark would require a live (or local) model harness and a QA dataset; defer indefinitely unless an offline local-model eval becomes worthwhile. The structural gate is the mandated, sufficient guard for shipping aggressive ratios (comparison Section 13).

**Severity**: Low (structural fidelity is exact and is the mandated pre-aggressive-ratio guard; semantic benchmark is an optional future addition)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-12`.

- **Migrated from**: v3.2#DF-v32hr-13 (reason: user-deferred); original `v3.2#DF-v32hr-13`, section `Open Items`.

#### Original source: DF-v32hr-13 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-13 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 5

**Plan reference**: T016/T017 (effectiveness gate)

**Reason**: The effectiveness floor gates CHARACTER-length reduction, not token reduction, because token counts depend on whether `tiktoken` (and its cached vocab) is available offline -- a value that varies across environments and would make the floor flaky. The token ratio is computed and reported but never gated. Consequence: a hypothetical regression that preserves character reduction while worsening *token* savings would not trip the gate.

**Suggested next step**: If a token-savings regression mode ever matters, add a separate token-reduction floor guarded behind `using_accurate_counter()` (skip the token assertion in fallback mode). Char reduction is a faithful, deterministic proxy for now.

**Severity**: Low (char reduction tracks token reduction closely for these content types; the headline token number is reported, just not gated)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-13`.

- **Migrated from**: v3.2#DF-v32hr-14 (reason: user-deferred); original `v3.2#DF-v32hr-14`, section `Open Items`.

#### Original source: DF-v32hr-14 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-14 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 6

**Plan reference**: T019 (ML token-dropper) vs T009 (ContentRouter)

**Reason**: The ML token-dropper is a standalone, individually-callable transform (`transforms.drop_tokens`); it is NOT wired into the default `ContentRouter`/`compress`/`compress_output` runtime path, which still passes free text/prose through unchanged. So even a user who installs the `[ml]` extra + places the public weights + sets `enabled=True` gets no automatic free-text compression in the runtime today -- they must call `drop_tokens` directly. This deliberately mirrors the CacheAligner situation (DF-v32hr-9): a lossy default belongs off the auto pipeline until a runtime owner opts it in explicitly, and the Phase 5 gate guards structural fidelity, not free-text drops.

**Suggested next step**: Add an opt-in seam in `compress_output`/`route` (behind an explicit config flag, default-off) that runs `drop_tokens` over `TEXT`-classified segments when the user has enabled the ML path; gate the default ratio against a free-text fidelity measure before any default-on consideration.

**Severity**: Low (the capability exists and is fully tested in isolation; only the runtime auto-wiring is deferred, by design)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-14`.

- **Migrated from**: v3.2#DF-v32hr-15 (reason: user-deferred); original `v3.2#DF-v32hr-15`, section `Open Items`.

#### Original source: DF-v32hr-15 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32hr-15 - MIGRATED to v4.13 (AR-24)

**Category**: DF

**Source phase**: adoption-headroom Phase 6

**Plan reference**: T019 (ML token-dropper)

**Reason**: The port scores and drops at WHITESPACE-WORD granularity rather than the upstream Kompress sub-word-token granularity. This was chosen for clean, dependency-light reconstruction (a word rebuilds to readable text without a sub-word detokenizer, and surviving-run spacing is preserved) and so the drop unit is the unit a reader sees. The trade-off: a coarser drop unit than sub-word scoring, and the model's sub-word importance scores are mean-pooled up to their covering word (`_pool_subword_scores`).

**Suggested next step**: If finer-grained dropping proves worthwhile, add a sub-word reconstruction path (needs the tokenizer's detokenizer and offset handling) and measure the ratio/fidelity effect with a free-text eval fixture before switching the default granularity.

**Severity**: Low (word-level drop is faithful to the importance signal and reconstructs cleanly; sub-word is an optional refinement)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32hr-15`.

- **Migrated from**: v3.2#MT-v32hr-1 (reason: user-deferred); original `v3.2#MT-v32hr-1`, section `Open Items`.

#### Original source: MT-v32hr-1 - MIGRATED to v4.13 (AR-24)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: MT-v32hr-1 - MIGRATED to v4.13 (AR-24)

**Category**: MT

**Source phase**: adoption-headroom Phase 6

**Plan reference**: T020 (tests)

**Reason**: The live ONNX inference glue cannot be exercised in CI: `onnxruntime`, `numpy`, `tokenizers`, and the public weights are all absent in the dev/CI environment, so `_onnx_word_scores` (real session.run + tokenizer encode) and the scorer returned by `build_onnx_scorer`'s all-present branch are never *called* under test. The two `_reduce_logits_to_importance` tests skip via `importorskip("numpy")`; `build_onnx_scorer`'s guard branches (each dep absent, weights absent, load failure, all-present-returns-callable) ARE covered with `sys.modules` stubs, and the entire drop/selection/reconstruction/pooling logic is covered through an injected scorer. So the untested surface is only the thin numpy/onnxruntime/tokenizers call-glue, which degrades safely (`_safe_scores` wraps it; any fault returns the original text).

**Suggested next step**: Add an opt-in CI lane (or a documented local dev test) that installs the `[ml]` extra and a tiny fixture ONNX importance model + tokenizer to exercise the live inference path end-to-end.

**Severity**: Low (pure logic fully tested; the untested glue is thin, uses documented APIs, and fails safe to identity)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `MT-v32hr-1`.

- **Migrated from**: v3.19#DF-3 (reason: user-deferred); original `v3.19.2#DF-3`, section `v3.19.2`.

#### Original source: DF-3 - Semantic reformatters cover a named short list, not ~60 command handlers - MIGRATED to v4.13 (AR-24)

- **Source phase**: Phase 4 (compressor and hook depth, task 4.3)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md` (Phase 4 / semantic reformatters)
- **Why deferred**: A dedicated command-output compressor in this class ships on the order of 60 handlers. Matching that set in one patch would dominate the release and still miss the long tail. This release ships git status, pytest/vitest/jest failures-only, and ruff/eslint/tsc grouped-by-file, each with a 60% token-reduction fixture, and documents the rest as a coverage gap.
- **Suggested next step**: add handlers only for commands whose fixtures miss the 60% bar in real sessions; do not chase handler-count parity.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-24`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.19.2`, section `v3.19.2`, and original ID `DF-3`.

### AR-25: Skill-scanner coverage limits

- **Current state**: a thin pattern set per class, module-level taint tracking, and 12 starter `.yar` rules with 5 offline OSV advisories.
- **Owner and next step**: scanner owner; expand or accept as a documented limit.
- **Historical transfer note**: v3.0#DF-v30-1, DF-v30-2, and DF-v30-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.0#DF-v30-1 (reason: user-deferred); original `v3.0#DF-v30-1`, section `Open Items`.

#### Original source: DF-v30-1 - MIGRATED to v4.13 (AR-25)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-1 - MIGRATED to v4.13 (AR-25)

**Category**: DF

**Source phase**: Phase 6

**Plan reference**: T027 (static analyzers)

**Reason**: The `nexus-skill-scanner` ships the highest-signal patterns for each of the 15 static classes (1-13, 15-16), not the full ~64-pattern surface described in the comparison. This is the deliberate "start with the highest-signal classes and grow the pattern set per release" approach from `comparison-skillspector.md` Section 13. Coverage is sufficient to score the planted-malicious fixture CRITICAL and pass the clean catalog, but individual classes (e.g. memory poisoning, tool misuse, output handling) have a thin pattern set.

**Suggested next step**: Grow the per-class pattern set in subsequent releases, adding eval fixtures per new pattern; prioritize classes by observed catalog/third-party false-negative rate. Class 14 (YARA) and the live OSV.dev lookup are scheduled for Phase 7, not gaps.

**Severity**: Low (by-design incremental coverage; gate + semantic skill compensate)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-25`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-1`.

- **Migrated from**: v3.0#DF-v30-2 (reason: user-deferred); original `v3.0#DF-v30-2`, section `Open Items`.

#### Original source: DF-v30-2 - MIGRATED to v4.13 (AR-25)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-2 - MIGRATED to v4.13 (AR-25)

**Category**: DF

**Source phase**: Phase 6

**Plan reference**: T027 (taint tracking)

**Reason**: Class 13 taint tracking is a module-scoped over-approximating heuristic: it marks names assigned from a tainted source (os.environ / os.getenv / input / sys.stdin) and flags them reaching a code-exec sink (HIGH) or process-exec sink (MEDIUM). It is flat (not intra-procedural / flow-sensitive), so it can over- or under-approximate across function boundaries. Severities are capped so the heuristic cannot trip the HIGH gate except on the genuinely dangerous input->exec/eval flow (which the catalog has none of).

**Suggested next step**: If false positives/negatives emerge in practice, replace with a flow-sensitive intra-procedural dataflow pass (per-function def-use chains). Add adversarial taint fixtures.

**Severity**: Low (conservative severities; bounded blast radius)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-25`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-2`.

- **Migrated from**: v3.0#DF-v30-3 (reason: user-deferred); original `v3.0#DF-v30-3`, section `Open Items`.

#### Original source: DF-v30-3 - MIGRATED to v4.13 (AR-25)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-3 - MIGRATED to v4.13 (AR-25)

**Category**: DF

**Source phase**: Phase 7

**Plan reference**: T033 / T034 (optional modules)

**Reason**: The two Phase 7 optional modules ship deliberately minimal starter content: the signature engine bundles 12 re-authored rules across 3 files (cryptominers, reverse-shell/exploit cradles, web shells), and the offline OSV advisory DB seeds 5 well-documented public advisories. Both are sufficient to demonstrate detection and graceful degradation, but neither is comprehensive coverage of its class. This mirrors the DF-v30-1 "highest-signal first, grow per release" philosophy.

**Suggested next step**: Grow the signature rule set (add a generic-malware/loader file and per-language web-shell coverage) and expand the offline advisory seed per release, each with a paired test fixture; the live `--osv` lookup already supplements the offline DB when enabled.

**Severity**: Low (by-design incremental coverage; modules are opt-in and adjudicated by the skill)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-25`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-3`.

### AR-27: Code-search covers 12 languages

- **Current state**: `extensions/nexus-code-search` still has 12 extractors.
- **Owner and next step**: code-search owner; add languages on demand.
- **Historical transfer note**: v3.0#DF-v30-5 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.0#DF-v30-5 (reason: user-deferred); original `v3.0#DF-v30-5`, section `Open Items`.

#### Original source: DF-v30-5 - MIGRATED to v4.13 (AR-27)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-5 - MIGRATED to v4.13 (AR-27)

**Category**: DF

**Source phase**: Phase 9

**Plan reference**: T040 (Swift/Kotlin extractors)

**Reason**: Phase 9 shipped the recommended mobile extractor batch (Swift + Kotlin), raising code-search language coverage 10 -> 12, each at 100% recall / 100% precision on its eval fixture. This carries forward the remaining DF-v24-7 scope: ~8 languages are still uncovered (Scala, Bash/shell, Lua, Perl, Objective-C, Dart, Haskell, etc.), and framework extractors (e.g. iOS/SwiftUI or Android/Jetpack route / component resolution) plus parameter-node parity were not in scope for the mobile batch.

**Suggested next step**: Implement the next demand batch following the per-language extractor pattern under `extensions/nexus-code-search/.../extraction/languages/`, each with an eval fixture clearing the 80% recall gate and unit tests. Note for grammar pinning: newer tree-sitter grammars version their own package independently of the core's <0.26 ceiling (swift at 0.7.x, kotlin at 1.x), so verify ABI compatibility with the installed core before pinning rather than assuming a <0.26 marker. Pick up at the next version's /generate-plan.

**Severity**: Low (incremental coverage; 12 of ~20 languages shipped)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-27`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-5`.

### AR-32: Usage-monitor extension test coverage

- **Current state**: Claude `recommendations.ts`, `warningView`, and `extension.ts` lack tests; `claude-usage-monitor` has no coverage threshold while the Codex and Cursor monitors do; no live render check of the theme icon; the Codex `icon.png` is still the reconstructed 512x512 asset.
- **Owner and next step**: extensions owner; add the tests and threshold, reuse the installed-VSIX method that closed v4.10 MT-2, and swap or accept the icon.
- **Historical transfer note**: v3.14.0#MT-1, v3.14.4#MT-1, v3.14.4#DF-1, v3.14.5#MT-1, and v3.17.0#MT-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.14#MT-1-v3145 (reason: user-deferred); original `v3.14.5#MT-1`, section `v3.14.5`.

#### Original source: MT-1-v3145 - Usage-monitor extensions' UI orchestration remains partially host-only - MIGRATED to v4.13 (AR-32)

- **Source phase**: v3.14.5 Phases 4-5 (carries the v3.14.4 MT-1)
- **Plan reference**: Phase 7.2
- **Reason**: Phases 4-5 ADDED Vitest coverage to both extensions - Codex 38 tests (the `wham/usage` window-alias mapper, the actionable empty-state banner, the status-bar priority constants + compact label) and Claude 5 (priority constants + compact label) - closing the largest prior gaps. What remains host-only (not unit-testable without a live VS Code extension host): the actual webview rendering (dashboard HTML, the theme-adaptive tab icon), the manual-entry input-box flow end to end, and the live status-bar left-to-right ordering. These are covered by the HO-1 manual smoke checklist below.
- **Suggested next step**: a `@vscode/test-electron` integration harness if UI-render regressions ever recur; today the unit tests plus the manual smoke checklist are proportionate.

**Original source identity**: `v3.14.5#MT-1` in `v3.14.5`; normalized stable ID `MT-1-v3145` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.5`, section `v3.14.5`, and original ID `MT-1`.

- **Migrated from**: v3.14#DF-1-v3144 (reason: user-deferred); original `v3.14.4#DF-1`, section `v3.14.4`.

#### Original source: DF-1-v3144 - Codex extension `icon.png` reconstructed from `codex-white.png`, not the user's `codex-2048x2048.png` - MIGRATED to v4.13 (AR-32)

- **Source phase**: v3.14.4 Phase 2
- **Plan reference**: Phase 2 sub-task 2.2 ("Save the two provided images")
- **Reason**: The user referenced two brand assets: `codex-white.png` (found in the user's Downloads, 640x640 white cloud silhouette with the `>_` knocked out) and `codex-2048x2048.png` (the full-color Marketplace icon). Only `codex-white.png` was on disk; `codex-2048x2048.png` could not be located anywhere on the machine, and no SVG rasterizer (ImageMagick / rsvg / cairosvg / inkscape) was available to synthesize one. `icon.png` (512x512) was therefore reconstructed with Pillow from `codex-white.png`'s exact silhouette: the cloud body filled with a periwinkle->`#5244BB` vertical gradient and the `>_` knockout painted black. The result is a faithful match to the described design, but it is a reconstruction rather than the user's original file.
- **Suggested next step**: If the user has the exact `codex-2048x2048.png`, drop it in as `extensions/codex-usage-monitor/icon.png` (a one-file swap; the manifest already points at `icon.png`, so no code change). By-design acceptable otherwise - the reconstructed icon is on-brand and functional.

**Original source identity**: `v3.14.4#DF-1` in `v3.14.4`; normalized stable ID `DF-1-v3144` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.4`, section `v3.14.4`, and original ID `DF-1`.

- **Migrated from**: v3.14#MT-1-v3144 (reason: user-deferred); original `v3.14.4#MT-1`, section `v3.14.4`.

#### Original source: MT-1-v3144 - Claude extension UI orchestration remains unit-test-light - MIGRATED to v4.13 (AR-32)

- **Source phase**: v3.14.4 Phase 1
- **Plan reference**: Phase 1 sub-task 1.4 (Testing and Stabilization)
- **Reason**: Removing the Codex provider dropped the Vitest suite from 35 tests to 3; the survivors cover `describeProviderError` and provider identity. The UI orchestration files (`statusBarManager`, `dashboardPanel`, `settingsPanel`, `warningView`, `extension`) and the `recommendations` engine have no direct unit tests. This is a pre-existing gap for a VS Code extension whose bulk is webview/status-bar UI (hard to unit-test without a VS Code host), not a regression introduced by the de-Codex work - the removed tests exercised Codex code that moves to the new extension in Phase 2.
- **Suggested next step**: In Phase 2, port the recommendations/mapping-style tests to the new Codex extension and consider adding pure-function unit tests for the shared `recommendations.ts` Claude branches (they are host-independent). Not a release blocker.

**Original source identity**: `v3.14.4#MT-1` in `v3.14.4`; normalized stable ID `MT-1-v3144` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.4`, section `v3.14.4`, and original ID `MT-1`.

- **Migrated from**: v3.14#MT-1-v3140 (reason: user-deferred); original `v3.14.0#MT-1`, section `v3.14.0`.

#### Original source: MT-1-v3140 - Extension UI modules have no automated tests - MIGRATED to v4.13 (AR-32)

- **Source phase**: Phase 1 (1.4)
- **Plan reference**: Phase 1 stability gate scoped automated tests to "provider unit tests"
- **Reason**: `statusBarManager.ts`, `dashboardPanel.ts`, `warningView.ts`, `settingsPanel.ts`, and `extension.ts` render VS Code UI and require the extension host, so they are validated by `tsc` compile and manual run only. The provider data layer, the Codex payload mapper, the error resolver, the provider factory, and the Codex recommendation branches ARE unit-tested (35 Vitest tests). This matches the pre-existing state (the extension had no tests before this phase).
- **Suggested next step**: Add a VS Code integration test harness (`@vscode/test-electron`) if the UI surface grows, or extract more pure logic behind the vscode boundary; not warranted for the current thin UI branches.

**Original source identity**: `v3.14.0#MT-1` in `v3.14.0`; normalized stable ID `MT-1-v3140` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.0`, section `v3.14.0`, and original ID `MT-1`.

- **Migrated from**: v3.17#MT-1-v3170 (reason: user-deferred); original `v3.17.0#MT-1`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: MT-1-v3170 - OPEN (pre-existing coverage debt): Claude Usage Monitor lacks an extension-wide coverage baseline - MIGRATED to v4.13 (AR-32)

- **Target file**: `extensions/claude-usage-monitor/src/`, `extensions/claude-usage-monitor/vitest.config.ts`
- **Source phase**: v3.17.0 Phase 5, sub-tasks 5.2 and 5.4
- **Plan reference**: 5.4 requires extension coverage of at least 80 percent.
- **Reason it is open**: the new autonomy state machine reaches 91.66 percent line coverage and is enforced at that explicit feature boundary, but enabling coverage over every imported Claude monitor module measured only 14.07 percent lines because the pre-existing provider, store, recommendation, type, and status-bar modules have little or no test coverage. Expanding those legacy tests is unrelated to the autonomy surface and would materially widen Phase 5.
- **Suggested next step**: add tests for the legacy Claude monitor modules in risk order, then remove the `coverage.include` feature boundary once the whole extension clears the same 80 percent line and statement floor that the Codex monitor already meets.

**Original source identity**: `v3.17.0#MT-1` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `MT-1-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `MT-1`.

### AR-44: The Cursor usage-monitor live visual smoke was never run

- **Current state**: `cursor-usage-live-smoke.md` has no recorded result.
- **Owner and next step**: maintainer on a live Cursor host; run status bar, three bars, and three themes and record the result.
- **Historical transfer note**: v3.15.9#QG-5 and v3.15.12#QG-4 (Cursor half) on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#QG-v31512-5 (reason: user-deferred); original `v3.15.12#QG-v31512-5`, section `v3.15.12 - cursor live transport and github billing monitor`.

#### Original source: QG-v31512-5 - Cursor on-demand bar extends the outstanding live visual smoke

| **QG-4 / QG-5 / MT-5** - MIGRATED to v4.13 (AR-44) | Maintainer-only interactive smokes. **Scope widened this version**: QG-4/QG-5 now also cover the Cursor on-demand bar (currency labels, shared-scope note, over-limit clamp, dropped-bar fallback), and MT-5 now also covers the renamed GitHub surfaces and the new Authorization panel section |

**Normalization, 2026-10-09 (v4.13.11 T006)**: The table adds a real Cursor residual: currency labels, the shared-scope note, the over-limit clamp, and the dropped-bar fallback. The original `v3.15.12#QG-4`, `v3.15.12#QG-5`, and `v3.15.12#MT-5` references and all GitHub clauses are retained in the source row above; this structural heading uses a distinct ID to preserve that widened source without colliding with v3.15.9 QG-5. GitHub-only renamed surfaces and Authorization-panel checks were superseded by withdrawal of that monitor in v3.18.2; the Cursor smoke remains open under AR-44 until its canonical copy preserves the widened scope.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-44`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.12`, section `v3.15.12 - cursor live transport and github billing monitor`, and original ID `QG-v31512-5`.

- **Migrated from**: v3.15#QG-5 (reason: user-deferred); original `v3.15.9#QG-5`, section `v3.15.9 - cross-provider-routing-and-cursor-usage-monitor`.

#### Original source: QG-5 - Cursor live visual smoke remains unobserved

**QG-5 (NEW, open at release): the Cursor live smoke was NOT executed for v3.15.9.** The checklist at `docs/v3/v3.15/development/cursor-usage-live-smoke.md` requires a human driving a real Cursor instance to confirm the status bar, meters, dashboard, threshold warning, and theme rendering; it cannot be performed by an automated agent and no local Cursor host ran it before the tag. The maintainer authorized the release to proceed without it (2026-08-04). What IS proven for the Cursor monitor is the automated surface: 132 extension tests green with coverage thresholds held, packaging verified in CI, and installer host isolation asserted by test. What is NOT proven is the rendered visual result on a live Cursor host. Close QG-5 by running the checklist post-release and recording the outcome here; treat any finding as a v3.15.10 fix candidate. This entry exists so the release record does not imply a verification that never happened. - MIGRATED to v4.13 (AR-44)

**Normalization, 2026-10-09 (v4.13.11 T006)**: Converted the authoritative prose record to a supported heading. Keep the full live-host checklist obligation open under AR-44 until its canonical source copy is verified.


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-44`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.9`, section `v3.15.9 - cross-provider-routing-and-cursor-usage-monitor`, and original ID `QG-5`.

### AR-49: `@vscode/vsce` transitive deprecation warnings

- **Current state**: still present in all three extension lockfiles; `npm audit` is clean.
- **Owner and next step**: extensions owner; re-check at the next toolchain bump or accept as upstream-bounded.
- **Historical transfer note**: v3.15.9#WN-4 on 2026-09-29 (reason: upstream, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#WN-4 (reason: user-deferred); original `v3.15.9#WN-4`, section `v3.15.9 - cross-provider-routing-and-cursor-usage-monitor`.

#### Original source: WN-4 - Latest VS Code packaging toolchain emits two transitive deprecation notices

- **Source phase**: v3.15.9 Phase 4.1 - Cursor extension scaffold
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` (sub-task 4.1 / T020)
- **Reason**: A clean `npm ci` installs the latest `@vscode/vsce` dependency tree and warns that transitive `whatwg-encoding@3.1.1` and `prebuild-install@7.1.3` are deprecated. Neither package is a direct dependency, `npm audit` reports zero vulnerabilities, and replacing them locally would require overriding the supported packaging toolchain.
- **Suggested next step**: Re-run `npm ci` when `@vscode/vsce` updates in Phase 5/6; accept the upstream warning while audit remains clean, and remove this item when the transitive packages disappear.

No new Phase 4 implementation, regression, missing-test, or quality-gate gap remains.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-49`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.9`, section `v3.15.9 - cross-provider-routing-and-cursor-usage-monitor`, and original ID `WN-4`.

### AR-52: contextmap detectors deferred

- **Current state**: TypeORM, Drizzle, ActiveRecord, GORM, Vue, and Svelte are still listed as deferred.
- **Owner and next step**: code-search owner; one detector plus fixture per target, on demand.
- **Historical transfer note**: v3.15.1#DF-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-3-v3151 (reason: user-deferred); original `v3.15.1#DF-3`, section `v3.15.1 - adoption-codesight`.

#### Original source: DF-3-v3151 - Additional frameworks / ORMs / component libs / event patterns deferred (explicit coverage, not silent) - MIGRATED to v4.13 (AR-52)

- **Source phase**: v3.15.1 adoption-codesight Phase 2 (2.1) + Phase 3 (3.1, 3.2)
- **Plan reference**: Phase 2.1 / Phase 3.1 / Phase 3.2 ("verifying each with a fixture before adding the next ... Do NOT attempt every framework at once")
- **Reason**: per the plan's incremental posture, each detector lands with its own fixture rather than all at once. Currently covered:
    - **Routes**: FastAPI, Flask, Django, Express (via the existing resolvers). Deferred: Hono / Fastify / Next / NestJS (TS), Gin (Go), Rails (Ruby), Spring Boot (Java), Laravel (PHP) - each needs a new extraction-time resolver + fixture.
    - **ORM schema**: SQLAlchemy, Django ORM, Prisma. Deferred: TypeORM, Drizzle (TS), ActiveRecord (Ruby), GORM (Go) - decorator/call-based, each needs its own detector + fixture.
    - **Components**: React (props via destructuring or the resolved prop type). Deferred: Vue, Svelte. Design-system-primitive auto-filtering is also deferred.
    - **Events**: declaration-strong signals (Celery task decorators, BullMQ `new Queue/Worker`, Kafka, `new EventEmitter`). Deferred: invocation-only patterns (`.delay(`, `.emit(`, Redis `.publish(`/`.subscribe(`) - too common to detect without false positives.
- **Suggested next step**: add a detector + fixture per additional target in a follow-on pass. The map's section renderers and the accuracy harness already handle any new detector's output generically.

**Original source identity**: `v3.15.1#DF-3` in `v3.15.1 - adoption-codesight`; normalized stable ID `DF-3-v3151` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-52`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.1`, section `v3.15.1 - adoption-codesight`, and original ID `DF-3`.

### AR-58: The installers still cite the pre-archive path of the install-selection contract

- **Current state**: comments in `scripts/installer.sh` and `scripts/installer.ps1` (three lines) still name `docs/releases/v3/v3.16/development/install-selection-contract.md`, which now lives at `docs/archives/v3/v3.16/development/install-selection-contract.md`. They were deliberately not repointed: the `distribution` handbook binds the installers' bytes in `docs/handbooks/_sources/distribution/evidence.json`, so any edit makes `check_handbooks.py` report stale evidence until a content, build, and rendered review is re-run.
- **Owner and next step**: handbook owner; repoint the three comments at the next distribution-handbook refresh and record new evidence.
- **Historical transfer note**: raised by the 2026-09-29 archive pass (reason: repointing requires a handbook evidence refresh outside this change).

### AR-59: Extension devDependencies are declared as caret ranges

- **Current state**: the three usage-monitor extensions (`claude-usage-monitor`, `codex-usage-monitor`, `cursor-usage-monitor`) declare 11, 11, and 7 devDependencies as caret ranges (re-counted on `develop` on 2026-09-30). The immediate risk is bounded: all three have a `package-lock.json`, CI installs with `npm ci`, which resolves from the lock and not from the ranges, and each `.npmrc` sets `save-exact=true` and `min-release-age=2`, so new dependencies are recorded exactly and the range surface does not grow. Pinning the existing ranges was deliberately not done when the supply-chain hardening landed, because it changes what a fresh resolve installs, and an unverified pin breaks builds for reasons unrelated to the change that caused it.
- **Owner and next step**: extensions owner; pin each manifest to the version its lockfile already resolves, one extension at a time, running that extension's build and Vitest suite before moving to the next.
- **Historical transfer note**: recovered on 2026-09-30 from an unmerged local draft of the v4.1.0 Pi-adoption ledger (source: comparison item A3, supply-chain install hardening). The archived v4.1 ledger does not carry it (reason: still open; the manifest, lockfile, and `.npmrc` facts were re-verified on `develop` on 2026-09-30).

### AR-60: Extension build workflows install with lifecycle scripts enabled

- **Current state**: `.github/workflows/claude-usage-monitor.yml` (line 46), `codex-usage-monitor.yml` (line 46), and `cursor-usage-monitor.yml` (line 52) run plain `npm ci`, not `npm ci --ignore-scripts` (line numbers as of 2026-09-30). The flag was held back for a specific reason: `ttf2woff2` is a native module that commonly relies on an install-time build step, so disabling lifecycle scripts could break icon generation in a way that only surfaces in CI. It is declared in all three manifests (the original draft said two of three; re-counted 2026-09-30). `.github/workflows/npm-audit.yml` does use `--ignore-scripts`, safely, because it installs only to read the dependency tree and never builds.
- **Owner and next step**: extensions owner; run each extension's full build locally with `npm ci --ignore-scripts` and confirm the VSIX is byte-comparable. Where a native module genuinely needs its install step, add an explicit lifecycle-script allowlist rather than dropping the flag for the whole tree.
- **Historical transfer note**: recovered on 2026-09-30 from the same unmerged draft as AR-59 (source: comparison item A3) (reason: still open; the workflow lines and manifest facts were re-verified on `develop` on 2026-09-30).

### Hooks and notifications

### AR-46: The Windows notification linger was never measured

- **Current state**: the default is still 5500 ms in `catalog/hooks/_notify_common.sh` and its `.ps1` sibling.
- **Owner and next step**: maintainer on a live Windows 10/11 desktop; measure the shortest safe `NEXUS_NOTIFY_LINGER_MS`.
- **Historical transfer note**: v3.15.10#DF-16 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-16 (reason: user-deferred); original `v3.15.10#DF-16`, section `v3.15.10 - end-of-task-agent-behavior`.

#### Original source: DF-16 - Windows notification linger remains unmeasured

- **DF-16 - Windows notification linger not shortened.** The 5.5-second post-`ShowBalloonTip` sleep keeps a `powershell.exe` alive per notification. Disposing a `NotifyIcon` early can cancel a queued toast on Windows 10/11, and the shortest safe value requires observing a rendered toast on a live desktop, which no test here can do. Exposed as `NEXUS_NOTIFY_LINGER_MS` to be measured rather than guessed. - MIGRATED to v4.13 (AR-46)

**Normalization, 2026-10-09 (v4.13.11 T006)**: Converted the authoritative bullet to a supported gap heading. The complete original source paragraph is retained above. The residual belongs to AR-46; the canonical copy must be verified before a parsed forward-migration marker is added.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-46`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.10`, section `v3.15.10 - end-of-task-agent-behavior`, and original ID `DF-16`.

### AR-48: `session-summary.sh` labels projects by the working directory

- **Current state**: still `basename "$(pwd)"`.
- **Owner and next step**: hooks maintainer; derive the name from the git top-level, as the notify hooks do, in both siblings.
- **Historical transfer note**: v3.15.10 (session-summary advisory) on 2026-09-29 (reason: still open).

### Documentation

### AR-29: `README_zh.md` needs a full re-translation

- **Current state**: 271 lines against the English README's 792.
- **Owner and next step**: docs owner.
- **Historical transfer note**: v3.8#WN-v38-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.8#WN-v38-1 (reason: user-deferred); original `v3.8#WN-v38-1`, section `Open Items`.

#### Original source: WN-v38-1 - MIGRATED to v4.13 (AR-29)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v38-1 - MIGRATED to v4.13 (AR-29)

**Category**: WN

**Source**: release prep (carried from WN-v37-3)

**Reason**: The `README_zh.md` global-install count line was refreshed to the current catalog counts, but the rest of the Chinese README has not had a full re-translation pass against the current English README.

**Suggested next step**: Do a full `README_zh.md` re-translation pass in a future docs sweep; the counts and install flow are now correct.

**Severity**: Low (secondary-language doc; counts + install flow correct; English README and all machine-read registries are authoritative).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-29`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.8`, section `Open Items`, and original ID `WN-v38-1`.

### AR-31: `docs/specs/README.md` still describes "legacy installer copy blocks"

- **Current state**: the stale framing moved there from AGENTS.md.
- **Owner and next step**: docs owner; say that Claude has the one custom installer block and every other platform goes through the integration registry.
- **Historical transfer note**: v3.14.5#DF-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.14#DF-3-v3145 (reason: user-deferred); original `v3.14.5#DF-3`, section `v3.14.5`.

#### Original source: DF-3-v3145 - Pre-existing: AGENTS.md "legacy installer copy blocks" framing predates the registry migration - MIGRATED to v4.13 (AR-31)

- **Source phase**: v3.14.5 Phase 7 (observed during the terminal refactor audit; pre-existing, NOT caused by this release)
- **Plan reference**: Phase 7.1 (flagged the "legacy 4 copy blocks" line as stale prose to update)
- **Reason**: AGENTS.md (lines ~381/389) describes Codex / Gemini / Copilot as installing via "legacy installer copy blocks", but `install_global` in both installers routes every platform except Claude through `invoke_registry_platform` -> `runner.py` (the integration registry). `git show develop:scripts/installer.sh` confirms this was already true on `develop`, so the framing was stale BEFORE v3.14.5 - this release did not change the install mechanism. Per the "every changed line traces to the request; no out-of-scope cleanup" rule, rewriting the canonical historical architecture prose (intertwined with the v2.1.0/v2.2.0 migration notes + DF-001) was judged out of scope for a release that did not touch it, and higher-risk than leaving it. The genuinely-new fact (the contract-freshness gate) WAS documented. The plan's 7.1 premise that "this release changed the fact" was incorrect (recorded as the Phase 7 DEVIATION in the session history).
- **Suggested next step**: a dedicated AGENTS.md doc-accuracy pass to reframe "Original 4 (legacy copy blocks) / Extended 4" around the current reality (Claude = the one bespoke installer block; every other platform = the integration registry), keeping the separate permissions "legacy 4" grouping intact.

**Original source identity**: `v3.14.5#DF-3` in `v3.14.5`; normalized stable ID `DF-3-v3145` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-31`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.5`, section `v3.14.5`, and original ID `DF-3`.

### AR-35: Optional provider failover and settlement reference for `multi-provider-ai`

- **Current state**: never written.
- **Owner and next step**: catalog maintainer; write it or close as won't-do.
- **Historical transfer note**: v3.14.0#DF-3 on 2026-09-29 (reason: optional, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.14#DF-3-v3140 (reason: user-deferred); original `v3.14.0#DF-3`, section `v3.14.0`.

#### Original source: DF-3-v3140 - P1: provider failover / settlement invariants as multi-provider-ai reference content - MIGRATED to v4.13 (AR-35)

- **Source phase**: comparison scope (out of the seven selected v3.14 candidates); the Definition of Done defers it here
- **Plan reference**: plan "Definition of Done" ("P1 (provider-routing reference content) is deferred to `docs/v3/v3.14/known-gaps.md` as an optional follow-up")
- **Reason**: codex-lb's provider failover / settlement invariants (from its load-balancer product) are a different product category from Nexus-Hub's catalog and were not selected for adoption. They survive only as OPTIONAL reference content for the `multi-provider-ai` skill.
- **Suggested next step**: If provider-routing reference content is wanted later, distill the failover / settlement invariants into `multi-provider-ai` as a body-only reference (skill-native, no external dependency), in a separate version.

**Original source identity**: `v3.14.0#DF-3` in `v3.14.0`; normalized stable ID `DF-3-v3140` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-35`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.0`, section `v3.14.0`, and original ID `DF-3`.

### AR-39: The official Claude plugin directory submission was never made

- **Current state**: README still says "If Anthropic later lists..."; the submission draft is `docs/archives/v3/v3.20/development/claude-marketplace-submission.md`.
- **Owner and next step**: maintainer (manual form); submit, then add the install line to the README.
- **Historical transfer note**: v3.20.3#DF-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.20#DF-2-v3203 (reason: user-deferred); original `v3.20.3#DF-2`, section `v3.20.3`.

#### Original source: DF-2-v3203 - Official Claude plugin directory listing not submitted - MIGRATED to v4.13 (AR-39)

- **Source phase**: Phase 5 - Official Claude plugin marketplace listing
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md` (sub-task 5.1)
- **Reason**: The phase prepares the package and the maintainer packet. Live Anthropic process (fetched 2026-08-24) is the [plugin directory submission form](https://clau.de/plugin-directory-submission), not a PR to `anthropics/claude-plugins-official`. Opening either from the implement loop is out of scope.
- **Suggested next step**: Maintainer submits the form using `docs/v3/v3.20/development/claude-marketplace-submission.md`. After listing, add the `@claude-plugins-official` install line to README.

**Original source identity**: `v3.20.3#DF-2` in `v3.20.3`; normalized stable ID `DF-2-v3203` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-39`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.20.3`, section `v3.20.3`, and original ID `DF-2`.

### Maintainer decisions pending

### AR-37: Conditional adoption candidates awaiting build-or-decline

- **Current state**: visual-brainstorming server, portable YAML orchestration engine, after-the-fact intent recovery in `session-query`, the quality-gate naming note, remaining worker-check hooks, and a durable prior-cycle review-signal store. None was built; none has a decline record.
- **Owner and next step**: maintainer; record a decline (for example a reverse-engineering-matrix row) or scope a plan.
- **Historical transfer note**: v3.0#DF-v30-9, v3.6 to v3.9#DF-v36-2, v3.9#DF-v39-nomistakes-1, v3.10#DF-v310-ruflo-A6, v3.10#DF-v310-ruflo-A10-rest, and v3.15.7#DF-6 on 2026-09-29 (reason: conditional, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

**Current residual from `v4.0.0#MT-1`**: Make an explicit build-or-decline disposition for the optional mechanically checkable command-template token subset.

**Partial disposition**: The general runtime prose-contract hook gate was already considered and rejected in the linked 2026-08-18 decision. Preserve that history; do not treat present/identical instruction text as runtime compliance proof.

**Current residual from `v4.7.0#DF-4`**: Make a build-or-decline disposition for optional workflow_call factoring, preserving required-context coverage and producer contracts if adopted.

**Partial disposition**: Deliberately excluded in the source plan. Existing green CI is not proof this optional factoring was adopted.

**Current residual from `v4.7.0#DF-5`**: Make a build-or-decline disposition for optional per-skill presentation metadata, with an actual rendering consumer and schema before adding Tier1 fields.

**Partial disposition**: No rendering host justified the metadata. Preserve that consumer requirement and the permanent token cost boundary.

- **Migrated from**: v3.0#DF-v30-9 (reason: user-deferred); original `v3.0#DF-v30-9`, section `Open Items`.

#### Original source: DF-v30-9 - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-9 - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source phase**: Phase 10

**Plan reference**: T047 (DF-v23-9 visual-brainstorming-server re-evaluation)

**Reason**: Re-evaluated and re-deferred. DF-v23-9 is a Superpowers-style visual-brainstorming server -- an intentional `re-full`, local-only deferral first recorded in v2.3.0 (binds 127.0.0.1, zero outbound, no new credential, so it would pass the MCP Registry Policy). The revisit trigger is "build only if a user-facing need for in-session visual collaboration emerges". No such concrete need has emerged through v3.0.0 (a command-consolidation + skill-security + orchestration-adoption release; nothing in it depends on or requests in-session visual collaboration). Per Nexus-Hub's catalog-content-first identity, a long-lived local Node websocket server is not built pre-emptively. Carries v2.3.0 DF-v23-9.

**Suggested next step**: Build only if a concrete user-facing need for in-session visual collaboration emerges; when it does, scope it as an `extensions/` internal MCP under the reverse-engineer-first policy and add a `docs/policy/mcp-reverse-engineering-matrix.md` row before building. Otherwise keep re-deferring with the revisit trigger preserved.

**Severity**: Low (intentional, identity-grounded deferral; revisit trigger preserved)


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-9`.

- **Migrated from**: v3.6#DF-v36-2 (reason: user-deferred); original `v3.6#DF-v36-2`, section `Open Items`.

#### Original source: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source phase**: adoption-spec-kit Phase 5 (sub-task 5.2)

**Plan reference**: comparison-spec-kit.md Bucket C; plan 5.2

**Reason**: N2b -- a portable, agent-agnostic declarative YAML orchestration runtime (usable across all ~40 agents) was deferred and is policy-disfavored as a runtime. The MCP Registry Policy prefers LLM-native skills over bespoke runtimes, and the harness's own Dynamic Workflows already cover orchestration on Claude Code. Only N2a's *vocabulary* (gate / persisted-resume / continue-on-error) was adopted (Phase 1), not the engine; a cross-agent YAML engine is high effort and would introduce a new runtime executing `shell`/`command` steps. Classified `re-full` (deferred), high effort.

**Suggested next step**: Revisit only if cross-agent declarative orchestration (a single workflow definition driving non-Claude-Code agents) becomes a stated product goal; until then the adopted N2a vocabulary + Dynamic Workflows are the answer.

**Severity**: Low (deferred + policy-disfavored; vocabulary already adopted, Dynamic Workflows cover Claude Code)


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.6`, section `Open Items`, and original ID `DF-v36-2`.

- **Migrated from**: v3.7#DF-v36-2 (reason: user-deferred); original `v3.7#DF-v36-2`, section `Open Items`.

#### Original source: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source phase**: carried forward from v3.6.0 (adoption-spec-kit Phase 5)

**Plan reference**: comparison-spec-kit.md Bucket C

**Reason**: N2b -- a portable, agent-agnostic declarative YAML orchestration runtime (usable across all ~40 agents) remains deferred and policy-disfavored as a runtime. The MCP Registry Policy prefers LLM-native skills over bespoke runtimes, and the harness's own Dynamic Workflows already cover orchestration on Claude Code. Only N2a's *vocabulary* (gate / persisted-resume / continue-on-error) was adopted (v3.6.0 Phase 1), not the engine. Not in scope for the v3.7.0 install-UX overhaul. Classified `re-full` (deferred), high effort.

**Suggested next step**: Revisit only if cross-agent declarative orchestration (a single workflow definition driving non-Claude-Code agents) becomes a stated product goal; until then the adopted N2a vocabulary + Dynamic Workflows are the answer.

**Severity**: Low (deferred + policy-disfavored; vocabulary already adopted, Dynamic Workflows cover Claude Code)


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.7`, section `Open Items`, and original ID `DF-v36-2`.

- **Migrated from**: v3.8#DF-v36-2 (reason: user-deferred); original `v3.8#DF-v36-2`, section `Open Items`.

#### Original source: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source**: carried from v3.6.0

**Reason**: A portable, agent-agnostic declarative YAML orchestration runtime (usable across all agents) remains deferred and policy-disfavored as a runtime. The MCP Registry Policy prefers LLM-native skills over bespoke runtimes, and the harness's own Dynamic Workflows already cover orchestration on Claude Code. The v3.8.0 loop-engineering enrichment reinforced this decision by declining a per-project loop runtime config + standalone loop runtime (recorded in the reverse-engineering matrix).

**Suggested next step**: Revisit only if cross-agent declarative orchestration becomes a stated product goal; until then the adopted vocabulary + Dynamic Workflows are the answer.

**Severity**: Low (deferred + policy-disfavored; vocabulary already adopted).


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.8`, section `Open Items`, and original ID `DF-v36-2`.

- **Migrated from**: v3.9#DF-v36-2 (reason: user-deferred); original `v3.9#DF-v36-2`, section `Open Items`.

#### Original source: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v36-2 - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source**: carried from v3.6.0 / v3.8.0

**Reason**: A portable, agent-agnostic declarative orchestration / loop runtime remains deferred and policy-disfavored as a runtime. The v3.9.0 enrichment reinforced this again by declining a portable loop runner script and its spec-compile step (both `drop-outright` in the reverse-engineering matrix, citing the v3.8.0 host-driver precedent).

**Suggested next step**: Revisit only if cross-agent declarative orchestration becomes a stated product goal; until then the declarative loop definition + host `/loop` / `/goal` driver + the harness's Dynamic Workflows are the answer.

**Severity**: Low (deferred + policy-disfavored; reinforced by the v3.9.0 decline).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.9`, section `Open Items`, and original ID `DF-v36-2`.

- **Migrated from**: v3.9#DF-v39-nomistakes-1 (reason: user-deferred); original `v3.9#DF-v39-nomistakes-1`, section `Open Items`.

#### Original source: DF-v39-nomistakes-1 - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v39-nomistakes-1 - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source**: adoption-no-mistakes Phase 3 (N7)

**Reason**: The optional reverse-engineerable enrichment (a diff-to-session matching heuristic for `session-query`: discover candidate local agent sessions in the commit time window, score each by file-overlap against the diff, then summarize the chosen session into intent) was deliberately not built. The source tool itself deprioritizes after-the-fact transcript inference in favor of intent passed verbatim from the live conversation -- which is exactly the intent-as-verbatim-oracle guidance delivered in Phase 1 -- so its value is low when the agent already knows the intent. It is a `re-partial` item (a local, read-only heuristic over session logs already in `session-query`'s scope) that would require a reverse-engineering-matrix row because it reads transcript content.

**Suggested next step**: Build only if a concrete need for after-the-fact intent recovery appears (the agent lacked the live intent and must reconstruct it). If built: add the diff-overlap-plus-time-window matching section to `session-query/SKILL.md`, add the required RE-matrix row classifying it `re-partial`, and confirm the existing redaction discipline covers transcript content.

**Severity**: Low (optional; verbatim live intent is preferred and already delivered in Phase 1).


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.9`, section `Open Items`, and original ID `DF-v39-nomistakes-1`.

- **Migrated from**: v3.10#DF-v310-ruflo-A6 (reason: user-deferred); original `v3.10#DF-v310-ruflo-A6`, section `Open Items`.

#### Original source: DF-v310-ruflo-A6 - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v310-ruflo-A6 - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source**: adoption-ruflo Phase 3.2 (A6)

**Reason**: The optional, low-value quality-gate naming note was considered and skipped. A6 would add a short note (to `plan-before-code` or `quality-gate-definitions`) observing that a named, phased guided-development methodology with per-phase quality gates is functionally equivalent to Nexus-Hub's existing `/plan` -> `/implement` -> `/spec` flow plus `quality-gate-definitions`, so a user who arrives expecting that named methodology is already served. The comparison rated it low value because that function is already fully delivered and the note risks duplicating shipped material.

**Suggested next step**: Add the short generic note only if users repeatedly arrive expecting the named methodology and do not find it. If built: add a 4-8 line note to the chosen planning skill mapping the named phases onto the existing flow, describe it as "a named phased guided-development methodology" with no branded token, and cross-link `quality-gate-definitions`.

**Severity**: Low (the phased-guided-development-with-gates function is already delivered by `/plan`, `/implement`, `/spec`, and `quality-gate-definitions`).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.10`, section `Open Items`, and original ID `DF-v310-ruflo-A6`.

- **Migrated from**: v3.10#DF-v310-ruflo-A10-rest (reason: user-deferred); original `v3.10#DF-v310-ruflo-A10-rest`, section `Open Items`.

#### Original source: DF-v310-ruflo-A10-rest - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v310-ruflo-A10-rest - MIGRATED to v4.13 (AR-37)

**Category**: DF

**Source**: adoption-ruflo Phase 6.1 (worker-check selection)

**Reason**: Phase 6.1 adopted the two highest-value, lowest-noise ruflo background-worker *check ideas* as advisory tool-event hooks (`test-gap-notice`, `dependency-staleness-notice`). The remaining worker-check ideas from the source catalog (a periodic audit / optimize pass, a docs-staleness check, a duplicate-code-elimination check, and a per-run cost check) were considered and not adopted, because each either lacks a clean Write/Edit tool-event trigger (it is a periodic-scan idea, not an event-driven one), is already covered by an existing skill or command (audit/optimize by `/review` + `code-optimizer`; docs by `/update docs` + `documentation-consistency`; duplicates by `dead-code-eliminator` + `code-simplification`), or would be redundant with the hard cost controls in `ai-billing-safeguards`. Adopting them as always-firing hooks would add noise without proportional value, and a periodic scanner would reintroduce the daemon model the cycle deliberately declined.

**Suggested next step**: Adopt an additional check as an advisory hook only when a clean tool-event trigger and a low false-positive rate are both demonstrable (for example, a docs-staleness advisory keyed on edits to a source file whose sibling doc was not also touched). Otherwise leave the capability to the existing skills/commands.

**Severity**: Low (the two highest-value checks are shipped; the rest are either covered elsewhere or noise-prone as always-firing hooks).


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.10`, section `Open Items`, and original ID `DF-v310-ruflo-A10-rest`.

- **Migrated from**: v3.11#DF-v310-ruflo-A6 (reason: user-deferred); original `v3.11.0#DF-v310-ruflo-A6`, section `adoption-spec-kit third cycle (2026-07-08)`.

#### Original source: DF-v310-ruflo-A6 (Low) - optional quality-gate-naming note; skipped, the function is already delivered by `/plan` -> `/implement` -> `/spec` + `quality-gate-definitions`. - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: Converted this historical list obligation into a supported item heading. The complete source line is retained below; prior transfer wording alone does not prove a migration.

**Original list entry**: - **DF-v310-ruflo-A6** (Low) - optional quality-gate-naming note; skipped, the function is already delivered by `/plan` -> `/implement` -> `/spec` + `quality-gate-definitions`. - MIGRATED to v4.13 (AR-37)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.11.0`, section `adoption-spec-kit third cycle (2026-07-08)`, and original ID `DF-v310-ruflo-A6`.

- **Migrated from**: v3.11#DF-v310-ruflo-A10-rest (reason: user-deferred); original `v3.11.0#DF-v310-ruflo-A10-rest`, section `adoption-spec-kit third cycle (2026-07-08)`.

#### Original source: DF-v310-ruflo-A10-rest (Low) - the remaining background-worker check ideas were not adopted as always-firing hooks (noise-prone or covered elsewhere). - MIGRATED to v4.13 (AR-37)

**v4.13.11 structural audit, 2026-10-09**: Converted this historical list obligation into a supported item heading. The complete source line is retained below; prior transfer wording alone does not prove a migration.

**Original list entry**: - **DF-v310-ruflo-A10-rest** (Low) - the remaining background-worker check ideas were not adopted as always-firing hooks (noise-prone or covered elsewhere). - MIGRATED to v4.13 (AR-37)


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.11.0`, section `adoption-spec-kit third cycle (2026-07-08)`, and original ID `DF-v310-ruflo-A10-rest`.

- **Migrated from**: v4.0#MT-1-v400 (reason: user-deferred); original `v4.0.0#MT-1`, section `v4.0.0 - agent-communication-overhaul`.

#### Original source: MT-1-v400 - No runtime check that a response actually follows the contract

- **Source phase**: Phase 1 - Communication contract and decision record
- **Plan reference**: `docs/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md` (Phase 1 design; recorded in the decision record's Consequences)
- **Reason**: Prose tone is not machine-checkable at `PreToolUse` time. The tests in this version prove that the contract is PRESENT and IDENTICAL everywhere it should be; nothing proves that a given response OBEYED it. This was considered and rejected as a hook gate in `docs/decisions/implemented/policy/2026-08-18-agent-communication-contract.md`; the gap is recorded here so it is visible rather than implied.
- **Suggested next step**: The mechanically checkable subset is narrow but real: a response containing a fenced command block with an unflagged `<...>`, `[...]`, or ALL-CAPS template token is detectable by pattern. If a future version wants partial enforcement, that single rule is the one worth automating; the rest stays advisory.

**Original source identity**: `v4.0.0#MT-1` in `v4.0.0 - agent-communication-overhaul`; normalized stable ID `MT-1-v400` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.0.0`, section `v4.0.0 - agent-communication-overhaul`, and original ID `MT-1`.

- **Migrated from**: v4.7#DF-4 (reason: user-deferred); original `v4.7.0#DF-4`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`.

#### Original source: DF-4 - Reusable `workflow_call` CI factoring (report item E5) deliberately excluded

- **Source phase**: Phase 7 - Known-gaps reconciliation (T028), as the plan directs.
- **Plan reference**: `comparisons/v4.7.0-comparison-ecc-agent-catalog.md` item E5 (P3); main plan sub-task 7.2.
- **Reason**: A refactor of working CI whose benefit is maintainer ergonomics, carrying the required-context risk the v3.17.6 policy exists to prevent: a reusable workflow changes which workflow produces a context, and a context produced by a filtered or conditionally called workflow sits Pending forever. Not rejected on principle; not worth a release that also changes twelve templates and the install path.
- **Suggested next step**: If ever done, its own release, with `check_required_check_coverage.py` and `tests/validators/test_ci_required_gate.py` extended first to resolve contexts through `workflow_call` producers.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.7.0`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`, and original ID `DF-4`.

- **Migrated from**: v4.7#DF-5 (reason: user-deferred); original `v4.7.0#DF-5`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`.

#### Original source: DF-5 - Per-skill presentation metadata (report item E6) deliberately excluded

- **Source phase**: Phase 7 - Known-gaps reconciliation (T028), as the plan directs.
- **Plan reference**: `comparisons/v4.7.0-comparison-ecc-agent-catalog.md` item E6 (P3); main plan sub-task 7.2.
- **Reason**: Display name, short description, brand colour, and default prompt per skill have no rendering host in Nexus-Hub today; frontmatter that nothing reads is Tier 1 cost on every session for no consumer.
- **Suggested next step**: Revisit when a consumer exists (the guide, the MCP skill server, or a downstream app asks for it), and add the fields to `data/skills.json` first rather than to every `SKILL.md`.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.7.0`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`, and original ID `DF-5`.

- **Migrated from**: v3.15#DF-6 (reason: user-deferred); original `v3.15.7#DF-6`, section `v3.15.7 - adoption-raptor-loop-hunt`.

#### Original source: DF-6 - Durable monotonic-scrutiny store remains deferred - MIGRATED to v4.13 (AR-37)

- **Source phase**: v3.15.7 Phase 7 - Known-gaps reconciliation.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.7-adoption-raptor-loop-hunt.md` (sub-task 7.2; comparison candidate B11).
- **Reason**: Phase 6 adopted the safety invariant that prior-cycle memory may only raise scrutiny, never establish coverage or exclude a candidate. A durable store is locally buildable but was intentionally deferred because its persistence, invalidation, and poisoning-resistance surface exceeds this patch's bounded scope.
- **Re-entry condition**: Re-propose only with a local storage schema, explicit invalidation rules, poisoning tests, and proof that every stored signal can only increase review priority.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-37`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.7`, section `v3.15.7 - adoption-raptor-loop-hunt`, and original ID `DF-6`.

### AR-41: Product atlas

- **Current state**: `docs/handbooks/overview.html` (commit `0b164f06`) may satisfy it, but `docs/README.md` still says no atlas exists.
- **Owner and next step**: maintainer; confirm the overview handbook counts, then close and correct `docs/README.md`.
- **Historical transfer note**: v3.21.0#DF-1 on 2026-09-29 (reason: decision pending).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.21#DF-1 (reason: user-deferred); original `v3.21.0#DF-1`, section `v3.21.0`.

#### Original source: DF-1 - Nexus-Hub catalog has no product atlas HTML - MIGRATED to v4.13 (AR-41)

- **Source phase**: Phase 5 - Living docs, git hygiene, CI/CD, Goal review
- **Plan reference**: `docs/archives/v3/v3.21/plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md` (sub-task 5.3)
- **Reason**: Last-phase scan found `docs/handbooks/` scaffolded (README, empty `markdown/` and `html/` with `.gitkeep`) and `atlas/companion html count: 0`. This repo is the upstream catalog, not an application with a user-facing walkthrough. Inventing a fake atlas would violate the plan's honesty rule.
- **Suggested next step**: If maintainers want a catalog atlas, author real markdown under `docs/handbooks/markdown/` and generate HTML via `/presentify`. Until then `/update release` regenerate-and-fail-on-stale is a no-op.

Prior v3.20 items (DF-1 invocation levers, DF-2 marketplace form, WN-3 personal-paths scan) stay in `docs/archives/v3/v3.20/known-gaps.md`. They were reviewed this last phase and remain out of this plan's scope per Phase B.5.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-41`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.21.0`, section `v3.21.0`, and original ID `DF-1`.

### AR-42: The docs-convention checker scans only the active minor

- **Current state**: `scripts/check_docs_conventions.py` still scans only the active minor, and its docstring is stale.
- **Owner and next step**: maintainer; record the grandfathering decision, then close and fix the docstring.
- **Historical transfer note**: v3.19.2#DF-2 on 2026-09-29 (reason: decision pending).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.19#DF-2 (reason: user-deferred); original `v3.19.2#DF-2`, section `v3.19.2`.

#### Original source: DF-2 - Docs convention checker covers only the active minor - MIGRATED to v4.13 (AR-42)

- **Source phase**: Phase 2 (triggering confidence and eval discipline, task 2.3)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md` (Phase 2 / link-integrity checker)
- **Why deferred**: A first pass over the whole `docs/` tree reported 141 missing relative targets, almost all in historical minors and policy matrices. Gating them in this patch would bury the new checker under archaeology. The guard therefore scans `docs/v3/v3.19/` in a repo checkout (tests still scan a tmp `docs/` tree that has no `v3.19`).
- **Suggested next step**: either repair historical links in a dedicated docs PR, or keep the active-minor scope and record older trees as grandfathered.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-42`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.19.2`, section `v3.19.2`, and original ID `DF-2`.

### AR-43: Signed execution contracts remain a design study

- **Current state**: no decision record exists.
- **Owner and next step**: maintainer; promote the study's deferral recommendation to a decision record, then close.
- **Historical transfer note**: v3.19.2#DF-4 on 2026-09-29 (reason: decision pending).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.19#DF-4 (reason: user-deferred); original `v3.19.2#DF-4`, section `v3.19.2`.

#### Original source: DF-4 - Signed execution contracts stay a design study - MIGRATED to v4.13 (AR-43)

- **Source phase**: Phase 5 (compressor polish and session mining, task 5.4)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md` (Phase 5 / signed-execution-contract study)
- **Why deferred**: A local single-user agent already has a 0/1/2/3 rewrite decision subordinated to host deny. Cryptographic signatures would add key material without blocking anything host settings cannot already refuse. Study: `docs/v3/v3.19/design/signed-execution-contract-study.md` (**# DEVIATION**: plan cited `docs/v3/v3.18/design/`). Recommendation: defer crypto; optionally adopt capability-id + TTL as an unsigned convention later.
- **Suggested next step**: revisit only if Nexus-Hub grows a multi-executor or remote-runner surface.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-43`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.19.2`, section `v3.19.2`, and original ID `DF-4`.

### Newly represented historical residuals - 2026-10-09

### AR-61: Hand-edited model references bypass the deterministic guard

**Owner**: Prompting and catalog owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual**: Decide and scope a repository-only model-name leakage guard with an explicit allowlist for legitimate mentions and triage of the historical 16 matches. The apply engine already prevents its own model-specific writes; human hand edits remain outside that boundary. Do not infer ACCEPTED meant the residual was closed.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v3.15#DF-2-v3155 (reason: user-deferred); original `v3.15.5#DF-2`, section `v3.15.5 - model-prompting-research`.

#### Original source: DF-2-v3155 - model-specific content in a shared body is unguarded against HAND edits (the engine rail binds only the engine)

- **Source phase**: v3.15.5 Phase 3.1.
- **Plan reference**: the plan's Overview and Definition of Done ("a model-specific finding provably cannot reach a shared body (parity guard proves it)").
- **Reason**: the plan's premise is false (see the Phase 3 paragraph above for the three-case evidence). The rail was therefore implemented in the apply engine, which makes the accurate claim: **this feature cannot autonomously write model-specific content into a shared body**. It is NOT the stronger claim that model-specific content cannot exist in a shared body, because a human hand-editing a `SKILL.md`, a command, or a `base-*.md` bypasses the engine entirely. A catalog-wide model-name gate was considered and deliberately not added in this phase: the catalog already carries pre-existing model mentions (6 matches across the `base-*.md` set and 10 SKILL.md files), several of them legitimate (`model-routing` documents tiers by name, `claude-api` names model ids), so such a gate would fail on day one and triaging those mentions is a separate decision with its own scope.
- **Suggested next step**: decide in Phase 6 (or as its own cycle) whether to add a repo-internal `check_model_specific_leakage.py` gate. It would need an allowlist for legitimate mentions and a triage pass over the 16 existing ones. It would need NO installer edit (it belongs in the `DEV_ONLY_SCRIPTS` allowlist in `catalog/hooks/tests/test_installer_smoke.py`, alongside the three existing repo-internal guards). Until then, the residual is documented rather than closed.
- **DISPOSITION (Phase 6.2/6.4): ACCEPTED as a documented residual, and the DoD wording corrected in the confirmation table above.** The maintainer deferred this decision to Phase 6, and the call is to accept rather than build the catalog-wide gate in this release, for three reasons. First, the DoD's *intent* is met: the autonomous path (the only one this release creates) provably cannot write model-specific content into a shared body, proven by a paired test rather than asserted. Second, the gate's blocking cost lands on pre-existing content, not on this feature: 6 matches across the `base-*.md` set and 10 SKILL.md files would fail on day one, several legitimately (`model-routing` documents tiers by name, `claude-api` names model ids), so shipping it would mean either a triage pass over unrelated skills or an allowlist large enough to blunt the guard. Third, the residual is bounded and visible: it is a human hand-edit, which already goes through review, and the corrected mechanism is now documented in three places (`references/edit-routing.md` with the three-case evidence, the SKILL.md hard-rail section, and the `/tune-prompting` command's safety posture) so no future reader inherits the false premise. **Carried forward, not closed**: a repo-internal `check_model_specific_leakage.py` remains the right long-term fix. It needs no installer edit (the `DEV_ONLY_SCRIPTS` allowlist in `catalog/hooks/tests/test_installer_smoke.py` covers repo-internal guards, with three precedents) but does need the triage pass. Recorded here for the next `/plan` ingest rather than as a v3.15.5 blocker.

**Original source identity**: `v3.15.5#DF-2` in `v3.15.5 - model-prompting-research`; normalized stable ID `DF-2-v3155` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-61`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.5`, section `v3.15.5 - model-prompting-research`, and original ID `DF-2`.

### AR-62: Exact installed helper delivery remains unproved across supported operating systems

**Owner**: Installer-smoke test owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v1.1#DF-006`**: Prove aggregate_benchmark.py, skill_eval_viewer.py and optimize_skill_description.py reach installed scripts on Linux and macOS through the real workspace installer smoke. Add those exact paths to EXPECTED_SCRIPTS per Phase3 T013; retain actual per-OS receipts.

**Partial disposition**: Existing generic recursive-copy and syntax tests do not by themselves prove these exact outputs. AR26 covers a different live macOS curl bootstrap boundary.

**Current residual from `v1.1#DF-008`**: Prove package_skill.py reaches the installed scripts path on real Linux/macOS workspace smoke, alongside the historical cumulative bundle delivery obligations.

**Partial disposition**: Group with DF-006 without replacing its exact helper list. The package round-trip tests are narrower than installer delivery.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v1.1#DF-006 (reason: user-deferred); original `v1.1#DF-006`, section `Open Items`.

#### Original source: DF-006 -- Phase 5 cross-OS installer dry-run deferred (extends DF-003 / DF-005)

**Source phase**: Phase 5, sub-task 5.6 (cross-platform installer verification).
**Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../../archives/v1/v1.1/plans/adoption-skills.md) lines 387-392 (sub-task 5.6) and the cross-cutting constraint at lines 535-543.
**Reason**: Phase 5 added three repo-level Python scripts (`scripts/aggregate_benchmark.py`, `scripts/skill_eval_viewer.py`, `scripts/optimize_skill_description.py`) and registered all three in BOTH `scripts/installer.sh` and `scripts/installer.ps1` per the AGENTS.md "Installer-Aware Changes" rule. Verification on Windows + Git Bash was performed: `bash -n scripts/installer.sh` clean; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on `installer.ps1`; ShellCheck clean on `installer.sh` and `install.sh`; the three scripts compile clean (`python -m py_compile`); the new pytest module (`catalog/hooks/tests/test_eval_loop.py`) passes 14/14; the dry-run mode of `optimize_skill_description.py` is exercised under three pytest cases (schema, determinism under fixed seed, no-CLI-invocation under empty PATH). Real `bash scripts/installer.sh` execution into a throwaway directory on a real macOS or Linux host was not run.
**Resolution applied in Phase 5**: None - intentionally deferred per the same rationale as DF-003 / DF-005 (the work-environment constraint is Windows 11 + PowerShell). Both installers' `safe_copy` / `Safe-Copy` primitives are already exercised by every prior installer block in the same file, so the new copy lines exercise no new code path - they are textual additions that piggyback on already-validated machinery.
**Suggested next step**: Same as DF-003 / DF-005. The cumulative cross-OS smoke run for v1.1.5 (which now covers Phase 2 doc-coauthoring SKILL.md, Phase 4 four bundled skill folders + two scaffolder scripts, AND Phase 5 three eval-loop scripts) should happen before the v1.1.5 -> v1.2.0 version bump in Phase 7's `/update-version` step. CI matrix coverage (Linux + macOS GitHub Actions runners performing a real `bash scripts/installer.sh` workspace install) is the durable fix.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-62`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v1.1`, section `Open Items`, and original ID `DF-006`.

- **Migrated from**: v1.1#DF-008 (reason: user-deferred); original `v1.1#DF-008`, section `Open Items`.

#### Original source: DF-008 -- Phase 7 packager installer registration not exercised on macOS / Linux

**Source phase**: Phase 7, sub-task 7.1 (`scripts/package_skill.py` + installer registration) and 7.2 (cross-platform installer verification).
**Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../../archives/v1/v1.1/plans/adoption-skills.md) lines 487-501 (sub-tasks 7.1 and 7.2) and the cross-cutting constraint at lines 535-543.
**Reason**: Phase 7 added one new repo-level Python script (`scripts/package_skill.py`) and registered it in BOTH `scripts/installer.sh` (after the eval-loop dispatcher block) and `scripts/installer.ps1` (matching `Safe-Copy` block at the same logical position) per the AGENTS.md "Installer-Aware Changes" rule. Verification on Windows + Git Bash was performed: `python -m py_compile scripts/package_skill.py` clean; `bash -n scripts/installer.sh` clean; ShellCheck (`--severity=warning`) clean on `scripts/installer.sh` and `install.sh`; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on `installer.ps1`; the new pytest module (`catalog/hooks/tests/test_package_skill.py`) passes 14/14; round-trip pack-and-extract works against a real Phase 5 skill bundle (`catalog/skills/workflow/skill-eval-loop/`, 8 files preserved at original relative paths). Real `bash scripts/installer.sh` execution into a throwaway directory on a real macOS or Linux host to confirm the new copy line lands `package_skill.py` at `~/.devai-hub/scripts/package_skill.py` was not run.
**Resolution applied in Phase 7**: None - intentionally deferred per the same rationale as DF-003 / DF-005 / DF-006 / DF-007 (the work-environment constraint is Windows 11 + PowerShell). The new copy line piggybacks on the same already-validated `safe_copy` / `Safe-Copy` primitives used for the four prior repo-level scripts in the same block (`generate_report.py`, `aggregate_benchmark.py`, `skill_eval_viewer.py`, `optimize_skill_description.py`). The packager itself is stdlib-only Python so the runtime risk surface is minimal once the file lands at the right path.
**Suggested next step**: Roll into the cumulative cross-OS smoke run scheduled for the v1.1.5 -> v1.2.0 bump in `/wrap-up-session` -> `/update-version`. The smoke task should now cover: Phase 2 (`doc-coauthoring` SKILL.md), Phase 4 (four bundled skill folders + two scaffolder scripts), Phase 5 (three eval-loop dispatcher scripts), Phase 6 (two skill folders + four bundled scaffolders), and Phase 7 (one packager script). CI matrix coverage (Linux + macOS GitHub Actions runners performing a real `bash scripts/installer.sh` workspace install) remains the durable fix.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-62`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v1.1`, section `Open Items`, and original ID `DF-008`.

### AR-63: The four MCP scaffolders lack real generation and server-start receipts

**Owner**: MCP scaffolder owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v1.1#DF-007`**: Execute all four Bash/PowerShell FastMCP and TypeScript scaffolders on clean supported hosts. Check successful generation, compile/type-check and a real startup or stdio handshake against the generated server for both stacks.

**Partial disposition**: Static syntax, recursive delivery and unrelated installer smoke do not prove a scaffolded server starts.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v1.1#DF-007 (reason: user-deferred); original `v1.1#DF-007`, section `Open Items`.

#### Original source: DF-007 -- Phase 6 mcp-builder bundled scaffolders not exercised end-to-end

**Source phase**: Phase 6, sub-task 6.3 (cross-platform installer verification).
**Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../../archives/v1/v1.1/plans/adoption-skills.md) lines 445-451 (sub-task 6.3) and the cross-cutting constraint at lines 535-543.
**Reason**: Phase 6 added two new skills (`brand-styling` in specialized-domains, `mcp-builder` in ai-development) and four bundled scaffolding scripts under `mcp-builder/scripts/`: `init-mcp-fastmcp.sh`, `init-mcp-fastmcp.ps1`, `init-mcp-ts.sh`, `init-mcp-ts.ps1`. Static validation was performed and is clean: `bash -n` clean on both `.sh` files; ShellCheck (`--severity=warning`) clean on both; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on both `.ps1` files. The existing recursive-copy primitives (`safe_folder_copy` / `Safe-Folder-Copy`) auto-distribute the bundled subdirs without an installer edit (the same machinery validated in Phase 3 / WN-001). However, end-to-end execution of the four scaffolders against a real Python 3.10+ / Node 20+ host -- actually running `init-mcp-fastmcp.sh hello-server` to scaffold a working FastMCP server, then `mcp dev server.py` to confirm the inspector loads, and the equivalent for the TS path -- was NOT performed in this session. The work-environment constraint (Windows 11 + PowerShell + this conversation's tool surface) does not include a way to spin up Python venvs and full Node installs to verify a complete scaffold-and-launch cycle for both stacks.
**Resolution applied in Phase 6**: None -- intentionally deferred. The scaffolders are syntactically valid and follow the same shape as the validated Phase 4 `init-artifact.{sh,ps1}` precedent. The risk surface is "the scaffolded server actually starts under `mcp dev` / `npm run dev`", which is not catchable by static syntax validation.
**Suggested next step**: Add a CI matrix step (or a manual release-readiness smoke task before the v1.1.5 -> v1.2.0 bump) that, on a Linux runner with Python 3.10+ and Node 20+ installed, executes each of the four scaffolders against a clean fixture directory and verifies: (a) the scaffold step exits 0; (b) the resulting `server.py` (FastMCP) or `src/server.ts` (TS SDK) file exists with the expected shape; (c) `python -m py_compile server.py` (FastMCP) or `tsc --noEmit` (TS SDK) returns 0; (d) optionally, `mcp dev server.py` / `npm run dev` starts and responds to a stdio handshake from a test client. This gap rolls up into the cumulative DF-003 / DF-005 / DF-006 cross-OS verification queue scheduled for Phase 7's `/update-version` step.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-63`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v1.1`, section `Open Items`, and original ID `DF-007`.

### AR-64: Live prompting roster completeness and CLI model qualification remain unproved

**Owner**: Prompting-profile owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.1.0#DF-1`**: Requalify prompting profiles against a complete then-current canonical model-ID roster, preserving platform/provider separation. Determine whether the old GPT-5.6 profile deficit is now fully closed by later profile publication and retain only current roster/profile mismatches.

**Partial disposition**: Group with v4.7 DF-2 and v4.9 MT-1, retaining distinct profile, CLI-picker and roster-completeness clauses. Later 16-model schema/profile qualification is not a complete account roster.

**Current residual from `v4.7.0#DF-2`**: Verify current Codex CLI/account picker availability and canonical identity of gpt-6-astra independently of the provider API catalog and profile presence.

**Partial disposition**: September24 picker still omitted it; API-profile correctness did not establish CLI availability. Group with model-roster owner without assuming the old account state remains current.

**Current residual from `v4.9#MT-1`**: Obtain a supported complete canonical-ID account roster and qualify current profiles with the deterministic writer before changing roster hashes or last_verified.

**Partial disposition**: Retain Haiku and GPT-5.6-family later profile publication closures (PR314/PR316) and 16/16 profile schema qualification. Account-backed Opus5.5 display-name picker visibility did not prove canonical ID or complete roster; helper models=[] stayed incomplete.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.1#DF-1-v410 (reason: user-credential); original `v4.1.0#DF-1`, section `v4.1.0`.

#### Original source: DF-1-v410 - Prompting profile layer does not match the live Codex roster

- **Source phase**: v4.1.0 release preparation
- **Evidence**: On 2026-08-31, `python scripts/check_model_prompting_freshness.py --advisory gpt-5.6-sol gpt-5.6-terra gpt-5.6-luna` reported `DRIFTED`: the three supplied live Codex model IDs are unprofiled and the four recorded Claude entries are absent from that host roster. The current v4.4 model map independently lists those three Codex IDs.
- **Reason deferred**: The advisory is intentionally not a release or CI gate, and a conformant refresh requires the separate calibrated `/tune-prompting` research and adversarial-verification workflow rather than a release-time hand edit.
- **Next action**: Run `/tune-prompting` in a separately scoped plan, calibrate on one live model before widening, and retain any unverified models as explicit gaps.

**Original source identity**: `v4.1.0#DF-1` in `v4.1.0`; normalized stable ID `DF-1-v410` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-64`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.1.0`, section `v4.1.0`, and original ID `DF-1`.

- **Migrated from**: v4.7#DF-2 (reason: user-credential); original `v4.7.0#DF-2`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`.

#### Original source: DF-2 - The Codex CLI does not yet list `gpt-6-astra`, so the codex profile entry reads DRIFTED

- **Source phase**: Amendment Phase 3 - the first OpenAI prompting profile (T049).
- **Plan reference**: `v4.7.0-adoption-gpt-6-astra-prompting.md` sub-task 3.3.
- **Reason**: `enumerate-models.sh codex` (`codex debug models`) on 2026-09-05 returned six models (`codex-auto-review`, `gpt-5.2`, `gpt-5.3-codex`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.5`) and not `gpt-6-astra`, which the vendor's API catalog lists as generally available. The layer's invariant (the index never claims a model it has no roster entry for) widens the codex entry's roster to include the profiled model, so `check_model_prompting_freshness.py --platform codex <live ids>` reports DRIFTED with `gpt-6-astra` as "recorded but no longer live". The profile itself is correct for the API surface the vendor documents; the drift is between the CLI's picker and the API catalog.
- **Suggested next step**: Re-run `enumerate-models.sh codex` at the next release; when the CLI lists `gpt-6-astra`, re-stamp the codex entry through the writer and this item closes. If the CLI never lists it, re-home the profile under an API-platform id in a later schema decision.

**2026-09-24 recheck**: The installed Codex CLI picker still lists six models and omits `gpt-6-astra`; the [archived read-only result](../../../archives/v4/v4.7/development/model-map-followup/verification.md) keeps API availability separate from CLI availability. DF-2 remains open and no profile was re-stamped.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-64`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.7.0`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`, and original ID `DF-2`.

- **Migrated from**: v4.9#MT-1 (reason: user-credential); original `v4.9#MT-1`, section `Follow-up Items - found 2026-09-08 during post-v4.8.0 follow-up`.

#### Original source: MT-1 - Incomplete prompting-profile coverage and roster freshness

- **Source**: the post-v4.8.0 `/tune-prompting` full roster sweep.
- **What was observed on 2026-09-08**: 12 of 16 rostered models were profiled. Four were not, each for a sourced reason rather than for lack of effort:
    - **`claude-haiku-4-5`**: Anthropic's model-specific guidance table lists dedicated prompting pages for Fable 5.1, Fable 5, Sonnet 5, Opus 5, and Opus 4.8 only. Haiku 4.5 is covered by the general best-practices reference, which is model-agnostic across current Claude models and therefore yields no model-SPECIFIC claim.
    - **`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`**: OpenAI's prompt-engineering guide documents `gpt-6-astra` (already profiled) and reasoning-versus-GPT guidance generally. It names no member of the 5.6 family, so there is nothing model-specific to record.
- **Why this is the correct outcome, not a shortfall**: the runbook is explicit that no primary source found means zero claims rather than a guess, because an unsourced claim in the layer is indistinguishable from a hallucinated one and every later phase treats recorded claims as verified input. All four are reported UNVERIFIED by `verify_model_prompting_profiles.py`, which treats that as tracked rather than as a gate failure.
- **Suggested next step**: re-check at the next `/tune-prompting` run. A vendor publishing a per-model page is the trigger; nothing else changes the answer. Do not fill these from the general guidance, which would silently convert model-agnostic advice into a model-specific claim.

**Source recheck, 2026-09-23**: The original observation above remains the record of the 2026-09-08 sweep, but its statement that OpenAI names no GPT-5.6 member is no longer current. [OpenAI's GPT-5.6 guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) now names Sol, Terra, and Luna and differentiates their workload and cost positioning; its prompting advice is framed for the GPT-5.6 family, not as distinct instructions for each member. [Anthropic's prompting reference](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) still has no dedicated Haiku 4.5 prompting page, although it names Haiku in a shared context-awareness subsection. No per-model profile was written or re-stamped in this source-only recheck. MT-1 remains open for a qualified `/tune-prompting` pass rather than treating family guidance or model-selection advice as a verified per-model prompting difference.

**Source recheck, 2026-09-25**: [Anthropic's advisor-tool reference](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool) contains an alternative Haiku 4.5 system prompt for predominantly coding or write-task executors using the optional `advisor` tool. Advisor calls forward the executor's full transcript to a separate server-side inference and are billed at the advisor model's rates; Anthropic also reports a browse-comprehension regression for the alternative block. This conditional tool configuration is not a generally applicable Haiku prompting profile and does not authorize transcript forwarding or extra spend in Nexus-Hub. [Anthropic's general prompting reference](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) still lists no dedicated Haiku prompting page, while [OpenAI's GPT-5.6 guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) names Sol, Terra, and Luna for model selection but frames its prompting advice at family scope. No profile or freshness stamp changed in this source-only pass; MT-1 remains open.

**Haiku calibration, 2026-09-25**: [Anthropic's Haiku 4.5 migration guide](https://platform.claude.com/docs/en/models/haiku-4-5/migration-guide) specifically recommends considering `thinking: {type: "enabled", budget_tokens: N}` for coding and reasoning tasks; its [extended-thinking reference](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) confirms that Haiku 4.5 supports this manual mode, while newer adaptive-mode guidance must not be copied to it. Independent source, currency, and actionability reviews found the recommendation usable as one conditional, model-specific profile claim after correcting the quoted API value. The installed Claude Code picker includes Haiku 4.5, but the enumeration helper returns only a picker sentinel, not a complete model-ID roster; the index's 2026-09-08 config roster cannot be re-stamped as live evidence. No profile or freshness marker was written. Capture the complete current Claude roster, run the deterministic one-model planner and writer, and verify the generated layer before closing the Haiku portion of MT-1; the three GPT-5.6 entries remain separate. The [archived calibration receipt](../../../archives/v4/v4.9/development/haiku-profile-calibration-2026-09-25/verification.md) preserves the bounded evidence.

**Claim-only qualification, 2026-09-25**: The deterministic writer now accepts a sourced claim for an already-rostered model without refreshing the roster date, provenance, or hash, and rejects unknown models and malformed roster refreshes. The qualified Haiku 4.5 claim was written through that path; the structural validator reports 13 of 16 profiled models and still dates the roster to 2026-09-08. This local qualification does not establish a complete live Claude roster, and the three GPT-5.6 entries remain unprofiled. At this local stage, MT-1 remained open for protected publication and those separate evidence gates. See the [bounded verification](../../../archives/v4/v4.9/development/haiku-profile-claim-only-2026-09-25/verification.md).

**Publication, 2026-09-25**: [PR #314](https://github.com/bendourthe/Nexus-Hub/pull/314) merged the claim-only writer and Haiku profile after 21 hosted checks passed with one intentional skip; [post-merge run 36137890656](https://github.com/bendourthe/Nexus-Hub/actions/runs/36137890656) passed smoke and provenance. The complete live Claude roster and the three GPT-5.6 profiles remain separate MT-1 gates.

**GPT-5.6 family qualification, 2026-09-25**: [OpenAI's current GPT-5.6 guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) supports one family-scoped migration-effort comparison for Sol, Terra, and Luna; their official model pages confirm the available effort settings. Three independent refutation lenses per candidate qualified a claim that excludes prior effort `none` and promises no quality equivalence. The claim-only writer generated all three per-model mirrors with an explicit family-scope note, and the structural gate reports 16 of 16 models in the recorded roster profiled without changing its 2026-09-08 date. The focused set passed 123 tests after removing a shipped-seed test that incorrectly required the roster to remain incomplete; a fixture still covers the unprofiled path. Claude Code 2.1.282 still returns a picker sentinel, and its account-backed `/model` view exposes display names rather than a complete canonical ID roster. MT-1 remains open for complete live roster evidence and protected publication. See the [bounded verification](../../../archives/v4/v4.9/development/gpt56-family-profiles-2026-09-25/verification.md).

**GPT-5.6 publication, 2026-09-25**: [PR #316](https://github.com/bendourthe/Nexus-Hub/pull/316) merged the three family-scoped profiles at `65baca12`; its hosted required checks passed, and [post-merge run 36162158349](https://github.com/bendourthe/Nexus-Hub/actions/runs/36162158349) passed smoke and provenance at that merge commit. The recorded roster still dates to 2026-09-08, and neither the merged profiles nor the post-merge jobs prove a complete live Claude model-ID roster. MT-1 remains open only for that roster-freshness gate.

**Public-catalog recheck, 2026-09-27**: [Anthropic's September 24 release notes](https://platform.claude.com/docs/en/release-notes/overview) and [current models overview](https://platform.claude.com/docs/en/models/overview) name `claude-opus-5-5`, which is absent from the recorded 2026-09-08 config roster. This proves that the recorded roster is stale against the public Claude API catalog, not that this model is available in the user's Claude Code account. The local Claude Code enumeration helper still returns `{"source":"picker","models":[]}`; no complete canonical picker/API roster was available. The profile schema passes with 16 of 16 recorded models, but that result is not current-roster completeness. No profile, roster hash, or `last_verified` value changed. MT-1 remains open: obtain a complete live roster before adding a new model through the deterministic writer or refreshing the roster date.

**Account-picker recheck, 2026-09-27**: Installed Claude Code 2.1.282 opened the account-backed `/model` picker in the already trusted checkout, with Opus 5.5 selected on the Claude Team account; the picker also showed other model display names but offered no complete canonical model-ID enumeration. The session exited without selecting another model or sending an inference prompt. This establishes account picker availability of Opus 5.5, narrowing the public-catalog note above, but it does not establish the canonical ID or a complete live roster. No profile, roster hash, or `last_verified` value changed; MT-1 remains open for a supported complete-ID read path and deterministic profile qualification.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-64`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.9`, section `Follow-up Items - found 2026-09-08 during post-v4.8.0 follow-up`, and original ID `MT-1`.

### AR-65: Optional scanner presets lack live none, some, and all-tool receipts

**Owner**: Security-audit owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.1.1#DF-1`**: On an already provisioned host execute security-audit with some, none and all applicable optional scanners, retaining UNAVAILABLE states and receipts. Cover Semgrep, gitleaks, OSV-Scanner, npm audit, pip-audit, Trivy and Checkov when applicable.

**Partial disposition**: Fixture tests are narrower than live binary execution. The source plan prohibits adding real scanner execution to repository CI.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.1#DF-1-v411 (reason: user-deferred); original `v4.1.1#DF-1`, section `v4.1.1`.

#### Original source: DF-1-v411 - Live optional scanners were not executed on the implementation host

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Plan reference**: `docs/archives/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md` T025 / T032
- **Evidence**: Fixture-driven closure-gate tests pass without invoking Semgrep, gitleaks, OSV-Scanner, npm audit, pip-audit, Trivy, or Checkov. Phase 4 history records that those binaries were not present or not executed.
- **Reason deferred**: The plan forbids adding real scanner execution to Nexus-Hub CI. Host-local binaries are optional; missing tools must remain visible as `UNAVAILABLE`.
- **Next action**: On a machine that already has the optional tools, run the `security-audit` preset once with some, none, and all applicable scanners and keep the receipts.

**Original source identity**: `v4.1.1#DF-1` in `v4.1.1`; normalized stable ID `DF-1-v411` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-65`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.1.1`, section `v4.1.1`, and original ID `DF-1`.

### AR-66: The five-person Training workshop remains unperformed

**Owner**: Guide owner and five participants. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.2.2#DF-2`**: Run the eight-step Training walkthrough with a cohort of five and record stalls and comprehension results.

**Partial disposition**: Both source patch entries represent the same inherited workshop obligation; preserve both origins. Rendered QA, keyboard, contrast and reduced motion do not satisfy cohort evidence.

**Current residual from `v4.2.3#DF-2`**: Run the eight-step Training walkthrough with a cohort of five and record stalls and comprehension results.

**Partial disposition**: Both source patch entries represent the same inherited workshop obligation; preserve both origins. Rendered QA, keyboard, contrast and reduced motion do not satisfy cohort evidence.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.2#DF-2-v422 (reason: user-deferred); original `v4.2.2#DF-2`, section `v4.2.2 - guide-cinematic-rebuild`.

#### Original source: DF-2-v422 - The five-person workshop validation was not run

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/archives/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md` T027
- **Reason**: Inherited from v4.2.1 DF-1. No cohort of five participants exists to run a workshop against. Rendered QA, WCAG AA contrast, keyboard, and reduced-motion checks were all run and are recorded; the workshop specifically was not, and is not claimed.
- **Suggested next step**: When a cohort is available, run the eight-step Training walkthrough with five people and record where they stall. Until then this stays open rather than being marked satisfied by proxy evidence.

**Original source identity**: `v4.2.2#DF-2` in `v4.2.2 - guide-cinematic-rebuild`; normalized stable ID `DF-2-v422` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-66`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.2.2`, section `v4.2.2 - guide-cinematic-rebuild`, and original ID `DF-2`.

- **Migrated from**: v4.2#DF-2-v423 (reason: user-deferred); original `v4.2.3#DF-2`, section `v4.2.3 - guide-refinement`.

#### Original source: DF-2-v423 - The five-person workshop validation was not run

- **Source phase**: carried from v4.2.2 DF-2
- **Plan reference**: `docs/archives/v4/v4.2/plans/v4.2.3-guide-refinement.md` T031
- **Reason**: no cohort of five participants exists. Rendered QA, WCAG AA contrast, keyboard, and reduced-motion checks were all run and recorded; the workshop specifically was not, and is not claimed.
- **Suggested next step**: when a cohort is available, run the eight-step Training walkthrough with five people and record where they stall.

**Original source identity**: `v4.2.3#DF-2` in `v4.2.3 - guide-refinement`; normalized stable ID `DF-2-v423` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-66`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.2.3`, section `v4.2.3 - guide-refinement`, and original ID `DF-2`.

### AR-67: Technical and nontechnical comprehension and final visual review remain unverified

**Owner**: Guide owner and representative readers. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.4.6#MT-446-1`**: Obtain unassisted technical and nontechnical reader exercise results and final user visual review for D13/T026.

**Partial disposition**: Shares a human-training owner with v4.2 workshop but does not replace the five-person requirement with a two-person sample.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.4#MT-446-1 (reason: user-deferred); original `v4.4.6#MT-446-1`, section `v4.4.6 - guide-learning-experience`.

#### Original source: MT-446-1 - Technical and non-technical comprehension plus final user visual review are unverified; D13 and T026 remain open

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: MT-446-1

**Gap and gate impact**: Technical and non-technical comprehension plus final user visual review are unverified; D13 and T026 remain open

**Owner**: Guide owner and two readers

**Next step**: Complete the [unassisted exercise](../../../archives/v4/v4.4/development/guide-learning-experience/phase-7/manual-review.md), retain actual responses, and address unclear concepts before publication. Carries HT-4.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-67`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.4.6`, section `v4.4.6 - guide-learning-experience`, and original ID `MT-446-1`.

### AR-68: OpenClaw tool interception requires an independently scoped typed plugin

**Owner**: OpenClaw integration owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.3.0#DF-4`**: Scope or explicitly decline a typed OpenClaw plugin for actual tool interception and responsive-write guard parity; retain NOT COVERED until proof exists.

**Partial disposition**: Lifecycle hooks and native skills do not gate tool calls. AR56 Gemini/Kimi upstream hook-path issues are different capabilities.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.3#DF-4 (reason: vendor-feature); original `v4.3.0#DF-4`, section `v4.3.0 - agentic-verification-discipline`.

#### Original source: DF-4 - OpenClaw tool interception requires a typed plugin

- **Source phase**: Phase 5 platform-contract verification
- **Plan reference**: `docs/archives/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T023
- **Evidence**: Current official OpenClaw documentation exposes native skills and lifecycle hooks, but those managed hooks do not intercept or gate tool calls. Tool gating requires a typed plugin.
- **Impact**: Nexus-Hub can deliver verified OpenClaw skills and document lifecycle-hook discovery, but it cannot claim responsive-write guard parity through the native hook surface.
- **Owner**: Platform integration maintainer.
- **Next step**: Scope and review a typed OpenClaw tool-interception plugin in a future platform plan; until then, keep the guardrail surface explicitly `NOT COVERED` and do not synthesize a shell-hook port.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-68`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.3.0`, section `v4.3.0 - agentic-verification-discipline`, and original ID `DF-4`.

### AR-69: Native browser zoom and OS occlusion need real host qualification

**Owner**: Guide and browser qualification owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.4.6#MT-446-2`**: Verify native 200% browser zoom on a real host. Verify actual OS occlusion delivery and observed guide visibility behavior.

**Partial disposition**: Effective-width CSS reflow and an instrumented hidden-state test were explicitly narrower. Current hidden-animation fixes do not prove this host boundary.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.4#MT-446-2 (reason: user-deferred); original `v4.4.6#MT-446-2`, section `v4.4.6 - guide-learning-experience`.

#### Original source: MT-446-2 - Native 200% browser zoom and OS occlusion delivery are not proven by effective-width reflow or an instrumented hidden-state test

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: MT-446-2

**Gap and gate impact**: Native 200% browser zoom and OS occlusion delivery are not proven by effective-width reflow or an instrumented hidden-state test

**Owner**: Guide owner on the target browser/OS

**Next step**: Perform the environment exercise; retain browser, OS, observations, and any affected correction. Native/fallback fullscreen and reduced-motion handlers have automated proof.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-69`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.4.6`, section `v4.4.6 - guide-learning-experience`, and original ID `MT-446-2`.

### AR-70: Writing Discipline benefit has not been judged on real replies

**Owner**: Writing Discipline owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.5.0#DF-1`**: Compare real replies across at least two platforms with human judgments of cleaner versus stiff/canned wording.

**Partial disposition**: Presence/parity and detector fixtures do not measure usefulness or human quality.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.5#DF-1 (reason: user-deferred); original `v4.5.0#DF-1`, section `v4.5.0 - anti-cliche-and-agent-security`.

#### Original source: DF-1 - Whether the always-on Writing Discipline clause improves replies is unverified by a person

- **Source phase**: Phase 1 - Writing Discipline rule; Phase 7 - final review.
- **Plan reference**: sub-task 1.5 (measured cost) and Human and Manual Testing Suggestions item 2.
- **Reason**: The cost is measured and justified on its own terms (163 words, roughly 215 tokens per turn per platform in use; ceilings raised by exactly the delta and recorded in `docs/policy/doc-budgets.md`). The benefit cannot be measured by a test: whether the self-check clause changes a live reply, and whether the change is an improvement or stiffness, is a judgment a person makes by asking a cliche-prone question on two platforms and reading the answers. Nobody has done that yet.
- **Suggested next step**: Run human test 2 after the release lands on at least two platforms; if the replies read as stiff rather than cleaner, shorten the prohibition list before touching the self-check clause, since the clause is the load-bearing part (see the decision record `docs/decisions/implemented/policy/2026-09-04-writing-discipline-binds-chat-replies.md`).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-70`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.5.0`, section `v4.5.0 - anti-cliche-and-agent-security`, and original ID `DF-1`.

### AR-71: Repository agent isolation and transitive shared-service reachability remain unqualified

**Owner**: Agent-isolation owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.5.0#DF-2`**: Complete transitive reachability and shared-writable service enumeration for this repository agent environment. Address or explicitly disposition shared-checkout isolation failure and establish an out-of-process allowlist union with retained proof.

**Partial disposition**: Preserve the September24 partial real audit and its fail findings; do not falsely retain the title implication that no audit of any scope exists.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.5#DF-2 (reason: user-deferred); original `v4.5.0#DF-2`, section `v4.5.0 - anti-cliche-and-agent-security`.

#### Original source: DF-2 - No transitive-reachability or shared-writable-service enumeration has been performed on this repository's own agent surface

- **Source phase**: Phase 5 - Agent isolation; Phase 7 - final review.
- **Plan reference**: sub-task 7.3 prompt ("any egress reachability or shared-service enumeration this repository has not performed on its own agent surface") and Human and Manual Testing Suggestions item 4.
- **Reason**: The security comparison raised this as an open question about Nexus-Hub itself: any write-capable service reachable from more than one agent session (a package registry, an artifact store, a CI cache) is a channel until proven otherwise, and any allowlisted destination with its own reach is part of the agent's real reachability. The v4.5.0 plan shipped the controls as catalog guidance; it did not apply them to the agents that develop this repository (CI runners, the MCP servers under `extensions/`, the memory store). That application is a design exercise on real infrastructure, not a documentation task.
- **Suggested next step**: Run human test 4: take step 3 sub-steps 6 to 8 and step 5 sub-steps 5 to 7 of `agent-execution-isolation` and apply them to this repository's CI and local agent surface, producing the two named artifacts (the shared-writable-service enumeration and the transitive-reachability union). If the controls cannot be applied as written, they are too abstract and the skill should be revised.

**Bounded audit, 2026-09-24**: The [shared-writable-service inventory](../../../archives/v4/v4.5/development/isolation-audit/shared-writable-services.md) and [transitive-reachability assessment](../../../archives/v4/v4.5/development/isolation-audit/transitive-reachability.md) now name the observed local checkout, user cache, GitHub cache and artifact surfaces, direct GitHub API access, configured web-fetch egress, and CI runner limits. The local shared checkout fails the per-session isolation minimum, and no out-of-process egress allowlist was evidenced in the inspected configuration from which to prove a transitive union. DF-2 remains open; these records are findings and design inputs, not a security pass or an exhaustive host inventory.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-71`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.5.0`, section `v4.5.0 - anti-cliche-and-agent-security`, and original ID `DF-2`.

### AR-72: Manual distribution read-path and prose false-positive exercises remain unperformed

**Owner**: Installation and writing owners. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Clause ownership**: MT-1 tests 1 and 3 remain here (distribution read-back and judged prose false positives). Its test 2 is owned by AR-70 and test 4 by AR-71. AR-57 owns the overlapping agent/hook delivery proof; this entry adds the broader installed instruction read-path exercise. The complete MT-1 body below is retained as history, not a second count of AR-70/AR-71.

**Current residual from `v4.5.0#MT-1`**: Run MT-1 test 1: a throwaway installed instruction read-path exercise across three non-Claude platforms, retaining host observations. Run MT-1 test 3: a person judges prose false-positive behavior on their own writing. Tests 2 and 4 remain owned by AR-70 and AR-71, respectively.

**Partial disposition**: Keep one migration owner for this compound source to avoid duplicate provenance. Cross-link AR57 for live platform delivery, the Writing Discipline efficacy owner and the repository-isolation owner; each clause remains independently pending.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.5#MT-1 (reason: user-deferred); original `v4.5.0#MT-1`, section `v4.5.0 - anti-cliche-and-agent-security`.

#### Original source: MT-1 - The four human and manual tests have not been run

- **Source phase**: Phase 7 - final phase.
- **Plan reference**: Human and Manual Testing Suggestions, items 1 to 4.
- **Reason**: All four require a person: a throwaway install across three non-Claude platforms with a read-path check; a judged comparison of replies on two platforms; a hand-judged false-positive rate on the reader's own writing; an attempt to apply the shared-storage control to this repository's own agent surface. The installer was also not run live on this host by standing instruction, so item 1's distribution check rests on the installer smoke suites until a person runs it.
- **Suggested next step**: Run items 1 and 3 before `/update release` if time allows (they are quick); items 2 and 4 after the release, since they need the installed block and real infrastructure respectively. Record outcomes here; item 2 resolves `DF-1` and item 4 resolves `DF-2`.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-72`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.5.0`, section `v4.5.0 - anti-cliche-and-agent-security`, and original ID `MT-1`.

### AR-73: Five historical CodeQL alerts and the required-context decision remain open

**Owner**: Security and CI owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Security**: historical CodeQL alert disposition. **Severity**: high pending per-alert triage. **Partial closure**: hosted alert #242 is fixed (2026-09-13T03:53:12Z), with no dismissal; `_STAGING_MODE = 0o600` in current `_owned.py` and commit `5f4c76eb7` preserve owner-only staging. Alert #223 and alerts #349/#350/#329/#330 remain open on the fresh 2026-10-09 hosted read-back. SEC-1 alerts #278-285 are a different set and cannot discharge these five.

**Current residual from `v4.8#WN-K`**: Identify exact remaining historical alerts and fix or dismiss each with reasons plus a fresh scan receipt. Record whether CodeQL should be a required context and how stale-main base comparisons would be handled.

**Partial disposition**: The distributed mode defect is already repaired: commit5f4c76eb7, _owned.py _STAGING_MODE=0o600 and exclusive os.open, destination mode preservation, tests/integrations/test_owned_file_modes.py. Keep this partial closure as proof, not new installer work. Other alerts include validate_skills argparse-help false-positive shape and archived example tag/XSS findings; do not whole-close without exact receipts.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.8#WN-K (reason: user-deferred); original `v4.8#WN-K`, section `Open Items - found 2026-09-07 during the v4.8.0 adoption plan`.

#### Original source: WN-K - A high-severity CodeQL alert sits in DISTRIBUTED installer code, and the release-time CodeQL check is red against a stale base

- **Source**: found at the v4.8.0 release, on the `develop` to `main` pull request (#186).
- **What was observed**: `CodeQL` reported fail while both `Analyze` jobs succeeded and all five REQUIRED contexts passed. `CodeQL` is not a required context, so it did not block; the red is an artifact of comparing against a `main` that was 72 commits behind, which surfaces the whole accumulated line's alerts as new relative to that base. Every open high alert predates v4.8.0 and none was introduced by it, verified per-alert with `git blame`.
- **The one that matters**: `py/overly-permissive-file` at `scripts/lib/integrations/_owned.py:105`. `_atomic_replace_bytes` creates its temporary file with mode `0o666` before moving it into place, so between `os.open` and the rename the file is world-writable subject only to the caller's umask. This is DISTRIBUTED code: it ships in `scripts/` and runs on a user's machine during install. `0o600` (or `0o644` where readability matters) would close it with no behavioral cost, since the file is immediately renamed over the destination. Untouched by this release and therefore deliberately not changed inside a release flow.
- **The rest, for completeness**: `py/clear-text-logging-sensitive-data` at `scripts/validate_skills.py:1017` is an argparse help string from v1.2.0 whose wording mentions a secret scan, a false-positive-prone shape for that rule; two `py/bad-tag-filter` and two `js/xss-through-dom` alerts sit in `docs/archives/v3/v3.12/development/` worked examples, which are documentation and are not installed (`docs/` is outside the installer's copy roots).
- **Suggested next step**: fix the `_owned.py` mode in the next patch and re-run the scan, then triage the remaining four with `[[security-review]]` and either fix or dismiss each with a recorded reason. Separately, decide deliberately whether `CodeQL` should become a required context: today it can be red on a release pull request without blocking, which is either correct (it compares against a stale base and would wedge releases) or a gap (a real new vulnerability would also not block). That is a decision record, not a release-time edit.
- **Why it did not hold the release**: the required gate was fully green, the finding is pre-existing, and the one alert in distributed code is a file-mode hardening rather than an exploitable path in the install flow. Recorded rather than fixed, per the rule that a release-time finding becomes a known gap plus a follow-up patch.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-73`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.8`, section `Open Items - found 2026-09-07 during the v4.8.0 adoption plan`, and original ID `WN-K`.

### AR-74: Gemini and OpenCode eval configuration isolation remains unproved

**Owner**: Eval-pipeline owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.10#EV-1`**: Prove exclusion of Gemini CLI system,user,project,environment and command-line configuration for each eval baseline before enabling provider-backed execution.

**Partial disposition**: GEMINI_CLI_HOME and -e none affect subsets only. Keep current fail-closed behavior; no provider-backed run was made in the source recheck.

**Current residual from `v4.10#EV-2`**: Prove exclusion of OpenCode global,project,remote,managed settings,instructions and plugins before enabling provider-backed execution.

**Partial disposition**: --pure disables plugins; additive config directories/inline overrides do not remove merged layers. Keep current fail-closed behavior.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.10#EV-1 (reason: vendor-feature); original `v4.10#EV-1`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`.

#### Original source: EV-1 - Gemini CLI has no documented all-configuration isolation flag

- **Source phase**: v4.10.1 Phase 2 (T005-T009).
- **What was observed**: the official CLI documents `-e none` for disabling extensions and `--model` for model selection, but separately documents system, user, project, environment, and command-line configuration layers. No flag in the checked official reference excludes them as a whole.
- **2026-09-25 source recheck**: the [current configuration reference](https://geminicli.com/docs/reference/configuration/) documents `GEMINI_CLI_HOME` for user-level configuration and storage, plus separate overrides for system settings paths. It still describes project settings and environment inputs as independent layers. A per-job home alone does not establish the all-configuration isolation needed for a comparable baseline; no provider-backed run was made in this recheck.
- **Current behavior**: provider-backed skill evals requested with `--cli gemini` fail closed before spawning the CLI. Their results are not represented as isolated or comparable.
- **Suggested next step**: establish a documented and tested per-run exclusion of every configuration source before enabling this branch; otherwise keep it fail-closed.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-74`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.10`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`, and original ID `EV-1`.

- **Migrated from**: v4.10#EV-2 (reason: vendor-feature); original `v4.10#EV-2`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`.

#### Original source: EV-2 - OpenCode has no documented all-configuration isolation flag

- **Source phase**: v4.10.1 Phase 2 (T005-T009).
- **What was observed**: the official CLI documents `--pure` as disabling external plugins and documents config path overrides, but no checked flag excludes all operator configuration, instructions, and saved settings.
- **2026-09-25 source recheck**: the [current configuration reference](https://dev.opencode.ai/docs/config/) says configuration files are merged, `OPENCODE_CONFIG_DIR` adds a searched directory after global and project directories, and managed settings override all user-controlled layers. A custom directory or inline override therefore does not prove that operator configuration was excluded; no provider-backed run was made in this recheck.
- **Current behavior**: provider-backed skill evals requested with `--cli opencode` fail closed before spawning the CLI. Their results are not represented as isolated or comparable.
- **Suggested next step**: establish a documented and tested per-run exclusion of global, project, remote, and managed settings before enabling this branch; otherwise keep it fail-closed.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-74`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.10`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`, and original ID `EV-2`.

### AR-75: GitHub retained read-only PR references require an explicit scope disposition

**Owner**: Repository owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.12.0#QG-1`**: Record the owner disposition of GitHub-retained read-only PR refs outside writable branch/tag publication. If complete purge is required, obtain GitHub supported administrative disposition rather than normal force pushes.

**Partial disposition**: Preserve captured writable/local proof scope and the212 read-only refs limitation. No promise that every old SHA or GitHub mirror disappears.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.12#QG-1 (reason: user-deferred); original `v4.12.0#QG-1`, section `v4.12.0`.

#### Original source: QG-1: GitHub retains read-only pull-request refs

**Source phase**: Phase 4 independent review. **Plan reference**: Goal, T020 and T023. **Reason**: 212 `refs/pull/*` exist on GitHub outside the 119 writable branches/tags. They cannot be replaced by a normal force-push; the local all-ref proof covers the captured 139 local refs, not every GitHub-retained ref.

**Owner**: Repository owner. **Suggested next step**: approve the explicit writable-ref publication scope only with this limitation understood; observe both default-branch contributor surfaces afterward. If purging every GitHub-held ref is required, obtain GitHub's supported administrative disposition separately. Do not promise old SHA disappearance or a clean GitHub mirror that fetches PR refs.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-75`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.12.0`, section `v4.12.0`, and original ID `QG-1`.

### AR-76: The public contributor view needs rendered confirmation or GitHub Support disposition

**Owner**: Repository owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.12.0#QG-2`**: Recheck the public Code contributor surface and reconcile it with API/Insights/user screenshot evidence. If still incorrect, repository owner submits the prepared GitHub Support handoff for supported cache correction or explanation.

**Partial disposition**: API and Insights passed; public Code still showed five on September25. Stale cache is an inference. No ticket submitted and no additional history rewrite justified.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.12#QG-2 (reason: user-credential); original `v4.12.0#QG-2`, section `v4.12.0`.

#### Original source: QG-2: GitHub contributor-view confirmation pending

**Recheck, 2026-09-25**: A fresh unauthenticated Chromium render of the public Code page still shows `Contributors 5` and links to `bendourthe`, `cursoragent`, `benjamin-dourthe`, `claude`, and `dependabot[bot]`. The contributors API returns only `bendourthe` with 1,753 contributions, and current `main` and `develop` shortlogs contain only Ben Dourthe's author identity. A stale GitHub presentation cache is an inference, not a confirmed cause. The [Support handoff draft](../../../archives/v4/v4.12/development/contributor-sidebar-recheck-2026-09-24.md) remains ready; no ticket was submitted. QG-2 stays open.

**Recheck, 2026-09-24**: A fresh unauthenticated Chromium render still shows `Contributors 5` with the same five avatar labels, while both read-only contributor APIs return only `bendourthe`. The [dated recheck and Support handoff draft](../../../archives/v4/v4.12/development/contributor-sidebar-recheck-2026-09-24.md) retain browser version, counts, default-branch SHA and the exact acceptance boundary. QG-2 stays open; no new history rewrite is justified.

**Recheck, 2026-09-22**: The live contributors API now returns only `bendourthe` (1,753 contributions), and the statistics API also returns only `bendourthe` (1,394 non-merge commits). A fresh, unauthenticated Chromium rendering of the public [Code page](https://github.com/bendourthe/Nexus-Hub) still shows `Contributors 5`; its avatar labels identify `bendourthe`, `cursoragent`, `benjamin-dourthe`, `claude`, and `dependabot[bot]`. The rendered Code result fails the one-contributor criterion despite the API results. No new history rewrite is justified by this discrepancy.

**Source phase**: Phase 4. **Plan reference**: T021-T023. **Reason**: the owner approved publication, all 120 reviewed writable refs were updated, both protections were restored exactly, and all five required checks passed. The fresh public clone scans 1,687 commits with zero findings. At `20260914T232622Z`, the contributor API still returned `bendourthe` (1655), `dependabot[bot]` (8), while the Insights default-main graph data contained only `bendourthe` (1,345 non-merge commits). Subsequent user screenshot 1 confirms Insights with Period: All, main, excluding merge commits, showing only bendourthe with 1,345 commits. Screenshot 2 confirms the published ba468f5 tip and a Code sidebar labeled Contributors 5. The other account names cannot be established from the avatars alone. The live API recheck still lists bendourthe and dependabot[bot], while the statistics endpoint lists only bendourthe. The rendered Code result therefore fails the one-contributor criterion; Insights passes. This discrepancy is consistent with GitHub's documented refresh delay, but the Code result is not yet resolved.

**Owner**: Repository owner and publication operator. **Suggested next step**: contact GitHub Support with the publication receipts, earlier screenshots, and the fresh Code-sidebar result; request a supported contributor-cache correction or explanation. Insights is already confirmed by the user's screenshot. GitHub documents about 24 hours for contributor displays to refresh after history changes and recommends contacting Support if they remain incorrect after that window. See [GitHub's stale-contributor guidance](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-a-projects-contributors#contributor-data-is-stale-after-history-changes). No further history rewrite is warranted by the current evidence. Existing releases and assets are already verified unchanged. No public-view success or release completion is claimed.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-76`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.12.0`, section `v4.12.0`, and original ID `QG-2`.

### AR-77: Antigravity legacy workflow retirement needs a dated vendor check

**Owner**: Antigravity integration owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.12.0#DF-1`**: After2026-11-01 recheck the vendor retirement date, then remove legacy commands_to_slash workflow emission/config destinations and requalify the platform contract.

**Partial disposition**: Before that date retain dual Skill/workflow distribution so older builds keep their slash surface. AR36 can reference this dated owner without collapsing it into general readback.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.12#DF-1 (reason: vendor-feature); original `v4.12.0#DF-1`, section `v4.12.0`.

#### Original source: DF-1: Antigravity workflow surface retires on 2026-11-01

**Source phase**: v4.12.1 release, platform-contract verification (2026-09-16). **Plan reference**: /update release governance step 4. **Reason**: the vendor documents retirement of the legacy workflow format on 2026-11-01 in favour of the Agent Skills standard. Nexus-Hub already emits every command as BOTH a skill and a workflow (`scripts/lib/integrations/antigravity.py` calls `commands_to_skills` alongside `commands_to_slash`), and the vendor states skills take precedence where both exist, so the skill copy is already what Antigravity executes.

**Impact**: none before the retirement date, and none after it for the skills surface. No re-architecture is required for Antigravity to remain supported.

**Why not now**: dropping workflow emission before the date would remove the slash surface for anyone still on a pre-retirement build. Shipping both is the correct posture until the date passes.

**Owner**: Antigravity integration maintainer. **Status**: open, dated. **Suggested next step**: after 2026-11-01, remove the `commands_to_slash` workflow emission from the Antigravity integration, drop `commands_subdir`/`ide_commands_subdir` from its config, update the read-contract row, and re-run the platform-contract verification. Re-check the date against the vendor page before acting, in case retirement slips.
**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-77`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.12.0`, section `v4.12.0`, and original ID `DF-1`.


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

#### BG-2-v4131: A test in the full profile writes into the real user's `~/.nexus-hub`

**Source phase**: Phase 9 (full local profile, 2026-09-26). **Plan reference**: T028. **Reason**: during `python scripts/ci/run.py --profile full` (17:46 to 19:53 local time), the real `~/.nexus-hub/scripts/nexus_git_attribution.py` was overwritten at 18:22 with this branch's version, and `~/.nexus-hub/VERSION` and `~/.nexus-hub/permissions-manifest.json` were rewritten at 18:36. Some test ran the real installer against the machine's own home folder instead of a throwaway one (a PowerShell run resolves the home from `USERPROFILE`, so redirecting `HOME` alone does not isolate it). The overwrite made `nexus-hub attribution check` fail with "Attribution guard version differs"; the file was restored from the durable guard (`~/.nexus-hub/git-hooks/guard.py`, which matches `develop`), a backup of the overwritten copy was kept outside the repository, and the check passes again. `VERSION` kept its value (4.13.0). This is most likely pre-existing: earlier runs from `develop` would have copied an identical file and gone unnoticed; it surfaced because this branch changed the script. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: in a disposable Windows account or container, snapshot the home folder, run the full profile group by group, and diff after each to find the test; then isolate it with both `HOME` and `USERPROFILE` (and `APPDATA`, `LOCALAPPDATA`), and add a guard that fails the profile when the real home changes. **Full inventory (2026-09-26)**: a scan of `~/.nexus-hub`, `~/.claude`, `~/.codex`, `~/.gemini`, `~/.cursor`, and the VS Code user settings for files modified during the run found only the three files above plus, in `~/.nexus-hub/state/`, lock files and backups of test fixtures (instruction files headed `# org-test` and `# org-lifecycle`), written by the organization-layer tests. The user's real instruction files (`~/.claude/CLAUDE.md` last changed 2026-09-23, the Codex, Gemini, OpenCode, and Qwen files 2026-09-15) and platform settings were not touched. The leftover fixture backups and locks contain no user data and are safe to delete. So at least two tests leak into the real home: one runs the real installer (the attribution script, `VERSION`, and the permissions manifest), and the organization tests write their backups and locks to the real state folder.

**Local repair (2026-09-27)**: the Bash and PowerShell selection-parity installer tests now provide a disposable `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `NEXUS_HUB_HOME`, and Git global-config path; both real installer tests passed, and the PowerShell test confirmed the attribution script landed under the disposable Nexus home. The instruction merger's state root now honors `NEXUS_HUB_HOME` for workspace installs while retaining explicit global-target precedence; a red-then-green root test and 42 organization/merger tests passed. The local full profile was not rerun against the real account. **Status**: open until protected hosted integration verifies this repair; audit any remaining full-profile home writers separately.

**Second writer found (2026-10-02, v4.13.7 Phase 9)**: the v4.13.7 full profile rewrote 52 files under the real `~/.nexus-hub/scripts/`, `permissions-manifest.json`, and `VERSION` (content unchanged at 4.13.6) at 14:51 UTC, while `repo-tests-skills` ran; the rewritten scripts were byte-identical to the v4.13.7 worktree. The writer was `tests/skills/test_presentify_dual_view_distribution.py::test_installed_bundle_runs_offline`, which ran both real installers with the inherited environment. It now redirects the same six variables; rerun alone, it gave `2 passed` with a real-home snapshot identical before and after (v4.13.7 BG-8). The attribution script still matched the durable guard and `nexus-hub attribution check` printed `VERIFIED`. Other full-profile groups were not audited for writers one by one, so this item stays open.

**Original source identity**: `v4.13.1#BG-2`; stable ID `BG-2-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-7-v4131: A generated-with footer followed by a long clause passes the attribution hook

**Source phase**: Phase 9 (adversarial pass). **Plan reference**: T014. **Reason**: to let descriptive sentences pass, a footer counts only when it ends at the agent's name, a link, or a clause of at most four words after `-`, `:`, `,`, or `|`. "Generated with Claude Code, then reviewed and edited by hand before merge" therefore passes on `gh` routes; the Git commit-msg hook still blocks it on commits. **Owner**: catalog maintainer. **Status**: open, accepted trade-off. **Suggested next step**: collect real footers from harness defaults and tune the clause limit against them.

**Original source identity**: `v4.13.1#WN-7`; stable ID `WN-7-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-1-v4131: A user edit made between sessions is preserved but not reported

**Source phase**: Phase 8. **Plan reference**: T019, [`v4.13.1-incident-replay.md`](development/v4.13.1-incident-replay.md). **Reason**: in scenario B the revision request arrives in a new session. All six Claude runs edited the deck in place (so the edit survived) but none named the edit: the new session does not treat the deck as a file it wrote, and its in-place save runs as inline `python -c`, which `user-edit-guard` does not read (it reads script files). **Owner**: catalog maintainer. **Status**: open. **Update (Phase 9 deep pass)**: the hook now also reads inline `python -c`, `node -e`, and `pwsh -Command` code for document paths (`test_deep_pass_writer_routes_are_blocked`), which removes the cause observed in the replay; this is covered by tests but not re-measured. **Suggested next step**: measure scenario B again (with WN-2 and WN-5).

**Original source identity**: `v4.13.1#WN-1`; stable ID `WN-1-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-2-v4131: A moved picture was never named in the agent's report

**Source phase**: Phase 8. **Plan reference**: T019. **Reason**: in scenario C, eight of eight runs named the user's new speaker note but none the moved picture; the helper listed the picture move only as a changed part name. The diff now prints "non-text change on slide N ...: tell the user about it", covered by tests but not re-measured by a paid run. **Owner**: catalog maintainer. **Status**: open until measured. **Suggested next step**: re-run scenario C (three Claude trials per condition) with the current helper.

**Original source identity**: `v4.13.1#WN-2`; stable ID `WN-2-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-3-v4131: Codex replay runs can see the machine's real user skills

**Source phase**: Phase 8. **Plan reference**: T018. **Reason**: Codex resolves the home folder through the Windows known-folder API, not `HOME`, so replay runs also load `~/.agents/skills` from the real profile. One Codex run did not find `edit_guard.py` and edited without the helper. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: run Codex replays under a separate Windows user or in a container, and check whether Codex prefers the workspace `.agents/skills` over the global one.

**Original source identity**: `v4.13.1#WN-3`; stable ID `WN-3-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-4-v4131: Antigravity 2.0 and Windsurf do not receive the guard hooks

**Source phase**: Phase 9 (implementation convergence). **Plan reference**: Definition of Done 3 ("on hook-capable platforms"). **Reason**: both adapters register a curated hook list with their own tool names and event names (`scripts/lib/integrations/antigravity.py` `_hook_registration`, `scripts/lib/integrations/windsurf.py` `_CASCADE_HOOKS`), so neither installs `user-edit-guard` or `attribution-guard`. The new hooks read Claude-style `tool_input.file_path` and `tool_input.command`; registering them where the payload fields are unverified would install hooks that silently pass everything. The always-loaded rule and the skill still reach both platforms. **Owner**: catalog maintainer, with [[platform-contract-verification]]. **Status**: open. **Suggested next step**: verify each platform's hook payload from a fetched vendor document, map its field names in `edit_guard.py hook` and the attribution scan, then add both hooks to the curated lists with a test per platform.

**Original source identity**: `v4.13.1#WN-4`; stable ID `WN-4-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-5-v4131: Scenario D (deck left open) was not re-measured on Claude after the fixes

**Source phase**: Phase 9 (implementation convergence). **Plan reference**: T019. **Reason**: the final replay round covered scenarios A, B, and C on Claude by the maintainer's reduced design; scenario D ran on Claude only in rounds 1 and 2 (before the second fix cycle) and on Codex in round 3, and every run preserved the edit. The post-fix Claude result for D is unmeasured. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: include scenario D in the WN-1 and WN-2 re-measurement.

**Original source identity**: `v4.13.1#WN-5`; stable ID `WN-5-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-6-v4131: Accepted blind spots of `user-edit-guard`

**Source phase**: Phase 9 (adversarial pass). **Plan reference**: T013. **Reason**: the hook cannot see a destination computed at run time inside a script (for example `'deck' + '.pptx'`), a destination held in a shell variable (`cp x "$OUT"`), or a user edit saved within 5 seconds of the agent's own write (the settle window that absorbs parallel formatter hooks). Two more are accepted by design after the Phase 9 deep pass: without hooks, a user edit that lands inside an agent's command-line check-write-record sequence (at most 120 seconds after the check) is recorded as the agent's, because the helper cannot tell who changed the file; and inside a git work tree an unrecorded or tracked file only warns, so an agent that runs `git init` around an unrecorded file gets a warning instead of a block (blocking unrecorded files stalled build logs and ignored outputs). Deliberate timestamp forgery by an agent evading the rule is outside the threat model. The always-loaded rule and the skill's `check` are the protection there. **Owner**: catalog maintainer. **Status**: open, accepted risk. **Suggested next step**: treat a `$`-bearing destination outside a worktree as "cannot verify" once its false-block rate is measured.

**Original source identity**: `v4.13.1#WN-6`; stable ID `WN-6-v4131` distinguishes this obligation from repeated IDs in other patch sections.

#### MT-1-v4131: No paid measurement of the rule on a platform other than Claude and Codex

**Source phase**: Phase 8. **Plan reference**: T018. **Reason**: the replay measured Claude Code (with and without the hook) and Codex. Copilot, Cursor, Gemini, and the rule-only platforms receive the same always-loaded rule and skill but were not measured. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: add one rule-only platform to the next replay.

**Original source identity**: `v4.13.1#MT-1`; stable ID `MT-1-v4131` distinguishes this obligation from repeated IDs in other patch sections.

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

#### WN-4-v4132: A headless OpenCode run cannot create a run record, so it cannot reach `PLAN COMPLETE`

**Source phase**: Phase 8 (T017), OpenCode pilot 3. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `record create` accepts an approval only from a captured prompt or from `yes` typed on the terminal device, and fails closed otherwise. OpenCode documents no prompt-submit lever (`docs/policy/completion-levers.json`, checked 2026-09-25), and `opencode run` attaches no terminal, so a scripted headless first turn can never be recorded. The plan's condition C assumed it could. The pilot showed the consequence before the runbook rule existed: the agent restated the approvals in a table and pushed, tagged, and released without a record.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: measure OpenCode interactively (the user answers `yes` at the terminal), or capture approvals through a documented OpenCode event once one exists; never infer a prompt-submit lever from `message.*` events.

**Original source identity**: `v4.13.2#WN-4`; stable ID `WN-4-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-7-v4132: On OpenCode a full run proceeds on in-prompt approvals without a run record

**Source phase**: Phase 8 (T017), condition C runs C4 to C6. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: with no record possible (WN-4), OpenCode 1.18.32 running Claude Sonnet 4.6 restated the approvals as a table, called them recorded, never ran `record create` or `record path`, and pushed, merged, tagged, and released. Every action matched the approval the prompt contained, and the completion gate and runner took no action without a record, but the run did not stop at the first approval point as the runbook requires. Two instruction changes (the Phase 0a rule and the point-of-use `record path` check) did not change the behavior. With the user's decision of 2026-09-27, v4.13.2 ships full-by-default on every platform with this gap recorded; OpenCode is reported as not verified.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: enforce the rule rather than state it: an OpenCode plugin on the documented `tool.execute.before` event could refuse `git push`, `gh pr merge`, and `gh release create` while an `/implement` run holds no record, once a reliable signal for such a run exists.

**Original source identity**: `v4.13.2#WN-7`; stable ID `WN-7-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### MT-1-v4132: Condition B (Codex) has one passing end-to-end run

**Source phase**: Phase 8 (T018). **Plan reference**: [v4.13.2 plan, Phase 8](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: after B7 reached `PLAN COMPLETE`, the OpenAI pilot key returned `Quota exceeded. Check your plan and billing details.` before any turn, so the planned second run did not happen; one run shows the chain works on Codex but bounds no failure rate.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: rerun condition B in WSL (`tests/e2e/implement_full/run_e2e.py --agent codex`) once the OpenAI limit allows, and record the result in the e2e evidence.

**Original source identity**: `v4.13.2#MT-1`; stable ID `MT-1-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-8-v4132: The run record's signature does not cover `pause` or `blockers`

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `approvals_hmac` now covers `start_head`, `nonce`, and `created` (fixed in this phase), but `pause` and `blockers` are rewritten by several writers (`record pause`, `record block`, the capture hook), so an edit that clears the user's pause or closes an open blocker is not reported as `record-tampered`.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: have every writer re-sign through one checker function, then add both fields to the signed payload.

**Original source identity**: `v4.13.2#WN-8`; stable ID `WN-8-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-9-v4132: Approval capture binds typed text, not the approval class - PARTIALLY RESOLVED 2026-09-29

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Original defect**: `approval-capture` stores a digest of every submitted prompt line, and `record create` accepts an approval whose text matches any captured line. A short reply such as `ok`, a pasted issue body containing "I approve release", or the agent piping a fabricated payload into `completion_gate.py capture` can therefore back an approval class the user never approved. Severity high: this is the threat the contract names.

**Resolved part**: [v4.13.6 Phase 1](plans/v4.13.6-minor-scope-implement-and-verified-cleanup.md) binds every user-origin record write (`record create`, `record answer`, `record pause`, `record resume`) to the exact line the checker generated. `record render` builds the canonical page data, draws a fresh 128-bit round nonce, derives an 8-character single-use code from `HMAC-SHA256(runs secret, page and nonce)`, and writes an owner-only pending round sealed by an HMAC over every field. The write then requires the seal and the live page's code to verify, the bound session (and, for a mid-run answer, pause, or resume, the run record's session), exactly one captured whole prompt equal to the line, and an earlier prompt in that session from before the render, and consumes the round. The capture hook stores only whole-prompt digests with a capture time and skips sessions marked `NEXUS_RUNNER_LAUNCH=1`, which `run_plan.py` sets for every session it launches. The terminal fallback was removed: a missing capture file now refuses, because a process that owns the console or a pty can type into it. So a lone "ok", a quoted code, a pasted body, a replayed or superseded line, a runner-launched prompt, an edited pending round, a fresh headless session opened only to submit the line, and an answer captured in another session never record. The rule is owned by the completion contract's Approval origin section.

**Still open**: the third bypass this item names, an approval the agent itself originates. The agent can pipe a fabricated payload into `completion_gate.py capture`, append a line to the capture file, or pre-seed a nested headless session (`claude -p` with `--session-id`, then resume it with the line), and the capture is indistinguishable from the user's paste. `tests/e2e/implement_full/stub_agent.py` does exactly the first of these to stand in for the user, and the harness passes. The original suggested step "refuse a capture the agent's own tool call produced" is not done; no signal the agent cannot also set (environment, session id, process tree) was found in this pass. Two related limits: the round expires 30 minutes after render, not when the session ends, so a later session can record a line pasted in an earlier one (bound to the session where it was captured); and on a platform with no prompt-submit capture no approval can be recorded at all, so the run asks at each approval point (see WN-4 and DF-5).

**Evidence**: `tests/validators/test_approval_binding.py` (29 passed, 1 POSIX-only skip on Windows): `test_exact_line_records_once_then_reads_code_used`, `test_a_prompt_that_is_not_the_whole_line_never_records[lone-ok|quoted-code|pasted-body|line-plus-text]`, `test_a_line_replayed_from_an_earlier_consumed_round_is_refused`, `test_a_newer_render_invalidates_the_older_code`, `test_a_runner_launched_prompt_is_never_captured`, `test_record_create_refuses_inside_a_runner_launched_session`, `test_a_plan_edit_after_render_reads_page_changed`, `test_an_expired_code_is_refused`, `test_a_mid_run_answer_needs_its_own_exact_line`, `test_a_fresh_session_that_only_carries_the_line_is_refused[auto|nested-agent]`, `test_an_edited_pending_round_is_refused[paste_digests|paste_lines|expires_at|rendered_at|session]`, `test_a_mid_run_answer_captured_in_another_session_is_refused`, `test_a_session_with_no_capture_file_refuses_without_a_terminal_fallback`, `test_pending_file_is_owner_only_on_posix`; plus `test_capture_skips_a_runner_launched_session` and `test_runner_launched_capture_drains_a_large_payload` (both hook implementations) and `test_every_launched_session_is_marked_runner_launched`.

**Owner**: catalog maintainer. **Status**: open (agent-originated capture); the resolved part is local in v4.13.6 Phase 1 and not yet integrated. **Suggested next step**: find a capture signal the agent's own tool calls cannot produce (for example a host-issued per-prompt attestation, if a platform documents one); until then, keep the threat model's statement that a deliberately forged user origin is not detected.

**Tracking alias retained**: `v4.13.6#WN-5`; the following complete historical source has the same current obligation and is not a separate future task.

##### Tracking source: v4.13.6#WN-5 (v4.13.6): v4.13.2 WN-9 is only partly closed

**Evidence**: Definition of Done 3 says it closes v4.13.2 WN-9 for every record type. Every bypass it names (a lone "ok", a quoted code, a pasted issue body, a runner-launched prompt) is refused by `tests/validators/test_approval_binding.py`, but the agent can still originate its own capture (pipe a payload into `completion_gate.py capture`, append to the capture file, or pre-seed a nested session), which is why that entry reads PARTIALLY RESOLVED. This pointer keeps the remainder visible in this plan's section; the item itself stays tracked under v4.13.2 WN-9. **Owner**: catalog maintainer. **Suggested next step**: bind a capture to a platform-authenticated user-turn signal where one exists, and record `cannot-verify` otherwise.

**Original source identity**: `v4.13.2#WN-9`; stable ID `WN-9-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-11-v4132: `run-plan` checks only global settings for an approval bypass

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `bypass_configured` reads the platform's global config with regular expressions. A committed project `.claude/settings.json` with `defaultMode: bypassPermissions`, a single-quoted `approval_policy = 'never'`, or the Cursor, Copilot, OpenCode, and Kimi rows (no check at all) pass unnoticed.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: parse JSON and TOML instead of matching text, include the project-scoped settings under the launch directory, and refuse a row with no check unless `unattended-with-bypass` is approved; confirm first which platforms honor project-level bypass settings.

**Original source identity**: `v4.13.2#WN-11`; stable ID `WN-11-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-12-v4132: `integration.checks` and `release.version-sync` read the working tree

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the checker reads `docs/policy/required-checks.json` and runs the project's version-sync script from the working tree, so an edit to either changes what "required" means or what runs at every turn end.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: read the manifest from `origin/<target>` and run version sync from the record's `start_head` tree, or keep version sync out of the turn-end gate.

**Original source identity**: `v4.13.2#WN-12`; stable ID `WN-12-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-13: Record lifetime and environment edge cases

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: three low-severity cases. A pull request opened moments ago may answer `no checks reported on the '<branch>' branch`, which is not in the not-found list and reads as `cannot-verify` (text reasoned from `gh`'s source, not reproduced). A record bound to the same session never expires, so a session resumed weeks later still carries its approvals. A home directory that is itself a git working tree, or a `GIT_DIR` in the environment, makes every record read as tampered.

**Owner**: catalog maintainer. **Status**: open, partially repaired and integrated through [PR #374](https://github.com/bendourthe/Nexus-Hub/pull/374) at `510fd987`; its required checks passed with one expected skip, and [post-merge run 36455108200](https://github.com/bendourthe/Nexus-Hub/actions/runs/36455108200) passed smoke and provenance. Same-session and unspecified-session records older than 72 hours are now ignored, and inherited Git repository selectors no longer misclassify an untracked private record inside a home Git tree; a tracked record still blocks as tampered. The 104 focused checker and runner tests passed, including negative controls for an extra `gh` error and a tracked record. The fresh-PR `no checks reported` text is handled in the checker and stub tests, but the exact stderr remains unverified: `gh pr checks 374` already showed pending jobs immediately after PR creation. **Suggested next step**: capture the live no-checks response on a future newly opened PR and compare it to the guarded pattern before closing this item; keep malformed or additional errors as `cannot-verify`.

#### DF-5-v4132: Approval capture is missing on Pi, OpenClaw, Hermes, and Windsurf

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `docs/policy/completion-levers.json` records a VERIFIED prompt-submit lever for these four platforms, but only Claude-format registrations and Cursor carry `approval-capture`, so on them `record create` cannot record an approval (the same effect as WN-4 on OpenCode). **Update (v4.13.6 Phase 1)**: the terminal fallback was removed, so on these platforms `record create` now refuses with `approval-not-captured` even in an interactive session until capture is added.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: add capture on each platform's documented prompt event in its plugin or hook adapter, with a parity test.

**Original source identity**: `v4.13.2#DF-5`; stable ID `DF-5-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-6: Copilot CLI gets no goal at all - RESOLVED

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: Copilot CLI's documented headless goal needs `--autopilot --yolo`, which the runner's denylist forbids, and the runbook prints an interactive goal line only for platforms whose goal is interactive-only, which the levers matrix does not mark Copilot CLI as.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: classify Copilot CLI's goal as interactive-only in the levers matrix and document why.

**Normalization, 2026-10-09 (v4.13.11 T006)**: Parsed RESOLVED marker records the already evidenced disposition retained above. No new runtime or historical capture is claimed.

#### DF-7-v4132: Recorded design deltas from Phases 2, 4, and 6

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: accepted deviations recorded only in phase histories until now: the per-run spend cap became `--max-cycles` (Phase 6); the gate infers its output format from the payload instead of `NEXUS_GATE_FORMAT`, reuses the existing handler ownership check instead of exact-identity manifest entries, and never marks degraded enforcement in the record (Phase 4); and the Phase 2 throwaway install check could not finish on Windows and was confirmed by the Phase 3 seven-platform install instead.

**Owner**: catalog maintainer. **Status**: open (accepted). **Suggested next step**: revisit the degraded-enforcement mark and a spend cap when a platform documents per-run spend reporting; no other change is needed.

**Original source identity**: `v4.13.2#DF-7`; stable ID `DF-7-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### MT-2: No real CLI run exercised a gate refusal or a runner resume

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: every passing Phase 8 run on Claude Code and Codex reached `PLAN COMPLETE` in its first turn, so the turn-end gate's refusal and the runner's resume are proven by stub tests (`test_harness.py`, `test_completion_gate.py`) and never by a paid session.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: run one paid condition with a fixture that cannot finish in one turn (for example a phase whose test only passes after a second commit) and record the gate and runner cycles. **Update (v4.13.6 Phase 1)**: under exact binding, the paid conditions in `tests/e2e/implement_full/run_e2e.py` (`--agent claude|codex|opencode`) cannot record: their first turn states the approvals verbatim in the prompt, which never equals a line `record render` generates, so `record create` refuses (`approval-not-captured` or `session-too-new`) and the run cannot reach `PLAN COMPLETE`. Owner: v4.13.6 Phase 7. The paid first turn needs a render step whose printed line is then fed as a second scripted user turn in the same session, before any paid run is spent on this item.

#### DF-1-v4132: Devin Desktop reads `.devin/hooks.json`, which the Windsurf integration does not model

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the Cascade hooks page (fetched 2026-09-25, [docs.devin.ai/desktop/cascade/hooks](https://docs.devin.ai/desktop/cascade/hooks)) lists `~/.codeium/windsurf/hooks.json` (user), `.devin/hooks.json` (workspace), and a system file. The `windsurf` integration writes native hooks but its read contract predates the `.devin/hooks.json` workspace path. No continuation lever exists on this surface either way (`post_cascade_response` is asynchronous), so the completion gate is unaffected; the drift matters for the guardrail hooks.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: at the next `/update release` platform pass, re-verify the Cascade workspace hook path and update `docs/policy/platform-read-contracts.json` and `scripts/lib/integrations/windsurf.py` together.

**Original source identity**: `v4.13.2#DF-1`; stable ID `DF-1-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-2-v4132: Antigravity 1.0 hook support is unconfirmed while the integration declares none

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `scripts/lib/integrations/antigravity.py:75` sets `hooks_supported: False` for Antigravity 1.0. The hooks page ([antigravity.google/docs/hooks](https://antigravity.google/docs/hooks/), fetched 2026-09-25) says hooks work across "Antigravity 2.0, Antigravity CLI, and Antigravity IDE" without stating whether that IDE is the 1.0 product. The plan's premise that 1.0 supports hooks is therefore not confirmed; `completion-levers.json` records every 1.0 lever as "none documented".

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: confirm against a first-party page scoped to Antigravity 1.0, or by observing a registered hook fire in a 1.0 install; change `hooks_supported` only on that evidence.

**Original source identity**: `v4.13.2#DF-2`; stable ID `DF-2-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-3-v4132: Devin CLI reads Claude Code's hook files, so Claude registrations also reach it

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the Devin CLI hooks overview ([docs.devin.ai/cli/extensibility/hooks/overview](https://docs.devin.ai/cli/extensibility/hooks/overview), fetched 2026-09-25) lists `.claude/settings(.local).json`, `~/.claude.json`, and `~/.claude/settings(.local).json` among its configuration sources. Every Claude hook Nexus-Hub registers therefore also runs under Devin CLI, which the read contract does not state. The completion gate relies on this deliberately (the `top-level-block` shape matches); other hooks may meet payload shapes they were not tested against.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: record the shared read in `docs/policy/platform-read-contracts.md` and add a Devin-CLI payload case to the hook parity tests for any hook that inspects payload fields.

**Original source identity**: `v4.13.2#DF-3`; stable ID `DF-3-v4132` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-4-v4132: OpenClaw and Hermes completion plugins need a manual enable step

**Source phase**: Phase 5 (T011). **Plan reference**: [v4.13.2 plan, sub-task 5.1](plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: OpenClaw loads a user plugin only when `plugins.entries.<id>.enabled` is set and its conversation hook is allowed (`hooks.allowConversationAccess`); Hermes loads one only when its name is in `plugins.enabled` in `~/.hermes/config.yaml`. The research on 2026-09-25 verified both requirements but not the exact config file locations and shapes verbatim, so the installer places the plugin files and reports NEEDS SETUP with each platform's documented enable command (`openclaw plugins enable nexus-completion-gate`, `hermes plugins enable nexus-completion-gate`) instead of editing an unverified config path. Until the user runs it, a full run on those two platforms continues only through `nexus-hub run-plan`.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: verify both config locations against first-party pages, then either write the enablement through the platform's own CLI when it is detected or seed the config key under the platform-defaults do-not-invent rule.

**Original source identity**: `v4.13.2#DF-4`; stable ID `DF-4-v4132` distinguishes this obligation from repeated IDs in other patch sections.

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

#### DF-1-v4133 (v4.13.3): Flip the skill-index pointer on by default, and decide todos-on-demand

**Plan reference**: Resolved decisions 1 and 4. **Reason**: the pointer ships opt-in. Flipping it needs organic-selection evidence that skills the model saw in the table are still chosen when it sees only a pointer; the todos-on-demand question needs the same instruction-size evidence. **Evidence**: [`rendered-context-baseline.md`](development/rendered-context-baseline.md) (the index is 81-84% of each rendered file; the pointer removes 99.5% of it). **Owner**: `v4.17.3-adoption-harness-economics-and-portable-engineering-system` (moved from `v4.16.0-instruction-necessity-review` on 2026-09-28: the organic-selection evidence comes from the v4.17.3 pairing evaluator, and the v4.16.0 plan never took the item on; see [`v4.17.3-comparison-harness-economics-delta.md`](../v4.17/comparisons/v4.17.3-comparison-harness-economics-delta.md) D4). **Suggested next step**: run the evaluator's required `NEXUS_HUB_SKILL_INDEX=full` against `pointer` variant pair, recording organic skill selection including guard skills, then decide the default.

**Original source identity**: `v4.13.3#DF-1`; stable ID `DF-1-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-2-v4133 (v4.13.3): Pilot variant mode for instruction-file comparisons

**Plan reference**: Resolved decision 6. **Reason**: `scripts/run_trigger_pilot.py` varies only SKILL.md description lines and runs with `--setting-sources project`, so it cannot compare an instruction file with the full index against one with the pointer. Spend cap for this plan: 0. **Owner**: v4.16.0. **Suggested next step**: add a variant mode that stages instruction files per arm.

**Original source identity**: `v4.13.3#DF-2`; stable ID `DF-2-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-3-v4133 (v4.13.3): Plan state in the session digest

**Plan reference**: Resolved decision 3. **Reason**: no plan-status contract exists that `/implement` writes, so a digest detector would report "none detected" almost always. **Owner**: the first plan that defines a plan-status contract. **Suggested next step**: once that contract exists, add one digest line read from it.

**Original source identity**: `v4.13.3#DF-3`; stable ID `DF-3-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-4-v4133 (v4.13.3): Static-measurement ownership split for v4.17.3

**Plan reference**: Phase 6.2 handoff. **Reason**: `scripts/measure_rendered_context.py` owns rendered instruction-file measurement; v4.17.3's static measurement must reuse its estimator and detector rather than add a second definition of an estimated token or a candidate span. **Owner**: v4.17.3. **Suggested next step**: import `estimate_tokens` and `legacy_instruction_block.detect` from their current owners.

**Original source identity**: `v4.13.3#DF-4`; stable ID `DF-4-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-5-v4133 (v4.13.3): Shared cleanup-aware merge requirement for v4.17.3

**Plan reference**: Phase 6.2 handoff. **Reason**: every marker-merged instruction write now goes through `instruction_merge.merge_instruction`, guarded by `test_no_integration_calls_the_primitive_directly`. Any v4.17.3 writer of a shared instruction file must route through the same owner so consent, backups, and byte preservation hold. **Owner**: v4.17.3. **Suggested next step**: cite this requirement in the v4.17.3 plan's writer tasks.

**Original source identity**: `v4.13.3#DF-5`; stable ID `DF-5-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-6-v4133 (v4.13.3): Pointer consumer installed before its shared-path provider across installer runner calls

**Source phase**: Phase 5. **Reason**: the installers run the Python runner once per platform, and the runner's pointer-mode second pass only sees integrations in the same call. A consumer installed before the platform that writes its path would get the full index until the next install (fail closed, never open). **Current state (2026-09-25)**: the only such dependency among VERIFIED paths is Copilot reading Codex's `~/.agents/skills`. Both installers run Codex before Copilot at both scopes, pinned by `test_installers_run_the_shared_path_provider_before_copilot`. A simulation of the installers' exact per-platform global order on a fresh home gave the same eligible set as a single combined run (Claude, Codex, OpenCode, Copilot, Qwen). The second pass now also runs for a single integration, so an integration that renders before copying its own skills is covered. **Residual**: a future VERIFIED shared path whose provider runs later would need a new order pin. **Owner**: v4.16.0 (with DF-1). **Suggested next step**: derive the order check from the facts when a second shared-path dependency appears.

**Original source identity**: `v4.13.3#DF-6`; stable ID `DF-6-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-7 (v4.13.3): Move the legacy-removal decision record to `implemented` - RESOLVED 2026-09-28

**Source phase**: Phase 4. **Reason**: `docs/decisions/implemented/tooling/2026-09-24-legacy-instruction-block-removal.md` describes shipped behavior once v4.13.3 is released. The record format requires a rewrite (Decision in present tense, Consequences) and a move, not a Status edit. **Owner**: `/update release` for v4.13.3. **Status**: resolved at the v4.13.3 release: the record moved to `docs/decisions/implemented/tooling/` with a Decision section and a Consequences section, and the capability-usage entry ships in the release notes.

#### DF-8 (v4.13.3): Per-agent `omitClaudeMd` for catalog agents

**Source**: [`v4.17.3-comparison-harness-economics-delta.md`](../v4.17/comparisons/v4.17.3-comparison-harness-economics-delta.md) D5, recorded 2026-09-28. **Reason**: Claude Code 2.1.271 added agent frontmatter `omitClaudeMd`, which lets a subagent run without user, project and local `CLAUDE.md` files (managed policy still loads). Each catalog agent now inherits the full rendered instruction files, measured at about 29k estimated tokens on the maintainer machine. **Owner**: `v4.16.2-adoption-agent-tooling-and-subagent-cost`. **Constraints**: decide agent by agent; exclude `project-standards-reviewer` and any agent that enforces repository conventions; confirm the Gemini and Codex agent loaders ignore an unknown frontmatter key, or emit the key only in the Claude copy. **Suggested next step**: accept a change only with a v4.17.3 pairing receipt showing lower cost at an unchanged pass rate.

#### WN-1-v4133 (v4.13.3): An uncooperative writer can race the final hash check

**Source phase**: Phase 4. **Reason**: cooperating installers serialize on a per-target lock, and the file is re-hashed immediately before the atomic replacement, but a program that ignores the lock can still write between that check and the rename; no portable primitive closes the window. **Mitigation**: a verified content-addressed backup of the pre-write bytes is always kept under `~/.nexus-hub/state/backups/`, and the report names it. **Owner**: installer maintainer. **Status**: accepted risk, documented in the decision record.

**Original source identity**: `v4.13.3#WN-1`; stable ID `WN-1-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-2 (v4.13.3): Copilot host-scope mismatch - RESOLVED 2026-09-28 UTC - RESOLVED

**Source phase**: Phase 5. **Original gap (2026-09-27)**: the [VS Code Agent Skills page](https://code.visualstudio.com/docs/agent-customization/agent-skills) documents `~/.claude/skills` for GitHub Copilot in VS Code, but the [Copilot CLI skill-location reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) omits that personal path. One `copilot` read-path fact governed pointer eligibility for both hosts, so it remained UNVERIFIED to prevent a CLI install from replacing its full index based only on VS Code evidence. **Owner**: Copilot integration maintainer. **Required resolution**: separate host-specific eligibility or obtain first-party CLI evidence before promoting the shared fact; preserve the full index for the unproved case.

**Local host-scope qualification, 2026-09-27**: The candidate recorded `~/.claude/skills` as VERIFIED for VS Code only and excluded host-only facts from the shared Copilot personal instruction's pointer eligibility. A redirected-home runner install with only that tree present retained the full index, while the existing common-path test still permitted a pointer. The [archived verification](../../../archives/v4/v4.13/development/copilot-host-scoped-skill-path-2026-09-27/verification.md) records the official-source boundary, red/green controls, 42 focused passes, and the contract check. WN-2 remained open pending protected integration and post-merge verification; Copilot CLI discovery of that path was not verified.

**Protected closure, 2026-09-28 UTC**: [PR #361](https://github.com/bendourthe/Nexus-Hub/pull/361) passed 24 hosted checks with one expected skip after correcting the historical v4.9 ledger hash exposed by its first full-profile run, merged as `6d9e4c39`, and [post-merge run 36361813686](https://github.com/bendourthe/Nexus-Hub/actions/runs/36361813686) passed smoke and provenance. The VS Code fact is host-scoped; shared and CLI pointer eligibility still excludes that path, so Copilot CLI discovery is not claimed. WN-2 is closed for the host-scope mismatch, not for a CLI discovery claim.

**Normalization, 2026-10-09 (v4.13.11 T006)**: Parsed RESOLVED marker records the already evidenced disposition retained above. No new runtime or historical capture is claimed.

#### MT-1-v4133 (v4.13.3): The full installers were not run end to end on a disposable machine

**Source phase**: Phases 4 and 5. **Reason**: the full PowerShell installer also installs VS Code extensions through the real `code` CLI and writes the real `%APPDATA%` settings, which a redirected HOME does not isolate, so the Phase 4 and 5 verification drove the installer's own engine (per-platform runner calls plus `legacy-report`) instead. The installers' flag parsing, forwarding, and report wiring are unit-tested, and CI runs both installers on their native hosts. **Owner**: release maintainer. **Suggested next step**: the last-phase human testing suggestions include a real install on a machine that carries a legacy block.

**Original source identity**: `v4.13.3#MT-1`; stable ID `MT-1-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-5-v4133 (v4.13.3): Read-path drift found by the release contract pass

**Source phase**: `/update release` platform-contract verification, 2026-09-28. **Reason**: the pass found no broken install path, but four documented changes the adapters do not yet model: Gemini CLI documents a root `GEMINI.md` for the workspace and no rules directory (the contract lists `<project>/.gemini/GEMINI.md` and `.gemini/rules/`); OpenClaw adds a named-profile workspace (`~/.openclaw-<profile>/workspace` under `OPENCLAW_PROFILE`) and a per-agent `agents.entries.*.workspace`, whose precedence against `agents.defaults.workspace` the docs do not fully state; and VS Code prompt files, Copilot's global slash surface, are deprecated for Agent Host sessions while the Local agent still loads them. Windsurf's preferred workspace hooks file is v4.13.2 DF-1. Sources are in `docs/policy/platform-read-contracts.json` `meta.verified_for_version_note`.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: change each adapter and its contract row in lockstep (Gemini CLI workspace file and rules; OpenClaw profile workspace once the precedence is confirmed), and migrate Copilot's global slash surface to skills before the Local agent is removed.

**Original source identity**: `v4.13.3#WN-5`; stable ID `WN-5-v4133` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-6-v4133 (v4.13.3): Behavioral-lever drift found by the release contract pass

**Source phase**: `/update release` platform-contract verification, 2026-09-28. **Reason**: advisory lever changes (logged in `docs/policy/platform-defaults-levers.md`): Claude Code ignores a user-scope `effortLevel` on Opus 5.5 and later, so that seed no longer reaches the default model (the seeded `env.CLAUDE_CODE_EFFORT_LEVEL` still does); Codex's documented `model_reasoning_effort` and `approval_policy` value lists changed, and the page no longer names those keys as user-only; and Antigravity's `agentMode` values now describe different behavior. Every seeded value remains valid.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: seed Claude's effort under `modelSettings` for the default model, refresh the Codex and Antigravity lever rows and `configs/platform-defaults.json`, then run `python scripts/sync_platform_defaults.py --check`.

**Original source identity**: `v4.13.3#WN-6`; stable ID `WN-6-v4133` distinguishes this obligation from repeated IDs in other patch sections.

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

#### WN-1-v4134 (v4.13.4): The header navigation overflows under the matrix's 200% CSS zoom at 1280x720

**Evidence**: `tests/guides/tools/browser_matrix.py --groups zoom` fails four cases (`zoom200-describe-review-*` and `zoom200-presentify-*` at 1280x720) on `horizontalOverflow` alone, with no page error, missing region, or overlap. The overflowing elements are `#navLinks` and `#themeToggle` (document `scrollWidth` 1324 against a 1280 viewport). The pre-rebuild guide on `develop` measures the same 1324 with 28 overflowing elements instead of 6, and a real 640x720 viewport, which is what 200% of 1280 represents, has no overflow on either revision. **Reason**: `document.documentElement.style.zoom` does not change the width that CSS media queries see, so the header never switches to its narrow layout under this emulation; native browser zoom does change that width but is not measured here. **Owner**: guide owner, together with the open [v4.4 MT-446-2](../../../archives/v4/v4.4/known-gaps.md) native-zoom item. **Suggested next step**: measure native 200% zoom on a real browser; if the header overflows there, collapse it by container width rather than viewport width, otherwise change the matrix's zoom cases to emulate native zoom.

**Original source identity**: `v4.13.4#WN-1`; stable ID `WN-1-v4134` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-2 (v4.13.4): An idle game labels its toggle "Pause game" - CLOSED

**Evidence**: before a game starts, its primary control reads "Pause game" while the HUD state reads `idle` (1440 px and 420 px section captures). `syncHud` derives the label only from the manual and pointer pause reasons, and the v4.4.x baseline uses the same expression. **Owner**: guide owner. **Suggested next step**: label the idle control from the lifecycle ("Start game" when idle, "Pause game" while running, "Resume game" when paused) and assert all three labels in `tests/guides/test_arcade_shooter_game.py`.

**Normalization, 2026-10-09 (v4.13.11 T006)**: Parsed CLOSED marker records the already evidenced disposition retained above. No new runtime or historical capture is claimed.

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

#### WN-1-v4136 (v4.13.6): Claude Code interactive `/goal` capture is observed only headless

**Evidence**: the Phase 1 probe (Claude Code 2.1.283, 2026-09-29) ran `claude -p "/goal test condition"`: the `UserPromptSubmit` payload's `prompt` field was exactly `/goal test condition` and the transcript shows `Goal set: test condition`. A person typing `/goal` in the interactive terminal was not exercised, so the `claude` row of `docs/policy/completion-levers.json` stays `goal_capture: unverified` with `probe_mode: headless`, and the validator accepts `verbatim` only from an interactive probe. **Owner**: catalog maintainer. **Suggested next step**: type `/goal test condition` in an interactive session of a scratch project whose `UserPromptSubmit` hook logs its payload, and set the row to `verbatim` with `probe_mode: interactive` if the logged prompt matches.

**Original source identity**: `v4.13.6#WN-1`; stable ID `WN-1-v4136` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-2-v4136 (v4.13.6): Most older known-gaps ledgers read cannot-verify for a minor-scope run

**Evidence**: a read-only `python scripts/minor_close.py status --minor v4.13` on 2026-09-29 reads `gaps.minor unmet`, with 369 open item headings; 30 of the 41 ledgers in scope read `cannot-verify` (663 rows that look like item ids but are not items, and 11 header `**Open items**` counts that disagree with the parsed count). The stricter Phase 4 parser is correct to refuse them: a looser reader would let open work pass as closed. **Owner**: catalog maintainer, before the first real minor-scope run (v4.17). **Suggested next step**: normalize those ledgers to the known-gaps-tracker format (one heading per item, a terminal RESOLVED, CLOSED, or MIGRATED marker, and a matching header count) in a docs-only change, then re-run the status command until every ledger parses. The 2026-09-30 re-run (Phase 8, after AR-01, AR-02, and v4.13.5 WN-1 were resolved) reads 368 open headings and 674 unparsed rows; it also shows that this file restarts ids in each patch section, so `v4.13#WN-1` names four items. `minor_close.py migrate` refuses such an id with `gap-ambiguous`, which is safe, but the normalization must also make ids unique per minor file.

**Original source identity**: `v4.13.6#WN-2`; stable ID `WN-2-v4136` distinguishes this obligation from repeated IDs in other patch sections.

#### MT-1-v4136 (v4.13.6): The guide's scope-matching test checks no scope

**Evidence**: `test_rendered_scopes_match_their_command_files` in `tests/guides/test_nexus_hub_guide.py` searches for a bare `<code>` tag, but every Cheatsheets scope is rendered as `<code data-ty="code">`, so the test passes without comparing any scope with its command file. Found while adding `tests/guides/test_cheatsheet_command_sync.py`, which covers the `/implement` card only. **Owner**: catalog maintainer. **Suggested next step**: match the attribute form and extend the comparison to every command card, then confirm it fails on a deliberately stale card.

**Original source identity**: `v4.13.6#MT-1`; stable ID `MT-1-v4136` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-4-v4136 (v4.13.6): The whole website guide reports 100 detector findings on views this plan did not touch

**Evidence**: `detect_visual_defects.py guides/website/nexus-hub-guide.html` (default viewports 420, 900, 1440; light and dark) reports the capped 100 findings, 10 `parent-padding-escape` (the first is the landing view's `h1 > b`) and 90 `svg-viewbox-overflow`, with the same distribution at base `7067df15`, so none comes from this plan. The Cheatsheets view this plan edited passes with 0 findings in both themes at base and head. **Owner**: guide maintainer. **Suggested next step**: run the detector per view with `--fragment`, fix or allowlist each finding with a recorded reason, and add the whole-page run to the guide render gate.

**Original source identity**: `v4.13.6#WN-4`; stable ID `WN-4-v4136` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-5 (v4.13.6): v4.13.2 WN-9 is only partly closed - CLOSED

**Evidence**: Definition of Done 3 says it closes v4.13.2 WN-9 for every record type. Every bypass it names (a lone "ok", a quoted code, a pasted issue body, a runner-launched prompt) is refused by `tests/validators/test_approval_binding.py`, but the agent can still originate its own capture (pipe a payload into `completion_gate.py capture`, append to the capture file, or pre-seed a nested session), which is why that entry reads PARTIALLY RESOLVED. This pointer keeps the remainder visible in this plan's section; the item itself stays tracked under v4.13.2 WN-9. **Owner**: catalog maintainer. **Suggested next step**: bind a capture to a platform-authenticated user-turn signal where one exists, and record `cannot-verify` otherwise.

**Tracking alias closure, 2026-10-09 (v4.13.11 T007)**: This source repeats the obligation tracked by `v4.13.2#WN-9`. Its stable normalized owner is `v4.13.2#WN-9-v4132`. The original body is retained; the canonical owner remains open, and this marker does not claim implementation.

#### DF-1-v4136 (v4.13.6): Copilot CLI sets no native goal headlessly

**Evidence**: `scripts/run_plan.py` keeps `copilot/cli` in `INTERACTIVE_GOAL_ROWS` because its headless path is `copilot --autopilot -p` with a bypass flag, not `/goal`; the plan's cut-line allowed this slip (sub-task 6.3, T051). Claude, Qwen, and Kimi launch the goal headlessly. **Owner**: catalog maintainer. **Target version**: v4.17, with v4.13.2 DF-6. **Suggested next step**: re-check the Copilot CLI documentation for a headless goal entry point and add the row when one is documented.

**Original source identity**: `v4.13.6#DF-1`; stable ID `DF-1-v4136` distinguishes this obligation from repeated IDs in other patch sections.

#### QG-1-v4136 (v4.13.6): The non-engineer read-back of the approval page is pending

**Evidence**: Definition of Done 6 requires one non-engineer read-back recorded in the final phase. **Read-back result, 2026-09-30**: the user read the ten-section page rendered from the two-plan fixture (`approval_page.py` at `219513b3`) and found it too wordy, noting that many users will not read it. That result led to the redesign: a results table (released, fixed, archived, cleaned up, and permission prompts when they are turned off), two bold limits, and the paste line, all within 80 words, with the technical sections moved under "Details (optional)". The redesigned page has not been read back yet, so this item stays open. The automated half (jargon list, sentence ceiling, risk order, paste line without paths) passes in `tests/validators/test_approval_page.py`. **Owner**: the user, via the orchestrator. **Suggested next step**: have a non-engineer read the redesigned page (the two-plan fixture render, saved beside the first read-back as `readback-page-v2.md`), then record pass or fail with the page version in `development/v4.13.6-last-phase-evidence.md`.

**Original source identity**: `v4.13.6#QG-1`; stable ID `QG-1-v4136` distinguishes this obligation from repeated IDs in other patch sections.

#### QG-2-v4136 (v4.13.6): The edited guide card had no full accessibility or design audit

**Evidence**: the Tier 3 pass covered the edited Cheatsheets `/implement` card with the visual-defect detector (0 findings), clipped captures at 1440 and 420 px (no horizontal overflow, inspected), and a control probe (both copy buttons named "Copy to clipboard" and focusable; scope text 16 px). The full `[[accessibility-engineering]]` and `[[hallmark-design]]` audits were not run in this phase. **Owner**: guide maintainer. **Suggested next step**: run both audits on the Cheatsheets view before the next guide release and record the result here.

**Original source identity**: `v4.13.6#QG-2`; stable ID `QG-2-v4136` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-6-v4136 (v4.13.6): Unusual branch, surface, and vendor names reach the approval page as written

**Evidence**: Tier 3 adversarial finding ADV-5 (P3). `render_page` with source branch `feat/refs/heads/check_plan_completion.py`, class `ask-first:hmac-nonce-schema`, and spend vendor `predicate` put every banned-list term and a script name above the paste line; the paste line itself stayed clean, and the allowed character sets rule out spaces, so no sentence can be injected. The plain-language guarantee is enforced by tests on fixture inputs, not at render time. **Owner**: catalog maintainer. **Suggested next step**: run the banned-term and path or script checks inside `render_page` (raising `PageError`), or move these values into the quoted details block.

**Original source identity**: `v4.13.6#WN-6`; stable ID `WN-6-v4136` distinguishes this obligation from repeated IDs in other patch sections.

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

Gaps from the Copilot usage monitor and usage-limit handoff plan ([`v4.13.7-copilot-usage-monitor-and-usage-limit-handoff`](plans/v4.13.7-copilot-usage-monitor-and-usage-limit-handoff.md)). Recorded by sub-task 4.1; Phase 4 ran before Phases 1-3, which wait on the maintainer's live Copilot readings. Reconciled by Phase 9 on 2026-10-02 (final-phase evidence: [`v4.13.7-last-phase-evidence.md`](development/v4.13.7-last-phase-evidence.md)).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 7 |
| Warnings (WN) | 0 | 4 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

### Resolved Items

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-1 | `skill-activation-suggest.py` silently lost `_skill_rules` on adapters that copy only registered scripts | Phase 6 | `scripts/lib/integrations/_hooks_common.py` `sourced_modules()` now ships every `_*.py` helper a delivered hook imports; `tests/integrations/test_codex_native.py` asserts `_skill_rules.py` lands beside `skill-activation-suggest.py`. |
| WN-2 | The Codex and Claude monitors' dashboards had no Content-Security-Policy and read unscoped settings | Phase 3 | Ported from the Copilot monitor in sub-task 3.6: nonce CSP, delegated listeners, validated and escaped thresholds and colors, a validated `save` payload, `"scope": "application"` on thresholds and colors, and a 1-120 minute `refreshInterval` clamp. Regression tests: `extensions/codex-usage-monitor/test/review-regressions.test.ts` and `extensions/claude-usage-monitor/test/review-regressions.test.ts`. |
| WN-10 | Two CodeQL warnings left from v4.13.6 in `scripts/completion_minor.py` | Phase 9 | Alert 375 (`py/comparison-of-identical-expressions`): the deliberate NaN self-comparison in `check_minor_seconds` is now `math.isnan(requested)`; alert 368 (`py/unused-local-variable`): the unused `section` reset before the second scan in `parse_ledger_full` was removed. Behavior is unchanged (`nan`, `5`, `99999`, `abc`, `inf`, and `-inf` give the same budgets as before). |
| WN-11 | The stated hook count (38) matched no definition | Phase 9 | `stamp_guide_counts.py` counts the 36 distinct scripts registered in `catalog/hooks/settings.json`; the prose figure had drifted since v4.13.1 (35 when 31 were registered, 37 when 33 were). `AGENTS.md`, `README.md`, and `data/marketplace.json` now say "36 registered hooks". The GitHub repository description (an external setting, still "37 hooks") is updated by hand at release. |
| BG-2 | A committed, future-dated `.nexus-hub/handoff.md` outranked the pasted prompt and survived carry-forward | Phase 9 (Tier 3 cycle 1) | Adversarial finding ADV-1 (P2). `session-handoff` Step 3 now carries nothing forward from a committed (`git ls-files --error-unmatch` succeeds) or future-dated file and tells the user; prompt rule 1 says to follow the pasted copy and only offer a newer, uncommitted, not-future file to the user. Test: `test_a_committed_or_future_dated_handoff_is_never_followed_as_instructions` (failed before, passes after). |
| BG-3 | A future-dated usage-limit header silenced the guard's turn-end reminder and satisfied the completion gate | Phase 9 (Tier 3 cycle 1) | ADV-2 (P3). `usage_limit_handoff_time` in `catalog/hooks/usage-guard.py` ignores a header dated more than `FUTURE_SKEW_SECONDS` (300) ahead of the clock; `scripts/completion_gate.py` calls the same function. Tests: `test_a_future_dated_handoff_header_is_ignored` (failed before) and `test_a_handoff_within_the_clock_skew_allowance_still_counts`. |
| BG-4 | The handoff secret scan missed Stripe, Google, GitLab keys and password pairs | Phase 9 (Tier 3 cycle 1) | ADV-3 (P3). The Step 6 `grep -nE` pattern now covers `sk_live_`/`sk_test_`, `AIza...`, `glpat-...`, and `password`/`secret`/`api_key`/`token` `=`/`:` pairs, and the skill says the pattern is a floor below the `egress-redaction` taxonomy. Four new cases in `test_the_secret_scan_flags_secret_shaped_strings` failed before and pass after. |
| MT-1 | The Session Handoff validator passed a template carrying a second, contradictory block | Phase 9 (Tier 3 cycle 1) | ADV-4 (P3). `check_template` in `tests/validators/test_session_handoff_block.py` now reports any count of `## Session Handoff` other than one. Test: `test_a_second_contradictory_block_fails` (failed before). |
| BG-5 | A malformed stricter reset count fell back to the looser one in the Codex monitor | Phase 9 (Tier 3 cycle 1) | ADV3-1 (P3). `readResets` reads `available_count` only when `applicable_available_count` is absent, so a present but malformed stricter count hides the row instead of enabling the button. Test: "never falls back to the looser count ..." in `extensions/codex-usage-monitor/test/resets.test.ts` (failed before). |
| BG-6 | The raw-response redactor missed camelCase and run-together identity keys | Phase 9 (Tier 3 cycle 1) | ADV3-2 (P3). Both monitors' `rawUsageResponse.ts` split keys into words before matching and also match secret words inside run-together keys (`sessiontoken`); `userId`, `displayName`, `password`, `phone`, and similar values are now replaced. Output on every captured vendor fixture is unchanged. The README and SECURITY.md claims now state what is kept and what is replaced. Test: "redacts camelCase, run-together, and secret-word keys ..." in both monitors (failed before). |
| BG-7 | A focused install could ship `/handoff` without `session-handoff`, and the `workflow` module lacked the skill | Phase 9 (Tier 3 cycle 2) | Found by the deep pass's real-installer exercise: `installer.sh --workspace ... --modules ai-engineering` installed `.claude/commands/handoff.md` but no `session-handoff` skill, because Phase 4 registered the skill only in the `core-developer` bundle and `/handoff`, a thin dispatcher over one skill, was missing from `surface_requirements.commands` in `data/bundles.json`. The skill is now in the `workflow` module (its category, like `session-history`) and `handoff` requires `session-handoff`. Re-run: `--modules workflow` installs both, `--modules testing` installs neither, and `usage-guard.py` lands in both. Test: `test_handoff_ships_only_with_its_skill` in `tests/integrations/test_selective_install.py` (failed before). |
| BG-8 | A full-profile test ran both real installers against the real home | Phase 9 (full-suite stabilization) | Pre-existing. A snapshot of the real `~/.nexus-hub` taken before the full profile showed 52 scripts, `permissions-manifest.json`, and `VERSION` rewritten at 14:51 UTC, byte-identical to this worktree, while `repo-tests-skills` ran. `tests/skills/test_presentify_dual_view_distribution.py` passed no environment to its installer subprocesses; it now redirects `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `NEXUS_HUB_HOME`, and `GIT_CONFIG_GLOBAL` to `tmp_path`. Rerun: `2 passed`, real-home snapshot unchanged. The real home still holds the worktree copies until the next real install; see v4.13.1 BG-2, which stays open. The real VS Code and Cursor extension lists were identical before and after the profile. |

## v4.13.8

Gaps from the Sonnet 5.5 profile and first-principles plan ([`v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test`](plans/v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md)); the admission record is [`v4.13.8-admission.md`](development/v4.13.8-admission.md).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |

### Open Items

### Resolved Items

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| QG-9 | The owner-account Connect run is not recorded yet | v4.13.8, 2026-10-03 | The maintainer ran Connect as the SupiraMedical owner: the token-free `read:org` route did not connect, and the guided token did. Per-endpoint status codes were not captured. Reading: [`v4.13.8-copilot-connect-verification.md`](development/v4.13.8-copilot-connect-verification.md) |

## v4.13.9

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 1 |
| Bugs / regressions (BG) | 3 | 0 |
| Warnings (WN) | 19 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 2 | 0 |

### Open Items

#### WN-1-v4139 (v4.13.9): The GPT-6.1 Sol announcement could not be read

- **Source phase**: Phase 1. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T403.
- **Reason**: `openai.com/index/introducing-gpt-6-1-sol/` returned HTTP 403 on 2026-09-30. The announcement's "a fifth of the price" and "Near-Astra" headline is therefore verified only as far as the wording of OpenAI's model catalog. Nothing in the Sol profile may rest on the announcement.
- **Suggested next step**: re-fetch the announcement from a session that is not blocked. If it is readable, check the profile claims against it and add any primary-source fact through the writer's `write --input` path.

**Original source identity**: `v4.13.9#WN-1`; stable ID `WN-1-v4139` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-2-v4139 (v4.13.9): Cursor's primary documentation for `/visualize` was not read

- **Source phase**: Phase 1. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T402 and T403.
- **Reason**: the comparison relied on a newsletter summary of Cursor's `/visualize`. On 2026-10-01 a `cursor.com` search and a fetch of `https://cursor.com/docs/agent/chat/commands` stated nothing about a built-in `/visualize`, about how a same-named user command takes precedence, or about where commands are stored. Only the discovery locations (`.cursor/commands/`, `~/.cursor/commands/`) were found.
- **Suggested next step**: when Cursor documents `/visualize` or command-name precedence, re-run T402's decision against that page. Option (b), mirroring everywhere, stands until then.

**Original source identity**: `v4.13.9#WN-2`; stable ID `WN-2-v4139` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-1-v4139 (v4.13.9): The Codex `doctor` advisory was cut from this plan

- **Source phase**: Phase 1. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T403 and the Non-Goals.
- **Reason**: interview Q2 chose a runbook only. The `doctor` advisory, its `DIAGNOSTIC_ADVISORY` constant, a host-hazard module, and a host-hazard data file are out of scope.
- **Suggested next step**: reopen only when two primary OpenAI sources confirm the fix version and a second host hazard appears, as the Non-Goals state.

**Original source identity**: `v4.13.9#DF-1`; stable ID `DF-1-v4139` distinguishes this obligation from repeated IDs in other patch sections.

#### DF-9 (v4.13.9): Claude Haiku 5.5 is announced but has no profile or map cell

- **Source phase**: Phase 1. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T304.
- **Reason**: Anthropic announced Claude Haiku 5.5 "in the coming weeks" and it is not yet in the models overview, so no prompting profile or model-map cell can be verified against a primary source.
- **Suggested next step**: when the models overview lists it, run `/tune-prompting <haiku-5-5-id> --profiles-only` and refresh the `fast` tier cell of the model map.

- **Carried from**: v4.13.8#DF-1 on 2026-10-02

#### DF-11 (v4.13.9): Nine newly rostered Claude models have no prompting profile

- **Source phase**: Phase 2. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T306.
- **Reason**: the live Claude roster read from the Models API on 2026-09-30 added nine ids that this plan does not research, by design (it calibrates on `claude-sonnet-5-5` only): `claude-fable-5`, `claude-haiku-4-5-20251001`, `claude-opus-4-5-20251101`, `claude-opus-4-6`, `claude-opus-4-7`, `claude-opus-4-8`, `claude-opus-5-5`, `claude-sonnet-4-5-20250929`, and `claude-sonnet-4-6`. Each is now a rostered UNVERIFIED model. The live id `claude-haiku-4-5-20251001` sits beside the existing `claude-haiku-4-5` profile, which uses the alias.
- **Suggested next step**: `claude-opus-5-5` first, through `v4.17.6`, which already plans that profile; then `/tune-prompting <id> --profiles-only` per remaining current model. Decide whether the dated Haiku id and the alias should share one profile before profiling either again.

- **Carried from**: v4.13.8#DF-3 on 2026-10-02

#### WN-21 (v4.13.9): A reasoning example asks the model to write its analysis into the reply

- **Source phase**: Phase 2. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T308 (sweep finding SW-1).
- **Reason**: `catalog/skills/ai-development/prompt-engineering/references/step-2-apply-reasoning-techniques.md` lines 92 to 101 tell the model to "Think through this step-by-step" and to structure its response as `<thinking>[Your step-by-step analysis]</thinking>` followed by an answer. On Claude Sonnet 5.5, instructions that ask for reasoning in the response invite `reasoning_extraction` declines. The classifier routed the finding `profile-only`, so no shared body was edited.
- **Suggested next step**: owner `prompt-engineering`. Revise the example to rely on the model's own thinking (adaptive thinking, with summarized thinking blocks when the reasoning must be read), or label it as written for older models. Route the change through `apply_prompting_edits.py` as a model-agnostic candidate only if it names no model.

- **Carried from**: v4.13.8#WN-1 on 2026-10-02

#### WN-22 (v4.13.9): A self-consistency example asks for written-out step-by-step reasoning

- **Source phase**: Phase 2. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T308 (sweep finding SW-2).
- **Reason**: the same file, line 127, prompts "Think step-by-step, then provide your final answer on the last line". The traced Sonnet 5.5 item and the classifier route are the same as WN-1.
- **Suggested next step**: owner `prompt-engineering`; fix together with WN-1 in one change.

- **Carried from**: v4.13.8#WN-2 on 2026-10-02

#### WN-23 (v4.13.9): The primary roster mixes vendors, so its freshness check always reads DRIFTED

- **Source phase**: Phase 2. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T306 and T309.
- **Reason**: the `claude-code` roster in `profiles-index.json` was recorded on 2026-09-08 from `config` as a multi-vendor union (Claude, Cursor, Gemini, and GPT-5.6 ids). The 2026-09-30 write refreshed it from the live Models API, and by design the writer unions the live ids with every already-profiled model, so no profile was orphaned. The result is 26 ids labelled `roster_source: api`, of which 16 did not come from the API. `check_model_prompting_freshness.py --advisory` against the 13 live Claude ids therefore reports DRIFTED, listing the non-Claude ids and the `claude-haiku-4-5` alias as "no longer live". The check is advisory and blocks nothing.
- **Suggested next step**: move the Cursor, Gemini, and GPT-5.6 profiles onto their own `meta.platforms` entries (schema 1.1.0), as was done for `codex`, so the `claude-code` roster holds only Claude ids and its freshness check can read IN SYNC. Decide the `claude-haiku-4-5` alias at the same time (see DF-3).

- **Carried from**: v4.13.8#WN-3 on 2026-10-02

#### DF-12 (v4.13.9): The first-principles pilot stopped at the smoke run because effort could not be confirmed

- **Source phase**: Phase 5. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T321 to T324; record [`v4.13.8-first-principles-pilot.md`](development/v4.13.8-first-principles-pilot.md).
- **Reason**: the pre-registered rule in `## T319` stops the pilot when the run metadata cannot confirm `--effort high`. On the one smoke run (2026-09-30, baseline, prompt 1, passed, USD 0.0396), Claude Code 2.1.283 reported `claude-sonnet-5-5` as an unrecognized model, recorded `costBasis: "unknown"` and a fallback `maxOutputTokens` of 32000, and exposed no effort field and 0 thinking tokens. The other 14 cells were not run, and the first-principles question is untested: this is not evidence for or against the instruction.
- **Suggested next step**: once a Claude Code release recognizes `claude-sonnet-5-5` and its run metadata can show the effort in effect, re-run the identical approved matrix (same arms, prompts, model, effort, 15 runs, USD 20 cap) with `python wrapper.py run` after deleting the stale smoke result, and decide go or not shown at this power from the rule recorded in `## T319`. Any change to the matrix needs a new approval.

- **Carried from**: v4.13.8#DF-4 on 2026-10-02

#### WN-24 (v4.13.9): The skill-eval-loop Claude adapter command no longer matches the installed CLI - CLOSED

- **Source phase**: Phase 5. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T319 and T321.
- **Reason**: `catalog/skills/workflow/skill-eval-loop/references/cli-adapter.md` documents the Claude runner as `claude -p "<prompt>" --setting-sources "" --model <model> --skill <path/to/SKILL.md>` (verified 2026-09-21), and `scripts/optimize_skill_description.py` builds that command. Claude Code 2.1.283's `--help` (checked 2026-09-30) documents no `--skill` option. The pilot used `--append-system-prompt-file` instead, without changing the shared adapter. The same CLI also reports `claude-sonnet-5-5` as an unrecognized model (see DF-4).
- **Suggested next step**: owner `skill-eval-loop`. Re-verify the Claude runner against the current official Claude Code CLI reference. If `--skill` is gone, choose and document the replacement (for example `--bare` with `--append-system-prompt-file`, or `--add-dir` with skill resolution), update the adapter and the optimizer's command builder together, and keep `TestEvalLoopCLIAdapter` parity green.

- **Carried from**: v4.13.8#WN-4 on 2026-10-02

**Tracking alias closure, 2026-10-09 (v4.13.11 T007)**: This source repeats the obligation tracked by `v4.13.0#AR-04`. Its stable normalized owner is `v4.13.0#AR-04`. The original body is retained; the canonical owner remains open, and this marker does not claim implementation.

#### WN-25 (v4.13.9): The profiling-harness test fails intermittently under host load

- **Source phase**: Phase 6. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T334.
- **Reason**: during the v4.13.8 full local gate on 2026-10-01, `tests/skills/test_profiling_harness.py::test_profile_run_emits_profile` failed once (`assert any("work" in fn["name"] ...)` was False: the profiled `work()` function was missing from the top 10 entries) while several suites shared the host. It passed 3 of 3 runs alone on the branch and 2 of 2 on `develop`. The test was last changed in v3.14.0, and this plan touches neither it nor the harness.
- **Suggested next step**: owner `code-optimizer`. Make the assertion independent of timing rank (for example look up `work` in the full function list, or raise `--top`), so host load cannot evict it from the reported entries.

- **Carried from**: v4.13.8#WN-5 on 2026-10-02

#### WN-26 (v4.13.9): Open Dependabot branches make the all-refs attribution check fail

- **Source phase**: Phase 6. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T330 and T334.
- **Reason**: `scripts/check_commit_attribution.py --all-refs` (fast and full profiles, `hygiene` group) scans every commit reachable from every ref against a closed author allowlist. On 2026-10-01 Dependabot opened PRs #402 to #404, and their branches carry `dependabot[bot]` commits (`3a940eede996`, `904486f2affb`, `16c5fc389a19`). Once those branches are fetched, the check reports `3 findings` and exits 1. None of the three commits is in this branch's history: `git merge-base --is-ancestor` is false for each, and every commit in `origin/develop..HEAD` is authored by the owner identity. The `validate` job checks out with `fetch-depth: 0`, so the hosted check sees the same refs: on PR #402 (run 36897160501) `validate` failed with `check_commit_attribution` reporting `3 findings` on Dependabot commits, which turned the required `ci-required` red. Every pull request is affected while those branches exist.
- **Mitigation applied 2026-10-01**: with the maintainer's approval, PRs #402 to #404 were closed and their branches deleted. After `git fetch --prune`, the check reads `2282 commits scanned; 0 findings` and the fast profile passes 17 of 17. The item stays open because the next scheduled Dependabot run will reintroduce such branches.
- **Suggested next step**: owner, the catalog maintainer, as a CI policy decision. Either close or merge the Dependabot PRs under the owner identity, or scope the all-refs scan to the branch under test plus the protected branches. Changing the check or the workflow is a CI security change that needs explicit approval.

- **Carried from**: v4.13.8#WN-6 on 2026-10-02

**Tracking alias retained**: `v4.13.9#WN-27`; the following complete historical source has the same current obligation and is not a separate future task.

##### Tracking source: v4.13.9#WN-27 (v4.13.9): The all-refs attribution scan fails on fetched Dependabot branches

**Evidence**: `python scripts/check_commit_attribution.py --all-refs`, run by the fast profile, uses `git log --all` and allows only approved identities, so the three `origin/dependabot/*` branches fetched into this repository on 2026-10-01 produce three `dependabot[bot]` author findings and fail the step. Commits still succeed, because the commit hook runs only the message and pending-identity checks. Merging a Dependabot pull request would put bot-authored commits into history and fail the scan permanently. **Owner**: catalog maintainer (attribution policy decision). **Suggested next step**: scope the all-refs scan to local branches, `origin/main`, `origin/develop`, and the current pull request head, and decide separately whether `dependabot[bot]` is an allowed author.

- **Carried from**: v4.13.7#WN-3 on 2026-10-02

- **Carried from**: v4.13.8#WN-14 on 2026-10-02

#### BG-12 (v4.13.9): `/usage` dispatches to a `check-usage` skill that does not exist

**Evidence**: `catalog/commands/usage.md` delegates every invocation to `check-usage` ("(any invocation) -> check-usage"), and no `catalog/skills/*/check-usage/` directory exists on `feat/v4.13.7-copilot-usage-monitor-and-usage-limit-handoff` after the 2026-10-01 merge of `develop` at `81d7e544`. The command therefore has no procedure behind it on any platform. Pre-existing; out of scope for this plan (plan Overview, "Out of scope"). **Owner**: catalog maintainer. **Suggested next step**: back `/usage` with `catalog/hooks/_usage_probe.py` (built in Phase 6) in a later release, either as a restored `check-usage` skill or by pointing the dispatcher at a skill that calls the probe.

- **Carried from**: v4.13.7#BG-1 on 2026-10-02

- **Carried from**: v4.13.8#BG-11 on 2026-10-02

#### WN-27 (v4.13.9): The all-refs attribution scan fails on fetched Dependabot branches - CLOSED

**Evidence**: `python scripts/check_commit_attribution.py --all-refs`, run by the fast profile, uses `git log --all` and allows only approved identities, so the three `origin/dependabot/*` branches fetched into this repository on 2026-10-01 produce three `dependabot[bot]` author findings and fail the step. Commits still succeed, because the commit hook runs only the message and pending-identity checks. Merging a Dependabot pull request would put bot-authored commits into history and fail the scan permanently. **Owner**: catalog maintainer (attribution policy decision). **Suggested next step**: scope the all-refs scan to local branches, `origin/main`, `origin/develop`, and the current pull request head, and decide separately whether `dependabot[bot]` is an allowed author.

- **Carried from**: v4.13.7#WN-3 on 2026-10-02

- **Carried from**: v4.13.8#WN-14 on 2026-10-02

**Tracking alias closure, 2026-10-09 (v4.13.11 T007)**: This source repeats the obligation tracked by `v4.13.9#WN-26`. Its stable normalized owner is `v4.13.9#WN-26`. The original body is retained; the canonical owner remains open, and this marker does not claim implementation.

#### WN-28 (v4.13.9): Dependabot does not track the Copilot Usage Monitor's npm dependencies

**Evidence**: `.github/dependabot.yml` has npm entries for the Claude, Codex, and Cursor monitors only, so `extensions/copilot-usage-monitor/` (added in Phase 2, installed from Phase 3) receives no dependency or security update pull requests. Adding the entry is a CI-configuration change that was not in the Phase 3 approval, and `tests/workflows/test_cursor_usage_monitor_workflow.py::test_dependabot_tracks_the_new_extension` asserts exactly three npm monitor entries, so the test has to change with it. **Owner**: catalog maintainer (CI configuration). **Suggested next step**: with approval, add an npm entry for `/extensions/copilot-usage-monitor` that ignores `@types/vscode` like its siblings, and change that assertion to four.

- **Carried from**: v4.13.7#WN-4 on 2026-10-02

- **Carried from**: v4.13.8#WN-15 on 2026-10-02

#### WN-29 (v4.13.9): `codexUsage.authPath` can still be set by a workspace

**Evidence**: Phase 3 made the Codex monitor's thresholds and colors `"scope": "application"` (WN-2), but `codexUsage.authPath` in `extensions/codex-usage-monitor/package.json` declares no scope. A trusted workspace's `.vscode/settings.json` can therefore point the monitor at another file, whose token the monitor reads and sends to `chatgpt.com/backend-api/wham/usage`. The destination stays fixed, so the exposure is limited to that one vendor endpoint, but which local credential is read is still decided by the workspace. **Owner**: catalog maintainer. **Suggested next step**: set `"scope": "machine"` or `"application"` on `codexUsage.authPath`, add it to the scope assertion in `extensions/codex-usage-monitor/test/review-regressions.test.ts`, and note in the README that a workspace value is ignored.

- **Carried from**: v4.13.7#WN-5 on 2026-10-02

- **Carried from**: v4.13.8#WN-16 on 2026-10-02

#### WN-30 (v4.13.9): Definition of Done 1 says "VS Code and Cursor"; the installers install the Copilot monitor into VS Code only

**Evidence**: Definition of Done 1 reads "installed into VS Code and Cursor by both installers", while sub-task 3.1 asked for the VS Code CLI. Both installers install the Copilot monitor exactly like its Claude and Codex siblings: `build_and_install_one_extension ... "$vscode_cli" "$vscode_label"` in `scripts/installer.sh` and `-CodeCli $vscodeCli -CodeLabel $vscodeLabel` in `scripts/installer.ps1`, and the banner both print says "Claude/Codex/Copilot install into VS Code only". Neither sibling installs into Cursor, so per the Phase 9 instruction the behavior was not changed. The optional second-host parameter (`also_cli` / `-AlsoCodeCli`) that would do it exists in both installers but no call passes it; it is left from the withdrawn GitHub monitor (v3.16.4). The Phase 9 run of both installers' real extension step confirmed the routing: the `code` stub received the three VS Code monitors and the `cursor` stub only the Cursor monitor. **Owner**: catalog maintainer (installer change, ask first). **Suggested next step**: decide whether Copilot users in Cursor are a supported surface. If yes, pass `"$cursor_cli" "$cursor_label"` (and `-AlsoCodeCli $cursorCli -AlsoCodeLabel $cursorLabel`) as the second host in both installers, update the banner line and `catalog/hooks/tests/test_installer_smoke.py`, and refresh the two installer hashes in `docs/handbooks/_sources/distribution/evidence.json`; if no, amend the Definition of Done wording to "VS Code".

- **Carried from**: v4.13.7#WN-6 on 2026-10-02

- **Carried from**: v4.13.8#WN-17 on 2026-10-02

#### WN-31 (v4.13.9): Definition of Done 7 asks for a reset's expiry; Codex serves a count and no expiry

**Evidence**: the 2026-10-01 capture recorded in `v4.13.7-decisions.md` ("Usage-limit resets", item 1) shows `rate_limit_reset_credits` carrying only `available_count` and `applicable_available_count`, with no kind and no expiry, although the ChatGPT page shows "Full reset, expires Oct 29". The Codex monitor therefore shows "1 reset available" with no date; `extensions/codex-usage-monitor/README.md` says why. Definition of Done 7's fallback covers only the case where no reset field exists at all, so a count without an expiry is a partial result, not a pass. The Claude monitor's no-field branch is met (no reset row; its README explains). **Owner**: extensions owner. **Suggested next step**: when a reset is next available, run `Codex Usage: Save Raw Usage Response` and check for an expiry field; map it into the reset row if one appears, otherwise amend the Definition of Done to "shows it with its expiry when the vendor data carries one".

- **Carried from**: v4.13.7#WN-7 on 2026-10-02

- **Carried from**: v4.13.8#WN-18 on 2026-10-02

#### WN-32 (v4.13.9): The monitor workflows differ in packaging checks, and two do not trigger on their own file

**Evidence**: Phase 9's field-by-field comparison (comments stripped, names normalized) found `.github/workflows/copilot-usage-monitor.yml` identical to the Claude and Codex monitor workflows except that it also triggers on its own file and runs `npm run package`; the Cursor workflow additionally runs `npm run verify:package` and uploads the VSIX as an artifact with a retention period. So the Copilot workflow builds the package but never checks its contents in CI (the Phase 2 history records a manual check: 49 files, no test, fixture, source, or map file), and the Claude and Codex workflows do not run when their own workflow file changes. These are pipeline changes outside the approved Copilot workflow, so they were recorded, not applied. **Owner**: CI owner. **Suggested next step**: with approval, add a `verify:package` script and step to the Copilot monitor (mirroring the Cursor monitor's), and add each workflow's own path to the Claude and Codex workflow filters.

- **Carried from**: v4.13.7#WN-8 on 2026-10-02

- **Carried from**: v4.13.8#WN-19 on 2026-10-02

#### WN-33 (v4.13.9): Redirecting HOME does not isolate the usage probe's Cursor reader on Windows

**Evidence**: `cursor_state_path()` in `catalog/hooks/_usage_probe.py` finds Cursor's `state.vscdb` through `%APPDATA%`, which is correct for Cursor but means a probe run with only `HOME` and `USERPROFILE` redirected still reads the real Cursor token. During the Phase 9 adversarial review one such run read the maintainer's real token and made one POST to `api2.cursor.sh` (Cursor's own host; the allowlist held, the token was not printed, and the cache file the run wrote held no token and was deleted). The shipped hook behaves as designed; the gap is that nothing tells a tester how to isolate the probe. **Owner**: catalog maintainer. **Suggested next step**: state in `docs/guides/usage-limit-handoff.md` that an isolated probe run must also redirect `APPDATA` (or exclude Cursor through `NEXUS_USAGE_PROBE_PROVIDERS`), and consider an explicit offline switch for testing.

- **Carried from**: v4.13.7#WN-9 on 2026-10-02

- **Carried from**: v4.13.8#WN-20 on 2026-10-02

#### QG-7 (v4.13.9): The real-editor and live-limit checks are manual and pending

**Evidence**: every automated check ran against stubs, fixtures, and throwaway homes. Not yet observed on the maintainer's machine: installing the VSIX into the real VS Code (and, if WN-6 is resolved that way, Cursor); the pinned work account's personal view and the organization pool percentage against the organization's AI usage page; the state file `~/.nexus-hub/state/usage-probe/copilot.json` written by the running monitor; the Codex reset row while a reset is available; and a live 99% crossing (with `NEXUS_HANDOFF_THRESHOLD=1`) on Codex, Cursor, and Copilot followed by pasting the prompt into a different platform. Claude Code's crossing was observed in Phase 7. **Owner**: maintainer. **Suggested next step**: run the checks listed under "Human/manual testing suggestions" in the final-phase evidence and record each result here.

- **Carried from**: v4.13.7#QG-1 on 2026-10-02

- **Carried from**: v4.13.8#QG-5 on 2026-10-02

#### QG-8 (v4.13.9): The run record was never captured, so the checker cannot sign off the run - CLOSED

- **Source phase**: Phase 6 (release)
- **Plan reference**: [v4.13.8 plan](plans/v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md)
- **Reason**: The upfront approval round on 2026-10-01 was never recorded: pasting the approval and goal lines as one message was refused (`approval-not-captured`), the failure v4.13.7 fixed in #406. With no run record, `check_plan_completion.py check` reports `approval.remote` as `cannot-verify` and can never print `PLAN COMPLETE` for v4.13.8. A record created now would start at today's `HEAD`, so every finished task would read unmet. On 2026-10-02 the user chose to release v4.13.8 on the chat approval of 2026-10-01 and record this gap.
- **Suggested next step**: None for v4.13.8. If a lost approval round recurs, add a recovery path: `record render` and `record create` taking the plan's first commit as the run's start, shown on the page the user approves.

- **Carried from**: v4.13.8#QG-6 on 2026-10-02

**Normalization, 2026-10-09 (v4.13.11 T006)**: Parsed CLOSED marker records the already evidenced disposition retained above. No new runtime or historical capture is claimed.

#### WN-35 (v4.13.9): The governance test group outgrows its 2700 s local cap on Windows

- **Source phase**: Phase 7 (final-phase full suite, re-run over Phase 6)
- **Plan reference**: [v4.13.8 plan, sub-task 7.9 (T334)](plans/v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md)
- **Reason**: `repo-tests-governance` in `scripts/ci/profiles.py` has `timeout=2700`. In the full profile on 2026-10-02 it hit that cap; re-run alone on the same Windows 11 machine it passed (2874 passed, 22 skipped) in 3063.9 s, above the cap. The v4.13.4 evidence recorded 1785.1 s for the same group, so the group has grown or the machine has slowed. A local full run therefore reports a timeout that is not a test failure, and a reader cannot tell the two apart from the verdict line.
- **Suggested next step**: Profile the slowest governance tests (`pytest --durations=25` on that group), then either split the group the way `repo-tests-integrations-*` was split, or raise the cap with a recorded measurement. Keep the hosted job's timing as the reference.

- **Carried from**: v4.13.8#WN-34 on 2026-10-03
- **Re-measured 2026-10-04 (v4.13.9 T434)**: the final full profile hit the cap again at 96 percent; run alone without the cap the group took 3325.7 s (2873 passed, 22 skipped, 1 failed). The one failure was a real stale assertion that no earlier full run reached because the step timed out first, so a timed-out step can also hide a failure.

#### BG-13 (v4.13.9): `auto-devlog.sh` silently drops every entry after a heading reaches line 1

- **Source phase**: Phase 5. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T423.
- **Reason**: the size-bound test's liveness check found that once a `## [` entry heading reaches line 1 of `DEVLOG.md`, the computed insert line is 0, which `awk`'s `NR == 0` never matches, so every later entry is dropped while the hook still prints that the entry was prepended. The second entry also lands above the `# Dev Log` title. The `.ps1` sibling inserts correctly, so the pair disagrees. This plan changes no hook (T423 failure mode), so the defect is recorded, and the test holds it as a strict expected failure that turns red once it is fixed. Measurement: [`v4.13.9-hook-size-bound.md`](development/v4.13.9-hook-size-bound.md).
- **Suggested next step**: fix the insert-line computation in `catalog/hooks/auto-devlog.sh` so a line-1 heading inserts before it, add an exit-code and output parity case to the hook's tests, then remove its `KNOWN_BREACHES` entry in `catalog/hooks/tests/test_hook_size_bound.py`.

#### BG-14 (v4.13.9): `learning-capture.sh` silently drops an event over 128 KiB on Linux

- **Source phase**: Phase 6 (integration pull request #424, Linux `tests` job). **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T435.
- **Reason**: the hook passes the whole payload to Python in one environment variable (`NEXUS_LC_PAYLOAD`). Linux caps a single environment string at 128 KiB (`MAX_ARG_STRLEN`), so for a larger payload Python fails to start with "Argument list too long", the error is discarded by `2>/dev/null || true`, and no record is written while the hook exits 0. Reproduced in WSL Ubuntu on 2026-10-04. On Windows and macOS the same payload is written whole instead (the WN-36 breach). The size-bound test holds the `.sh` breach as expected only off Linux (`[not-linux]`).
- **Suggested next step**: pass the payload to Python on standard input instead of in the environment, truncate `hook_event_name` and `tool_name` with the WN-36 fix, then remove the `[not-linux]` gate and the breach entry.

#### WN-36 (v4.13.9): Five file-writing hooks copy a field without truncation

- **Source phase**: Phase 5. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T423.
- **Reason**: one oversized event (64 KiB fields) grows a file by 65 to 132 KB, measured 2026-10-03: `learning-capture` copies the event and tool names whole (131549 bytes .sh, 131543 .ps1), `provenance-ledger` copies the file path whole and rotates by lines rather than bytes (65699), `session-summary` copies the session duration whole into its log and digest (.ps1 always; .sh when `jq` is present), `auto-devlog.ps1` lists commit subjects whole, and `skill-tracker.py` stores the skill name whole. Ordinary events stay at 70 to 1100 bytes. The test records each as a known breach, so a fix shows up as a failing expected-failure. Measurement: [`v4.13.9-hook-size-bound.md`](development/v4.13.9-hook-size-bound.md).
- **Suggested next step**: truncate each copied field the way `learning-capture` already truncates its prompt sample, bound the provenance ledger by bytes as well as lines, and remove the matching `KNOWN_BREACHES` entries.

#### WN-37 (v4.13.9): Multi-byte text grows two to six times in hook output on Windows

- **Source phase**: Phase 5. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T422.
- **Reason**: the multi-byte payload measured larger on Windows than its UTF-8 length (for example `session-summary.ps1` 3568 bytes and `auto-devlog.ps1` 4574 bytes for one event), consistent with input decoded through a legacy code page: Windows PowerShell 5.1 standard input and git output, and Python standard input read as cp1252. The size test records this and does not assert it. Measurement: [`v4.13.9-hook-size-bound.md`](development/v4.13.9-hook-size-bound.md).
- **Suggested next step**: read hook standard input as UTF-8 explicitly in the `.ps1` siblings and the Python hooks, then re-measure the multi-byte column.

#### WN-38 (v4.13.9): The hook test step outgrows its 1800 s local cap on Windows

- **Source phase**: Phase 6. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T434.
- **Reason**: `hook-tests` in `scripts/ci/profiles.py` has `timeout=1800`. In the final full profile on 2026-10-04 it hit that cap at 91 percent with no failure; run alone without the cap on the same Windows 11 machine it passed (2057 passed, 49 skipped, 8 xfailed) in 2096.9 s. Phase 5's `test_hook_size_bound.py` added about 3.5 minutes, and an earlier v4.13 run had already measured 1701.8 s, so the step was near its cap before this plan. As with WN-35, a local full run reports a timeout that is not a test failure.
- **Suggested next step**: run `pytest --durations=25` on `catalog/hooks/tests`, then split the step (for example, the size-bound test into its own step) or raise the cap with a recorded measurement. Keep the hosted job's timing as the reference.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-3 | The Codex fix version is not verified against OpenAI's primary sources | v4.13.9, 2026-10-03 | Closed by T424: the `rust-v0.142.0` release notes (2026-06-22) list the persistent-log reduction citing #29432 and #29457, and #29432's merge commit lies between the `rust-v0.141.0` and `rust-v0.142.0` tags. Runbook: [`docs/guides/host-agent-disk-writes.md`](../../../guides/host-agent-disk-writes.md) |
| DF-10 | The bundled model-map snapshot lists superseded models | v4.13.9, 2026-10-01 | Carried from v4.13.8 DF-2. Fixed by v4.13.9 T407: `last-known-model-map.json` reads `verified_as_of` 2026-10-01, `standard`/Anthropic `claude-sonnet-5-5`, and `strong`/OpenAI `gpt-6.1-sol`; `model-map.py validate` reports valid. |

## v4.13.10

Gaps from the Training page rebuild ([`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md)). The maintainer's Training acceptance was recorded on 2026-10-08 and PRs #435/#436 merged green into develop on 2026-10-09. The v4.13.11 sweep owns subsequent gap reconciliation and minor close. The maintainer retains the in-progress develop-to-main PR #438 and v4.13.10 tag.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 2 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 7 | 5 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 1 |

### Open Items

#### WN-1-v41310 (v4.13.10): The missing-file notice is verified in Chromium only

- **Source phase**: Phase 7. **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), T027.
- **Reason**: the guide detects a missing `training.html` under `file://` with a stylesheet probe (`media="not all"`, its `onload` and `onerror`). Tests run headless Chromium; Firefox and Safari treat `file://` loads differently and were not exercised.
- **Owner**: guide owner. **Suggested next step**: open the guide from a folder without `training.html` in Firefox and Safari and click the Training tab; if no notice appears, fall back to showing the notice on any `file://` load that does not navigate within a second.

**Original source identity**: `v4.13.10#WN-1`; stable ID `WN-1-v41310` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-5-v41310 (v4.13.10): A game started through the API on a hidden stage runs unseen

- **Source phase**: Phase 8 deep pass (adversarial pass). **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), Phase 3 engine.
- **Reason**: `SkySentinel.get('fixed').start()` called while `#intro` is showing starts a game on a hidden stage. Its IntersectionObserver never fires for a host that was never visible, and Escape is ignored because the game does not own the keyboard, so it runs until the reader opens its stage. No button or key reaches this path: start controls are hidden on other stages and navigation pauses games.
- **Owner**: guide owner. **Suggested next step**: in `start()` and `resume()`, pause with reason `stage` when the host is not rendered (`host.offsetParent === null`), and add an engine test that starts a game on a hidden stage.

**Original source identity**: `v4.13.10#WN-5`; stable ID `WN-5-v41310` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-6-v41310 (v4.13.10): Three minor accessibility findings in shared markup

- **Source phase**: Phase 8 deep pass (accessibility audit). **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), Phase 8.6.
- **Reason**: the audit passed both pages with minor findings. Three sit in markup both pages share or the guide already had before this plan, so they are recorded rather than changed here: the theme toggle carries `aria-pressed` with an action label ("Switch to light theme, pressed"); the guide's active nav link has no `aria-current="page"` (Training's does); there is no skip link, so reaching the provider switch on a session stage takes 19 Tab presses (landmarks are present).
- **Owner**: guide owner. **Suggested next step**: drop `aria-pressed` from `#themeToggle` in `shared/header.html`, add `aria-current="page"` in the guide router, and add a "Skip to content" link to the shared header.

**Original source identity**: `v4.13.10#WN-6`; stable ID `WN-6-v41310` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-8-v41310 (v4.13.10): The Foundations opening figure is taller than a phone screen

- **Source phase**: rework goal review (after R5). **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), T046.
- **Reason**: at 390 px the narrow drawing of the layer stack is 898 px tall (923 px after revision 2 added captions to the Tokens and Context window cards), so the reader scrolls through the figure before the page content starts. It is legible and does not overflow.
- **Owner**: guide owner. **Suggested next step**: in the narrow drawing, show the four inner parts as a two-by-two grid and shorten the loop caption, aiming at no more than 600 px.

**Original source identity**: `v4.13.10#WN-8`; stable ID `WN-8-v41310` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-9-v41310 (v4.13.10): The Nexus AI Studio trailer shows no screens of the app

- **Source phase**: rework goal review (after R5). **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), round 2 of the maintainer review.
- **Reason**: the trailer is six drawn scenes (icon, title, line) taken from the Nexus-AI README. The page is offline and self-contained, and no screenshots of the app are bundled, so it shows what the app does but not what it looks like.
- **Owner**: maintainer. **Suggested next step**: decide whether to embed a few compressed screenshots of the app (the byte ceiling now allows it) in place of the drawn icons.

**Original source identity**: `v4.13.10#WN-9`; stable ID `WN-9-v41310` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-11-v41310 (v4.13.10): The WebGL game's frame rate is unverified on a real GPU

- **Source phase**: revision 2 goal review. **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), T067.
- **Reason**: the running game measured 19 frames per second in headless Chromium, which renders WebGL in software (SwiftShader). The figure says nothing about a reader's machine, and no real GPU was available to measure it. The IDE players measured 55 frames per second and the page 59 in the same session.
- **Owner**: maintainer. **Suggested next step**: play the reward game on a laptop with integrated graphics and on a phone; if it stutters, lower the particle count and the mesh detail on small canvases.

**Original source identity**: `v4.13.10#WN-11`; stable ID `WN-11-v41310` distinguishes this obligation from repeated IDs in other patch sections.

#### WN-12-v41310 (v4.13.10): Minor visual nits left from the revision 2 review

- **Source phase**: revision 2 goal review (P3 findings). **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), R8 and R10.
- **Reason**: small findings were not fixed in this pass. Enemies spawn under the in-game level header for a moment. At 1280 px the rail shows dots only, with the current label on hover and low-contrast empty circles. The IDE editor soft-wraps long lines, which can leave a single word on a line. From the revision 3 review: an IDE highlight's label can cover a line of code above its box; on a phone's first view of the start screen the sticky Start button covers two ships' stat meters; mid-wormhole the HUD names the next level before the map label changes.
- **Owner**: guide owner. **Suggested next step**: start enemy spawns below the header band; raise the slim rail's empty-dot contrast; turn off soft wrap in the editor and let it scroll sideways like VS Code.

**Original source identity**: `v4.13.10#WN-12`; stable ID `WN-12-v41310` distinguishes this obligation from repeated IDs in other patch sections.

#### QG-2-v41310 (v4.13.10): The learner check has not been run

- **Source phase**: Phase 8 (8.8). **Plan reference**: [`v4.13.10-training-page-rebuild`](plans/v4.13.10-training-page-rebuild.md), decision 16.
- **Reason**: two or three non-technical readers must go through the page on a desktop and a phone; an agent cannot stand in for them. Per decision 16 this does not block the release.
- **Owner**: maintainer. **Suggested next step**: run it with the script in the evidence file under `## Human testing suggestions` and record the results there.

**Original source identity**: `v4.13.10#QG-2`; stable ID `QG-2-v41310` distinguishes this obligation from repeated IDs in other patch sections.

### Resolved Items

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| QG-1 | The two stamp guards were not in CI | v4.13.10, 2026-10-04 | T036 wired `stamp_guide_shared.py --check` and `stamp_training_models.py --check` into `scripts/ci/profiles.py` (docs group) and the `Makefile` beside `stamp_guide_counts.py --check`; a deliberate drift made the shared guard exit 1 for both pages. Path scoping needed no change: the `changes` job marks any non-docs path relevant. No workflow file changed. Pre-commit was not wired: it carries no stamp guard today (not even `stamp_guide_counts`), and both guards run in under a second in the docs group of every CI run and every `make validate`. |
| WN-2 | Training had no next-stage control | v4.13.10, 2026-10-04 | Maintainer review: add one. Every stage but the last now ends with a Continue link naming the next stage, its step, and its command (`continueFor` in `src/training-story.js`); `test_continue_links_walk_every_stage_in_order` walks all 15 stages by Continue alone. Superseded in R3: Training became one scrolling page, so the Continue links were removed at the maintainer's request. |
| WN-3 | The game arena started below the fold at 1440 x 900 | v4.13.10, 2026-10-04 | Maintainer review: yes. `start()` brings the whole game (arena, HUD, touch controls) into view with the minimal scroll, instant under reduced motion; `test_starting_a_game_brings_it_into_view` fails on the previous page and passes now. |
| WN-4 | Cheatsheets no longer links `/compare` and `/presentify` into Training | v4.13.10, 2026-10-04 | Maintainer review: removal confirmed. Both old hashes still redirect to the intro. |
| DF-1 | Session output appeared at once rather than typing in | v4.13.10, 2026-10-04 | Maintainer review: build it. Sessions type out on first view: the command is typed, then each report line and activity line wipes in, in reading order; layout never moves. Reduced motion shows the finished report. `test_sessions_type_out_and_skip_and_run_again`, `test_reduced_motion_never_hides_a_report`. Superseded in R4: each step is an emulated IDE whose Send runs the agent's steps; reduced motion completes a run at once. |
| DF-2 | No "Run again" control on session stages | v4.13.10, 2026-10-04 | Built with DF-1: the control reads Skip while typing and Run again after. Kept in R4 on the IDE's Send button. |
| WN-10 | The provider switch changed the model shown in the locked chat | v4.13.10, 2026-10-05 | Plan revision 2: the provider buttons are gone. Each step's IDE animation picks its own model, and `/implement` shows the harness's portability directly: Anthropic reaches its usage limit, `/handoff` runs, and the work finishes on OpenAI. `test_the_handoff_plays_from_the_usage_limit_to_the_second_provider`. |
| WN-7 | The shared opening read as a generic template | v4.13.10, 2026-10-04 | Maintainer review: keep the opening consistent but distinct per page. Each opening is now a title, a one-sentence subtitle, and one animated figure of the page's content (the Training journey, the Foundations layers, a Cheatsheets entry), drawn in a wide and a narrow form and animated with NexusSeq; the identical card rows are gone. `test_guide_openings_carry_their_own_figures`. |

## v4.13.11

Admission and normalization findings for the [known-gaps sweep plan](plans/v4.13.11-known-gaps-sweep-and-minor-close.md). Admission is based on the maintainer's 2026-10-09 exception and merged develop `ae60a3240`; main, PR #438 and tags remain maintainer-owned.

### Open Items

#### WN-39 (v4.13.11): Scheduled supply-chain audit reports vulnerable PyJWT 2.14.0

**Source phase**: Phase 1, T003. **Plan reference**: Phase 6, T029. **Severity**: medium; security. **Owner**: catalog maintainer.

**Evidence**: Scheduled main run [37322151526](https://github.com/bendourthe/Nexus-Hub/actions/runs/37322151526) failed on 2026-10-05; artifact 11350332112 was downloaded and its audit JSON names `pyjwt==2.14.0`, `PYSEC-2026-4141`, `CVE-2026-101918`, and `GHSA-42vr-xj54-vc7v`, with first fixed version `2.15.0`. The [primary advisory](https://github.com/jpadilla/pyjwt/security/advisories/GHSA-42vr-xj54-vc7v) confirms a raw request-level recursion exception before signature verification. It does not establish a process crash or authentication bypass. Retained identity and hashes: [security receipt](development/v4.13.11-supply-chain-admission.json).

**Reason**: This is a new finding after the successful 2026-09-28 audit that resolved v4.7#WN-2. That historical pass cannot close the October 5 finding. **Suggested next step**: trace the authoritative dependency and lock surfaces, pin the supported fixed version, prove deeply nested unsigned payload rejection and ordinary decoding, then run the actual project audit. **Acceptance**: all affected dependency surfaces use a qualified fixed version and the fresh audit is clean. **Proving command**: the same supply-chain audit command used by the scheduled workflow, plus the retained deterministic payload regression.

#### BG-15 (v4.13.11): Existing migration destination reuse accepts an incomplete residual copy - RESOLVED

**Source phase**: Planning adversarial review and Phase 1, T003. **Plan reference**: Phase 2, T005. **Severity**: high; data integrity. **Owner**: completion tooling maintainer.

**Reason**: `minor_close.py` can reuse the first matching Migrated-from destination without proving it contains the source obligation. A provenance-only stub, truncated copy, or duplicate matching provenance can therefore hide residual clauses while the source is marked migrated. **Suggested next step**: strengthen the existing writer and completion verifier with the same unique, complete-copy predicate; keep forward-minor, approved-ID, security and historical hash refusals. **Acceptance**: stubs, truncations and ambiguous matches refuse without writing either ledger; a complete partial-write rerun is idempotent. **Proving command**: `python -m pytest -q tests/validators/test_gap_migration_and_archive.py tests/validators/test_completion_minor_verdict.py`, including direct helper negative cases.

**Resolution, 2026-10-09 (v4.13.11 T005/T009)**: The writer and completion verifier now share a unique complete-copy predicate. Stub, truncated, ambiguous and hidden proof copies refuse before source mutation; ordinary complete copies and proven same-kind within-minor carry remain valid. Final required validators and affected carry coverage passed: `python -m pytest -q tests/validators/test_gap_migration_and_archive.py tests/validators/test_completion_minor_record.py tests/validators/test_completion_minor_verdict.py tests/validators/test_plan_carry_and_archive.py`, exit 0, 271 passed in 1229.99s (0:20:29). The real scoped ledger proof verifies all 158 complete historical copies with no parser or visibility errors. Independent security and contract reviews approved the final correction. See [Phase 2 evidence](development/v4.13.11-phase-2-evidence.md) and its retained terminal receipts. This resolution closes only the migration-copy defect; it does not close migrated residual work.

#### WN-40 (v4.13.11): Ship-balance browser fixture takes 18-38 minutes on CI

**Source phase**: Maintainer's v4.13.10 CI profiling report on 2026-10-09. **Plan reference**: Phase 5 guide batch; retain PLAN if not bounded. **Severity**: low; runtime cost. **Owner**: guide test maintainer.

**Reason**: The maintainer reports 18-38 minutes for `tests/guides/tools/game_balance.py`, called by `test_training_game_engine.py`. Profiling is dominated by native `(program)` time. `front()` state reuse and a `fitPanel` signature guard produced identical balance output and no speed-up, and were reverted. This admission records supplied observations, not an independently repeated profiling receipt. **Suggested next step**: isolate software-WebGL rendering cost on one runner, preserve the real balance assertions, and qualify any change by equal balance output and measured runtime improvement. Do not restore pytest-xdist: concurrent software-WebGL workers on one runner starve each other. **Acceptance**: a bounded representative fixture retains its balance guarantees and has measured lower single-runner runtime, or the full fixture remains explicitly deferred with profiling evidence. **Proving command**: the selected ship-balance test with `pytest --durations=1` and retained before/after balance results on the same runner configuration.

#### BG-16 (v4.13.11): Approval preparation draft uses incorrect action bounds - RESOLVED

**Source phase**: Phase 2 T008 real approval-render command after local preparation. **Severity**: medium; workflow blocker. **Owner**: completion tooling maintainer.

**Evidence**: The actual `check_plan_completion.py record render --minor v4.13 --session auto --approvals docs/releases/v4/v4.13/development/v4.13.11-approval-draft.json --summary docs/releases/v4/v4.13/development/v4.13.11-approval-summary-draft.json --page --platform codex` exited 1 with `approval page not rendered: the push-merge bound names an unknown field`. No valid page or native record was produced. The draft had already passed the native minor-spec shape check, so the producer/renderer contract must be traced rather than bypassed.

**Reason**: The supported native freeze cannot proceed when its generated minor approval payload is refused by the page renderer. **Suggested next step**: apply the smallest compatible producer/consumer correction, retaining strict unknown-field and branch/member validation, then exercise both negative fixtures and this exact real command. **Acceptance**: valid single-plan and minor payloads render their exact bounded actions; malformed or unrelated fields refuse; the actual sole-member page renders successfully. **Proving command**: focused approval-page regressions plus the exact native command above. This gap is recorded before the migration-ID freeze and cannot be closed from a mocked result alone.

**Diagnosis and resolution, 2026-10-09**: The preparation draft used numeric bounds for actions that require an explicit branch mapping or no bound. Native page validation correctly refused it before replacing a valid round. The draft now uses exact `remote`, `source`, `target` and `repo` fields for push-merge and omits bounds on cleanup-merged and archive-minor. Repush 3 and minor-close-pr 1 retain their existing retry meanings. No renderer or approval-schema change was needed. Existing focused regressions passed 27 tests (105 deselected) in 0.76 seconds, including wrong bounds, unknown fields, unsafe remotes and contradictory targets. The exact real minor-render command exited 0 and produced a page after this correction. Its pre-amend preview is verification evidence only; the final committed HEAD must be rendered separately before requesting the supported user paste. See [bound validation](development/v4.13.11-approval-bound-validation.json).
