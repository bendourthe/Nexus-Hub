# v4.9.2 runtime-deck build-state probe

This release-scoped evidence tests the preserved LVEDP handbook deck against the authored-fragment budget without changing its source repository. It extends the [runtime render](../runtime-deck-render-2026-09-27/verification.md) and [stage-floor correction](../runtime-deck-stage-floor-correction-2026-09-27/verification.md); it does not replace either record or close [MT-3](../../../../../releases/v4/v4.9/known-gaps.md).

## Input and method

- Immutable source: `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html` in the local `rd-data-dev` repository, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`.
- Reproducer: [probe.py](probe.py). It reads the Git blob, verifies its hash, blocks all network requests, uses the real deck-open control and navigation dots, then samples every declared fragment index after its finite browser animation end time at 1366x768 and 390x844.
- Structural rule: indices must be positive and contiguous, with no more than eight distinct authored fragments per slide. The in-memory negative control changes the first fragment on compliant slide 8 to index zero; the source blob is unchanged.
- State observations are deliberately limited to active-slide count and an opacity-and-box visibility proxy for fragment elements. The probe records figure SVG boxes but does not judge semantic order, ink fill, or whether a figure was re-laid out rather than uniformly scaled.

## Result

| Viewport | Slides reached | Timed states sampled | Fragment-budget failures | Active-slide failures | External requests | Zero-index control |
|---|---:|---:|---|---:|---:|---|
| 1366x768 | 15 | 73 | Slides 2 and 6 | 0 | 0 | Rejected |
| 390x844 | 15 | 73 | Slides 2 and 6 | 0 | 0 | Rejected |

Slide 2 declares indices 1 through 9 and its last sampled completion is 3,900 ms; slide 6 declares indices 1 through 16 and its last sampled completion is 6,700 ms. Both exceed the eight-fragment budget. The long slide-6 schedule is produced by its figure renderer, so the separate CSS delay rules for table and flow fragments are not evidence that its later chart fragments appear immediately.

## Remaining boundary

This is a real-artifact non-pass, not a scorer regression. The historical deck exposes `.dkslide` rather than `.slide-stage`, so the three static slide checks still report `unchecked`. The opacity-and-box proxy does not reliably classify SVG strokes, so its `visibleIndices` output is diagnostic only and is not a finding about hidden chart content. Two viewports and these completion samples do not establish the four-viewport rendered-type floor, semantic fragment dependencies, figure re-layout, or every intermediate visual state. MT-3 stays open until a preserved compliant static-stage artifact is available or a separately qualified runtime path covers those concerns with negative controls. No distributed scorer behavior changed in this follow-up.
