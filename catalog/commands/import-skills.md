---
description: DEPRECATED (removed in v4.0.0). Forwarding to /skills import. Was: import catalog skills into a project.
---

# /import-skills (deprecated)

`/import-skills` is deprecated and will be removed in v4.0.0. It now forwards to `/skills import`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/skills import` delegates to the same retained `import-skills` skill that ran the original work. Update scripts, docs, and muscle memory to call `/skills import` directly.

When invoked, first print this notice:

      /import-skills is deprecated and will be removed in v4.0.0. Forwarding to /skills import.

then delegate to `/skills import`, passing every argument through unchanged.
