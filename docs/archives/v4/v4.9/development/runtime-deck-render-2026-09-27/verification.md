# v4.9.2 real runtime-deck render qualification

**Correction, 2026-09-27:** The floor comparison below used viewport height where the deck's scaled canvas requires stage height. The [append-only correction](../runtime-deck-stage-floor-correction-2026-09-27/verification.md) shows that all four sampled-state minima pass the correct 2%-of-stage floor. The original observations and method remain below as historical evidence; their viewport-floor failure verdicts must not be used as current stage-floor findings.

This read-only follow-up measures the preserved LVEDP presentation as a runtime deck. It adds rendered evidence to [MT-3](../../known-gaps.md) but does not close the gap or certify the deck as visually acceptable.

## Artifact and method

The input was the unchanged Git blob `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html` in the local `rd-data-dev` repository: 773,172 bytes, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`. No file in that repository was edited. Chromium loaded the blob with `page.set_content`; all network routes were blocked, and the run observed zero external requests. The real `[data-deck-open]` control opened the deck, then `ArrowRight` visited the 15 `.dkslide.on` articles with contiguous `data-slide` values 1 through 15. Exactly one slide was active and none was empty at every tested viewport.

The first measurement reused `measure_handbook.py`'s `MEASURE` probe, but that probe selects named elements and omitted visible `span`, `tspan`, and `i` text in this older deck. The authoritative second pass walked every nonblank visible text node in the active slide, required a rendered range rectangle, and applied the same effective-font formula: computed font size times ancestor transform and zoom for HTML, or `getScreenCTM()` scale for SVG. It used the tool's 0.1px comparison tolerance and 2% of viewport height as the slide-stage floor. Each slide was sampled once after a 650ms settle; intermediate build states were not measured.

| Viewport | Floor | Visible text nodes | Rendered stage-floor result | Other structural observation |
|---|---:|---:|---|---|
| 2560x1300 | 26.00px | 290 | No sampled node below floor; minimum 26.02px | Slide 4 exceeds four rendered sizes. |
| 1920x1080 | 21.60px | 290 | No sampled node below floor with 0.1px tolerance; minimum 21.50px | Slide 4 exceeds four rendered sizes. |
| 1366x768 | 15.36px | 289 | Slides 4 and 6 each have four nodes below floor; minimum 15.02px | Slide 4 exceeds four rendered sizes. |
| 390x844 | 16.88px | 294 | All 15 slides have nodes below floor; minimum 4.63px | Slide 4 exceeds four rendered sizes. |

The original blob still produces `presentation-declared: fail`, `nav: scroll`, and `page_pass: false` in `visual_qa_score.py`. An in-memory declaration-only copy, SHA-256 `4813af3bf0ffd6c01bbd67474438df922fc01fb7bd2dfdd9150b16fb3a0605c2`, produces `slide-structure: fail` and `unchecked` for `slide-fragments`, `slide-type-variety`, and `slide-figure-scaled`, because it has zero `.slide-stage` elements. These are the same fail-closed outcomes as the earlier [structural follow-up](../empty-slide-stage-coverage-2026-09-27/verification.md); this pass adds real rendered slide observations, not static-stage coverage.

## Boundary and next action

This is one settled-state runtime inspection, not a reusable runtime-deck scorer, a full animation-state census, or a visual-quality pass. The observed floor and size-variety failures belong to the historical pre-rule deck and were not repaired here. MT-3 remains open until a preserved real `.slide-stage` artifact exercises the legacy checks, or a separately verified runtime path checks the corresponding structure, builds, figure scaling, and every relevant rendered state with negative controls. The runtime path must retain distinct results rather than presenting the legacy scorer's `unchecked` checks as passes.
