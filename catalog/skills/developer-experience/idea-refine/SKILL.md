---
name: idea-refine
description: "Refines raw ideas and vague requests into concrete, buildable problem statements before any planning or coding begins. Use when a task is described as a vague goal, a user story without acceptance criteria, a \"what if we...\" conversation, or anything that starts without a clear definition of done. Trigger phrases: refine this idea, I'm thinking about, help me figure out what to build, is this worth building, what should I actually make."
summary_l0: "Refine vague ideas into concrete problem statements with clear success criteria"
overview_l1: "This skill transforms vague goals, rough ideas, and ambiguous requests into concrete, buildable problem statements. Use it before any planning or specification work begins, especially when the task is described as a feeling, a direction, or a 'what if' rather than a clear requirement. Key capabilities include stakeholder intent extraction, assumption surfacing, scope bounding, success criteria formulation, and build-vs-buy-vs-wait decision framing. The expected output is a single refined problem statement with: the core user need, explicit constraints, definition of done in observable terms, and identified open questions. Without this skill, planning and implementation risk solving the wrong problem with the right code. Trigger phrases: refine this idea, I'm thinking about building, help me figure out what to make, is this worth building, what should I actually build."
---

# Idea Refine

Transform a vague direction into a concrete problem statement before any design, planning, or code is written. The most expensive mistake in software is building the right solution to the wrong problem.

## When to Use This Skill

Use when:
- The request is a goal, direction, or desire rather than a requirement ("make it faster", "add AI to the dashboard", "we should do something about onboarding")
- There is no clear definition of done
- Multiple interpretations of the request are plausible
- The request is for a new feature with no existing specification
- You are about to invest significant time and want to confirm alignment first

**When NOT to use:** When requirements are already specific and testable. If the task has explicit acceptance criteria and a clear scope, skip directly to `spec-driven-development` or `plan-before-code`.

## Instructions

### Step 1: Restate the Idea Neutrally

Echo back the idea in your own words without interpreting it yet. This confirms your understanding and gives the human a chance to correct misreadings before you invest in analysis.

```
I hear: "You want to [X] so that [Y]. Is that right?"
```

If the idea is multi-part, list each component separately and confirm which is the priority.

### Step 2: Surface the Real Problem

Ask one focused clarifying question at a time. Do not interrogate with a list of 10 questions. Common areas where vague ideas hide real problems:

**User**: Who specifically experiences this problem? In what context?
**Pain**: What happens today without this? How painful is that, concretely?
**Frequency**: How often does this occur? For how many people?
**Previous attempts**: Has this been tried before? Why did it fail or not get built?

Reframe from "what to build" to "what problem to solve":

```
Instead of: "We want a notification system"
Ask: "What is the user failing to do today because they don't get notified?"
```

### Step 3: Bound the Scope

Vague ideas are infinite. Good problem statements are bounded. Explicitly define:

- **In scope**: What this must do for the problem to be considered solved
- **Out of scope**: What it explicitly does not need to do (prevents scope creep)
- **Later**: Good ideas that are real, but belong in a future iteration

Use the following test: "If we shipped X and nothing else, would the core problem be solved?" If no, X is not the minimal scope. If yes, add nothing more.

### Step 4: Define Success in Observable Terms

Convert every "it should feel better" or "users will like it" statement into something you can measure or observe:

| Vague goal | Observable success criterion |
|---|---|
| "Make it faster" | Dashboard LCP < 2.5s on 4G |
| "Improve onboarding" | User activates within 24h of signup (activation = first core action taken) |
| "Add AI" | The AI suggestion is accepted by users ≥ 40% of the time |
| "Better error messages" | Support tickets mentioning error X drop by 50% |

At least one success criterion must be binary (either it happened or it did not).

### Step 5: Identify Open Questions

List what is genuinely unknown and must be resolved before design or planning can begin. Separate these from "nice to know" questions that do not block progress.

Format:
```
BLOCKING (must resolve before planning):
- [ ] Does the backend support real-time events, or do we need to add infrastructure?
- [ ] What is the target release date?

NON-BLOCKING (can assume for now, revisit later):
- [ ] Exact visual design of the notification panel
- [ ] Whether to support push notifications (mobile)
```

**3-marker cap aligned with `[[spec-driven-development]]` and `[[ambiguity-detector]]`**: when the problem statement carries open questions that would persist into the spec phase, format them as inline `[NEEDS CLARIFICATION: <specific question>]` markers and apply a hard cap of 3 total. Refinement of vague ideas should produce no more than 3 outstanding markers; resolve the rest via informed defaults (write them into the BLOCKING vs NON-BLOCKING split above, or as an `## Assumptions` subsection of the problem statement). Prioritize markers per `scope > security/privacy > UX > technical` - the same priority order downstream skills use. A problem statement that surfaces 8 markers signals the refinement is not done; force triage and resolve at least 5 of them through informed defaults before handing off to `[[spec-driven-development]]`.

