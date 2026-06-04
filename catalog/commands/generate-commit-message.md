---
description: DEPRECATED (removed in v4.0.0). Forwarding to /update commit. Was: generate a structured commit message for the staged changes.
---

# /generate-commit-message (deprecated)

`/generate-commit-message` is deprecated and will be removed in v4.0.0. It now forwards to `/update commit`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/update commit` delegates to the same retained `generate-commit-message` skill that ran the original work. Update scripts, docs, and muscle memory to call `/update commit` directly.

When invoked, first print this notice:

      /generate-commit-message is deprecated and will be removed in v4.0.0. Forwarding to /update commit.

then delegate to `/update commit`, passing every argument through unchanged.
