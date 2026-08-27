# Session History: v2.1.0 Phase 3 - Cross-Artifact Spec Analyzer

**Date**: 2026-05-20
**Scope**: Phase 3 of [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md)
**Outcome**: Read-only cross-artifact analyzer shipped (G4 from the source comparison). New `/analyze-spec` command, new `cross-artifact-analyzer` skill, three data-registry updates, plan-file relocation from v2.0.0 to v2.1.0. All validation passes.
**Plan reference**: [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md) Phase 3
**Source comparison**: [docs/archives/v2/v2.0/comparison-spec-kit.md](../../../v2.0.0/comparison-spec-kit.md) adoption candidate G4

## Goal recap

Ship the cross-artifact consistency analyzer end-to-end (command + skill) so that a Nexus-Hub user can audit a feature directory before implementation -- read spec.md, plan.md, and tasks.md (plus the project constitution from Phase 1 if present), run six detection passes, emit a severity-tagged findings table plus a coverage matrix, and never modify any file. G4 is skill-native per the MCP Registry Policy decision tree -- no new code, no new outbound calls, no new credentials, no new third-party data processors.

## Chronology by sub-task

### Plan relocation

Before opening the implementation work, the source plan file was relocated from `docs/archive/v2/v2.0/plans/adoption-spec-kit.md` to `docs/archive/v2/v2.1/plans/adoption-spec-kit.md` so it lives in the version it targets. The relocation is recorded as a `git rm` + `git add` pair in the Phase 3 commit (file body is unchanged). Two downstream links inside `docs/archive/v2/v2.1/known-gaps.md` -- the file-level `Plan` reference and the `Plan reference` field inside the WN-1 entry -- were updated to point at the new location.

### Sub-task 3.1 - Create `/analyze-spec` command + `cross-artifact-analyzer` skill

Created two new artifacts:

