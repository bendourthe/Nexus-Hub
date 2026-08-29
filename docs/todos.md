# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.1.2-release`
**Active plan:** [`docs/releases/v4/v4.1/plans/v4.1.2-adoption-minimal-construction.md`](releases/v4/v4.1/plans/v4.1.2-adoption-minimal-construction.md)
**Last refreshed:** 2026-08-28

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.1.2 adoption phases complete | 5 | 5 | 0 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 328 | 328 | 0 |
| New MCP servers | 0 | 0 | 0 |
| New installer-copied top-level scripts | 0 | 0 | 0 |

---

## Release - v4.1.2 [LOCAL PREPARATION]

- [x] Merge the five-phase implementation into `develop` with green integration checks ([#141](https://github.com/bendourthe/Nexus-Hub/pull/141), `34d8272b`)
- [x] Derive release notes from `v4.1.1..origin/develop`
- [x] Prepare and verify the v4.1.2 release commit
- [ ] Promote `develop` to `main`, tag v4.1.2, publish the GitHub Release, and back-merge

---

## Plan - v4.1.2 Minimal Construction Discipline [INTEGRATED]

- [x] Phase 1 - Construction-discipline contract and always-on templates
- [x] Phase 2 - `minimal-construction` skill
- [x] Phase 3 - `over-engineering-review` skill
- [x] Phase 4 - Construction-debt harvest and eval proof
- [x] Phase 5 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

Every Nexus-Hub-backed agent now has an always-on pre-write construction ladder, plus two skills for intensity and delete-list review, without an MCP, Ponytail vendor, or a weaker security or verification owner.

---

## Other queued plans (not started)

These are committed plan documents awaiting their own cycle. Listing them here is a pointer, not a claim of progress.

- [`v4.2.0-interactive-guide-redesign.md`](releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md)

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
