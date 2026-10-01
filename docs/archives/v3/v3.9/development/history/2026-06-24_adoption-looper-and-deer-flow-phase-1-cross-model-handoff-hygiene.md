# Session History - v3.9.0 adoption-looper-and-deer-flow Phase 1: Cross-model handoff hygiene

**Date**: 2026-06-24
**Plan**: [`../../plans/adoption-looper-and-deer-flow.md`](../../plans/adoption-looper-and-deer-flow.md) Phase 1 (L1 + L3 + L5 cross-model half, skill-native)
**Branch**: `develop`
**Outcome**: Complete. All Phase 1 exit-checklist items satisfied; quality gate GO. Phase 1 of 3; not the final phase, so no release-readiness run.

## Goal

Add to `cross-model-orchestrator` the egress discipline it currently lacked entirely: redaction-glob defaults and a first-send consent gate before any project artifact crosses to a second model (L1, the P1 security headline), the reviewer-versus-judge verdict-honesty rule in its quality-gate step (L3), and the argv-array invocation discipline for model invocations (L5, cross-model half). Skill-native Markdown enrichment only: no new skill, command, hook, outbound call, dependency, or credential.

## What shipped

- **`catalog/skills/orchestration/cross-model-orchestrator/SKILL.md`** (20 insertions, body now 310 lines): three additive edits.
  - **Handoff Egress Hygiene section (1.1, L1)**: a new `### Handoff Egress Hygiene` section placed immediately after Step 3 (the artifact-handoff step) and before Step 4. It frames every artifact handed to a second model behind an external CLI/API as a content-egress boundary governed by the MCP Registry Policy in `AGENTS.md`, and teaches three rules: redact-before-first-send against a default deny-glob set (`.env`, `.env.*`, `secrets/**`, `**/*.key`, plus project-specific secret paths) using a visible `[redacted:<relative-path>]` marker; explicit first-send consent stating WHAT/WHICH-model/WHICH-globs with a recorded consent so later same-session sends do not re-prompt; and a fully-local-reviewer carve-out that needs no egress consent. Cross-links `[[agent-access-policy]]`.
  - **Reviewer vs. judge rule (1.2, L3)**: a `**Reviewer vs. judge**` subsection folded into Step 4's Gate Actions area. A reviewer produces non-binding notes; a judge returns a structured pass-or-revise verdict with blocking issues and a confidence value; only a judge or a human may be the deciding source for a "revise until clean" gate, because treating reviewer notes as a clean verdict is fake precision. Tied to the existing self-review entry in the Common Rationalizations table; cross-links `[[quality-gate-definitions]]` and `[[adversarial-verifier]]`.
  - **Argv-array invocation discipline (1.3, L5 cross-model half)**: one Best Practices bullet requiring model and check invocations to be expressed as argument arrays with an explicit per-call timeout, never interpolated shell strings, citing the project Bash security rules and the injection-resistance rationale.

## Key decisions / troubleshooting

- **Heading level: `###` not `##` for the egress section.** The plan's sub-task 1.1 prompt titled the section `## Handoff Egress Hygiene` and placed it between `### Step 3` and `### Step 4`. A literal H2 there would have orphaned Step 4 and Step 5 from their parent `## Instructions` (they would nest under the new H2), violating the Markdown style guide's heading-hierarchy rule. Resolved by keeping the exact title text and placement but making it an `###` peer of the workflow steps. Step 4 (Quality Gates) was kept as Step 4 because sub-task 1.2 references it by that name; no renumbering.
- **Bold lead-in, not a new heading level, for "Reviewer vs. judge".** The file uses bold paragraph leads (`**Gate Actions**:`, `**Gate 1: ...**`) within steps and has no H4 anywhere. Matching the file's idiom (`**Reviewer vs. judge**`) beat introducing the catalog's only H4.
- **Frontmatter deliberately untouched.** Per the plan, the registry/summary-edit decision is deferred to Phase 3 sub-task 3.4; Phase 1 changes only the body. The pre-existing 261-char `description` heuristic warning is therefore unchanged by this phase.

## Verification (quality gate: GO)

- `make` is not on PATH, so the gate was run via its documented equivalents:
  - **JSON catalog integrity**: `data/skills.json` OK (256 skills), `data/bundles.json` OK (15 bundles).
  - **Orphan-bundle audit** (`python scripts/validate_skills.py --bundles-only`, the `make validate` gate): PASS, 0 errors. No new bundle files were added.
  - **Dangling-wikilink audit**: the three cross-link targets resolve to real skills (`agent-access-policy`, `quality-gate-definitions`, `adversarial-verifier` all under `catalog/skills/orchestration/`); the `## MCP Registry Policy` section exists in `AGENTS.md`.
  - **ASCII-only**: Python scan of all added (`+`) diff lines found zero non-ASCII characters.
  - **Body size**: 310 lines, under the 500-line norm.
  - **Attribution grep**: the diff contains zero matches for `Looper`, `ksimback`, `DeerFlow`, `privacy.egress`, `ensure_consent`, `redact_prompt_for_member`.
- The bare `validate_skills.py --verbose` strict run reports 155 pre-existing `description`-length heuristic warnings across the catalog (the project's intentionally long "pushy" descriptions, drained via `--allow-existing`); none were introduced by this phase, and the canonical `make validate` gate does not block on them.

## Files changed

- `catalog/skills/orchestration/cross-model-orchestrator/SKILL.md`
- `docs/v3/v3.9/plans/adoption-looper-and-deer-flow.md` (Phase 1 exit checklist checked off)
- `docs/archive/v3/v3.9/development/history/2026-06-24_adoption-looper-and-deer-flow-phase-1-cross-model-handoff-hygiene.md` (this file)

## Next

Phase 2: Design-first loop doctrine in `loop-engineering` (the "Design the Loop Before You Run It" section composing the task-readiness gate, the typed-verification ordering plus a render-and-confirm note, the argv-array note in the `check_command` guidance, and a council-seat cross-link back to this phase's egress hygiene). CHANGELOG `## [Unreleased]` and `docs/v3/v3.9/known-gaps.md` updates are consolidated in Phase 3 sub-task 3.4, per the plan's phasing.
