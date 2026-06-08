# Known Gaps -- v3.1.0 (adoption-claude-red)

**Status**: in progress (Phase 3 of 5 closed -- web AppSec methodology fold-in). Green for this phase: the catalog skill-security scanner gate is clean (0 HIGH/CRITICAL); a targeted scan of the two enriched skills + the new `references/web-appsec-methodology.md` is 5/100 LOW (0 HIGH / 0 CRITICAL / 0 MEDIUM, the single LOW a pre-existing Step-4 timing-attack prose line); the 87-test scanner package suite passes; JSON catalogs valid (250 skills, count unchanged -- Phase 3 enriches existing skills, it does not add); bundle audit PASS (`web-appsec-methodology.md` referenced); no-personal-paths / unicode-safety / supply-chain-IOCs / `check_version_sync.py` all green; both bodies within the 500-line norm (366 / 324).
**Last updated**: 2026-06-08 (Phase 3)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for the v3.1.0 `adoption-claude-red` plan (`docs/v3.1.0/plans/adoption-claude-red.md`). The next version's `/generate-plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

Note: v3.1.0 is worked on two parallel feature branches off `develop` (`feat/adoption-claude-red` and `feat/adoption-dynamic-workflows`), both version-scoped to v3.1.0. This file is the claude-red plan's gap log; the dynamic-workflows plan maintains its own gap log at the same path on its branch. The two will reconcile when both branches merge into `develop` (see WN-v31cr-3).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 4 | 0 |
| QG | 0 | 0 |
| **Total** | **4** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v31cr-1 | WN | Phase 1 (extended Phase 3) | T004 (validate the new skills); T007/T008 (enriched skills) | `scripts/validate_skills.py` run with no flags (its default mode) reports 150 description-length "errors" (description > 250 characters) across the catalog, including all four security skills this plan has touched: the Phase 1 new skills (`ai-attack-patterns`, `pentest-reporting`) and the Phase 3 enriched skills (`advanced-attack-patterns`, `business-logic-abuse`), whose pushy descriptions gained trigger phrases + a `SKIP:` clause. This is NOT a gate: `make validate` and the CI `validate` job run only `validate_skills.py --bundles-only` and `--quality` (both PASS on the new skills), never the bare default. The 250-char cap directly conflicts with the AGENTS.md mandatory pushy-description rule (which "trades 6 words for 60" with trigger phrases + a SKIP clause), and every shipped security skill already exceeds it (e.g. `skill-security-scan` at ~600 chars). The long descriptions are intentional and norm-consistent. | Do not shorten the pushy descriptions to chase the default-mode cap. If the divergence is undesirable, reconcile `validate_skills.py` default-mode behavior with the pushy-description rule (raise/remove the 250-char cap or scope it to a non-`description` field) so the script does not contradict the authoring contract. Out of scope for this plan. | Low (not a CI/`make validate` gate; by-design per the authoring contract) |
| WN-v31cr-2 | WN | Phase 1 | T004 (stabilization) | Local verification on the Windows dev host was partial: `make` is not on PATH, so `make validate` and `make scan` were emulated by invoking each validator and the scanner directly (all green: JSON catalogs, bundle audit, quality, no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security, solution-frontmatter, `check_version_sync.py`, and `scan_skill_security.py ... --fail-on high` all exit 0). `make lint` (ShellCheck) was not run -- this phase added only Markdown + JSON, so there is no shell surface. | Confirm the CI `validate` job is green for this commit on the ubuntu runner (it runs the same validators + the scanner gate); no code change expected. | Low (covered by CI; phase added no shell/Python surface) |
| WN-v31cr-3 | WN | Phase 1 | T003 / plan layout | Both v3.1.0 feature branches write `docs/v3.1.0/known-gaps.md`, so the file will conflict when `feat/adoption-claude-red` and `feat/adoption-dynamic-workflows` both merge into `develop`. IDs here are namespaced `-v31cr-` (claude-red) to avoid ID collisions on merge, but the file body itself still needs a manual merge. | At develop-integration, merge the two v3.1.0 gap logs into a single `docs/v3.1.0/known-gaps.md` (concatenate Open Items, recompute the Summary). The `-v31cr-` / dynamic-workflows ID namespacing keeps individual entries distinct. | Low (mechanical merge; IDs already namespaced) |
| WN-v31cr-4 | WN | Phase 2 | T006 (allowlist regression tests) | `tests/validators/test_scan_skill_security.py` carries a pre-existing unused `import pytest` (F401, present at HEAD line 16, not introduced by this phase). It was left untouched per the "every changed line traces to the request / no out-of-scope cleanup" rule, and the repo has no ruff hook in pre-commit or CI (lint gate is ShellCheck-only), so it is not a gate. Separately, the entire `nexus-skill-scanner` package is non-ruff-format-clean by convention (15 of 18 files would be reformatted); the new `allowlist.py` / `test_allowlist.py` match the established package style rather than introducing a lone ruff-formatted outlier. | If desired, remove the unused `import pytest` and adopt ruff format package-wide in a dedicated lint-hygiene change (add a ruff pre-commit hook + one reformat commit). Out of scope for this adoption plan. | Low (not a CI/`make` gate; consistent with the package's established style) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none) | -- | -- | -- | Phase 1 is the first phase of this plan; no prior open items to resolve. |
