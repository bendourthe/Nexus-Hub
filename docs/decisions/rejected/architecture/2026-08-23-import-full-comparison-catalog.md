# Decision: Import the full 817-skill comparison cybersecurity catalog

Status: rejected - the ~416k-token always-resident projection is incompatible with Nexus-Hub's three-tier loading model

## Problem

The comparison catalog is 817 SKILL.md files on the same open standard. Nexus-Hub's security-domain coverage at plan time was 40 skills. A full import would close every named gap in one release and would make Nexus-Hub a drop-in superset for users coming from that catalog.

## Proposal

Copy or independently rewrite all 817 skills into `catalog/skills/`, register them in the three registry files, and accept the Tier-1 token cost as the price of completeness.

## Alternatives considered

- **Independent authorship of all 817, still as 817 entries.** This is what won on license grounds if completeness were the goal, and it still loses: 817 always-loaded description blocks project to about 416k Tier-1 tokens (from ~104k at 273 skills). Completeness that cannot fit in a session is not completeness.
- **Import as Tier-3 only (bodies on disk, no Tier-1 frontmatter in the index).** Rejected as a variant: the skill index and MCP server still need `name` plus `description` plus `summary_l0` plus `overview_l1` for routing. Hiding 817 skills from the index makes them undiscoverable, which is the same as not shipping them.
- **Vendor-neutral consolidation at about 4.3:1 (40 skills).** This is what shipped. See `docs/decisions/implemented/architecture/2026-08-23-vendor-neutral-capability-consolidation.md`.

## Acceptance criteria

- Catalog skill count would rise by 817 (or by the independently rewritten equivalent).
- Every comparison-catalog topic would have a same-named or mapped Nexus-Hub skill.
- `make validate` would still pass.

The first criterion is the one that fails the architecture, so the proposal is rejected even though the third is mechanically achievable.
