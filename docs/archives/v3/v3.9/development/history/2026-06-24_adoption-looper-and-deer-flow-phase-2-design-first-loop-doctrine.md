# Session History - v3.9.0 adoption-looper-and-deer-flow Phase 2: Design-first loop doctrine

**Date**: 2026-06-24
**Plan**: [`../../plans/adoption-looper-and-deer-flow.md`](../../plans/adoption-looper-and-deer-flow.md) Phase 2 (L2 + L4 + L5 loop half + L1 cross-link, skill-native)
**Branch**: `develop`
**Outcome**: Complete. All Phase 2 exit-checklist items satisfied; quality gate GO. Phase 2 of 3; not the final phase, so no release-readiness run.

## Goal

Add to `loop-engineering` the pre-flight design doctrine Looper surfaces: a staged design pass that tightens the goal and types the verification before the first iteration (L2, the P1 design gap), the programmatic-then-judge-then-human verification ordering plus a render-and-confirm-before-first-run note (L4), the argv-array invocation discipline in the `check_command` guidance (L5, loop half), and a cross-link from the maker/checker (council-seat) material back to the Phase 1 egress hygiene (L1 link). Skill-native Markdown enrichment only: no new skill, command, hook, outbound call, dependency, or credential.

## What shipped

- **`catalog/skills/workflow/loop-engineering/SKILL.md`** (body 190 -> 207 lines): one new section plus three inline edits.
  - **"Design the Loop Before You Run It" section (2.1 L2 + 2.2 L4)**: a new `## Design the Loop Before You Run It` placed before `## Instructions` (a pre-flight pass that precedes assembly). It teaches three design stages critiqued before the first iteration: GOAL shape (concrete outcome plus the artifact or state that proves the loop finished, scope boundaries, named context sources, named consumer; reject "improve the project" / "make it good"; critique prompt "what would count as done if two competent agents disagreed?"), VERIFICATION typing (programmatic / judge / human, at least one non-vibe check, with the explicit preference order programmatic-then-judge-then-human and the rule that a judge-or-human-only loop must say why no programmatic check was available), and CONTROL guards (the mandatory `iteration_cap` and command-derived `exit_condition`, plus `progress_check` and `handoff` for production loops). The section explicitly COMPOSES the existing task-readiness gate and routes underspecified goals to `/plan` / `/idea-refine` and to `[[ambiguity-detector]]` + `[[requirement-enhancer]]` without duplicating them, tying underspecified-goal-looping back to the existing loopmaxxing guardrail. It closes with a `**Render and confirm before the first run.**` note (render goal -> gates -> caps as plain text and confirm before any file changes) tied to the Step 5 scope-first calibration discipline.
  - **Argv-array note (2.3 L5 loop half)**: Step 4 item 3 (the `check_command` pick) now requires the check and any model invocation to be expressed as an argument array with an explicit timeout, never an interpolated shell string, citing the project Bash security rules and the injection-resistance rationale. This matches the Best Practices bullet added to `cross-model-orchestrator` in Phase 1.
  - **Egress cross-links (2.3 L1 link)**: Step 4 item 7 (maker/checker assignment) and the Scheduled-Triage Recipe step 5 (independent checker reviews) each gained a one-line pointer that when a checker or council seat is a different model behind an external CLI the handoff is an egress event governed by the handoff-egress-hygiene discipline in `[[cross-model-orchestrator]]` (redaction defaults plus first-send consent), wiring Phase 2 back to the Phase 1 section.

## Key decisions / troubleshooting

