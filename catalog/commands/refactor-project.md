---
description: DEPRECATED (removed in v4.0.0). Forwarding to /update refactor. Was: refactor project artifacts to standard conventions.
---

# /refactor-project (deprecated)

`/refactor-project` is deprecated and will be removed in v4.0.0. It now forwards to `/update refactor`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/update refactor` delegates to the same retained `refactor-project` skill that ran the original work. Update scripts, docs, and muscle memory to call `/update refactor` directly.

When invoked, first print this notice:

      /refactor-project is deprecated and will be removed in v4.0.0. Forwarding to /update refactor.

then delegate to `/update refactor`, passing every argument through unchanged.
