# Plan -- Spec-Kit Adoption (v2.1.0 + v2.2.0+)

**Project**: Nexus-Hub
**Version**: v2.0.0 (plan output location; targeted releases are v2.1.0 and v2.2.0+)
**Slug**: adoption-spec-kit
**Plan Type**: Feature/Enhancement (additive adoption of conventions, templates, and one refactor)
**Created**: 2026-05-20
**Source comparison**: [../comparison-spec-kit.md](../comparison-spec-kit.md)
**Scope filter**: all (P0 + P1 + P2 + P3 + G12 re-full)
**Sequencing mode**: reverse-engineer-first (MCP Registry Policy default)
**Goal**: Adopt 12 capabilities from GitHub Spec Kit into Nexus-Hub -- 11 skill-native items shipping as v2.1.0, 4 P3 polish items shipping as v2.1.x patches, and 1 re-full installer refactor (G12) shipping as v2.2.0.

## Overview

This plan operationalizes the adoption candidates identified in [comparison-spec-kit.md](../comparison-spec-kit.md). Spec Kit is GitHub's open-source toolkit for Spec-Driven Development (SDD); Nexus-Hub already has overlapping skills (`spec-driven-development`, `idea-refine`, `ambiguity-detector`, `generate-plan`, `quality-gate-definitions`) but lacks the gating discipline, the project-governance file, and the cross-artifact analyzer that make SDD enforceable rather than aspirational. The adoption is structured as additive conventions, templates, and commands -- no breaking changes to existing skills.

**Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale.** All 11 Bucket A items (G1-G11) are classified `skill-native` per the policy: they ship as new commands, new skills, and updates to existing skill bodies -- no new code, no new outbound calls, no new credentials, no new third-party data processors. The single re-full item (G12 Integration Registry pattern) is a Python refactor of Nexus-Hub's own installer template logic -- still no external dependency, but substantially larger in scope. It lands in its own phase targeted at v2.2.0.

**Prior-version known-gaps ingest**: v1.1.5 is the immediately prior version; its `known-gaps.md` is finalized. The 5 still-open `DF-*` / `QG-001` / `MT-1` items concern cross-OS installer dry-run verification and are orthogonal to spec-kit adoption -- they are explicitly out of scope for this plan and remain tracked in `docs/archive/v1/v1.1/known-gaps.md` for a future CI-matrix plan.

**Out of scope for this plan**: anything outside the 12 spec-kit adoption candidates -- including the cross-OS installer dry-run items above. The four P3 polish items (methodology essay, devcontainer, `.markdownlint-cli2.jsonc`, installer path-traversal test) are *in* scope as Phase 9 but may slip to v2.1.x patches without blocking v2.1.0.

## Phases at a Glance

| Phase | Title | Outcome | Target release |
|-------|-------|---------|----------------|
| 1 | Foundation - Constitution + clarification marker discipline | New `/constitution` command, new `project-constitution` skill, `constitution-template.md`, and standardized `[NEEDS CLARIFICATION]` marker convention with 3-marker hard limit | v2.1.0 |
| 2 | Constitution Check gate in `/generate-plan` | `/generate-plan` output gains Constitution Check + Complexity Tracking sections that pass before Phase 0 research and re-check after Phase 1 design | v2.1.0 |
| 3 | Cross-artifact spec analyzer | New `/analyze-spec` command + skill: read-only cross-artifact consistency / coverage / ambiguity analyzer with severity-tagged findings table | v2.1.0 |
| 4 | Spec template upgrade - user stories + requirement IDs | `spec-driven-development` skill + new `spec-template.md` enforce P1/P2/P3 user-story priorities, Independent Test criteria, FR-###/SC-### IDs with coverage matrix | v2.1.0 |
| 5 | Clarification loop + spec quality checklist | New `/clarify-spec` command (sequential 5-question loop with recommended-option table) + auto-generated `spec-quality-checklist.md` invoked at end of specify | v2.1.0 |
| 6 | Task discipline - `[P]/[US#]` labels + phase organization | `/generate-plan` emits tasks in the strict `- [ ] T### [P?] [US?] file_path` format, organized by user story with MVP-first phasing | v2.1.0 |
| 7 | Feature directories + GitHub issues conversion | Opt-in `specs/<NNN>-<slug>/` layout for `/generate-plan`; new `/tasks-to-issues` command driving `gh issue create` | v2.1.0 |
| 8 | v2.1.0 release stabilization | `make validate` + `make lint` + `make test` pass; CHANGELOG.md and RELEASE_NOTES.md authored; data registries updated; installer smoke verified | v2.1.0 ship |
| 9 | P3 polish - methodology essay, devcontainer, markdownlint config, installer test | `docs/archive/v2/v2.1/spec-driven-methodology.md`, `.devcontainer/`, `catalog/style-guides/markdownlint-cli2.jsonc`, `tests/installer/test_registrar_path_traversal.py` | v2.1.x patches |
| 10 | Integration Registry refactor (re-full) | Python class hierarchy (`IntegrationBase` -> Markdown / TOML / YAML / Skills) replacing lock-step `base-*.md` template editing; one subclass per supported agent | v2.2.0 |

---

## Phase 1: Foundation - Constitution + Clarification Marker Discipline

**Goal**: Establish the project-governance file (constitution) and the `[NEEDS CLARIFICATION]` marker convention that downstream phases reference.
**Prerequisites**: None.
**Stability Gate**: `/constitution` command runs end-to-end on a throwaway test project and produces `docs/archive/v2/v2.0/constitution.md`; all three target skills (`spec-driven-development`, `ambiguity-detector`, `idea-refine`) reference the new marker convention and the 3-marker hard limit in their bodies; `make validate` passes.

### Sub-tasks

#### 1.1 -- Create `project-constitution` skill + `/constitution` command + constitution template

**Objective**: Ship the constitution-as-governance pattern (adoption candidate G1) end-to-end: skill, command, and template. The constitution is a versioned MUST/SHOULD document of project principles, distinct from CLAUDE.md (agent-instructions).

