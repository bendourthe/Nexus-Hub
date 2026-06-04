---
description: DEPRECATED (removed in v4.0.0). Forwarding to /review pentest. Was: deep OWASP-WSTG static penetration test with proof-of-concept findings.
---

# /run-penetration-test (deprecated)

`/run-penetration-test` is deprecated and will be removed in v4.0.0. It now forwards to `/review pentest`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/review pentest` delegates to the same retained `run-penetration-test` skill that ran the original work. Update scripts, docs, and muscle memory to call `/review pentest` directly.

When invoked, first print this notice:

      /run-penetration-test is deprecated and will be removed in v4.0.0. Forwarding to /review pentest.

then delegate to `/review pentest`, passing every argument through unchanged.
