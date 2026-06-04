---
description: DEPRECATED (removed in v4.0.0). Forwarding to /spec clarify. Was: sequential 5-question spec clarification loop.
---

# /clarify-spec (deprecated)

`/clarify-spec` is deprecated and will be removed in v4.0.0. It now forwards to `/spec clarify`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/spec clarify` delegates to the same retained `clarify-spec` skill that ran the original work. Update scripts, docs, and muscle memory to call `/spec clarify` directly.

When invoked, first print this notice:

      /clarify-spec is deprecated and will be removed in v4.0.0. Forwarding to /spec clarify.

then delegate to `/spec clarify`, passing every argument through unchanged.
