---
description: DEPRECATED (removed in v4.0.0). Forwarding to /update version. Was: semantic-version upgrade with cleanup and changelog.
---

# /update-version (deprecated)

`/update-version` is deprecated and will be removed in v4.0.0. It now forwards to `/update version`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/update version` delegates to the same retained `update-version` skill that ran the original work. Update scripts, docs, and muscle memory to call `/update version` directly.

When invoked, first print this notice:

      /update-version is deprecated and will be removed in v4.0.0. Forwarding to /update version.

then delegate to `/update version`, passing every argument through unchanged.
