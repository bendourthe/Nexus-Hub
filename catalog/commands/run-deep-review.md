---
description: DEPRECATED (removed in v4.0.0). Forwarding to /review full. Was: orchestrated pre-release deep review across all lenses.
---

# /run-deep-review (deprecated)

`/run-deep-review` is deprecated and will be removed in v4.0.0. It now forwards to `/review full`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/review full` delegates to the same retained `run-deep-review` skill that ran the original work. Update scripts, docs, and muscle memory to call `/review full` directly.

When invoked, first print this notice:

      /run-deep-review is deprecated and will be removed in v4.0.0. Forwarding to /review full.

then delegate to `/review full`, passing every argument through unchanged.
