---
name: design-interview
description: Interview the user in dependency-ordered rounds until every branch of the design tree is resolved, asking the whole settled frontier at once with a recommended answer per question, and maintain a domain glossary at CONTEXT.md. Use whenever the user says "grill me", "grill this plan", "challenge my plan", "interview me about this design", "stress-test my thinking", "poke holes in this", "ask me questions until this is fully specified", "build a domain glossary", "shared language", "ubiquitous language", or wants an interview engine that idea-refine, ambiguity-detector, doc-coauthoring, plan-review, or implementation-plan can invoke. SKIP - turning a vague idea into a problem statement (use idea-refine); auditing an already-written spec for ambiguity (use ambiguity-detector); upgrading requirement testability (use requirement-enhancer); autonomous critique of a plan with no user in the loop (use plan-review). CONTEXT.md is a sibling of .claude/context/architecture.md, never a replacement.
summary_l0: "Interview in dependency-ordered rounds until the design tree is resolved"
overview_l1: "Reusable interview engine. Models the work as a design tree and questions it in rounds: the frontier is every decision whose prerequisites are already settled, and a round asks that whole frontier at once, numbered, each question carrying a recommended answer so the user reacts instead of composing. Dependent questions wait for a later round. Finding facts is the agent's job: environment questions go to a sub-agent, and only the branch downstream of that lookup blocks. No hard question cap; natural-language steering is the control surface. Second job: maintain CONTEXT.md at the repo root as a domain glossary (definition, avoid-list, relationships). Other skills invoke this engine; they are not replaced. Trigger phrases: grill me, grill this plan, challenge my plan, interview me about this design, stress-test my thinking, build a domain glossary."
category: developer-experience
---

# Design Interview

Question the user about a plan, decision, or idea until every branch of the design tree is resolved. Work in dependency-ordered rounds: ask everything that is answerable now, all at once, and let the answers unlock the next round. Attach a recommended answer to every question so the user has something to react to rather than a blank prompt. There is no hard question cap: natural-language steering ("enough on this branch", "park that") is the control surface.

This skill is the interview engine that `idea-refine`, `ambiguity-detector`, `doc-coauthoring`, `plan-review`, and `implementation-plan` can invoke. It is not a fifth overlapping owner of their jobs.

A second, durable output is the project domain glossary at `CONTEXT.md` (repo root). Each term gets a definition, an avoid-list of rejected synonyms, and a relationships section. Update it inline whenever an interview surfaces new or ambiguous vocabulary so later sessions share a language.

## When to Use This Skill

Use when:

- The user asks to be grilled, interviewed, challenged, or questioned until a design is fully specified.
- A plan or decision still has unresolved branches and the cheapest next move is a question, not a guess.
- Another skill needs an interview engine and does not want to restate these rules.
- The project needs a shared vocabulary file (`CONTEXT.md`) or an existing one has drifted.

**When NOT to use:**

- The request is a vague idea that needs a problem statement. That is [[idea-refine]]. Invoke this skill from there only if that skill needs a deeper interview after the problem is named.
- The artifact is already a written spec to audit for ambiguity. That is [[ambiguity-detector]].
- The job is to upgrade requirement quality, testability, or acceptance criteria. That is [[requirement-enhancer]].
- The job is an autonomous critique of a finished plan with no user in the loop. That is [[plan-review]]. The two compose: run the lenses first, then seed this interview's first round from their findings.
- Do not treat `CONTEXT.md` as a replacement for `.claude/context/architecture.md`. Architecture stays in the architecture file. `CONTEXT.md` holds ubiquitous language only.

## Rule ownership

This skill owns the interview mechanics for the whole cluster. Callers reference it by name and describe only the handoff.

| Concern | Owner |
|---|---|
| Frontier computation, round format, recommended answers, sub-agent fact-finding | this skill |
| Problem statement from a vague idea | [[idea-refine]] |
| Ambiguity audit of a written spec | [[ambiguity-detector]] |
| Autonomous multi-persona critique of a plan | [[plan-review]] |
| Async questions for an absent stakeholder | [[decision-questionnaire]] |

