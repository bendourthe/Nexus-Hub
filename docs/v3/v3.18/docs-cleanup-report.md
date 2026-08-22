# Docs Cleanup Report - Nexus-Hub - 2026-08-21

**Active version:** v3.18.0
**Mode:** audit
**Scope:** `docs/v3/v3.18/`, plus the repo-wide retention audit this version introduced

## Summary

| Category | Count |
|---|---|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 in scope; **306 files across 16 versions** flagged repo-wide, deferred |
| Cat 3 (stale-flag) | 0 |
| Cat 4 (active) | 9 |
| **Total in scope** | **9** |

Every v3.18 artifact is active: the three plans (v3.18.0 docs-lifecycle-retention plus the queued v3.18.1 and v3.18.2), the four Phase 1-4 session histories, the known-gaps ledger opened by Phase 5, and this report. No archive or deletion action is proposed within `docs/v3/v3.18/`.

## Dispositions

| File | Cat | Reason |
|---|---|---|
| `plans/v3.18.0-docs-lifecycle-retention.md` | 4 | The plan being implemented; linked from the roadmap and every session history |
| `plans/v3.18.1-github-usage-monitor-accuracy.md` | 4 | Queued, unshipped; target version matches its directory |
| `plans/v3.18.2-presentify-slide-navigation.md` | 4 | Queued, unshipped; target version matches its directory |
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

306 files, all `development/` subtrees, destined for `docs/archive/v3/v3.<MINOR>/development/`. `plans/`, `comparisons/`, and `known-gaps.md` are exempt and stay in the active tree.

**Deferred, not skipped.** Recorded as `MT-1` in `docs/v3/v3.18/known-gaps.md`. Three reasons:

1. It is a 306-file move requiring reference repair across plans, the DEVLOG index, known-gaps files, and the CHANGELOG. The policy specifies propose-then-apply through `[[docs-layout-refactor]]`, which is a reviewed pass, not a step inside another phase.
2. This working copy is on a OneDrive-synced drive where a partially-completed git operation has already corrupted a release tag (v3.17.5) and aborted a `git stash -u` during this plan's own Phase 1. A 306-file move is precisely the operation that hazard punishes.
3. Nothing is broken while it waits. The retention rule is advisory by design, and the backlog is the one-time cost of having had no rule until now, not a regression introduced here.

## Layout observations

- **No empty directories remain in the tracked tree.** One was removed in Phase 5: `Microsoft/Windows/PowerShell`, created as a side effect of the installer and hook suites invoking `powershell.exe` with the repo as CWD. Git does not track empty directories, so it never appeared in `git status` while still being real enough to abort a `git stash -u`. It is now in `.gitignore` so a run that does leave a file there cannot commit it.
- **No duplicate or orphan documentation** was found in scope. The two files created by this version's relocations (`guides/reference/SKILL_BUNDLED_RESOURCES.md`, `docs/policy/model-routing-in-plan-and-implement.md`) are each linked from `AGENTS.md`, and `docs/policy/docs-retention.md` is linked from `AGENTS.md` plus three skills.
- **`docs/archive/DEVLOG-v0-v3.17.md`** is a new archive artifact at the `docs/archive/` root rather than under a version directory. That is deliberate: it spans v0.1.0 through v3.17.6 and belongs to no single version. It is linked from both `docs/DEVLOG.md` and `README.md`.
- **The remaining non-versioned subtrees** (`docs/policy/`, `docs/decisions/`, `docs/solutions/`, `docs/incidents/`, `docs/specs/`, `docs/git/`, `docs/security/`) are explicitly exempt from version-based archival by the new policy, so their growth is governed by their own lifecycles rather than left undefined.
