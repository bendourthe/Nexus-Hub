# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.0.0-docs-lifespan-tree-and-enforcement`
**Active plan:** [`docs/v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md`](v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md)
**Last refreshed:** 2026-08-26

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/v3/roadmap-prioritization.md`](v3/roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) resolves DF-2 in [`docs/v3/v3.21/known-gaps.md`](v3/v3.21/known-gaps.md), which recorded that the dashboard had drifted to describe an old feature branch and carried scores from earlier minors.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.0.0 docs-lifespan phases complete | 4 | 7 | 3 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 325 | 325 | 0 |
| Substantive templates carrying the plan-lifecycle block | 12 | 12 | 0 |
| Terminal pipeline comparison fields PASS | 22 of 23 | 23 | 1 (DF-1, artifact upload) |
| Repository-native CI profiles | 5 | 5 | 0 |
| Workflows re-running the suite after merge | 0 | 0 | 0 |

---

## Plan - v4.0.0 Docs Lifespan Tree and Enforcement [IN PROGRESS]

- [x] Phase 1 - Enforcement mechanisms
- [x] Phase 2 - Lifespan axis
- [x] Phase 3 - Breaking rename of the prescription
- [x] Phase 4 - Executable guards and anti-regression tests
- [ ] Phase 5 - Distribution to every platform class
- [ ] Phase 6 - Dogfood migration of Nexus-Hub's own tree
- [ ] Phase 7 - Architecture refactor, known-gaps reconciliation, and CI/CD
- [ ] Release - cut v4.0.0 only after all three bundle plans and the final integration gate are complete.

### What this plan changes, in one paragraph

The documentation standard will use lifespan as its single placement axis, ship proof-oriented link and move safeguards before the breaking rename, migrate Nexus-Hub's own tree to `docs/releases/` and `docs/archives/`, and distribute the rule to every supported platform class.

---

## Plan - v4.0.0 Agent Communication Overhaul [DONE]

All five phases complete; merged to `develop` via PR #123. Outcome in [`docs/v4/v4.0/known-gaps.md`](v4/v4.0/known-gaps.md).

---

## Plan - v4.0.0 Cost-Effective CI/CD [DONE]

All eight phases complete; merged to `develop` via PR #124 with follow-up PR #125. Outcome in [`docs/v4/v4.0/known-gaps.md`](v4/v4.0/known-gaps.md).

---

## Carried gaps under active consideration

- [ ] **v3.21 DF-1** - no product atlas HTML under `docs/handbooks/`. Deliberately not invented; needs real authored content before generation is meaningful. See [`docs/v3/v3.21/known-gaps.md`](v3/v3.21/known-gaps.md).
- [x] **v3.21 DF-2** - this dashboard described an old feature branch. Resolved by the refresh above.

---

## Other queued plans (not started)

These are committed plan documents awaiting their own cycle. Listing them here is a pointer, not a claim of progress.

- [`v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md`](v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md)
- [`v4.2.0-interactive-guide-redesign.md`](v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md)

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
