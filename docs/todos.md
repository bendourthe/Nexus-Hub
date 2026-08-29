# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.2.1-guide-visual-education`
**Active plan:** [v4.2.1 guide-visual-education](releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md)
**Last refreshed:** 2026-08-29

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.2.1 guide-visual-education phases complete | 2 | 7 | -5 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 328 | 328 | 0 |
| New MCP servers | 0 | 0 | 0 |
| New installer-copied top-level scripts | 0 | 0 | 0 |

---

## Plan - v4.2.1 Interactive Guide Visual Education [IN PROGRESS]

- [x] Phase 1 - Contract, IA, and example freeze
- [x] Phase 2 - Chrome, theme, and install terminals
- [ ] Phase 3 - Home loop visual
- [ ] Phase 4 - Foundations visual education
- [ ] Phase 5 - Training slideshow and Glow Booth
- [ ] Phase 6 - Cheatsheets merge
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

The unpublished v4.2.0 guide becomes a visual, interactive, accessible first-contact site: opaque chrome and working light theme, Foundations that teach prompt/context/harness/loop engineering with pictures, a Training slideshow of Glow Booth going from buggy to fixed, and one Cheatsheets tab instead of Workflows plus Reference, without changing command semantics or adding a runtime network dependency.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
