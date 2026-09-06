# Oxlint in Nexus-Hub

**Out of scope**: adding Oxlint or `@oxlint/plugins` to Nexus-Hub runtime or CI, and shipping a catalog skill that vendors a typed-boundary Oxlint plugin into consumer TypeScript repositories.

## Why this is out of scope

The `typed-boundary-hygiene` skill already teaches the intended behavior across every supported agent platform without a package dependency, network lookup, or repository-specific lint configuration. Nexus-Hub has no in-repo TypeScript application that could prove an ESTree visitor implementation or continuously exercise `@oxlint/plugins` API compatibility.

A vendor skill would therefore make Nexus-Hub maintain installation, package-manager detection, configuration merging, overwrite safety, rule semantics, and upstream API drift for code that never runs in Nexus-Hub itself. That is a larger and less testable ownership surface than the capability warrants. The rejected decision records the evidence and the explicit superseding-decision requirement if those facts later change.

## Prior requests

- Rejected decision: [docs/decisions/rejected/tooling/2026-08-24-typed-boundary-oxlint-vendor.md](../../decisions/rejected/tooling/2026-08-24-typed-boundary-oxlint-vendor.md).
- Adoption plan: [docs/releases/v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md](../../releases/v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md), Phase 5.
- Seeding comparison: [docs/releases/v4/v4.1/comparisons/v4.1.0-comparison-skill-trial-records-and-low-evidence-ts.md](../../releases/v4/v4.1/comparisons/v4.1.0-comparison-skill-trial-records-and-low-evidence-ts.md).
