# Known Gaps - v4.16

**Project**: Nexus-Hub
**Status**: in-progress
**Open items**: 25

## v4.16.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 21 | 0 |
| Bugs / regressions (BG) | 2 | 2 |
| Warnings (WN) | 16 | 0 |
| Missing tests / coverage gaps (MT) | 3 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |

### Open Items

#### DF-1: Raising `references/` adoption beyond the measured 163 of 340 skills

**Source phase**: v4.15.1 Phase 3, T111 known-gaps reconciliation. **Plan reference**: [`v4.15.1-adoption-model-adaptive-harness.md`](../v4.15/plans/v4.15.1-adoption-model-adaptive-harness.md), sub-task 3.2 item 3.

The plan named 156 of 337 skills as the measured count. A scan of the merged tree on 2026-11-14 finds 163 of 340 skill folders with a `references/` directory. The count is descriptive; this plan changes no skill.

**Owner**: catalog maintainer. **Severity**: low (P3, high effort). **Status**: open. **Suggested next step**: decide in a future plan whether a target share of skills should carry Tier-3 references, and which skills benefit; no work is scheduled here.

- **Acceptance**: a plan states a target share and a per-skill selection rule
- **Proving command**: manual: count skill folders containing `references/` and compare with the stated target

#### DF-2: No root STRATEGY.md exists to ground queued plans

**Source phase**: v4.15.1 Phase 3, T111 known-gaps reconciliation. **Plan reference**: [`v4.15.1-adoption-model-adaptive-harness.md`](../v4.15/plans/v4.15.1-adoption-model-adaptive-harness.md), Knowledge-base grounding and sub-task 3.2 item 5.

The seven-lens review's product lens noted that several queued plans record the same absence of a root `STRATEGY.md`. A check on 2026-11-14 confirms the file is still absent. This plan creates none.

**Owner**: `product-strategy` skill owner. **Severity**: low. **Status**: open. **Suggested next step**: run `[[product-strategy]]` to author the anchor in a separate change, then re-ground the queued plans against it.

- **Acceptance**: a root `STRATEGY.md` exists and is cited by at least one plan's grounding section
- **Proving command**: `python -B -c "import pathlib; print(pathlib.Path('STRATEGY.md').exists())"` prints `True`

#### DF-3: Benefit, cache, and interactive model-switch behavior remain unqualified for any future runtime proposal

**Source phase**: v4.15.1 Phase 1 and Phase 3, T103 and sub-task 3.8. **Plan reference**: [`v4.15.1-adoption-model-adaptive-harness.md`](../v4.15/plans/v4.15.1-adoption-model-adaptive-harness.md), sub-tasks 1.2 and 3.8.

The injection experiment labels model benefit and live prompt-cache behavior UNEVALUATED, the symlink-path control was unavailable on the Windows account used, and no interactive `/model` switch was observed against transcript metadata. The decision declines an automatic runtime on this evidence, so none of these blocks the verdict. They are the evidence a future runtime proposal would have to supply first.

**Owner**: catalog maintainer. **Severity**: low. **Status**: open. **Suggested next step**: if a runtime is ever proposed again, qualify the three limits before the proposal, and ask a human to switch models mid-session and confirm the transcript metadata follows the switch.

- **Acceptance**: a future proposal cites a measured benefit, a cache observation, and a model-switch observation
- **Proving command**: manual: open the future proposal's evidence and confirm each of the three items is present with a quoted observation

#### WN-1: The full local CI profile cannot pass on this Windows host within its fixed shard timeouts

**Source phase**: v4.15.1 Phase 3 full-suite testing, 2026-11-15. **Plan reference**: [`v4.15.1-adoption-model-adaptive-harness.md`](../v4.15/plans/v4.15.1-adoption-model-adaptive-harness.md), final-phase full-suite duty.

`repo-tests-governance-validators-d-o` exceeded the profile's fixed 1800 s timeout twice (1823 s and 1813.7 s) and passed untimed in 8774 s (1144 passed, 2 skipped). Hosted CI runs the same tests split across shorter jobs and is not affected; every final phase run locally on this host will hit the same timeout.

**Owner**: CI owner. **Severity**: low - local evidence only; hosted CI is the gate. **Status**: open. **Suggested next step**: size the local profile shards by measured duration per process launch (the Windows shard-sizing rule), or make the per-command timeout scale with a measured host factor.

