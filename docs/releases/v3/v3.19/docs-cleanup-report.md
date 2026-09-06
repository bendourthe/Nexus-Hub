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
| Cat 4 (active) | 31 |
| **Total in scope** | **31** |

All v3.19 artifacts remain active. v3.19.2 Phase 6 is complete. No file move, rename, archive, or deletion is proposed.

## Dispositions

| Artifact group | Cat | Count | Reason |
|---|---|---:|---|
| `plans/` | 4 | 3 | Current v3.19 work; v3.19.0 and v3.19.1 shipped, v3.19.2 in progress |
| `comparisons/` | 4 | 3 | Seed evidence for each queued plan |
| `research/` | 4 | 1 | Active input to the separate CI/CD research note |
| `development/history/` | 4 | 21 | Seven v3.19.0 histories, eight v3.19.1 write-ups, plus six v3.19.2 phase write-ups |
| `design/` | 4 | 1 | v3.19.2 signed-execution-contract study |
| `known-gaps.md` | 4 | 1 | v3.19.2 subsection (DF-1 through DF-4); v3.19.1 BG-1 remains until `/update release` regenerates `MANIFEST.sha256` |
| `docs-cleanup-report.md` | 4 | 1 | This audit artifact |

## Layout Observations

- The canonical `docs/v3/v3.19/` directory exists with `plans/` and `comparisons/`.
- `docs/v3/v3.19/design/` is the active-minor home for the B6 study (the plan cited `docs/v3/v3.18/design/`).
- No docs-tree migration is required before `/update release`.
