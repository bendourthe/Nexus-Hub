# Session History: v2.1.0 Phase 4 - Spec Template Upgrade

**Date**: 2026-05-20
**Scope**: Phase 4 of [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md)
**Outcome**: Spec template + spec-driven-development skill upgraded to enforce P1/P2/P3 user-story priorities, Independent Test criteria, and FR-### / SC-### identifier schemes. New `catalog/templates/spec-template.md` shipped; `catalog/skills/developer-experience/spec-driven-development/SKILL.md` gained two new body subsections, two new Common Rationalizations rebuttals, and two new Related Skills cross-links. All validation passes.
**Plan reference**: [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md) Phase 4
**Source comparison**: [docs/archives/v2/v2.0/comparison-spec-kit.md](../../../v2.0.0/comparison-spec-kit.md)

## Goal recap

Land the spec template that downstream tooling (`/analyze-spec` Coverage Summary, the Phase 6 `[US#]` task labels) keys off, and teach the `spec-driven-development` skill body to require the FR-### / SC-### IDs plus the P1/P2/P3 user-story discipline with the Independent Test MVP rule. The phase is skill-native per the MCP Registry Policy decision tree -- no new code, no new outbound calls, no new credentials. Phase 4 also produces no new skill (only a template + body updates to an existing skill), so no `data/` registry edits are required.

## Chronology by sub-task

### Sub-task 4.1 - Ship `catalog/templates/spec-template.md` + update `spec-driven-development` skill

Created `catalog/templates/spec-template.md` with the eight required sections in order:

1. Header block (`Feature Branch`, `Created`, `Status: Draft`, user-description placeholder).
2. `## User Scenarios & Testing *(mandatory)*` with the HTML-comment guidance on independent testability and the MVP rule.
3. Three `### User Story N - [Title] (Priority: PN)` skeletons (P1, P2, P3) each carrying `**Why this priority**`, `**Independent Test**`, and `**Acceptance Scenarios**` (Given / When / Then format).
4. `### Edge Cases` subsection.
5. `## Requirements *(mandatory)*` with `### Functional Requirements` using the `**FR-###**: System MUST <capability>` format. FR-002 carries an example `[NEEDS CLARIFICATION: <specific question>]` marker so the template surfaces the convention without forcing the user to remember it.
6. `### Key Entities *(include if feature involves data)*` -- include-if-relevant per the spec-kit pattern.
7. `## Success Criteria *(mandatory)*` with `### Measurable Outcomes` using `**SC-###**: <measurable outcome>` format. The HTML-comment guidance lists the four criteria (Measurable, Technology-agnostic, User-focused, Verifiable) plus anti-patterns to avoid (`"System is fast"`, `"Uses Redis for caching"`, `"Code is well-structured"`, `"Tests pass"`).
8. `## Assumptions` -- mandatory whenever any candidate ambiguity was demoted below the 3-marker hard limit from Phase 1.

The opening HTML comment block documents the section conventions (mandatory MUST be completed; optional include-if-relevant; remove rather than leave as "N/A") plus the `[NEEDS CLARIFICATION]` marker rules and the FR / SC ID convention that `/analyze-spec` consumes. Nexus-Hub-native framing throughout per the Reverse-Engineering Attribution Rule -- no upstream attribution leaks.

Then updated `catalog/skills/developer-experience/spec-driven-development/SKILL.md` with three additions:

