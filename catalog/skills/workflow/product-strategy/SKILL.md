---
name: product-strategy
description: Author and maintain a durable product-strategy anchor (STRATEGY.md or docs/<version>/strategy.md) that declares the target problem, the chosen approach, the target persona, the key metrics, and the active work tracks - the upstream framing that ideation, brainstorming, and planning read as grounding. Make sure to use this skill whenever the user says "write a strategy", "what is our product strategy", "define the target problem", "who is this for", "what metrics matter", "set the product direction", "create a STRATEGY.md", "update the strategy", "what are our bets", "what tracks are we working on", or otherwise wants to capture or revise the product-level framing that should bound every downstream idea and plan. SKIP, do NOT use for, governance MUST / SHOULD rules and architectural invariants (use project-constitution), refining one vague idea into a single problem statement (use idea-refine), per-version unfinished-work logging (use known-gaps-tracker), or a single feature's requirements (use spec-driven-development).
summary_l0: "Author and maintain a STRATEGY.md anchor (problem, approach, persona, metrics, tracks) for planning grounding"
overview_l1: "Produces and maintains a durable product-strategy anchor at STRATEGY.md (repo root) or docs/<version>/strategy.md. The anchor is distinct from the project constitution: the constitution declares MUST / SHOULD governance rules, while the strategy declares product framing - the target problem, the chosen approach, the target persona, the key metrics, and the active work tracks (the current bets). The skill defines the anchor's five required sections, an authoring flow, and an amendment flow that revises changed sections and bumps Last updated. Ideation, brainstorming, and planning read this anchor as grounding so new work traces back to a stated problem and metric instead of drifting. Everything is local and zero-outbound. Trigger phrases: write a strategy, what is our product strategy, define the target problem, who is this for, what metrics matter, set the product direction, what are our bets, what tracks are we working on."
---

# Product Strategy

Author and maintain a durable product-strategy anchor that states, in one place, what problem the product solves, the approach it takes, who it is for, how success is measured, and which bets are active right now. This anchor is the upstream framing of the compound loop: ideation, brainstorming, and planning read it as grounding so every new idea and plan traces back to a stated problem and metric rather than drifting.

The strategy anchor is **product framing**, not **governance**. It is the sibling of [[project-constitution]]: the constitution declares the MUST / SHOULD rules every plan must obey; the strategy declares the problem and persona every plan should serve. Both are durable, versioned context; neither replaces the other.

Everything this skill does is local and zero-outbound: it reads the repo and the current session, then writes (or amends) exactly one Markdown file. It never uploads the strategy and never calls an external service.

## When to Use This Skill

Use when:

- The user wants to **write, set, or capture the product strategy / product direction** for a project for the first time.
- The user wants to **declare the target problem, the target persona, the key metrics, or the active tracks** ("who is this for", "what metrics matter", "what are our bets").
- The user wants to **amend an existing strategy** (the problem sharpened, the persona shifted, a track opened or closed, a metric changed).
- Ideation or planning is starting and there is **no stated framing to ground it** - author the anchor first, then plan against it.

**When NOT to use:**

- Declaring MUST / SHOULD governance rules, architectural invariants, or non-negotiables - use [[project-constitution]].
- Refining one vague idea into a single concrete problem statement - use [[idea-refine]] (its output can feed the Target Problem section here).
- Logging per-version unfinished work, deferrals, or bugs - use [[known-gaps-tracker]].
- Writing the requirements for a single feature - use [[spec-driven-development]].
- Any flow that sends the strategy to an external service or shared store. This skill is local-only by design.

## File Location

**Recommended**: `STRATEGY.md` at the repo root - the strategy is usually stable across many versions and benefits from one canonical, easy-to-find path that ideation and planning can always locate.

**Acceptable**: `docs/<version>/strategy.md` - when the strategy is being re-framed per release cycle and you want it to evolve in the same version folder as the plans that cite it.

Default to the repo-root path. If the file already exists at either location, amend it in place rather than creating a second copy.

## Anchor Structure

The anchor has five required sections. Keep each tight - the value is in the framing being unambiguous, not in length.

```markdown
# Product Strategy

**Project**: <name>
**Last updated**: <YYYY-MM-DD>

## Target Problem

<The specific problem this product solves, stated as a problem (not a solution). One short paragraph. What pain, for whom, and why it matters now.>

## Approach

<The chosen approach to solving the problem and why this approach over the obvious alternatives. One short paragraph. This is the strategic bet, not the implementation detail.>

## Target Persona

<Who the product is for - the primary user and, if relevant, the secondary. Concrete enough that a feature idea can be tested against "does this serve them?". Avoid "everyone".>

## Key Metrics

<The 2-5 observable signals that tell you the approach is working for the persona. Each metric is a name plus what a good value looks like. These are outcome metrics, not vanity counts.>

## Tracks

<The active bets / workstreams currently in flight, each one line: <track name> - <the outcome it pursues>. Closed or paused tracks move to a "## Tracks (closed)" list with a one-line reason so the history is legible.>
```

