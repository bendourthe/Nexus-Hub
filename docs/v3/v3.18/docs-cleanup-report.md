# Docs Cleanup Report - Nexus-Hub - 2026-08-21

**Active version:** v3.18.0
**Mode:** audit
**Scope:** `docs/v3/v3.18/`, plus the repo-wide retention audit this version introduced

## Summary

| Category | Count |
|---|---|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 in scope; **216 files across 16 versions** archived repo-wide (executed) |
| Cat 3 (stale-flag) | 0 |
| Cat 4 (active) | 9 |
| **Total in scope** | **9** |

Every v3.18 artifact is active: the three plans (v3.18.0 docs-lifecycle-retention plus the queued v3.18.1 and v3.18.2), the four Phase 1-4 session histories, the known-gaps ledger opened by Phase 5, and this report. No archive or deletion action is proposed within `docs/v3/v3.18/`.

## Dispositions

| File | Cat | Reason |
|---|---|---|
| `plans/v3.18.0-docs-lifecycle-retention.md` | 4 | The plan being implemented; linked from the roadmap and every session history |
| `plans/v3.18.1-github-usage-monitor-accuracy.md` | 4 | Queued, unshipped; target version matches its directory |
| `plans/v3.18.3-presentify-slide-navigation.md` | 4 | Queued, unshipped; re-slotted from v3.18.2 on 2026-08-22 after that number was taken by the monitor withdrawal |
| `development/history/2026-08-21_...-phase-1-devlog-conversion-and-archive.md` | 4 | Current version's history; the DEVLOG index will link this directory at release |
| `development/history/2026-08-21_...-phase-2-tooling-rewrite.md` | 4 | As above |
| `development/history/2026-08-21_...-phase-3-agents-md-ratchet-down.md` | 4 | As above |
| `development/history/2026-08-21_...-phase-4-history-retention-policy.md` | 4 | As above |
| `known-gaps.md` | 4 | Opened by Phase 5; read forward by the next version's plan, and exempt from archival by the policy this version added |
| `docs-cleanup-report.md` | 4 | This file |

## New in this version: the repo-wide retention audit

v3.18.0 added `docs/policy/docs-retention.md` and `scripts/check_docs_retention.py`, which is the first mechanical answer this project has had to "which docs are no longer current". Its report:

```text
docs retention: 16 version(s) due for archival (current v3.17, threshold 2 minors)
  v3.0 (10)   v3.1 (8)    v3.2 (10)   v3.3 (4)    v3.4 (11)   v3.5 (3)
  v3.6 (5)    v3.7 (6)    v3.8 (1)    v3.9 (23)   v3.10 (6)   v3.11 (16)
  v3.12 (53)  v3.13 (30)  v3.14 (29)  v3.15 (91)
```

That first report counted 306 files across whole `development/` subtrees. The pass that followed moved **216** of them: only the `history/` subtrees, for the reason in the next paragraph. `plans/`, `comparisons/`, and `known-gaps.md` are exempt and stay in the active tree.

**Executed in Phase 5.** 216 files moved (the `history/` subtrees only, see below), one version at a time with a per-version file-count check, plus 75 files of inbound reference repair. The checker now reports nothing due.

**The pass narrowed the rule.** The policy as authored in Phase 4 archived a version's whole `development/` subtree. Building the inbound-reference index before moving anything (227 occurrences across 128 files) showed that some references were CI `run:` steps and shipped-code comments rather than documentation links:

| Content that stayed | Why |
|---|---|
| `docs/v3/v3.12/development/fixtures/`, `docs/v3/v3.13/development/fixtures/` | `.github/workflows/presentify-extractor.yml` **executes** six of these Python scripts |
| `docs/v3/v3.15/development/*.md` (11 contract docs) | Shipped hooks and tests cite them by path |
| `docs/v3/v3.9,v3.12,v3.13/development/worked-example/` | 68 non-Markdown files, referenced by the fixtures above |
| One-off design notes in v3.4, v3.7, v3.11 | Small, still referenced, not the growth problem |

Recorded as `DF-4` (resolved) in `docs/v3/v3.18/known-gaps.md`. A blanket rule would have broken CI and orphaned a shipped code citation.

**Reference repair, by artifact:**

| Repaired | Files |
|---|---|
| `docs/DEVLOG.md` (54 rows, the index built in Phase 1) | 1 |
| Session histories inside the moved trees (self-references) | ~60 |
| Plans, known-gaps, and the DEVLOG archive | ~14 |
| **Total** | **75** |

Nine `development/` directories became empty once their `history/` left and were removed. No empty directory remains in the tracked tree.

## Layout observations

- **No empty directories remain in the tracked tree.** Ten were removed in Phase 5: the nine `development/` directories emptied by the archive pass, plus `Microsoft/Windows/PowerShell`, created as a side effect of the installer and hook suites invoking `powershell.exe` with the repo as CWD. Git does not track empty directories, so that last one never appeared in `git status` while still being real enough to abort a `git stash -u`. It is now in `.gitignore` so a run that does leave a file there cannot commit it.
- **No duplicate or orphan documentation** was found in scope. The two files created by this version's relocations (`guides/reference/SKILL_BUNDLED_RESOURCES.md`, `docs/policy/model-routing-in-plan-and-implement.md`) are each linked from `AGENTS.md`, and `docs/policy/docs-retention.md` is linked from `AGENTS.md` plus three skills.
- **`docs/archive/DEVLOG-v0-v3.17.md`** is a new archive artifact at the `docs/archive/` root rather than under a version directory. That is deliberate: it spans v0.1.0 through v3.17.6 and belongs to no single version. It is linked from both `docs/DEVLOG.md` and `README.md`.
- **The remaining non-versioned subtrees** (`docs/policy/`, `docs/decisions/`, `docs/solutions/`, `docs/incidents/`, `docs/specs/`, `docs/git/`, `docs/security/`) are explicitly exempt from version-based archival by the new policy, so their growth is governed by their own lifecycles rather than left undefined.
