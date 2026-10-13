# Decision: The install-verify manifest excludes extensions

Status: implemented - `nexus-hub verify` keeps covering only the copied roots (catalog, templates, scripts, data); the pip-installed `extensions/` sources are excluded by design.

## Problem

`scripts/generate_manifest.py` defines `COVERED_ROOTS` as `catalog`, `templates`, `scripts`, and `data`, so `nexus-hub verify` never checks `extensions/`. A v3.10 deferral (carried as v4.13 AR-21) asked whether to extend the manifest to the MCP-server sources or record the exclusion.

## Decision

The manifest stays limited to the roots the installer copies verbatim. The `extensions/` MCP servers are installed with pip into their own environments, so their installed form is a built package, not a byte copy of the repository files; a hash of the repository sources would not describe what is installed, and pip already verifies package integrity at install time.

Reopening trigger: the installer starts copying any `extensions/` file verbatim into an installed tree, or the MCP servers move to a distribution path without package-level integrity.

## Alternatives considered

**Add `extensions/` to `COVERED_ROOTS`.** Rejected. Hashing several hundred source files that are never present byte for byte in an installed tree would report every installation as modified, or would require mapping built packages back to sources, which duplicates pip's own integrity checks.

**Leave the item open.** Rejected by the maintainer on 2026-10-10 during v4.13.11 Phase 7.

## Consequences

- v4.13 AR-21 (origin v3.10 DF-v310-ruflo-P4-extensions, also carried in v3.11) closes on this record.
- `nexus-hub verify` continues to report only on copied files; extension integrity remains pip's responsibility.