## Instructions

### Authoring a new anchor

1. Confirm the file location (default `STRATEGY.md` at the repo root).
2. Collect each of the five sections. For each, ask one focused question and write one tight paragraph or list:
    - **Target Problem**: "What problem does this product solve, for whom, and why now?" (If [[idea-refine]] already produced a problem statement, reuse it.)
    - **Approach**: "What is the approach, and why this approach over the obvious alternative?"
    - **Target Persona**: "Who is the primary user? Any important secondary?"
    - **Key Metrics**: "What 2-5 outcomes tell you it is working?"
    - **Tracks**: "What bets / workstreams are active right now?"
3. Write the file with the header block (`Project`, `Last updated` = today) and the five sections. Do not invent content the user did not provide; mark genuine unknowns with a short `(TBD: <question>)` rather than guessing.
4. Tell the user the anchor exists and that planning (`/generate-plan`) and ideation now read it as grounding.

### Amending an existing anchor

1. Read the existing anchor. Identify which of the five sections is changing.
2. Revise only the changed section(s). Move any retired track to `## Tracks (closed)` with a one-line reason; never silently delete a track (the history is part of the framing).
3. Update `Last updated` to today.
4. Write the file in place.

### Grounding read (how downstream skills use it)

When [[implementation-plan]] / `/generate-plan`, [[idea-refine]], or a brainstorming flow runs, it should read the anchor and check the new idea or plan against the Target Problem, Persona, and Key Metrics. An idea that serves no stated persona or moves no stated metric is a signal either to drop the idea or to amend the strategy - surface that tension rather than planning around it.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We already have a constitution, that covers strategy" | The constitution declares rules (MUST / SHOULD) the project obeys; the strategy declares the problem and persona the project serves. A plan can pass every constitutional gate and still build the wrong thing for the wrong user. They are complementary, not substitutes. |
| "The strategy is obvious / in everyone's head" | In-everyone's-head framing cannot be read by a planning skill or a new contributor, and it drifts silently. A half-page anchor is what lets ideation and `/generate-plan` test ideas against a stated problem and metric. |
| "Let me list ten metrics to be thorough" | Ten metrics measure nothing - the team cannot move ten numbers at once and a reviewer cannot tell which idea matters. Cap at 2-5 outcome metrics; vanity counts (page views, total users) belong in a dashboard, not the strategy. |
| "I'll write the approach as a feature list" | A feature list is not an approach. The Approach section is the strategic bet (why this path beats the obvious alternative); features are downstream of it and belong in plans and specs. |
| "Just delete the track we paused" | Deleting a paused track erases why it was a bet and why it stopped, so it gets re-proposed later. Move it to `## Tracks (closed)` with a one-line reason instead. |
| "I should push this to the team wiki so everyone sees it" | Out of scope and against the local-only design. This skill writes to the repo only. Syncing to an external store is an outbound flow the MCP Registry Policy governs; the team wires that explicitly, not through this skill. |

## Verification

- [ ] Exactly one anchor file exists (`STRATEGY.md` at the repo root or `docs/<version>/strategy.md`), not both.
- [ ] The header block has `Project` and `Last updated` (ISO `YYYY-MM-DD`), and `Last updated` is today on any write.
- [ ] All five required sections are present: Target Problem, Approach, Target Persona, Key Metrics, Tracks.
- [ ] Target Problem is stated as a problem (a pain + who + why now), not as a solution or feature list.
- [ ] Key Metrics lists 2-5 outcome metrics, each with a name and what a good value looks like.
- [ ] Any retired track is in `## Tracks (closed)` with a one-line reason (no track was silently deleted).
- [ ] No content was invented for the user; genuine unknowns are marked `(TBD: ...)`.
- [ ] No network call, upload, or external store write occurred.

## Related Skills

- [[project-constitution]] - the governance sibling: it declares MUST / SHOULD rules; this skill declares the product framing those rules serve. Author both for a project that wants its plans grounded in problem and rule.
- [[idea-refine]] - refines one vague idea into a concrete problem statement; its output is a natural input to this anchor's Target Problem section.
- [[implementation-plan]] - reads this anchor (via `/generate-plan`) as grounding so each plan traces back to a stated problem, persona, and metric.
- [[solution-knowledge-base]] - the downstream capture half of the compound loop; the strategy frames the problem, solved-problem docs record how problems were resolved.
- [[known-gaps-tracker]] - records what slipped per version; a recurring gap may signal a track that needs opening or closing in this anchor.
