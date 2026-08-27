# Docs Cleanup Audit - v4.0.0 Docs Lifespan Tree and Enforcement

**Date**: 2026-08-26
**Mode**: audit only; no files moved
**Plan**: `docs/v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md`

## Phase 1 - Enforcement mechanisms

### Layout check

The current two-level `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` layout remains canonical until Phase 3 changes the prescription and Phase 6 migrates this repository. `check_doc_colocation.py`, `check_docs_conventions.py`, and `check_docs_retention.py` passed in the full profile. No cleanup move is approved or needed in this phase.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `catalog/skills/code-cleanup/docs-layout-refactor/references/link-integrity.md` | Tier-3 skill reference | Keep; required by the Phase 1 repair contract and referenced from `SKILL.md`. |
| `docs/v4/v4.0/development/history/2026-08-26_v4.0.0-docs-lifespan-phase-1-enforcement-mechanisms.md` | Active phase evidence | Keep under the current version's development history. |
| `docs/v4/v4.0/docs-cleanup-report.md` | Active audit record | Keep and append later phase audits until release close. |

### Result

No duplicate, orphaned, stale, or misplaced documentation was created. The bundled-resource validator reported 0 errors and confirmed that the new script and reference files are linked from the owning skill.

## Phase 2 - Lifespan axis

### Admission and contradiction artifacts

| Path | Category | Disposition |
|---|---|---|
| `catalog/skills/code-cleanup/docs-layout-refactor/evals/trigger-cases.json` | Generated routing fixture input | Keep with the owning skill; catalog routing consumes it directly. |
| `tests/skills/test_docs_lifespan.py` | Durable regression test | Keep; it proves unknown-name admission, release-tag chronology, single-source rule ownership, and the Tier-2 size target. |
| `docs/v4/v4.0/development/history/2026-08-26_v4.0.0-docs-lifespan-phase-2-lifespan-axis.md` | Active phase evidence | Keep under the current version's development history. |

### Result

The admission test classifies an unrecognized living subtree without adding its name to policy. Signal 9's algorithm exists once in `references/link-integrity.md`; both consuming skills link to it. The `docs-layout-refactor` body is 474 lines, below the 500-line target and 800-line hard cap. No files moved and no new cleanup finding was created.

## Phase 3 - Breaking rename of the prescription

### Canonical and legacy layout artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/decisions/implemented/tooling/2026-08-20-docs-tree-organised-by-lifespan.md` | Cross-release decision record, promoted to implemented at the v4.0.0 release | Keep outside release-scoped documentation; the decision remains relevant after v4.0 closes. |
| `catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py` | Canonicalization and inventory helper | Keep; it recognizes releases, v-bucket, flat, and versions layouts and emits the exact layout per record. |
| `tests/skills/test_docs_lifespan_phase3.py` | Durable migration contract | Keep; it guards the decision, canonical paths, generated registry, and intentional-legacy labeling rule. |
| `catalog/skills/*/*/evals/trigger-cases.json` for the 15 newly covered consumers | Generated routing fixture inputs | Keep with their owning skills; the whole-catalog runner consumes them directly. |

### Result

The canonical prescription is now `docs/releases/` plus `docs/archives/`, while every previous shape remains an explicit legacy input. The migration fixture moved `docs/v3/v3.17/` to `docs/releases/v3/v3.17/` and the Phase 1 link diff reported zero newly broken links. No repository documentation was physically moved in this phase; dogfood migration remains Phase 6. The task-converter shell helper named by the plan is absent from the live catalog, so there was no file to edit; its owning SKILL.md and registry surfaces were updated and tested.

## Phase 4 - Executable guards and anti-regression tests

### Guard and enforcement artifacts

| Path | Category | Disposition |
|---|---|---|
| `catalog/hooks/old-version-docs-guard.sh` and `.ps1` | Cross-platform historical-doc guard | Keep as a shipped hook pair; both recognize the canonical tree and every supported legacy shape. |
| `catalog/hooks/tests/test_old_version_docs_guard.py` | Durable cross-platform behavior contract | Keep; one parametrized runner applies every assertion to both siblings. |
| `tests/validators/test_docs_layout_prescription.py` | Catalog-wide anti-regression contract | Keep; exact-content exemptions distinguish migration support from accidental old-shape prescriptions. |
| `docs/v4/v4.0/development/history/2026-08-26_v4.0.0-docs-lifespan-phase-4-executable-guards.md` | Active phase evidence | Keep under the current version's development history. |

### Result

The old-version guard is live for `docs/releases/`, `docs/archives/`, and all supported legacy layouts. Session-summary and notification hooks have no runtime dependency on the documentation tree; their remaining legacy paths are provenance-only comments. The workflow notice is proven against `docs/releases/v9/v9.9/plans/`. No documentation was moved, no duplicate policy was introduced, and the new aggregate validator rejects a deliberately reintroduced old prescription.

## Phase 5 - Distribution to every platform class

### Distribution artifacts

| Path | Category | Disposition |
|---|---|---|
| `templates/ai-instructions/*.md` across the 12 substantive templates | Distributed instruction contract | Keep; each substantive platform template carries the same concise lifespan block. |
| `scripts/check_base_template_parity.py` | Repository-only invariant gate | Keep; `Documentation Layout` is byte-locked across the five lockstep templates and remains listed in `DEV_ONLY_SCRIPTS`. |
| `tests/validators/test_check_base_template_parity.py` | Negative mutation proof | Keep; it proves one deliberately divergent template fails the gate. |
| `tests/validators/test_communication_contract_rollout.py` | Aggregate distribution proof | Keep; one data-driven roster covers all 12 substantive templates and the four inheriting stubs. |
| `docs/v4/v4.0/development/history/2026-08-26_v4.0.0-docs-lifespan-phase-5-platform-distribution.md` | Active phase evidence | Keep under the current version's development history. |

### Result

All 12 substantive templates carry one byte-identical `Documentation Layout` body, while the four thin include stubs inherit without duplication. Isolated workspace renders proved Codex, Copilot, and Aider output paths and content. No product documentation moved in this phase. The attempted global throwaway proof exposed BG-2 in the integration runner's target-root handling; it is recorded rather than concealed or fixed outside the phase boundary.

## Phase 6 - Dogfood migration of Nexus-Hub's own tree

### Migration

| Movement | Files | Disposition |
|---|---|---|
| `docs/v3/v3.<minor>/` and `docs/v4/v4.<minor>/` -> `docs/releases/...` | 276 | Moved by `audit-docs.py canonicalize-layout` (25 v-bucket migrations). |
| `docs/archive/` -> `docs/archives/` | 486 | Moved by the same command after Phase 6 extended it to the archive container. |
| `docs/v3/roadmap-prioritization.md` -> `docs/roadmap-prioritization.md` | 1 | Relocated to a living root by the lifespan admission test; decision record `2026-08-27-roadmap-ordering-doc-moves-to-a-living-root.md`. |
| `docs/v3/`, `docs/v4/` | 0 | Pruned once empty. No legacy active container remains. |

### Result

763 tracked files moved and git classified all 763 as renames with zero unpaired deletions. The `.gitignore` pre-flight ran before the first move and matched no destination. The move-aware link set diff reports zero newly broken links and 59 fixed. Two dead links predate the migration and are recorded as BG-6 rather than silenced with placeholder files. No document was deleted, and no content was edited except link targets and the four consuming artifacts listed in the phase session history.
