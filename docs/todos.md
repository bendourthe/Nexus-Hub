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
| v4.4.0 guide-depth-and-training-rebuild phases complete | 5 | 7 | -2 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 329 | 329 | 0 |
| Guide pages with clean v4.4.0 verification evidence | 4 | 4 | 0 |
| Local phase commits | 5 | 7 | -2 |

---

## Plan - v4.4.0 Guide Depth and Training Rebuild [IN PROGRESS]

- [x] Phase 1 - Home identity, platforms, installation, and comparison
- [x] Phase 2 - Foundations structure, model, tokens, and prompts
- [x] Phase 3 - Chatbot vs agent, context, harness, and loop
- [x] Phase 4 - Playable Asteroids with a seeded bug
- [x] Phase 5 - Training terminal, file explorer, and command loop
- [ ] Phase 6 - Cross-page polish, accessibility, budget, and hallmark audit
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

Rebuilds the guide so Home sells the product clearly, Foundations teaches core AI concepts to non-technical readers with legible diagrams, and Training becomes a playable Asteroids walkthrough driven by the eight-command loop. Every phase dogfoods the v4.3.0 visual detector, functional smoke, plan-delta record, and fail-closed deep pass.

### Prerequisite status

v4.3.0 is tagged and released, so its verification discipline is available to gate this plan. Back-merge PR #149 is green and remains outside this plan; the v4.4.0 feature branch starts from `origin/develop`, whose tree matched the back-merge branch at pre-flight.

### Current checkpoint

Phase 5 is locally complete at its commit gate. All eight Training commands now run against the Asteroids game and a cumulative, keyboard-accessible file explorer with real artifacts. The seeded shot visibly changes from a miss to a fixed hit at `/implement`, then produces two fragments after `/compare`; reruns and direct jumps remain coherent. The fail-closed guide and detector aggregate is green at 148 passed with one expected portfolio-copy skip, both Training theme sweeps report zero findings, and independent re-review approved the corrected implementation with no P0-P3 findings. DF-1 and MT-1 remain open. No push, pull request, or remote CI run has occurred.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
