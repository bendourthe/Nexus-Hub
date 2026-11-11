# Decision: The guide's Home shows the README animations as files beside the guide

Status: implemented - Home follows the README's order and shows the README's own workflow, settings, usage, continuity, and platforms animations from `guides/website/assets/`, with still posters under reduced motion. The guide's 500,000-byte ceiling is unchanged.

## Problem

The README presents Nexus Hub through short animations: the development workflow, the Settings panel, the usage monitors, a handoff between desktop apps, and the Cursor and Antigravity integrations. The interactive guide's Home covered none of the IDE features, and its other sections repeated one another: three sections explained hooks and skills, a 1,100-pixel static mockup showed a platform switch, and a command table sat beside a duplicate summary.

A first attempt embedded the Settings and usage tour as one live widget. The maintainer's review rejected it: a reader had to wait for one scene to finish, or press buttons, to see the next. The README's animations each play as the reader scrolls past them, and the guide should behave the same way.

## Decision

Home shows each README animation in its own section, in the README's order: Installation, The Development Workflow, Centralized IDE Settings, Usage Monitors, Handoffs, Platform Coverage, and a closing Why Nexus Hub.

- The animations are the README's own GIFs and still PNG posters, copied byte for byte into `guides/website/assets/` beside `ml-boat.webp`. A `<picture>` element shows the poster under `prefers-reduced-motion`; images load lazily as Home scrolls. No script drives them.
- A guide test fails when a copy differs from `assets/readme/`, so a README re-render and the guide copies move together.
- Redundant content leaves Home: the command strip that the workflow animation already shows, the static platform-switch mockup that the handoff animation replaces, the Skills, Hooks, and Governance cards, and the guardrail text columns. Why Nexus Hub keeps the guardrail figure and the five before-and-after rows. The built-in command comparison moves to the Cheatsheets page under Harness and Session Management.

## Alternatives considered

**A live tour rendering the shipped components in the page.** Sharp at any zoom and pausable, but the README's scenes are driven frame by frame by capture scripts, so independent per-section playback means re-implementing three choreographies in JavaScript. It also needed the byte ceiling raised to 600,000 bytes. Rejected in review because it required waiting or pressing buttons.

**Animated WebP instead of GIF.** Measured larger than the GIFs for these flat interface captures (for example 0.85 MB against 0.36 MB for the handoff), so the README's GIFs are used unchanged.

**Keep every existing Home illustration and only add the animations.** Leaves the repetition the review called out and makes Home longer. Rejected.

## Consequences

- Sharing the guide still means sending `nexus-hub-guide.html` and `training.html` with the `assets/` folder; that folder grows by about 3.6 MB. The portfolio copy needs the same files.
- The HTML falls to about 487,000 bytes, so the 500,000-byte ceiling from the 2026-10-04 decision stands.
- When the README animations are re-rendered, copy the new files into `guides/website/assets/` in the same change.
