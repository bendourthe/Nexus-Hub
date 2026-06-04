---
description: DEPRECATED (removed in v4.0.0). Forwarding to /session continue. Was: resume work after an interruption with a brief recap.
---

# /continue-session (deprecated)

`/continue-session` is deprecated and will be removed in v4.0.0. It now forwards to `/session continue`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/session continue` delegates to the same retained `continue-session` skill that ran the original work. Update scripts, docs, and muscle memory to call `/session continue` directly.

When invoked, first print this notice:

      /continue-session is deprecated and will be removed in v4.0.0. Forwarding to /session continue.

then delegate to `/session continue`, passing every argument through unchanged.
