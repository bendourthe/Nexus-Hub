---
description: DEPRECATED (removed in v4.0.0). Forwarding to /review sbom. Was: generate a Software Bill of Materials.
---

# /generate-sbom (deprecated)

`/generate-sbom` is deprecated and will be removed in v4.0.0. It now forwards to `/review sbom`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/review sbom` delegates to the same retained `generate-sbom` skill that ran the original work. Update scripts, docs, and muscle memory to call `/review sbom` directly.

When invoked, first print this notice:

      /generate-sbom is deprecated and will be removed in v4.0.0. Forwarding to /review sbom.

then delegate to `/review sbom`, passing every argument through unchanged.
