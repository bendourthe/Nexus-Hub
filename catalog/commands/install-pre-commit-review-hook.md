---
description: DEPRECATED (removed in v4.0.0). Forwarding to /setup hooks. Was: install an opt-in AI pre-commit review hook.
---

# /install-pre-commit-review-hook (deprecated)

`/install-pre-commit-review-hook` is deprecated and will be removed in v4.0.0. It now forwards to `/setup hooks`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/setup hooks` delegates to the same retained `install-pre-commit-review-hook` skill that ran the original work. Update scripts, docs, and muscle memory to call `/setup hooks` directly.

When invoked, first print this notice:

      /install-pre-commit-review-hook is deprecated and will be removed in v4.0.0. Forwarding to /setup hooks.

then delegate to `/setup hooks`, passing every argument through unchanged.
