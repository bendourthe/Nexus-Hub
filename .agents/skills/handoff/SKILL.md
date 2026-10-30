---
name: handoff
description: "Run the /handoff command. Print a paste-ready handoff prompt in the chat so another agent, on this or any other platform, can resume the task; no file is written unless you ask for one (\"/handoff file\", optionally with a path). Use to \"hand off\", \"write a handoff\", \"write the handoff to a file\", \"I am about to hit my usage limit\", \"continue this in another tool\", \"switch to Codex\", \"switch to Claude Code\", \"save my progress for another agent\", or when a \"Usage limit:\" hook message asks for /handoff. Accepts an optional focus, for example \"/handoff focus on the failing migration\". SKIP - an end-of-session history document (use /session), compacting context within this session (use the context-compression skill), or checking how much usage is left (use /usage)."
disable-model-invocation: true
---

# /handoff Command

Produce the cross-platform resume prompt: one fenced, self-contained prompt, printed in this chat, that the user can copy and paste into any agent to continue the task. No file is written. `/handoff` has no scopes; every invocation does the same thing, with an optional free-text focus.

A file is written only when the user asks for one in the same invocation: `/handoff file` writes `.nexus-hub/handoff.md`, and `/handoff file PATH` writes PATH. The prompt is still printed. An earlier request never carries over to a later handoff.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive logic lives in the skill; this file only delegates.

## Delegation

Dispatch every invocation to the skill:

      (any invocation) -> session-handoff

Pass any remaining arguments through unchanged (`/handoff focus on the failing migration` hands `focus on the failing migration` to the skill, which reads a leading `file` as the file request and the rest as the focus). With no arguments, run the skill's manual mode. When the invocation comes from a `Usage limit:` hook directive, the skill's usage-limit mode applies.

## Notes

- The prompt format, the chat-only default, the explicit file request, the carry-forward rule, the `.nexus-hub/` exclude rule, and the secret prohibition are defined in the `session-handoff` skill. Keep this dispatcher thin.
