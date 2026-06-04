---
description: DEPRECATED (removed in v4.0.0). Forwarding to /plan. Was: guided discovery interview producing a phased plan.
---

# /generate-plan (deprecated)

`/generate-plan` is deprecated and will be removed in v4.0.0. It now forwards to `/plan`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/plan` delegates to the same retained `generate-plan` skill that ran the original work. Update scripts, docs, and muscle memory to call `/plan` directly.

When invoked, first print this notice:

      /generate-plan is deprecated and will be removed in v4.0.0. Forwarding to /plan.

then delegate to `/plan`, passing every argument through unchanged.
