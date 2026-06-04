---
description: DEPRECATED (removed in v4.0.0). Forwarding to /update gitignore. Was: audit .gitignore, clean the index, and recommend Git LFS.
---

# /update-gitignore (deprecated)

`/update-gitignore` is deprecated and will be removed in v4.0.0. It now forwards to `/update gitignore`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/update gitignore` delegates to the same retained `update-gitignore` skill that ran the original work. Update scripts, docs, and muscle memory to call `/update gitignore` directly.

When invoked, first print this notice:

      /update-gitignore is deprecated and will be removed in v4.0.0. Forwarding to /update gitignore.

then delegate to `/update gitignore`, passing every argument through unchanged.
