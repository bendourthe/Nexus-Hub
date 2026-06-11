# Known Gaps -- v3.3.0

**Status**: v3.3.0 `adoption-loop-engineering` is in progress. Phases 1-2 are complete on `feat/adoption-loop-engineering` (Phase 1: Foundation -- loop-engineering skill + schema + seeded library; Phase 2: goal-based stopping + independent-evaluator pattern enrichments); Phases 3-4 remain. Phase 2 introduced no new gaps -- it edited three SKILL.md bodies only, added no skill, and changed no JSON registry.
**Last updated**: 2026-06-11 (adoption-loop-engineering Phase 2 complete)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.3.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 1 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 3 | 0 |
| QG | 0 | 0 |
| **Total** | **4** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| DF-v33-1 | DF | adoption-loop-engineering Phase 1 | T1.1/T1.5; Phase 4 T4.1 | `catalog/skills/workflow/loop-engineering/SKILL.md` carries the intentionally pushy description required by the plan and AGENTS.md, so the bare default `scripts/validate_skills.py` description-length rule would flag it until the planned allowlist edit lands. This is deferred by design: `make validate` and CI use `--bundles-only` and `--quality`, which passed, and Phase 4 owns the allowlist update. | In Phase 4, add `catalog/skills/workflow/loop-engineering/SKILL.md` to `scripts/validate_skills.allowlist.json` without shortening the description, then confirm the strict `--allow-existing` path demotes the length issue. | Low (not a `make validate` gate; deliberate Phase 4 scope) |
| WN-v33-1 | WN | adoption-loop-engineering Phase 1 | T1.5 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` was run by invoking the underlying validators directly. The context-compressor eval gate and targeted pytest run first hit sandbox/host-temp `PermissionError` failures, then passed when rerun with host temp access. | Confirm CI `validate` and relevant tests are green on the ubuntu runner. No code change expected; alternatively set a writable temp directory for local sandboxed runs. | Low (direct validator equivalents and targeted tests passed) |
| WN-v33-2 | WN | adoption-loop-engineering Phase 1 | T1.5 (Testing and Stabilization) | The global bundle and quality audits pass with pre-existing warnings outside this phase: `demo-capture` has an orphan `.pyc` under its skill bundle, and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. The new `loop-engineering` bundle and quality checks are clean, and the new files are ASCII-clean. | Handle the pre-existing warnings in a dedicated cleanup pass; do not change unrelated files during this phase. | Low (warnings are unrelated to Phase 1 and do not fail the gate) |
| WN-v33-3 | WN | adoption-loop-engineering Phase 1 | T1.4 (Register the skill) | Machine-readable registries now agree at 252 skills (`data/skills.json` array/statistics and `data/marketplace.json` category sum), but headline prose count surfaces are intentionally not reconciled here per the plan: `data/SKILL_INDEX.md` Total label, `data/marketplace.json` plugin description, README, AGENTS.md, and similar release prose still reflect pre-Phase-1 counts. | Reconcile headline count prose during the develop-to-main release via `/update version` or `/update release`, not in this Phase 1 feature branch. | Low (machine-readable registries are consistent; prose reconciliation is release-owned) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none) | - | - | - | Phase 1 is the first phase of this plan. |
