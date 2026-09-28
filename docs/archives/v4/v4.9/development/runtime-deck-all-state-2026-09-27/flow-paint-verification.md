# v4.9.2 runtime-deck flow-connector paint qualification

This release-scoped record narrows [MT-3](../../../../../releases/v4/v4.9/known-gaps.md) on the pinned LVEDP deck. It checks settled connector-body paint in the three authored flow slides. It does not change the historical deck or close MT-3.

## Functional exercise

- **Revision and source**: `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html` from the local algorithms Git repository, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`. The [probe](flow-paint-probe.py), SHA-256 `4a28ba7b553de36be295642973c0846505ba01e83c5e8f0949068c24f2e662ec`, refuses a different source blob.
- **Boundary and input**: Playwright Chromium opened the real Presentation Mode control and navigated to slides 12, 14, and 15 through their dot handlers at 1366x768, 1024x768, 768x1024, and 390x844. The probe waited for the finite build, paused animations for each slide's screenshot comparison, and required one active slide with zero deck-overlay scroll. It blocked and counted external requests and page errors.
- **Expected contract**: Slides 12, 14, and 15 expose 6, 4, and 3 flow connectors. Each connector has computed opacity at least 0.95 and a stroke other than `none`; hiding it must change at least two pixels by 16 color levels within a 19x19-pixel window at its transformed midpoint. An in-memory control first makes one connector fully transparent, then requires hiding that already invisible connector to change zero pixels. Any offscreen midpoint, network request, or page error fails the run.
- **Command**: `python docs/archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/flow-paint-probe.py C:\Users\BEDOURTHE\Documents\Supira\software\algorithms`.
- **Observed result**: Exit 0. All 52 connector-viewport observations met the paint contract; each hiding operation changed 19-70 midpoint-window pixels, with maximum per-pixel color deltas of 50-141. All 12 invisible-stroke controls changed zero pixels. No midpoint was offscreen; external requests and page errors were zero.
- **Harness correction**: The first developmental run was rejected because its animation-pause rule persisted into later slides and CSS animation overrode a non-important inline opacity control. The retained probe removes the pause rule after each slide and uses an important opacity override for the control. Only the corrected, gated rerun supports the result above.
- **Environment and comparison**: Local Playwright Chromium on Windows with Pillow screenshot differences. This is direct rendered-pixel evidence for connector bodies at their midpoints in the settled states of three flow slides. It is not a human visual review, a complete SVG-path audit, or evidence for chart strokes, arrowheads, intermediate animation frames, or reading-figure-to-slide re-layout.

## Remaining boundary

MT-3 stays open. Slides 2 and 6 still exceed the eight-fragment budget, the historical deck still has no `.slide-stage` sections for the three static checks, and full figure re-layout lacks a verified reading-figure-to-slide mapping. Other internal SVG paint and whole-deck build semantics remain unqualified.
