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
| Cat 4 (active) | 21 |
| **Total in scope** | **21** |

All v3.19 artifacts remain active. Phases 1 through 4 of the agent-memory substrate plan added session-history files and kept the known-gaps ledger open for v3.19.1. The inventory found no binary, duplicate, empty-directory, or older-version artifact in scope. No file move, rename, archive, or deletion is proposed.

## Dispositions

| Artifact group | Cat | Count | Reason |
|---|---|---:|---|
| `plans/` | 4 | 3 | Current v3.19 work; v3.19.0 is shipped and the other two plans remain scheduled |
| `comparisons/` | 4 | 3 | Seed evidence for each queued plan |
| `research/` | 4 | 1 | Active input to the separate CI/CD research note |
| `development/history/` | 4 | 11 | Seven v3.19.0 histories plus four v3.19.1 phase write-ups |
| `known-gaps.md` | 4 | 1 | Reopened for v3.19.1; v3.19.0 subsection stays finalized |
| `docs-cleanup-report.md` | 4 | 1 | This audit artifact |

## Layout Observations

- The canonical `docs/v3/v3.19/` directory exists with `plans/` and `comparisons/`.
- Living policy files (`output-truncation-limits.md`, `memory-substrate-contract.md`, `memory-integration-prose.md`) sit under `docs/policy/` and are correctly outside this tree.
- No cleanup action is required before Phase 5.
