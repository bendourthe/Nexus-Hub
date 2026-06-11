# Known Gaps -- v3.3.0

**Status**: v3.3.0 `adoption-loop-engineering` is complete on `feat/adoption-loop-engineering` (Phase 1: Foundation -- loop-engineering skill + schema + seeded library; Phase 2: goal-based stopping + independent-evaluator pattern enrichments; Phase 3: scheduled-triage recipe + named loop anti-patterns; Phase 4: catalog integration, validation, and release readiness). Phase 4 added the allowlist entry (resolving DF-v33-1), staged the `## [Unreleased]` CHANGELOG entry, and ran the full gate; it changed only `scripts/validate_skills.allowlist.json` and `CHANGELOG.md` and added no skill or reference file. The plan is ready for the develop-to-main release via `/update version` (MINOR -> v3.3.0), which owns the headline-count reconciliation (WN-v33-3).
**Last updated**: 2026-06-11 (adoption-loop-engineering Phase 4 complete)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.3.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 1 |
| BG | 1 | 0 |
| MT | 0 | 0 |
| WN | 4 | 0 |
| QG | 0 | 0 |
| **Total** | **5** | **1** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v33-1 | WN | adoption-loop-engineering Phase 1; re-confirmed Phase 4 | T1.5, T4.5 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` and `make scan` were run by invoking the underlying validators and the scanner directly. In Phase 4 the full direct chain (10 validate steps + the skill-security scan) passed green. | Confirm CI `validate` and `scan` are green on the ubuntu runner. No code change expected; alternatively set a writable temp directory for local sandboxed runs. | Low (direct validator/scanner equivalents passed) |
| WN-v33-4 | WN | adoption-loop-engineering Phase 4 | T4.1/T4.3 (allowlist + cross-link audit) | The strict `scripts/validate_skills.py --allow-existing` pass reports 3 errors for pushy-description skills that are NOT in `scripts/validate_skills.allowlist.json`: `catalog/skills/security/ai-attack-patterns/SKILL.md` (869 chars), `catalog/skills/security/pentest-reporting/SKILL.md` (833 chars), and `catalog/skills/workflow/git-branching-workflow/SKILL.md` (805 chars). All three predate this plan and are out of its scope (this phase only allowlisted the new `loop-engineering` skill). `make validate` does not run the description-length check, so the catalog gate is unaffected. | In a dedicated allowlist-drain pass, add the three skills to `scripts/validate_skills.allowlist.json` (or shorten their descriptions) so the strict `--allow-existing` path is clean. | Low (not a `make validate` gate; pre-existing, out of scope) |
| BG-v33-1 | BG | adoption-loop-engineering Phase 4 | T4.3 (cross-link audit) | `catalog/skills/workflow/session-teach-back/SKILL.md` contains a dangling wikilink `[[generate-session-history]]`; the real catalog skill is `session-history`. Introduced in v3.2.0 (commit db9db4b, the `adoption-teach` work), it predates this plan and is out of its scope. All wikilinks added by this plan (Phases 1-3) resolve correctly. | Repoint `[[generate-session-history]]` to `[[session-history]]` in `session-teach-back/SKILL.md` during a cross-link cleanup pass. | Low (broken cross-link reference; not a build gate; pre-existing) |
| WN-v33-2 | WN | adoption-loop-engineering Phase 1 | T1.5 (Testing and Stabilization) | The global bundle and quality audits pass with pre-existing warnings outside this phase: `demo-capture` has an orphan `.pyc` under its skill bundle, and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. The new `loop-engineering` bundle and quality checks are clean, and the new files are ASCII-clean. | Handle the pre-existing warnings in a dedicated cleanup pass; do not change unrelated files during this phase. | Low (warnings are unrelated to Phase 1 and do not fail the gate) |
| WN-v33-3 | WN | adoption-loop-engineering Phase 1 | T1.4 (Register the skill) | Machine-readable registries now agree at 252 skills (`data/skills.json` array/statistics and `data/marketplace.json` category sum), but headline prose count surfaces are intentionally not reconciled here per the plan: `data/SKILL_INDEX.md` Total label, `data/marketplace.json` plugin description, README, AGENTS.md, and similar release prose still reflect pre-Phase-1 counts. | Reconcile headline count prose during the develop-to-main release via `/update version` or `/update release`, not in this Phase 1 feature branch. | Low (machine-readable registries are consistent; prose reconciliation is release-owned) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| DF-v33-1 | DF | adoption-loop-engineering Phase 1 | Phase 4 (T4.1) | Added `catalog/skills/workflow/loop-engineering/SKILL.md` to `scripts/validate_skills.allowlist.json` without shortening the description. The strict `--allow-existing` pass now demotes the 496-char description to a warning for this file (warning count moved 1365 -> 1366), and the description is unchanged per the AGENTS.md pushy-description mandate. |
