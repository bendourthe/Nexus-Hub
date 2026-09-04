# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.4.3-guide-illustration-rebuild`
**Active plan:** [v4.4.6 guide-learning-experience](releases/v4/v4.4/plans/v4.4.6-guide-learning-experience.md), implementation in progress; Phases 1-4 complete. Predecessor v4.4.5 is locally complete and unpublished.
**Last refreshed:** 2026-09-04

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.


---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.4.6 guide-learning-experience phases complete | 4 | 7 | 3 |
| v4.4.6 guide-learning-experience tasks complete | 12 | 28 | 16 |
| v4.4.1 guide-visual-and-arcade-rebuild phases complete | 7 | 7 | 0 |
| v4.4.2 guide-production-ready-rebuild phases complete | 8 | 8 | 0 |
| v4.4.2 local phase commits | 8 | 8 | 0 |
| Prior v4.4.2 release blockers (historical) | 0 | 0 | 0 |
| Confirmed guide defects remaining | 1 | 0 | 1 |
| Catalog skills | 329 | 329 | 0 |
| Canonical guide bytes (strict ceiling 500,000) | 358,278 | < 500,000 | met |
| Platform marks approved with staged hashes | 5 | 5 | 0 |

---

## Plan - v4.4.6 Guide Learning Experience [IN PROGRESS]

- [x] Review current Home, Foundations, Training, and the two supplied source documents; retain current browser evidence.
- [x] Write the seven-phase implementation plan with continuous visual and performance gates.
- [x] Phase 1 - Baseline and teaching/design contract.
- [x] Phase 2 - Shared layout and motion repair.
- [x] Phase 3 - Home refinement.
- [x] Phase 4 - Foundations: model, tokens, prompt, context.
- [ ] Phase 5 - Foundations: harness, loop, graph.
- [ ] Phase 6 - Training clarity and state integrity.
- [ ] Phase 7 - Final verification, known gaps, CI/CD, and approval-gated integration.

Shared visibility and idle game rendering are fixed and browser-verified. Home is concise and browser-verified; Foundations content rebuilds are next; the pre-run Training success claim remains scheduled for Phase 6. Earlier dashboard counts below are historical and do not qualify this plan.

---

## Plan - v4.4.1 Guide Visual and Arcade Rebuild [MERGED TO DEVELOP 2026-09-02, PR #154; release pending]

- [x] Phase 1 - Contracts, asset provenance, and byte budget
- [x] Phase 2 - Home identity, platform rail, and workflow loop
- [x] Phase 3 - Foundations structure, Tokens, Prompt, and Context
- [x] Phase 4 - Foundations Models, Agentic Platform, comparison, and harnesses
- [x] Phase 5 - Deterministic arcade-shooter engine
- [x] Phase 6 - Training workspace, fullscreen, and integrated loop
- [x] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration (local duties; publication in progress)

## Plan - v4.4.2 Guide Production-Ready Rebuild [PUBLISHED FOR INTEGRATION 2026-09-02]

Plan: [v4.4.2-guide-production-ready-rebuild.md](releases/v4/v4.4/plans/v4.4.2-guide-production-ready-rebuild.md). Branch cut from `develop` at `46f18986` on 2026-09-02.

- [x] Phase 1 - Contracts, motion system, scale tokens, and rename
- [x] Phase 2 - Home hero and restored sections
- [x] Phase 3 - Foundations title system, layout balance, and annotated prompts
- [x] Phase 4 - Foundations Models, Agentic Platform, and the layered harness animation
- [x] Phase 5 - Arena engine v2
- [x] Phase 6 - Training fullscreen three-pane presentation
- [x] Phase 7 - Integrated verification and documentation
- [x] Phase 8 - Architecture refactor, known-gaps, CI/CD, and publication (local duties and GO; integration PR open, merge on green)

### What this plan changes, in one paragraph

A corrective visual and teaching pass over the shipped v4.4.0 guide. Home gains a floating Nexus Hub lockup, five integrated platform marks, and readable two-line command pills. Foundations is compacted and reordered into eight professionally titled concepts, with Models and Agentic Platform sharing one visual grammar. Training replaces the Asteroids scenario with a deterministic arcade shooter carrying a seeded lives bug, a falling-asteroid hazard, and a vertical-movement feature, and stays readable in and out of fullscreen.

### Prerequisite status

Met. v4.4.0 is released: integration PR #150 merged at `46518d01`, release PR #151 merged at `39f73a7e`, release PR #152 merged to `main` at `5c4b1346`, tag `v4.4.0` pushed with its GitHub Release published, and the artifact round-trip verified PASS over 1835 files. Back-merge PR #153 merged, and this branch was cut from a refreshed `develop` (`316aba97`) that contains the release merge.

### Earlier checkpoint (retained; superseded by the v4.4.5 local closeout)

Phase 5 complete. `window.NexusShooter` replaces the Asteroids engine: a mulberry32-seeded fixed-step portrait shooter (360x480, 1/60s tick) whose deep-frozen snapshots deep-equal across runs with one seed, with terminal `destroyed` semantics, composable pause reasons, a Click-to-start idle gate, procedural layered art, an authoritative HUD with a change-only live region, and full keyboard, touch, reduced-motion, and no-canvas paths. The seeded bug is now first-enemy-hit-destroys; `/implement` fixes damage to walk lives 3 -> 2 -> 1 -> 0 and `/compare` enables band-clamped vertical movement. Both scene-data copies migrated to the three-field game schema (prose stays v4.4.0 until Phase 6). New 29-test engine suite replaces the 1,094-line Asteroids suite; full guide suite 190 passed, 1 skipped; detector clean on Training both themes. Guide at 284,278 bytes. Three engine defects found and fixed during stabilization (boot-order crash, a fixture that could not demonstrate fixed damage, and reset creating an unstartable game). Next: Phase 6 writes the shooter teaching narrative and the integrated Training workspace.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.
