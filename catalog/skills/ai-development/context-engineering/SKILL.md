---
name: context-engineering
description: "Designs and manages the information loaded into an AI session to maximize task effectiveness. Use when an AI agent is producing poor results due to missing context, when tasks require many files and the context window is filling with noise, or when designing prompts for production AI systems. Distinct from token optimization (which reduces cost) -- this skill shapes what information is present and in what form. Trigger phrases: context engineering, load the right context, improve AI context, shape the context window, context management for agents."
summary_l0: "Shape AI session context deliberately to maximize task effectiveness, not just reduce token count"
overview_l1: "This skill teaches deliberate, structured context shaping for AI coding sessions -- distinct from token cost reduction. Use it when AI agent output quality is limited by what information is available in the context window, when a task requires many files and relevant information is being crowded out, or when building production AI systems that must handle complex multi-step tasks. Key capabilities include progressive context loading (load what is needed for the current step only), information hierarchy design (most important facts first), task-scoped context pruning, and context refresh between session phases. The expected output is an AI session that produces higher-quality results because the right information is present at the right time -- not because more tokens are consumed. Trigger phrases: context engineering, context window management, load the right context, agent context design, improve AI quality through context."
---

# Context Engineering

Shape what information is present in an AI session so the agent produces the best possible output for the current task -- not just fewer tokens, but the *right* tokens.

## When to Use This Skill

Use when:
- AI output quality is poor and the likely cause is missing or irrelevant context
- The task requires many files and you need to decide what to load and when
- Designing a multi-phase workflow where each phase needs different context
- Building production AI systems where prompt design is part of the architecture
- An AI session is long and earlier context may be contaminating later outputs

**When NOT to use:** When the task is simple enough to fit in one context load without thought. Use `context-optimization` if the primary goal is token cost reduction. Use `context-compression` if the session is too long and needs summarization.

## Core Principle: Context is a Design Decision

Context engineering is not about cramming more information into the window. It is about designing *which information* is present *at which point* in a task.

The mental model:
```
Good context = relevant signal at the right moment
Bad context  = relevant signal buried in noise
              OR missing signal at the moment it matters
```

## Instructions

### Step 1: Define the Context Budget

Before loading any files, answer these three questions:

1. **What is the AI trying to accomplish right now?** (Not the whole feature -- the current step)
2. **What does it need to know to do that?** (Minimum information set)
3. **What would distract it?** (Everything else)

Use a context budget table:

| Information | Needed now? | When needed | Load strategy |
|---|---|---|---|
| Full system architecture | No | Overview only at start | Load summary, not full ADR set |
| The 3 files being modified | Yes | Now | Load in full |
| Test file for the component | Yes | After implementation | Load when writing tests |
| Unrelated service code | No | Never | Do not load |

### Step 2: Layer Context Progressively

Do not front-load all context at the start of a session. Load context in layers matching the task phases:

**Layer 1: Orientation** (session start)
- Project identity: name, purpose, tech stack (from README or CLAUDE.md -- not full docs)
- Current task goal: one paragraph
- The specific files that will be changed

**Layer 2: Task execution** (during implementation)
- Only the files relevant to the current step
- Related tests for the component being changed
- Any interfaces or contracts this code must satisfy

**Layer 3: Verification** (after implementation)
- Test runner output
- Linting output
- The acceptance criteria from the spec

Clear Layer 1 context before loading Layer 3 context if the session is long.

### Step 3: Use Summaries at Boundaries

When a large file or document must be referenced but not read in full, provide a structured summary at the boundary:

```
ARCHITECTURE SUMMARY (full doc at docs/ARCHITECTURE.md):
- Services: auth-service, user-service, notification-service
- Auth uses JWT stored in httpOnly cookies
- Services communicate via REST; async events via Redis Pub/Sub
- Database: PostgreSQL with Prisma ORM
→ Load full doc only if you need schema details or service-to-service contracts.
```

This preserves the AI's ability to decide whether to load the full doc without consuming the full context upfront.

### Step 4: Scope Context to the Current Task

When a multi-step plan is being executed (see `incremental-implementation`), refresh the context at each task boundary:

```
CONTEXT FOR CURRENT TASK: Add email validation to createUser
Loading: src/handlers/users.ts, tests/handlers/users.test.ts, src/validators/index.ts
Not loading: All other handlers (irrelevant), full test suite (too large), database schema (not needed for this task)
```

Scoping context this way prevents the AI from "remembering" details from a previous task that no longer apply.

### Step 5: Design for Context Refresh

For long sessions, plan explicit context refresh points between phases:

- Before switching from planning to implementation: summarize the approved plan in one paragraph
- Before switching from implementation to testing: summarize what was built
- Before a code review step: clear implementation details; load only the diff and acceptance criteria

Context refreshes prevent earlier decisions from silently influencing later outputs.

## Information Hierarchy

When loading multiple pieces of information, order them by importance to the current task:

```
1. MOST IMPORTANT: Current task goal + acceptance criteria
2. ESSENTIAL: The files being changed
3. REFERENCE: Interfaces/contracts those files must satisfy
4. BACKGROUND: Architectural context (summarized)
5. OMIT: Everything else
```

Information at the bottom of the context window has less influence on output than information at the top. Put the most decision-critical information first.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Load everything -- the model will figure out what's relevant" | Models weight recent and prominent context more than buried context. Noise degrades signal. Curated context outperforms complete context. |
| "More context is always better" | More relevant context is better. More total context is not. Information about unrelated services, old decisions, and irrelevant tests competes with the signal you need. |
| "Context management is overhead" | Poor context management causes re-work cycles, hallucinated function signatures, and missed constraints. The overhead is in the rework, not the engineering. |
| "Just summarize everything at the start" | Summaries lose specificity. Load specific, relevant files for specific tasks rather than summaries of everything. |

## Verification

- [ ] A context plan exists for the task (even if informal): what is loaded, what is not, and why
- [ ] Context loads are scoped to the current step -- not the entire feature at once
- [ ] Large documents are represented by summaries with explicit "load if needed" pointers
- [ ] Context is refreshed between significantly different task phases (planning → implementation → testing)
- [ ] The AI's output for the current step does not contain hallucinated details about unloaded context

## Related Skills

- [[context-optimization]] -- reduces token cost and context window bloat
- [[context-compression]] -- compresses long sessions to fit within context limits
- [[context-manager]] -- manages context across large codebases with attention budgeting
- [[plan-before-code]] -- defines the task structure that determines what context each step needs
- [[incremental-implementation]] -- executes one step at a time, enabling scoped context loads
- [[code-semantic-search]] -- retrieval-based context shaping for source-code corpora; specialized over the general rag-implementation skill
- [[context-pack-builder]] -- distills prior-session context into a committed pack you can load as a Layer-1 orientation artifact for the current task
