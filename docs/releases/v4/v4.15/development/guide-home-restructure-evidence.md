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

## Second Pass

The maintainer reviewed the published Home and set a new order, noting that the hero already says what Nexus Hub is, and asked for a Why Nexus Hub that reads as a closing argument.

- Home order: hero, Installation, Platform Coverage, The Development Workflow, Centralized IDE Settings, Handoffs, Usage Monitors, Why Nexus Hub.
- Why Nexus Hub is now a six-card benefits summary (Every Platform, Expert Skills, Repeatable Workflow, Enforced Guardrails, One Settings Panel, Continuity). Each card states the benefit and, under a "Without" label, the problem it removes. The cards reveal in reading order on scroll, and a closing statement ends with two buttons: Install Nexus Hub (back to Installation) and Start the Training.
- Removed: the guardrail ring figure, the five before-and-after rows, and their CSS. The ring explanation remains in Foundations.
- Guide size (LF): 479,925 bytes, under the 500,000-byte ceiling.

Verification:

- Chromium at 1440 (dark) and 390 (light) pixels: the new order, no horizontal scroll, no page errors, and the Install button returns to Installation.
- New tests in `tests/guides/test_v415_home_animations.py`: the six cards in order with their call to action, and the scroll reveal plus the Install button under both motion settings.
- Retired with the figure: `test_v443_phase2_guardrails.py` and the comparison-row tests. Retargeted: the Home order lists, the type-role check for the migration-table headers, the contrast tool's labels, and the guardrail-claim test, which now reads the Enforced Guardrails card.
- Full guide suite: 986 passed, 2 skipped, 1 failed. The failure was an R44 assertion that `id="nhg-why"` must not appear anywhere on Home; that id then named the removed Raw Prompting Limits cards above Installation. The check now covers the hero only, and its file passes (27 tests).

## Release Inclusion

Include with the settings branch work in v4.15.0. The portfolio copy (`online-portfolio/nexus-hub`) needs the guide, `training.html`, and the new `assets/` files, and is refreshed only after the maintainer's review.
