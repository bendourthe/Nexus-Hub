---
name: design-interview
description: Run a relentless one-question-at-a-time design interview until every branch of the design tree is resolved, and maintain a project domain glossary at CONTEXT.md. Use whenever the user says "grill me", "interview me about this design", "ask me questions until this is fully specified", "build a domain glossary", "shared language", "ubiquitous language", or wants an interview engine that idea-refine, ambiguity-detector, doc-coauthoring, or implementation-plan can invoke. SKIP - turning a vague idea into a problem statement (use idea-refine); reviewing an already-written spec for ambiguity (use ambiguity-detector); upgrading requirement quality and testability (use requirement-enhancer). CONTEXT.md is a sibling of .claude/context/architecture.md, never a replacement.
summary_l0: "Interview until the design tree is resolved and keep a CONTEXT.md glossary"
overview_l1: "Reusable interview engine: one question at a time, follow each answer's implications, no hard question cap. Second job: maintain CONTEXT.md at the repo root as a domain glossary (definition, avoid-list, relationships) whenever an interview surfaces new or ambiguous vocabulary. Other skills invoke this engine; they are not replaced. Soft-depends on an existing CONTEXT.md. Trigger phrases: grill me, interview me about this design, ask me questions until this is fully specified, build a domain glossary, shared language."
category: developer-experience
---

# Design Interview

Question the user about a plan, decision, or idea until every branch of the design tree is resolved. Ask one question at a time. Follow the implications of each answer before moving on. There is no hard question cap: natural-language steering ("enough on this branch", "park that") is the control surface.

This skill is the interview engine that `idea-refine`, `ambiguity-detector`, `doc-coauthoring`, and `implementation-plan` can invoke. It is not a fourth overlapping owner of their jobs.

A second, durable output is the project domain glossary at `CONTEXT.md` (repo root). Each term gets a definition, an avoid-list of rejected synonyms, and a relationships section. Update it inline whenever an interview surfaces new or ambiguous vocabulary so later sessions share a language.

## When to Use This Skill

Use when:

- The user asks to be grilled, interviewed, or questioned until a design is fully specified.
- A plan or decision still has unresolved branches and the cheapest next move is a question, not a guess.
- Another skill needs an interview engine and does not want to restate these rules.
- The project needs a shared vocabulary file (`CONTEXT.md`) or an existing one has drifted.

**When NOT to use:**

- The request is a vague idea that needs a problem statement. That is [[idea-refine]]. Invoke this skill from there only if that skill needs a deeper interview after the problem is named.
- The artifact is already a written spec to audit for ambiguity. That is [[ambiguity-detector]].
- The job is to upgrade requirement quality, testability, or acceptance criteria. That is [[requirement-enhancer]].
- Do not treat `CONTEXT.md` as a replacement for `.claude/context/architecture.md`. Architecture stays in the architecture file. `CONTEXT.md` holds ubiquitous language only.

## Instructions

### 1. Name the tree, then ask one question

State in one sentence what is being specified (a plan, a decision, an idea, a glossary pass). Ask exactly one question. Wait for the answer. Do not batch a questionnaire; that belongs to [[decision-questionnaire]] and is for a stakeholder who is not in this session.

Good first questions name a branch: "Which user is blocked today if we ship nothing?" not "Tell me everything about the design."

### 2. Follow implications before switching branches

Each answer opens or closes child branches. Walk the children of the current answer to a decision (keep / drop / park with a reason) before opening a sibling. Parking is allowed; silent skipping is not. Record parked branches in the running note so they can be reopened.

There is no maximum question count. Stop a branch when the user steers ("enough", "later", "that is decided") or when Verification for that branch would already pass.

### 3. Maintain CONTEXT.md as the glossary, not the architecture

Path: `CONTEXT.md` at the repository root. Create it if missing. If `.claude/context/architecture.md` (or the project's equivalent) exists, leave it alone and do not copy architecture into `CONTEXT.md`.

For every term the interview treats as load-bearing:

1. Write a one-sentence definition in the project's voice.
2. List rejected synonyms (words the team must not use for this concept).
3. Add a Relationships line (broader / narrower / "not the same as").

Update the file in the same turn the term appears. Do not wait until the interview ends; a crashed session should still leave the new words behind.

Template for one term:

```markdown
## <Term>

**Definition**: <one sentence>

**Avoid**: <comma-separated rejected synonyms>

**Relationships**: <broader/narrower/not-the-same-as>
```

### 4. Close with the resolved tree

When the user stops the interview or every live branch is decided, print a short tree: decided branches, parked branches with reasons, glossary terms added or changed, and the path of `CONTEXT.md`. Do not invent a spec or a plan here; hand off to [[idea-refine]], [[implementation-plan]], or [[doc-coauthoring]] by name.

### 5. Invocation from other skills

When this skill is invoked as an engine, do not re-run the caller's When-to-use. Run steps 1-4 on the caller's named tree, then return control. If this skill is unavailable, the caller must mark the interview portion uncovered (missing-delegate honesty in `AGENTS.md`) rather than improvise a second grilling protocol.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will send ten questions at once to save turns." | Batching hides which answer opened which branch. One question is the whole method. A stakeholder questionnaire is [[decision-questionnaire]]. |
| "Five questions is enough; I can guess the rest." | Unguessed branches become silent scope. Park with a reason or ask. There is no cap that makes guessing legitimate. |
| "CONTEXT.md would collide with architecture.md, so I will skip the glossary." | They are siblings. Architecture describes the system; CONTEXT.md names the language. Skipping the glossary is how the next session re-litigates "what we meant by X". |
| "This is just idea-refine with extra questions." | idea-refine owns the problem statement. This skill owns unresolved design branches and the glossary. Merging them under-triggers the engine when a plan is already named. |
| "The spec is ambiguous, so I should grill the user instead of reading it." | Reading a written spec for gaps is [[ambiguity-detector]]. Grilling here is for branches that are not yet written. |

## Verification

- [ ] Every live branch is decided, parked with a reason, or still has a pending question the user can see.
- [ ] No turn asked more than one question.
- [ ] `CONTEXT.md` exists at the repo root if any term was treated as load-bearing; each such term has Definition, Avoid, and Relationships.
- [ ] `.claude/context/architecture.md` (if present) was not overwritten or replaced.
- [ ] The close-out names the handoff skill (idea-refine, implementation-plan, or doc-coauthoring) or states that none is needed.
- [ ] Look-alike jobs were not absorbed: idea-refine, ambiguity-detector, and requirement-enhancer still own their SKIP cases.

## Related Skills

- [[idea-refine]] - owns vague-idea to problem-statement; may invoke this engine after the problem is named
- [[ambiguity-detector]] - audits a written spec; does not replace this interview
- [[requirement-enhancer]] - upgrades requirement quality; not an interview engine
- [[doc-coauthoring]] - long-form co-authoring that can invoke this engine for unresolved branches
- [[implementation-plan]] - `/plan` may invoke this engine during discovery; this skill does not write the plan
- [[decision-questionnaire]] - async questionnaire for a stakeholder who is not in this session
- [[ddd-strategic-design]] - bounded contexts and ubiquitous language at domain-model scale; CONTEXT.md is the lightweight file convention, not a DDD substitute
