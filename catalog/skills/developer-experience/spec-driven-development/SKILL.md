---
name: spec-driven-development
description: "Writes a structured technical specification before any code is written. Use when starting a new project, feature, or significant change and no written specification exists -- especially when requirements are ambiguous, the change touches multiple files, or architectural decisions must be made. Trigger phrases: write a spec, create a specification, spec this out, define the requirements, spec-driven, write the spec before coding. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
summary_l0: "Write specifications before code and place release-bound artifacts canonically"
overview_l1: "This skill produces a written technical specification before implementation begins, following a four-phase gated workflow: Specify → Plan → Tasks → Implement. Use it when requirements are ambiguous, the change spans multiple files or modules, or you are making an architectural decision. Key capabilities include assumption surfacing, success criteria formulation, scope bounding through explicit non-goals, spec depth chosen by blast radius, and task breakdown with per-task acceptance criteria. The spec is committed to the repo as a living document -- updated as decisions change, referenced in PRs, and never discarded after implementation begins. Without this skill, implementation risks solving the wrong problem or building an architecture that does not match the team's intent. Trigger phrases: write a spec, spec this out, create a specification, define requirements, spec before coding, what should I build. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Spec-Driven Development

Write a structured specification before writing any code. The spec is the shared source of truth between you and the human engineer -- it defines what we're building, why, and how we'll know it's done. Code without a spec is guessing.

"Guessing" is the precise word, and it explains why the cost is worse than rework. An agent that reaches an unstated requirement does not stop and ask; it fills the gap with the most plausible interpretation and keeps building on it. In a small codebase those guesses stay visible, because there is not much code for them to hide in. In a large one they land in details nobody inspects, so the consequence surfaces later, somewhere else, in code the author never touched, where it reads as an unrelated bug rather than as a decision that was never made. Guess cost therefore scales with the size of the system, not with the size of the change, which is why a small change to a large codebase deserves more written agreement than its diff suggests. The two mechanisms this skill ships exist for exactly this: the `[NEEDS CLARIFICATION]` marker and the mandatory `## Assumptions` section both convert a silent guess into a recorded decision the reviewer can overturn with one line.

## Hard Gate: No Implementation Before an Approved Design

This is a hard gate, not a guideline. Until a design has been presented in reviewable sections AND the user has explicitly approved it, you MUST NOT:

