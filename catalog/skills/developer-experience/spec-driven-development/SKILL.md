---
name: spec-driven-development
description: Writes a structured technical specification before any code is written. Use when starting a new project, feature, or significant change and no written specification exists — especially when requirements are ambiguous, the change touches multiple files, or architectural decisions must be made. Trigger phrases: write a spec, create a specification, spec this out, define the requirements, spec-driven, write the spec before coding.
summary_l0: "Write a structured specification before coding to prevent rework from misunderstood requirements"
overview_l1: "This skill produces a written technical specification before implementation begins, following a four-phase gated workflow: Specify → Plan → Tasks → Implement. Use it when requirements are ambiguous, the change spans multiple files or modules, or you are making an architectural decision. Key capabilities include assumption surfacing, success criteria formulation, project structure definition, boundaries (Always/Ask/Never), and task breakdown with per-task acceptance criteria. The spec is committed to the repo as a living document — updated as decisions change, referenced in PRs, and never discarded after implementation begins. Without this skill, implementation risks solving the wrong problem or building an architecture that does not match the team's intent. Trigger phrases: write a spec, spec this out, create a specification, define requirements, spec before coding, what should I build."
---

# Spec-Driven Development

Write a structured specification before writing any code. The spec is the shared source of truth between you and the human engineer — it defines what we're building, why, and how we'll know it's done. Code without a spec is guessing.

## When to Use This Skill

Use when:
- Starting a new project or feature with no written requirements
- Requirements exist only as a verbal description or a vague request
- The change touches multiple files or modules
- You are about to make an architectural decision
- The task would take more than 30 minutes to implement

**When NOT to use:** Single-line fixes, typo corrections, or changes where requirements are unambiguous and self-contained. If you already have a well-defined spec, move directly to `plan-before-code`.

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

Use `catalog/templates/spec-template.md` (installed at `~/.nexus-hub/templates/spec-template.md`) as the starting skeleton for every feature spec. The template enforces the convention that downstream tooling depends on - in particular, the `**FR-###**: System MUST <capability>` format for functional requirements and the `**SC-###**: <measurable outcome>` format for success criteria.

Why the FR-### / SC-### IDs matter: the `[[cross-artifact-analyzer]]` skill (run via `/analyze-spec`) builds a Coverage Summary table by matching each FR-### and SC-### in the spec against the task descriptions in the plan or tasks.md. A spec written with prose bullets instead of FR-### / SC-### IDs produces an empty coverage matrix and the analyzer cannot flag missing tasks. The IDs are the contract between the spec and the analyzer.

Stability rules for IDs:

- IDs are sequential within their category (FR-001, FR-002, ...; SC-001, SC-002, ...).
- IDs are stable - once an FR or SC is assigned an ID, do not renumber on edits. Removing a requirement leaves a gap in the sequence; do not backfill.
- IDs are unique within the spec but not globally across the project - FR-001 in `specs/003-auth/spec.md` is a different requirement from FR-001 in `specs/004-billing/spec.md`.

