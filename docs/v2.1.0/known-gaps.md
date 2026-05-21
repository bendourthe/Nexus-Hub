# Known Gaps -- v2.1.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.1.0/plans/adoption-spec-kit.md](plans/adoption-spec-kit.md)
**Status**: ready-to-ship (v2.1.0 release stabilization complete)
**Last updated**: 2026-05-20 (Phase 8 close -- WN-1 resolved; 1 new BG resolved during the same phase; CHANGELOG.md `[2.1.0]` block authored; `docs/v2.1.0/RELEASE_NOTES.md` shipped; `data/marketplace.json` `plugin.version` bumped 2.0.0 -> 2.1.0 and `plugin.description` updated to "206+ curated skills"; `data/skills.json` statistics block rebaselined from `total_skills: 197` to `total_skills: 206` to match the actual array length, closing WN-1. A single upstream-attribution leak was identified during Phase 8.1 step 6 and resolved: the user-facing GitHub-issues label `spec-kit-task` (introduced by the Phase 7 prompt against the Reverse-Engineering Attribution Rule in `AGENTS.md` cross-cutting constraint #1) was renamed to `spec-driven-task` across the `/tasks-to-issues` command file, the `tasks-to-issues` SKILL.md, both helper scripts (POSIX + PowerShell), the `gh-cli-auth-runbook.md` reference, and the `data/skills.json` description / overview_l1 fields. All other matches for `spec-kit` in the catalog tree are internal path references to our own plan file `docs/v2.1.0/plans/adoption-spec-kit.md` and are acceptable per the rule. Full validation sweep passed: `python -m pytest catalog/hooks/tests/` 370 passed + 3 skipped; extension test suites unchanged (37 + 36 + 23 passed); `python scripts/validate_skills.py --bundles-only` 0 errors / 0 warnings across 210 skill bundles; 26/26 installer-smoke assertions green; `bash -n` clean on `scripts/installer.sh`, `scripts/new-feature.sh`, and `catalog/skills/workflow/tasks-to-issues/scripts/tasks-to-issues.sh`; PowerShell AST parse clean on `scripts/installer.ps1`, `scripts/new-feature.ps1`, and the PS1 helper sibling. Data-registry deltas all match the expected `previous_total + 3`: SKILL_INDEX.md 205 -> 208 rows, skills.json 203 -> 206 entries, marketplace.json 200 -> 203 category sum. Cross-OS smoke recorded in `docs/v2.1.0/installer-smoke-post.txt` with the Linux/macOS coverage carry-over from v1.1.5 DF-003 / DF-005 / DF-006 explicitly noted as out of scope for v2.1.0. `git tag v2.1.0` cut locally; push deferred per the CLAUDE.md destructive-git rule.)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 0 | 0 |
| BG -- Bug or unresolved test failure | 0 | 1 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 0 | 1 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **0** | **2** |

## Open Items

(none)

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-1 | `data/skills.json` statistics block out of sync with the actual skills array | Phase 8.1 | Rebaselined `statistics.total_skills` from `197` to `206` and `statistics.categories.*` to match the actual skills array. Per-category counts mirror the array categorization (kebab-case primary keys plus 3 historical Title-Case duplicates for `Developer Experience`, `Research`, `Workflow` carried over from before v2.0.0 -- left as-is because they are pre-existing data-quality artifacts unrelated to v2.1.0 scope and renaming them would break downstream consumers that already index by the legacy keys). |
| BG-1 | `spec-kit-task` GitHub-issues label leaks upstream attribution | Phase 8.1 step 6 | The Phase 7 prompt prescribed the label `spec-kit-task` for `/tasks-to-issues`, which violates the Reverse-Engineering Attribution Rule in `AGENTS.md` (cross-cutting constraint #1 of the plan also forbids `spec-kit` in user-facing artifacts). The label was renamed to `spec-driven-task` across the `/tasks-to-issues` command file, the `tasks-to-issues` SKILL.md (description + body + examples), both helper scripts (`tasks-to-issues.sh` + `tasks-to-issues.ps1`), the `gh-cli-auth-runbook.md` reference (including the `gh label create` recipe + the audit query), and the `data/skills.json` description / overview_l1 fields. Note: the historical plan file `docs/v2.1.0/plans/adoption-spec-kit.md` still mentions `spec-kit-task` in the Phase 7 prompt block -- left as-is because the plan is a frozen historical record. |

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 2 (per-phase append), swept by `/wrap-up-session` Phase 4 step 4b (catch-all from live conversation), and finalized by `/update-version` at the v2.1.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
