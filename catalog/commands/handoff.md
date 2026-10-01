---
description: Write .nexus-hub/handoff.md and print a paste-ready prompt so another agent, on this or any other platform, can resume the task. Use to "hand off", "write a handoff", "I am about to hit my usage limit", "continue this in another tool", "switch to Codex", "switch to Claude Code", "save my progress for another agent", or when a "Usage limit:" hook message asks for /handoff. Accepts an optional focus, for example "/handoff focus on the failing migration". SKIP - an end-of-session history document (use /session), compacting context within this session (use the context-compression skill), or checking how much usage is left (use /usage).
---

# /handoff Command

Produce the cross-platform resume artifact: `.nexus-hub/handoff.md` in the project root, plus one fenced, self-contained prompt the user can paste into any agent to continue the task. `/handoff` has no scopes; every invocation does the same thing, with an optional free-text focus.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive logic lives in the skill; this file only delegates.

## Delegation

Dispatch every invocation to the skill:

      (any invocation) -> session-handoff

Pass any remaining arguments through unchanged as the focus (`/handoff focus on the failing migration` hands `focus on the failing migration` to the skill). With no arguments, run the skill's manual mode. When the invocation comes from a `Usage limit:` hook directive, the skill's usage-limit mode applies.

## Notes

- The file format, the carry-forward rule, the `.nexus-hub/` exclude rule, and the secret prohibition are defined in the `session-handoff` skill. Keep this dispatcher thin.
