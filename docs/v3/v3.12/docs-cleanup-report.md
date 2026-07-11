# Docs Cleanup Audit - v3.12 (Phase 1)

**Mode**: audit (no files moved)
**Date**: 2026-07-11

## Findings

- `docs/v3/v3.12/` follows the canonical `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` layout: `plans/` (1 plan), `development/fixtures/` (fixture kit), `known-gaps.md`, this report.
- The fixture kit (`development/fixtures/`) is intentional committed evidence following the v3.9 `worked-example/` precedent: generator + verifier scripts + README committed; generated binaries (`inputs/`, `models/`) gitignored via the kit's own `.gitignore`.
- No deprecated files, empty directories, redundant files, or misplaced version content detected in the v3.12 subtree at this phase.

## Actions

- None required. Scratch docs created this phase are all intentional evidence; nothing proposed for cleanup.
