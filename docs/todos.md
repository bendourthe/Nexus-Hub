# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.2.2-guide-cinematic-rebuild` (v4.2.3 folds into the same branch and PR #146)
**Active plan:** [v4.2.3 guide-refinement](releases/v4/v4.2/plans/v4.2.3-guide-refinement.md)
**Last refreshed:** 2026-08-29

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.2.3 guide-refinement phases complete | 5 | 7 | -2 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 328 | 328 | 0 |
| New MCP servers | 0 | 0 | 0 |
| New installer-copied top-level scripts | 0 | 0 | 0 |

---

## Plan - v4.2.3 Interactive Guide Refinement [IN PROGRESS]

- [x] Phase 1 - Fluid layout, copy affordance, and shared conventions
- [x] Phase 2 - Home: readable install verify and an animated comparison
- [x] Phase 3 - Foundations: project-generic content and diagram repair
- [x] Phase 4 - Training: full-screen present mode and loop-stage progress
- [x] Phase 5 - Cheatsheets: terminal usage illustration and readable scopes
- [ ] Phase 6 - Cross-page polish, accessibility, and hallmark audit
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

Refines the v4.2.2 rebuild against the maintainer's second review: body text fills the content column with no hardcoded measure, copy affordances become bare icons instead of chips inside chips, the install verify block is rebuilt for readability, Home's plain comparison table becomes an animated visual, Foundations drops its number line and teaches in project-generic language with repaired diagrams and consistent without-then-with ordering, Training uses the full screen in present mode with bottom-right icon controls and a loop-stage progress bar, Cheatsheets shows usage in a terminal with commands colored apart from arguments, and page-nav buttons are sized to their content. v4.2.2 remains unpublished; both ship together through PR #146.

### v4.2.2 status

Complete and committed (7 phases). Its stabilization commit `f4203850` is held locally with this work; PR #146 is open and BLOCKED until the v4.2.3 final phase pushes.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
