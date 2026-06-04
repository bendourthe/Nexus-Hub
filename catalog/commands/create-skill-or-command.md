---
description: DEPRECATED (removed in v4.0.0). Forwarding to /skills create. Was: interactive wizard to create a new skill or command.
---

# /create-skill-or-command (deprecated)

`/create-skill-or-command` is deprecated and will be removed in v4.0.0. It now forwards to `/skills create`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/skills create` delegates to the same retained `create-skill-or-command` skill that ran the original work. Update scripts, docs, and muscle memory to call `/skills create` directly.

When invoked, first print this notice:

      /create-skill-or-command is deprecated and will be removed in v4.0.0. Forwarding to /skills create.

then delegate to `/skills create`, passing every argument through unchanged.
