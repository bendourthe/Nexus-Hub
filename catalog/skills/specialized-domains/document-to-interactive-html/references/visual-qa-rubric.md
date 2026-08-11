# Visual-QA Rubric (per-segment grading)

The measurable pass criteria the Step 9 visual-QA loop grades each output segment against, assembled from Phases 1-4 plus baseline readability. It is the single source of truth the loop scores against, the fan-out template (`assets/visual-qa-workflow.js`) fans out over, and the deterministic scorer (`scripts/visual_qa_score.py`) checks.

Two kinds of check run against every segment:

- **STRUCTURAL** - deterministic, checkable from the rendered DOM, the computed CSS, or the markup by `scripts/visual_qa_score.py` (headless-optional). These certify the measurable metrics without a human eye.
- **AGENT-VISION** - a judgment the agent makes by reading a screenshot and comparing it to the SOURCE segment (crop of meaningful content, dead space, annotation placement vs the source, imagery relevance, contrast and legibility). These cannot be certified structurally.

The loop runs BOTH kinds when a headless browser and the agent's vision are available; without a browser it degrades to the STRUCTURAL subset with a one-line note (see the degradation contract below). It never hard-fails on a missing browser.

## Segmenting the page

A "segment" is one top-level content band or section: a slide section, a hero, a figure with its overlay, an image band, or a data section. Grade each segment independently against the applicable criteria, then roll the findings up to the page-level pass bar. Per-segment grading is deliberate: a single whole-page pass misses per-segment defects (a ballooned image in one section, a dropped overlay in another), which is exactly how the four observed defects reached production.

## The eight criteria

Each criterion lists what it checks, the observable metric, the check kind, and the severity of a failure. Criteria 1-5 came from v3.15.4 Phases 1-4; criteria 6-7 grade the `references/responsive-typography.md` contract and criterion 8 the `references/svg-diagram-quality.md` contract, both added in v3.16.5.

