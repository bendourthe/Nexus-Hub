# v4.9.2 runtime-deck chart-line paint qualification

This bounded follow-up narrows [MT-3](../../known-gaps.md) on the preserved LVEDP deck. It checks every settled SVG `path.c-line` in the 14 model-backed slide charts at four viewports. It does not change the deck or establish that every other chart mark paints correctly.

## Functional exercise

- **Pinned source**: `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html` in the local algorithms repository, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`. The [probe](chart-line-paint-probe.py), SHA-256 `79b06ad1613b87240244d719d658b1432f2bd8e7a60f6d122574ef8a9936f865`, refuses another blob.
- **Real boundary**: Playwright Chromium opened Presentation Mode through the deck control, selected all 15 slides through their dot handlers, and required one active slide and zero horizontal deck scroll at 1366x768, 1024x768, 768x1024, and 390x844. External requests were blocked and counted; page errors were counted.
- **Paint predicate**: after each slide's finite animation settled, the probe paused animations and inspected every `path.c-line` in each `.dkfig[data-fig]`. Each path needs nonzero length, computed opacity at least 0.95, a stroke other than `none`, and at least one rendered pixel inside its viewport-clipped bounding box that changes by 16 or more color levels when the path is hidden. The probe requires exactly 14 charts per viewport.
- **Negative controls**: for every path, making it fully transparent before hiding it must change zero pixels. On slide 2 at each viewport, forcing `stroke: none` must make the visible-style predicate reject the line.
- **Command**: `python docs/archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/chart-line-paint-probe.py C:\Users\BEDOURTHE\Documents\Supira\software\algorithms`.
- **Observed result**: exit 0. All 124 chart-line-viewport observations showed changed pixels, ranging from 42 to 41,849 within their path boxes; all 124 invisible-line controls changed zero pixels; all four null-stroke controls were rejected. The 14 charts contained 31 line paths per viewport, and every one was inspected. No external request or page error occurred.

## Remaining boundary

MT-3 stays open. The probe does not inspect axes, ticks, markers, fills, arrowheads, or animation frames. Slides 2 and 6 still exceed the eight-fragment budget; the deck has no `.slide-stage` sections for the three static checks; and no verified reading-figure-to-slide map supports a full figure re-layout claim. The result is direct settled-pixel evidence for every chart line, not a whole-figure visual qualification.
