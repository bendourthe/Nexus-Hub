# Known gaps - v4.13

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-09-15

Release-scoped gaps for the evidence-driven agent improvement plan. Planned future-phase work is tracked in the plan rather than reported as completed here.

## v4.13.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |

### Open Items

#### DF-1: Phase 6 trigger pilot deferred as UNMEASURED

**Source phase**: Implementation entry (recorded at Phase 1). **Plan reference**: Implementation entry prerequisite, T021-T024. **Reason**: the plan's fail-closed entry gate requires a native execution path providing two accessible model tiers, observed skill-selection and pause records, bounded subprocess time, an enforceable aggregate spend ceiling, and the T022 isolation controls. Read-only inspection found two of the five controls absent.

**Missing capability**: an execution path that both enforces an aggregate spend ceiling across the pilot and records organic skill selection rather than forced skill loading.

**Evidence**: `scripts/run_trigger_evals.py` is self-described as a "deterministic, model-free gate". `scripts/optimize_skill_description.py::_run_subprocess` calls `subprocess.run` with no `timeout=`, and its CLI builder passes `--skill <path>`, which explicitly loads the skill under test and so cannot observe unprompted selection. `claude --max-budget-usd` bounds a single invocation, not an aggregate across up to 96 calls. Full inspection record in `development/phase-1-evidence.md`.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: scope the pilot runner as a separate decision, per the plan's own boundary that "building an adapter or changing the two-model/cost/evidence contract requires a separately scoped decision; it is outside this plan." Candidate A3 remains unmeasured until then; no wording change may be promoted on its behalf.

#### QG-1: Phase 6 acceptance criteria unexercised

**Source phase**: Implementation entry (recorded at Phase 1). **Plan reference**: T021-T023. **Reason**: the frozen per-model acceptance criteria (no loss of positive selections, no increase in irrelevant loads or unnecessary pauses, at least one strict reduction, no trust-boundary loss) cannot be evaluated without the deferred pilot.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: evaluate against the frozen protocol once DF-1 is closed. Per the plan, an unrun pilot is UNMEASURED and is not satisfied by any structural or keyword check.

#### WN-1: Pre-existing commit-attribution findings in the fast profile

**Source phase**: Phase 1. **Plan reference**: T004. **Reason**: `python scripts/ci/run.py --profile fast` reports `check_commit_attribution` FAIL with 3186 findings across 3377 scanned commits. The branch carried zero commits when this was observed, so every finding predates this plan.

**Owner**: repository maintainer. **Status**: open. **Suggested next step**: address in a dedicated attribution-history change; this plan neither introduces nor widens the condition, and its own commits omit `Co-Authored-By` trailers per the project instruction.
