# Known Gaps -- v3.2.0

**Status**: v3.2.0 `adoption-teach` in development on `feat/adoption-teach` (off `origin/develop`). Phases 1-2 of 3 complete (Phase 1: core `session-teach-back` skill + registration; Phase 2: teach-someone-else mode, eli5/eli14/intern depth levels, multiple-choice discipline, and an opt-in off-by-default checklist commit added to the same skill body). Catalog green at Phase 2: JSON catalogs valid (251 skills -- Phase 2 grows the existing skill, adds none), the skill-security scanner gate is clean (0 HIGH/CRITICAL, exit 0, no findings on `session-teach-back`), and `validate_skills.py --bundles-only` / `--quality` / no-personal-paths / unicode-safety / supply-chain / workflow-security / solution-frontmatter / `check_version_sync.py` all exit 0. The v3.2.0 version bump, CHANGELOG finalization, count-prose reconciliation, and tag are applied at the develop->main release (owned by `/update version` / `/update release`).
**Last updated**: 2026-06-08 (Phase 2)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.2.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 3 | 0 |
| QG | 0 | 0 |
| **Total** | **3** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v32-1 | WN | Phase 1 (grown in Phase 2) | T001 (write the core skill); T002 (register); T004 (teaching-mode trigger phrases) | `scripts/validate_skills.py` run with no flags (its default mode) reports a description-length error (description > 250 characters) for `session-teach-back` (923 chars after Phase 2's T004 added 2 more verbatim teaching-mode trigger phrases; 828 chars at Phase 1), whose pushy `description` carries 7 verbatim trigger phrases + a 3-way SKIP clause as the plan's T001/T004 mandate. This is NOT a gate: `make validate` and the CI `validate` job run only `validate_skills.py --bundles-only` and `--quality` (both PASS), never the bare default; the strict `--allow-existing` path demotes the violation to a warning for files in `scripts/validate_skills.allowlist.json`, to which `session-teach-back/SKILL.md` was added (mirroring its sibling `session-query` and the two most-recent skills, `skill-security-scan` and `agent-orchestration-primitives`). The 250-char cap directly conflicts with the AGENTS.md mandatory pushy-description rule and the plan's explicit T001 requirement. The long description is intentional and norm-consistent. (Same root class as v3.1.0 WN-v31cr-1; note that a few other catalog skills -- e.g. `ai-attack-patterns`, `pentest-reporting`, `git-branching-workflow` -- carry pushy descriptions not yet in the allowlist on `develop`, a separate pre-existing item, not introduced here.) | Do not shorten the pushy description to chase the default-mode cap. If the divergence is undesirable catalog-wide, reconcile `validate_skills.py` default-mode behavior with the pushy-description rule (raise/remove the 250-char cap or scope it to a non-`description` field). Out of scope for this plan. | Low (not a CI/`make validate` gate; by-design per the authoring contract) |
| WN-v32-2 | WN | Phase 1 (re-confirmed Phase 2) | T003, T007 (stabilization) | Local verification on the Windows dev host is partial: `make` is not on PATH, so `make validate` and `make scan` were emulated by invoking each validator and the scanner directly (all green at both Phase 1 and Phase 2). `make lint` (ShellCheck) was not run -- Phases 1 and 2 added only Markdown + JSON, so there is no shell surface. (Same root class as v3.1.0 WN-v31cr-2 / WN-v31-1.) | Confirm the CI `validate` + scanner jobs are green for this commit on the ubuntu runner (it runs the same validators + the scanner gate); no code change expected. | Low (covered by CI; phase added no shell/Python surface) |
| WN-v32-3 | WN | Phase 1 | T002 (register); T003 (consistency) | Count-prose surfaces on `develop` predate the v3.1.0 release-time count reconciliation: on `origin/develop` the `data/SKILL_INDEX.md` Total label read 248 while `data/skills.json` already had 250 entries (the v3.1.0 reconciliation to 250 was applied on the release/main side). Adding `session-teach-back` bumped the label by 1 (248 -> 249) and the true skills.json/marketplace count to 251, so the machine-readable registries agree at 251 but the SKILL_INDEX Total label and other headline-total prose surfaces (README, AGENTS.md, plugin description) still read pre-reconciliation values on `develop`. | Reconcile every count-prose surface to the truthful total (251 after Phase 1) at the v3.2.0 develop->main release bump via `/update version` -- exactly as the resolved v3.1.0 WN-v31-3 did at that release. No per-phase action needed; do not hand-reconcile on the feature branch. | Low (machine-readable registries already consistent at 251; prose reconciliation is the release bump's job) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | -- | -- | -- | Phase 1 is the first phase. |
