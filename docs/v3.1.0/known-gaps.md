# Known Gaps -- v3.1.0

**Status**: `adoption-dynamic-workflows` plan COMPLETE (all 3 phases / T001-T009 closed). v3.1.0 itself is still in progress at the version level -- the sibling `adoption-claude-red` sub-plan is not yet done, and the version bump/tag is deferred to release time (`/update version`) per the master roadmap. Catalog green: orphan-bundle audit 0 errors (1 pre-existing warning unrelated to these phases), all JSON catalogs valid, no-personal-paths / unicode-safety / supply-chain / workflow-security / solution-frontmatter / check_version_sync all exit 0; the skill-security scanner reports 0 findings (0 HIGH/CRITICAL) on the two edited orchestration skills.
**Last updated**: 2026-06-05 (Phase 3 / adoption-dynamic-workflows)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for the v3.1.0 `adoption-dynamic-workflows` plan. The next version's `/generate-plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

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
| WN-v31-1 | WN | Phase 1-3 | T003, T006, T009 (stabilization) | Local verification on the Windows dev host is partial: `make` is not on PATH, so `make validate` is emulated by invoking each validator directly (all green: orphan-bundle audit 0 errors with 1 pre-existing `demo-capture` `.pyc` warning unrelated to these phases, all four JSON catalogs valid, no-personal-paths / unicode-safety / supply-chain / workflow-security / solution-frontmatter / check_version_sync all exit 0). Phase 3 made markdown-only edits (three SKILL/reference files + CHANGELOG), so there is no `.js` bundle, no ShellCheck surface, and no new-code pytest surface; the skill-security scanner on the two edited orchestration skills is 0 findings, and the `tests/validators` suite (134 tests) passes. | Confirm the CI `validate` + scanner jobs are green for this commit on the ubuntu runner; no code change expected. | Low (covered by CI; matches the cross-version local-make pattern from WN-v30-4 / WN-v30-7) |
| WN-v31-2 | WN | Phase 3 | T008 | The `/loop` and `/goal` cross-reference added to `agent-orchestration-primitives/SKILL.md` was authored per the plan and the source comparison article. `/loop` is a confirmed Claude Code built-in; `/goal` could not be independently confirmed against this session's command surface (only `/loop` appeared). The reference frames both as platform commands the user invokes, not catalog artifacts Nexus-Hub ships, so an incorrect name would be a documentation-accuracy nit, not a broken artifact. | Before the v3.1.0 release, verify the exact `/goal` command name against the current Claude Code command set; correct the prose if the built-in is named differently. | Low (prose-only; no artifact depends on the command existing) |
| WN-v31-3 | WN | Phase 3 | T009 (validation) | Observed during Phase 3 `make validate`: `data/skills.json` reports 248 skills, while the v3.0.0 release prose (README, AGENTS.md, plugin.json, marketplace.json) states 247. This drift is pre-existing (Phase 3 added zero skills -- markdown edits only) and predates this plan. Reconciling catalog counts is an explicit v3.1.0 Version Definition-of-Done item, not this phase's scope. | At release, reconcile the skill count across `data/skills.json`, `data/marketplace.json`, README, AGENTS.md, and `.claude-plugin/plugin.json` (the `/update version` + count-reconciliation step in the roadmap DoD). | Low (release-time reconciliation; no functional impact) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none) | -- | -- | -- | No prior open items were resolvable this phase; WN-v31-1 remains open (CI-covered) and was broadened to Phase 1-3. |
