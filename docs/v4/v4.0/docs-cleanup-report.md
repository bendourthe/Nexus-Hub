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
