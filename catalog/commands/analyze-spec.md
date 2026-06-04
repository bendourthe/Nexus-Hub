---
description: DEPRECATED (removed in v4.0.0). Forwarding to /spec analyze. Was: cross-artifact spec consistency and coverage analysis.
---

# /analyze-spec (deprecated)

`/analyze-spec` is deprecated and will be removed in v4.0.0. It now forwards to `/spec analyze`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/spec analyze` delegates to the same retained `analyze-spec` skill that ran the original work. Update scripts, docs, and muscle memory to call `/spec analyze` directly.

When invoked, first print this notice:

      /analyze-spec is deprecated and will be removed in v4.0.0. Forwarding to /spec analyze.

then delegate to `/spec analyze`, passing every argument through unchanged.
