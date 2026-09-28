# v4.9.2 runtime-deck chart-layout boundary

This release-scoped record narrows [MT-3](../../../../../releases/v4/v4.9/known-gaps.md) on the pinned LVEDP handbook. It checks whether model-backed slide charts are simply scaled SVGs and establishes what cannot be inferred about source-to-slide re-layout. It does not change the historical deck or close MT-3.

## Input and method

- **Immutable source**: `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html` from the local `algorithms` Git repository, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`. [The probe](figure-layout-probe.py) checks this digest before rendering.
- **Browser boundary**: Playwright Chromium opens the real deck control, activates all 15 slides without Playwright-induced overlay scrolling, blocks network requests, and inspects every `.dkfig[data-fig]` at 1366x768, 1024x768, 768x1024, and 390x844.
- **Measured structure**: each slide figure must resolve a `SupiraFigModel`, produce a chart SVG and plot rectangle, and report the authored chart text size and SVG screen scale after dividing out the presentation stage scale. A CSS `scale(0.5)` mutation on the slide-2 SVG must lower the measured figure scale. The probe requires 14 chart instances, zero missing models, zero external requests, 21-unit authored chart text, no extra SVG scale beyond the stage within 0.02, and rejection of the half-scale control at each viewport.

Run from the Nexus-Hub root on a host with Playwright Chromium and the cited local source repository:

```powershell
python docs/archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/figure-layout-probe.py C:\Users\BEDOURTHE\Documents\Supira\software\algorithms
```

## Observed result

| Viewport | Slides | Model-backed slide charts | Missing model/chart | Extra SVG scale beyond stage | Half-scale control | External requests |
|---|---:|---:|---:|---:|---|---:|
| 1366x768 | 15 | 14 | 0 | 1.00 on all 14 | Rejected at 0.50 | 0 |
| 1024x768 | 15 | 14 | 0 | 1.00 on all 14 | Rejected at 0.50 | 0 |
| 768x1024 | 15 | 14 | 0 | 1.00 on all 14 | Rejected at 0.50 | 0 |
| 390x844 | 15 | 14 | 0 | 1.00 on all 14 | Rejected at 0.50 | 0 |

### Functional exercise - model-backed chart layout

- **Revision**: pinned source commit `bab8523`, source SHA-256 above; probe SHA-256 `c39a07342ac2ebfcbe8f2fc220360a995fe3072ad14c84f66317f7b7f7f36649`.
- **Artifact and boundary**: the historical HTML opened through its real Presentation Mode control in Playwright Chromium; the probe invokes that control and each real deck dot handler through DOM clicks.
- **Command and input**: the PowerShell command above, the pinned source blob, and four browser viewports.
- **Expected contract**: 15 slides, 14 model-backed slide charts, 21-unit authored chart text, no extra figure scale beyond the stage, zero missing models or external requests, and an in-memory half-scale mutation detected at every viewport.
- **Exit code and observed state**: exit 0; all four rows above met the scoped contract, with the mutation measured at 0.50 of baseline. Navigation assertions found one active slide and zero deck-overlay scroll on every inspected slide.
- **Comparison and boundary**: the measured model-to-slide scale contract matches; full reading-figure-to-slide fidelity is NOT COVERED because no reading-page chart instance maps to these models. Internal painted strokes and the non-chart figures are NOT COVERED by this probe.
- **Environment and evidence**: local Playwright Chromium; this file and `figure-layout-probe.py` retain the command, predicates, and observed counts. `[[known-gaps-tracker]]` retains the unresolved scope as MT-3.

The deck constructs these charts from `FIGDATA` through `SupiraChart` with a holder-derived height and explicit 21-unit text and note sizes. Their plot rectangles are generated in the slide SVG's own coordinate system; the observed SVGs are not additionally scaled inside the stage. The identical design-unit results across viewports are expected because the presentation stage itself scales to fit those viewports.

The reading-page call site selects `figure.fig[id]`, but this pinned HTML has zero such elements in the rendered DOM. Its reading figures are separately authored `.drawn` SVGs, without a chart-instance ID mapping to these 14 slide models. The model's `panel.rect` values are data/export coordinates, not verified source figure box dimensions; one has a reversed coordinate span. Computing a source aspect from those values would create a false re-layout verdict. Consequently, this run proves the absence of an additional uniform SVG scale for the 14 generated slide charts, not that every reading figure was faithfully recomposed for a materially different slide box. The non-chart SVGs and internal painted strokes also remain outside this probe.

## Remaining boundary

MT-3 stays open. The historical deck still exceeds the eight-fragment budget on slides 2 and 6, has no `.slide-stage` sections for the three legacy static checks, and lacks a verified reading-figure-to-slide mapping for the full re-layout rule. A source figure ledger or a different preserved real deck is needed to compare panel rectangles, tick density, legend placement, and type against an actual source aspect. Internal SVG paint and other build semantics also remain unqualified.
