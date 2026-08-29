# Nexus-Hub Progress Dashboard

**Branch:** `develop`
**Active plan:** [`docs/releases/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md`](releases/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md)
**Last refreshed:** 2026-08-28

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.1.1 adoption phases complete | 5 | 5 | 0 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 326 | 326 | 0 |
| New MCP servers | 0 | 0 | 0 |
| Scanner auto-install paths | 0 | 0 | 0 |

---

## Release - v4.1.1 [LOCAL PREPARATION]

- [x] Merge the five-phase implementation into `develop` with green integration checks ([#137](https://github.com/bendourthe/Nexus-Hub/pull/137), `0787ebf9`)
- [x] Approve release notes derived from `v4.1.0..origin/develop`
- [x] Prepare and verify the v4.1.1 release commit
- [ ] Promote `develop` to `main`, tag v4.1.1, publish the GitHub Release, and back-merge

---

## Plan - v4.1.1 Security-Audit Scanner Receipts [INTEGRATED]

- [x] Phase 1 - Fail-closed schema-v2 scanner receipts
- [x] Phase 2 - Optional local scanner recipes, one owner each
- [x] Phase 3 - Ordered `security-audit` preset and read-only reviewer
- [x] Phase 4 - Inert fixtures, e2e, `security-specialist`, user guide
- [x] Phase 5 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

A full local security-audit run now proves which optional scanners ran, keeps missing tools visible, separates remediation from verification, and requires a same-detector re-scan after a user-approved patch, without adding OpenWorker, MCP, hosted scanning, or auto-install.

---

## Other queued plans (not started)

These are committed plan documents awaiting their own cycle. Listing them here is a pointer, not a claim of progress.

- [`v4.2.0-interactive-guide-redesign.md`](releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md)

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
