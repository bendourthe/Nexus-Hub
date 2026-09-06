# Presentation Geometry - measured baseline and the v4.4.2 three-pane target

**Plan**: [v4.4.2-guide-production-ready-rebuild.md](../../plans/v4.4.2-guide-production-ready-rebuild.md), Phase 6, sub-task 6.1
**Measured**: 2026-09-02 on the v4.4.1 layout as merged (`46f18986`), in present mode on `#training/describe`, Chromium headless, device scale 1

## 1. What the v4.4.1 layout actually does

Region rectangles are `[left, top, width, height]` in CSS pixels. Coverage is the fraction of an 8 px grid over the viewport touched by any region.

| Viewport | Coverage | Stage height / viewport | Game column width | Where the terminal's tools and artifacts land |
|---|---:|---:|---:|---|
| 1280x720 | 0.81 | 0.10 | 213 px | tools at y 781, artifacts at y 856: BELOW a 720 px viewport |
| 1366x768 | 0.81 | 0.13 | 213 px | tools at y 808, artifacts at y 854: below the viewport |
| 1440x900 | 0.80 | 0.20 | 213 px | tools at y 885, artifacts at y 931: below the viewport |
| 1920x1080 | 0.68 | 0.26 | 214 px | slide capped at `max-width: 1600px`, 182 px of dead margin on each side |

Three faults, all structural rather than cosmetic. The `.nht-grid` two-column split gives the game a 5fr share of a 5fr + 7fr grid and the stage is then sized by height inside a column capped at 58 percent, so the arena is a narrow strip. The evidence column stacks terminal, tools, and artifacts with the terminal at a fixed six-line height, and the leftovers fall below the fold at every size. The 1600 px cap was inherited from the in-page layout and simply wastes a fullscreen 1920.

## 2. Target

At viewports at least 1024 px wide AND at least 640 px tall, the slide is a three-pane grid that fills the whole window:

```text
grid-template-columns: minmax(300px, 34fr) 33fr 33fr;
grid-template-rows:    auto minmax(0, 1fr) auto auto;   /* head, body, takeaway, controls */
max-width: none; height: 100%; padding: 6px 16px;
```

- `.nht-grid` becomes `display: contents` in present mode, so its two `.nht-col` children are placed directly in the slide grid: the game column in track 1, the evidence column (terminal, tools, artifacts) in track 2, and the explorer, which is a sibling of `.nht-grid`, in track 3. DOM order is unchanged, so every focus-order and Escape-precedence contract holds.
- Every pane's height is the body row's definite track. Inside the game pane the stage is `flex: 1 1 auto` with its 3:4 aspect ratio deriving the width from the available height; inside the evidence pane the terminal is `flex: 1 1 auto` and its output is the one permitted secondary scroll; the explorer stacks the tree above the file body and the body scrolls.
- Head, takeaway, and controls span all three tracks at their natural height, clamped to two lines as before.
- The Outline panel is `position: absolute` below the bar in present mode, so opening it moves nothing; it closes automatically if the viewport crosses the 1024 px breakpoint while open.
- Below 1024 px wide OR below 640 px tall, the whole slide reflows into ONE vertical scroll surface (the v4.4.1 narrow rules, now also keyed on height).

## 3. Acceptance numbers

- **Coverage floor: 0.88** of the viewport at 1280x720, 1366x768, 1440x900, and 1920x1080.
- **Stage-height floor: 0.45** of the viewport height at the same four sizes. The plan text named 0.70; that number is not reachable while the toolbar, progress strip, head, takeaway, and controls stay visible, which the Definition of Done also requires. Arithmetic at 720 px: 720 minus bar 49, progress 30, head about 60, takeaway 36, controls 38, and about 30 px of gaps leaves about 477 px for the body row; the game pane's own chrome (title bar, HUD, actions) takes about 114 px, leaving about 363 px of stage, which is 0.50 of the viewport. At 1080 the same sum leaves about 723 px, 0.67. A 0.70 floor would need 886 px of stage plus chrome at 1080 and is impossible even there. The floor is therefore recorded as 0.45 and the deviation is carried into the Phase 1 contract's deviations section.
- **No pairwise intersection** and **no horizontal overflow**, unchanged from v4.4.1.
- **Outline invariance**: every region rectangle is identical before and after opening Outline.

## 4. Measured after implementation

Same method, same routes, measured 2026-09-02 after sub-task 6.2.

| Viewport | Coverage | Stage height / viewport | Game pane width | Stage (w x h) |
|---|---:|---:|---:|---|
| 1280x720 | 0.93 | 0.47 | 415 px | 253 x 337 |
| 1366x768 | 0.93 | 0.50 | 444 px | 288 x 385 |
| 1440x900 | 0.93 | 0.53 | 469 px | 360 x 480 |
| 1920x1080 | 0.95 | 0.61 | 632 px | 495 x 660 |

Every region sits inside the viewport at all four sizes (the v4.4.1 layout pushed tools and artifacts below the fold at every one), no pairwise intersection exists, and opening Outline changes no region rectangle. At 1280x720 the first build reached 0.42 stage height; a `(max-height: 768px)` rule that clamps the head, intent, and takeaway to one line and tightens the arena chrome lifted it to 0.47. Proving tests: `test_desktop_presentation_fills_the_window`, `test_opening_outline_moves_no_region`, `test_short_window_reflows_like_a_narrow_one`, plus the unchanged v4.4.1 intersection, reflow, Escape-precedence, and route-change tests.
