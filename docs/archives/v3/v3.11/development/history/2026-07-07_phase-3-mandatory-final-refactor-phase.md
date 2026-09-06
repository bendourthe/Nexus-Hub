# Session History - v3.11.0 Phase 3: Mandatory final refactor + known-gaps + CI/CD phase in planning

**Date**: 2026-07-07
**Plan**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md`
**Phase**: 3 of 8 - Mandatory final refactor + known-gaps + CI/CD phase in planning
**Status**: Complete (stability gate PASS)

## Goal

Every plan `/plan` generates ends with a mandatory final phase (architecture refactor + known-gaps reconciliation + CI/CD create-update-optimize), and every phase's testing sub-task creates/updates and optimizes CI/CD.

## What changed

### 3.1 - Mandatory final phase in the plan template (`implementation-plan/SKILL.md`)

- Added a `#### Mandatory Final Phase (every plan)` block right before the Phase Design Guidelines. It emits, verbatim, a terminal `## Phase N: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD` with four sub-tasks: N.1 architecture refactor (deprecated/obsolete files, empty dirs, redundant files/dirs, overcomplicated structure -> clean layout via `[[project-refactor]]` + `[[docs-layout-refactor]]`), N.2 known-gaps reconciliation via `[[known-gaps-tracker]]`, N.3 CI/CD create/update/optimize, N.4 testing and stabilization.
- Reconciled with the "testing is per-phase, not a final QA phase" philosophy: the block states explicitly that this is a REFACTOR / known-gaps / CI phase, NOT a deferred-testing phase, and that per-phase testing still stands.
- Added a "Terminal refactor phase" row to the Phase Design Guidelines table.
- Added a Verification checklist item: "The plan's last phase is the mandatory Architecture Refactor, Known-Gaps Reconciliation, and CI/CD phase (N.1-N.4)".

### 3.2 - Per-phase CI/CD create/update/optimize language

- Strengthened the per-phase `#### N.X - Testing and Stabilization` template prompt so that, after tests pass, it creates or updates the CI/CD pipeline for the phase's changes and optimizes it (path filters, concurrency cancel-in-progress, dependency caching, gating expensive-OS/matrix jobs to merges/schedule) while keeping comprehensive coverage - platform-agnostic, GitHub Actions as the primary example.
- Added a "CI/CD per phase" row to the Phase Design Guidelines table, and folded the CI/CD expectation into the "every phase ends with a testing sub-task" Verification item.

### 3.3 - `/plan` dispatcher note (`plan.md`)

- Added a thin "Mandatory final phase (planning scopes)" section before Delegation that surfaces the guarantee and cross-references the `[[implementation-plan]]` skill's template and design guidelines, without duplicating the template (keeps the dispatcher thin per the command-scope-mechanism contract).

## Verification

- All five template markers present exactly once: the Mandatory Final Phase heading, the `## Phase N: Architecture Refactor...` template heading, the "Terminal refactor phase" and "CI/CD per phase" guideline rows, and the last-phase Verification item.
- Code-fence balance in `implementation-plan/SKILL.md`: 6 fence lines = 3 complete fenced blocks (the new Mandatory Final Phase template added one balanced `markdown` fence).
- Frontmatter still parses (`implementation-plan`).
- `validate_skills.py --bundles-only`: PASS (0 errors). `--quality`: PASS (0 errors). `validate_unicode_safety.py`: 0 errors. `check_version_sync.py`: clean at 3.10.3.

## Notes and environment caveats

- This phase changes the plan *contract* (the template every future plan inherits); it does not retrofit the current v3.11.0 plan, which was authored before Phase 3. `/implement` handles a pre-Phase-3 plan by running the refactor+known-gaps+CI/CD gate on its last phase anyway (that wiring is Phase 5, sub-task 5.2). The current plan's terminal Phase 8 (dogfood) already covers the same ground by design.
- "Generate a small throwaway plan" from the plan's 3.4 prompt is an agent-execution simulation of the skill; the meaningful verification for a template change is that the template block, guideline rows, and Verification item are present and coherent (confirmed above), so the skill now emits the mandatory final phase.
- `make` is unavailable on this Windows host; validate gates were run individually. The extension-local compression eval was not run (untouched by Phase 3).

## Next steps

- Phase 4: Refactor-engine upgrade (`project-refactor` gains empty-dir, duplicate, non-version-orphan, and structure-complexity detection) - the engine the Phase 3 terminal phase (N.1) invokes.
