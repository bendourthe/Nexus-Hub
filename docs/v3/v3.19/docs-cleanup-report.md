# Docs Cleanup Report - Nexus-Hub - 2026-08-23

**Active version**: v3.19.1
**Mode**: audit
**Scope**: `docs/v3/v3.19/`

## Summary

| Category | Count |
|---|---:|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 |
| Cat 3 (stale-flag) | 0 |
| Cat 4 (active) | 18 |
| **Total in scope** | **18** |

All v3.19 artifacts remain active. Phase 1 of the agent-memory substrate plan added one session-history file and reopened the known-gaps ledger for v3.19.1. The inventory found no binary, duplicate, empty-directory, or older-version artifact in scope. No file move, rename, archive, or deletion is proposed.

## Dispositions

| Artifact group | Cat | Count | Reason |
|---|---:|---:|---|
| `plans/` | 4 | 3 | Current v3.19 work; v3.19.0 is shipped and the other two plans remain scheduled |
| `comparisons/` | 4 | 3 | Seed evidence for each queued plan |
| `research/` | 4 | 1 | Active input to the separate CI/CD research note |
| `development/history/` | 4 | 8 | Seven v3.19.0 histories plus this phase's output-safety write-up |
| `known-gaps.md` | 4 | 1 | Reopened for v3.19.1; v3.19.0 subsection stays finalized |
| `docs-cleanup-report.md` | 4 | 1 | This audit artifact |

## Layout Observations

- The canonical `docs/v3/v3.19/` directory exists with `plans/` and `comparisons/`.
- Phase 1 added only the expected history file and known-gaps subsection.
- The new policy file lives at `docs/policy/output-truncation-limits.md` (living policy, not a per-version artifact) and is correctly outside this tree.
