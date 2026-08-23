# Docs Cleanup Report - Nexus-Hub - 2026-08-23

**Active version**: v3.19.2
**Mode**: audit
**Scope**: `docs/v3/v3.19/`

## Summary

| Category | Count |
|---|---:|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 |
| Cat 3 (stale-flag) | 0 |
| Cat 4 (active) | 26 |
| **Total in scope** | **26** |

All v3.19 artifacts remain active. v3.19.2 Phase 2 is in progress. No file move, rename, archive, or deletion is proposed.

## Dispositions

| Artifact group | Cat | Count | Reason |
|---|---|---:|---|
| `plans/` | 4 | 3 | Current v3.19 work; v3.19.0 and v3.19.1 shipped, v3.19.2 in progress |
| `comparisons/` | 4 | 3 | Seed evidence for each queued plan |
| `research/` | 4 | 1 | Active input to the separate CI/CD research note |
| `development/history/` | 4 | 17 | Seven v3.19.0 histories, eight v3.19.1 write-ups, plus two v3.19.2 phase write-ups |
| `known-gaps.md` | 4 | 1 | v3.19.2 subsection updated (DF-1, DF-2); v3.19.1 BG-1 remains until the next patch |
| `docs-cleanup-report.md` | 4 | 1 | This audit artifact |

## Layout Observations

- The canonical `docs/v3/v3.19/` directory exists with `plans/` and `comparisons/`.
- No docs-tree migration is required before `/update release`.