- **Acceptance**: `python -B scripts/ci/run.py --profile full` completes without a timeout on this host
- **Proving command**: `python -B scripts/ci/run.py --profile full`

#### DF-45: No live harness pairing trial and no live Claude `AGENTS.md` session were run

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phases 1 to 4

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md); [`v4.15.2-claude-agents-evaluation.md`](development/v4.15.2-claude-agents-evaluation.md)

**Reason**: the spend cap for the run was USD 0, so the pairing evaluator ran only against synthetic fixtures and no real Claude Code session read a shared project `AGENTS.md`.

**Owner**: catalog maintainer. **Severity**: medium - the evaluator and the shared-file path have no live receipt. **Status**: open.

**Suggested next step**: after DF-46 ships a backend, run one approved live pairing trial and one live Claude `AGENTS.md` session through it, and record both receipts.

**Acceptance**: a live pairing receipt and a live Claude session transcript are recorded under `docs/releases/v4/v4.15/development/` with the spend limit named.

**Proving command**: manual: `python -B scripts/evaluate_harness_pairings.py --help`, then the approved live run named in the guide `guides/reference/HARNESS_PAIRING_EVALUATION.md`

#### DF-46: No isolation backend ships, so live evaluator modes are refused

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 1

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md)

**Reason**: live modes stop with `isolation-backend-unavailable` because no backend proves filesystem, process-tree, network, credential-injection and cleanup containment.

**Owner**: catalog maintainer. **Severity**: medium - blocks every live pairing run. **Status**: open.

**Suggested next step**: build or select a backend under `agent-execution-isolation` that proves those five containment properties, then register it with the evaluator.

**Acceptance**: the evaluator accepts a live mode with the backend present and refuses it with the backend removed; each containment property has a passing probe.

**Proving command**: `python -B -m pytest tests/ -k harness_pairing -q`

#### MT-9: The pairing runner's POSIX behavior was not exercised

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 1

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md)

**Reason**: `killpg` and the path checks in the runner were run on a Windows host only.

**Owner**: catalog maintainer. **Severity**: low - Windows is the only host observed. **Status**: open.

**Suggested next step**: run the evaluator's fixture tests on Linux and macOS, either locally or on the CI matrix, and fix any difference.

**Acceptance**: the evaluator tests pass on a Linux and a macOS host.

**Proving command**: `python -B -m pytest tests/ -k harness_pairing -q` on Linux and macOS

#### DF-47: Three platforms still write their own template into the shared `AGENTS.md` block

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 3

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md); [`v4.15.2-shared-agents-inventory.md`](development/v4.15.2-shared-agents-inventory.md)

**Reason**: Antigravity 2.0, OpenClaw and the Windsurf root file write platform-specific text into the shared block, so they cannot yet join the shared-owner migration.

**Owner**: catalog maintainer. **Severity**: low - those platforms keep working through their current path. **Status**: open.

**Suggested next step**: give each platform a verified sidecar or global owner for its platform-specific text, then migrate it to the shared body.

**Acceptance**: no platform writes its own template into the shared `AGENTS.md` block, and the migration tests cover all three.

**Proving command**: `python -B -m pytest tests/installer/test_verify_read_paths.py -k migration -q`

#### MT-10: Both installers were edited and parse-checked but not executed

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 3

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md)

**Reason**: each installer gained one checklist row and passed `bash -n` and the Windows PowerShell 5.1 parser with 0 errors, but the run rules did not allow executing them. The registry runner that both call was exercised end to end.

**Owner**: catalog maintainer. **Severity**: medium - installer behavior is parse-checked only. **Status**: open.

**Suggested next step**: run both installers into disposable roots on the CI matrix and record the output.

**Acceptance**: both installers complete a disposable-root run on Windows, Linux and macOS with the new checklist row present.

**Proving command**: `python -B scripts/ci/run.py --profile full` plus the installer smoke jobs on CI

#### WN-33: Claude Code vendor inputs for the shared-file decision are best effort

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 3

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md); [platform-read-contracts.md](../../../policy/platform-read-contracts.md)

**Reason**: managed-settings file locations, provider-surface environment variables and the `enabledPlugins` shape for a disabled built-in reader are unverified and fail toward `CLAUDE.md`. The vendor memory page lists three residual differences, not the eight the plan recorded, so only sourced ones are published.

**Owner**: catalog maintainer. **Severity**: low - every unknown case keeps `CLAUDE.md`. **Status**: open.

