# v4.9.2 runtime-deck all-state text and SVG-box follow-up

This release-scoped record extends [MT-3](../../known-gaps.md) on the preserved LVEDP deck. It measures visible text against the rendered stage-height floor and tests SVG element boxes against the viewport at every declared fragment completion. It does not change the deck or qualify semantic build order, internal SVG paths, figure re-layout, or the legacy static-stage checks.

## Input and method

- **Nexus-Hub baseline**: `372a9e83` on `develop`; the isolated worktree passed the unchanged fast profile, 17/17, before this probe was added.
- **Immutable source**: `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html` from the local `algorithms` Git repository, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`. [The probe](probe.py) checks that digest before opening the blob.
- **Browser boundary**: Playwright Chromium blocks network routes, opens the deck through its real control, then uses the deck's ArrowRight navigation through all 15 slides. It samples the initial state and every declared fragment after the finite animation end time at four viewports. It requires exactly one active slide and zero internal overlay scroll at every sample.
- **Text rule**: every nonblank text node with a rendered range rectangle and effective ancestor opacity of at least 0.05 is measured using computed font size times ancestor transform/zoom for HTML, or `getScreenCTM()` scale for SVG. The floor is 2% of the rendered `#deck .dkcanvas` height, with the scorer's 0.1px comparison tolerance. The opacity boundary matches the project's invisible-after-animation detector. This follows the [stage-height correction](../runtime-deck-stage-floor-correction-2026-09-27/verification.md), not the invalidated viewport-height denominator.
- **Figure rule**: visible `.dkfig`, `.dkfill`, and `.dkflow` SVG element boxes must remain within the browser viewport. This checks outer boxes only; it does not inspect strokes, paths, semantic grouping, or whether the layout actually reflows rather than shrinking.

Run from the Nexus-Hub root on a host with Playwright Chromium and the cited local source repository:

```powershell
python docs/archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/probe.py C:\Users\BEDOURTHE\Documents\Supira\software\algorithms
```

## Observed result

The table records the first run after the opacity-boundary correction. Visible-element counts are sampled during timed fragment animations, so they are not a fixed deck inventory.

| Viewport | Slides | States | Visible text-node checks | Visible SVG-box checks | Floor / clipped-box failure states | Active-slide / wrong-slide / internal-scroll failures | External requests |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1366x768 | 15 | 88 | 2,147 | 114 | 0 / 0 | 0 / 0 / 0 | 0 |
| 1024x768 | 15 | 88 | 2,107 | 114 | 0 / 0 | 0 / 0 / 0 | 0 |
| 768x1024 | 15 | 88 | 2,153 | 116 | 0 / 0 | 0 / 0 / 0 | 0 |
| 390x844 | 15 | 88 | 2,177 | 117 | 0 / 0 | 0 / 0 / 0 | 0 |

Across four viewports, the recorded run checked 352 initial-or-fragment states, 8,584 text-node instances, and 461 visible SVG-box instances. Two fresh reruns of the same pinned blob and probe checked 8,569 / 458 and 8,527 / 456 instances respectively, each across the same 352 states. All three runs reported zero floor, outer-box, active-slide, wrong-slide, internal-scroll, and external-request failures; both negative controls were rejected in each run. The observed coverage range is therefore 8,527-8,584 text-node instances and 456-461 visible SVG-box instances, not one reproducible exact count. The unchanged source continued to show the separate fragment-budget failures on slides 2 and 6 in the [four-viewport build-state probe](../runtime-deck-four-viewport-build-state-2026-09-27/verification.md).

The first version of this probe navigated through Playwright dot-button clicks and falsely reported 61 off-screen SVG-box states at 390x844. Playwright scrolled the deck's `overflow:hidden` overlay horizontally by 55-62px to reach dot buttons; the stage and SVG boxes moved with it. The corrected ArrowRight run kept `#deck.scrollLeft` at zero in all 352 states and found no box overflow. The 61-state result is a rejected harness artifact, not a deck defect.

Local qualification on the final staged tree passed the 17-command fast profile, the 8-command docs group, 94 focused scorer/docs tests, and `git diff --cached --check`. These are local checks; hosted merge-result validation remains a separate publication gate.

## Remaining boundary

MT-3 stays open. The historical deck has no `.slide-stage` elements, so the three static slide checks remain `unchecked`. These measurements establish a stage-relative text floor and outer SVG containment at the sampled build completions, not semantic node-before-connector order, intermediate animation-frame quality, internal SVG stroke visibility, text overlap/contrast, or responsive figure re-layout. A preserved static-stage deck or an independently verified runtime path must cover those concerns with negative controls before the gap can close.
