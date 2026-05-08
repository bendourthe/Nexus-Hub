# Known Gaps -- v1.1.5

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v1.1.5/plans/adoption-skills.md](plans/adoption-skills.md)
**Last updated**: 2026-05-08 (Phase 2 complete)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 3 | 0 |
| BG -- Bug or unresolved test failure | 0 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 0 | 0 |
| QG -- Quality gate bypassed | 1 | 0 |
| **Total** | **4** | **0** |

## Open Items

### DF-001 -- `create-skill-or-command` skill does not exist in catalog

**Source phase**: Phase 1, sub-task 1.1 (A14 -- pushy-description guidance).
**Plan reference**: [docs/v1.1.5/plans/adoption-skills.md](plans/adoption-skills.md) lines 42-49 (sub-task 1.1).
**Reason**: The sub-task prompt directed the agent to "Read `catalog/skills/workflow/create-skill-or-command/SKILL.md` and `catalog/skills/workflow/create-custom-command/SKILL.md`. In each, add a new section..." Only `create-custom-command/SKILL.md` exists in the catalog; the `create-skill-or-command` skill referenced in the plan does not exist as a tracked file (`Glob` for `catalog/skills/**/create-skill*/SKILL.md` returned no results). The skill name does appear in the global skill list surfaced by the harness, but that is an external skill (likely a Claude Code built-in or a separately-installed skill), not a DevAI-Hub catalog entry. The de facto skill-authoring guide for DevAI-Hub authors is `AGENTS.md` "Adding a New Skill -> Write SKILL.md", not a dedicated catalog skill.
**Resolution applied in Phase 1**: A14 was applied to (a) `catalog/skills/workflow/create-custom-command/SKILL.md` (the existing skill, which covers commands; commands also have descriptions and the same under-triggering risk applies) and (b) `AGENTS.md` "Adding a New Skill -> Write SKILL.md" (the actual skill-authoring guide for DevAI-Hub). Both insertions carry the same pushy-description rules, the same before / after example (adapted to commands vs. skills), and a cross-link between them. Original A14 intent met.
**Suggested next step**: Decide whether `create-skill-or-command` should exist as a dedicated catalog skill. Options: (a) leave the responsibility in AGENTS.md (current state -- skill-authoring guidance is project-level, not a catalog skill); (b) extract the AGENTS.md "Adding a New Skill" section into a new `catalog/skills/workflow/create-skill/SKILL.md` so skill authors get the same trigger surface as command authors; (c) rename `create-custom-command` to `create-command-or-skill` and broaden its scope. Recommend option (a) -- AGENTS.md is the canonical authoring guide and a catalog skill that duplicates it would drift. If revisited, it becomes a future plan item, not a v1.1.5 phase.

### DF-002 -- A4 starting state in plan does not match repo state

**Source phase**: Phase 2, sub-task 2.1 (A4 -- claude-api restore-or-delist decision).
**Plan reference**: [docs/v1.1.5/plans/adoption-skills.md](plans/adoption-skills.md) lines 121-134 (sub-task 2.1).
**Reason**: The plan (and the source comparison report at `docs/v1.1.5/comparison-skills.md` Section 5a A4) described the starting state as: the `claude-api` row exists in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`, but the file `catalog/skills/ai-development/claude-api/SKILL.md` does not exist. The plan therefore asked the agent to choose between four options: (A) restore from upstream, (B) restore from prior history, (C) de-list, (D) user-supplied content. At Phase 2 start, the actual repo state was that the `claude-api` row was already absent from all three `data/` files (verified via `grep claude-api data/`, zero matches). The de-list path appears to have been executed between the comparison report being written and Phase 2 starting; no record of when. So sub-task 2.1 was a no-op verification rather than an edit, and the user-facing question in the plan (A/B/C/D) was not surfaced.
**Resolution applied in Phase 2**: Verified zero matches for `claude-api` in `data/` (consistent state -- no row, no file). Documented in the Phase 2 CHANGELOG `### Removed` section. Committed registry updates for `doc-coauthoring` only.
**Suggested next step**: If a future plan wants to actually adopt the upstream `claude-api` skill (which has substantive language-specific content under `csharp/`, `python/`, etc. in the upstream `anthropics/skills/claude-api/`), it should be a fresh net-new skill addition (option A path), with frontmatter and body authored to DevAI-Hub conventions. Not in scope for v1.1.5.

### DF-003 -- macOS / Linux installer dry-run deferred

**Source phase**: Phase 2, sub-task 2.3 (cross-platform installer verification).
**Plan reference**: [docs/v1.1.5/plans/adoption-skills.md](plans/adoption-skills.md) lines 148-153 (sub-task 2.3) and the cross-cutting constraint at lines 535-543.
**Reason**: Verification was performed on Windows + Git Bash (the work-environment constraint -- the user runs Windows 11 with PowerShell as the primary shell). Both installers were confirmed to use recursive-copy primitives (`rsync -a --delete` / `cp -R "$source/"*` for `installer.sh`; `robocopy ... /MIR` for `installer.ps1`) that auto-distribute new skill files without an installer edit. `bash -n` syntax check passed; ShellCheck warnings clean. Actual `bash scripts/installer.sh` execution on a real macOS or Linux host was not run.
**Suggested next step**: Defer the cross-OS smoke run to either (a) a CI matrix step (Linux runner + macOS runner each performing a `bash scripts/installer.sh --dry-run` if `--dry-run` is added in Phase 3, since 3.3's PowerShell counterpart already mentions adding such a flag if missing) or (b) a periodic "release-readiness" smoke task before any v1.x.x version bump. Phase 3's A13 work explicitly adds dry-run capability, after which this gap can be closed by running the dry-run on at least one Unix host.

### QG-001 -- Cross-OS verification gate ran on one OS only

**Source phase**: Phase 2, Stability Gate.
**Plan reference**: [docs/v1.1.5/plans/adoption-skills.md](plans/adoption-skills.md) lines 113-117 (Phase 2 Stability Gate clause "installer dry-run on at least one OS includes the new skill in the recursive copy").
**Reason**: The Phase 2 Stability Gate explicitly says "at least one OS", and Windows + Git Bash satisfies that minimum. However, the cross-cutting constraint at the top of the plan asks for cross-OS parity verification at minimum once per phase that adds bundled scripts. Phase 2 does not add bundled scripts (the new skill is a single SKILL.md file), so the cross-cutting constraint is satisfied by the recursive-copy primitive analysis. Recording this as QG rather than DF because the user opted to proceed under the minimum gate language rather than reach for the cross-OS coverage now.
**Suggested next step**: Same as DF-003. The cross-OS smoke run for v1.1.5 cumulative state should happen before the v1.1.5 → v1.2.0 version bump, not as a Phase 2 blocker.

## Resolved

(none this version yet)
