---
description: DEPRECATED (removed in v4.0.0). Forwarding to /test tdd. Was: red-green-refactor TDD workflow with an 80% coverage gate.
---

# /tdd (deprecated)

`/tdd` is deprecated and will be removed in v4.0.0. It now forwards to `/test tdd`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/test tdd` delegates to the same retained `tdd` skill that ran the original work. Update scripts, docs, and muscle memory to call `/test tdd` directly.

When invoked, first print this notice:

      /tdd is deprecated and will be removed in v4.0.0. Forwarding to /test tdd.

then delegate to `/test tdd`, passing every argument through unchanged.