1. **Full-width compliance** (Phase 1). When the resolved aspect is full-width, the widest top-level content band's rendered width is at least ~95% of a 1920px viewport (after the defined gutters), and NO global zoom, `transform: scale()`, or `zoom` is used to simulate width. Metric: band width / viewport at or above 0.95. Kind: STRUCTURAL. Severity: HIGH (a full-width run that renders a narrow centered column is the Phase 1 defect). N/A when the resolved aspect is not full-width.
2. **Image sizing** (Phase 2). No image breaks its prominence box: a hero's rendered height stays at or below ~80vh; a low-`page_fraction` secondary renders no wider than its section's hero (no balloon); no meaningful content is cropped (rendered aspect ratio matches the native ratio within ~2%); no image band carries dead space beyond ~30% of the band. Metrics: rendered box vs viewport, aspect-distortion ratio, whitespace fraction. Kind: STRUCTURAL for the caps (the `max-height` and `object-fit: contain` rules are present, the rendered box is within the cap); AGENT-VISION for "meaningful content cropped" and "dead space". Severity: HIGH for a hero filling the whole viewport or a cropped chart axis / labeled region / face; MEDIUM for dead space.
3. **Annotation fidelity** (Phase 3). For an annotated source figure, the built segment reproduces the source's regions and labels as a registered overlay over the base image, not a flat image beside a textual list. Metric: the overlay is present with a region element and a label per source annotation, and a view-original toggle; the placement is compared against the SOURCE figure. Kind: STRUCTURAL for overlay presence, region and label count, and the view-original toggle (from the DOM); AGENT-VISION for placement fidelity vs the source. Severity: HIGH (a dropped overlay demoted to side text is the Phase 3 defect). A LOW-confidence figure that CORRECTLY degraded to the enhanced-original viewer plus a textual complement is a PASS on this criterion, never a fail (the confidence gate did its job).
4. **Imagery integration** (Phase 4). A consented `stock` / `mix` run integrated at least one relevant, license-verified asset into each image-starved section OR recorded a per-section reason. Metric: per starved section, an embedded `data:` image is present OR a recorded reason exists; a consented stock / mix run with zero integrated assets and no recorded reason FAILS. Kind: STRUCTURAL for embedded-asset presence and count (given the run's consent and its starved-section expectation); AGENT-VISION for relevance. Severity: HIGH for silent zero-integration; MEDIUM for a loosely-relevant asset. N/A for a procedural, non-consented, or non-interactive run (those stay on Tier 1 by design).
5. **Readability and layout integrity** (at 100% zoom). No horizontal page overflow; text is legible (contrast within the `[[hallmark-design]]` accessibility gate, no overlap or clipping); every chart draws; no table overflows its container; the page is well-formed and opens offline. Metrics: no element wider than the viewport at 100%; contrast within the gate; no broken chart or overflowing table. Kind: STRUCTURAL for horizontal overflow, offline-cleanliness, and well-formedness; AGENT-VISION for contrast, legibility, and broken renders. Severity: HIGH for a broken render, unreadable text, or horizontal overflow.

6. **Fluid layout** (`references/responsive-typography.md` rules 1-3). Macro spacing is viewport-proportional and wrapping serves the viewport rather than a fixed column. Metrics: no band / grid container declares a fixed `padding` / `gap` at or above 24px (STRUCTURAL, `fluid-spacing`); and in the 1920px screenshot, **no text block sits beside empty space wider than roughly a third of its own band** without either widening toward its maximum measure or the band reflowing to multi-column (AGENT-VISION). The named failure to look for: "prose stranded beside dead space" - a measure-capped paragraph in a wide track with a dead corridor down one side, which reads as broken even though the paragraph obeys the measure. Kind: STRUCTURAL for the spacing declarations; AGENT-VISION for the stranded-prose judgment. Severity: HIGH for stranded prose or more than two fixed macro dimensions; MEDIUM for one or two.
7. **Readability floors** (`references/responsive-typography.md` rules 4-6). Every rendered text size clears its role floor, emphasis tokens are distinguishable, and contrast clears AA. Metrics: font sizes at or above 16px (body prose) / 13px (secondary) / 12px (interactive) at BOTH the clamp minimum and 1920px (STRUCTURAL, `font-floor`); inline tokens declare a color AND a family / weight change on the unqualified base rule (STRUCTURAL, `emphasis-token`); declared ink / background pairs clear 4.5:1 (STRUCTURAL, `contrast`). The AGENT-VISION half asks two questions of the screenshot that no parser can answer: **is the secondary text readable at 100% zoom on a 27-inch display** (margin notes, captions, footer link lists, credits - not squinted at, read), and **are emphasis tokens discernible at a glance** (can you find every command name in a paragraph without hunting)? Kind: STRUCTURAL for the three deterministic checks; AGENT-VISION for the two glance judgments plus status-badge contrast (excluded from the automated set because its floor depends on rendered size). Severity: HIGH for any floor violation, indistinguishable tokens, or a foreground unusable on every background; MEDIUM for a single failing foreground / background combination.

8. **Diagram integrity** (`references/svg-diagram-quality.md`). An authored inline SVG reads as intended artwork rather than as fragments. Metrics: no hand-placed triangle arrowhead path exists outside a `<marker>` and arrowheads are applied consistently across a diagram's connectors (STRUCTURAL, `svg-arrowhead`); every `<svg>` in a `position: sticky` / `fixed` container carries a `max-height` (STRUCTURAL, `svg-viewport-fit`); every marker reference resolves and every defined marker is used (STRUCTURAL, `svg-marker-integrity`). The AGENT-VISION half is what a parser cannot judge: **every arrow reads as ONE object** (line and head visibly attached, pointing along the line's tangent), **the whole diagram is visible in one sticky viewport** with no node below the fold, and **no label collides with a line** (a dashed path crossing text fragments both). Kind: STRUCTURAL for the three checks; AGENT-VISION for the three glance judgments plus SVG label legibility, whose effective size is `declared_size * (rendered_width / viewBox_width)` and is held to the same 13px secondary floor. Severity: HIGH for a detached arrowhead, an unconstrained pinned graphic, or a dangling marker reference (no head renders at all); MEDIUM for inconsistently applied heads or a defined-but-unused marker. N/A when the page carries no inline SVG.

## Per-segment score schema

Each segment yields one entry per applicable criterion:

