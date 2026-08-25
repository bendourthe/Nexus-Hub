# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.0.0-agent-communication-overhaul`
**Active plan:** [`docs/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md`](v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md)
**Last refreshed:** 2026-08-25

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/v3/roadmap-prioritization.md`](v3/roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) resolves DF-2 in [`docs/v3/v3.21/known-gaps.md`](v3/v3.21/known-gaps.md), which recorded that the dashboard had drifted to describe an old feature branch and carried scores from earlier minors.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.0.0 agent-communication phases complete | 5 | 5 | 0 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 325 | 325 | 0 |
| Substantive templates carrying the communication contract | 12 | 12 | 0 |

---

## Plan - v4.0.0 Agent Communication Overhaul [IN PROGRESS]

- [x] Phase 1 - Communication contract and decision record
- [x] Phase 2 - `agent-communication` skill
- [x] Phase 3 - Instruction-template rollout and parity gate
- [x] Phase 4 - Workflow report touchpoints
- [x] Phase 5 - Architecture refactor, known-gaps reconciliation, and CI/CD
- [ ] Release - deliberately NOT cut. Three plans target v4.0.0 and two are unstarted, so the version number is not spent yet. Maintainer decision 2026-08-25: push the branch, defer the numbering. See the Release handoff section of [`docs/v4/v4.0/development/last-phase-evidence.md`](v4/v4.0/development/last-phase-evidence.md).

---

## Carried gaps under active consideration

- [ ] **v3.21 DF-1** - no product atlas HTML under `docs/handbooks/`. Deliberately not invented; needs real authored content before generation is meaningful. See [`docs/v3/v3.21/known-gaps.md`](v3/v3.21/known-gaps.md).
- [x] **v3.21 DF-2** - this dashboard described an old feature branch. Resolved by the refresh above.

---

## Other queued plans (not started)

These are committed plan documents awaiting their own cycle. Listing them here is a pointer, not a claim of progress.

- [`v4.0.0-cost-effective-ci-cd.md`](v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md)
- [`v4.0.0-docs-lifespan-tree-and-enforcement.md`](v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md)
- [`v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md`](v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md)
- [`v4.2.0-interactive-guide-redesign.md`](v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md)

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
