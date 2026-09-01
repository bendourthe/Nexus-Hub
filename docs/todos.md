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
| v4.4.1 guide-visual-and-arcade-rebuild phases complete | 4 | 7 | -3 |
| Local phase commits | 4 | 7 | -3 |
| Open release blockers | 0 | 0 | 0 |
| Catalog skills | 329 | 329 | 0 |
| Canonical guide bytes (strict ceiling 500,000) | 280,351 | < 500,000 | met |
| Platform marks approved with staged hashes | 5 | 5 | 0 |

---

## Plan - v4.4.1 Guide Visual and Arcade Rebuild [IN PROGRESS]

- [x] Phase 1 - Contracts, asset provenance, and byte budget
- [x] Phase 2 - Home identity, platform rail, and workflow loop
- [x] Phase 3 - Foundations structure, Tokens, Prompt, and Context
- [x] Phase 4 - Foundations Models, Agentic Platform, comparison, and harnesses
- [ ] Phase 5 - Deterministic arcade-shooter engine
- [ ] Phase 6 - Training workspace, fullscreen, and integrated loop
- [ ] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration

### What this plan changes, in one paragraph

A corrective visual and teaching pass over the shipped v4.4.0 guide. Home gains a floating Nexus Hub lockup, five integrated platform marks, and readable two-line command pills. Foundations is compacted and reordered into eight professionally titled concepts, with Models and Agentic Platform sharing one visual grammar. Training replaces the Asteroids scenario with a deterministic arcade shooter carrying a seeded lives bug, a falling-asteroid hazard, and a vertical-movement feature, and stays readable in and out of fullscreen.

### Prerequisite status

Met. v4.4.0 is released: integration PR #150 merged at `46518d01`, release PR #151 merged at `39f73a7e`, release PR #152 merged to `main` at `5c4b1346`, tag `v4.4.0` pushed with its GitHub Release published, and the artifact round-trip verified PASS over 1835 files. Back-merge PR #153 merged, and this branch was cut from a refreshed `develop` (`316aba97`) that contains the release merge.

### Current checkpoint

Phase 4 complete; Foundations is finished end to end. Scenes 4 through 8 became semantic HTML on the shared grammar: Models separates provider training from the live request and shows four output kinds whose embedded bytes hash-match the settled media ledger (DF-1 closed); Agentic Platform reuses the byte-identical entry motif and work-cycle glyph before three mission lanes, one permission-and-tool boundary, observations, and a report; the chatbot comparison keeps its honest-copy contracts; and the harness hierarchy is split into the built-in platform loop and the Nexus-Hub layer with its five repository-anchored claims. The rebuild orphaned and removed the traveling-pulse, fade, flip, dual-variant, and phase3-diagram CSS machinery, each retirement guarded in the suite. 165 passed, 1 skipped with rendering required; detector clean both themes at six viewports; guide at 280,351 bytes. Next: Phase 5 builds the deterministic arcade-shooter engine.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