```json
{
  "segment": "<id or heading>",
  "criterion": "full-width | image-sizing | annotation-fidelity | imagery-integration | readability-layout | fluid-spacing | font-floor | emphasis-token | contrast | svg-arrowhead | svg-viewport-fit | svg-marker-integrity",
  "status": "pass | fail | n/a",
  "severity": "high | medium | low",
  "kind": "structural | agent-vision",
  "evidence": "<measured value, DOM observation, or screenshot note>"
}
```

`severity` is present only when `status` is `fail`. `evidence` records the concrete basis: a measured fraction (`band 0.61 of viewport`), a DOM observation (`fig-annotated has 0 regions`), or a screenshot note (`chart axis cropped on the right`).

## Page-level pass bar (binary)

The page PASSES when there is NO open finding with `severity: high`. A `medium` or `low` finding is recorded and surfaced for the fix pass (the loop tries to clear it within the iteration cap) but does not by itself block. A criterion that is `n/a` for the run does not count against the page (full-width when the aspect is not full; imagery-integration for a procedural run; annotation-fidelity when there is no annotated figure). A LOW-confidence annotated figure that shipped the enhanced-original plus textual complement is a PASS on annotation-fidelity.

## The degradation contract (structural vs agent-vision)

The rendered path is the DEFAULT (v3.16.5). Degradation is a disclosed exception, reached only after the provisioning offer, never a silent fallback.

- **Step 0 - probe, then offer.** Run `scripts/ensure_render_env.py` BEFORE grading. It exits with a distinct code per state and prints the exact one-time provisioning commands. If the state is not ready, offer the install ONCE, up front. A browser is usually one consented command away, and skipping straight to the structural subset is how this repo shipped a stranded paragraph, an 11px footer, and a diagram in pieces from runs that believed they had passed.
- **Headless browser AND agent vision** (the default): grade both kinds. Capture 1920x1080, 1366x768, and 390x844 plus the interaction states, measure bands and boxes, AND compare each segment's screenshot to its SOURCE figure / section.
- **Headless browser, no vision step**: grade the STRUCTURAL kind from the rendered DOM and computed CSS.
- **No headless browser** (only after the offer was declined or failed): degrade to the STRUCTURAL kind via the markup / computed-CSS heuristic (`scripts/visual_qa_score.py`, structural mode) and state the degradation in one line in the final report. NEVER hard-fail on a missing browser.

Why the 1366x768 capture is not optional: a `clamp()` is usually still pinned at its MINIMUM at that width, so the readability floors bite there and not at 1920px. Grading only the wide viewport passes type that resolves correctly on a monitor and is unreadable on the laptop most readers use.

When only the structural subset ran, label the page-level verdict "structural-only" so the reader knows the AGENT-VISION criteria (crop of meaningful content, dead space, annotation placement vs source, imagery relevance, contrast and legibility) were not graded. A structural-only pass is a weaker but valid gate, recorded as such.

## Related

- `references/interactive-features.md` - the Phase 1 full-width contract, the Phase 2 image-box rules, and the Phase 4 imagery detection + integration gate whose metrics this rubric grades.
- `references/svg-diagram-quality.md` - the authored-SVG integrity contract criterion 8 grades: marker-based arrowheads, dash patterns clear of labels, connectors on node edges, viewport-fit for pinned graphics, and the numeric geometry self-check.
- `references/responsive-typography.md` - the fluid-layout and readability contract criteria 6-7 grade: macro-spacing fluidity, viewport-serving wrapping, the tokenized type scale, the rendered-size floors, the two-axis emphasis-token rule, and the validated contrast floors.
- `references/figure-reconstruction.md` - the Phase 3 annotated-figure overlay-recreation pattern and its confidence gate.
- `scripts/ensure_render_env.py` - the render-environment probe the loop runs FIRST, so a degraded environment is explicit and remediable rather than a silent fallback.
- `scripts/visual_qa_score.py` - the deterministic structural scorer that checks the STRUCTURAL subset headless-optional.
- `assets/visual-qa-workflow.js` - the Dynamic-Workflow template that fans the per-segment grading out (Dynamic Workflows when available, degrading to subagents then a single sequential pass).
