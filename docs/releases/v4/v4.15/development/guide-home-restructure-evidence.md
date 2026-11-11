# Guide Home Restructure Evidence

This record covers the 2026-11-10 restructure of the interactive guide's Home page (`guides/website/nexus-hub-guide.html`) after the maintainer's review: Home now follows the README and shows the README's own animations. The design is recorded in `docs/decisions/implemented/architecture/2026-11-10-guide-home-shows-readme-animations.md`.

## Changes

- Home order: hero, Installation, The Development Workflow, Centralized IDE Settings, Usage Monitors, Handoffs, Platform Coverage, Why Nexus Hub.
- The README's workflow, settings, usage, continuity, and platforms GIFs and still PNG posters are byte-identical copies in `guides/website/assets/`. Each sits in its own section, loads lazily, and shows its poster under reduced motion through a `<picture>` source. No script drives them.
- Removed as repetition: the workflow command strip (the workflow animation shows the same six steps), the static platform-switch mockup (the handoff animation replaces it), the Skills, Hooks, and Governance cards, the guardrail text columns, the definitions block, and their 49 orphaned CSS rules. Why Nexus Hub keeps the guardrail figure and the five before-and-after rows.
- The built-in command comparison moved to Cheatsheets, at the end of Harness and Session Management.
- The installer terminal keeps a 350-pixel output frame with a thin dark scrollbar and scrolls to the newest line; the version step lists each command once with its description.

## Size

| Item | Value |
|---|---:|
| Guide before (LF) | 499,794 bytes |
| Guide after (LF) | 487,073 bytes |
| Added assets (5 GIFs, 5 PNGs) | about 3.6 MB |
| Home words below the hero | about 1,560 before, about 570 after |

The 500,000-byte ceiling is unchanged.

## Verification

- Chromium at 1440 and 390 pixels: every animation loads, no horizontal scroll, and no console errors. Captures reviewed for each section, the moved table, and phone width.
- `tests/guides/test_v415_home_animations.py` (9 tests): byte-identical copies and posters, the Home order, the moved table, still posters under reduced motion, and the installer frame. All pass.
- Full guide suite (excluding the game-engine shards) before test maintenance: 630 passed, 31 failed. Every failure asserted removed content or used it as a fixture. Retired: the workflow-pill, loop-strip, mid-task-strip, and definitions tests. Retargeted: the sequencer engine tests to the Foundations prompt annotation, the comparison table tests to Cheatsheets, the Training order test to the README workflow table, and the Home order, section titles, and word ceilings to the new structure. The changed files then ran 219 tests with 4 failures, which were fixed (a dropped import and the annotation's two elements per step), and those tests pass.

## Release Inclusion

Include with the settings branch work in v4.15.0. The portfolio copy (`online-portfolio/nexus-hub`) needs the guide, `training.html`, and the new `assets/` files, and is refreshed only after the maintainer's review.
