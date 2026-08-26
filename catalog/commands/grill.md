---
description: Grill a plan, design, or decision in dependency-ordered rounds until every branch is resolved, asking the whole settled frontier at once with a recommended answer per question. Use to "grill me", "grill this plan", "challenge my plan", "poke holes in this", "stress-test my thinking", "interrogate my design", "ask me questions until this is fully specified". SKIP - autonomous multi-persona critique with no user in the loop (use /review plan), turning a vague idea into a problem statement (use /plan goals), or auditing an already-written spec for ambiguity (use /spec clarify).
argument-hint: "[plan-path or topic]"
---

# /grill Command

Interrogate a plan, design, or decision until nothing is left silently assumed. `/grill` is the single-word entry point people reach for by name; the interview itself runs in the retained `design-interview` skill.

This is a thin dispatcher over that skill, following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). Heavy logic stays in the skill: this file resolves the target and delegates.

## Target resolution

Resolve the target from `$ARGUMENTS`.

- `/grill <path-to-plan-or-spec>` grills that artifact. Read it first, then derive the design tree from what it leaves open.
- `/grill <topic>` grills the named topic or decision.
- `/grill` (bare) grills the current subject of the session. If there is no obvious subject, ask which artifact or decision to grill before starting; do not invent one.

When the target is a plan file that a `/review plan` pass has already produced findings for, pass those findings in as the seeded first round rather than deriving one from scratch.

## Delegation

Dispatch to the retained skill:

      design-interview   (frontier rounds, recommended answers, sub-agent fact-finding, CONTEXT.md glossary)

Pass the resolved target and any remaining arguments through unchanged.

## What the user should expect (guarantee)

The interview mechanics are owned by `[[design-interview]]` and are not restated here, but three properties are worth surfacing because they change how the session feels:

- **Rounds, not a drip feed.** Every question whose prerequisites are already settled is asked in the same round. A question that depends on another open question waits for a later round.
- **Every question carries a recommendation.** The user reacts to a proposal instead of composing an answer from nothing.
- **Facts are the agent's job.** Anything discoverable from the repository or the environment is looked up (via a sub-agent where available) rather than asked. Only the branch downstream of a pending lookup waits.

The session ends when the frontier is empty and the user confirms shared understanding. It does not end because a question budget ran out.

## Notes

- `/grill` is a permanent entry point, not a deprecation shim. Do not print a deprecation notice.
- `/plan` runs this same engine automatically at its post-draft gate, so a freshly generated plan is already grilled. Use `/grill` for an artifact that did not come from `/plan`, or to reopen a plan after it changed.
- Keep this file thin. The frontier algorithm, the round format, the recommendation rule, and the glossary duties all live in `[[design-interview]]`; duplicating them here would create a second owner of one concern.
