---
description: DEPRECATED (removed in v4.0.0). Forwarding to /test unit. Was: exhaustive per-unit unit-test generation.
---

# /generate-unit-tests (deprecated)

`/generate-unit-tests` is deprecated and will be removed in v4.0.0. It now forwards to `/test unit`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/test unit` delegates to the same retained `generate-unit-tests` skill that ran the original work. Update scripts, docs, and muscle memory to call `/test unit` directly.

When invoked, first print this notice:

      /generate-unit-tests is deprecated and will be removed in v4.0.0. Forwarding to /test unit.

then delegate to `/test unit`, passing every argument through unchanged.
