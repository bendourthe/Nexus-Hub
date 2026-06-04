---
description: DEPRECATED (removed in v4.0.0). Forwarding to /usage. Was: check usage limits and model-switch advice.
---

# /check-usage (deprecated)

`/check-usage` is deprecated and will be removed in v4.0.0. It now forwards to `/usage`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/usage` delegates to the same retained `check-usage` skill that ran the original work. Update scripts, docs, and muscle memory to call `/usage` directly.

When invoked, first print this notice:

      /check-usage is deprecated and will be removed in v4.0.0. Forwarding to /usage.

then delegate to `/usage`, passing every argument through unchanged.
