# Known Gaps -- v2.1.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.1.0/plans/adoption-spec-kit.md](plans/adoption-spec-kit.md)
**Status**: in-progress
**Last updated**: 2026-05-20 (Phase 7 close -- no new gaps, no resolved items; Phase 7 shipped the opt-in `--specs-layout` directory mode for `/generate-plan` plus the new `/tasks-to-issues` command and `tasks-to-issues` skill bundle, together with the two new repo-level helper scripts `scripts/new-feature.sh` and `scripts/new-feature.ps1` and their per-skill helper siblings under `catalog/skills/workflow/tasks-to-issues/scripts/tasks-to-issues.{sh,ps1}` and the `references/gh-cli-auth-runbook.md` one-page runbook. The `/generate-plan` command file gained a new Step 0d.1 documenting the opt-in `--specs-layout` flag (sequential or timestamp prefix resolution from `.specify/init-options.json`, `specs/<NNN>-<slug>/` directory creation, `.specify/feature.json` persistence, reserved-slug and collision rules) and a new Step 4 directory-layout subsection describing the three-file output (`spec.md` from the v2.1.0 spec template, `plan.md` with Constitution Check + Complexity Tracking intact, optional `tasks.md`); the default single-file behavior is unchanged when the flag is absent. The `/tasks-to-issues` command file documents the 4-step flow (pre-flight `gh auth status` + `gh repo view`, payload build with title cap at 200 chars / body block / labels `nexus-hub` + `spec-kit-task` + optional `parallel` + optional `user-story-N`, dry-run vs sequential execution with idempotency markers `[gh#<num>]` appended to source task lines after each successful filing, final summary table). Both helper scripts pass `bash -n` and `[System.Management.Automation.Language.Parser]::ParseFile` parser checks; `scripts/new-feature.sh` was smoke-tested end-to-end on a throwaway git repo (sequential mode, `specs/001-test-feature/` created, `.specify/feature.json` persisted with the correct relative path); `tasks-to-issues.sh --dry-run` was smoke-tested on a fixture and correctly aborted at the `gh` pre-flight check with the documented remediation message. The two new feature-directory bootstrap scripts are registered in BOTH `scripts/installer.sh` (3 references: source path declaration + `safe_copy` + `chmod +x`) and `scripts/installer.ps1` (2 references: source path declaration + `Safe-Copy`) per the Installer-Aware Changes rule in `AGENTS.md`; the per-skill `tasks-to-issues/scripts/` and `tasks-to-issues/references/` subdirectories are auto-copied by the recursive `safe_folder_copy` primitive and require no installer edit. Data registries updated atomically: `data/SKILL_INDEX.md` row added (total 206), `data/skills.json` array entry appended (count moves from 205 to 206), `data/marketplace.json` workflow category `skill_count` 22 -> 23. `python -c json` checks on all four data files pass; `scripts/validate_skills.py --path catalog/skills/workflow/tasks-to-issues` returns 0 errors / 5 optional-field warnings matching the pattern shipped by the Phase 1 and Phase 3 skills; `scripts/validate_skills.py --bundles-only` returns 0 errors / 0 warnings across 210 skill bundles. The 6 pre-existing false-positive secret-scan errors in `catalog/skills/{documentation/user-documentation,infrastructure/cd-pipeline-generator,infrastructure/rollback-strategy-advisor}/SKILL.md` are NOT a Phase 7 regression -- confirmed identical on the pre-Phase-7 tree via `git stash` round-trip. No DEVIATION markers, no test failures, no coverage shortfalls, no suppressed lint rules, no bypassed gates)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 0 | 0 |
| BG -- Bug or unresolved test failure | 0 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 1 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **1** | **0** |

## Open Items

### WN-1 -- `data/skills.json` statistics block is out of sync with the actual skills array

**Source phase**: Phase 1, sub-task 1.1 (data registries update).
**Plan reference**: [docs/v2.1.0/plans/adoption-spec-kit.md](plans/adoption-spec-kit.md) sub-task 1.1 ("add the new skill row to `data/SKILL_INDEX.md`, the skill entry to `data/skills.json`, and increment `data/marketplace.json` `total_skills` + category count").
**Reason**: After adding the `project-constitution` entry, `data/skills.json` `statistics.total_skills` reads `197` and `statistics.categories.workflow` reads `20`, but the actual skills array length is `205` and the SKILL_INDEX.md total reads `205` across `22` categories (Phase 3 added the `cross-artifact-analyzer` skill which compounded the gap by one more). The discrepancy is pre-existing - the `statistics` block had been stale since before v2.0.0 (it carried `196` when the array already held `203` skills). Phases 1 and 3 each applied the prescribed `+1` increment correctly; the underlying drift was not in scope to repair.
**Suggested next step**: Resolve during Phase 8 (v2.1.0 release stabilization) sub-task 8.1 step 5 ("Verify all three data registries are internally consistent"). Re-run `make build-catalog` once `infrastructure/tools/build_skills_catalog.py` is confirmed clean (v2.0.0 BG-001 closed it for the `Nexus-Hub` rename, so it should produce a faithful catalog now). Then re-baseline the `statistics.total_skills` and `statistics.categories.*` to match the array length and SKILL_INDEX.md total.

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 2 (per-phase append), swept by `/wrap-up-session` Phase 4 step 4b (catch-all from live conversation), and finalized by `/update-version` at the v2.1.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
