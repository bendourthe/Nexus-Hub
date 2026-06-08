# Known Gaps -- v3.1.0 (adoption-claude-red)

**Status**: in progress (Phase 1 of 5 closed -- low-collision skill-native ships). Catalog green for this phase: JSON catalogs valid (250 skills), bundle audit PASS (0 errors, 1 pre-existing warning), quality 0/0 on the two new skills, all v2.3.0 CI validators + `check_version_sync.py` exit 0, and the skill-security scanner gate is clean (0 HIGH/CRITICAL; the two new skills score LOW, max severity MEDIUM).
**Last updated**: 2026-06-08 (Phase 1)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for the v3.1.0 `adoption-claude-red` plan (`docs/v3.1.0/plans/adoption-claude-red.md`). The next version's `/generate-plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

Note: v3.1.0 is worked on two parallel feature branches off `develop` (`feat/adoption-claude-red` and `feat/adoption-dynamic-workflows`), both version-scoped to v3.1.0. This file is the claude-red plan's gap log; the dynamic-workflows plan maintains its own gap log at the same path on its branch. The two will reconcile when both branches merge into `develop` (see WN-v31cr-3).

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
| WN-v31cr-1 | WN | Phase 1 | T004 (validate the new skills) | `scripts/validate_skills.py` run with no flags (its default mode) reports 150 description-length "errors" (description > 250 characters) across the catalog, including both new skills (`ai-attack-patterns`, `pentest-reporting`). This is NOT a gate: `make validate` and the CI `validate` job run only `validate_skills.py --bundles-only` and `--quality` (both PASS on the new skills), never the bare default. The 250-char cap directly conflicts with the AGENTS.md mandatory pushy-description rule (which "trades 6 words for 60" with trigger phrases + a SKIP clause), and every shipped security skill already exceeds it (e.g. `skill-security-scan` at ~600 chars). The long descriptions are intentional and norm-consistent. | Do not shorten the pushy descriptions to chase the default-mode cap. If the divergence is undesirable, reconcile `validate_skills.py` default-mode behavior with the pushy-description rule (raise/remove the 250-char cap or scope it to a non-`description` field) so the script does not contradict the authoring contract. Out of scope for this plan. | Low (not a CI/`make validate` gate; by-design per the authoring contract) |
| WN-v31cr-2 | WN | Phase 1 | T004 (stabilization) | Local verification on the Windows dev host was partial: `make` is not on PATH, so `make validate` and `make scan` were emulated by invoking each validator and the scanner directly (all green: JSON catalogs, bundle audit, quality, no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security, solution-frontmatter, `check_version_sync.py`, and `scan_skill_security.py ... --fail-on high` all exit 0). `make lint` (ShellCheck) was not run -- this phase added only Markdown + JSON, so there is no shell surface. | Confirm the CI `validate` job is green for this commit on the ubuntu runner (it runs the same validators + the scanner gate); no code change expected. | Low (covered by CI; phase added no shell/Python surface) |
| WN-v31cr-3 | WN | Phase 1 | T003 / plan layout | Both v3.1.0 feature branches write `docs/v3.1.0/known-gaps.md`, so the file will conflict when `feat/adoption-claude-red` and `feat/adoption-dynamic-workflows` both merge into `develop`. IDs here are namespaced `-v31cr-` (claude-red) to avoid ID collisions on merge, but the file body itself still needs a manual merge. | At develop-integration, merge the two v3.1.0 gap logs into a single `docs/v3.1.0/known-gaps.md` (concatenate Open Items, recompute the Summary). The `-v31cr-` / dynamic-workflows ID namespacing keeps individual entries distinct. | Low (mechanical merge; IDs already namespaced) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none) | -- | -- | -- | Phase 1 is the first phase of this plan; no prior open items to resolve. |