The template also reserves three additional mandatory blocks: User Scenarios & Testing, Requirements (with FR-### IDs and an optional Key Entities subsection), and Success Criteria (with SC-### IDs). An Assumptions section is mandatory whenever any candidate ambiguity was demoted below the 3-marker hard limit.

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

Write a spec document covering six core areas:

**1. Objective** — What are we building and why? Who is the user? What does success look like in observable terms?

**2. Commands** — Full executable commands, not just tool names:
```
Build: npm run build
Test: npm test -- --coverage
Lint: npm run lint --fix
Dev: npm run dev
```

**3. Project Structure** — Where source code lives, where tests go, where docs belong:
```
src/           → Application source code
src/components → React components
src/lib        → Shared utilities
tests/         → Unit and integration tests
docs/          → Documentation
```

**4. Code Style** — One real code snippet showing your style beats three paragraphs describing it. Include naming conventions, formatting rules, and examples of expected output.

**5. Testing Strategy** — Framework, test locations, coverage targets, which test levels cover which concerns.

**6. Boundaries** — Three-tier system:
- **Always do**: Run tests before commits, follow naming conventions, validate inputs
- **Ask first**: Database schema changes, adding dependencies, changing CI config
- **Never do**: Commit secrets, edit vendor directories, remove failing tests

**Success Criteria**: Reframe instructions as testable conditions:
```
REQUIREMENT: "Make the dashboard faster"

REFRAMED:
- Dashboard LCP < 2.5s on 4G connection
- Initial data load completes in < 500ms
- No layout shift during load (CLS < 0.1)
→ Are these the right targets?
```

**Spec template:**
```markdown
# Spec: [Project/Feature Name]

## Objective
[What we're building, who the user is, success criteria]

## Tech Stack
[Framework, language, key dependencies with versions]

## Commands
[Build, test, lint, dev — full commands]

## Project Structure
[Directory layout with descriptions]

## Code Style
[Example snippet + key conventions]

## Testing Strategy
[Framework, test locations, coverage requirements]

## Boundaries
- Always: [...]
- Ask first: [...]
- Never: [...]

## Success Criteria
[Observable, testable conditions — not aspirations]

## Open Questions
[Unresolved items that need human input before implementation]
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
  - Acceptance: [What must be true when done — observable]
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

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is simple — I don't need a spec" | Simple tasks don't need long specs, but they still need acceptance criteria. A two-line spec is fine. |
| "I'll write the spec after coding" | That's documentation, not specification. The spec's value is forcing clarity *before* code. Writing it after confirms what you built, not what you should have built. |
| "The spec will slow us down" | A 15-minute spec prevents hours of rework. The spec itself is not the slowdown; vague requirements are. |
| "Requirements will change anyway" | That's why the spec is a living document. An outdated spec is still better than no spec — it shows the intent at the time. |
| "The user knows what they want" | Users know what outcome they want; they rarely know which implementation delivers it. The spec surfaces that gap before code is written. |
| "I'll just use bullet points instead of FR/SC IDs" | The IDs are not decoration - they are the join key the `[[cross-artifact-analyzer]]` skill uses to build the Coverage Summary table in `/analyze-spec`. A spec written with prose bullets produces an empty matrix and the analyzer cannot flag missing tasks. Use the format from `catalog/templates/spec-template.md`. |
| "This feature only has one user story" | Still write it as `### User Story 1 - [Title] (Priority: P1)` with the full Independent Test paragraph and Acceptance Scenarios. The single-story case is the most common; `/analyze-spec` and the Phase 6 task discipline both key off the story heading regardless of count. A spec with no `## User Stories` block fails the analyzer's underspecification pass. |

## Verification

- [ ] A spec document exists as a committed file in the repository
- [ ] The spec covers all six core areas (Objective, Commands, Structure, Style, Testing, Boundaries)
- [ ] Success criteria are specific and observable — not "it works well" but "test X passes and metric Y is met"
- [ ] Boundaries (Always/Ask First/Never) are defined and non-empty
- [ ] The human has reviewed and approved the spec before any implementation begins
- [ ] Open questions are listed; none are silently assumed away

## Related Skills

- `idea-refine` — clarify the idea before writing the spec
- `plan-before-code` — detailed implementation planning once the spec is approved
- `incremental-implementation` — execute the plan one task at a time
- `ambiguity-detector` — detect gaps in an existing spec before implementation
- `cross-artifact-analyzer` — verify the FR-### / SC-### IDs in the spec have matching tasks in the plan via the Coverage Summary table emitted by `/analyze-spec`
- `project-constitution` — establish the MUST/SHOULD principles that the `Constitution Check` section of every plan validates against
- `/clarify-spec` (Phase 5 command) — sequential 5-question loop that resolves spec ambiguities after the template's slots are filled; pairs with the spec-quality-checklist for the final readiness gate before `/generate-plan`

## Methodology essay

For the broader motivation behind treating the specification as the source of truth that code compiles from, see `docs/v2.1.0/spec-driven-methodology.md`. The essay covers the power inversion (specs lead, code follows), the seven-station Nexus-Hub SDD workflow, the six core principles, and the pitfalls / anti-patterns (over-specifying the trivial, hiding behind the gate, treating the analyzer as a linter).