- **Authored 2.1 and 2.2 as one cohesive section, not two passes.** The plan tracks the design stages (2.1) and the verification ordering plus render-and-confirm (2.2) as separate sub-tasks, but both edit the same new region. The verification ordering folds naturally into the VERIFICATION-typing bullet, and the render-and-confirm closes the section; authoring them together avoided re-editing the same lines and produced a single coherent doctrine block. Outcomes preserved, mechanical edits consolidated.
- **Kept the rubric inline; no `references/loop-design-rubric.md`.** The plan made the reference file conditional on the 500-line norm. At 207 lines the body stays well under the norm, so an extra file would have added an orphan-risk and a maintenance hop for no token-budget benefit. The section lives in the body and the orphan-bundle audit stays clean (the two existing reference files, `loop-schema.md` and `loop-library.md`, remain linked and untouched).
- **`## Design the Loop Before You Run It` as an H2 before `## Instructions`.** Matching the file's heading idiom (top-level doctrine sections are H2; workflow steps are `### Step N` under `## Instructions`) and the plan's stated placement. No heading-hierarchy violation since it is a peer of the other H2 doctrine sections.
- **CHANGELOG and known-gaps intentionally deferred.** Per the plan's phasing, the `## [Unreleased]` CHANGELOG entry, the `docs/v3/v3.9/known-gaps.md` update, and the registry-edit decision are consolidated in Phase 3 sub-task 3.4; Phase 2 leaves them untouched. Frontmatter was likewise not changed in this phase.

## Verification (quality gate: GO)

- `make` is not on PATH, so the gate was run via its documented equivalents:
  - **JSON catalog integrity**: `data/skills.json` OK (256 skills), `data/bundles.json` OK (15 bundles), `data/workflows.json` OK (17 workflows).
  - **Orphan-bundle audit** (`python scripts/validate_skills.py --bundles-only`, the `make validate` gate): PASS, 0 errors (1 pre-existing warning unrelated to `loop-engineering`). No new bundle files were added.
  - **Unicode-safety** (`python scripts/validate_unicode_safety.py`): exit 0 (1051 pre-existing warnings catalog-wide); `loop-engineering/SKILL.md` does not appear anywhere in the report, confirming every added line is ASCII-only.
  - **Dangling-wikilink audit**: the three new/used cross-link targets resolve to real skills -- `ambiguity-detector` and `requirement-enhancer` under `catalog/skills/developer-experience/`, `cross-model-orchestrator` under `catalog/skills/orchestration/`.
  - **Body size**: 207 lines, under the 500-line norm.
  - **Attribution grep**: the file contains zero matches for `Looper`, `ksimback`, `loop.yaml`, `definition_of_done`, `ASCII flow preview`, `DeerFlow`.
  - **Internal consistency**: the new design pass composes (does not duplicate) the existing task-readiness gate; the argv-array note matches the Phase 1 `cross-model-orchestrator` Best Practices bullet; the egress cross-links name the exact Phase 1 discipline (redaction defaults plus first-send consent). No contradiction with the Strict Control Loops, Exit-Signal Protocol, Stall and Fault Detection, Workflow-Control Patterns, or Sandboxing sections.

## Files changed

- `catalog/skills/workflow/loop-engineering/SKILL.md`
- `docs/v3/v3.9/plans/adoption-looper-and-deer-flow.md` (Phase 2 exit checklist checked off)
- `docs/archive/v3/v3.9/development/history/2026-06-24_adoption-looper-and-deer-flow-phase-2-design-first-loop-doctrine.md` (this file)

## Next

Phase 3: Low-priority doctrine notes and consolidation -- the default-deny host-execution posture in `agent-access-policy` (D1) with a reciprocal cross-link to the loop-engineering sandbox subsection, the optional typed-fact memory schema note in a memory skill (D2), the RE-matrix rows recording the two `drop-outright` runtime declines plus the advisory-cost-cap cautionary note and the DeerFlow convergent-validation finding, the registry-edit decision (most likely `cross-model-orchestrator` gaining handoff egress hygiene as a headline capability), and the consolidated CHANGELOG `## [Unreleased]` and `docs/v3/v3.9/known-gaps.md` updates. Phase 3 is the final phase, so `/implement` will run the release-readiness workflow after the post-phase sequence.
