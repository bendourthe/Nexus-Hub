---
description: Check Claude Code usage limits and get smart model-switching recommendations based on current consumption. Use to "check my usage", "how much have I used", "am I near my limit", "should I switch models", "what's my token consumption", "check usage limits". SKIP - billing safeguards for autonomous agent systems (that is the ai-billing-safeguards skill) or project cost estimation.
---

# /usage Command

Check current Claude Code usage limits and get a model-switching recommendation based on how much of the window has been consumed. `/usage` has no scopes; it reports usage and advice directly.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive logic lives in the retained skill; this file only delegates.

## Delegation

Dispatch directly to the retained skill:

      (any invocation) -> check-usage

The skill reports current consumption against the limits and recommends whether (and to what) to switch models. Pass any remaining arguments through unchanged.

## Notes

- This command replaces the deprecated `/check-usage`. The old name forwards here via a deprecation shim through v3.x (removed at v4.0.0).
- Keep this dispatcher thin. The usage-check procedure lives entirely in the `check-usage` skill.
