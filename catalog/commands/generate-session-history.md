---
description: DEPRECATED (removed in v4.0.0). Forwarding to /session history. Was: document the development session as a standalone history file.
---

# /generate-session-history (deprecated)

`/generate-session-history` is deprecated and will be removed in v4.0.0. It now forwards to `/session history`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/session history` delegates to the same retained `generate-session-history` skill that ran the original work. Update scripts, docs, and muscle memory to call `/session history` directly.

When invoked, first print this notice:

      /generate-session-history is deprecated and will be removed in v4.0.0. Forwarding to /session history.

then delegate to `/session history`, passing every argument through unchanged.
