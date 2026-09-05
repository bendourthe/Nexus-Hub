# Decision: An always-loaded Autonomous Operation block on every platform, with the autonomy boundary stated once

Status: implemented - every substantive instruction template carries a byte-identical `## Autonomous Operation` block that states when the agent proceeds without asking and when it stops, `## Consequential Decisions` references that boundary instead of restating it, the block carries the user-over-skill precedence rule with disclosed deviation, and a parity guard plus a twelve-template validator prove it stays distributed

## Problem

The v4.7.0 comparison of Nexus-Hub against the current frontier model's documented behavior found that the vendor's highest-leverage rule for long-horizon agent work was absent from every instruction template: a grep for "autonomous" across `templates/ai-instructions/` returned only two HTML comments. The rule is that the agent is operating autonomously, the user may not be watching, asking permission for work the request already covered blocks progress, and only destructive or scope-changing actions stop for the user; with it come three companions (report-and-stop when the user is thinking out loud, finish the last paragraph's promises before ending the turn, prefer targeted edits over whole-file rewrites). Nexus-Hub's product is always-loaded behavioral guidance for about twenty platforms, and its plan-and-implement lifecycle is exactly the long-horizon autonomous work the rule governs.

Two shipped rules sat next to the gap. `## Consequential Decisions` requires a plain-language walkthrough before asking approval on consequential choices, and `## Skill Discovery` says not to mention the skill lookup. Both agree with the new rule in substance and both would read as contradicting it if shipped unreconciled.

## Decision

Every substantive template (the lockstep five, `base-google-shared.md`, the five guardrails-only files, and `generic-instructions.md`) carries one `## Autonomous Operation` block, byte-identical everywhere, inserted after `## Consequential Decisions`. It states the autonomy boundary once and names `## Consequential Decisions` as the owner of how a stop is presented; `## Consequential Decisions` gains one sentence pointing back. The block's second paragraph states that the user's instructions take precedence over a skill's guidelines, that routine lookup stays silent, and that a skill instruction which blocks, narrows, or alters the request is disclosed by name, link, and quoted line; `## Skill Discovery` keeps its original sentence and cross-references the block. The block names no vendor, model, or API parameter.

Enforcement: `scripts/check_base_template_parity.py` treats `Autonomous Operation` as a required heading and an invariant block across the lockstep five; `tests/validators/test_autonomy_block_rule.py` derives the twelve-template roster from the directory, asserts the heading, the opening clause, the precedence paragraph, and the disclosure instruction on each, asserts absence from the four include-only shims, pins the original Skill Discovery sentence, and carries a negative fixture proving a block without the precedence paragraph fails by file name. The five word ceilings rose by the measured delta, recorded in `docs/policy/doc-budgets.md`.

## Alternatives considered

- **Keep both texts and add one precedence sentence (option b in the decision note).** Cheapest edit, rejected because it leaves two statements of the same boundary for a reader to reconcile, which is the runtime inference the reconciliation exists to remove.
- **Fold `## Consequential Decisions` into the block (option c).** Rejected because that heading is load-bearing outside the templates: both parity guard lists, AGENTS.md's description of the organization knowledge layer, and the v4.5.0 decision record cite it by name.
- **Ship the rule as a skill rather than in the templates.** Rejected because a skill loads on trigger and this rule must hold on every turn; the v4.1.2 and v4.5.0 decisions made the same call for the construction and writing rules for the same reason.
- **Disclose every skill load, or keep every deviation silent (options b and c of the disclosure note).** Rejected: the first narrates routing the user did not ask about; the second hides a decision the user did not make.
- **A reduced block for the guardrails-only templates.** Considered because those files carry shorter sections elsewhere; rejected in favour of the identical block because the existing `## Construction Discipline` and `## Writing Discipline` blocks are already identical across all twelve, the validator can byte-compare all twelve when they are, and the block is short enough (four paragraphs at most, under 260 words) that reduction would drop a rule rather than shorten prose.

## Consequences

- Every platform pays the block's cost on every turn (measured in the Phase 2 history; roughly 1.3 tokens per word), once per platform in use.
- An agent on any supported platform now proceeds on reversible covered work without asking, which is a behavior change for users who relied on being asked; the boundary is destructive or scope-changing actions, unchanged from `## Consequential Decisions`.
- A skill can no longer silently narrow a request: the deviation is named, linked, and quoted. Skills that legitimately constrain requests will be visible when they do so.
- Editing the block means editing all twelve templates; a partial edit fails the parity guard, the validator, or both.
- Whether the block reads naturally beside each platform's existing sections is a human check, recorded in the plan's last-phase human testing suggestions.
