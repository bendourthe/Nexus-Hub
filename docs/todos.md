# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.4.0-guide-depth-and-training-rebuild`
**Active plan:** [v4.4.0 guide-depth-and-training-rebuild](releases/v4/v4.4/plans/v4.4.0-guide-depth-and-training-rebuild.md)
**Last refreshed:** 2026-08-31

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.4.0 guide-depth-and-training-rebuild phases complete | 6 | 7 | -1 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 329 | 329 | 0 |
| Guide pages with clean v4.4.0 verification evidence | 4 | 4 | 0 |
| Local phase commits | 7 | 7 | 0 |

---

## Plan - v4.4.0 Guide Depth and Training Rebuild [IN PROGRESS]

- [x] Phase 1 - Home identity, platforms, installation, and comparison
- [x] Phase 2 - Foundations structure, model, tokens, and prompts
- [x] Phase 3 - Chatbot vs agent, context, harness, and loop
- [x] Phase 4 - Playable Asteroids with a seeded bug
- [x] Phase 5 - Training terminal, file explorer, and command loop
- [x] Phase 6 - Cross-page polish, accessibility, budget, hallmark audit, and harness defaults
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

Rebuilds the guide so Home sells the product clearly, Foundations teaches core AI concepts to non-technical readers with legible diagrams, and Training becomes a playable Asteroids walkthrough driven by the eight-command loop. Every phase dogfoods the v4.3.0 visual detector, functional smoke, plan-delta record, and fail-closed deep pass.

### Prerequisite status

v4.3.0 is tagged and released, so its verification discipline is available to gate this plan. Back-merge PR #149 is green and remains outside this plan; the v4.4.0 feature branch starts from `origin/develop`, whose tree matched the back-merge branch at pre-flight.

### Current checkpoint

Phase 7 local closeout is complete in this scoped seventh commit. The corrected guide and detector aggregate passes 154 tests with one expected optional portfolio-copy skip, 27 of 27 implementation tasks and 9 of 9 Goal clauses converge, and the approved `guide-render` CI job closes MT-1. The corrected platform profile passed overall with 4 commands across 3 groups and the expected empty Windows shell-lint skip. The isolated exact-candidate full profile passed all 43 commands across 11 groups with no failure, skip, or advisory in 3,685.4 seconds; the earlier primary-worktree failure remains recorded as contamination from the excluded v4.4.1 plan. The three owner-authorized v4.4.0 decision records pass isolated candidate validation. DF-1 is the only open v4.4 product gap. No push, pull request, remote CI run, merge, tag, release, or back-merge has occurred.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
