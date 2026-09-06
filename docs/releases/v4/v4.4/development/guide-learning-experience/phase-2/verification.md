# Phase 2 verification

Status: shared layout and motion repair complete locally. Source SHA-256: `148089232b9dfeac8af90a932c2e6af5c54914cb3c063d29111a4b2195dba3a4`; 404,762 bytes. Model: current frontier session; max-effort recommendation retained.

## Changed behavior and root cause

Essential sequence nodes and connectors are visible before animation. Replay is finite; pause, offscreen observation, document visibility, and live reduced-motion changes cancel pending work. CSS now owns heading wrapping and body reading measure. All reading pages are available without JavaScript. Focused buttons own their arrow keys.

The idle-frame regression identified a concrete lag source: the Training game unconditionally scheduled the next frame and painted even while idle on Foundations. Instrumentation observed about 61 callbacks per second, with the recurring caller inside the game's frame function. Scheduling now belongs to the running lifecycle. Starting/resuming the active game schedules a frame; paused, hidden, idle, destroyed, or inactive states cancel it. The existing game rules are preserved.

## Tests

- New visibility and heading regressions: four failures reproduced on the baseline, then passed after the fix.
- Broad guide run: 331 passed, one optional skip, and six old motion expectations failed. Every failure was inspected and updated in the [assertion migration register](../assertion-migration.json), with no skips or expected failures added.
- Corrected motion/typography selection: 17 passed; final three autoplay/pulse corrections: 3 passed.
- Lifecycle suite: 11 passed, covering three reading widths, pause/replay, live reduced motion, no-JS, idle frames on all four routes, and running-game route exit/return.
- Deterministic game plus the earlier lifecycle selection: 41 passed. Damage, movement, pause, reset, and step behavior survived the scheduling change.
- The browser fixture was subsequently aligned with the repository's optional/required Playwright convention and rerun before commit.
- No aggregate result is inferred by adding overlapping suites. The final phase reruns the complete final-tree suite.

## Clean browser audit

Command: `python tests/guides/tools/learning_experience_audit.py --out docs/releases/v4/v4.4/development/guide-learning-experience/phase-2 --screenshots --performance`.

The [raw audit](audit.json) contains 72 cases, zero page overflow, zero JavaScript errors, zero external requests, and twelve timing samples including warmups. No other guide browser suite ran during these samples.

| Case | Median task duration | Median layouts | Median style recalculations | Worst p95 frame | Longest task | Maximum navigation feedback |
|---|---|---|---|---|---|---|
| Light, 1440px | 0.495s | 75 | 67 | 16.7ms | 0ms | 43.1ms |
| Dark, 1440px | 1.091s | 75 | 64 | 16.8ms | 0ms | 39.7ms |
| Light, 420px | 0.727s | 75 | 64 | 16.8ms | 0ms | 47.4ms |

The baseline had roughly 611-785 layouts and 2,313-2,487 style recalculations. This is evidence of substantially less repeated layout work; the early baseline's overlapping suite remains a timing confound. Final paired quiet runs will use the saved baseline through the audit's new --guide option. Resize, throttling, and completed Training-state measurements belong to final stabilization.

## Visual review

All sixteen top viewport captures were inspected: Home, Foundations, Training, and Cheatsheets at 1440x900 and 420x900 in both themes. Shared headings, reading measures, navigation, and surfaces are consistent and bounded. Full-page captures are retained as overviews, not substituted for legibility inspection. The geometry matrix also includes 320, 719, 720, 721, 768, 1024, and 1920px.

Considered but rejected as a new regression: the pale light-theme game at rest comes from its unchanged start-overlay color mixing, not the idle scheduler; Phase 6 will refine it. Existing long Foundations compositions, model GIF, oversized inner tags, and old Home claims remain the explicitly scheduled scene replacements in Phases 3-5. This checkpoint does not claim the final learning design is complete.

## Plan delta

Incomplete initial diagnosis: the hidden game loop, rather than just the scene observers, was responsible for continuous JavaScript frames. The smallest fix extended the Phase 2 motion scope into game scheduling, with the full deterministic game suite and route-resume regression. No game rules were rewritten. Added no-JS reading navigation after a new boundary test found that only Home was visible without scripting.

## Closeout

CI impact: no pipeline edits; the existing guide-render job owns the changed tests. No new runtime dependency. The browser audit remains a development tool. README, progress tracker, and the v4.4.6 known-gap subsection record the behavior; BG-39 and BG-40 are resolved. Gitignore and documentation placement require no change. One local phase commit; no push, PR, or remote CI.
