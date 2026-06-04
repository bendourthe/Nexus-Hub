---
description: DEPRECATED (removed in v4.0.0). Forwarding to /update changelog. Was: generate CHANGELOG.md from git history in Keep a Changelog format.
---

# /generate-changelog (deprecated)

`/generate-changelog` is deprecated and will be removed in v4.0.0. It now forwards to `/update changelog`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/update changelog` delegates to the same retained `generate-changelog` skill that ran the original work. Update scripts, docs, and muscle memory to call `/update changelog` directly.

When invoked, first print this notice:

      /generate-changelog is deprecated and will be removed in v4.0.0. Forwarding to /update changelog.

then delegate to `/update changelog`, passing every argument through unchanged.
