---
description: DEPRECATED (removed in v4.0.0). Forwarding to /test all. Was: deep whole-codebase test-coverage generation.
---

# /generate-tests (deprecated)

`/generate-tests` is deprecated and will be removed in v4.0.0. It now forwards to `/test all`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/test all` delegates to the same retained `generate-tests` skill that ran the original work. Update scripts, docs, and muscle memory to call `/test all` directly.

When invoked, first print this notice:

      /generate-tests is deprecated and will be removed in v4.0.0. Forwarding to /test all.

then delegate to `/test all`, passing every argument through unchanged.
