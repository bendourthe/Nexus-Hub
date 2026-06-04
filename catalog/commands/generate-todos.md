---
description: DEPRECATED (removed in v4.0.0). Forwarding to /plan todos. Was: bootstrap docs/todos.md from git history, docs, and code annotations.
---

# /generate-todos (deprecated)

`/generate-todos` is deprecated and will be removed in v4.0.0. It now forwards to `/plan todos`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/plan todos` delegates to the same retained `generate-todos` skill that ran the original work. Update scripts, docs, and muscle memory to call `/plan todos` directly.

When invoked, first print this notice:

      /generate-todos is deprecated and will be removed in v4.0.0. Forwarding to /plan todos.

then delegate to `/plan todos`, passing every argument through unchanged.