**Boundary with `/clarify-spec`**: `idea-refine` operates BEFORE a spec exists - input is a vague idea or `[NEEDS CLARIFICATION]`-laden problem statement; output is a one-page problem statement with a bounded scope and observable success criteria. `/clarify-spec` (the command driven by Phase 5 of the adoption-spec-kit plan) operates AFTER `spec.md` is written - input is an already-structured spec with FR-### / SC-### IDs; output is the same spec with ambiguities resolved at the requirement and user-story granularity through a sequential 5-question loop. Use `idea-refine` to decide *what to build*; use `/clarify-spec` to lock down *how a written spec should behave*. Do not invoke `/clarify-spec` against a vague problem statement - it expects the structured template from `catalog/templates/spec-template.md`.

### Step 6: Write the Problem Statement

Synthesize the above into one page or less:

```markdown
## Problem Statement: <Name>

**User**: <Who>
**Context**: <In what situation>
**Problem**: <What fails today>
**Impact**: <Why this matters, quantified if possible>

**In Scope**
- <Observable thing this must do>

**Out of Scope**
- <What we are deliberately not solving>. Reason: <deferred, separate initiative, not validated, or too expensive>

**Success Criteria**
- [ ] <Observable criterion 1>
- [ ] <Observable criterion 2>

**Open Questions (blocking)**
- [ ] <Question>
```

The **Out of Scope** block above is the upstream producer of the spec's `## Non-Goals` section in `catalog/templates/spec-template.md`; the hand-off is a copy, which is why each entry carries its reason here rather than gaining one later. Likewise the **Problem Statement** heading feeds the spec's `## Problem Statement` section.

Once the human approves this statement, hand off to `spec-driven-development` or `plan-before-code`. Note that approving the problem statement here is a separate approval from approving the *design*. The `spec-driven-development` hard gate still requires an explicit design approval before any code is written; do not treat a green light on the problem as a green light to implement.

## Interactive grill mode (opt-in)

Enter this mode ONLY when the user explicitly asks for it (trigger phrases: "grill me", "stress-test this plan", "interrogate my design", "poke holes in this"). It is NOT the default behavior of `idea-refine`, and it is NOT how any routine clarifying step works.

Once invoked, interview the user relentlessly about the plan or design:

- **Walk the decision tree branch by branch.** Take one branch at a time, resolve the dependencies between decisions, and do not jump ahead until the current branch is settled.
- **One question at a time.** Ask a single question and wait for the answer before asking the next, so each decision is pressure-tested in isolation.
- **Always recommend an answer.** For every question, offer your own recommended answer with a one-line rationale, so the user reacts to a concrete proposal rather than starting from a blank page.
- **Explore before asking.** When a question can be answered by reading the codebase, explore the codebase and answer it yourself instead of asking the user.

**Exit condition.** The mode ends when the branches are resolved and there is shared understanding of the design. At that point, summarize the resolved decisions so the outcome is captured, then hand back to the normal flow (`spec-driven-development` or `plan-before-code`).

**Gating (read before using this mode).** This one-question-at-a-time loop is an opt-in interactive mode. It does NOT change Nexus-Hub's default convention, which is to BATCH clarifying questions into a single consolidated turn rather than asking one per turn (see the global batch-not-ping-pong rule and the "batch, not ping-pong" instruction in [[doc-coauthoring]]). Outside this explicitly-invoked mode the agent still batches its clarifying questions; never let the grill loop become the default clarifying behavior.

Related: [[ambiguity-detector]] is the structured, non-interactive way to detect the same gaps this mode probes by hand; [[plan-review]] runs parallel-persona review of a finished plan (the non-interactive counterpart to grilling); and the `/spec clarify` scope resolves ambiguities in an already-written spec at the requirement granularity.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The idea is obvious -- let's just build it" | The idea is obvious to you; the user's actual need is still unverified. 30 minutes of clarification prevents 2 weeks of wrong implementation. |
| "We'll figure out the details as we go" | That's not agility -- that's guessing. Scope defined during coding inflates scope by 3-5x. |
| "I've built this before, I know what they want" | Every context is different. The user's situation, constraints, and definition of success may not match your mental model. |
| "We don't have time for this" | You don't have time to rebuild after shipping the wrong thing. A problem statement takes under an hour. |
| "The user knows what they want" | Users know what outcome they want; they rarely know which solution will deliver it. That gap is the job. |

## Verification

- [ ] A written problem statement exists (not just a verbal agreement)
- [ ] Success criteria are stated in observable, testable terms (not "users will be happy")
- [ ] Scope is explicitly bounded: at least one thing is declared out of scope
- [ ] Blocking open questions are listed; none are quietly assumed away
- [ ] The human has reviewed and confirmed the problem statement in writing

## Related Skills

- [[spec-driven-development]] -- next step after a confirmed problem statement; writes the full technical spec
- [[ambiguity-detector]] -- detects ambiguous, incomplete, or contradictory requirements in existing specs
- [[requirement-enhancer]] -- improves an existing requirement's quality, testability, and completeness
- [[plan-before-code]] -- planning phase after the spec is confirmed
- [[design-interview]] -- interview engine for unresolved design branches and the CONTEXT.md glossary; invoke it after the problem is named, do not use it as a substitute for this skill
