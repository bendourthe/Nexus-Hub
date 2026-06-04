---
description: DEPRECATED (removed in v4.0.0). Forwarding to /setup project. Was: bootstrap CLAUDE.md, scaffolding, README, DEVLOG, and CHANGELOG.
---

# /setup-project (deprecated)

`/setup-project` is deprecated and will be removed in v4.0.0. It now forwards to `/setup project`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/setup project` delegates to the same retained `setup-project` skill that ran the original work. Update scripts, docs, and muscle memory to call `/setup project` directly.

When invoked, first print this notice:

      /setup-project is deprecated and will be removed in v4.0.0. Forwarding to /setup project.

then delegate to `/setup project`, passing every argument through unchanged.
