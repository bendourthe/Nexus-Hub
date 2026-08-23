# Docs Cleanup Report - Nexus-Hub - 2026-08-22

**Active version**: v3.19.0
**Mode**: audit
**Scope**: `docs/v3/v3.19/`

## Summary

| Category | Count |
|---|---:|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 |
| Cat 3 (stale-flag) | 0 |
| Cat 4 (active) | 16 |
| **Total in scope** | **16** |

All v3.19 artifacts are active: three queued plans, three supporting comparisons, one CI/CD research document, the Phase 1 through Phase 7 histories, the known-gaps ledger, and this report. The inventory found no binary, duplicate, empty-directory, or older-version artifact in scope. The reference graph found no inbound links from outside `docs/v3/v3.19/`; that is expected for an unreleased version and does not make its plans or implementation history orphaned.

## Dispositions

| Artifact group | Cat | Count | Reason |
|---|---:|---:|---|
| `plans/` | 4 | 3 | Current v3.19 work; all seven code-intelligence phases are implemented and the other plans remain scheduled |
| `comparisons/` | 4 | 3 | Seed evidence for each queued plan |
| `research/` | 4 | 1 | Active input to the separate v3.19.0 CI/CD plan |
| `development/history/` | 4 | 7 | Current phase implementation evidence |
| `known-gaps.md` | 4 | 1 | Finalized code-intelligence gap and policy-audit ledger; reusable by the remaining v3.19 plans |
| `docs-cleanup-report.md` | 4 | 1 | This audit artifact |

## Layout Observations

- The canonical `docs/v3/v3.19/` directory exists with `plans/` and `comparisons/`.
- Phases 1 through 7 add only the expected `development/history/`, `known-gaps.md`, and audit report artifacts.
- No file move, rename, archive, or deletion is proposed.

## Release Retention Pass

The v3.19.0 version bump made `docs/v3/v3.17/development/history/` two minors behind the current release. The release pass copied all 27 files to `docs/archive/v3/v3.17/development/history/`, verified SHA-256 equality by filename, removed the original subtree only after the sets matched, and repaired live and intra-history references. No documentation was deleted.
