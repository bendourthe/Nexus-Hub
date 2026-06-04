---
description: DEPRECATED (removed in v4.0.0). Forwarding to /compare. Was: compare the project to an external source and produce an adoption plan.
---

# /compare-project (deprecated)

`/compare-project` is deprecated and will be removed in v4.0.0. It now forwards to `/compare`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/compare` delegates to the same retained `compare-project` skill that ran the original work. Update scripts, docs, and muscle memory to call `/compare` directly.

When invoked, first print this notice:

      /compare-project is deprecated and will be removed in v4.0.0. Forwarding to /compare.

then delegate to `/compare`, passing every argument through unchanged.
