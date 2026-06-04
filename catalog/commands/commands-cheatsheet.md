---
description: DEPRECATED (removed in v4.0.0). Forwarding to /skills list. Was: list all commands in a categorized cheatsheet.
---

# /commands-cheatsheet (deprecated)

`/commands-cheatsheet` is deprecated and will be removed in v4.0.0. It now forwards to `/skills list`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/skills list` delegates to the same retained `commands-cheatsheet` skill that ran the original work. Update scripts, docs, and muscle memory to call `/skills list` directly.

When invoked, first print this notice:

      /commands-cheatsheet is deprecated and will be removed in v4.0.0. Forwarding to /skills list.

then delegate to `/skills list`, passing every argument through unchanged.
