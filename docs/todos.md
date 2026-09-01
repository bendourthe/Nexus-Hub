# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.4.1-guide-visual-and-arcade-rebuild`
**Active plan:** [v4.4.1 guide-visual-and-arcade-rebuild](releases/v4/v4.4/plans/v4.4.1-guide-visual-and-arcade-rebuild.md)
**Last refreshed:** 2026-09-01

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.4.1 guide-visual-and-arcade-rebuild phases complete | 2 | 7 | -5 |
| Local phase commits | 2 | 7 | -5 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 329 | 329 | 0 |
| Canonical guide bytes (strict ceiling 500,000) | 281,301 | < 500,000 | met |
| Platform marks approved with staged hashes | 5 | 5 | 0 |

---

## Plan - v4.4.1 Guide Visual and Arcade Rebuild [IN PROGRESS]

- [x] Phase 1 - Contracts, asset provenance, and byte budget
- [x] Phase 2 - Home identity, platform rail, and workflow loop
- [ ] Phase 3 - Foundations structure, Tokens, Prompt, and Context
- [ ] Phase 4 - Foundations Models, Agentic Platform, comparison, and harnesses
- [ ] Phase 5 - Deterministic arcade-shooter engine
- [ ] Phase 6 - Training workspace, fullscreen, and integrated loop
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

A corrective visual and teaching pass over the shipped v4.4.0 guide. Home gains a floating Nexus Hub lockup, five integrated platform marks, and readable two-line command pills. Foundations is compacted and reordered into eight professionally titled concepts, with Models and Agentic Platform sharing one visual grammar. Training replaces the Asteroids scenario with a deterministic arcade shooter carrying a seeded lives bug, a falling-asteroid hazard, and a vertical-movement feature, and stays readable in and out of fullscreen.

### Prerequisite status

Met. v4.4.0 is released: integration PR #150 merged at `46518d01`, release PR #151 merged at `39f73a7e`, release PR #152 merged to `main` at `5c4b1346`, tag `v4.4.0` pushed with its GitHub Release published, and the artifact round-trip verified PASS over 1835 files. Back-merge PR #153 merged, and this branch was cut from a refreshed `develop` (`316aba97`) that contains the release merge.

### Current checkpoint

Phase 2 complete. Home leads with one floating `Nexus Hub` lockup whose mark and both wordmark spans share a single observer-gated 7s float, five approved platform marks inlined verbatim and hash-checked against the provenance ledger, a CC BY 4.0 credits disclosure, and readable two-line workflow pills. OpenCode and the text-treatment fallback are gone. The visual detector passes both themes at six viewports with 0 findings and 60 documented allowlisted entries covering the Gemini mark's blur construction. Guide at 281,301 bytes, 218,699 under the ceiling. Next: Phase 3 must cut the 1440 px Foundations scroll height from 7,294 px to at most 5,835 px and land the first three accepted scene titles.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
