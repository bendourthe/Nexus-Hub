---
description: DEPRECATED (removed in v4.0.0). Forwarding to /memory. Was: audit, prune, and manage CLAUDE.md and memory files.
---

# /manage-memory (deprecated)

`/manage-memory` is deprecated and will be removed in v4.0.0. It now forwards to `/memory`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/memory` delegates to the same retained `manage-memory` skill that ran the original work. Update scripts, docs, and muscle memory to call `/memory` directly.

When invoked, first print this notice:

      /manage-memory is deprecated and will be removed in v4.0.0. Forwarding to /memory.

then delegate to `/memory`, passing every argument through unchanged.