## Instructions

### 1. Name the tree, then compute the frontier

State in one sentence what is being specified (a plan, a decision, an idea, a glossary pass).

Model it as a **design tree**: every decision branches into the decisions that hang off it. The **frontier** is every decision whose prerequisites are already settled, meaning every question you can ask *now* without guessing at an answer you have not heard yet.

A question belongs in this round only if answering it does not require assuming the answer to another question in this round. If it does, it belongs to a later round. That test is the whole discipline: it is what separates a dependency-ordered round from an undifferentiated questionnaire dump.

Good frontier questions name a branch: "Which user is blocked today if we ship nothing?" not "Tell me everything about the design."

### 2. Ask the whole frontier in one round, with recommendations

Number every question in the round and attach your recommended answer to each. The recommendation is not a formality: it converts a blank prompt into a yes/no/counter-proposal, which is a far cheaper thing for a user to answer, and it forces you to have a position.

Use this ASCII format (this repository's Markdown is ASCII-only, so do not substitute emoji markers):

```markdown
**Q1. <question title>**

<question body, which may run to several paragraphs and may offer explicit choices>

> **Recommended**: <your recommended answer, with the one-line reason it is your pick>

---

**Q2. <question title>**

<question body>

> **Recommended**: <your recommended answer, with the one-line reason it is your pick>
```

Then stop and wait. Do not answer your own questions and proceed.

### 3. Find facts yourself; never outsource a lookup to the user

Finding **facts** is your job. Deciding is theirs.

When a frontier question needs a fact from the environment (what the filesystem holds, what a dependency version is, what an existing module already does, what a vendor document says), dispatch a sub-agent to find it. Never ask the user for anything you could look up.

Do not block the round on that lookup. A running exploration is an unsettled prerequisite, so only the questions **downstream of it** wait for the sub-agent to report. Ask the rest of the frontier now, in this round. When the sub-agent returns, its finding either settles a branch outright or becomes a recommended answer in the next round.

If the sub-agent facility is unavailable, do the lookup inline with the tools you have, and say in the round which questions are still waiting on a fact rather than silently deferring them.

### 4. Recompute the frontier each round until it empties

Each set of answers reshapes the tree. Settled decisions push the frontier outward and unblock questions that depended on them. Recompute and ask the next round.

Parking is allowed; silent skipping is not. Record parked branches in the running note so they can be reopened. Stop a branch when the user steers ("enough", "later", "that is decided") or when Verification for that branch would already pass.

The session is done when the frontier is empty: every branch visited, nothing left silently assumed. Do not act on the result until the user confirms you have reached a shared understanding.

### 5. Maintain CONTEXT.md as the glossary, not the architecture

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

### 6. Close with the resolved tree

When the user stops the interview or every live branch is decided, print a short tree: decided branches, parked branches with reasons, glossary terms added or changed, and the path of `CONTEXT.md`. Do not invent a spec or a plan here; hand off to [[idea-refine]], [[implementation-plan]], or [[doc-coauthoring]] by name.

### 7. Invocation from other skills

When this skill is invoked as an engine, do not re-run the caller's When-to-use. Run steps 1-6 on the caller's named tree, then return control.

Two caller-supplied inputs are honored when present:

- **A seeded frontier.** A caller that has already found unresolved decisions (for example [[plan-review]] findings, or a `/plan` gate) passes them in as round one. Use them instead of deriving a first round from scratch, since an evidence-backed question beats a speculative one.
- **A single-question constraint.** A caller that genuinely needs strict one-at-a-time pacing says so, and this engine then emits rounds of exactly one question. The frontier logic is unchanged; only the round size is capped.

If this skill is unavailable, the caller must mark the interview portion uncovered (missing-delegate honesty in `AGENTS.md`) rather than improvise a second grilling protocol.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will ask one question per turn to be safe." | A frontier of twelve independent decisions then costs twelve turns, and the user re-reads the context twelve times. Ask the settled frontier at once. One question per round is correct only when the frontier genuinely holds one item, or a caller asked for that constraint. |
| "I will send every question I can think of at once to save turns." | That is the opposite failure. A question whose answer depends on another open question is unanswerable, so the user either guesses or stalls, and a guessed prerequisite silently corrupts every branch beneath it. Round membership is decided by the dependency test in step 1, never by convenience. |
| "Recommended answers will bias the user." | An unanchored question gets a vague answer or no answer. The recommendation is a proposal to react to, and it is labelled as yours; a user who disagrees says so in three words. Withholding your position to seem neutral just moves the work onto them. |
| "I will ask the user which version the dependency is on." | That is a fact, not a decision, and it is sitting in the repository. Dispatch a sub-agent. Asking the user to be your filesystem is the fastest way to make an interview feel like an interrogation. |
| "The sub-agent has not reported, so I will wait before asking anything." | Only the branch downstream of that lookup is blocked. Holding the entire round hostage to one fact turns a parallel interview into a serial one. |
| "Five questions is enough; I can guess the rest." | Unguessed branches become silent scope. Park with a reason or ask. There is no cap that makes guessing legitimate. |
| "CONTEXT.md would collide with architecture.md, so I will skip the glossary." | They are siblings. Architecture describes the system; CONTEXT.md names the language. Skipping the glossary is how the next session re-litigates "what we meant by X". |
| "This is just idea-refine with extra questions." | idea-refine owns the problem statement. This skill owns unresolved design branches and the glossary. Merging them under-triggers the engine when a plan is already named. |
| "The spec is ambiguous, so I should grill the user instead of reading it." | Reading a written spec for gaps is [[ambiguity-detector]]. Grilling here is for branches that are not yet written. |
| "plan-review already critiqued the plan, so the interview is redundant." | The lenses find what is wrong without the user; they cannot decide anything. Every finding that needs a human choice is still open until someone chooses. The critique is what makes the interview's questions evidence-backed, not what replaces them. |

## Verification

- [ ] Every live branch is decided, parked with a reason, or still has a pending question the user can see.
- [ ] No round contained a question whose answer depended on another question in the same round.
- [ ] Every question in every round carried a labelled recommended answer.
- [ ] No question asked the user for a fact obtainable from the environment; such facts were dispatched to a sub-agent or looked up inline.
- [ ] A round was not blocked in full by a pending lookup; only downstream questions waited.
- [ ] `CONTEXT.md` exists at the repo root if any term was treated as load-bearing; each such term has Definition, Avoid, and Relationships.
- [ ] `.claude/context/architecture.md` (if present) was not overwritten or replaced.
- [ ] The close-out names the handoff skill (idea-refine, implementation-plan, or doc-coauthoring) or states that none is needed.
- [ ] Look-alike jobs were not absorbed: idea-refine, ambiguity-detector, requirement-enhancer, and plan-review still own their SKIP cases.

## Related Skills

- [[idea-refine]] - owns vague-idea to problem-statement; may invoke this engine after the problem is named
- [[ambiguity-detector]] - audits a written spec; does not replace this interview
- [[requirement-enhancer]] - upgrades requirement quality; not an interview engine
- [[doc-coauthoring]] - long-form co-authoring that can invoke this engine for unresolved branches
- [[implementation-plan]] - `/plan` invokes this engine at its post-draft gate; this skill does not write the plan
- [[plan-review]] - autonomous multi-persona critique whose findings seed this interview's first round
- [[decision-questionnaire]] - async questionnaire for a stakeholder who is not in this session
- [[ddd-strategic-design]] - bounded contexts and ubiquitous language at domain-model scale; CONTEXT.md is the lightweight file convention, not a DDD substitute
