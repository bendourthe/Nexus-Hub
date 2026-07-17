---
name: doc-coauthoring
description: "Guide users through a structured 3-stage workflow for co-authoring documentation - specs, proposals, decision docs, RFCs, ADRs, technical writeups, and long-form internal memos. Use whenever the user wants to co-write a doc, draft a proposal, refine documentation iteratively, brainstorm a writeup, or pair on a longer-form written artifact, even if they don't explicitly say \"co-author\". Covers Stage 1 (Context Gathering), Stage 2 (Refinement and Structure), and Stage 3 (Reader Testing). SKIP: simple READMEs that don't need a workflow, single-paragraph commit messages, one-line code comments, or quick inline questions that resolve in one turn."
summary_l0: "Guide users through a 3-stage workflow for co-authoring documentation"
overview_l1: "This skill drives a 3-stage co-authoring workflow for any non-trivial written artifact: specs, proposals, decision docs, RFCs, ADRs, technical memos, and long-form internal writeups. Stage 1 - Context Gathering surfaces the audience, the purpose, prior art, and constraints before any prose is written. Stage 2 - Refinement and Structure produces an outline, then a draft, then iterates on shape until the structure carries the argument. Stage 3 - Reader Testing simulates a fresh reader who has not seen the conversation, identifies the gaps that drop them, and closes those gaps. The output is a doc that holds together for someone who reads it cold, not just for the author who already knows the answer. Trigger phrases: co-author, co-write, draft a proposal, write a spec, write an RFC, write an ADR, decision doc, technical writeup, internal memo, refine documentation, iterate on a doc."
---

# Doc Co-authoring Workflow

A structured three-stage workflow for co-authoring any non-trivial written artifact - specs, proposals, decision docs, RFCs, ADRs, technical memos, internal writeups - where the author and the agent iterate together rather than the agent generating a one-shot draft. Each stage produces a tangible artifact that the next stage builds on, so the doc that ships is the one that survived Stage 3 reader testing, not the one the agent guessed at in Stage 2.

## When to Use This Skill

Use this skill when the user wants to:

- Co-write a specification, RFC, ADR, design doc, or product proposal
- Draft a long-form decision doc that needs to convince a reader who is not in the room
- Iterate on a documentation page that has a real audience and a real purpose
- Write a technical writeup, post-mortem, or incident report that other people will read cold
- Pair on an internal memo, briefing, or strategy doc where structure carries the argument

**Trigger phrases**: "co-author", "co-write", "let's draft", "help me write a spec / RFC / ADR / proposal / design doc", "write up a decision", "write a memo", "draft the writeup", "iterate on this doc", "refine this proposal", "structure this writeup".

**When NOT to use**:

- Simple READMEs or one-page docs that do not need a workflow (use `documentation/user-documentation` directly)
- Single-paragraph commit messages or PR descriptions (use `workflow/code-commit-workflow`)
- One-line comments inside source code (use `documentation/strategic-comments`)
- A quick inline question that resolves in a single turn
- Pure copy-editing on an already-structured draft (use `developer-experience/writing-editing`)

If the doc is short, has one obvious audience, and has one obvious purpose, the workflow is overhead. The workflow earns its keep when at least one of audience, purpose, prior art, or shape is unclear.

## Instructions

The workflow has three stages. Do not skip stages. Do not collapse Stage 1 into Stage 2 by inferring the context from the request - ask the user. The single most common failure mode for this skill is the agent guessing at Stage 1 in order to "save time" and then producing a Stage 2 draft that has to be thrown away.

### Stage 1: Context Gathering

Goal: surface enough about the audience, the purpose, the prior art, and the constraints that the doc's shape becomes obvious before any prose is written.

Ask the user the following, in one consolidated turn (batch, not ping-pong):

1. **Audience**. Who reads this and decides something based on it? Is it one person, a team, a leadership review, a public audience? What do they already know? What do they NOT know?
2. **Purpose**. What does the reader do after reading? Approve a decision? Choose between options? Implement a spec? Get oriented? "Inform" is not a purpose - find the action.
3. **Prior art**. What has already been written about this, in this org or externally? What docs does the user want this one to feel similar to (or deliberately different from)? Are there prior decisions this builds on?
4. **Constraints**. Length cap, deadline, format requirements (RFC template, ADR template, internal memo template), required sections, required reviewers. What is OUT of scope?
5. **Shape signals**. Is the reader mostly going to skim? Mostly going to study? Are they looking for a recommendation or a comparison? Is there a TL;DR they will read first and then stop?

Record the answers in a Stage 1 artifact - either inline in the working doc as a top "Context" section that gets removed before ship, or in a sibling `<doc>-context.md`. The artifact is durable: Stage 3 reads it back to detect drift.

**Do not move to Stage 2** until at least Audience, Purpose, and Constraints have non-empty answers. Prior art and Shape signals can be "none" if the user explicitly says so.

### Stage 2: Refinement and Structure

Goal: produce a draft whose structure carries the argument before any sentence is polished.

Iterate on shape, then content, in this order:

