---
description: DEPRECATED (removed in v4.0.0). Forwarding to /plan issues. Was: convert a tasks.md checklist into linked GitHub issues via gh.
---

# /tasks-to-issues (deprecated)

`/tasks-to-issues` is deprecated and will be removed in v4.0.0. It now forwards to `/plan issues`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/plan issues` delegates to the same retained `tasks-to-issues` skill that ran the original work. Update scripts, docs, and muscle memory to call `/plan issues` directly.

When invoked, first print this notice:

      /tasks-to-issues is deprecated and will be removed in v4.0.0. Forwarding to /plan issues.

then delegate to `/plan issues`, passing every argument through unchanged.
