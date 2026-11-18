---
description: DEPRECATED (removed in v4.15.5). Forwarding to /progress.
---

# /status Command (deprecated)

`/status` was renamed to `/progress` and is removed in v4.15.5.

Print this notice once, on one line: `/status is deprecated and is removed in v4.15.5. Use /progress.`

Forwarding to /progress: run [`/progress`](progress.md) with the same argument (`[vX.Y | vX.Y.Z | plan-path | plan-slug]`) and return its output unchanged. This shim holds no logic of its own, starts no work and changes no file.
