# Session History: v2.1.0 Phase 1 - Project Constitution + NEEDS CLARIFICATION Marker Discipline

**Date**: 2026-05-20
**Scope**: Phase 1 of [docs/archives/v2/v2.0/plans/adoption-spec-kit.md](../../../v2.0.0/plans/adoption-spec-kit.md)
**Outcome**: Foundation laid for the spec-driven-development adoption (G1 + G2 from the source comparison). New `project-constitution` skill, `/constitution` command, `catalog/templates/constitution-template.md`, and standardized `[NEEDS CLARIFICATION]` marker convention with 3-marker hard limit. All validation passes.
**Plan reference**: [docs/archives/v2/v2.0/plans/adoption-spec-kit.md](../../../v2.0.0/plans/adoption-spec-kit.md) Phase 1
**Source comparison**: [docs/archives/v2/v2.0/comparison-spec-kit.md](../../../v2.0.0/comparison-spec-kit.md) adoption candidates G1 and G2

## Goal recap

Ship the constitution-as-governance pattern end-to-end (skill + command + template) and standardize the `[NEEDS CLARIFICATION]` marker convention with a hard cap of 3 markers per artifact, prioritized by `scope > security/privacy > UX > technical`. The constitution becomes the project's highest-authority rulebook (downstream artifacts cite it), and the marker convention forces agents to surface uncertainty rather than guess. Both adoption candidates are skill-native per the MCP Registry Policy decision tree -- no new code, no new outbound calls, no new credentials, no new third-party data processors.

## Chronology by sub-task

### Sub-task 1.1 - Create `project-constitution` skill + `/constitution` command + constitution template

Created three new artifacts:

- `catalog/skills/workflow/project-constitution/SKILL.md` (159 lines) with required YAML frontmatter (`name`, `description`, `summary_l0`, `overview_l1`) and all required body sections (`When to Use This Skill`, `File Location`, `File Format`, `Instructions`, `Common Rationalizations`, `Verification`, `Related Skills`). Description follows the pushy-description rule from `AGENTS.md` (lists trigger phrases verbatim plus a SKIP clause covering CLAUDE.md / AGENTS.md edits, single-feature READMEs, one-decision ADRs, and commit-message conventions). Body explains:
    - What a project constitution is (versioned governance file with MUST / SHOULD principles).
    - Where it lives (recommended: `docs/<version>/constitution.md`; acceptable: `CONSTITUTION.md` at root).
    - How it differs from CLAUDE.md / AGENTS.md (project-principles vs. agent-instructions).
    - The amendment workflow (SemVer applied to principles: MAJOR for removals or redefinitions, MINOR for additions, PATCH for clarifications).
    - The Sync Impact Report HTML comment emitted at the top of the file on every edit.
    - The Constitution Check gate that Phase 2 wires into `/generate-plan`.
    - Cross-links via `[[name]]` syntax to `spec-driven-development`, `architecture-decision-record`, `implementation-plan`, `ambiguity-detector`, `idea-refine`, and `known-gaps-tracker`.

- `catalog/commands/constitution.md` (no `speckit.` prefix per the Nexus-Hub unprefixed-commands convention). Seven-step flow: resolve constitution location, collect or derive placeholder values, draft the constitution, run the propagation check, emit the Sync Impact Report, validate, write. Three invocation modes: `/constitution` (interactive author or amend), `/constitution amend` (explicit amend mode), `/constitution check <plan-path>` (read-only Constitution Check shorthand). Nexus-Hub-native framing throughout per the Reverse-Engineering Attribution Rule -- no upstream attribution in the user-facing artifact.

- `catalog/templates/constitution-template.md` (new top-level `catalog/templates/` directory created -- prior version had no templates folder). Skeleton with the Sync Impact Report HTML comment placeholder, the four header fields (Project, Version, Ratified, Last Amended), the Preamble, three example principle subsections each with Statement / Rationale / Applies to (extensible up to 7), two optional sections (Section 2: Operational Standards, Section 3: Quality Bars), Governance, and Versioning. `[ALL_CAPS_IDENTIFIER]` placeholders are bracketed for the validator to detect any that were not filled in.

Then updated the three data registries per the rule in `AGENTS.md`:

