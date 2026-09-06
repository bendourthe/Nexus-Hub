# Decision Note - Where is the boundary between autonomous operation and Consequential Decisions?

**Plan**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md`, sub-task 2.1 (T006)
**Date**: 2026-09-05
**Decided by**: the maintainer, at the Phase 1 to Phase 2 boundary, after the plain-language walkthrough `## Consequential Decisions` itself requires

## The two rules

`## Consequential Decisions` (present in all twelve substantive templates, byte-locked across the lockstep five) requires a short plain-language walkthrough before the agent asks the user to approve or choose anything that changes security posture, deletes or overwrites data, changes distributed or user-facing behavior, or expands the agreed scope. The vendor's autonomous-operation guidance (Fable 5.1 comparison item A8, confirmed independently by the GPT-6 Astra guide) tells the agent not to ask permission for work the original request already covered, stopping only for destructive actions or genuine scope changes.

Where they agree: both draw the line at destructive and scope-changing actions. Where they disagree: nowhere in substance, but shipped as two texts they leave the agent to infer that the walkthrough section is about how to stop and the autonomy block is about when.

## Options presented

- **(a) State the boundary once in the new block; `## Consequential Decisions` references it.** One authoritative statement of when autonomy stops; the walkthrough section keeps its name and its job (how a stop is presented) and points to the block for the when.
- **(b) Keep both texts and add one precedence sentence.** Both stay as written; one sentence names which governs on disagreement. Cheapest, but leaves two statements of the same line.
- **(c) Fold `## Consequential Decisions` into the new block.** One section fewer, but the parity guard lists `Consequential Decisions` in both `REQUIRED_HEADINGS` and `INVARIANT_SECTIONS`, AGENTS.md describes it by name as behavioral context guidance for the organization knowledge layer, and v4.5.0's decision record cites it; removing the heading has costs beyond the templates.

## Decision

**(a).** The new `## Autonomous Operation` block states the boundary in one sentence ("Stop for destructive actions and genuine scope changes; that is the one boundary, and `## Consequential Decisions` governs how such a stop is presented"), and `## Consequential Decisions` gains one closing sentence pointing back: "The boundary itself is stated once, in `## Autonomous Operation`: reversible work the request already covers proceeds without asking; destructive actions and genuine scope changes stop here." Neither section restates the other's rule.

## What it changes for a user on a non-Claude platform

Every substantive template receives the same block, so a Codex, Cursor, Gemini, OpenCode, Qwen, Kimi, or Aider user gets the same when-to-stop rule and the same how-to-stop walkthrough as a Claude Code user. The block names no vendor, model, or API parameter. Its per-turn cost is recorded in the Phase 2 history and in `docs/policy/doc-budgets.md`.
