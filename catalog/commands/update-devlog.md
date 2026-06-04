---
description: DEPRECATED (removed in v4.0.0). Forwarding to /update devlog. Was: append a DEVLOG entry for recent changes.
---

# /update-devlog (deprecated)

`/update-devlog` is deprecated and will be removed in v4.0.0. It now forwards to `/update devlog`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/update devlog` delegates to the same retained `update-devlog` skill that ran the original work. Update scripts, docs, and muscle memory to call `/update devlog` directly.

When invoked, first print this notice:

      /update-devlog is deprecated and will be removed in v4.0.0. Forwarding to /update devlog.

then delegate to `/update devlog`, passing every argument through unchanged.
