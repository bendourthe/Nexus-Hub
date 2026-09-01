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

## Phase 7 - Final Architecture and Evidence-Retention Audit

### Scope and mode

The final scan covered the committed repository tree and the active `docs/releases/v4/v4.4/` release tree in audit-only mode. No file or directory was moved or deleted. Pre-existing untracked future-version work and concurrent user-owned edits were excluded from the v4.4.0 change set.

### Repository architecture scan

| Check | Observed result | Disposition |
|---|---|---|
| Tracked files | 3,708 | Existing root layout retained. |
| Empty tracked directories | 0 | No cleanup action. |
| Duplicate content | 8 sets across 30 files | Retained: empty package markers, platform base templates, shared extension sources/configuration, paired reference fixtures, icons, and licenses are intentional parity or test assets. |
| Obsolete-name candidates | 5 | Retained: the cross-platform `old-version-docs-guard` pair, the active `deprecated-api-updater` skill and agent declaration, and the explicit legacy deprecation notice are named compatibility surfaces rather than abandoned files. |
| v4.4 release files | 84 files, 24,001,901 bytes | Committed active Cat 4 release evidence at the start of Phase 7, excluding untracked future-release work; no archive move before release close. |
| v4.4 duplicate sets | 0 | No redundant v4.4 artifact found. |
| Documentation reference graph | 108 referenced paths and 452 inbound references | No move or deletion was approved, so no reference repair was required. |
| Lifespan contradictions | 263 historical findings repository-wide; 0 in v4.2, v4.3, or v4.4 | Historical findings remain report-only; no active v4.4 record was auto-moved. |

### Render-evidence retention

| Set | Files | Bytes | Disposition |
|---|---:|---:|---|
| Phase 1 | 8 | 1,701,447 | Retain as the Home phase's cited browser evidence. |
| Phase 2 | 8 | 2,976,497 | Retain as the first Foundations phase's cited browser evidence. |
| Phase 3 | 8 | 4,330,823 | Retain as the second Foundations phase's cited browser evidence. |
| Phase 4 | 8 | 1,130,518 | Retain as the initial playable-game phase's cited browser evidence. |
| Phase 5 | 8 | 1,199,992 | Retain as the end-to-end Training-loop phase's cited browser evidence. |
| Phase 6 | 32 | 12,449,986 | Retain as the final four-route, two-theme, four-width sweep. |
| **Total** | **72** | **23,789,263** | **Retained; no screenshot deletion was authorized.** |

The v4.2.3 precedent kept the final sweep and unique states while pruning superseded standard sweeps only after an explicit decision. This run did not receive the separate destructive-action approval required to remove the Phase 1 through Phase 5 sets, so all 72 captures remain in the active tree. Every file is still available at its cited path, and the final Phase 6 matrix remains the release-wide rendered baseline.

### Result

The v4.4 split is coherent: the self-contained guide stays in its living product path, release-bound plans, histories, measurements, and captures stay under `docs/releases/v4/v4.4/`, and no committed artifact is orphaned or duplicated. The final audit proposes no architecture mutation and self-classifies this report as Cat 4 while v4.4.0 remains active.