- `data/SKILL_INDEX.md`: added the `project-constitution` row and bumped the total from 203 to 204 (across 22 categories).
- `data/skills.json`: added the new skill entry following the established schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security). Bumped `statistics.total_skills` from 196 to 197 and `statistics.categories.workflow` from 19 to 20.
- `data/marketplace.json`: bumped the workflow category `skill_count` from 21 to 22 and updated the category description to include "project governance".

### Sub-task 1.2 - Standardize `[NEEDS CLARIFICATION]` marker convention with 3-marker hard limit

Updated three existing skills, each with a body-only edit (no frontmatter or registry changes):

- `catalog/skills/developer-experience/spec-driven-development/SKILL.md`: added subsection "Marking uncertainty with `[NEEDS CLARIFICATION]`" under "When to Use This Skill". Cites the priority order verbatim ("scope > security/privacy > UX > technical"), states the hard limit ("Maximum 3 markers total"), explains the rationale ("forces prioritization; markers above the cap demote to assumptions with informed defaults"), includes before / after examples (a vague unmarked statement; a specific marker within the cap with priority justification; a candidate ambiguity demoted to an explicit assumption), and cross-links via `[[name]]` syntax to `ambiguity-detector` and `idea-refine`.

- `catalog/skills/developer-experience/ambiguity-detector/SKILL.md`: added subsection "Step 7: Emit `[NEEDS CLARIFICATION]` Markers Aligned with the Project Convention" after "Step 6: Generate the Ambiguity Report" and before "Best Practices". Explains how the detector's output flows back into the spec text using the standardized marker rather than free-form prose, requires inline placement (not separated into an end-of-spec block), and adds a `Priority:` annotation pattern for the markers that earn a slot under the cap. Cross-links to `spec-driven-development` and `idea-refine`.

- `catalog/skills/developer-experience/idea-refine/SKILL.md`: added a paragraph under "Step 5: Identify Open Questions" that cross-links to the convention and clarifies the refinement should produce no more than 3 outstanding markers, with the rest resolved via informed defaults. Cross-links to `spec-driven-development` and `ambiguity-detector`.

### Sub-task 1.3 - Phase 1 testing and stabilization

Ran the verification suite per the plan's prompt:

