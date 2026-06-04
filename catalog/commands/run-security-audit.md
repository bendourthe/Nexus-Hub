---
description: DEPRECATED (removed in v4.0.0). Forwarding to /review security. Was: security audit with an active remediation loop.
---

# /run-security-audit (deprecated)

`/run-security-audit` is deprecated and will be removed in v4.0.0. It now forwards to `/review security`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/review security` delegates to the same retained `run-security-audit` skill that ran the original work. Update scripts, docs, and muscle memory to call `/review security` directly.

When invoked, first print this notice:

      /run-security-audit is deprecated and will be removed in v4.0.0. Forwarding to /review security.

then delegate to `/review security`, passing every argument through unchanged.
