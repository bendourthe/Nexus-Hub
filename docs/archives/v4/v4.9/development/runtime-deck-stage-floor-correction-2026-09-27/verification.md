# v4.9.2 runtime-deck stage-floor correction

This append-only correction to the [runtime render qualification](../runtime-deck-render-2026-09-27/verification.md) uses the same preserved LVEDP deck and the stage-height denominator required by [responsive typography section 4.1](../../../../../../catalog/skills/specialized-domains/document-to-interactive-html/references/responsive-typography.md). It corrects the prior floor verdict only; it does not certify visual quality or close [MT-3](../../../../../releases/v4/v4.9/known-gaps.md).

## Evidence

The unchanged input is Git blob `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html` in the local `rd-data-dev` repository, 773,172 bytes, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`. Chromium opened the real deck control with fullscreen rejected only for stable viewport measurement, blocked all network routes, and measured the rendered `#deck .dkcanvas` rectangle. The design canvas is 900 units tall and scales with `--k`; comparing rendered text with 2% of rendered canvas height is equivalent to dividing both values by `--k` and comparing against 18 design units. The earlier report instead compared rendered text with 2% of the whole viewport, which includes unused letterbox space and is not the section 4.1 rule for this deck.

| Viewport | Rendered stage height | Correct 2% floor | Prior text-node census minimum | Corrected sampled-state floor verdict |
|---|---:|---:|---:|---|
| 2560x1300 | 1232.64px | 24.65px | 26.02px | Pass |
| 1920x1080 | 1018.62px | 20.37px | 21.50px | Pass |
| 1366x768 | 711.36px | 14.23px | 15.02px | Pass |
| 390x844 | 219.33px | 4.39px | 4.63px | Pass |

The four minima and text-node counts are the original report's settled-state census, not a new all-state census. The corrected floors are fresh browser measurements of the same hashed blob. Every recorded minimum exceeds its corrected floor, even without the original 0.1px tolerance. At 390x844, a separate in-memory negative control changed the first slide's visible eyebrow from its computed 21px font to `10px !important`: its rendered size changed from 5.1177px (pass) to 2.437px (fail) against a 4.3866px stage floor. The source blob was not modified.

## Remaining boundary

The prior report's viewport-relative floor failures are invalid for this scaled stage; its slide-4 finding of more than four rendered text sizes is unaffected. One settled state per slide was sampled, so intermediate and late build states are still unqualified. The historical deck still has no static `.slide-stage` sections, and the legacy scorer's three static-stage checks remain `unchecked`. MT-3 still requires a preserved static-stage artifact or a separately verified runtime path with structure, build, figure-scaling, and state coverage plus negative controls.
