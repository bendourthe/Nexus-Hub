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