**Suggested next step**: re-read the vendor pages and verify each input on a real installation, then publish only what is sourced.

**Acceptance**: each input is marked verified with a source URL and date in the read contract, or marked unverified with its fallback.

**Proving command**: `python -B scripts/check_platform_contract_freshness.py`

#### DF-48: Two upstream dependencies of the harness work were not landed

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 2

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md)

**Reason**: the `v4.16.2` harness-cost guidance and the `v4.19.0` evidence vocabulary were recorded as dependencies and are not yet shipped.

**Owner**: catalog maintainer. **Severity**: low - the work is sequenced after this plan. **Status**: open.

**Suggested next step**: land each in its own plan, then re-run the Phase 2 references against it.

**Acceptance**: both plans are released and the Phase 2 references name the shipped guidance.

**Proving command**: manual: confirm the v4.16.2 and v4.19.0 releases exist, then `python -B scripts/ci/run.py --profile fast`

#### BG-9: The harness audit's marker check looks for markers the installer never writes

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 3 (noticed, not fixed, outside scope)

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md)

**Reason**: `scripts/harness_audit.py::_has_marker` searches for `<!-- nexus-hub:start -->`, but the real markers are `<!-- NEXUS_HUB_START -->`, so the per-integration `marker_integrity` axis always reads 0 of N for a real install.

**Owner**: catalog maintainer. **Severity**: medium - an audit axis reports a false failure. **Status**: open.

**Suggested next step**: match the real marker, and add a test that renders a real install and reads a non-zero count.

**Acceptance**: `marker_integrity` reads N of N on a fresh install of the supported integrations.

**Proving command**: `python -B -m pytest tests/ -k harness_audit -q`

#### BG-12: The 20-second plan-check budget runs out before a large minor's migration proof finishes

**Source phase**: 2026-11-22 Nexus-AI v2.16 re-check after the BG-10 and BG-11 fixes (observed downstream, not fixed).

**Plan reference**: none; found while re-checking a consumer project's archived minor.

**Reason**: `scripts/check_plan_completion.py` gives every plan check a fixed `BUDGET_SECONDS = 20.0` with no override. On the archived Nexus-AI v2.16.2 plan the `gaps.carried` proof over 248 migrated items alone takes 20.7 seconds, so the check reports `INCOMPLETE: gaps.carried archive.minor`, both as `cannot-verify`. Run with a 900-second budget, `gaps.carried` is met in 20.7 seconds and `archive.minor` in 0.4 seconds, with no failing git call. The verdict is honest (unproven, not failed) but can never become `PLAN COMPLETE` for a minor of this size.

**Owner**: catalog maintainer. **Severity**: medium - a correct, fully closed minor cannot reach its completion verdict. **Status**: open.

**Suggested next step**: make the migration proof cheaper (for example, read each ledger at `start_head` once instead of once per item), or scale the budget with the number of migrated items; keep `cannot-verify` when the budget is still exceeded.

**Acceptance**: `check <plan>` on a plan whose minor migrated about 250 items reports `gaps.carried` and `archive.minor` met within the budget.

**Proving command**: manual: run `check_plan_completion.py check <archived v2.16.2 plan>` from the Nexus-AI main checkout and read the two conditions

#### WN-34: Pytest runs left five empty lock files in the real user state folder

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 Phase 3

**Plan reference**: [v4.15.2 plan](plans/v4.15.2-adoption-harness-economics-and-portable-engineering-system.md)

**Reason**: before `NEXUS_HUB_HOME` isolation fixtures were added to the new installer tests, the worker's runs created five empty lock files under `~/.nexus-hub/state/locks/`. They are harmless markers.

**Owner**: catalog maintainer. **Severity**: low - empty files only. **Status**: open.

**Suggested next step**: delete the five empty files under `~/.nexus-hub/state/locks/` at minor close.

**Acceptance**: no empty lock file remains under `~/.nexus-hub/state/locks/` after the cleanup.

**Proving command**: `Get-ChildItem "$env:USERPROFILE\.nexus-hub\state\locks" | Where-Object Length -eq 0` returns nothing

#### WN-35: The v4.15.0 release skipped the back-merge of `main` into `develop`

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 publication run, 2026-11-16

**Plan reference**: [v4.15.1 release](../../../../CHANGELOG.md)

**Reason**: without the back-merge, the v4.15.1 develop-to-main pull request showed BEHIND until PR #667 merged `main` back into `develop`.

