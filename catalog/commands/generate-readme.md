---
description: DEPRECATED (removed in v4.0.0). Forwarding to /update docs. Was: generate a production-quality README.md.
---

# /generate-readme (deprecated)

`/generate-readme` is deprecated and will be removed in v4.0.0. It now forwards to `/update docs`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/update docs` delegates to the same retained `generate-readme` skill that ran the original work. Update scripts, docs, and muscle memory to call `/update docs` directly.

When invoked, first print this notice:

      /generate-readme is deprecated and will be removed in v4.0.0. Forwarding to /update docs.

then delegate to `/update docs`, passing every argument through unchanged.
