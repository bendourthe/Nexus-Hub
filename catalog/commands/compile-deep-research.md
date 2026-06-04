---
description: DEPRECATED (removed in v4.0.0). Forwarding to /research compile. Was: merge multiple research reports into one cited document.
---

# /compile-deep-research (deprecated)

`/compile-deep-research` is deprecated and will be removed in v4.0.0. It now forwards to `/research compile`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/research compile` delegates to the same retained `compile-deep-research` skill that ran the original work. Update scripts, docs, and muscle memory to call `/research compile` directly.

When invoked, first print this notice:

      /compile-deep-research is deprecated and will be removed in v4.0.0. Forwarding to /research compile.

then delegate to `/research compile`, passing every argument through unchanged.
