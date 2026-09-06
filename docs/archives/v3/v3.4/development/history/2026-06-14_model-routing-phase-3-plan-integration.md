# Session History -- v3.4.0 model-routing Phase 3: /plan integration (planning-time routing)

**Date**: 2026-06-14
**Plan**: [`docs/releases/v3/v3.4/plans/model-routing.md`](../../plans/model-routing.md)
**Phase**: 3 of 4 -- `/plan` integration (planning-time routing)
**Branch**: `feat/model-routing` (off `develop`; no version tag cut this phase)
**Outcome**: complete; all Phase 3 sub-tasks closed and the Phase 3 exit checklist is satisfied.

## Goal

Make `/plan` assess every phase it generates and annotate the plan with a recommended model and reasoning effort per phase, platform-agnostically and degrading silently when routing is unavailable. Phase 3 folds the standalone routing capability (Phases 1-2) into the planning half of the Nexus-Hub loop. It is skill-native catalog + docs content only -- no new dependency, credential, remote registry, or third-party processor, and zero new outbound call (the only optional call remains Phase 1's key-gated Anthropic `GET /v1/models`).

## Subtasks completed

1. **3.1 -- Add a routing-assessment step to the plan workflow.** Added a new "Optional per-phase model-routing assessment (graceful degradation)" section to `catalog/commands/plan.md` (modeled on the existing dynamic-workflow-robustness section's tone, placed before `## Delegation`) and a new "Step 3.5: Assess Each Phase's Model (best-effort routing)" to the retained planning skill `catalog/skills/workflow/implementation-plan/SKILL.md` (between "Design the Phase Breakdown" and "Write the Plan"). Both invoke `[[model-routing]]` once per phase after the breakdown is fixed and before the file is written, default to the strongest tier on uncertainty, and degrade to the neutral `assess at implementation time` placeholder when routing or live enumeration is unavailable. `plan.md` stays a thin dispatcher; the heavy logic lives in the skill. There is no separate `generate-plan` skill folder in the catalog -- `implementation-plan` is the retained planning skill (its command entry point is `/generate-plan`), so it was the single skill edited.
2. **3.2 -- Extend the plan template to carry per-phase model recommendations.** In `implementation-plan/SKILL.md`, added a "Rec. model / effort" column to the "Phases at a Glance" table template and a `**Recommended model**` line to the per-phase header block (alongside `**Goal**` / `**Prerequisites**` / `**Stability Gate**`), each holding a platform-agnostic tier intent plus the concretely-enumerated model id + effort when available and a one-line rationale. Added an optional-friendly note so existing plans without the column still validate, a recommended-model item to the skill's Verification checklist, a `[[model-routing]]` entry to Related Skills, and bumped the skill footer to v1.4.0.
3. **3.3 -- Update platform-coverage docs and CHANGELOG.** Added a "Model Routing in the Plan/Implement Loop" subsection to `AGENTS.md` (after "Adding a New Command"; AGENTS.md had no prior `/plan`/loop section) describing the best-effort per-phase assessment, the template surfaces, graceful degradation, and the explicit statement that this is command + skill + docs behavior, NOT a `base-*.md` lockstep change. Added a `## [Unreleased]` -> `### Changed` CHANGELOG entry recording the same.
4. **3.4 -- Testing and stabilization.** Ran the full validate chain and both pytest suites directly (WN-v33-1). All gates green (see Test results). Confirmed the template additions are optional-friendly and the degradation path resolves to the neutral placeholder.

## Key decisions

- **Step 3.5 placement (after the breakdown, before the write).** The assessment must run once the phases exist to be scored but before the file is serialized, so it slots between "Design the Phase Breakdown" (Step 3) and "Write the Plan" (Step 4) rather than into the discovery interview. This mirrors the plan's "after the phase breakdown is designed and before the plan file is written" instruction exactly.
- **Tier intent recorded alongside the concrete model name.** The recommendation stores a platform-agnostic intent ("strong reasoning tier, high effort") next to the enumerated model id + effort, so it survives a platform switch between planning and implementation. This is the durable artifact Phase 4's `/implement` re-confirms against the then-current model set.
- **Optional-friendly template, not a hard schema.** The new column and field are additive: an existing plan generated before the column was added still validates, and a fresh plan whose routing assessment came back unavailable carries `assess at implementation time` rather than a fabricated model name. Plans are not parsed by a catalog validator, so "still validates" means the change introduces no structural break.
- **AGENTS.md gets a new subsection rather than editing a non-existent one.** The plan's 3.3 assumed a `/plan` surface / loop section in AGENTS.md; none existed, so a concise dedicated subsection was added after "Adding a New Command". Phase 4 extends the same subsection with the `/implement` re-confirmation and troubleshooting-loop upshift.
- **No edit to `model-routing` itself.** The wikilink `[[model-routing]]` resolves to the Phase 1 skill; a backlink from `implementation-plan` Related Skills was added (the planning skill now depends on it), but `model-routing`'s own body was left untouched to keep the change scoped to the `/plan` integration.

## Troubleshooting

None. The phase is pure catalog Markdown and prose; no defect surfaced during validation. The only validator output of note was the pre-existing unicode-safety warning baseline (em-dashes in the grandfathered `implementation-plan` body and the legacy AGENTS.md/CHANGELOG content) -- none of the warnings fall on lines added this phase (verified by line-range cross-check; the validator exits 0 on warnings).

## Test results

`make` is not on PATH on this Windows host (WN-v33-1), so the gate was emulated by invoking the validators, scanner, and pytest directly. All green:

- JSON integrity: `data/skills.json` parses (253 skills).
- Orphan-bundle audit (`validate_skills.py --bundles-only`): RESULT PASS, 0 errors / 0 warnings.
- Quality pass (`validate_skills.py --quality`): 0 errors, 1 warning -- the pre-existing `git-branching-workflow` 169-word `overview_l1` soft warning (WN-v33-2), not Phase 3 content.
- v2.3.0 CI validators (no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security) + solution-frontmatter: all exit 0. Every Phase 3 added line is ASCII- and personal-path-clean; the unicode warnings are a pre-existing baseline in grandfathered/legacy files.
- `check_version_sync.py`: all six surfaces match canonical 3.3.4 (this phase changed no version-carrying surface).
- Hook pytest suite (`catalog/hooks/tests/`): 439 passed, 7 pre-existing skips.
- Repo-level suite (`tests/` -- installer + integrations + validators): 415 passed.

## CI/CD edits

None. The phase edited catalog Markdown (`plan.md`, `implementation-plan/SKILL.md`) and repo docs (`AGENTS.md`, `CHANGELOG.md`, plan + known-gaps + this session history). The command file and skill directory auto-distribute via the installers' recursive copy, so no installer edit was required. No new script, hook, dependency, or `base-*.md` template was touched.

## Deviations

- **No separate `generate-plan` skill.** The plan's 3.1 references "the `generate-plan` skill it references"; the catalog has no such folder. `implementation-plan` is the retained planning skill (command entry point `/generate-plan`), so it was the single skill edited. Not a scope change -- the routing step landed in the correct retained skill.
- **AGENTS.md had no `/plan`/loop section to edit.** Added a concise new "Model Routing in the Plan/Implement Loop" subsection instead of editing a pre-existing one (see Key decisions). Surface reconciliation, not a scope change.

## Known gaps

See [`docs/releases/v3/v3.4/known-gaps.md`](../../known-gaps.md). Open: DF-v34-1 (Phase 1-2 helper unit-test residual, untouched this phase), WN-v33-1 (local `make`/ShellCheck unavailable; validators run directly -- re-confirmed for Phase 3), WN-v33-2 (benign pre-existing global-audit warnings outside this work). No new gaps introduced and none resolved this phase.

## Next steps

- **Phase 4 -- `/implement` integration (per-phase re-confirmation)**: make `/implement` re-run the routing assessment at the start of each phase (reading the Phase-3-written `**Recommended model**`, re-assessing against the currently-enumerated models, applying the confirm-then-auto-execute posture, and surfacing a delta when a newer/cheaper model now dominates), wire the troubleshooting-loop conditional upshift (upshift-only, never auto-downshift mid-phase), and update AGENTS.md + the interactive guide (`nexus-hub-guide.html` loop section) + CHANGELOG. As the plan's final phase, Phase 4 triggers release readiness via `/update release`.