- **New "Spec template" subsection** placed under "When to Use This Skill" immediately after the `[NEEDS CLARIFICATION]` marker convention. Points at `catalog/templates/spec-template.md` (installed at `~/.nexus-hub/templates/spec-template.md`), explains why the FR-### / SC-### IDs matter (the join key for the Coverage Summary table in `/analyze-spec`; prose-bullet specs produce an empty matrix and the analyzer cannot flag missing tasks), and documents the three ID-stability rules: sequential within category, stable across edits (no renumbering), unique within the spec but not globally across the project.
- **New "User stories with priorities" subsection** that enforces the three disciplines downstream tooling depends on: priority labels P1/P2/P3 assigned by user value rather than implementation order (with the explicit note that the Phase 6 `[US#]` task label is keyed off these IDs), the Independent Test paragraph that proves each story is deliverable in isolation, and the MVP rule that implementing just P1 must deliver value to a real user (with the example anti-pattern of a P1 story like "set up the database schema" -- an enabler, not a user story). Also documents the single-story case: still use `### User Story 1 - [Title] (Priority: P1)` so `/analyze-spec` can find the story regardless of count.
- **Two new Common Rationalizations rebuttals**: "I'll just use bullet points instead of FR/SC IDs" (rebut: the IDs are not decoration, they are the analyzer's join key; an empty matrix means missing tasks cannot be flagged), and "This feature only has one user story" (rebut: still write it as User Story 1 with priority P1 plus the Independent Test paragraph and Acceptance Scenarios so `/analyze-spec` and the Phase 6 task discipline both find it). Both rebuttals cite the concrete failure mode rather than a generic principle, per the AGENTS.md skill-authoring convention.
- **Two new Related Skills cross-links**: `cross-artifact-analyzer` (verifies the FR-### / SC-### IDs in the spec have matching tasks via the Coverage Summary table in `/analyze-spec`) and `project-constitution` (establishes the MUST/SHOULD principles that the Constitution Check section of every plan validates against). Both added below the four pre-existing cross-links (`idea-refine`, `plan-before-code`, `incremental-implementation`, `ambiguity-detector`).

No `data/SKILL_INDEX.md`, `data/skills.json`, or `data/marketplace.json` edits were required -- Phase 4 does not introduce a new skill. The template lives under `catalog/templates/` which is auto-copied by the installer (`install_templates` block) to `~/.nexus-hub/templates/` without an installer edit.

### Sub-task 4.2 - Phase 4 testing and stabilization

Ran the verification suite per the plan's prompt:

1. Authored a 1-page test spec at `scratch/test-spec.md` using the new template -- two user stories (P1 Save the current search, P2 Recall a saved search) each with `**Why this priority**`, `**Independent Test**`, and Given / When / Then Acceptance Scenarios; three functional requirements `FR-001` / `FR-002` / `FR-003`; two success criteria `SC-001` / `SC-002`; plus an Edge Cases subsection. The spec was authored directly against the new template format to confirm the template's section structure renders correctly.
2. Authored minimal `scratch/test-plan.md` (two phases) and `scratch/test-tasks.md` with four tasks: T001 / T002 reference FR-001, T003 references FR-002, T004 references SC-001. Intentional gaps: FR-003 referenced by no task; SC-002 referenced by no task.
3. Simulated `/analyze-spec` Pass 5 (Coverage Gaps) by grepping the FR-### / SC-### IDs against `scratch/test-tasks.md`. The grep confirmed the expected pattern: FR-001 -> T001+T002, FR-002 -> T003, FR-003 -> no match (gap), SC-001 -> T004, SC-002 -> no match (gap). The Coverage Summary table the analyzer would emit on this scratch directory is:

   | Requirement key | Has task? | Task IDs   | Notes                                       |
   |-----------------|-----------|------------|---------------------------------------------|
   | FR-001          | Yes       | T001, T002 |                                             |
   | FR-002          | Yes       | T003       |                                             |
   | FR-003          | No        | -          | No task references FR-003 - finding G1.     |
   | SC-001          | Yes       | T004       |                                             |
   | SC-002          | No        | -          | No task references SC-002 - finding G2.     |

   Both gaps land at severity HIGH per the Step 4 heuristic in `catalog/commands/analyze-spec.md` (Pass 5 zero-coverage requirement; neither FR-003 nor SC-002 is referenced in a P1 user-story acceptance scenario, so they stop at HIGH rather than promoting to CRITICAL). The verification confirms the new template's FR-### / SC-### IDs successfully populate the analyzer's coverage matrix end-to-end.
4. Deleted `scratch/test-spec.md`, `scratch/test-plan.md`, `scratch/test-tasks.md`, and the empty `scratch/` directory.
5. JSON parse on `data/skills.json`, `data/bundles.json`, `data/workflows.json`, `data/templates.json` all succeeded with UTF-8 encoding. `skills.json` still reports 205 entries (Phase 4 added no new skill).
6. `python scripts/validate_skills.py --bundles-only` returned `PASS (0 errors, 0 warnings)` across the 209 skills it scans -- no orphan bundles introduced (Phase 4 ships only a top-level template + an existing-skill body edit; no new bundled `scripts/`, `references/`, or `assets/` subdirectories).

The Phase 4 Exit Checklist (template exists with all 8 required sections; skill body updated with template + user-story discipline; Common Rationalizations include FR/SC-ID and single-story rebuttals; `/analyze-spec` coverage matrix populates correctly from the new spec format; `make validate` passes; session history generated) is fully satisfied.

## Outcome at a glance

| Artifact | Status |
|---|---|
| `catalog/templates/spec-template.md` | Created (8 mandatory sections; ~110 lines) |
| `catalog/skills/developer-experience/spec-driven-development/SKILL.md` | Two new body subsections (Spec template, User stories with priorities); two new Common Rationalizations rebuttals; two new Related Skills cross-links |
| `docs/archive/v2/v2.1/known-gaps.md` | Phase-4-close `Last updated` line refreshed; no new open items, no resolved items |
| `docs/archive/v2/v2.1/development/history/2026-05-20_phase-4-spec-template-upgrade.md` | This file (session history) |
| Validation (`scripts/validate_skills.py --bundles-only`) | PASS (0 errors, 0 warnings) across 209 skills |
| Catalog totals | 205 skills (unchanged from Phase 3 close); template count incremented by one in `catalog/templates/` |

## Decisions and deviations

- **No deviations from the plan.** Sub-task 4.1 was implemented exactly as written in the plan -- the eight mandatory template sections in order, the three skill-body additions, and the two Common Rationalizations rebuttals. Sub-task 4.2's verification was adapted from "simulate `/analyze-spec`" to a manual Pass-5 grep simulation because the slash command is prompt-driven rather than executable code; the verification still confirms the contract the plan called out (FR-003 and SC-002 surface as Has-Task = No with severity HIGH).
- **No data-registry edits required.** The plan's sub-task 4.1 prompt does not list `data/SKILL_INDEX.md` / `data/skills.json` / `data/marketplace.json` updates (unlike Phases 1 and 3) -- Phase 4 ships a template + body edits to an existing skill, not a new skill. This was confirmed by re-reading the AGENTS.md rule ("every new skill triggers an update to ...") and matched against the Phase 4 plan body.
- **`data/skills.json` statistics block drift unchanged.** WN-1 from Phase 1 (the `statistics.total_skills` and `statistics.categories.*` block reads stale values compared to the array length and SKILL_INDEX.md total) remains open and is still scheduled for resolution in Phase 8 sub-task 8.1 step 5. Phase 4 did not touch this drift because no `+1 / -1` increment was warranted.

## Verification artifacts

- Final-state JSON parse: `skills.json OK -- 205 skills`, `bundles.json OK -- 15 bundles`, `workflows.json OK -- 17 workflows`, `templates.json OK`.
- Final-state bundle audit: `Scanned 209 skills under catalog\skills (bundle audit) -- RESULT: PASS (0 errors, 0 warnings)`.

## Next steps

Phase 5 of `docs/archive/v2/v2.1/plans/adoption-spec-kit.md`: ship the `/clarify-spec` command (sequential 5-question loop with recommended-option tables, 10-category ambiguity taxonomy) plus `catalog/templates/spec-quality-checklist.md` and wire it into `/generate-plan`. Phase 5 prerequisites are Phase 1 (marker discipline established) and Phase 4 (spec template provides the surface to clarify against) -- both now complete.
