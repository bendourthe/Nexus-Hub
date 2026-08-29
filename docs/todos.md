# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.2.0-interactive-guide-redesign`
**Active plan:** [v4.2.0 interactive-guide-redesign](releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md)
**Last refreshed:** 2026-08-29

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.2.0 guide-redesign phases complete | 6 | 7 | -1 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 328 | 328 | 0 |
| New MCP servers | 0 | 0 | 0 |
| New installer-copied top-level scripts | 0 | 0 | 0 |

---

## Plan - v4.2.0 Interactive Guide Redesign [IN PROGRESS]

- [x] Phase 1 - Baseline, content model, and UX contract
- [x] Phase 2 - Portfolio-aligned shell, theme, and navigation
- [x] Phase 3 - Concise Home and embedded installation
- [x] Phase 4 - Model-versus-harness Foundations
- [x] Phase 5 - Interactive IDE training workbench
- [x] Phase 6 - Maintainer docs and copy contract
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

The public Nexus-Hub guide becomes a short orientation and install surface, a model-versus-harness Foundations page, and one data-driven IDE workbench for eight closed Training scenes, without changing command semantics or adding a runtime network dependency.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
