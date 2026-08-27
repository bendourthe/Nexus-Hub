# Session History - Interface-Craft Skills Phase 7: refactor, known-gaps, CI/CD

**Date**: 2026-08-23
**Branch**: `feat/v3.20.2-interface-craft-skills`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.2-interface-craft-skills.md`](../../plans/v3.20.2-interface-craft-skills.md)
**Phase**: 7 - Architecture refactor, known-gaps, CI/CD (final phase)
**Environment**: Windows 11, PowerShell, Python 3
**Outcome**: No layout moves. D1 re-measured and resolved. Catalog-count drift deferred to `/update release`. CI left on the existing unfiltered-trigger workflow. Ready to hand off.

## 1. Starting State and Routing

- **Starting commit**: `cf07afc0` (Phase 6 coordinator)
- **Plan recommendation**: strong reasoning tier, high effort
- **Implementation route**: current Cursor session; no downshift
- **`is_final_phase`**: yes (phase 7 of 7, prior phases complete)

## 2. What Was Implemented

### 7.1 - Refactor

`project-refactor` and `docs-layout-refactor` in propose-then-apply. Proposal: no empty dirs under the new skill trees, no thin reference files to collapse, docs tree already canonical. Apply was a no-op (nothing to move).

### 7.2 - Known gaps

- **BG-2** (comparison D1): 140 `agents/openai.yaml` files exist. After unfolding YAML folded scalars, 140/140 end with sentence punctuation. The comparison's "improving test cove" / "mid-sessio" examples are line wraps of complete sentences (`unit-tests`, `context-degradation`). Resolved in this phase. The six new skills have no sidecar.
- **DF-6**: prose counts still say 315 (`README.md`, `AGENTS.md`, `plugin.json`, marketplace plugin.description) against 321 in the registries. Handed to `/update release`.
- **WN-3**: remains open (OneDrive full-tree personal-path scan). Left to CI on ubuntu-latest.

### 7.3 - CI/CD

No workflow edit. `.github/workflows/ci.yml` already: unfiltered `on:` (required-check contract), job-level `changes` classifier (non-docs paths including `catalog/skills/**` and `data/**` are relevant), concurrency cancel-in-progress, pip cache, `validate_skills.py --bundles-only` (do not switch to strict; v3.14.2 WN-1), `run_trigger_evals.py --gate`, `check_registry_entries.py` via `make validate`. A second workflow or a workflow-level `paths:` filter would recreate the v3.17.5 Pending-forever failure.

## 3. Tests

Phase 6 already left `validate_skills.py --bundles-only`, `check_registry_entries.py --strict`, `run_trigger_evals.py --gate`, and `check_agentskills_conformance.py` green at 321. This phase changed docs only.

## 4. Next Steps

`/update release`: reconcile DF-6 headline counts, bump 3.20.1 -> 3.20.2, finalize CHANGELOG / DEVLOG / manifest. Do not tag until HEAD is on the release branch and equal to origin (pre-tag gate).