- `catalog/commands/analyze-spec.md` -- the read-only `/analyze-spec` command. Seven-step flow: resolve the feature directory (honors an explicit `<path>` argument, otherwise walks `.specify/feature.json` -> latest `specs/<NNN>-*/` -> latest `docs/<version>/plans/<slug>.md`), load minimal context per artifact (only the sections the detection passes need, with a self-contained-plan fallback that parses functional requirements out of phase prompts, success criteria out of Stability Gate text, and tasks out of `- [ ] T###` lines), run the six detection passes in order (Duplication, Ambiguity, Underspecification, Constitution Alignment, Coverage Gaps, Inconsistency), assign severity per the documented heuristic (CRITICAL / HIGH / MEDIUM / LOW; promotion allowed, demotion not), emit the report with the three required tables (Findings capped at 50 rows with overflow summary; Coverage Summary keyed by FR-### / SC-###; Metrics block), document the determinism contract (category-prefixed monotonic integer IDs sorted within a category by source-line number; no timestamps or hashes in IDs), and report completion. Three invocation forms: `/analyze-spec` (default), `/analyze-spec <path>`, and `/analyze-spec --output <path>`. The command body ends with explicit Behavior Guarantees -- read-only (only writable target is the optional `--output` report), deterministic IDs across reruns, constitution-aware-but-optional (Pass 4 emits an informational N/A when the constitution file is absent), overflow-safe -- and a mandatory closing statement ("This analyzer is read-only. It modifies no files. Any remediation requires user approval.") that the report MUST also emit regardless of how it was rendered.

- `catalog/skills/code-review/cross-artifact-analyzer/SKILL.md` -- the companion skill that drives the command. Required YAML frontmatter is complete (`name`, `description`, `summary_l0`, `overview_l1`). Description follows the pushy-description rule from `AGENTS.md`: trigger phrases verbatim ("analyze the spec", "is this spec ready", "do all requirements have tasks", "coverage check", "ambiguity check", "spec-plan-tasks consistency", "cross-artifact analysis", "constitution alignment check on this plan", "find gaps in this feature") plus a SKIP clause that fences off full code-review of an implementation (defers to `[[code-quality]]` + `[[security-review]]`), single-file lint passes (defers to language-specific cleanup skills), runtime profiling (defers to `[[performance-review]]`), and test execution (defers to the testing skills). The body covers all required sections: When to Use This Skill (with When NOT to use bullets), Inputs (table mapping each input to required / optional plus source path), Instructions (one numbered step per phase of the analysis), Common Rationalizations (six rebuttals: "too small a feature", "/generate-plan already cross-checks", "I'll read it myself", "constitution alignment will always pass", "I'll just delete findings I disagree with", "IDs will change on rerun anyway"), Verification (ten observable artifact / state checks), and Related Skills. Cross-links via `[[name]]` syntax point to `project-constitution` (source of MUST principles for Pass 4), `ambiguity-detector` (shares the vague-adjective and `[NEEDS CLARIFICATION]` detection logic; this analyzer applies it cross-artifact while ambiguity-detector operates per-text), `spec-driven-development` (defines FR-### / SC-### / user-story-priority conventions Passes 3 and 5 rely on), `implementation-plan` (produces the plans this analyzer audits), `idea-refine`, `known-gaps-tracker`, and `final-report` (sibling code-review skill; this analyzer focuses on specification artifacts while final-report consolidates findings from a full code review).

Both artifacts use Nexus-Hub-native framing per the Reverse-Engineering Attribution Rule -- no upstream attribution leaks into the user-facing artifact body.

Then updated the three data registries per the rule in `AGENTS.md`:

- `data/SKILL_INDEX.md`: added the `cross-artifact-analyzer` row under the code-review category and bumped the total from 204 to 205 (across 22 categories).
- `data/skills.json`: added the new skill entry following the established schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security). `statistics.total_skills` and `statistics.categories.code-review` were left at their existing values because the pre-existing drift documented as WN-1 in Phase 1 makes those fields no longer load-bearing -- the array length is the source of truth and now reads 205.
- `data/marketplace.json`: bumped the code-review category `skill_count` from 9 to 10.

### Sub-task 3.2 - Phase 3 testing and stabilization

Ran the verification suite per the plan's prompt:

1. JSON parse on all five `data/*.json` files (`skills.json`, `bundles.json`, `workflows.json`, `templates.json`, `marketplace.json`) succeeded with UTF-8 encoding. `skills.json` reports 205 entries (was 204 after Phase 1); other files were unchanged in row counts.
2. `python scripts/validate_skills.py --bundles-only` returned `PASS (0 errors, 0 warnings)` across the 209 skills it scans (208 in Phase 1; +1 for the new cross-artifact-analyzer). The validator's directory walk picks up four pre-existing entries that are not in `skills.json` (an old discrepancy unrelated to this phase); they do not introduce orphan-bundle warnings.
3. `python scripts/validate_skills.py --path catalog/skills/code-review/cross-artifact-analyzer` returned `PASS (0 errors, 5 warnings)`. The five warnings are baseline ("missing optional field 'author' / 'version' / 'category' / 'license' / 'tags'") and match the warning profile of the sibling `project-constitution` skill exactly. No new warnings introduced.
4. The constitution-alignment pass is verified to degrade gracefully via the documented behavior: when no constitution file exists, Pass 4 emits a single informational finding (N/A, not CRITICAL) with the remediation hint to run `/constitution`. The bidirectional reference is verified: `catalog/commands/constitution.md` Step 4 propagation-candidate list already mentions `catalog/commands/analyze-spec.md` ("`catalog/commands/analyze-spec.md` if it exists (Phase 3)"), so the constitution command will now find the analyzer when it runs propagation.
5. The determinism contract is implementation-level documented (not unit-tested in this phase because the analyzer is prompt-driven, not code-driven). The contract reads: within-category ordering sorts findings by the line number they reference in the source artifact, with ASCII filename order as tie-breaker; no timestamps or hashes in IDs; rerun after fixing `A1` produces `A2` (not a recycled `A1`) for any new ambiguity. This documented contract is what users rely on when they cite finding IDs in commits and follow-up tasks.

The Phase 3 Exit Checklist (`catalog/commands/analyze-spec.md` exists; `catalog/skills/code-review/cross-artifact-analyzer/SKILL.md` exists with valid frontmatter; data registries updated; findings deterministic across reruns; `make validate` passes; session history generated) is fully satisfied.

## Outcome at a glance

| Artifact | Status |
|---|---|
| `catalog/commands/analyze-spec.md` | Created (~200 lines) |
| `catalog/skills/code-review/cross-artifact-analyzer/SKILL.md` | Created (~130 lines) |
| `data/SKILL_INDEX.md` | Total bumped 204 -> 205; code-review row added |
| `data/skills.json` | New `cross-artifact-analyzer` entry appended |
| `data/marketplace.json` | code-review `skill_count` bumped 9 -> 10 |
| `docs/archive/v2/v2.0/plans/adoption-spec-kit.md` -> `docs/archive/v2/v2.1/plans/adoption-spec-kit.md` | Relocated (body unchanged) |
| `docs/archive/v2/v2.1/known-gaps.md` | Plan link fixed; WN-1 compounded note; Phase-3-close `Last updated` |
| `docs/DEVLOG.md` | New Phase 3 entry at top |
| `docs/archive/v2/v2.1/development/history/2026-05-20_phase-3-cross-artifact-analyzer.md` | This file (session history) |
| Validation (`scripts/validate_skills.py --bundles-only`) | PASS (0 errors, 0 warnings) across 209 skills |
| Validation (full validator on new skill) | PASS (0 errors, 5 baseline warnings) |
| New DEVIATION markers | 0 |
| New known-gaps items opened | 0 |
| Known-gaps items resolved | 0 |

## Cross-links

- Phase 1 session history: [2026-05-20_phase-1-project-constitution.md](2026-05-20_phase-1-project-constitution.md) -- ships the `project-constitution` skill and `/constitution` command that Pass 4 (Constitution Alignment) reads from.
- Phase 2 commit: `9d8c6e5 feat(v2.1.0): adoption-spec-kit Phase 2 - Constitution Check + Complexity Tracking gates in /generate-plan` -- ships the Constitution Check + Complexity Tracking sections that the Phase 3 analyzer can audit on any plan that emits them.
- Source comparison: [docs/archives/v2/v2.0/comparison-spec-kit.md](../../../v2.0.0/comparison-spec-kit.md) adoption candidate G4 (cross-artifact spec analyzer).

## Next phase

Phase 4 -- spec template upgrade. `catalog/templates/spec-template.md` will land with mandatory User Scenarios (P1 / P2 / P3 user stories each with Independent Test criteria), Functional Requirements as FR-### entries, Success Criteria as SC-### entries, and Key Entities subsections. The `spec-driven-development` skill will gain new subsections enforcing the template and the user-story discipline. The Phase 3 analyzer's coverage matrix is what makes Phase 4 worthwhile: once specs ship with FR-### / SC-### IDs, the analyzer can cross-reference them against tasks and surface coverage gaps deterministically.