**Prompt**:
> Create three new artifacts implementing adoption candidate G1 from `docs/archive/v2/v2.0/comparison-spec-kit.md`:
>
> 1. New skill at `catalog/skills/workflow/project-constitution/SKILL.md` with required YAML frontmatter (`name`, `description`, `summary_l0`, `overview_l1`) and required body sections (`When to Use This Skill`, `Instructions`, `Common Rationalizations`, `Verification`, `Related Skills`). Description follows the "pushy" rule from `AGENTS.md` (lists trigger phrases verbatim + a SKIP clause). The body explains: what a project constitution is (versioned governance file with MUST/SHOULD principles), where it lives (`docs/<version>/constitution.md` or root `CONSTITUTION.md` -- author MUST recommend `docs/<version>/constitution.md` to align with Nexus-Hub's versioned-docs convention), how it differs from CLAUDE.md (agent-instructions vs. project-principles), the amendment workflow (detect old version, increment per SemVer: MAJOR for removals, MINOR for additions, PATCH for clarifications; emit a Sync Impact Report at the top of the file as an HTML comment listing version-change, modified principles, added/removed sections, templates requiring updates).
> 2. New command at `catalog/commands/constitution.md` (no `speckit.` prefix; Nexus-Hub uses unprefixed commands per Section 13 of the comparison report). Body adapts `templates/commands/constitution.md` from Spec Kit (do not name the upstream repo in the artifact per the Reverse-Engineering Attribution Rule in `AGENTS.md`). Steps: collect/derive placeholder values, draft updated constitution content, run propagation checklist (read `catalog/commands/generate-plan.md` + `catalog/templates/spec-template.md` (created in Phase 4) + any other constitution-aware templates and verify alignment), emit Sync Impact Report, validate, write.
> 3. New template at `catalog/templates/constitution-template.md` adapted from `templates/constitution-template.md` (5 principle slots with example comments, Section 2 / Section 3 slots, Governance section, version line with Ratified / Last Amended dates). Generic Nexus-Hub framing; no spec-kit attribution.
>
> Then update three data registries per the rule in `AGENTS.md`: add the new skill row to `data/SKILL_INDEX.md`, the skill entry to `data/skills.json`, and increment `data/marketplace.json` `total_skills` + category count.
>
> Run `make validate`. Confirm zero errors and zero new orphan warnings (the new skill ships only `SKILL.md`, no bundled subdirs).

#### 1.2 -- Standardize `[NEEDS CLARIFICATION]` marker convention with 3-marker hard limit

**Objective**: Implement adoption candidate G2. The marker is a prose convention that forces agents to surface uncertainty rather than guess; the 3-marker limit forces prioritization by impact (scope > security/privacy > UX > technical).

**Prompt**:
> Update the bodies of three existing skills to standardize on the `[NEEDS CLARIFICATION: <specific question>]` marker convention with a hard limit of 3 markers, prioritized by `scope > security/privacy > UX > technical`. Source reference: `templates/commands/specify.md` lines 117-131 and 188-227 in the spec-kit repo (do not link upstream URL; this is a convention adoption per the Reverse-Engineering Attribution Rule in `AGENTS.md`).
>
> 1. `catalog/skills/developer-experience/spec-driven-development/SKILL.md`: add a new subsection under "When to Use This Skill" titled "Marking uncertainty with `[NEEDS CLARIFICATION]`" that explains the marker, the 3-marker hard limit with priority order, and the rule "make informed guesses for the rest" (document assumptions in an Assumptions section). Include before/after examples.
> 2. `catalog/skills/developer-experience/ambiguity-detector/SKILL.md`: add a new subsection in the body that aligns the skill's output with the marker convention -- when ambiguity is detected, emit the standardized marker rather than free-form prose.
> 3. `catalog/skills/developer-experience/idea-refine/SKILL.md`: add a cross-reference to the marker convention; clarify that refinement of vague ideas should produce no more than 3 outstanding markers, with the rest resolved via informed defaults.
>
> Each update must:
> - Cite the priority order verbatim: "scope > security/privacy > UX > technical"
> - Include the hard limit ("Maximum 3 markers total") with the rationale ("forces prioritization; markers above the cap demote to assumptions with informed defaults")
> - Use the `[[name]]` link syntax from `AGENTS.md` memory-file conventions to cross-link the three skills together
>
> Run `make validate`. The updates are body-only; no frontmatter or registry changes.

#### 1.3 -- Phase 1 testing and stabilization

**Objective**: Verify the new skill and command run end-to-end and that no existing skill broke.

**Prompt**:
> Run the Phase 1 verification suite:
> 1. `make validate` must pass with zero errors.
> 2. `make lint` must pass with no new ShellCheck warnings.
> 3. Read `catalog/skills/workflow/project-constitution/SKILL.md` end-to-end and confirm all required sections are present, the description follows the pushy-description rule, and `summary_l0` / `overview_l1` are quoted strings.
> 4. Simulate the `/constitution` command flow on a throwaway scratch file (`scratch/constitution-test.md`): provide three principles, generate the file, verify the Sync Impact Report HTML comment appears at the top, verify dates are ISO format, verify no `[ALL_CAPS_IDENTIFIER]` placeholders remain.
> 5. Verify the three skills updated in sub-task 1.2 still pass `python scripts/validate_skills.py --path <each>` with zero errors.
> 6. Delete the scratch file.
> 7. After all checks pass, run `/generate-session-history` to document Phase 1.

### Phase 1 Exit Checklist

- [ ] `catalog/skills/workflow/project-constitution/SKILL.md` exists with valid frontmatter and all required sections
- [ ] `catalog/commands/constitution.md` exists
- [ ] `catalog/templates/constitution-template.md` exists
- [ ] `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` updated
- [ ] Three existing skills updated with `[NEEDS CLARIFICATION]` marker convention
- [ ] `make validate` passes with zero errors
- [ ] Session history generated

---

## Phase 2: Constitution Check Gate in `/generate-plan`

**Goal**: Wire the constitution from Phase 1 into the plan-generation workflow as a gate that must pass before Phase 0 research and be re-checked after Phase 1 design.
**Prerequisites**: Phase 1.
**Stability Gate**: A test invocation of `/generate-plan` on a scratch goal produces a plan that includes a Constitution Check section near the top and a Complexity Tracking table near the end; the gate triggers a re-check note after the design phase.

### Sub-tasks

#### 2.1 -- Add Constitution Check + Complexity Tracking to `/generate-plan` output

**Objective**: Implement adoption candidate G11. Plans must declare alignment with the project constitution before research and re-affirm after design; violations must be justified in a Complexity Tracking table.

**Prompt**:
> Update `catalog/commands/generate-plan.md` to add two new template sections that the generated plan file MUST include after Step 4 (Generate the Plan File):
>
> 1. **Constitution Check** section, placed immediately after the plan's `## Overview` and before `## Phases at a Glance`. Template:
>
>    ```
>    ## Constitution Check
>
>    *GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
>
>    [List each MUST principle from docs/<version>/constitution.md and state PASS / FAIL / N/A per principle, with a one-sentence justification. If constitution.md does not exist, state "No constitution file found at docs/<version>/constitution.md -- skipping check. Recommend running /constitution to establish project principles." -- this is informational, not blocking.]
>    ```
>
> 2. **Complexity Tracking** section, placed near the end of the plan file (before the Phase N Exit Checklist of the last phase). Template:
>
>    ```
>    ## Complexity Tracking
>
>    > **Fill ONLY if Constitution Check has violations that must be justified**
>
>    | Violation | Why Needed | Simpler Alternative Rejected Because |
>    |-----------|------------|-------------------------------------|
>    | [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
>    ```
>
> Update the command's "How to Run This Command" section to mention that when a constitution file exists, the generated plan will surface the check; when it does not, the plan emits the informational note above. Both behaviors are non-blocking by design (the constitution itself is opt-in).
>
> Also update `catalog/skills/workflow/implementation-plan/SKILL.md` (or whichever skill drives the generate-plan flow) with the same two template sections in its body, with a cross-link `[[project-constitution]]` to the Phase 1 skill.
>
> Run `make validate`.

#### 2.2 -- Phase 2 testing and stabilization

**Objective**: Verify a generated plan includes both new sections regardless of whether a constitution file exists.

**Prompt**:
> Run the Phase 2 verification suite:
> 1. Create a throwaway `scratch/test-constitution.md` with three MUST principles.
> 2. Simulate `/generate-plan` on a small scope ("Add a `/hello` command that prints `world`") and verify the produced plan includes both the Constitution Check section (with PASS/FAIL/N/A per principle) and the Complexity Tracking table.
> 3. Delete the scratch constitution file and re-run the simulation; verify the Constitution Check section emits the informational "no constitution file found" note instead of failing.
> 4. Delete both scratch files.
> 5. `make validate` must pass.
> 6. Run `/generate-session-history` to document Phase 2.

### Phase 2 Exit Checklist

- [ ] `catalog/commands/generate-plan.md` emits Constitution Check + Complexity Tracking sections
- [ ] Behavior is correct both with and without a constitution file
- [ ] `make validate` passes
- [ ] Session history generated

---

## Phase 3: Cross-Artifact Spec Analyzer

**Goal**: Ship the read-only `/analyze-spec` command that cross-checks spec / plan / tasks artifacts for duplication, ambiguity, underspecification, constitution-misalignment, and coverage gaps.
**Prerequisites**: Phase 1 (for constitution alignment check).
**Stability Gate**: `/analyze-spec` runs on a sample feature directory and produces a severity-tagged findings table (CRITICAL / HIGH / MEDIUM / LOW) plus a coverage summary; the command modifies no files (read-only).

### Sub-tasks

#### 3.1 -- Create `/analyze-spec` command

**Objective**: Implement adoption candidate G4. Cross-artifact consistency analyzer that detects duplication, ambiguity, underspecification, constitution-misalignment, and coverage gaps across spec.md + plan.md + tasks.md.

**Prompt**:
> Create a new command at `catalog/commands/analyze-spec.md` adapted from `templates/commands/analyze.md` in the spec-kit repo (do not name the upstream; use Nexus-Hub framing per the Reverse-Engineering Attribution Rule).
>
> Command behavior (read-only; never modifies files):
>
> 1. Accept a feature directory path as argument (default: latest under `docs/<version>/plans/` or `specs/<NNN>-*/` if that layout exists from Phase 7).
> 2. Load minimal context from each artifact:
>    - `spec.md`: Overview, Functional Requirements, Success Criteria, User Stories, Edge Cases
>    - `plan.md`: Architecture, Data Model references, Phases, Technical constraints
>    - `tasks.md`: Task IDs, Descriptions, Phase grouping, `[P]` parallel markers, file paths
>    - Constitution file from Phase 1 if it exists at `docs/<version>/constitution.md`
> 3. Run six detection passes: Duplication, Ambiguity (vague adjectives + unresolved placeholders), Underspecification, Constitution Alignment, Coverage Gaps (requirements without tasks; tasks without requirements; success criteria requiring buildable work but not reflected in tasks), Inconsistency (terminology drift, conflicting requirements, ordering contradictions).
> 4. Assign severity per the heuristic: CRITICAL (constitution MUST violation, zero-coverage core requirement), HIGH (duplicates, ambiguous security/performance, untestable acceptance), MEDIUM (terminology drift, missing non-functional task coverage), LOW (style/wording).
> 5. Emit a compact Markdown report with three tables: Findings (50-row cap with overflow summary), Coverage Summary (Requirement Key | Has Task? | Task IDs | Notes), Metrics (Total Requirements, Total Tasks, Coverage %, Ambiguity Count, Duplication Count, Critical Issues Count). Append Next Actions and Offer Remediation steps.
> 6. End by stating explicitly: "This analyzer is read-only. It modifies no files. Any remediation requires user approval."
>
> Also create a companion skill at `catalog/skills/code-review/cross-artifact-analyzer/SKILL.md` with the required frontmatter + body sections (When to Use, Instructions, Common Rationalizations, Verification, Related Skills). Cross-link to `[[project-constitution]]` and `[[ambiguity-detector]]`.
>
> Update three data registries (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) for the new skill.
>
> Run `make validate`.

#### 3.2 -- Phase 3 testing and stabilization

**Objective**: Verify the analyzer produces a stable report from a known-good feature directory.

**Prompt**:
> Run the Phase 3 verification suite:
> 1. Pick an existing feature directory in the repo to use as test input. Either use `docs/archive/v2/v2.0/plans/nexus-hub-rename.md` as a self-contained mini spec+plan (no separate spec.md), or scaffold a throwaway `scratch/feat-test/` with a spec.md (3 FR-### + 2 SC-###), plan.md (2 phases), tasks.md (5 tasks with `[P]/[US#]` labels manually authored).
> 2. Simulate `/analyze-spec` on the test directory. Verify the output includes: Findings table with stable IDs prefixed by category initial (A1 for ambiguity, D1 for duplication, etc.); Coverage Summary table; Metrics block.
> 3. Run `/analyze-spec` a second time on the same directory and confirm finding IDs are stable across reruns (determinism is part of the contract).
> 4. Delete any scratch files created.
> 5. `make validate` must pass.
> 6. Run `/generate-session-history` to document Phase 3.

### Phase 3 Exit Checklist

- [ ] `catalog/commands/analyze-spec.md` exists and command behavior matches the spec
- [ ] `catalog/skills/code-review/cross-artifact-analyzer/SKILL.md` exists with valid frontmatter
- [ ] Data registries updated
- [ ] Findings are deterministic across reruns
- [ ] `make validate` passes
- [ ] Session history generated

---

## Phase 4: Spec Template Upgrade - User Stories + Requirement IDs

**Goal**: Upgrade `spec-driven-development` skill + ship `spec-template.md` to enforce P1/P2/P3 user-story priorities, Independent Test criteria, and FR-###/SC-### identifier schemes with coverage matrix.
**Prerequisites**: Phase 3 (analyzer will consume the new ID scheme).
**Stability Gate**: A test spec authored against the new template successfully passes through `/analyze-spec` with the new coverage matrix populated (FR/SC IDs cross-referenced against tasks).

### Sub-tasks

#### 4.1 -- Ship `catalog/templates/spec-template.md`

**Objective**: Implement the spec template with user stories (P1/P2/P3), Independent Test criteria per story, FR-###/SC-### IDs, and a Key Entities subsection.

**Prompt**:
> Create `catalog/templates/spec-template.md` adapted from `templates/spec-template.md` in the spec-kit repo (Nexus-Hub framing; no upstream attribution in the artifact per the Reverse-Engineering Attribution Rule).
>
> Required sections (in order):
>
> 1. Header block: Feature Specification name, Feature Branch slot, Created date slot, Status (Draft / Reviewed / Approved), Input ("User description: `$ARGUMENTS`")
> 2. `## User Scenarios & Testing *(mandatory)*` with HTML-comment guidance ("User stories should be PRIORITIZED as user journeys ordered by importance. Each user story/journey must be INDEPENDENTLY TESTABLE -- if you implement just ONE of them, you should still have a viable MVP")
> 3. `### User Story 1 - [Brief Title] (Priority: P1)` template with `**Why this priority**:`, `**Independent Test**:`, `**Acceptance Scenarios**:` (Given/When/Then format). Repeat for P2, P3.
> 4. `### Edge Cases` subsection
> 5. `## Requirements *(mandatory)*` with `### Functional Requirements` using FR-001, FR-002, ... IDs in `**FR-###**: System MUST <capability>` format. Include example NEEDS CLARIFICATION usage.
> 6. `### Key Entities *(include if feature involves data)*`
> 7. `## Success Criteria *(mandatory)*` with `### Measurable Outcomes` using SC-001, SC-002, ... IDs. Guidance: Measurable, Technology-agnostic, User-focused, Verifiable.
> 8. `## Assumptions` subsection
>
> Section requirements: Mandatory must be completed; Optional include only when relevant; When a section doesn't apply, remove it entirely (don't leave as "N/A").
>
> Then update `catalog/skills/developer-experience/spec-driven-development/SKILL.md`:
> - Add a new subsection in the body titled "Spec template" that points to `catalog/templates/spec-template.md` and explains the FR-###/SC-### convention.
> - Add a subsection titled "User stories with priorities" that enforces P1/P2/P3, Independent Test criteria, and the MVP rule (implementing just P1 must deliver value).
> - Add Common Rationalizations rebuttals for "I'll just use bullet points instead of FR/SC IDs" (rebut: IDs enable coverage matrix in `/analyze-spec`) and "this feature only has one user story" (rebut: still write it as User Story 1 with priority P1 so analyzer can find it).
>
> Run `make validate`.

#### 4.2 -- Phase 4 testing and stabilization

**Objective**: Verify the template + skill update enable the analyzer's coverage matrix.

**Prompt**:
> Run the Phase 4 verification suite:
> 1. Author a 1-page test spec at `scratch/test-spec.md` using the new template: 2 user stories (P1, P2) each with Independent Test criteria, 3 functional requirements (FR-001, FR-002, FR-003), 2 success criteria (SC-001, SC-002).
> 2. Author a minimal `scratch/test-plan.md` and `scratch/test-tasks.md` referencing FR-001 in 2 tasks, FR-002 in 1 task, FR-003 in 0 tasks (intentional gap), SC-001 in 1 task, SC-002 in 0 tasks (intentional gap).
> 3. Run `/analyze-spec` (built in Phase 3) on `scratch/`. Confirm the Coverage Summary table identifies FR-003 and SC-002 as "Has Task? = No" with severity HIGH.
> 4. Delete scratch files.
> 5. `make validate` must pass.
> 6. Run `/generate-session-history` to document Phase 4.

### Phase 4 Exit Checklist

- [ ] `catalog/templates/spec-template.md` exists with all 8 required sections
- [ ] `spec-driven-development` skill body updated with template + user-story discipline
- [ ] Common Rationalizations include FR/SC-ID and single-story rebuttals
- [ ] `/analyze-spec` coverage matrix populates correctly from new spec format
- [ ] `make validate` passes
- [ ] Session history generated

---

## Phase 5: Clarification Loop + Spec Quality Checklist

**Goal**: Ship the sequential 5-question clarification loop (with recommended-option tables) and the auto-generated spec quality checklist ("unit tests for English").
**Prerequisites**: Phase 1 (NEEDS CLARIFICATION discipline established), Phase 4 (spec template provides the surface to clarify against).
**Stability Gate**: A scratch ambiguous spec is run through `/clarify-spec`, produces 5 prioritized questions with recommended options, integrates accepted answers back into a `## Clarifications` section, and emits the new spec-quality-checklist.md.

### Sub-tasks

#### 5.1 -- Create `/clarify-spec` command with sequential 5-question loop

**Objective**: Implement adoption candidate G3. Detect ambiguity using a 10-category taxonomy (Functional Scope, Domain & Data Model, Interaction & UX Flow, Non-Functional Quality Attributes, Integration & External Dependencies, Edge Cases & Failure Handling, Constraints & Tradeoffs, Terminology & Consistency, Completion Signals, Misc / Placeholders). Ask one question at a time with a Recommended option highlighted at the top, options rendered as a Markdown table, and accepted answers integrated back into the spec.

**Prompt**:
> Create `catalog/commands/clarify-spec.md` adapted from `templates/commands/clarify.md` (Nexus-Hub framing; no upstream attribution per the Reverse-Engineering Attribution Rule).
>
> Required behavior:
>
> 1. Load the current spec file (default: latest under `docs/<version>/plans/` or `specs/<NNN>-*/spec.md`). Abort with a guidance message if no spec is found.
> 2. Perform a structured ambiguity scan using a 10-category taxonomy: Functional Scope & Behavior, Domain & Data Model, Interaction & UX Flow, Non-Functional Quality Attributes (Performance / Scalability / Reliability / Observability / Security & Privacy / Compliance), Integration & External Dependencies, Edge Cases & Failure Handling, Constraints & Tradeoffs, Terminology & Consistency, Completion Signals, Misc / Placeholders. Mark status Clear / Partial / Missing per category.
> 3. Generate (internally) a prioritized queue of at most 5 candidate questions, balanced across high-impact unresolved categories. Each question must be answerable with EITHER a 2-5 option multiple choice OR a short-phrase answer (<=5 words).
> 4. Sequential questioning loop: present EXACTLY ONE question at a time. For multiple-choice: analyze options, pick the most suitable, present `**Recommended:** Option [X] - <reasoning>` at the top, then render all options in a Markdown table. End with "Reply with the option letter, accept the recommendation with 'yes' or 'recommended', or provide your own short answer."
> 5. After each accepted answer: maintain the spec in memory, ensure a `## Clarifications` section exists with `### Session YYYY-MM-DD` subheading, append `- Q: <question> -> A: <final answer>`, then immediately apply the clarification to the appropriate section(s) of the spec (Functional Requirements, User Stories, Data Model / Key Entities, Success Criteria, Edge Cases, Terminology). Save the spec atomically after EACH integration.
> 6. Stop when: 5 questions asked, all critical ambiguities resolved early, or user signals "done" / "good" / "no more".
> 7. Report completion: number asked, path to updated spec, sections touched, coverage table (Resolved / Deferred / Clear / Outstanding per category), recommend next command.
>
> Update `catalog/skills/developer-experience/idea-refine/SKILL.md` body to cross-link to the new command and clarify that idea-refine is for vague-idea-to-concrete-problem-statement, while `/clarify-spec` is for already-written-spec ambiguity reduction.
>
> Run `make validate`.

#### 5.2 -- Ship `catalog/templates/spec-quality-checklist.md` + wire into `/generate-plan` (or new `/specify` flow)

**Objective**: Implement adoption candidate G9. Auto-generated checklist that validates spec completeness ("unit tests for English") with three sections: Content Quality, Requirement Completeness, Feature Readiness.

**Prompt**:
> Create `catalog/templates/spec-quality-checklist.md` adapted from `templates/checklist-template.md` (Nexus-Hub framing).
>
> Required content:
>
> ```markdown
> # Specification Quality Checklist: [FEATURE NAME]
>
> **Purpose**: Validate specification completeness and quality before proceeding to planning
> **Created**: [DATE]
> **Feature**: [Link to spec.md]
>
> ## Content Quality
>
> - [ ] No implementation details (languages, frameworks, APIs)
> - [ ] Focused on user value and business needs
> - [ ] Written for non-technical stakeholders
> - [ ] All mandatory sections completed
>
> ## Requirement Completeness
>
> - [ ] No [NEEDS CLARIFICATION] markers remain
> - [ ] Requirements are testable and unambiguous
> - [ ] Success criteria are measurable
> - [ ] Success criteria are technology-agnostic (no implementation details)
> - [ ] All acceptance scenarios are defined
> - [ ] Edge cases are identified
> - [ ] Scope is clearly bounded
> - [ ] Dependencies and assumptions identified
>
> ## Feature Readiness
>
> - [ ] All functional requirements have clear acceptance criteria
> - [ ] User scenarios cover primary flows
> - [ ] Feature meets measurable outcomes defined in Success Criteria
> - [ ] No implementation details leak into specification
>
> ## Notes
>
> - Items marked incomplete require spec updates before /clarify-spec or /generate-plan
> ```
>
> Update `catalog/skills/developer-experience/spec-driven-development/SKILL.md` to add a new subsection titled "Auto-validating the spec" that explains: after writing a spec, copy `catalog/templates/spec-quality-checklist.md` to the feature directory's `checklists/requirements.md` and iterate up to 3 times until all items pass. If items still fail after 3 iterations, document remaining issues in the checklist Notes section and warn the user.
>
> Update `catalog/commands/generate-plan.md` Step 4 to mention: when generating a feature-level plan (plan type 2), the agent should also write a spec-quality-checklist alongside the plan if a spec exists in the same directory.
>
> Run `make validate`.

#### 5.3 -- Phase 5 testing and stabilization

**Objective**: Verify clarification loop + auto-checklist work end-to-end.

**Prompt**:
> Run the Phase 5 verification suite:
> 1. Author a deliberately-ambiguous test spec at `scratch/ambiguous-spec.md` (use vague adjectives "fast", "scalable", missing user stories, no FR/SC IDs).
> 2. Simulate `/clarify-spec`. Confirm: exactly one question asked per turn; each question has a Recommended option at the top; multiple-choice options rendered as a properly-formatted Markdown table with aligned pipes; at most 5 questions total; accepted answers are written to a `## Clarifications` section with `### Session YYYY-MM-DD` subheading; the spec body is updated in place.
> 3. Copy `catalog/templates/spec-quality-checklist.md` to `scratch/checklists/requirements.md`, run a validation pass (manual or skill-driven), confirm at least one item flips from `[ ]` to `[x]` after the clarifications integrated above.
> 4. Delete scratch files.
> 5. `make validate` must pass.
> 6. Run `/generate-session-history` to document Phase 5.

### Phase 5 Exit Checklist

- [ ] `catalog/commands/clarify-spec.md` exists with full sequential-loop behavior spec
- [ ] `catalog/templates/spec-quality-checklist.md` exists
- [ ] `idea-refine` and `spec-driven-development` skills updated with cross-links
- [ ] Test run produces 5 prioritized questions with Recommended options
- [ ] Clarifications integrate back into spec body
- [ ] `make validate` passes
- [ ] Session history generated

---

## Phase 6: Task Discipline - `[P]/[US#]` Labels + Phase Organization

**Goal**: `/generate-plan` emits tasks in the strict `- [ ] T### [P?] [US?] file_path` format, organized by user story with MVP-first phasing.
**Prerequisites**: Phase 4 (user-story IDs).
**Stability Gate**: A test plan generation produces tasks.md (or equivalent in-plan section) with every task in the strict format and at least one parallel `[P]` marker plus per-story labels `[US1]`, `[US2]`.

### Sub-tasks

#### 6.1 -- Update `/generate-plan` to emit strict task checklist format

**Objective**: Implement adoption candidate G6. Task format: `- [ ] T### [P?] [US?] Description with file path`.

**Prompt**:
> Update `catalog/commands/generate-plan.md` Step 3 (Design the Phase Breakdown) and Step 4 (Generate the Plan File) to enforce a strict task checklist format when generating phased sub-tasks.
>
> Format components (every sub-task MUST satisfy all five):
>
> 1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
> 2. **Task ID**: Sequential `T001`, `T002`, ... in execution order across the entire plan (not per-phase)
> 3. **`[P]` marker**: Include ONLY when task is parallelizable (different files, no dependencies on incomplete tasks)
> 4. **`[Story]` label**: REQUIRED for user-story phase tasks only:
>    - Format: `[US1]`, `[US2]`, `[US3]`, ... mapping to user stories from spec.md
>    - Setup phase: NO story label
>    - Foundational phase: NO story label
>    - User Story phases: MUST have story label
>    - Polish phase: NO story label
> 5. **Description**: Clear action with exact file path (e.g., `src/services/user_service.py`)
>
> Example correct lines:
>
> - `- [ ] T001 Create project structure per implementation plan`
> - `- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py`
> - `- [ ] T012 [P] [US1] Create User model in src/models/user.py`
> - `- [ ] T014 [US1] Implement UserService in src/services/user_service.py`
>
> Phase organization (Step 3 update):
>
> - Phase 1: Setup (project initialization, no story labels)
> - Phase 2: Foundational (blocking prerequisites for all user stories, no story labels)
> - Phase 3+: User Stories in priority order (P1, P2, P3, ...). Within each story phase: Tests (if requested) -> Models -> Services -> Endpoints -> Integration. Each phase must be a complete, independently testable increment.
> - Final Phase: Polish & Cross-Cutting Concerns (no story labels)
>
> Add a Format Validation step in Step 5 (Confirm with the User) that scans the produced plan and reports: "Task format validation: N tasks total, M with [P] marker, K mapped to user stories. ALL tasks match the required format." (or list violations and re-prompt).
>
> The existing `executable prompt per sub-task` discipline in `/generate-plan` is preserved -- the strict task-line format is the *summary* line for each sub-task, and the prompt block underneath remains the executable detail.
>
> Run `make validate`.

#### 6.2 -- Phase 6 testing and stabilization

**Objective**: Verify task format compliance on a real plan.

**Prompt**:
> Run the Phase 6 verification suite:
> 1. Simulate `/generate-plan` on a scope with 3 user stories (P1, P2, P3) and 8 tasks total.
> 2. Open the generated plan and verify every task line matches the strict format: checkbox + T###  + optional [P] + optional [US#] + file path. Use grep to confirm zero violations: `grep -E "^- \[ \] T[0-9]{3,} (\[P\] )?(\[US[0-9]+\] )?.+$" <plan-file>` should match every task line.
> 3. Verify Setup/Foundational/Polish phase tasks have NO `[US#]` label and user-story phase tasks DO have one.
> 4. Verify at least one task carries `[P]` marker (parallel opportunities exist in any non-trivial plan).
> 5. Delete the test plan.
> 6. `make validate` must pass.
> 7. Run `/generate-session-history` to document Phase 6.

### Phase 6 Exit Checklist

- [ ] `catalog/commands/generate-plan.md` emits tasks in strict checklist format
- [ ] Phase organization rules enforced (Setup / Foundational no labels; user-story phases with labels)
- [ ] Format Validation step in Step 5 confirms compliance
- [ ] Test run produces zero format violations
- [ ] `make validate` passes
- [ ] Session history generated

---

## Phase 7: Feature Directories + GitHub Issues Conversion

**Goal**: Opt-in `specs/<NNN>-<slug>/` layout for `/generate-plan`; new `/tasks-to-issues` command driving `gh issue create`.
**Prerequisites**: Phase 6 (parseable task format).
**Stability Gate**: `/generate-plan --specs-layout` produces `specs/<NNN>-<slug>/` with `spec.md`, `plan.md`, optionally `tasks.md`; `/tasks-to-issues --dry-run` parses tasks and prints the `gh issue create` invocations it would perform without actually creating issues.

### Sub-tasks

#### 7.1 -- Add `--specs-layout` opt-in flag to `/generate-plan`

**Objective**: Implement adoption candidate G5. Opt-in alternate layout `specs/<NNN>-<slug>/` (sequential or timestamp prefix) preserved alongside the default `docs/<version>/plans/<slug>.md`.

**Prompt**:
> Update `catalog/commands/generate-plan.md` Step 0d (Slug Derivation) and Step 4 (Generate the Plan File) to support an opt-in `--specs-layout` flag.
>
> When `--specs-layout` is NOT provided (default): emit a single plan file at `docs/<version>/plans/<slug>.md` exactly as today.
>
> When `--specs-layout` IS provided:
>
> 1. Resolve the prefix per `.specify/init-options.json` if it exists (key: `branch_numbering`, values: `sequential` or `timestamp`). Default to `sequential`.
> 2. If `sequential`: scan `specs/*/` for existing `NNN-` prefixes; pick next available 3-digit number.
> 3. If `timestamp`: prefix is `YYYYMMDD-HHMMSS` (current UTC timestamp).
> 4. Construct directory name: `specs/<prefix>-<slug>/` (e.g., `specs/003-user-auth/` or `specs/20260520-143022-user-auth/`).
> 5. `mkdir -p` the directory.
> 6. Write `spec.md`, `plan.md`, and (if Phase 6 task structure is enabled) `tasks.md` into the new directory. The skeleton spec uses `catalog/templates/spec-template.md` from Phase 4.
> 7. Persist the resolved path to `.specify/feature.json` at repo root: `{"feature_directory": "specs/<prefix>-<slug>"}`. This allows downstream commands (`/clarify-spec`, `/analyze-spec`, `/tasks-to-issues`) to locate the feature directory without relying on git-branch coupling.
>
> Add a small helper script at `scripts/new-feature.sh` (+ `.ps1` sibling for Windows) that implements the prefix-resolution logic. Both scripts MUST be added to the installer copy block (per the rule in `AGENTS.md` Installer-Aware Changes section): one new copy line in `scripts/installer.sh` near the existing `generate_report.py` block, and one `Safe-Copy` line in `scripts/installer.ps1`. Both destinations point to `~/.nexus-hub/scripts/new-feature.{sh,ps1}`.
>
> Document the new behavior in the command's "How to Run This Command" section. Note that the default behavior is unchanged -- `--specs-layout` is fully opt-in.
>
> Run `make validate` and `make lint`.

#### 7.2 -- Create `/tasks-to-issues` command

**Objective**: Implement adoption candidate G10. Convert a generated tasks.md (or task list inside a plan) into linked GitHub issues via the user's local `gh` CLI.

**Prompt**:
> Create `catalog/commands/tasks-to-issues.md` adapted from `templates/commands/taskstoissues.md` in the spec-kit repo (Nexus-Hub framing; no upstream attribution per the Reverse-Engineering Attribution Rule).
>
> Command behavior:
>
> 1. Accept a feature directory path as argument (default: latest under `specs/<NNN>-*/` if `.specify/feature.json` exists, else latest under `docs/<version>/plans/<slug>/`).
> 2. Pre-flight checks:
>    - Verify `gh` CLI is installed and authenticated: `gh auth status`. Abort with a clear remediation message if not.
>    - Verify the working directory is inside a GitHub-tracked git repo: `gh repo view`. Abort with remediation if not.
>    - Parse tasks.md (or the in-plan task list) per the strict format from Phase 6. Abort if format does not match.
> 3. For each task line: extract T### + optional [P] + optional [US#] + description + file path. Build a GitHub issue payload:
>    - Title: `[T###] <description>`
>    - Body: file path + parallel marker + user-story link (if [US#] present, link to the user story heading in the spec file)
>    - Labels: `nexus-hub`, `spec-kit-task`, plus `parallel` if [P] marker present, plus `user-story-N` if [US#] present
> 4. Support a `--dry-run` flag that prints the `gh issue create` invocations the command would run, one per task, without actually creating issues.
> 5. Without `--dry-run`: invoke `gh issue create --title "<title>" --body "<body>" --label <labels>` per task. Run sequentially (not parallel) to avoid rate-limit surprises. Echo the created issue URLs.
> 6. Emit a final summary table: T### | Created issue URL | Labels.
>
> Ship a companion helper script at `catalog/skills/workflow/tasks-to-issues/scripts/tasks-to-issues.sh` (+ `.ps1` sibling) that does the parsing + gh invocation under the hood; the command file orchestrates it.
>
> Create the companion skill at `catalog/skills/workflow/tasks-to-issues/SKILL.md` with required frontmatter (description follows pushy-description rule, lists trigger phrases: "convert tasks to issues", "create GitHub issues from plan", "issue tracking from tasks.md") + required body sections. The skill body MUST reference the helper script under `scripts/` and the references file under `references/gh-cli-auth-runbook.md` (a 1-page runbook on `gh auth setup-git` and rate-limit handling).
>
> Update three data registries (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) for the new skill.
>
> The helper scripts MUST be added to the installer copy block in BOTH `scripts/installer.sh` and `scripts/installer.ps1` per the Installer-Aware Changes rule in `AGENTS.md`. (Note: the per-skill `scripts/` and `references/` subdirectories are auto-copied by the recursive `safe_folder_copy` / `Safe-Folder-Copy` primitives -- no installer edit needed for them. The installer edit is only required for repo-level helper scripts under `scripts/`, which this phase does NOT add.)
>
> Run `make validate` and `make lint`.

#### 7.3 -- Phase 7 testing and stabilization

**Objective**: Verify the opt-in layout and the issues conversion both work end-to-end.

**Prompt**:
> Run the Phase 7 verification suite:
> 1. Simulate `/generate-plan --specs-layout` on a small scope. Verify: `specs/<NNN>-<slug>/` directory created; `spec.md` (from template), `plan.md`, optionally `tasks.md` written; `.specify/feature.json` persisted with the directory path.
> 2. Verify the default behavior (no flag) still writes to `docs/<version>/plans/<slug>.md` -- no regression.
> 3. Verify `bash -n scripts/new-feature.sh` and PowerShell parser check on `scripts/new-feature.ps1` both pass.
> 4. Confirm the new script lines were added to BOTH installers; run a dry inspection: `grep -n "new-feature.sh" scripts/installer.sh` and `Select-String -Path scripts\installer.ps1 -Pattern 'new-feature.ps1'` (both should return exactly one match).
> 5. Run `/tasks-to-issues --dry-run` on the test plan. Verify the command prints `gh issue create ...` invocations for each task, with correct labels including `parallel` where [P] applied and `user-story-N` where [US#] applied. Verify no actual issues were created.
> 6. Delete `specs/<NNN>-<slug>/` and `.specify/feature.json` after the test.
> 7. `make validate` and `make lint` must pass.
> 8. Run `/generate-session-history` to document Phase 7.

### Phase 7 Exit Checklist

- [ ] `catalog/commands/generate-plan.md` supports `--specs-layout` flag
- [ ] `scripts/new-feature.sh` + `.ps1` exist and are registered in both installers
- [ ] `catalog/commands/tasks-to-issues.md` exists
- [ ] `catalog/skills/workflow/tasks-to-issues/SKILL.md` exists with bundled `scripts/` + `references/`
- [ ] Data registries updated
- [ ] Dry-run produces correct `gh issue create` invocations
- [ ] `make validate` and `make lint` pass
- [ ] Session history generated

---

## Phase 8: v2.1.0 Release Stabilization

**Goal**: All v2.1.0 scope (Phases 1-7) is stable, documented, and shippable.
**Prerequisites**: Phases 1-7.
**Stability Gate**: `make validate`, `make lint`, and `make test` all pass with zero new errors / warnings. `CHANGELOG.md` and `docs/archive/v2/v2.1/RELEASE_NOTES.md` author the v2.1.0 release. Cross-OS installer smoke verification recorded.

### Sub-tasks

#### 8.1 -- Full repo validation sweep

**Objective**: Run all validators and confirm zero regressions.

**Prompt**:
> Run the full v2.1.0 validation suite:
>
> 1. `make validate` -- must pass with zero errors. Capture orphan-bundle warnings count; compare against the baseline (v2.0.0 Phase 8 closed all 4 pre-existing orphans, so the baseline is 0). New orphan warnings introduced by Phase 7's bundled `scripts/`/`references/` subdirectories must be resolved by either referencing every file from `SKILL.md` or removing the file.
> 2. `make lint` -- ShellCheck must produce zero warnings on any new shell scripts.
> 3. `make test` -- pytest hook test suite must pass.
> 4. `python scripts/validate_skills.py --path catalog/skills/<each new skill>` must pass per skill: workflow/project-constitution, code-review/cross-artifact-analyzer, workflow/tasks-to-issues.
> 5. Verify all three data registries are internally consistent: count rows in `data/SKILL_INDEX.md`, count entries in `data/skills.json`, sum category counts in `data/marketplace.json`. All three should equal `previous_total + 3` (3 new skills shipped in v2.1.0).
> 6. Open every new command file and verify all `__SPECKIT_COMMAND_*__` placeholders are replaced with Nexus-Hub equivalents (`__NH_COMMAND_*__` or unprefixed `/<command>` references). No upstream-attribution leaks.
> 7. Report any failures and fix before proceeding.

#### 8.2 -- Author CHANGELOG.md + docs/archive/v2/v2.1/RELEASE_NOTES.md entries

**Objective**: Document the v2.1.0 release per Nexus-Hub conventions.

**Prompt**:
> Author the v2.1.0 release documentation:
>
> 1. Add a new `## [2.1.0] - <today>` section to `CHANGELOG.md` (positioned above the existing `## [2.0.0]` block) following the Keep-a-Changelog format. Sections: Added (new skills, new commands, new templates, new helper scripts), Changed (updated skill bodies, updated `/generate-plan` behavior), Deprecated (none expected), Removed (none expected), Fixed (none expected unless any issues surfaced in Phase 8.1), Security (note that all adoption items pass the MCP Registry Policy review per the source comparison's Section 9). Include explicit references to adoption candidate IDs G1-G11 and to `docs/archive/v2/v2.0/comparison-spec-kit.md`.
> 2. Create `docs/archive/v2/v2.1/` directory and author `docs/archive/v2/v2.1/RELEASE_NOTES.md` modeled on `docs/archive/v2/v2.0/RELEASE_NOTES.md`. Sections: Highlights, Spec-Driven Development adoption (the headline narrative), New skills (3), New commands (4: constitution, analyze-spec, clarify-spec, tasks-to-issues), New templates (3: constitution-template, spec-template, spec-quality-checklist), Updated skills (5: spec-driven-development, ambiguity-detector, idea-refine, generate-plan-related, implementation-plan), Migration notes (none -- additive only).
> 3. Update `data/marketplace.json` `version` field to `2.1.0` and `last_updated` to today.
> 4. Update root README's "What's new" section (if such a section exists) to highlight the v2.1.0 SDD adoption.
> 5. ASCII-only commit message text (no em-dashes, en-dashes, curly quotes, ellipsis characters per the global rule). Use straight quotes and `...` instead.

#### 8.3 -- Cross-OS installer smoke + carry-over close

**Objective**: Verify the installer correctly distributes the new artifacts on at least one OS; close the carry-over from v1.1.5 known-gaps (DF-003 / DF-005 / DF-006) for any Phase 7 scripts added.

**Prompt**:
> Run the cross-OS installer smoke verification:
>
> 1. On Windows (PowerShell) -- the primary work environment per session memory: run `scripts/installer.ps1 --target <throwaway-dir>` (or equivalent dry-target install) and confirm:
>    - All 3 new skills land at the expected `~/.nexus-hub/skills/<category>/<name>/SKILL.md` paths
>    - All 4 new commands land at the expected per-platform command directories (Claude `commands/`, Codex `prompts/`, Gemini `workflows/`)
>    - All 3 new templates land at `~/.nexus-hub/templates/`
>    - The two new repo-level helper scripts from Phase 7 (`scripts/new-feature.sh`, `scripts/new-feature.ps1`) land at `~/.nexus-hub/scripts/`
>    - The per-skill bundled `scripts/` and `references/` subdirectories under `tasks-to-issues/` are auto-copied
> 2. If a Linux or macOS host is available, repeat the smoke run with `bash scripts/installer.sh --target <throwaway-dir>` and record the result. If unavailable, record the deferral in `docs/archive/v2/v2.1/known-gaps.md` as a continuation of DF-003 / DF-005 / DF-006 from v1.1.5.
> 3. Write the smoke results to `docs/archive/v2/v2.1/installer-smoke-post.txt`.
> 4. Tag the release: `git tag v2.1.0` (do NOT push until user confirms).
> 5. Run `/generate-session-history` to document Phase 8.

### Phase 8 Exit Checklist

- [ ] `make validate`, `make lint`, `make test` all pass with zero new errors/warnings
- [ ] `CHANGELOG.md` `[2.1.0]` section authored
- [ ] `docs/archive/v2/v2.1/RELEASE_NOTES.md` authored
- [ ] `data/marketplace.json` version bumped
- [ ] Cross-OS installer smoke run captured in `docs/archive/v2/v2.1/installer-smoke-post.txt`
- [ ] `git tag v2.1.0` created (push deferred to user confirmation)
- [ ] Session history generated

---

## Phase 9: P3 Polish - Methodology Essay, Devcontainer, Markdownlint Config, Installer Test

**Goal**: Ship the four P3 polish items from the comparison report; can land as v2.1.x patches without blocking v2.1.0 if scope is tight.
**Prerequisites**: Phase 8 (v2.1.0 base release stable).
**Stability Gate**: All four artifacts ship; `make validate` continues to pass.

### Sub-tasks

#### 9.1 -- Author Spec-Driven Methodology essay at `docs/archive/v2/v2.1/spec-driven-methodology.md`

**Objective**: Adapt the philosophical narrative ("specs are executable; code serves the spec") to Nexus-Hub's broader catalog framing.

**Prompt**:
> Create `docs/archive/v2/v2.1/spec-driven-methodology.md` (a single-file essay, target 2500-3500 words). Sections:
>
> 1. The Power Inversion (specs become the source of truth; code serves the spec; the gap between intent and implementation closes)
> 2. The Nexus-Hub SDD Workflow (constitution -> specify -> clarify -> plan -> tasks -> analyze -> implement, with explicit reference to the v2.1.0 commands)
> 3. Why SDD Matters Now (AI capability threshold; software complexity growth; pace-of-change acceleration -- frame these from the Nexus-Hub perspective: the harness exists to amplify the developer, not replace them)
> 4. Core Principles (specs as lingua franca, executable specs, continuous refinement, research-driven context, bidirectional feedback, branching for exploration)
> 5. Implementation Approaches (how to practice SDD with the v2.1.0 Nexus-Hub commands)
> 6. Template-Driven Quality (how `[NEEDS CLARIFICATION]` markers + FR/SC IDs + the spec-quality-checklist constrain LLMs toward higher-quality specs)
> 7. Pitfalls and Anti-Patterns (when SDD over-extends; cases where lightweight skills like `incremental-implementation` are a better fit)
>
> Do NOT plagiarize or paraphrase upstream text wholesale; produce a Nexus-Hub-native essay that uses the same conceptual scaffolding but Nexus-Hub-native examples (e.g., reference adopting a new MCP per the Registry Policy as a spec-first exercise). No spec-kit attribution in the essay per the Reverse-Engineering Attribution Rule.
>
> Link from `catalog/skills/developer-experience/spec-driven-development/SKILL.md` to the essay.
>
> Run `make validate`.

#### 9.2 -- Add `.devcontainer/` with per-agent CLI install

**Objective**: First-touch developer experience improvement.

**Prompt**:
> Create a `.devcontainer/` directory at the repo root with:
>
> 1. `.devcontainer/devcontainer.json` declaring a Python 3.11+ base image, common VS Code extensions (Python, Markdown, ShellCheck), and `postCreateCommand: bash .devcontainer/post-create.sh`.
> 2. `.devcontainer/post-create.sh` (bash, `set -euo pipefail`) installing common AI CLI tools used by Nexus-Hub users: `claude`, `gh`. Use `command -v` guards so existing installs are not re-installed. Echo install status per tool.
> 3. Add a section to `README.md` under "Development setup" pointing to the devcontainer for users who want a one-click setup.
>
> Verify the devcontainer.json parses (use `python -c "import json; json.load(open('.devcontainer/devcontainer.json'))"`).
>
> Run `make validate`.

#### 9.3 -- Ship `catalog/style-guides/markdownlint-cli2.jsonc`

**Objective**: Ship a markdownlint config that downstream projects bootstrapping from Nexus-Hub can pick up.

**Prompt**:
> Create `catalog/style-guides/markdownlint-cli2.jsonc` with a configuration that aligns with the existing `catalog/style-guides/markdown.md` rules (blank line before lists/headings/code-blocks/tables, ATX-style headings, hyphens for unordered lists, etc.). Use the standard `markdownlint-cli2` schema.
>
> Update `catalog/style-guides/markdown.md` to mention the new JSON config file and how to enable it in a downstream project (`npx markdownlint-cli2 "**/*.md"`).
>
> Confirm the installer's `install_templates` block copies `catalog/style-guides/` recursively (it does per `safe_folder_copy` -- no installer edit needed).
>
> Run `make validate`.

#### 9.4 -- Add path-traversal test for installer registrar logic

**Objective**: Mirror Spec Kit's `tests/test_registrar_path_traversal.py` defensive practice. Sub-task lands a new test category (`tests/installer/`).

**Prompt**:
> Create `tests/installer/__init__.py` and `tests/installer/test_registrar_path_traversal.py`. The test suite verifies that the installer's path-resolution logic refuses to install any artifact whose resolved destination would escape the target install root.
>
> Test cases:
>
> 1. Skill name containing `../` characters: `name = "../etc/passwd"` -- installer must reject.
> 2. Skill name containing absolute path: `name = "/etc/passwd"` -- installer must reject.
> 3. Skill name containing null bytes: `name = "foo\x00bar"` -- installer must reject.
> 4. Skill name containing UNC paths on Windows: `name = "\\\\server\\share\\evil"` -- installer must reject.
>
> Test implementation: import the installer's path-resolution helper (or invoke the installer scripts via subprocess with the malicious name as input). Assert non-zero exit code OR a thrown ValueError.
>
> Wire the test into `make test` via the existing pytest discovery (no `Makefile` change should be needed; pytest's `tests/installer/` is auto-discovered).
>
> Run `make test` and confirm the new test suite passes (the installer SHOULD already reject these inputs since `realpath` / `Resolve-Path` collapse `..` before write).

#### 9.5 -- Phase 9 stabilization

**Objective**: Verify all four P3 polish items integrated cleanly.

**Prompt**:
> Run the Phase 9 verification suite:
> 1. `make validate`, `make lint`, `make test` all pass.
> 2. `docs/archive/v2/v2.1/spec-driven-methodology.md` exists and is non-empty.
> 3. `.devcontainer/devcontainer.json` is valid JSON.
> 4. `catalog/style-guides/markdownlint-cli2.jsonc` exists.
> 5. `tests/installer/test_registrar_path_traversal.py` runs and passes.
> 6. Decide whether Phase 9 ships as part of v2.1.0 (re-tag) or as v2.1.1 (separate release). Default: ship as v2.1.1 patch to keep v2.1.0 scope tight to G1-G10.
> 7. Run `/generate-session-history` to document Phase 9.

### Phase 9 Exit Checklist

- [ ] Methodology essay shipped
- [ ] `.devcontainer/` shipped
- [ ] `catalog/style-guides/markdownlint-cli2.jsonc` shipped
- [ ] `tests/installer/test_registrar_path_traversal.py` shipped and passing
- [ ] `make validate`, `make lint`, `make test` all pass
- [ ] Release decision made (re-tag v2.1.0 or new v2.1.1)
- [ ] Session history generated

---

## Phase 10: Integration Registry Refactor (G12, re-full, v2.2.0+)

**Goal**: Refactor the lock-step per-platform `base-*.md` template editing into a Python class hierarchy (`IntegrationBase` -> `MarkdownIntegration` / `TomlIntegration` / `YamlIntegration` / `SkillsIntegration`) with one subclass per supported agent. Reduces adding a new agent from ~10 file changes to one Python subclass.
**Prerequisites**: Phase 8 (v2.1.0 shipped). This phase is a separate v2.2.0 effort and may run weeks or months after Phase 8.
**Stability Gate**: All five existing platforms (Claude, Codex, Cursor, Gemini, OpenCode) still receive identical artifacts via the new class hierarchy as they did via the lock-step templates. Behavior must be byte-identical before adding any new agent.

### Sub-tasks

#### 10.1 -- Design the integration class hierarchy

**Objective**: Document the new architecture in an ADR before any code lands.

**Prompt**:
> Author `docs/archive/v2/v2.2/adr-001-integration-registry.md` (using the `architecture-decision-record` skill from the catalog) covering:
>
> 1. Context: lock-step `templates/ai-instructions/base-*.md` editing is brittle; adding Windsurf, Goose, Forge, Qwen, Tabnine, Kiro, Pi, Mistral Vibe currently requires editing 5 templates + potentially installer logic. Reverse-engineered from `src/specify_cli/integrations/base.py` in the spec-kit repo (rationale stays in this ADR; do NOT name the upstream repo in user-facing artifacts).
> 2. Decision: introduce a Python class hierarchy under `scripts/lib/integrations/`. `IntegrationBase` defines the common contract (`key`, `config`, `registrar_config`, `context_file`, `setup()`, `teardown()`). Four base subclasses: `MarkdownIntegration`, `TomlIntegration`, `YamlIntegration`, `SkillsIntegration`. Each supported agent is a single subclass with at most ~30 lines declaring its config.
> 3. Consequences: adding a new agent becomes one subclass + one `_register()` line. Both `installer.sh` and `installer.ps1` invoke a single Python entry point (`python scripts/lib/integrations/runner.py install --target <dir>` for example) that walks the registry and dispatches per-agent. The 5 existing `base-*.md` templates remain in the repo (now consumed by the Python registrar, not edited per-change).
> 4. Status: Accepted; targets v2.2.0.
> 5. Alternatives considered: Keep lock-step templates (rejected: known brittleness, agents not added beyond initial 5); Adopt spec-kit's `specify-cli` wholesale (rejected: heavy dependency, conflicts with Nexus-Hub's installer-as-template-distributor architecture).

#### 10.2 -- Build the registrar skeleton with parity tests

**Objective**: Land the class hierarchy + behavioral-parity tests for the 5 existing platforms BEFORE touching any installer code.

**Prompt**:
> Create the directory `scripts/lib/integrations/` with:
>
> 1. `__init__.py` containing `INTEGRATION_REGISTRY: dict[str, IntegrationBase] = {}` and a `_register_builtins()` function that imports each per-agent subclass and registers it. Alphabetical order.
> 2. `base.py` with class definitions for `IntegrationBase`, `MarkdownIntegration`, `TomlIntegration`, `YamlIntegration`, `SkillsIntegration`. Each base class implements `setup()` and `teardown()` with template-processing logic that produces output byte-identical to the current `installer.sh` / `installer.ps1` behavior for that file class.
> 3. `manifest.py` tracking which files were created during install (so teardown can remove them).
> 4. Five per-agent subclass files: `claude/__init__.py`, `codex/__init__.py`, `cursor/__init__.py`, `gemini/__init__.py`, `opencode/__init__.py`. Each ~30 lines declaring `key`, `config`, `registrar_config`, `context_file`.
>
> Then create `tests/integrations/test_parity_with_legacy_installer.py`. For each of the 5 platforms: run the new Python registrar against a throwaway target dir; run the legacy installer against another throwaway target dir; diff the two trees with `os.walk` + content hashing. Assert byte-identical output.
>
> The legacy installers (`scripts/installer.sh`, `scripts/installer.ps1`) are NOT modified in this sub-task. They remain canonical until parity is proven.
>
> Run `make test` and confirm the parity suite passes for all 5 platforms.

#### 10.3 -- Switch installers to invoke the Python registrar

**Objective**: Replace the per-platform copy logic in both installers with a single Python invocation. Behavior must remain byte-identical (verified by parity tests).

**Prompt**:
> Refactor `scripts/installer.sh` and `scripts/installer.ps1` so that the per-platform `base-*.md` copy blocks (and the per-platform commands / skills / hooks / rules copy blocks) are replaced with a single call: `python scripts/lib/integrations/runner.py install --target "<target-dir>" --integrations "<list>"`. The runner uses the registry from Phase 10.2 to dispatch per-agent.
>
> Constraint: the user-facing CLI surface of both installers (flags, prompts, target paths, output text) MUST remain unchanged. Internal implementation changes only.
>
> Re-run the parity tests from sub-task 10.2 AFTER the installer changes. Both installers should still produce byte-identical output to the legacy behavior (because the underlying logic is now shared through the Python runner).
>
> Document the change in `docs/archive/v2/v2.2/installer-refactor.md` with a migration note (for downstream contributors who relied on editing the per-platform templates in lockstep -- they now edit the relevant base class or per-agent subclass instead).

#### 10.4 -- Add Windsurf (or another previously-out-of-scope agent) as a proof-of-value

**Objective**: Validate the new architecture by adding a 6th agent in a single subclass + one `_register()` line.

**Prompt**:
> Add Windsurf as the 6th supported agent. Create `scripts/lib/integrations/windsurf/__init__.py` with a single subclass:
>
> ```python
> from ..base import MarkdownIntegration
>
> class WindsurfIntegration(MarkdownIntegration):
>     key = "windsurf"
>     config = {
>         "name": "Windsurf",
>         "folder": ".windsurf/",
>         "commands_subdir": "workflows",
>         "install_url": None,
>         "requires_cli": False,
>     }
>     registrar_config = {
>         "dir": ".windsurf/workflows",
>         "format": "markdown",
>         "args": "$ARGUMENTS",
>         "extension": ".md",
>     }
>     context_file = ".windsurf/rules/nexus-hub-rules.md"
> ```
>
> Add one import + one `_register()` line to `scripts/lib/integrations/__init__.py`.
>
> Add a test at `tests/integrations/test_integration_windsurf.py` that exercises the install + teardown flow and asserts files land at the expected paths.
>
> Run `make test`. Confirm zero regressions in the 5 existing platforms.
>
> Update `README.md` and `AGENTS.md` to add Windsurf to the supported-agents list.

#### 10.5 -- Phase 10 stabilization + v2.2.0 release

**Objective**: Validate the refactor + ship v2.2.0.

**Prompt**:
> Run the Phase 10 verification suite:
> 1. `make validate`, `make lint`, `make test` all pass.
> 2. The parity suite (sub-task 10.2) still asserts byte-identical output for all 5 original platforms.
> 3. The Windsurf integration test passes; a manual install onto a throwaway target dir produces the expected `.windsurf/workflows/` directory.
> 4. Author `CHANGELOG.md` `[2.2.0]` section with Added (Windsurf support, integration registrar, parity tests), Changed (installer internals refactored to use Python registrar; user-facing CLI unchanged), Removed (the per-platform copy blocks in `installer.sh` / `installer.ps1` -- mention the migration for contributors).
> 5. Author `docs/archive/v2/v2.2/RELEASE_NOTES.md`.
> 6. `git tag v2.2.0` (push deferred to user confirmation).
> 7. Run `/generate-session-history` to document Phase 10.

### Phase 10 Exit Checklist

- [ ] ADR-001 authored at `docs/archive/v2/v2.2/adr-001-integration-registry.md`
- [ ] `scripts/lib/integrations/` skeleton + 5 per-agent subclasses + parity tests landed
- [ ] Installers switched to invoke the Python registrar; CLI surface unchanged
- [ ] Windsurf added as 6th supported agent in one subclass + one register line
- [ ] All parity tests pass
- [ ] `make validate`, `make lint`, `make test` pass
- [ ] `CHANGELOG.md [2.2.0]` and `docs/archive/v2/v2.2/RELEASE_NOTES.md` authored
- [ ] `git tag v2.2.0` created
- [ ] Session history generated

---

## Items explicitly NOT adopted (security / policy reasons)

No items in this plan were classified `drop-outright` under Section 9.3 of the source comparison. Spec Kit is fully open-source, MIT-licensed, no third-party data processors, no commercial dependencies. The full MCP Registry Policy review passed for all 12 candidates.

This appendix is intentionally empty.

---

## Cross-cutting Constraints

These apply to every phase, sub-task, and prompt in this plan:

1. **Reverse-Engineering Attribution Rule**: do NOT name "spec-kit", "GitHub Spec Kit", "github/spec-kit", or any specific upstream file path in user-facing Nexus-Hub artifacts (skill bodies, command bodies, README, docs). Attribution belongs in the comparison report (`docs/archive/v2/v2.0/comparison-spec-kit.md`) and in the reverse-engineering matrix at `docs/policy/mcp-reverse-engineering-matrix.md`, not in the distributed artifact. Use generic descriptive names ("spec template", "constitution skill", "cross-artifact analyzer") instead.
2. **Slash-command prefix**: Nexus-Hub commands are unprefixed (`/constitution`, `/analyze-spec`, `/clarify-spec`, `/tasks-to-issues`). Do NOT use `/speckit.*` or `/sk.*` prefixes. Document the upstream source pattern only in the comparison report.
3. **Cross-platform parity**: every new shell script under `scripts/` ships with a `.ps1` sibling. Every per-skill `scripts/` bundled subdirectory likewise.
4. **Installer-Aware Changes**: any new file under `scripts/<name>.py` or `scripts/<name>.sh` MUST be registered in BOTH `scripts/installer.sh` and `scripts/installer.ps1` by explicit name. Auto-copied subdirectories (per-skill `scripts/`, `references/`, `assets/`) do NOT need installer edits.
5. **Data registry consistency**: every new skill triggers an update to `data/SKILL_INDEX.md`, `data/skills.json`, AND `data/marketplace.json`. Run `make validate` after each edit.
6. **No commit during phase work** unless the user explicitly asks. Each phase produces commits at the Stability Gate step, never mid-phase.
7. **ASCII-only commit messages**: no em-dashes, en-dashes, curly quotes, ellipsis characters. Use `-`, straight quotes, and `...` instead. Prevents encoding corruption on Windows.
8. **No AI attribution footers** in commit messages.
9. **MCP Registry Policy**: cite the policy by name in any phase that introduces a new outbound call, new API key, new third-party data processor, or new runtime dependency. (None of the phases in this plan should trigger this, but the rule applies if scope creeps.)
10. **Pushy-description rule**: every new skill description follows the format from `AGENTS.md` -- list trigger phrases verbatim, add a SKIP clause, cover synonyms and adjacent intents.

---

## How to Begin

Run `/implement-phase adoption-spec-kit` to start Phase 1, or paste the prompt from sub-task 1.1 into a fresh Claude Code session.