1. **Outline first**. Propose a section-by-section outline (headers + 1-line purpose per header). Do not write prose yet. Show the outline to the user. Iterate until the user accepts it. An outline that fits the Stage 1 audience and purpose is worth more than three paragraphs that don't.
2. **Draft against the accepted outline**. Write each section to its purpose-line. Keep the outline visible at the top of the working draft so divergence is detectable.
3. **Iterate on shape, not just words**. After the first draft, ask the user: "Does the structure carry the argument, or does the structure get in the way of the argument?" If the structure is wrong, regenerate the outline - do not patch prose around a broken outline.
4. **Content checkpoints**. After each major iteration, restate in one line what the doc is now saying. If the one-liner does not match the Stage 1 Purpose, the doc has drifted - flag it and ask the user whether the doc should change or whether the Purpose should change.
5. **Resist polish before structure is settled**. Word-level polish is Stage 3 territory. Do not rewrite a sentence three ways before the section it lives in is locked.

Stage 2 ends when the user says the draft holds together as a whole, not when the prose is pretty.

### Stage 3: Reader Testing

Goal: simulate a reader who has NOT seen this conversation and find the places they fall off.

1. **Adopt the fresh-reader persona**. Read the doc top-to-bottom as if you only know what Stage 1's audience description said this reader knows. Do not reference earlier turns of the conversation. Do not "remember" decisions that the doc itself does not state.
2. **Track three failure modes**:
   - **Unbacked claims**. Sentences that assert something the reader has no way to verify or evaluate.
   - **Missing antecedents**. References to concepts, projects, or systems the reader has not been introduced to.
   - **Lost-thread transitions**. Section breaks where the reader cannot reconstruct why the next section follows from the previous one.
3. **Surface a gap list, not a fix list**. Report each gap as: location, what dropped you, what the reader would need. Do not silently rewrite - the user decides whether to add context, cut the section, or restructure.
4. **One pass minimum, two passes if the doc is long or high-stakes**. After fixes, re-do the fresh-reader read. The second pass catches drift introduced by the first round of fixes.
5. **Stop condition**. The doc passes Stage 3 when the fresh-reader pass produces zero "I dropped here" markers, OR when the user explicitly accepts a remaining gap.

After Stage 3 passes, the doc ships. Strip any Stage 1 working notes from the final artifact unless the doc format calls for them (an ADR's "Context" section is durable; a working doc's "Stage 1 notes" block is not).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I just need the doc fast - skip the workflow" | A one-shot draft for a multi-reader doc almost always rewrites once at Stage 3 anyway. The workflow front-loads that rewrite into Stage 1, where it is cheap. Slow is smooth, smooth is fast on docs that get reused 100 times. |
| "The user already told me what they want" | The user told you the OUTCOME (a spec exists, a proposal lands). Stage 1 surfaces the SHAPE (what kind of spec, what the reader is doing with it). Outcome and shape are not the same thing. |
| "Stage 1 is obvious - I can infer it from the request" | Inferring Stage 1 is the single most common cause of a Stage 2 draft that gets thrown away. If you can answer the five Stage 1 questions cold, ask them anyway - the user's answer is the contract Stage 3 tests against. |
| "Stage 3 reader testing is overkill for an internal doc" | Internal docs are read by the people who will execute on them. If the executors drop, the work drops. Stage 3 is not a politeness step - it is a correctness step. |
| "The structure can be fixed in editing" | Word-level edits cannot fix a section that is in the wrong place or doing the wrong job. Stage 2 locks structure before Stage 3 locks words. Polishing prose around a broken outline wastes both passes. |
| "I'll co-author by writing the whole thing and asking for feedback" | That is solo authoring with a review step, not co-authoring. Co-authoring means the user is in Stage 1 and Stage 2 with you - their answers shape the outline. Skipping their input in Stage 1 produces an artifact that is yours, not theirs. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] Stage 1 answers exist in the working doc or a sibling `<doc>-context.md`, with non-empty Audience, Purpose, and Constraints fields.
- [ ] Stage 2 produced a section-by-section outline that the user explicitly accepted before any prose was written.
- [ ] The final draft's section structure matches the accepted outline (or, if it diverged, the divergence was acknowledged in conversation).
- [ ] At least one Stage 3 fresh-reader pass was performed and its gap list was either resolved or explicitly accepted by the user.
- [ ] Stage 1 working notes are stripped from the final artifact (unless the format - e.g., ADR Context section - calls for them).
- [ ] The doc's one-line summary matches the Stage 1 Purpose.

"The doc reads well" is not a valid verification criterion. Stage 3 must have surfaced and resolved (or accepted) at least one concrete gap, or the pass did not happen.

## Related Skills

- [[technical-writer]] -- audience-appropriate technical documentation; complements Stage 2 when the doc's content (not just structure) needs domain-specific framing.
- [[writing-editing]] -- sentence-level polish and clarity; the Stage 3 successor when reader-testing has identified the right shape and you now need the right words.
- [[technical-documentation]] -- architecture docs, ADRs, and design specs; provides the format templates this workflow's Stage 2 outline can target.
- [[internal-comms]] -- structured templates for internal communication formats (3P updates, status reports, leadership briefings); use in place of this skill when the doc is short and the format is fixed.
- [[idea-refine]] -- refine vague ideas into concrete problem statements; an upstream pre-Stage-1 step when the user is not yet sure what they want to document.
- [[spec-driven-development]] -- turn an accepted spec into implementation; the downstream consumer when this workflow's output is a spec.

## Bundled Resources

Future bundled scripts for this skill go under `scripts/`. None present at v1.2.0; the directory is reserved as a sentinel proving the per-skill bundled-resources convention (AGENTS.md "Per-skill Bundled Resources") survives an installer copy.
