# Nexus-Hub Progress Dashboard

**Branch:** `feat/v4.4.3-guide-illustration-rebuild`
**Active work:** [v4.4.5 targeted visual refinement](releases/v4/v4.4/development/guide-visual-refinement/verification.md). The v4.4.6 content redesign is rejected and superseded. Preserve existing sections; Models has an explicitly authorized rebuild.
**Last refreshed:** 2026-09-05

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

- [ ] Implement the queued [v4.9.0 master interactive-handbooks plan](releases/v4/v4.9/plans/v4.9.0-interactive-handbooks-and-presentation-default.md). All source analyses and approved-build lessons, including final fullscreen, motion sequencing, headerless layout, PowerPoint export and standalone sharing, are consolidated into R01-R30, conflict resolutions and 31 mapped tasks. Implementation remains 0/7 phases and 0/31 tasks; earlier isolated command/skill drafts require reconciliation before adoption. The active guide work remains unchanged.

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.4.5 baseline guide/test files restored | 59 | 59 | 0 |
| Exact production-file restorations | 3 | 3 | 0 |
| v4.4.1 guide-visual-and-arcade-rebuild phases complete | 7 | 7 | 0 |
| v4.4.2 guide-production-ready-rebuild phases complete | 8 | 8 | 0 |
| v4.4.2 local phase commits | 8 | 8 | 0 |
| Prior v4.4.2 release blockers (historical) | 0 | 0 | 0 |
| Restored views with page errors or horizontal overflow | 0 | 0 | 0 |
| Catalog skills | 329 | 329 | 0 |
| Canonical guide bytes (strict ceiling 500,000) | 497,896 | < 500,000 | met |
| Platform marks approved with staged hashes | 5 | 5 | 0 |

---

## Current work - v4.4.5 visual refinement

- [x] Compact all Models demos, enrich the animated networks, add perspective room navigation and a new game redesign, sweep provider-labeled capability tiers, and compare four reasoning allowances simultaneously; 154 focused guide checks, 24 final Models tests and 40 layout cases pass, with one optional portfolio check skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-compact-comparisons/verification.md).

- [x] Refine Models with training icons and reinforcement learning, a simpler language response, faster photographic diffusion, consistent room framing, voice-plus-UI multimodal input and four distinct architecture illustrations; 153 focused tests and 40 layout cases pass, with one optional portfolio check skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-photographic-examples/verification.md).

- [x] Refine Models with a common prompt/network/output flow, continuous token prediction, furnished-room camera sequence, native multimodal example, provider-labeled capability graphics and reasoning loops; 152 affected checks and 40 layout cases pass after the final source-label retest. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-flow-refinement/verification.md).

- [x] Rebuild Models with four visual demonstrations, capability/effort controls, and finite accessible animations; 150 affected tests pass with one optional skip, 20 final Models tests pass, and 40 layout cases pass. The default section is 29% shorter with 45% fewer visible words. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/verification.md).

- [x] Move the concise shared-plan explanation into the center handoff callout and remove the bottom repetition; 34 focused tests and 12 layout/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/centered-handoff-explanation/verification.md).

- [x] Rename the example plan, emphasize Example:, and add a prominent handoff callout with a fixed centered clock; 34 focused tests and 12 responsive/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/handoff-callout/verification.md).

- [x] Add the phase/model/effort plan table and show the same Phase 1 checklist from interruption through Codex completion; 52 focused checks plus the updated word-budget rerun and 12 layout/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/phase-one-handoff/verification.md).

- [x] Replace the Model network with a colored clustered illustration and show six guardrail pills; 59 focused tests and 12 responsive/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/clustered-model-and-guardrails/verification.md).