- `python scripts/validate_skills.py --bundles-only` -- 0 errors, 0 warnings across 208 skills (the bundle audit covers the new `project-constitution` directory which ships only `SKILL.md` with no bundled subdirectories, so no orphan-warning risk).
- `python scripts/validate_skills.py --path catalog/skills/workflow/project-constitution` -- 0 errors, 5 warnings (missing optional `author` / `version` / `category` / `license` / `tags` frontmatter fields; identical to the sibling `known-gaps-tracker` skill's warning profile -- this is the established baseline, not a regression introduced by Phase 1).
- The three updated existing skills (`spec-driven-development`, `ambiguity-detector`, `idea-refine`) each return 0 errors with the same 5 baseline warnings (no new warnings introduced by the body edits).
- All five JSON files in `data/` parse cleanly with UTF-8 encoding (`skills.json` 204 entries, `bundles.json` 15, `workflows.json` 17, `templates.json`, `marketplace.json`).
- Read the new skill end-to-end: all required sections present, description follows the pushy-description rule (trigger phrases verbatim + SKIP clause), `summary_l0` and `overview_l1` are properly-quoted strings.
- Authored an end-to-end constitution document at `scratch/constitution-test.md` (Nexus-Hub project, version 1.0.0, three principles: Reverse-Engineer Before Wrapping / Cross-Platform Parity / Pushy-Description Triggering, with full Governance and Versioning sections). Verified via inline Python check: Sync Impact Report HTML comment at the top, all four header fields populated, ISO Ratified and Last Amended dates, all principle subsections complete (Statement / Rationale / Applies to per principle), Governance and Versioning sections present, no leftover `[ALL_CAPS_IDENTIFIER]` placeholders. All 12 structural checks passed. Scratch file then deleted per the verification spec.

## Troubleshooting log

- `make` is not on `PATH` on Windows; ran the underlying `python -c` invocations and `python scripts/validate_skills.py` directly per the `Makefile` `validate` target. Outcome: same gates exercised, all clean. Tracked as a known-environment constraint, not a Phase 1 deviation.
- Surfaced a pre-existing inconsistency in `data/skills.json` `statistics.total_skills` (now reads 197 after my +1 increment, but the actual array length is 204). The drift predates v2.0.0 -- the statistics block was reading 196 when the array already held 203 entries. Phase 1's edit faithfully applied the prescribed `+1` increment; the underlying drift is out of scope for this phase. Recorded as `WN-1` in `docs/archive/v2/v2.1/known-gaps.md` for Phase 8 release stabilization to repair via `make build-catalog` (the builder script was confirmed clean of `DevAI` literals in v2.0.0 BG-001, so it should now produce a faithful catalog when rebuilt).

## Cross-cutting constraints applied

- **Reverse-Engineering Attribution Rule**: no spec-kit, github/spec-kit, or upstream-file-path attribution in any of the three new artifacts. The comparison report at `docs/archive/v2/v2.0/comparison-spec-kit.md` carries the attribution; the distributed artifacts use generic descriptive names.
- **Slash-command prefix**: `/constitution` is unprefixed; no `/speckit.constitution`.
- **Cross-platform parity**: no new shell scripts introduced in Phase 1, so the `.sh` / `.ps1` parity rule does not apply.
- **Installer-Aware Changes**: no new files under `scripts/`; the new skill, command, and template land in folders already copied recursively by the installer. No installer edit required for Phase 1.
- **Data registry consistency**: all three registries updated per the rule.
- **ASCII-only documentation**: no em-dashes, en-dashes, curly quotes, or ellipsis characters in any artifact. The skill and template use hyphens, straight quotes, and `...` consistently.
- **Pushy-description rule**: the new skill description lists trigger phrases verbatim ("draft a constitution", "ratify principles", "project governance", "MUST rules", "set the ground rules", "amend the constitution", "what are our non-negotiables", "principle 4 says...", "constitution check") and ends with a SKIP clause.

## Quality gates

| Gate | Threshold | Status |
|---|---|---|
| All tests passing | 0 failures | N/A (no test code added in Phase 1) |
| Line coverage | >= 80% | N/A (no test code added in Phase 1) |
| Lint errors | 0 errors | PASS (no shell scripts added; no linter-relevant code touched) |
| Build / compile | Succeeds | PASS (validators clean) |
| Skill-bundle audit | 0 errors | PASS (0 errors, 0 warnings across 208 skills) |
| New skill full validator | 0 errors | PASS (0 errors, 5 baseline warnings matching sibling-skill profile) |
| Three updated skills validator | 0 errors | PASS (each returns 0 errors, 5 baseline warnings) |
| JSON data integrity | All files parse | PASS (all 5 files parse cleanly with UTF-8 encoding) |
| End-to-end constitution authoring | Structural checks pass | PASS (12 / 12 checks on `scratch/constitution-test.md`) |

## Files written or modified

**Created**:

- `catalog/skills/workflow/project-constitution/SKILL.md`
- `catalog/commands/constitution.md`
- `catalog/templates/constitution-template.md` (new top-level `catalog/templates/` directory)
- `docs/archive/v2/v2.1/known-gaps.md` (status `in-progress`, single WN-1 entry)
- `docs/archive/v2/v2.1/development/history/2026-05-20_phase-1-project-constitution.md` (this file)

**Modified**:

- `data/SKILL_INDEX.md` (one new row; total 203 -> 204)
- `data/skills.json` (one new entry; `total_skills` 196 -> 197; workflow category 19 -> 20)
- `data/marketplace.json` (workflow category `skill_count` 21 -> 22; description gained "project governance")
- `catalog/skills/developer-experience/spec-driven-development/SKILL.md` (new subsection on `[NEEDS CLARIFICATION]` markers)
- `catalog/skills/developer-experience/ambiguity-detector/SKILL.md` (new Step 7 on emitting markers aligned with the convention)
- `catalog/skills/developer-experience/idea-refine/SKILL.md` (new paragraph cross-linking to the convention)
- `docs/DEVLOG.md` (Phase 1 entry prepended at the top)

## Known gaps recorded

- `WN-1` -- `data/skills.json` statistics block out of sync with actual skills array (pre-existing drift; out of Phase 1 scope; scheduled for Phase 8 sub-task 8.1 to repair via `make build-catalog`).

## Next steps

- Phase 2 -- wire the constitution into the plan-generation workflow as a Constitution Check gate. `/generate-plan` will gain a Constitution Check section near the top of every produced plan and a Complexity Tracking table near the end. Gate runs before Phase 0 research and re-checks after Phase 1 design.
- Phase 3 -- the cross-artifact `/analyze-spec` command will consume the constitution (when present) as one of its inputs for the Constitution Alignment detection pass.
