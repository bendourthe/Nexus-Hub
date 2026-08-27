# Audit -- Category Placement and Slug Uniqueness (Phase 1.1)

**Plan**: [adoption-pm-claude-skills.md](./adoption-pm-claude-skills.md)
**Sub-task**: Phase 1.1 -- Confirm category placements for all 6 new skills
**Date**: 2026-05-19
**Status**: Confirmed -- no overrides, no collisions

## Method

For each of the 6 skill-native adoption candidates, the proposed category from the [comparison report](../comparison-pm-claude-skills.md) Section 11 was verified against the 22 existing catalog categories listed in [AGENTS.md](../../../AGENTS.md) "Adding a New Skill -> Choose the right category". Sibling skills in each proposed category were sampled to confirm topical fit. Slug uniqueness was checked by listing every directory under `catalog/skills/<proposed-category>/` AND by globally grepping `data/SKILL_INDEX.md` for each candidate slug.

## Results

| Skill | Proposed | Final category | Final slug | Sibling fit | Collision check |
|---|---|---|---|---|---|
| incident-postmortem | infrastructure | infrastructure | incident-postmortem | Sits next to sre-engineer, observability-setup, rollback-strategy-advisor. Postmortem document is an SRE-flavored operational artifact, matches the category's "production reliability and operations" theme. | No collision in catalog/skills/infrastructure/; no occurrence in data/SKILL_INDEX.md or anywhere else under catalog/skills/. |
| runbook-writer | infrastructure | infrastructure | runbook-writer | Same theme as above; complements release-notes-writer (which is also a "document-producer" sibling in this category) and cd-pipeline-generator. | No collision. release-notes-writer is the nearest name but distinct. |
| oncall-runbook | infrastructure | infrastructure | oncall-runbook | Per-alert response runbook is a tier-1 SRE artifact; sits next to runbook-writer (general ops runbooks) and sre-engineer. | No collision. |
| pr-description-writer | workflow | workflow | pr-description-writer | Sits next to code-commit-workflow, intent-based-review's adjacent workflow concerns, and shipping-and-launch. PR-authoring is git/workflow territory, not code-review (which evaluates a PR after it exists). | No collision in catalog/skills/workflow/; no global occurrence. |
| architecture-decision-record | architecture | architecture | architecture-decision-record | Sits next to architecture-design, api-design, ddd-strategic-design, component-boundary-identifier. ADRs are an architecture-recording artifact, which fits this category cleanly. | No collision in catalog/skills/architecture/; no global occurrence. |
| test-strategy-doc | tests-generation | tests-generation | test-strategy-doc | Sits next to test-structure, test-cases, code-coverage, testing-review. A test-strategy document is a meta-planning artifact for test generation, which matches the category. (The alternative was `testing/` -- which holds runtime test capabilities like browser-testing-with-devtools and domain-contract-validator -- a worse fit because the strategy doc is an upfront planning artifact, not runtime behavior.) | No collision in catalog/skills/tests-generation/; no global occurrence. |

## Decisions

- All 6 placements are **confirmed as proposed**.
- No category override needed.
- No slug rename needed; no `-doc` or `-template` suffix added (none required, no collisions).
- All 6 skills will be created at `catalog/skills/<category>/<slug>/SKILL.md` in Phases 2 and 3.

## Next

Proceed to Phase 1.2 -- baseline validator run.
