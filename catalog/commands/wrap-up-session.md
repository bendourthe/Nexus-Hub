---
description: DEPRECATED (removed in v4.0.0). Forwarding to /session wrap-up. Was: wrap up a session: history, cleanup, docs, devlog, and commit message.
---

# /wrap-up-session (deprecated)

`/wrap-up-session` is deprecated and will be removed in v4.0.0. It now forwards to `/session wrap-up`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/session wrap-up` delegates to the same retained `wrap-up-session` skill that ran the original work. Update scripts, docs, and muscle memory to call `/session wrap-up` directly.

When invoked, first print this notice:

      /wrap-up-session is deprecated and will be removed in v4.0.0. Forwarding to /session wrap-up.

then delegate to `/session wrap-up`, passing every argument through unchanged.
