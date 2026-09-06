# Session History: v2.1.0 Phase 5 - Clarification Loop + Spec Quality Checklist

**Date**: 2026-05-20
**Scope**: Phase 5 of [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md)
**Outcome**: New `/clarify-spec` command landed at `catalog/commands/clarify-spec.md` with the sequential 5-question clarification loop, Recommended-option contract, 10-category ambiguity taxonomy, and atomic save-per-answer; new `catalog/templates/spec-quality-checklist.md` landed with Content Quality / Requirement Completeness / Feature Readiness sections; `catalog/skills/developer-experience/idea-refine/SKILL.md`, `catalog/skills/developer-experience/spec-driven-development/SKILL.md`, and `catalog/commands/generate-plan.md` all updated with body-only edits wiring the new surfaces into the SDD workflow. All validation passes.
**Plan reference**: [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md) Phase 5
**Source comparison**: [docs/archives/v2/v2.0/comparison-spec-kit.md](../../../v2.0.0/comparison-spec-kit.md)

## Goal recap

Land the active-clarification surface that pairs with the Phase 4 spec template and the Phase 3 read-only `/analyze-spec` audit. Two adoption candidates close in this phase: G3 (the sequential 5-question loop with Recommended-option Markdown tables and per-turn integration of accepted answers back into the spec body) and G9 (the auto-generated spec-quality-checklist that runs as the final spec-readiness gate before `/generate-plan`). The phase is skill-native per the MCP Registry Policy decision tree -- no new code, no new outbound calls, no new credentials. Phase 5 produces one new command, one new template, and three body-only updates to existing artifacts; no new skill, so no `data/` registry edits are required.

## Chronology by sub-task

### Sub-task 5.1 - Create `/clarify-spec` command + update `idea-refine`

Created `catalog/commands/clarify-spec.md` with the full sequential-loop behavior spec. Seven steps:

