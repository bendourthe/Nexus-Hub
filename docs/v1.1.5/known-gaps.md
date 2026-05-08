# Known Gaps -- v1.1.5

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v1.1.5/plans/adoption-skills.md](plans/adoption-skills.md)
**Last updated**: 2026-05-08 (Phase 1 complete)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 1 | 0 |
| BG -- Bug or unresolved test failure | 0 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 0 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **1** | **0** |

## Open Items

### DF-001 -- `create-skill-or-command` skill does not exist in catalog

**Source phase**: Phase 1, sub-task 1.1 (A14 -- pushy-description guidance).
**Plan reference**: [docs/v1.1.5/plans/adoption-skills.md](plans/adoption-skills.md) lines 42-49 (sub-task 1.1).
**Reason**: The sub-task prompt directed the agent to "Read `catalog/skills/workflow/create-skill-or-command/SKILL.md` and `catalog/skills/workflow/create-custom-command/SKILL.md`. In each, add a new section..." Only `create-custom-command/SKILL.md` exists in the catalog; the `create-skill-or-command` skill referenced in the plan does not exist as a tracked file (`Glob` for `catalog/skills/**/create-skill*/SKILL.md` returned no results). The skill name does appear in the global skill list surfaced by the harness, but that is an external skill (likely a Claude Code built-in or a separately-installed skill), not a DevAI-Hub catalog entry. The de facto skill-authoring guide for DevAI-Hub authors is `AGENTS.md` "Adding a New Skill -> Write SKILL.md", not a dedicated catalog skill.
**Resolution applied in Phase 1**: A14 was applied to (a) `catalog/skills/workflow/create-custom-command/SKILL.md` (the existing skill, which covers commands; commands also have descriptions and the same under-triggering risk applies) and (b) `AGENTS.md` "Adding a New Skill -> Write SKILL.md" (the actual skill-authoring guide for DevAI-Hub). Both insertions carry the same pushy-description rules, the same before / after example (adapted to commands vs. skills), and a cross-link between them. Original A14 intent met.
**Suggested next step**: Decide whether `create-skill-or-command` should exist as a dedicated catalog skill. Options: (a) leave the responsibility in AGENTS.md (current state -- skill-authoring guidance is project-level, not a catalog skill); (b) extract the AGENTS.md "Adding a New Skill" section into a new `catalog/skills/workflow/create-skill/SKILL.md` so skill authors get the same trigger surface as command authors; (c) rename `create-custom-command` to `create-command-or-skill` and broaden its scope. Recommend option (a) -- AGENTS.md is the canonical authoring guide and a catalog skill that duplicates it would drift. If revisited, it becomes a future plan item, not a v1.1.5 phase.

## Resolved

(none this version yet)
