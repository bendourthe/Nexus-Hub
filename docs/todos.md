# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts`
**Active plan:** [`docs/releases/v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md`](releases/v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md)
**Last refreshed:** 2026-08-27

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) resolves DF-2 in [`docs/releases/v3/v3.21/known-gaps.md`](releases/v3/v3.21/known-gaps.md), which recorded that the dashboard had drifted to describe an old feature branch and carried scores from earlier minors.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.1.0 adoption phases complete | 4 | 6 | 2 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 326 | 326 | 0 |
| New typed-boundary skills | 1 | 1 | 0 |
| Oxlint dependencies in Nexus-Hub | 0 | 0 | 0 |

---

## Plan - v4.1.0 Skill Trial Records and Typed-Boundary Hygiene [IN PROGRESS]

- [x] Phase 1 - Procedural-anchor authoring rule
- [x] Phase 2 - Typed-boundary-hygiene skill and TypeScript handoff
- [x] Phase 3 - Distillation labels, confusability, and two-level triggers
- [x] Phase 4 - Eval-loop third arm
- [ ] Phase 5 - Decide whether to vendor Oxlint into user TypeScript repositories
- [ ] Phase 6 - Architecture refactor, known-gaps reconciliation, and CI/CD

### What this plan changes, in one paragraph

Skill authors will write procedural runbooks with labeled evidence and confusable-trigger fences, while a new typed-boundary-hygiene skill replaces low-evidence TypeScript contracts without adding Oxlint to Nexus-Hub itself.

---

## Other queued plans (not started)

These are committed plan documents awaiting their own cycle. Listing them here is a pointer, not a claim of progress.

- [`v4.2.0-interactive-guide-redesign.md`](releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md)

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
