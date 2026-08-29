# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.2.2-guide-cinematic-rebuild`
**Active plan:** [v4.2.2 guide-cinematic-rebuild](releases/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md)
**Last refreshed:** 2026-08-29

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.2.2 guide-cinematic-rebuild phases complete | 2 | 7 | -5 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 328 | 328 | 0 |
| New MCP servers | 0 | 0 | 0 |
| New installer-copied top-level scripts | 0 | 0 | 0 |

---

## Plan - v4.2.2 Interactive Guide Cinematic Rebuild [IN PROGRESS]

- [x] Phase 1 - Design brief, design system, shell, and render harness
- [x] Phase 2 - Home page rebuild
- [ ] Phase 3 - Foundations rebuild
- [ ] Phase 4 - Training rebuild
- [ ] Phase 5 - Cheatsheets rebuild
- [ ] Phase 6 - Cross-page polish, accessibility, and hallmark audit
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

The guide is re-engineered from the ground up, superseding the unpublished v4.2.1 UI (its publication step is never run): a compact cinematic design system with rendered-screenshot QA every phase, a Home page fixing all seven 2026-08-29 screenshot defects (Windows-first install, slim copy buttons, no warning box, copyable verify commands, shared hero measure, fixed GitHub icon, light-mode logo chip), a from-scratch animated Foundations, a from-scratch interactive Training (Glow Booth mockup, simulated terminal, fullscreen slides), and Cheatsheets with per-scope command documentation - all inside the same single offline HTML file and test gate.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
