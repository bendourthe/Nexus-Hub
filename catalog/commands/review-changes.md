---
description: DEPRECATED (removed in v4.0.0). Forwarding to /review changes. Was: multi-agent persona review of the current diff, branch, or PR.
---

# /review-changes (deprecated)

`/review-changes` is deprecated and will be removed in v4.0.0. It now forwards to `/review changes`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/review changes` delegates to the same retained `review-changes` skill that ran the original work. Update scripts, docs, and muscle memory to call `/review changes` directly.

When invoked, first print this notice:

      /review-changes is deprecated and will be removed in v4.0.0. Forwarding to /review changes.

then delegate to `/review changes`, passing every argument through unchanged.