**Owner**: catalog maintainer. **Severity**: medium - a skipped step blocks the next release pull request. **Status**: open.

**Suggested next step**: `/update release` must back-merge `main` into `develop` after every release. It did so for v4.15.1 (PR #668).

**Acceptance**: every release since v4.15.1 shows `main` merged into `develop` before the next version starts.

**Proving command**: `git merge-base --is-ancestor origin/main origin/develop`

#### WN-36: Two guide-render browser tests timed out once on CI and passed on rerun

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 publication run, 2026-11-16

**Plan reference**: PR #671, run 43927442771

**Reason**: `tests/guides/test_training_game_revision10.py::test_the_finale_hands_off_to_the_reward_panel_in_real_time` and `tests/guides/test_training_game_revision13.py::test_the_passage_shares_no_element_with_the_level_wormholes_or_the_finale[2d]` timed out in the CI job guide-render (game) on attempt 1 and passed on attempt 2.

**Owner**: catalog maintainer. **Severity**: low - passes on rerun, but costs a rerun. **Status**: open.

**Suggested next step**: capture the timing of both tests on a hosted runner, then raise the wait or fix the cause.

**Acceptance**: both tests pass on 10 consecutive hosted runs.

**Proving command**: `python -B -m pytest tests/guides/test_training_game_revision10.py tests/guides/test_training_game_revision13.py -q`

#### WN-37: Native short replies are matched case-sensitively

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 publication run, 2026-11-16 (affects v4.15.10, approval modes)

**Plan reference**: `scripts/approval_binding.py`

**Reason**: `SHORT_REPLIES` holds `Approve`, `Yes` and `Continue` and is matched case-sensitively, so a lowercase `continue` was not captured as a native reply.

**Owner**: catalog maintainer. **Severity**: low - the reply is refused, not misread. **Status**: open.

**Suggested next step**: decide whether lowercase replies should bind, and either match case-insensitively with a test or state the rule in the approval page.

**Acceptance**: a lowercase `continue` is either captured or refused with a message that names the accepted spellings.

**Proving command**: `python -B -m pytest tests/ -k approval_binding -q`

#### WN-38: `record controller-handoff` preview and apply disagreed on the same arguments

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: v4.15.2 publication run, 2026-11-16 (generation 5 to 6)

**Plan reference**: `scripts/completion_minor.py`

**Reason**: the preview printed `BLOCKED: target-remote-outside-approval`, while the immediately following `--apply` with identical arguments printed `TRANSFERRED`.

**Owner**: catalog maintainer. **Severity**: medium - a preview that blocks while apply succeeds cannot be trusted as a gate. **Status**: open.

**Suggested next step**: reproduce with a recorded run, find the check that differs between preview and apply, and make both use the same check.

**Acceptance**: preview and apply print the same verdict for identical arguments in a fixture that reproduces the case.

**Proving command**: `python -B -m pytest tests/validators -k controller_handoff -q`

#### DF-49: Settings 0.8.8 has no second-machine, active-session or native hover evidence

**Carried from**: v4.15 ledger, section v4.15.2 (id preserved, text unchanged).

**Source phase**: Settings 0.8.8 repair, 2026-11-16

**Plan reference**: [settings-portability-repair.md](development/settings-portability-repair.md)

**Reason**: 0.8.8 has no second-machine verification, no packaged-host restart against an active authenticated provider session, and no observed native-pane hover rendering.

**Owner**: Settings maintainer. **Severity**: medium - the repair is verified only on the build machine. **Status**: open.

**Suggested next step**: install 0.8.8 on the second machine, restart against an active Claude and Codex session, and look at the native hover in the pane.

**Acceptance**: the evidence file records all three observations with the machine and date.

**Proving command**: manual: the three checks named above, recorded in `docs/releases/v4/v4.15/development/settings-portability-repair.md`

#### DF-50: The evaluator receipt cannot carry feedback-cadence fields

**Carried from**: v4.15 ledger, section v4.15.3 (id preserved, text unchanged).

**Owner**: evaluator owner. **Severity**: medium; blocks a live cadence study. **Source phase**: v4.15.3 Phase 2. **Plan reference**: cadence matrix tasks.

**Reason**: The v4.15.2 evaluator receipt has no fields for feedback timing, initial versus post-repair acceptance, feedback and repair counts, or spend provenance beyond cost. v4.15.3 works around this with a sidecar history written by the fake adapter. **Suggested next step**: extend the pairing contract with these fields before any live cadence study. **Acceptance**: a receipt carries the fields and the cadence matrix reads them without the sidecar. **Proving command**: the cadence matrix tests in `tests/skills/` with the sidecar removed.

#### DF-51: The security envelope has no proof class or duplicate links

**Carried from**: v4.15 ledger, section v4.15.3 (id preserved, text unchanged).

**Owner**: security-review. **Severity**: low. **Source phase**: v4.15.3 Phase 3. **Plan reference**: generic review projection tasks.

**Reason**: The normalized security envelope has no proof class and no duplicate or root-cause links, so the projection lists them as unavailable and no static-only control exists. Duplicate handling is exercised only in the workflow consumer. **Suggested next step**: add the fields to the envelope when a consumer needs them. **Acceptance**: the projection fills both fields from the envelope and a static-only control is tested. **Proving command**: `python -B -m pytest tests/skills -q -k projection`.

#### DF-52: The CI comparison predates the v4.15.7 contract rewrite

**Carried from**: v4.15 ledger, section v4.15.3 (id preserved, text unchanged).

**Owner**: coordinator. **Severity**: low. **Source phase**: v4.15.3 Phase 4. **Plan reference**: CI/CD comparison task.

**Reason**: The six-step comparison was made against `docs/policy/ci-cd-lifecycle-contract.md` before v4.15.7 rewrites it. **Suggested next step**: repeat the six-step comparison after v4.15.7 merges. **Acceptance**: the comparison is recorded against the rewritten contract. **Proving command**: manual: the comparison steps in the v4.15.3 last-phase evidence, rerun on the post-v4.15.7 tree.

#### MT-11: The review fan-out workflow template ran only under a Node stub

**Carried from**: v4.15 ledger, section v4.15.3 (id preserved, text unchanged).

**Owner**: coordinator. **Severity**: low. **Source phase**: v4.15.3 Phase 3. **Plan reference**: fan-out template task.

**Reason**: `review-fanout-workflow.js` was exercised under a Node stub, not a native Dynamic Workflows run. **Suggested next step**: one native run when the runtime is available. **Acceptance**: a native run completes and its output matches the stub run's projection. **Proving command**: manual: one native Dynamic Workflows run of the template.

#### QG-7: The coverage threshold was not measured

**Carried from**: v4.15 ledger, section v4.15.3 (id preserved, text unchanged).

**Owner**: coordinator. **Severity**: low. **Source phase**: v4.15.3 Phase 4. **Plan reference**: final validation task.

**Reason**: Coverage was not collected in the lane, so the threshold is ungated for this plan. **Suggested next step**: read the coverage result from hosted CI. **Acceptance**: coverage of the new modules is measured and meets the project threshold. **Proving command**: hosted CI coverage job on the integration pull request.

#### WN-39: The review projection has no integrity seal

**Carried from**: v4.15 ledger, section v4.15.3 (id preserved, text unchanged).

**Owner**: coordinator. **Severity**: low. **Source phase**: v4.15.3 review pass (LV-1). **Plan reference**: generic review projection tasks.

**Reason**: A forged projection paired with a matching expected context can inject findings, because the projection carries no seal. **Suggested next step**: optional hardening; add `run_fingerprint` to the expected context. **Acceptance**: a projection whose fingerprint does not match the run is rejected. **Proving command**: a negative test with a forged projection.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|

#### BG-11: A run record cannot be found after its worktree is removed

**Source phase**: 2026-11-21 Nexus-AI v2.16 minor close (observed downstream, not fixed).

**Plan reference**: none; found while closing a consumer project's minor.

**Reason**: `scripts/check_plan_completion.py` locates the run record from the repository top level of the starting directory. Once the plan's worktree is removed (which the cleanup step requires), the record is no longer found, so `approval.remote` and `archive.minor` cannot be verified, and the checker has no option to name a record directly.

**Further finding, 2026-11-21**: the record key is a hash of the repository root, the repository and the plan path, and the archive changes two of them (the worktree root and `docs/releases/` to `docs/archives/`). Neither `repo_root` nor `plan` is in the signed payload, so a re-key needs no new signature. The archive's link repair also rewrites relative links inside the plan, so the frozen, signed `plan_sha256` no longer matches: on the Nexus-AI v2.16.2 plan the pre-archive text matches and the archived text (18 bytes longer) does not. Re-keying alone would therefore turn `approval.remote cannot-verify` into `record-tampered`. A fix must also define when an archived plan counts as unchanged, for example by reversing the archive's own link rewrite before hashing.

**Owner**: catalog maintainer. **Severity**: medium - completing cleanup prevents the completion verdict it is meant to enable. **Status**: resolved.

**Suggested next step**: resolve the record through the main worktree or the plan path when the recorded worktree is gone, or add a signed re-key action; keep `record-tampered` detection intact.

**Acceptance**: after `cleanup_merged.py --apply` removes the plan worktree, `check <plan>` from the main checkout finds the same record.

**Proving command**: manual: remove a finished plan's worktree, then run `check_plan_completion.py check <plan>` from the main checkout

**Resolution**: `plan_hash_matches` accepts an archived plan whose approved text, found by the frozen hash in the history of its former active-tree path, differs only in relative links and tree mentions that resolve to the same targets; any other edit still reads as `record-tampered`. `check_plan_completion.py record rekey <archived plan> --session <id> [--apply]` moves the record to the plan's current key, changing only the unsigned `repo_root` and `plan`. Tests: the four `test_rekey_*` cases in `tests/validators/test_check_plan_completion.py`. Checked against the Nexus-AI v2.16.2 record: the archived plan matches its frozen hash, an edited copy does not, and the dry run names the record.

#### BG-10: Per-plan migration check rejects the minor-scoped label the minor-close tool writes

**Source phase**: 2026-11-21 Nexus-AI v2.16 minor close (observed downstream, not fixed).

**Plan reference**: none; found while closing a consumer project's minor.

**Reason**: `scripts/minor_close.py` writes `**Migrated from**: <minor>#<id>` (for example `v2.16#DF-1`), but `scripts/completion_minor.py::plan_migration_met` builds the label from the patch section (`v2.16.0#DF-1`). Every item migrated by a minor close therefore reads `migration-target-missing`, and `gaps.carried` can never pass for that minor's plans. Nexus-AI v2.16 shows 248 such items.

**Owner**: catalog maintainer. **Severity**: medium - a correct minor close cannot reach `PLAN COMPLETE`. **Status**: resolved.

**Suggested next step**: accept both the patch-scoped and the minor-scoped label when the minor-scoped one names the item's minor and the item id is unique in that minor; add a test that runs a minor close and then the plan check.

**Acceptance**: a plan whose gaps were migrated by `minor_close.py` reports `gaps.carried` met.

**Proving command**: `python -B -m pytest tests/validators/test_gap_migration_and_archive.py -q`

**Resolution**: `plan_migration_met` in `scripts/completion_minor.py` falls back to the minor form when the patch form is missing and exactly one migrated item in the source ledger carries the id; two migrated items with one id still need the patch form. Test: `test_plan_check_accepts_minor_close_label_only_for_one_migrated_id`. Checked against the Nexus-AI v2.16 ledger: 248 of 248 migrated items met, `gaps.carried met`.

#### DF-53: Historical ledgers incompatible with fail-closed parsing

**Carried from**: v4.15 ledger, section v4.15.4 (id preserved, text unchanged).

**Source phase**: v4.15.4 plan, consumer handoff 1

**Plan reference**: [v4.15.4 plan](plans/v4.15.4-checker-evidence-and-diagnostics.md), Scope and Dispositions; [last-phase evidence](development/v4.15.4-last-phase-evidence.md)

**Reason**: changing how older ledgers are parsed is a policy change. This plan allowed no cutoff date and no exemption for finalized ledgers.

**Suggested next step**: design a structured historical-ledger contract before changing the parsing.

#### DF-54: Test failures recorded in prose

**Carried from**: v4.15 ledger, section v4.15.4 (id preserved, text unchanged).

**Source phase**: v4.15.4 plan, consumer handoff 2

**Plan reference**: [v4.15.4 plan](plans/v4.15.4-checker-evidence-and-diagnostics.md), Scope and Dispositions

**Reason**: accepting a prose record of known failures changes evidence policy. The `tests.evidence` predicate stays unchanged in this plan.

**Suggested next step**: design a structured baseline and CI evidence record.

#### DF-55: Run record recreation and renumbering

**Carried from**: v4.15 ledger, section v4.15.4 (id preserved, text unchanged).

**Source phase**: v4.15.4 plan, consumer handoff 4

**Plan reference**: [v4.15.4 plan](plans/v4.15.4-checker-evidence-and-diagnostics.md), Scope and Dispositions

**Reason**: the plan allowed no `start_head` inheritance and no re-signing of an existing record.

**Suggested next step**: write a separate design for migrating approval identity to a recreated record.

#### DF-56: Recently active and detached worktree cleanup

**Carried from**: v4.15 ledger, section v4.15.4 (id preserved, text unchanged).

**Source phase**: v4.15.4 plan, consumer handoff 5

**Plan reference**: [v4.15.4 plan](plans/v4.15.4-checker-evidence-and-diagnostics.md), Scope and Dispositions

**Reason**: the cleanup idle thresholds and the protection for detached worktrees were kept as they are.

**Suggested next step**: decide whether any idle threshold should be configurable.

#### DF-57: Missing prompt capture

**Carried from**: v4.15 ledger, section v4.15.4 (id preserved, text unchanged).

**Source phase**: v4.15.4 plan, consumer handoff 7

**Plan reference**: [v4.15.4 plan](plans/v4.15.4-checker-evidence-and-diagnostics.md), Scope and Dispositions

**Reason**: not confirmed. The cited prompt line began with `Continue`, not with a slash command.

**Suggested next step**: reproduce with a real capture before any redesign.

#### DF-58: Record mutation from a sibling-worktree controller

**Carried from**: v4.15 ledger, section v4.15.4 (id preserved, text unchanged).

**Source phase**: v4.15.4 plan, consumer handoff 9

**Plan reference**: [v4.15.4 plan](plans/v4.15.4-checker-evidence-and-diagnostics.md), Scope and Dispositions

**Reason**: only the diagnostic shipped in this plan.

**Suggested next step**: design rekeying of the record by the common git directory, if wanted.

#### WN-41: Repository description says 21 commands, README says 22

**Carried from**: v4.15 ledger, section v4.15.4 (id preserved, text unchanged).

**Source phase**: v4.15.4 Phase 5, git-tree hygiene

**Plan reference**: [last-phase evidence](development/v4.15.4-last-phase-evidence.md), Git-tree hygiene

**Reason**: `check_release_preconditions.py --repo-settings` reports the mismatch. The GitHub repository description is a repository setting outside the files this plan can change.

**Suggested next step**: update the description to 22 commands with `gh repo edit --description` at the next release, under the maintainer's approval.

#### DF-59: Unused-tool report

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 plan grill (T005)

**Plan reference**: [v4.15.5 plan](plans/v4.15.5-adoption-token-economizer-and-agent-scripts.md), comparison item B

**Reason**: Claude Code's MCP documentation (https://code.claude.com/docs/en/mcp, "Scale with MCP tool search") states that tool search is on by default and that "Only tool names and server instructions load at session start", so an unused-tool report saves little on current Claude Code.

**Suggested next step**: revisit in v4.16.4 after v4.16.3's context attribution, for setups without tool search (`ENABLE_TOOL_SEARCH=false`, Microsoft Foundry on Azure, models earlier than Opus 4 and Sonnet 4). Scope it at server level.

#### DF-60: No live Claude Code payload capture

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Phase 2 (T007)

**Plan reference**: [implementation decisions](development/v4.15.5-implementation-decisions.md), T007

**Reason**: a live `claude -p` capture is a paid call and the lane's spend cap was USD 0. The maintainer accepted the documented payload format on 2026-11-18.

**Suggested next step**: capture redacted payloads once, when a run already holds spend authority, and compare them with the documented fields.

#### DF-61: Default-on measurement of the stuck-turn notice

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Phase 2 (T018)

**Plan reference**: [implementation decisions](development/v4.15.5-implementation-decisions.md), T018

**Reason**: deciding a default needs consent to read at least 30 real sessions across 3 projects and a maintainer spot-check of 5 labels. The maintainer chose to ship opt-in on 2026-11-18.

**Suggested next step**: with consent, run `python catalog/hooks/_turn_ledger.py replay-transcripts <dir>` over real sessions and decide the default in a later minor.

#### DF-63: Ledger retention below the size cap and fact-store bounds

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Tier 3 deep pass (adversarial review, 2026-11-18)

**Plan reference**: [last-phase evidence](development/v4.15.5-last-phase-evidence.md), Tier 3 deep pass

**Reason**: the 30-day filter runs only when the ledger exceeds 256 KiB, a long single session never rotates, and `env-facts.json` has no entry cap or expiry.

**Suggested next step**: prune by age at session-start rotation regardless of size, and cap fact entries by `last_seen`.

#### WN-42: Windows PowerShell 5.1 wrapper latency above budget

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Phase 2 (T013)

**Plan reference**: [implementation decisions](development/v4.15.5-implementation-decisions.md), T013

**Reason**: on a loaded host the `ps1` wrapper p95 was 856 ms to 1082 ms against a 500 ms budget, mostly PowerShell's own start-up. Accepted while the notice is opt-in (maintainer decision, 2026-11-18).

**Suggested next step**: re-measure on a quiet host; if it still misses, prefer the `.sh` wrapper where Git Bash exists.

#### WN-43: Kimi hook matcher does not match Kimi tool names

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Phase 2 (predates this plan)

**Plan reference**: [last-phase evidence](development/v4.15.5-last-phase-evidence.md)

**Reason**: the derived Kimi matcher is `^(Bash|Edit|Write)$`, while Kimi's tools are named `Shell`, `WriteFile` and `StrReplaceFile`, so no Kimi tool hook fires.

**Suggested next step**: map Kimi tool names in the Kimi settings derivation and add a test.

#### WN-49: Stuck-turn failure signal misses Windows Qwen installs and Copilot

**Carried from**: v4.15 ledger, section v4.15.5 (recorded at release; the remainder of WN-44).

**Source phase**: v4.15.5 T015 (derivation fix, pull request #705)

**Plan reference**: [last-phase evidence](development/v4.15.5-last-phase-evidence.md)

**Reason**: Qwen now receives `PostToolUseFailure` on a POSIX install, but the settings.json derivation registers only the installing host's shell flavor, and the catalog failure matcher is `Bash` alone, so a Windows Qwen install drops it. The Copilot derivation still drops `postToolUseFailure`.

**Suggested next step**: register the failure entry on `Bash|PowerShell` in `catalog/hooks/settings.json` (checking Claude Code's PowerShell tool payload first), and map Copilot's `postToolUseFailure` in `scripts/lib/integrations/copilot.py` once its payload is verified.

#### WN-45: Lifespan audit flags every v4.15 member edit after the v4.15.0 tag

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Phase 4

**Plan reference**: [last-phase evidence](development/v4.15.5-last-phase-evidence.md), Architecture refactor

**Reason**: `audit-docs.py lifespan-contradictions` reports 48 findings, 5 of them on this plan's files, because it compares member edits with the first tag of the minor.

**Suggested next step**: compare against each member's own release tag instead of the minor's first tag.

#### WN-46: Ledger appends are not atomic across processes on Windows

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Tier 3 deep pass

**Plan reference**: [last-phase evidence](development/v4.15.5-last-phase-evidence.md), Tier 3 deep pass

**Reason**: the C runtime implements append as seek-then-write, so parallel tool calls can overwrite a ledger line, and a parallel call can name the wrong command in a notice. Both stay within the documented worst case of a missed or duplicate notice.

**Suggested next step**: document the limitation in the helper, or append through a Windows handle opened with append-only access; echo a command only when it matches the signal key.

#### WN-47: State directory trust and key creation

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Tier 3 deep pass

**Plan reference**: [last-phase evidence](development/v4.15.5-last-phase-evidence.md), Tier 3 deep pass

**Reason**: the helper does not check the owner or mode of `~/.nexus-hub/state/`, opens files by name after a symlink check, and an interrupted key creation leaves an empty `ledger.key` that silently disables the feature. Exploiting the first two needs another local principal with write access to the state directory.

**Suggested next step**: on POSIX open with `O_NOFOLLOW` and refuse group- or world-writable or foreign-owned directories; write the key through a temporary file and rename.

#### WN-48: Bash wrapper stdin handling

**Carried from**: v4.15 ledger, section v4.15.5 (id preserved, text unchanged).

**Source phase**: v4.15.5 Tier 3 deep pass

**Plan reference**: [last-phase evidence](development/v4.15.5-last-phase-evidence.md), Tier 3 deep pass

**Reason**: `stuck-turn-notice.sh` reads stdin one byte at a time (about 2 s for a 900 KB payload on Git Bash), and payloads over 1 MiB are dropped silently, so large writes never count toward edit churn.

**Suggested next step**: pipe stdin straight to the first available interpreter and buffer only when a fallback is needed.
