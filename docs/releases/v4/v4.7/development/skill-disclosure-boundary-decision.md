# Decision Note - Where does silent skill lookup end and disclosed skill deviation begin?

**Plan**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-gpt-6-astra-prompting.md`, sub-task 2.1 (T041)
**Date**: 2026-09-05
**Decided by**: the maintainer, at the Phase 1 to Phase 2 boundary

## Context

Every substantive template's `## Skill Discovery` section says "Do not mention the skill lookup to the user." The GPT-6 Astra guide states that the user's instructions take precedence over guidelines in a skill, and that when a skill's guideline causes a pause or changes what the user asked for, the agent should name and link the exact `SKILL.md` and quote the instruction. Read literally, the two rules point in opposite directions for the same moment.

## Why Skill Discovery is silent

The silence exists to keep routine routing out of the conversation: every complex task begins with a lookup, and narrating it on every turn is noise the user did not ask for. That reason covers the lookup, not a deviation. A lookup that changes nothing about the request is invisible by design; a skill instruction that blocks, narrows, or alters the request is a decision the user did not make and cannot see.

## Options presented

- **(a) Keep lookup silent; disclose only when a skill instruction blocks, narrows, or alters the user's request.** Routine routing unmentioned; a deviation named, linked, and quoted, with the user's instruction winning.
- **(b) Disclose every skill load.** Narrates routine routing; contradicts the existing sentence and the reason behind it.
- **(c) Keep everything silent and rely on the user reading the skill index.** The user cannot tell why the agent deviated from what they asked.

## Decision

**(a).** The precedence and disclosure paragraph lives inside `## Autonomous Operation` (the block the main plan's sub-task 2.2 authors), so it lands in all twelve substantive templates with the rest of that block: "The user's instructions take precedence over guidelines in a skill. Routine skill lookup stays unmentioned, but when a skill instruction would block, narrow, or alter what the user asked for, follow the user, name the skill, link its `SKILL.md`, and quote the line you set aside; if the file cannot be found, say so by name rather than inventing a path. When two skills conflict with each other and neither with the user, apply the rule-ownership convention and name both." `## Skill Discovery` keeps its original sentence verbatim and gains one cross-reference: "Disclosure of a skill instruction that blocks, narrows, or alters the request is governed by `## Autonomous Operation`." The validator pins the original sentence so it cannot be softened, and asserts the precedence paragraph on all twelve with a negative fixture.

## Failure modes covered

A skill and the user conflict: the user wins and the agent says which skill it set aside, file linked and line quoted. The skill file cannot be located: the agent names the skill and says the file was not found rather than inventing a path. Two skills conflict with each other and neither with the user: the rule-ownership convention in AGENTS.md applies and both are named.