- invoke any implementation skill (`incremental-implementation`, a language-specific build skill, `plan-before-code`'s execution step),
- write, edit, or generate production or test code,
- scaffold files, create directories, or run a generator,
- run an installer or add a dependency in service of the unbuilt feature.

The gate applies regardless of how simple the change looks. "Simple" is a judgment about implementation effort; the gate is about whether you and the user agree on *what* to build and *why*. Those are independent: a one-file change built against the wrong assumption is still rework. The cost of presenting a short design for a simple change is a minute; the cost of building the wrong simple thing is the build plus the rebuild plus the conversation about why it was wrong.

What satisfies the gate: a design or spec presented in sections the user can react to (objective, the proposed approach, success criteria, boundaries), followed by an explicit approval ("yes, build that", "approved", a clear go-ahead). Silence is not approval. A thumbs-up on the *problem statement* is not approval of the *design*. If the user says "just build it" before any design exists, present the smallest reviewable design first and ask for the go-ahead - that exchange takes one turn and is the entire point of the gate.

### Spec depth is proportional; the gate is not

The gate governs whether you and the user agree on *what* to build. The depth governs how much document that agreement needs. These are independent axes, and this rule moves only the second one.

Depth is keyed on blast radius, meaning how far a wrong assumption propagates, not on effort, line count, or how long the change takes to write. A three-line change to a public API has a larger blast radius than a three-hundred-line change to a private helper.

| Blast radius | Required spec depth |
|---|---|
| One file, internal, with no surface a consumer can observe | Problem Statement, acceptance criteria, and Non-Goals. Short enough to fit in a chat message; it does not need its own file. |
| Multiple files or multiple modules, still internal | The above, plus User Scenarios with an Independent Test, FR-### items, and Assumptions. |
| A change to behavior, a public API, a data schema, or a CLI surface | The full canonical template written to `spec.md`, including Invariants. |

The top tier names the same four surfaces as "The Spec as a Merge Gate" below, and that is deliberate: a change that must update its spec before it can merge is a change that needed the full spec before it started. The two rules are one rule seen from each end.

Two boundaries keep the tiering honest:

- **Depth never scales the approval.** A three-bullet spec in a chat message is still a design presented in reviewable sections, and it still requires an explicit go-ahead before any code. Shrinking the artifact does not shrink the gate, shorten it, or make silence count.
- **The bottom tier is a short spec, not an absent one.** Whether a change needs *no* spec is a different question, answered in "When NOT to use" below, and it covers only a single-line fix or a typo. Everything above that floor gets a written statement of the problem, what done means, and what is out of scope, however brief.

When two tiers both look defensible, take the higher one. Over-specifying costs a paragraph; under-specifying costs the rebuild.

### One Question at a Time

When you need to resolve ambiguity before the design is complete, ask one question at a time and wait for the answer before asking the next. A wall of ten questions forces the user to context-switch across ten decisions at once and usually produces partial answers that leave the design ambiguous anyway. A single, specific question ("session cookies or JWT?") gets a clean answer you can build the next question on. This Socratic, one-at-a-time flow is the same discipline `/clarify-spec` automates as a sequential 5-question loop; use it manually whenever you are clarifying a design before the gate. (This complements, and does not replace, the `[NEEDS CLARIFICATION]` marker convention below, which is for ambiguities recorded *in* the written spec.)

Cross-link: `[[idea-refine]]` runs before this skill to sharpen the problem statement; the hard gate here governs the transition from an approved design to code. Approving the problem (idea-refine) and approving the design (this gate) are two separate approvals - do not collapse them.

## When to Use This Skill

Use when:
- Starting a new project or feature with no written requirements
- Requirements exist only as a verbal description or a vague request
- The change touches multiple files or modules
- You are about to make an architectural decision
- The task would take more than 30 minutes to implement

**When NOT to use:** A single-line fix, a typo correction, or a change whose requirements are already unambiguous and self-contained needs no spec at all.

This section answers only whether a spec is needed. How much spec is a separate question, answered by the depth rule above. Keeping them apart matters, because "the change is small" is an answer to the second question that reads like an answer to the first: a change that is small but real gets a SHALLOW spec, not no spec. Reach for "no spec" only when there is genuinely nothing to agree on, not when there is little to agree on.

If you already have a well-defined spec, move directly to `plan-before-code`.

### Marking uncertainty with `[NEEDS CLARIFICATION]`

When the spec author cannot resolve an ambiguity from the conversation alone, surface it inline with the `[NEEDS CLARIFICATION: <specific question>]` marker rather than guessing. The marker is a hard contract between the spec author and the human reviewer: every marker is an item the reviewer is expected to resolve before the spec advances to the Plan phase.

Rules:

- **Hard limit: 3 markers total per spec**. If more candidates surface, prioritize per `scope > security/privacy > UX > technical` and demote the rest to assumptions with informed defaults. The cap forces triage; a spec carrying 12 markers signals scope confusion, not detail.
- **Make informed guesses for the rest**. For every candidate ambiguity below the 3-marker cap, write the most plausible interpretation as an explicit assumption in an `## Assumptions` section. The reviewer can override the assumption with one line; an unanswered marker requires a full back-and-forth.
- **Be specific in the marker question**. `[NEEDS CLARIFICATION: which auth method - OAuth2, JWT, or session cookies?]` is actionable. `[NEEDS CLARIFICATION: auth?]` is not.

Before / after:

```
Before (vague, no marker, no assumption):
The system should authenticate users somehow.

After (specific marker within the 3-cap, with priority justification):
The system MUST authenticate users.
[NEEDS CLARIFICATION: which auth method - session cookies (matches existing stack) or JWT (matches the mobile-app plan)?]
Priority: scope (which auth method drives data-model and deploy-shape choices downstream).

After (below the 3-cap, demoted to assumption):
The system MUST authenticate users via session cookies (matches the existing stack).
See ## Assumptions for the override path if JWT is required instead.
```

Cross-link: `[[ambiguity-detector]]` emits markers in this same format when it scans an existing spec; `[[idea-refine]]` produces no more than 3 outstanding markers in the problem statement.

### Spec template

`catalog/templates/spec-template.md` (installed at `~/.nexus-hub/templates/spec-template.md`) is the single canonical spec skeleton. Every feature spec starts from it. There is no second skeleton and no abbreviated variant: if a section does not apply, remove that section rather than substituting a different structure. The template enforces the convention that downstream tooling depends on - in particular, the `**FR-###**: System MUST <capability>` format for functional requirements and the `**SC-###**: <measurable outcome>` format for success criteria.

Why the FR-### / SC-### IDs matter: the `[[cross-artifact-analyzer]]` skill (run via `/analyze-spec`) builds a Coverage Summary table by matching each FR-### and SC-### in the spec against the task descriptions in the plan or tasks.md. A spec written with prose bullets instead of FR-### / SC-### IDs produces an empty coverage matrix and the analyzer cannot flag missing tasks. The IDs are the contract between the spec and the analyzer.

Stability rules for IDs:

- IDs are sequential within their category (FR-001, FR-002, ...; SC-001, SC-002, ...).
- IDs are stable - once an FR or SC is assigned an ID, do not renumber on edits. Removing a requirement leaves a gap in the sequence; do not backfill.
- IDs are unique within the spec but not globally across the project - FR-001 in `specs/003-auth/spec.md` is a different requirement from FR-001 in `specs/004-billing/spec.md`.

The template's mandatory sections, in document order:

1. **Problem Statement** -- the actor, what fails today, and the observable outcome that marks success. This carries forward the problem statement `[[idea-refine]]` produced; it is not re-derived here.
2. **User Scenarios & Testing** -- at least one prioritized user story with its Independent Test paragraph and Given/When/Then acceptance scenarios.
3. **Requirements** -- the FR-### items, plus an optional Key Entities subsection when the feature involves data.
4. **Success Criteria** -- the SC-### items.
5. **Non-Goals** -- what the system explicitly will NOT do, one reason per entry.

Two conditional sections complete the set. **Assumptions** is mandatory whenever any candidate ambiguity was demoted below the 3-marker hard limit. **Invariants** is required whenever the change touches existing behavior, and declares the behavior that must not break.

`## Non-Goals` is the section three auditing surfaces check against, so an empty or missing one produces findings downstream: `spec-quality-checklist.md`'s "Scope is clearly bounded" item, the `scope-guardian-reviewer` agent's missing-cut-line lens, and `[[idea-refine]]`'s own "scope is explicitly bounded" gate. It is also where `idea-refine`'s **Out of Scope** block lands, so the hand-off is a copy rather than a rewrite. Keep the Non-Goals / Assumptions boundary straight: an Assumption is a decision the reviewer can overturn with one line, whereas a Non-Goal is scope the reviewer is being asked to confirm is excluded.

### User stories with priorities

Every spec MUST include at least one user story under `## User Scenarios & Testing`, formatted as `### User Story N - [Title] (Priority: PN)`. The story format enforces three disciplines that the rest of the workflow depends on:

1. **Priority labels (P1 / P2 / P3 / ...)**: priorities are assigned by user value, not by implementation order. P1 is the story that delivers the most value with the smallest scope. P2 and P3 add value but are not required to ship a viable MVP. The Phase 6 task discipline (the `[US#]` label on every user-story-phase task) is keyed off these priority IDs - tasks for P1 stories carry `[US1]`, tasks for P2 carry `[US2]`, and so on.
2. **Independent Test paragraph**: each story declares the smallest end-to-end test that proves it is delivered. The test MUST be runnable without implementing any other story. This is the MVP contract: if you implement only the P1 story, the Independent Test for P1 must pass even though P2 and P3 are untouched. Stories that cannot be tested in isolation fail this contract and must be re-scoped.
3. **MVP rule**: implementing just the P1 story must deliver value to a real user. A spec where P1 is "set up the database schema" violates the rule - that is an enabler, not a user story. Re-scope until P1 names an outcome a user observes.

A spec with a single user story still uses the format: `### User Story 1 - [Title] (Priority: P1)` with the full Independent Test and Acceptance Scenarios subsections. The single-story case is the most common; the format exists so that `/analyze-spec` can find the story regardless of count.

Acceptance Scenarios use the Given / When / Then format. Each scenario maps directly to one of the FR-### items - the scenario is the FR's executable verification.

### Auto-validating the spec

A spec is not "done" the moment the template's slots are filled. Run the spec through the spec-quality-checklist as a final gate before handoff to `/generate-plan` or `/clarify-spec`.

The mechanism: copy `catalog/templates/spec-quality-checklist.md` (installed at `~/.nexus-hub/templates/spec-quality-checklist.md`) into the feature directory as `checklists/requirements.md`. Iterate up to **3 passes** through the checklist, ticking items that already pass and editing the spec to make the remaining items pass:

1. **Pass 1 - Content Quality**: confirm no implementation details leak into the spec (frameworks, languages, APIs), and that the spec reads correctly for a non-technical stakeholder. If implementation details appear, move them to the plan or to a `### Technical Notes` subsection that the analyzer ignores.
2. **Pass 2 - Requirement Completeness**: confirm every `[NEEDS CLARIFICATION]` marker is either resolved or moved to `## Assumptions` per the 3-marker cap. Confirm SC-### IDs are measurable (numeric thresholds, boolean conditions, or explicit pass/fail signals). Confirm acceptance scenarios cover every FR-###.
3. **Pass 3 - Feature Readiness**: confirm every functional requirement has at least one acceptance scenario, and that user scenarios cover the primary flows end-to-end.

After 3 iterations, document any remaining unchecked items in the spec's `## Assumptions` section and warn the user before advancing. Unchecked items are a contract with the reviewer - they tell the next stage exactly which corners of the spec are still soft.

The checklist is "unit tests for English": it validates the spec's prose, not the implementation. Implementation correctness is validated separately by tests against FR-### / SC-### IDs in `[[cross-artifact-analyzer]]`'s coverage matrix.

## The Gated Workflow

Spec-driven development has four phases. Do not advance to the next phase until the human has reviewed and approved the current one.

```
SPECIFY ──→ PLAN ──→ TASKS ──→ IMPLEMENT
   │          │        │          │
   ▼          ▼        ▼          ▼
 Human      Human    Human      Human
 reviews    reviews  reviews    reviews
```

### Phase 1: Specify

Surface assumptions before writing any spec content. List what you are assuming and ask for correction:

```
ASSUMPTIONS I'M MAKING:
1. This is a web application (not native mobile)
2. Authentication uses session-based cookies (not JWT)
3. The database is PostgreSQL (based on existing Prisma schema)
→ Correct me now or I'll proceed with these.
```

Then write the spec from the canonical template. Copy `catalog/templates/spec-template.md` into the feature directory as `spec.md` and fill its mandatory sections in document order: Problem Statement, User Scenarios & Testing, Requirements (FR-###), Success Criteria (SC-###), and Non-Goals, adding Assumptions and Invariants where they apply. Do not substitute an alternative structure; the section-by-section contract is in the "Spec template" section above, and the Verification checklist at the end of this skill is keyed to exactly those sections.

Project-level material (build and test commands, the directory layout, code-style conventions, the tech stack, and the three-tier Always / Ask first / Never boundaries) is deliberately NOT part of a feature spec. It is stable across features, so restating it per feature guarantees drift. See "Project-level context (distinct from a feature spec)" below for where it belongs instead.

**Success Criteria**: Reframe instructions as testable conditions:
```
REQUIREMENT: "Make the dashboard faster"

REFRAMED:
- Dashboard LCP < 2.5s on 4G connection
- Initial data load completes in < 500ms
- No layout shift during load (CLS < 0.1)
→ Are these the right targets?
```

### Phase 2: Plan

With the validated spec, generate a technical implementation plan:

1. Identify major components and their dependencies
2. Determine implementation order (what must be built first)
3. Note risks and mitigation strategies
4. Identify parallel vs. sequential work
5. Define verification checkpoints between phases

The plan must be reviewable: a developer joining the project tomorrow should be able to read it and say "yes, that's the right approach."

### Phase 3: Tasks

Break the plan into discrete, implementable tasks:

```markdown
- [ ] Task: [Description]
  - Acceptance: [What must be true when done -- observable]
  - Verify: [Test command, build command, or manual check]
  - Files: [Which files will be touched]
```

Rules:
- Each task completable in a focused session
- Each task has explicit, binary acceptance criteria
- Tasks ordered by dependency, not perceived importance
- No task should require changing more than ~5 files

### Phase 4: Implement

Execute tasks following `incremental-implementation` (one task at a time, test after each). Load only the spec section and source files relevant to the current task.

## Keeping the Spec Alive

- **Update on decision changes**: If the data model changes, update the spec first, then implement
- **Update on scope changes**: Features added or removed must be reflected in the spec
- **Commit the spec**: The spec belongs in version control alongside the code
- **Reference in PRs**: Link back to the spec section each PR implements

## Normative Spec vs Free-Form Context

Split the specification into two artifacts with different jobs, so the spec cannot promise behavior the code does not implement:

- **The normative spec** holds ONLY testable requirements: the `**FR-###**: System MUST/SHALL <capability>` and `**SC-###**: <measurable outcome>` items, plus the acceptance scenarios that verify them. No rationale, no prose narrative, no "why". Every line is a claim the code and tests can be checked against. Prose in the normative spec is a liability: it reads like a commitment but nothing verifies it, so it drifts silently from the code.
- **The free-form context** holds everything that explains the spec but is not itself testable: the rationale, the decisions and their alternatives, constraints, known failure modes, and at least one concrete worked example. Context is where "why session cookies, not JWT" lives; the spec only records "the system MUST authenticate via session cookies".

Map this onto Nexus-Hub's EXISTING surfaces - do not introduce a parallel change-folder tree:

- The normative spec is the `spec.md` this skill already produces from `catalog/templates/spec-template.md` (the FR-### / SC-### blocks). `/spec` creates and updates it.
- The context lives in the surrounding per-version `docs/` tree already in use: the plan, the comparison report, and any decision records under `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`. A dedicated `context.md` beside the spec is fine when a feature warrants one, but the default is the docs tree you already keep.

**The external `openspec` CLI is NOT adopted - only the convention is.** The normative/context separation is a convention Nexus-Hub adopts skill-natively; the external `openspec` tool that popularized it is not added as a dependency. Per the AGENTS.md MCP Registry Policy (reverse-engineer-first: prefer an LLM-native / skill-native convention over an external tool dependency), a convention the agent can follow with its own judgment beats a new CLI, and no parallel `openspec/`-style change-folder tree is created. The convention rides on `/spec`, the spec template, and the per-version `docs/` tree.

## Project-level context (distinct from a feature spec)

Five kinds of context are stable across every feature in a repository: the tech stack, the executable commands, the directory layout, the code-style conventions, and the operating boundaries. They are essential for an agent to work in the codebase, and they are NOT feature-spec content. Restating them in each `spec.md` guarantees that N specs eventually disagree about the build command.

Their home is the project's own instruction file (`AGENTS.md`, `CLAUDE.md`, or the platform equivalent) or the `docs/` context tree, written once and referenced from there. A feature spec inherits them silently.

The five, with the shape each should take where it lives:

- **Tech stack**: framework, language, and key dependencies with versions.
- **Commands**: full executable commands, not tool names. `Build: npm run build`, `Test: npm test -- --coverage`, `Lint: npm run lint --fix`, `Dev: npm run dev`. A bare "we use vitest" is not runnable.
- **Project structure**: where source, tests, and docs live.

    ```
    src/            -> Application source code
    src/components  -> React components
    src/lib         -> Shared utilities
    tests/          -> Unit and integration tests
    docs/           -> Documentation
    ```

- **Code style**: one real code snippet showing the style beats three paragraphs describing it. Include naming conventions, formatting rules, and an example of expected output.
- **Testing strategy**: framework, test locations, coverage targets, and which test level covers which concern.
- **Boundaries**, as a three-tier system:
    - **Always do**: run tests before commits, follow naming conventions, validate inputs.
    - **Ask first**: database schema changes, adding dependencies, changing CI config.
    - **Never do**: commit secrets, edit vendor directories, remove failing tests.

This is the same layering as the normative/context split above, applied one level out: that split separates testable requirements from their rationale within a feature, while this one separates per-feature content from per-project content. A spec that carries project-level context is not merely verbose; it creates a second, staler copy of a fact the instruction file already owns.

## The Spec as a Merge Gate

A change to behavior, a public API, a data schema, or a CLI surface requires the spec to be created or updated BEFORE the code, and the change is not review-ready until the spec, the code, and the tests all agree. This extends the hard gate at the top of this skill (which governs starting new work) to the merge boundary (which governs that a shipped change leaves the spec in sync, not stale).

It composes with tooling Nexus-Hub already has:

- `/spec` creates or updates the normative spec first.
- `[[cross-artifact-analyzer]]` (via `/analyze-spec`) verifies the FR-### / SC-### coverage between the spec and the plan or tasks - the spec-to-task join.
- `[[implementation-convergence]]` closes the loop after implementation: it assesses the built code against the plan/spec, classifies gaps, and appends remaining work, so "the code matches the spec" is a checked assertion, not a hope.
- The merge-readiness contract in `[[quality-gate-definitions]]` treats "spec and code and tests agree" as one condition of a mergeable change, and "a behavior / API / schema / CLI change updated its spec first" is a natural project entry for `[[review-trapdoors]]`.

The rule is scoped on purpose: a typo fix, a refactor with no behavior change, or an internal-only change needs no spec update. It is behavior, API, schema, and CLI surface - the things a consumer can observe - that must not ship ahead of their spec.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is simple -- I don't need a spec" | Simple tasks don't need long specs, but they still need acceptance criteria. A two-line spec is fine. |
| "This is too simple to need a design before I code it" | Simplicity of implementation is independent of agreement on intent. The hard gate is not about effort; it is about whether you and the user agree on what to build. A trivial change built against a wrong assumption is still a rebuild. Present the smallest reviewable design and get the go-ahead -- it costs one turn. |
| "The user said 'just build it', so the gate is satisfied" | "Just build it" before any design exists is a request to skip the design, not approval of one. Present the smallest design in reviewable sections and get an explicit go-ahead first. Approval of the problem is not approval of the design. |
| "The depth rule says small changes get a short spec, so I can skip the approval step" | The depth rule scales the document, never the agreement. It moves one axis and leaves the other exactly where it was: a one-line spec still requires an explicit go-ahead before code. If reading the tier table made the gate feel negotiable, re-read the gate - it says the approval applies regardless of how simple the change looks, and the tier table is a refinement inside that constraint, not an exception to it. |
| "The change is small, so it falls under 'When NOT to use'" | "Small" is an answer to how deep the spec should be, not to whether one is needed. "When NOT to use" covers a single-line fix or a typo, where there is nothing to agree on. A small-but-real change gets the bottom tier: problem, acceptance criteria, Non-Goals. Collapsing the two questions is how a shallow spec turns into no spec. |
| "I'll write the spec after coding" | That's documentation, not specification. The spec's value is forcing clarity *before* code. Writing it after confirms what you built, not what you should have built. |
| "The spec will slow us down" | A 15-minute spec prevents hours of rework. The spec itself is not the slowdown; vague requirements are. |
| "Requirements will change anyway" | That's why the spec is a living document. An outdated spec is still better than no spec -- it shows the intent at the time. |
| "The user knows what they want" | Users know what outcome they want; they rarely know which implementation delivers it. The spec surfaces that gap before code is written. |
| "I'll just use bullet points instead of FR/SC IDs" | The IDs are not decoration - they are the join key the `[[cross-artifact-analyzer]]` skill uses to build the Coverage Summary table in `/analyze-spec`. A spec written with prose bullets produces an empty matrix and the analyzer cannot flag missing tasks. Use the format from `catalog/templates/spec-template.md`. |
| "This feature only has one user story" | Still write it as `### User Story 1 - [Title] (Priority: P1)` with the full Independent Test paragraph and Acceptance Scenarios. The single-story case is the most common; `/analyze-spec` and the Phase 6 task discipline both key off the story heading regardless of count. A spec with no `## User Stories` block fails the analyzer's underspecification pass. |
| "I changed the behavior; I'll sync the spec after" | A behavior / API / schema / CLI change that ships ahead of its spec leaves the spec promising the old contract - the silent drift the spec/context split exists to prevent. Update the normative spec first, then the code and tests, and treat "they disagree" as a merge blocker, not a follow-up. |
| "I'll put the rationale right in the spec so it's all in one place" | Prose in the normative spec reads like a commitment but nothing verifies it, so it drifts from the code silently. Rationale, decisions, and examples belong in the free-form context (the docs tree or a context.md); the spec holds only testable FR-### / SC-### items. |

## Verification

Every item below is checked against the canonical template `catalog/templates/spec-template.md`.

- [ ] A spec document exists as a committed file in the repository, started from `catalog/templates/spec-template.md`
- [ ] `## Problem Statement` names the actor, what fails today, and the observable outcome that marks success
- [ ] `## User Scenarios & Testing` has at least one story headed `### User Story N - [Title] (Priority: PN)`, each with an Independent Test paragraph and Given/When/Then acceptance scenarios
- [ ] `## Requirements` uses `**FR-###**: System MUST <capability>` IDs, sequential and not renumbered
- [ ] `## Success Criteria` uses `**SC-###**` IDs, and each is measurable, technology-agnostic, and verifiable without asking the author
- [ ] `## Non-Goals` is present and non-empty, and every entry carries a reason
- [ ] `## Assumptions` records an informed default for every candidate ambiguity demoted below the 3-marker cap
- [ ] `## Invariants` is present whenever the change touches existing behavior, and each entry is observable enough to assert in a test
- [ ] No more than 3 `[NEEDS CLARIFICATION]` markers remain, and each names a specific question
- [ ] No project-level context (commands, directory layout, code style, tech stack, boundaries) leaked into the spec
- [ ] The human has reviewed and approved the spec before any implementation begins
- [ ] Open questions are listed; none are silently assumed away

## Related Skills

- [[idea-refine]] -- clarify the idea before writing the spec
- [[plan-before-code]] -- detailed implementation planning once the spec is approved
- [[incremental-implementation]] -- execute the plan one task at a time
- [[ambiguity-detector]] -- detect gaps in an existing spec before implementation
- [[cross-artifact-analyzer]] -- verify the FR-### / SC-### IDs in the spec have matching tasks in the plan via the Coverage Summary table emitted by `/analyze-spec`
- [[implementation-convergence]] -- after implementation, assess the built code against the spec/plan, classify gaps, and append remaining work (the merge-gate's post-build check)
- [[review-trapdoors]] -- "a behavior / API / schema / CLI change must update its spec first" is a natural project review trapdoor
- [[quality-gate-definitions]] -- its merge-readiness contract treats "spec, code, and tests agree" as one condition of a mergeable change
- [[project-constitution]] -- establish the MUST/SHOULD principles that the `Constitution Check` section of every plan validates against
- `/clarify-spec` (Phase 5 command) -- sequential 5-question loop that resolves spec ambiguities after the template's slots are filled; pairs with the spec-quality-checklist for the final readiness gate before `/generate-plan`

## Methodology essay

For the broader motivation behind treating the specification as the source of truth that code compiles from, see `docs/archives/v2/v2.1/spec-driven-methodology.md`. The essay covers the power inversion (specs lead, code follows), the seven-station Nexus-Hub SDD workflow, the six core principles, and the pitfalls / anti-patterns (over-specifying the trivial, hiding behind the gate, treating the analyzer as a linter).
