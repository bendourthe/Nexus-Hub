# Known Gaps - v4.16

**Project**: Nexus-Hub
**Status**: in-progress
**Open items**: 4

## v4.16.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
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

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
