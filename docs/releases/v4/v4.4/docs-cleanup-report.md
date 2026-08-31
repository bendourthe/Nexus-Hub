# Docs Cleanup Audit - v4.4.0 Guide Depth and Training Rebuild

**Date**: 2026-08-31
**Mode**: audit only; no files moved
**Plan**: `docs/releases/v4/v4.4/plans/v4.4.0-guide-depth-and-training-rebuild.md`

## Phase 1 - Home Identity, Platforms, Installation, and Comparison

### Layout check

Phase 1 keeps all version-bound planning, gap tracking, render evidence, and history inside the canonical `docs/releases/v4/v4.4/` tree. The guide remains in its living product location at `guides/website/nexus-hub-guide.html`, and `docs/todos.md` remains the living progress dashboard. `docs/DEVLOG.md` remains unchanged because v4.4.0 is not yet released.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/releases/v4/v4.4/plans/v4.4.0-guide-depth-and-training-rebuild.md` | Active plan | Keep and advance transactionally with each phase. |
| `docs/releases/v4/v4.4/known-gaps.md` | Active release gap ledger | Keep in the active release tree for reconciliation and next-plan ingestion. |
| `docs/releases/v4/v4.4/docs-cleanup-report.md` | Active release audit record | Keep and append each later phase audit. |
| `docs/releases/v4/v4.4/development/history/2026-08-31_v4.4.0-guide-depth-and-training-rebuild-phase-1-home.md` | Active phase evidence | Keep in the v4.4 development history through release closure. |
| `docs/releases/v4/v4.4/development/guide-rebuild/renders/phase-1/` | Automated visual evidence | Keep under the release development tree pending the Phase 7 retention decision. |

### Audit evidence

Command: `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root ./docs/releases/v4/v4.4` plus `refgraph` against the same root.

Result: `docs-audit: files=12; duplicate-sets=0; refgraph-paths=2; active-tree=Cat4; moves=0`.

### Result

No documentation move or deletion is proposed. Phase 1 introduced no living-document duplication, no release evidence outside the active v4.4 tree, and no reason to add an unreleased line to the bounded development index.

## Phase 2 - Foundations Structure, Model, Tokens, and Prompts

### Layout check

Phase 2 keeps implementation history and browser evidence in `docs/releases/v4/v4.4/development/`, while the guide and functional-verification skill remain in their living product locations. The active plan, release gap ledger, and `docs/todos.md` advance in place. `docs/DEVLOG.md` remains unchanged because v4.4.0 is not yet released.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/releases/v4/v4.4/development/history/2026-08-31_v4.4.0-guide-depth-and-training-rebuild-phase-2-foundations-part-1.md` | Active phase evidence | Keep in the v4.4 development history through release closure. |
| `docs/releases/v4/v4.4/development/guide-rebuild/renders/phase-2/` | Automated visual evidence | Keep under the release development tree pending the Phase 7 retention decision. |

### Audit evidence

Command: `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root ./docs/releases/v4/v4.4 --repo-root .` plus `refgraph` against the same root.

Result: `docs-audit: files=21; duplicate-sets=0; refgraph-paths=2; active-tree=Cat4; moves=0`.

### Result

No documentation move or deletion is proposed. Phase 2 introduces no duplicate living documentation, no evidence outside the active v4.4 tree, and no unreleased entry in the bounded development index.
