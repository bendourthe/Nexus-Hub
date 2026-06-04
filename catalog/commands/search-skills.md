---
description: DEPRECATED (removed in v4.0.0). Forwarding to /skills search. Was: search the catalog by keyword, category, or role.
---

# /search-skills (deprecated)

`/search-skills` is deprecated and will be removed in v4.0.0. It now forwards to `/skills search`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/skills search` delegates to the same retained `search-skills` skill that ran the original work. Update scripts, docs, and muscle memory to call `/skills search` directly.

When invoked, first print this notice:

      /search-skills is deprecated and will be removed in v4.0.0. Forwarding to /skills search.

then delegate to `/skills search`, passing every argument through unchanged.
