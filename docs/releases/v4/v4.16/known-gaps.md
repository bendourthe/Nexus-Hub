# Known Gaps - v4.16

**Project**: Nexus-Hub
**Status**: in-progress
**Open items**: 18

## v4.16.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 8 | 0 |
| Bugs / regressions (BG) | 1 | 0 |
| Warnings (WN) | 7 | 0 |
| Missing tests / coverage gaps (MT) | 2 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

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

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
