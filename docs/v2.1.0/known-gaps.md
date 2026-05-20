# Known Gaps -- v2.1.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.0.0/plans/adoption-spec-kit.md](../v2.0.0/plans/adoption-spec-kit.md)
**Status**: in-progress
**Last updated**: 2026-05-20 (Phase 2 close -- no new gaps, no resolved items; Phase 2 was a pure-additive template change to `catalog/commands/generate-plan.md` and `catalog/skills/workflow/implementation-plan/SKILL.md` introducing the Constitution Check + Complexity Tracking sections with no DEVIATION markers, no test failures, no suppressed lint rules, and no bypassed gates)

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
**Plan reference**: [docs/v2.0.0/plans/adoption-spec-kit.md](../v2.0.0/plans/adoption-spec-kit.md) sub-task 1.1 ("add the new skill row to `data/SKILL_INDEX.md`, the skill entry to `data/skills.json`, and increment `data/marketplace.json` `total_skills` + category count").
**Reason**: After adding the `project-constitution` entry, `data/skills.json` `statistics.total_skills` reads `197` and `statistics.categories.workflow` reads `20`, but the actual skills array length is `204` and the SKILL_INDEX.md total reads `204` across `22` categories. The discrepancy is pre-existing - the `statistics` block had been stale since before v2.0.0 (it carried `196` when the array already held `203` skills). Phase 1's edit applied the prescribed `+1` increment correctly; the underlying drift was not in scope to repair.
**Suggested next step**: Resolve during Phase 8 (v2.1.0 release stabilization) sub-task 8.1 step 5 ("Verify all three data registries are internally consistent"). Re-run `make build-catalog` once `infrastructure/tools/build_skills_catalog.py` is confirmed clean (v2.0.0 BG-001 closed it for the `Nexus-Hub` rename, so it should produce a faithful catalog now). Then re-baseline the `statistics.total_skills` and `statistics.categories.*` to match the array length and SKILL_INDEX.md total.

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 2 (per-phase append), swept by `/wrap-up-session` Phase 4 step 4b (catch-all from live conversation), and finalized by `/update-version` at the v2.1.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