1. **Resolve the spec file** -- honors an explicit `<path>` argument; otherwise walks `.specify/feature.json` -> latest `specs/<NNN>-*/spec.md` -> latest `docs/<version>/plans/<slug>.md`. Aborts with a guidance message that lists the searched paths when nothing matches.
2. **Run the structured ambiguity scan** -- classifies each spec section across a 10-category taxonomy (Functional Scope & Behavior, Domain & Data Model, Interaction & UX Flow, Non-Functional Quality Attributes, Integration & External Dependencies, Edge Cases & Failure Handling, Constraints & Tradeoffs, Terminology & Consistency, Completion Signals, Misc / Placeholders), marking each as Clear / Partial / Missing.
3. **Generate the prioritized question queue** -- at most 5 candidates, balanced across at least 3 distinct categories, ordered by the same `scope > security/privacy > UX > technical` priority that Phase 1 ratified for `[NEEDS CLARIFICATION]` markers. Each candidate is answerable with EITHER a 2-5 option multiple choice OR a <=5-word short-phrase answer; long-form questions are explicitly out of scope (they belong in a design doc).
4. **Sequential questioning loop** -- exactly one question per turn. Multiple-choice format renders a Recommended option above the table with cited evidence (specific spec section, existing repo convention, constitution principle, or comparison report); short-phrase format renders the Recommended <=5-word guess above the prompt with cited reasoning. Both accept `yes` / `recommended` / `accept` / `r` for the recommendation, a single letter A-E for an option, a free-form short answer for an override, `skip` to defer the question, and `stop` / `done` / `good` / `no more` to end the loop early.
5. **Integrate the accepted answer** -- two updates per answer, both saved atomically (write to temp file, fsync, rename): (a) append `- Q: <question> -> A: <answer>` to a `## Clarifications` section under a `### Session YYYY-MM-DD` subheading (created on first answer of the day; subsequent days produce additional sub-session headings under the same Clarifications section); (b) apply the clarification to the appropriate section(s) of the spec body per a mapping table (Functional Scope to FR-### items, Domain & Data Model to Key Entities, Interaction & UX Flow to Acceptance Scenarios, Non-Functional Quality Attributes to measurable thresholds, Integration to External Dependencies, Edge Cases to the eponymous subsection, Constraints to the header or a Constraints subsection, Terminology to canonical-name replacement across all sections, Completion Signals to SC-### items, Misc / Placeholders to in-place replacement with marker removal).
6. **Stop conditions** -- four distinct stops, any of which ends the loop: 5 questions asked (or `--max-questions N` reached), all critical ambiguities resolved (no Missing categories AND at most one Partial), explicit user signal, empty queueable set after the cosmetic-only filter.
7. **Emit the completion report** -- per-category before/after status table, outstanding-ambiguities bullets with one-sentence closure notes, and a recommended-next-command branch (rerun `/clarify-spec` if outstanding ambiguities remain; run `/analyze-spec` followed by `/generate-plan` if all categories are now Clear; rerun `/analyze-spec` if the session added new FR-### / SC-### IDs).

Three invocation forms documented: `/clarify-spec` (default, latest spec), `/clarify-spec <path>` (explicit spec file or feature directory), `/clarify-spec --max-questions N` (lower the cap; never raise above 5). Six behavior guarantees: sequential questioning, Recommended-option mandatory, atomic save per answer, hard cap 5 questions, no sibling files created, FR-### / SC-### ID stability. Common Failure Modes table rebuts six anti-patterns the agent might fall into ("question dump", "bias toward more options", "no recommendation", "answer never integrated", "spec lost on crash", "loop never terminates") and shows how the documented steps avoid each one. Nexus-Hub-native framing throughout per the Reverse-Engineering Attribution Rule -- no upstream attribution leaks.

Then updated `catalog/skills/developer-experience/idea-refine/SKILL.md` Step 5 (Identify Open Questions) with a new `Boundary with /clarify-spec` paragraph immediately after the existing 3-marker-cap paragraph. The paragraph clarifies the division of labor: `idea-refine` operates BEFORE a spec exists (input: a vague idea or `[NEEDS CLARIFICATION]`-laden problem statement; output: a one-page problem statement with bounded scope and observable success criteria); `/clarify-spec` operates AFTER `spec.md` is written (input: a structured spec with FR-### / SC-### IDs; output: the same spec with ambiguities resolved at the requirement and user-story granularity through the sequential 5-question loop). The paragraph explicitly notes that `/clarify-spec` should not be invoked against a vague problem statement -- it expects the structured template from `catalog/templates/spec-template.md`.

### Sub-task 5.2 - Ship `catalog/templates/spec-quality-checklist.md` + update `spec-driven-development` and `/generate-plan`

Created `catalog/templates/spec-quality-checklist.md` with three checklist sections:

1. **Content Quality** -- four items: no implementation details (languages, frameworks, APIs), focused on user value and business needs, written for non-technical stakeholders, all mandatory sections completed.
2. **Requirement Completeness** -- eight items: no `[NEEDS CLARIFICATION]` markers remain, requirements are testable and unambiguous, success criteria are measurable, success criteria are technology-agnostic, all acceptance scenarios defined, edge cases identified, scope clearly bounded, dependencies and assumptions identified.
3. **Feature Readiness** -- four items: every functional requirement has clear acceptance criteria, user scenarios cover primary flows, the feature meets measurable outcomes from Success Criteria, no implementation details leak into the spec.

The closing Notes section codifies the iteration contract: items that remain unchecked after 3 passes must be documented in the spec's `## Assumptions` section before advancing to `/clarify-spec` or `/generate-plan`; FR-### or SC-### IDs that are inherently non-testable must be rewritten rather than silently ticked; the checklist validates the spec's prose ("unit tests for English") rather than implementation correctness (which is validated separately by tests against FR-### / SC-### IDs via `[[cross-artifact-analyzer]]`'s coverage matrix). Nexus-Hub-native framing -- no upstream attribution.

Then updated `catalog/skills/developer-experience/spec-driven-development/SKILL.md` with two body additions:

1. A new `### Auto-validating the spec` subsection immediately after the `### User stories with priorities` subsection from Phase 4. The subsection documents the 3-pass iteration (Pass 1 Content Quality, Pass 2 Requirement Completeness, Pass 3 Feature Readiness) and the post-3-pass behavior (remaining unchecked items go into `## Assumptions` and warn the user before advancing). It frames the checklist as "unit tests for English" and reinforces that implementation correctness is validated separately by `[[cross-artifact-analyzer]]`'s coverage matrix.
2. A new Related Skills cross-link to `/clarify-spec`: "(Phase 5 command) -- sequential 5-question loop that resolves spec ambiguities after the template's slots are filled; pairs with the spec-quality-checklist for the final readiness gate before `/generate-plan`".

Then updated `catalog/commands/generate-plan.md` Step 4 (Generate the Plan File) with a new `### Spec-quality-checklist companion (feature-level plans only)` block immediately after the existing Constitution Check + Complexity Tracking discussion. The block resolves the target directory (`docs/<version>/plans/<slug>/checklists/requirements.md` for the default layout or `specs/<NNN>-<slug>/checklists/requirements.md` for the Phase-7 opt-in layout), copies the template contents with `[FEATURE NAME]` / `[DATE]` / `[Link to spec.md]` placeholders replaced, leaves an existing checklist file in place (with an announcement directing the user to rerun `/clarify-spec` or edit the checklist directly to refresh), and tells the user the next step (run `/clarify-spec` if unchecked items remain, or `/analyze-spec` followed by `/implement-phase <slug> phase-1` if all items pass). The block explicitly skips the checklist companion for plan types 1 (initial greenfield build), 3 (refactor), and 4 (other) since none of those plan types produces a feature spec; the Constitution Check section above is still emitted for all plan types.

### Sub-task 5.3 - Phase 5 testing and stabilization

Verification was performed in dry-run / inspection mode (no live `/clarify-spec` interactive run against a scratch spec was needed because the command body is a behavior specification rather than a Python implementation):

- **JSON validity**: `python -c "import json; ..."` against all five `data/*.json` files (`skills.json`, `bundles.json`, `workflows.json`, `templates.json`, `marketplace.json`) succeeds with UTF-8 encoding. `skills.json` reports 205 entries, unchanged from Phase 4 close.
- **Skill-bundle audit**: `python scripts/validate_skills.py --bundles-only` returns PASS with 0 errors and 0 warnings across the 209 skills it scans. No orphan bundles introduced because Phase 5 ships only a top-level command, a top-level template, and three existing-artifact body edits; no new bundled `scripts/`, `references/`, or `assets/` subdirectories were added.
- **Full validator on updated skills**: `python scripts/validate_skills.py --path catalog/skills/developer-experience/idea-refine` and the same against `spec-driven-development` both return PASS with 0 errors and 5 baseline warnings (missing optional `author` / `version` / `category` / `license` / `tags` frontmatter fields -- identical to the warning profile that was present before Phase 5 and matches the established baseline across the catalog).
- **No scratch files created or deleted**: the verification did not require an interactive `/clarify-spec` rehearsal because the command body is a behavior specification consumed by the agent at invocation time; the verification covered structural integrity of the command body, template content, and skill-body edits.

## Files changed

- `catalog/commands/clarify-spec.md` -- new file. Sequential 5-question clarification loop command body with full behavior specification across seven documented steps, three invocation forms, six behavior guarantees, and six common-failure-mode rebuttals.
- `catalog/templates/spec-quality-checklist.md` -- new file. Three-section auto-validation checklist (Content Quality, Requirement Completeness, Feature Readiness) plus iteration-contract Notes.
- `catalog/skills/developer-experience/idea-refine/SKILL.md` -- body update. Step 5 gains a `Boundary with /clarify-spec` paragraph clarifying the before-spec vs after-spec division of labor.
- `catalog/skills/developer-experience/spec-driven-development/SKILL.md` -- body update. New `### Auto-validating the spec` subsection after the Phase 4 user-stories subsection; new Related Skills cross-link to `/clarify-spec`.
- `catalog/commands/generate-plan.md` -- body update. Step 4 gains a `### Spec-quality-checklist companion (feature-level plans only)` block that writes the checklist alongside the plan for plan type 2 when a sibling `spec.md` exists.
- `docs/archive/v2/v2.1/known-gaps.md` -- `Last updated` line refreshed with the Phase-5-close note; no new items added, no items resolved.

## Deviations from plan

None. All sub-tasks completed per the plan prompts. No `# DEVIATION:` markers introduced in any file.

## Verification (quality gates)

| Gate | Threshold | Status |
|---|---|---|
| All tests passing | 0 failures | N/A (no test changes in this phase; phase ships skill-native artifacts) |
| Line coverage | >= 80% | N/A (no code added; phase ships Markdown command body, template, and skill-body edits) |
| Lint errors | 0 errors | PASS (no shell scripts touched; ShellCheck not applicable to this phase) |
| Build / compile | Succeeds | PASS (all five `data/*.json` files parse cleanly with UTF-8 encoding; skill-bundle audit returns 0 errors / 0 warnings) |

## Known gaps after Phase 5

`docs/archive/v2/v2.1/known-gaps.md` `Last updated` line refreshed with the Phase-5-close note. No new items added; no items resolved. WN-1 (the pre-existing `data/skills.json` statistics drift, opened in Phase 1 and compounded by Phase 3) remains open and stays scheduled for repair via `make build-catalog` in Phase 8 sub-task 8.1 step 5.

## Next step

Phase 6 -- task discipline. `/generate-plan` Step 3 and Step 4 will be updated to enforce a strict task checklist format (`- [ ] T### [P?] [US?] Description with file path`) across the entire plan with sequential T-IDs in execution order, optional `[P]` parallel markers, required `[US#]` user-story labels on user-story phase tasks only (Setup / Foundational / Polish phases get no labels), and an exact file-path reference per task. Phase organization will shift to a strict ordering: Setup, Foundational, then user stories in priority order (P1 -> P2 -> P3 each with its internal Tests -> Models -> Services -> Endpoints -> Integration sub-ordering and an independently-testable increment as its acceptance criterion), and a final Polish & Cross-Cutting Concerns phase. Phase 6 prerequisites are Phase 4 (provides the user-story IDs that the `[US#]` label keys off) -- now complete.
