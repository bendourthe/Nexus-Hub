# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.0.0-cost-effective-ci-cd`
**Active plan:** [`docs/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md`](v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md)
**Last refreshed:** 2026-08-25

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/v3/roadmap-prioritization.md`](v3/roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) resolves DF-2 in [`docs/v3/v3.21/known-gaps.md`](v3/v3.21/known-gaps.md), which recorded that the dashboard had drifted to describe an old feature branch and carried scores from earlier minors.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.0.0 cost-effective-ci-cd phases complete | 8 | 8 | 0 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 325 | 325 | 0 |
| Substantive templates carrying the plan-lifecycle block | 12 | 12 | 0 |
| Terminal pipeline comparison fields PASS | 22 of 23 | 23 | 1 (DF-1, artifact upload) |
| Repository-native CI profiles | 5 | 5 | 0 |
| Workflows re-running the suite after merge | 0 | 0 | 0 |

---

## Plan - v4.0.0 Cost-Effective CI/CD [IN PROGRESS]

- [x] Phase 1 - Canonical lifecycle contract and baseline audit
- [x] Phase 2 - Canonical CI/CD skill architecture
- [x] Phase 3 - Plan generation defaults
- [x] Phase 4 - Implementation and commit lifecycle
- [x] Phase 5 - Branch, release, and cross-platform policy
- [x] Phase 6 - Repository-native CI engine
- [x] Phase 7 - Workflow migration
- [x] Phase 8 - Architecture refactor, known-gaps reconciliation, and CI/CD
- [ ] Release - deliberately NOT cut. Two of the three v4.0.0 plans are done and one is unstarted, so the version number is not spent yet. See the Release handoff section of [`docs/v4/v4.0/development/last-phase-evidence.md`](v4/v4.0/development/last-phase-evidence.md).

### What this plan changed, in one paragraph

Remote CI now runs once per completed plan rather than once per phase, and against the merge result rather than the branch tip. Every plan phase verifies locally and ends with one local commit; only the final phase pushes. Validation logic moved out of workflow YAML into five repository-native profiles a developer can run with no CI provider present, and `ci.yml` lost its protected-branch `push` trigger so a merge no longer re-runs what the pull request already proved.

---

## Plan - v4.0.0 Agent Communication Overhaul [DONE]

All five phases complete; merged to `develop` via PR #123. Outcome in [`docs/v4/v4.0/known-gaps.md`](v4/v4.0/known-gaps.md).

---

## Carried gaps under active consideration

- [ ] **v3.21 DF-1** - no product atlas HTML under `docs/handbooks/`. Deliberately not invented; needs real authored content before generation is meaningful. See [`docs/v3/v3.21/known-gaps.md`](v3/v3.21/known-gaps.md).
- [x] **v3.21 DF-2** - this dashboard described an old feature branch. Resolved by the refresh above.

---

## Other queued plans (not started)

These are committed plan documents awaiting their own cycle. Listing them here is a pointer, not a claim of progress.

- [`v4.0.0-docs-lifespan-tree-and-enforcement.md`](v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md)
- [`v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md`](v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md)
- [`v4.2.0-interactive-guide-redesign.md`](v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md)

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
