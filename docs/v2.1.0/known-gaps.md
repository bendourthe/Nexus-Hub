# Known Gaps -- v2.1.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.1.0/plans/adoption-spec-kit.md](plans/adoption-spec-kit.md)
**Status**: in-progress
**Last updated**: 2026-05-20 (Phase 6 close -- no new gaps, no resolved items; Phase 6 was a single-file additive update to `catalog/commands/generate-plan.md` enforcing the strict `- [ ] T### [P?] [US?] file_path` task-line format on every sub-task summary line, with the executable `**Prompt**:` block preserved intact underneath -- specifically a new `### Phase organization for user-story-driven plans` subsection in Step 3 codifying the Setup -> Foundational -> US1 -> US2 -> ... -> Polish phase shape (Setup / Foundational / Polish phases MUST omit story labels; user-story phases MUST carry the matching `[US#]` label), an updated File Format template in Step 4 showing the task line above the `**Objective**:` of each sub-task plus a new `### Task line format (required for every sub-task)` subsection with five-rule grammar, five concrete correct examples (T001 setup, T005 [P] foundational, T012 [P] [US1] story, T014 [US1] story-with-dependency, T042 polish), and seven anti-patterns that fail validation (missing hyphen-space, missing T prefix, ID under three digits, story label on Setup phase, missing required [US#] in user-story phase, reversed marker order, missing file path), and a new Step 5 `### Task Format Validation` block that runs the regex `^- \[ \] T[0-9]{3,}( \[P\])?( \[US[0-9]+\])? .+$` against every task line, verifies ID sequentiality / story-label scoping / marker order / path-token heuristic, emits the summary `Task format validation: <N> tasks total, <M> with [P] marker, <K> mapped to user stories. ALL tasks match the required format.`, fixes in-place with a hard cap of three repair iterations, and only then reports to the user; no DEVIATION markers, no test failures (validation surface is documentation, not Python), no coverage shortfalls, no suppressed lint rules, no bypassed gates; `python -c json` checks on all four data registries pass and `scripts/validate_skills.py --bundles-only` returns 0 errors / 0 warnings across 209 skill bundles)

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
