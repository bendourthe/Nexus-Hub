# Changesets release automation

**Out of scope**: adopting npm changesets, a changesets-driven version-PR GitHub Action, or any second release pipeline that bumps versions outside `/update release` and `scripts/check_version_sync.py`.

## Why this is out of scope

Nexus-Hub already has a machine-enforced release path. `/update release` bumps every version-carrying surface as one atomic set (`plugin.json`, both installers, marketplace metadata, changelog heading, README / AGENTS.md catalog-version prose). `scripts/check_version_sync.py` fails `make validate` and CI when those surfaces drift. That is the v2.4.0 defect class, closed on purpose.

Changesets would add npm devDependencies and a parallel version-PR workflow to a repo whose installers, hooks, and validators are Python/bash/PowerShell. The new pipeline would either duplicate `/update release` or fight it: two tools that both believe they own the version number is how drift returns.

The decline is not "we have not gotten to it". The v3.20.3 comparison scored the item as `~` resolved in Nexus-Hub's favor and dropped it. Capability is already present locally and is strictly better for this catalog because it is drift-guarded across every installer-copied surface, not only `package.json`.

## Prior requests

- Decline record: [docs/releases/v3/v3.20/comparisons/v3.20.3-comparison-skills-craft-and-prime-agent.md](../../releases/v3/v3.20/comparisons/v3.20.3-comparison-skills-craft-and-prime-agent.md) (NOT recommended: changesets release automation).
- Plan that operationalized the drop: [docs/releases/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md](../../releases/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md) Phase 1, sub-task 1.2.
- The release path that stays in force: `/update release` in `catalog/commands/update.md`, plus `scripts/check_version_sync.py`.
- No dedicated GitHub issue asked to add changesets; the request arrived as a comparison candidate and was declined there.
