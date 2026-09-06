# Decision: Raise seven instruction-doc ceilings for the plan-lifecycle block

Status: implemented - shipped in v4.0.0 (plan `v4.0.0-cost-effective-ci-cd`, Phase 5).

## Problem

The v4.0.0 cost-effective-CI/CD plan requires a "Plan Lifecycle and CI/CD" rule block in every substantive instruction template, so the lifecycle survives platform and context differences through the installed instruction layer rather than depending on a skill triggering. The same rule has to reach this repository's own `AGENTS.md` and `CLAUDE.md`, because Nexus-Hub must follow the lifecycle it distributes.

`docs/policy/doc-budgets.json` declares a word ceiling for exactly this class of always-loaded doc, and `scripts/validate_doc_budgets.py` gates it in `make validate` and in CI. Adding the block breaches seven of the eight ceilings.

The policy's ratchet is deliberate and worth restating: lowering a ceiling is free, raising one is a decision requiring explicit justification in the pull request that raises it. That is what this record supplies.

The complicating fact is that six of the eight budgeted docs were already flagged `<- tight` by the validator's own `--list` before this change:

| Doc | Words | Ceiling | Headroom |
|---|---|---|---|
| `AGENTS.md` | 8086 | 8150 | +64 (1%) `tight` |
| `base-claude.md` | 1358 | 1410 | +52 (4%) `tight` |
| `base-codex.md` | 1007 | 1020 | +13 (1%) `tight` |
| `base-cursor.md` | 976 | 990 | +14 (1%) `tight` |
| `base-gemini.md` | 997 | 1010 | +13 (1%) `tight` |
| `base-opencode.md` | 976 | 990 | +14 (1%) `tight` |

The policy says a budget with under 5% headroom "is effectively frozen, which is a stricter policy than intended". So the pre-existing state was not a healthy budget that this change wanted to loosen. It was six budgets that had already drifted into a stricter regime than the policy intends, where any addition at all is a ceiling change.

## Decision

Condense first, then re-seed the affected ceilings to the policy's own seeding rule (current size plus roughly 10%), rounded up to the nearest ten.

**Condense first.** The block was drafted at 110 words and shipped at 104: five bullets and a one-line skill pointer. Everything expandable went to `[[cicd-architect]]`, which is on-demand and therefore unbudgeted by design. The always-loaded text carries only what changes an agent's next action: commit locally per phase, do not push before the final phase, record CI impact rather than editing pipelines, reconcile and publish once at the end, release only after green integration.

**Then re-seed, do not merely unblock.** Setting each ceiling to current-plus-13-words would pass the gate and leave every doc frozen again, which is how the six `tight` entries arose in the first place. Each affected ceiling is instead recomputed as `ceil(words * 1.10 / 10) * 10`, which is the manifest's documented seeding rule for a newly budgeted doc.

| Doc | Old | New | Headroom after |
|---|---|---|---|
| `AGENTS.md` | 8150 | 9100 | 9% |
| `CLAUDE.md` | 240 | 270 | 10% |
| `base-claude.md` | 1410 | 1610 | 9% |
| `base-codex.md` | 1020 | 1230 | 10% |
| `base-cursor.md` | 990 | 1190 | 9% |
| `base-gemini.md` | 1010 | 1220 | 10% |
| `base-opencode.md` | 990 | 1190 | 9% |

`catalog/style-guides/markdown.md` is unchanged; it was not `tight` and this plan does not touch it.

**What was added, per the policy's three required answers.**

- *What was added*: 104 words of lifecycle rule per substantive template, plus a ~190-word paragraph in `AGENTS.md` and a one-line item in `CLAUDE.md`.
- *Why it must be always-loaded rather than on-demand*: the rule governs an action an agent takes at a phase boundary without necessarily invoking any skill. A rule that only fires when `cicd-architect` triggers cannot prevent the default it exists to remove, because the default is what happens when nothing triggers. This is the same argument that put `Branching` and `Consequential Decisions` in these files.
- *What was removed to offset it*: nothing from these docs. The offset was taken on the skill side instead, where three bodies were reduced by moving Tier 2 content to Tier 3 references in the same release: `cicd-architect` 790 to 275 lines, `code-commit-workflow` 504 to 394, `version-upgrade` 510 to 447, plus `implementation-plan` 543 to 499. That is a net reduction of roughly 1,100 lines of per-trigger content against roughly 1,600 words of per-session content added.

## Alternatives considered

**Fold the rule into the existing `## Branching` section.** Rejected. It would have avoided a new heading, but `Branching` answers "which branch does this work go on", while the lifecycle answers "when does it leave this machine". Merging them makes both harder to state and makes the rollout unverifiable, because a body-identity check needs a section boundary to slice on.

**Condense the block to fit inside existing headroom (13 words on four of the five templates).** Rejected as not achievable honestly. Thirteen words cannot carry five distinct rules. Any version that fit would have said "follow the plan lifecycle" and pointed at a skill, which is precisely the on-demand form that the always-loaded placement exists to avoid.

**Relocate other content out of the templates to pay for the block.** Rejected as out of scope and as the wrong trade. The candidates (`MCP Registry Policy`, `Output Minimization`, `Consequential Decisions`) are all always-loaded for the same reason the lifecycle rule is: they change behavior in sessions that never invoke a skill. Trading one for another does not reduce cost, it just picks a different rule to stop enforcing. A genuine template-slimming pass is worth doing, but it is its own change with its own evidence, not a side effect of this one.

**Put the rule only in the five lockstep templates, where the parity gate already runs.** Rejected. That is the exact shape of known gap DF-1: the non-lockstep seven are the files a change silently misses, and shipping the rule to five of twelve would guarantee the drift the gap describes. Coverage of all twelve is asserted by `tests/skills/test_cicd_lifecycle_contract.py`, including body identity, stub exclusion, and roster completeness.

**Skip the budget entirely by exempting instruction blocks from the word count.** Rejected outright. The manifest's counting rule already anticipates this: words are counted across the whole file including fences and tables, because exempting anything makes "move the prose into an exempt construct" the cheapest way to pass. An exemption for behavioral blocks would make every future addition a behavioral block.

## Consequences

- Seven ceilings are higher. The aggregate always-loaded cost of a session rises by roughly 100 words per platform, plus 190 in `AGENTS.md`.
- Six docs that were effectively frozen now have working headroom again. That is a real loosening, and it is the intended effect: a frozen budget produces exactly this record every time anyone needs to add a line, which trains people to treat the gate as an obstacle rather than a measurement.
- The ratchet still holds in the direction that matters. Nothing here weakens the requirement to justify a raise; it supplies one.
- A future template-slimming pass should lower these numbers again. Lowering is free and needs no record.