- [x] Restore the exact v4.4.5 guide, Training data, README, and related tests.
- [x] Verify baseline file parity and inspect restored desktop/mobile pages.
- [x] Complete the guide-specific regression suite: 340 passed, one optional skip; four inherited warnings.
- [x] Refine the token illustration and harness animation while preserving all 27 sections and 1,150 text fragments.
- [x] Stop idle Training frame scheduling: Foundations samples fell from 61 callbacks per second to zero.
- [x] Verify both themes and responsive layouts; complete the guide suite: 342 passed, one optional skip.
- [x] Rebuild the screenshot-selected Home safety and platform diagrams, enlarge their text, and keep all original content.
- [x] Verify the Home refinements across nine widths and both themes; all 49 final focused regression checks pass. See [evidence](releases/v4/v4.4/development/guide-visual-refinement/screenshot-segments/plan.md).

- [x] Align the safety figure, center the platform source text, remove connector dots, and repair line joins; 45 focused tests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/alignment-correction/verification.md).

- [x] Match all Foundations section headings to Home and align the token and context box pairs; 59 affected tests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/foundations-alignment/verification.md).

- [x] Remove the Home and Foundations Next sections and replace the safety shield with the transparent floating Nexus Hub logo; 56 focused tests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/logo-and-page-endings/verification.md).

- [x] Standardize prompt labels, merge selected attachments into the context prompt, and match the Best Practices heading; 143 tests pass and one is skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/prompt-composer/verification.md).

- [x] Illustrate the Claude Code usage-limit interruption and Codex continuation of the same Nexus Hub plan; 40 verification checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/session-handoff/verification.md).

- [x] Add the checkout repair example with image/PDF attachment previews and an expandable asset-folder explorer; 36 preview checks, 128 focused tests, and 32 final retests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/context-previews/verification.md).

- [x] Make the Home guardrails and platform handoff accessible to non-developers with platform logos, plain-language safety examples, and an appointment-booking plan; 169 focused tests and 28 layout checks pass, with one test skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/accessible-home-examples/verification.md).

- [x] Move checkout attachments above the prompt, render the image as PNG, add matching Request/Attachments/Goal/Context highlights, and rename Query to Request; 144 focused tests, 12 layout/color cases, and 36 keyboard preview checks pass, with one test skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/prompt-categories/verification.md).

- [x] Widen the safety Model box, add a neural-network illustration, and shorten guardrails into highlighted pills; 59 focused tests and 12 layout checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/model-and-guardrail-pills/verification.md).

- [x] Keep prompt text plain until its matching box activates, slow both annotation sequences, and compact attachment thumbnails beside their labels; 145 focused tests, 12 layout checks, four timing cases, and 36 preview interactions pass, with one test skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/prompt-animation-and-attachments/verification.md).

- [ ] Fix the pre-existing two-pixel internal overflow in Agentic Platforms at 320 pixels, reproduced before and after the context-preview change. See [baseline evidence](releases/v4/v4.4/development/guide-visual-refinement/context-previews/baseline-overflow.json).

- [ ] Improve the pre-existing Home guardrail pill contrast in light mode (4.462:1 against a 4.5:1 target). See [baseline evidence](releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/baseline-sweep.json).

- [ ] Reconcile five pre-existing guide assertions for the approved prompt labels/highlights, Home session dialogue, and the cx-png marker. All failures reproduce before the Models rebuild; see [verification](releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/verification.md).

## Plan - v4.4.6 Guide Learning Experience [SUPERSEDED BY USER]

- [x] Review current Home, Foundations, Training, and the two supplied source documents; retain current browser evidence.
- [x] Write the seven-phase implementation plan with continuous visual and performance gates.
- [x] Phase 1 - Baseline and teaching/design contract.
- [x] Phase 2 - Shared layout and motion repair.
- [x] Phase 3 - Home refinement.
- [x] Phase 4 - Foundations: model, tokens, prompt, context.
- [x] Phase 5 - Foundations: harness, loop, graph.
- [x] Phase 6 - Training clarity and state integrity.
- [ ] Phase 7 - Final verification, known gaps, CI/CD, and approval-gated integration.

Historical implementation record only: the user rejected this content/structure rewrite. v4.4.5 has been restored, and the plan above must not resume. Prior test and performance results describe the rejected artifact, not the restored guide.

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
