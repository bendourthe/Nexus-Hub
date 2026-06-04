---
description: DEPRECATED (removed in v4.0.0). Forwarding to /implement. Was: implement one plan phase end-to-end with the post-phase docs and commit sequence.
---

# /implement-phase (deprecated)

`/implement-phase` is deprecated and will be removed in v4.0.0. It now forwards to `/implement`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/implement` delegates to the same retained `implement-phase` skill that ran the original work. Update scripts, docs, and muscle memory to call `/implement` directly.

When invoked, first print this notice:

      /implement-phase is deprecated and will be removed in v4.0.0. Forwarding to /implement.

then delegate to `/implement`, passing every argument through unchanged.
