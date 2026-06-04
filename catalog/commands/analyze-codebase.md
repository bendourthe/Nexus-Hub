---
description: DEPRECATED (removed in v4.0.0). Forwarding to /describe full. Was: structured multi-section codebase analysis with diagrams.
---

# /analyze-codebase (deprecated)

`/analyze-codebase` is deprecated and will be removed in v4.0.0. It now forwards to `/describe full`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/describe full` delegates to the same retained `analyze-codebase` skill that ran the original work. Update scripts, docs, and muscle memory to call `/describe full` directly.

When invoked, first print this notice:

      /analyze-codebase is deprecated and will be removed in v4.0.0. Forwarding to /describe full.

then delegate to `/describe full`, passing every argument through unchanged.
