# Agent-Writing Theory

Six authoring concepts that keep a skill cheap to load, cheap to follow, and still able to change the agent's behavior. This file is Tier 3: read it when drafting or rewriting a SKILL.md, not on every session.

The always-loaded pointer is the skill's `description` and the short Rule 6 / draft-step bullets in `skill-description-authoring` and `skill-create`. Those pointers must stay sharp enough that an author looking for this craft actually opens this file. Do not name external sources here; this is operational guidance for Nexus-Hub skills.

## Contents

- [Context pointers](#context-pointers)
- [The two loads](#the-two-loads)
- [Leading words](#leading-words)
- [Negation avoidance](#negation-avoidance)
- [Sediment and relevance pruning](#sediment-and-relevance-pruning)
- [Hard vs soft setup-dependency](#hard-vs-soft-setup-dependency)
- [Authoring checklist](#authoring-checklist)

## Context pointers

An always-loaded reference's wording, not its target, decides whether the agent ever reaches the material. The body can sit on disk forever; if the description, the Related Skills line, or the one-sentence body pointer does not name the situation, the agent will not open it.

Consequences for SKILL.md work:

- **Sharpen wording before inlining.** If a section is long because you do not trust the pointer, fix the pointer. Inlining a 200-line runbook into the body spends Tier 2 tokens on every trigger and still does not help the sessions that never triggered.
- **One trigger family per genuinely distinct branch.** Two unrelated jobs in one description teach the matcher to fire on both and the agent to guess which half applies. Split the skill, or put the second job behind a SKIP fence that names the owning skill.
- **Name the file the agent should open.** "See the bundled reference for details" is a weak pointer. "See `references/agent-writing-theory.md` for the six concepts and the no-op test" is a context pointer: the agent knows the path and why to read it.

Worked move: a skill that wraps a 40-step installer does not paste the 40 steps into Instructions. It keeps a three-line body procedure and a pointer: "Run `scripts/install-wrapper.sh`; the flags and failure modes are in `references/install-flags.md`." The description still has to mention the user phrases that should load the skill (`install the wrapper`, `wrapper flags`), or the body and the reference never enter context.

## The two loads

Every authoring decision spends one of two budgets. They are not interchangeable.

| Budget | What it is | Who pays | Typical spend |
|---|---|---|---|
| **Context load** | Tokens that occupy the window | Every session that loads the text | Tier 1 fields (`description`, `summary_l0`, `overview_l1`) across the whole catalog; the SKILL.md body once the skill triggers |
| **Cognitive load** | What a human or the following agent must remember without looking it up | The author, and the agent if the pointer is weak | A convention the body assumes ("you already ran `/plan`"); a reference the agent is expected to open |

Rules of spend:

- Tier 1 is under catalog-wide pressure. A longer `description` is paid on every session whether this skill fires or not. Pushy is required; encyclopedic is not.
- Tier 2 is paid per trigger. Put the procedure the agent needs on every use in the body. Put the branch that is needed only some of the time in `references/`.
- A weak pointer saves context load on paper and raises cognitive load in practice: the agent must remember that a file exists. A strong pointer (path + why) converts cognitive load back into a cheap, on-demand context load.
- Do not "save" context load by omitting a SKIP clause. The SKIP fence is how the matcher Rejects look-alikes; cutting it spends cognitive load on every near-miss as a wrong trigger.

When compacting, ask which budget the extra words spend. Marketing filler spends context load and buys no matching signal: cut it. A verbatim user phrase spends context load and buys a High-band match: keep it.

## Leading words

A leading word is a compact, pretraining-anchored concept that the model already treats as a unit. Repeating it as a token anchors behavior better than restating the whole idea in a new sentence each time.

Nexus-Hub already uses several: `SKIP`, `Verification`, `Rationalizations`, `frontmatter`, `summary_l0`, `overview_l1`. An author who spells those out as "the clause that lists requests this skill must not handle" is paying context load for a concept the catalog already named.

Two mechanical moves:

### Refactor move

Collapse a spelled-out triad into one strong word once that word is in the skill's vocabulary.

Before: "Write a list of excuses the agent might use to skip this work, and next to each excuse write the reason the excuse is wrong, citing a real failure."

After: "Fill the Common Rationalizations table. Each row cites a concrete failure mode."

The after form works only because `Common Rationalizations` is already a leading word in `AGENTS.md`. Do not invent a private leading word that appears once.

### No-op test

If the model already obeys an instruction by default, delete the instruction. Do not trim it. A shortened no-op is still a no-op, and it dilutes the lines that actually change behavior.

Examples of no-ops in skill bodies: "be careful", "think step by step", "use good judgment", "write clean code", "do not hallucinate file paths" on a harness that can only write through a tool. Delete them. Replace only when you can name the observable that would fail without the line (a command, a file, a schema).

## Negation avoidance

State the positive target behavior. Models overweight the object of a prohibition: "do not wrap the description" puts `wrap` and `description` in the same clause and leaks that shape into drafts.

Prefer:

- "Write the `description` as one physical line."
- "Keep `name` identical to the parent directory."
- "Put look-alike requests in a `SKIP:` clause."

Reserve "do not" / "never" / "SKIP" for hard guardrails, and pair each prohibition with the allowed alternative:

- "Do not auto-register a draft. Surface it for maintainer review, then register under `AGENTS.md` Register the skill."
- "Never commit secrets. Use the `secret-scan` hook's block as the stop condition."
- "SKIP idea-refine look-alikes: a vague idea becoming a problem statement belongs to `idea-refine`, not this skill."

A body that is mostly prohibitions with no positive target is unfinished, not strict.

## Sediment and relevance pruning

Skills accrete layers: an extra "also consider", a workaround for a bug that was fixed, a second explanation of a rule that `AGENTS.md` already states. That sediment still occupies Tier 2 tokens and trains the agent to skim.

A line earns its keep only if removing it would change the agent's action. If the agent would do the same thing without the line, it is sediment. Cut it.

Prune on every substantial edit, not only when the body approaches 500 lines:

- Does this sentence change a file, a command, a skip, or a check? Keep.
- Does it restate `AGENTS.md` or another skill this body already links? Cut and keep the link.
- Does it document a workaround whose root cause is gone? Cut.
- Does it list a third example of a pattern two examples already teach? Cut the third.

The size-norm (target 500 lines, hard cap 800) is a backstop, not the first prune signal. A 200-line body can still be sediment-heavy.

## Hard vs soft setup-dependency

Some skills cannot produce a valid result until something else has run. Others are merely sharper when extra context exists. Mixing those two into the same "prerequisites" paragraph either blocks work that could start, or lets the agent run a skill that will invent the missing input.

| Kind | Test | How to write it |
|---|---|---|
| **Hard** | Without this setup, the skill's Verification items cannot pass | An explicit run-this-first pointer: "Run `/plan` until a plan file exists at `docs/**/plans/*.md`. This skill will not implement a phase without that file." Put it at the top of Instructions, not buried in When to Use. |
| **Soft** | The skill still produces a valid result; setup improves it | Soft prose: "A `CONTEXT.md` glossary shortens later questions; if it is absent, continue and create terms as they appear." Never fail closed on a soft dependency. |

Examples:

- `implement-phase` has a hard dependency on a plan file. The pointer is the plan path, not a vibe.
- `skill-description-authoring` has no hard setup dependency. You can rewrite a description from the SKILL.md in front of you.
- `skill-create` has a hard dependency on local git history that actually contains the pattern. Soft-depends on `continuous-learning` instincts: useful when present, not a gate.

When in doubt, classify as soft. A false hard dependency is how a skill interviews the user instead of working (see Rule 5 in the parent SKILL.md: clarification ceiling).

## Authoring checklist

Use this when drafting or editing a SKILL.md. Every item maps to one concept above.

- [ ] The `description` names the situations that should load this skill, including the path of any bundled reference the agent must open for a distinct branch (context pointer).
- [ ] Tier 1 fields stay inside their word limits; extra procedure went to the body or to `references/` (two loads).
- [ ] Repeated concepts use catalog leading words; spelled-out triads were collapsed; no-op instructions were deleted, not trimmed (leading words).
- [ ] Positive target behavior is stated first; every prohibition is a hard guardrail paired with the allowed alternative (negation avoidance).
- [ ] Removing any remaining sentence would change an action, a skip, or a check (sediment prune).
- [ ] Hard setup is an explicit run-this-first pointer; soft setup is prose that does not block (setup-dependency split).
- [ ] Existing Nexus-Hub rules still hold: pushy description with a SKIP clause, trigger-noun preservation, quoted `summary_l0` / `overview_l1`, Common Rationalizations that cite failure modes, binary Verification.
