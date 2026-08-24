# Decision: Adopt comparison-catalog security coverage by independent authorship, not text reuse

Status: implemented - Phase 4 skills are original MIT prose written from public primary sources; no Apache-2.0 comparison-catalog text is copied into the tree

## Problem

The v3.20.1 comparison identified an 817-skill Apache-2.0 cybersecurity catalog on the same SKILL.md standard, with framework-mapping keys that already match Nexus-Hub's optional frontmatter. Copying those files would close coverage gaps quickly. Nexus-Hub is MIT. Mixing Apache-2.0 skill bodies into an MIT catalog, or shipping a dual-license subtree, would put every downstream installer user on a license they did not opt into, and would make provenance of every later edit legally ambiguous.

## Decision

Security content is adopted by independent authorship. Each new skill is written from public primary sources (MITRE ATT&CK, D3FEND, NIST CSF, OWASP, NERC CIP, SLSA, SSVC, platform vendor security guides). Distributed artifacts (SKILL.md, references/, evals/) do not name the comparison catalog. Attribution for the comparison itself stays in `docs/v3/v3.20/comparisons/` and in this record. A mixed-license catalog is out of bounds.

## Alternatives considered

- **Copy the Apache-2.0 SKILL.md files and add an Apache-2.0 notice in those directories.** Rejected: the installer flattens skills into `~/.nexus-hub/` and into platform skill folders with no per-file license surface a user will read. Dual license in a catalog consumed as one MIT product is a silent license change for every install.
- **Vendor the comparison catalog as a separate optional pack behind a license prompt.** Rejected: Nexus-Hub's installer is no-prompt by default, and an optional pack would still land Apache-2.0 prose next to MIT skills on disk. It also explodes Tier-1 tokens (see the companion rejection of a full-catalog import).
- **Rewrite by paraphrase from the comparison SKILL.md files.** Rejected: close paraphrase of copyrighted expression is still a derivative work. Independent authorship means primary sources, not a thesaurus pass over someone else's skill body.

## Consequences

- Phase 4 took longer than a copy would have: forty skills, frontmatter, authorization gates, and trigger evals were authored in-tree.
- Coverage can lag the comparison catalog on vendor-specific product names; that lag is accepted in the vendor-neutral consolidation decision.
- Any later proposal to import third-party SKILL.md files must re-open this record, not treat Phase 4 as a precedent for paste.
