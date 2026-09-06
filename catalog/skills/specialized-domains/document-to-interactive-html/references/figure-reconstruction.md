# Figure Reconstruction Protocol

The LLM-native method for turning static figure images into faithful interactive reconstructions - or honest fallbacks - without ever inventing data. This protocol runs whenever the content model contains `image` blocks (see `content-model.md` for the schema-v2 fields it reads and writes). It is the truthfulness core of the skill: every number shown in a reconstructed chart must be traceable to an auditable worksheet, and anything unreadable is presented as the original image, never as a fabricated chart.

The protocol has seven parts, run in order: classification, the read-the-figure worksheet, fidelity cross-checks, the confidence gate, map/diagram handling, the model round-trip, and the scanned-page transcription/verification pass.

## 1. Classification pass

Render and read EVERY `image` block in the content model (decode its `data_uri`; the agent views the image directly). Assign each a `classification` - one of:

| Classification | Meaning | Downstream handling |
|---|---|---|
| `chart` | A data-bearing plot: bar, line, pie, scatter, area, combo, gauge | Read-the-figure worksheet (part 2) |
| `map` | A geographic or spatial graphic, possibly annotated | Map/diagram rules (part 5) |
| `diagram` | Flowchart, org chart, architecture, timeline, process graphic | Map/diagram rules (part 5) |
| `table-image` | A table rendered as an image (no extractable cells) | Worksheet-style transcription (part 2, table variant) |
| `photo` | A photograph (people, places, products) | Render as original, lightbox-enabled |
| `screenshot` | A UI or document screenshot | Render as original, lightbox-enabled |
| `decorative` | Logos, dividers, background art with no content value | MAY be dropped, ONLY with a coverage skip entry |

Record the classification back into the model JSON (the block's `classification` field). Blocks with `origin: "scanned-page"` are NOT classified here - they take part 7. Use the block's `caption`, `page`, and surrounding section text as context, but classify from the pixels: a caption saying "Figure 3" does not make a photo a chart.

**Annotated figures (the `annotated` signal).** Beyond the base classification, a `map`, `diagram`, `photo`, or `screenshot` may carry AUTHOR-ADDED overlays: region rectangles or shaded zones, callout labels, leader lines, pins, or color-coded groupings drawn on top of a base image. Record this with an `annotated: true` signal alongside the base `classification` (for example, a specialist-coverage map is `classification: "map"` with `annotated: true`). An annotated figure routes to the OVERLAY-RECREATION path in part 5 (keep the base image, recreate the annotations as an interactive layer), NOT to a full SVG rebuild or a flat enhanced-original. When the extractor supplied structured annotation metadata (an `annotations` array on the image block, from PPTX overlay shapes with image-relative boxes, text, and colors; see `content-model.md`), that metadata is the ground truth for the overlay; for a flattened source (a PDF page image, or a PPTX whose annotations are baked into one picture) read the annotations from the rendered image directly, under the part-4 confidence gate.

Classification is complete when NO image block has an empty `classification` (scanned pages excepted). An unclassifiable image (corrupt, blank) is classified `decorative` with a skip reason stating why.

## 2. Read-the-figure worksheet (charts and table-images)

For every `chart`-classified image (and every `table-image`), fill the worksheet BEFORE building anything. The worksheet is the audit trail: it is written into the output HTML as a comment adjacent to the reconstructed chart, so every number in the reconstruction traces to a recorded reading.

Worksheet template (copy verbatim, fill every line; write "none" or "not shown" rather than leaving a line blank):

```text
FIGURE WORKSHEET - <source file> page/slide <n>, "<caption or alt>"
Chart family:        <bar | grouped bar | stacked bar | line | area | pie | doughnut | scatter | combo | table-image>
Title (as printed):  <...>
X axis:              <label and unit, or "categorical: <labels>">
Y axis:              <label and unit; min-max as printed; scale: linear | log>
Gridlines / ticks:   <tick values as printed, e.g. 0, 50, 100, 150>
Legend:              <series names and their visual encoding (color/pattern)>
Series readings:     <per series: each category/x value -> value estimate>
Estimated precision: <e.g. "read to the nearest 5 against gridlines">
Footnotes/source:    <any source line or footnote printed in the figure>
Anomalies:           <broken axis, dual axis, annotations, error bars, or "none">
```

Reading rules:

- Read values against gridlines and axis ticks; interpolate between ticks and STATE the precision ("nearest 5"). Never report more precision than the pixels support.
- When exact values are printed on the figure (data labels), use them verbatim and record precision as "printed values".
- A `table-image` uses the same template with `Series readings` replaced by a row-by-row cell transcription; illegible cells are written `<unreadable>`, never guessed.
- Read EVERY series and EVERY category. A worksheet that samples "representative" points is incomplete - if the figure is too dense to read fully, that is a confidence signal (part 4), not a license to subsample.

## 3. Fidelity cross-checks

Run these checks on every completed worksheet BEFORE accepting it. Any failure forces a re-read of the figure; a second failure downgrades confidence (part 4).

- **Endpoints and extrema**: the largest and smallest read values match the visually tallest/shortest bars or highest/lowest points.
- **Category count**: the number of readings per series equals the number of categories/x positions visible in the figure.
- **Sum checks**: pie/doughnut slices and 100%-stacked series sum to ~100% (within the stated precision); part-of-whole readings never exceed the whole.
- **Axis containment**: every read value lies within the printed axis range; nothing extrapolates past the axis.
- **Monotonic/order sanity**: rankings visible in the figure (A taller than B) hold in the readings.
- **Unit carry-through**: the axis unit and any multiplier ("in thousands") are recorded in the worksheet and carried into the chart block's `axis` object - a reconstruction that drops a "millions" multiplier is a fidelity failure even if the digits match.

## 4. Confidence gate

Assign each worksheet a confidence tier and act on it. The tier is recorded on the reconstructed block (`confidence`) and governs what the reader sees. Fabricating, smoothing, or "cleaning up" data to make a chart buildable is prohibited in ALL tiers.

- **`high`** - the figure is crisp, every tick and label is legible, all cross-checks pass, and readings are at printed or near-tick precision. Build the interactive reconstruction: a `chart` block with `provenance: "reconstructed-from-image"`, `confidence: "high"`, `source_image` set to the original image's data URI, the `axis` object filled (labels, min/max, unit), and the worksheet embedded as an adjacent HTML comment. The rendered chart carries a small provenance badge ("reconstructed from source figure") and a view-original toggle that swaps in the embedded original.
- **`medium`** - readable overall, but some values are interpolated between sparse gridlines or a label is partially obscured; cross-checks pass. Build the same reconstruction PLUS: a visible caption line stating that values are read from the figure to the stated precision, and the original image displayed by default alongside (not only behind the toggle).
- **`low`** - illegible ticks, too-dense series, ambiguous encoding, broken/dual axes that cannot be confidently separated, or repeated cross-check failures. Do NOT reconstruct. Present the original image in the enhanced viewer (pan/zoom lightbox, caption preserved, the highest-resolution render available - re-render the region at higher scale when the source was a `rasterized-region`), with one line stating why no reconstruction was built. No `chart` block is emitted; the image block's `classification` stays `chart` so coverage reconciliation can see the decision.

**Annotated-figure overlays follow the same tiers.**

- **`high` / `medium`** - every region boundary, label, and grouping is legible and placeable. Recreate the interactive overlay per part 5, with `provenance: "reconstructed-from-image"` (or a parallel `annotation-overlay` provenance), a `confidence` tier, `source_image` set to the base image for the view-original toggle, and a worksheet-style comment recording each annotation (each entry: region label, normalized bbox, group/color, and any leader target). At `medium`, add a caption line stating the annotations are placed from the source figure.
- **`low`** - ambiguous boundaries, unreadable labels, or freeform dense annotation. Do NOT fabricate an overlay: ship the enhanced-original viewer with one line stating why, plus the textual complement (part 5). A guessed region is as much a fidelity failure as a guessed data point; the no-fabrication and label-lossy-redraw prohibitions apply unchanged.

Tier decisions are per-figure, not per-document. When in doubt between two tiers, take the LOWER one - an honest image beats a doubtful chart.

## 5. Maps and diagrams (three decision paths)

A `map` or `diagram` (and any figure carrying an `annotated: true` signal from part 1) resolves to exactly ONE of three paths. Prefer the path that preserves the most of the source faithfully.

1. **Full SVG rebuild.** Rebuild the whole figure as interactive inline SVG ONLY when the rebuild preserves every label, region, node, edge, and relationship in the original: typically simple all-vector structures (a handful of labeled regions with markers, a small flowchart, a linear timeline). The SVG rebuild may add hover highlights, labeled tooltips, and pan/zoom, and it carries the same provenance badge and view-original toggle as a reconstructed chart.

2. **Overlay recreation (annotated figures).** When the figure is a BASE IMAGE (a map, diagram, photo, or screenshot) carrying author-added overlays that cannot be losslessly rebuilt as full SVG, keep the base image and recreate ONLY its annotations as a registered overlay layer:
    - **Keep the extracted base image as the bottom layer** at native resolution (the same asset that powers the lightbox and the view-original toggle).
    - **Recreate each annotation in a registered overlay layer** (inline SVG, or absolutely-positioned HTML) whose coordinate space is normalized to the base image (use PERCENTAGE coordinates so the overlay scales with the image). Region boxes, zone fills, labels, and leader lines land where they do in the source. When the extractor supplied `annotations` on the image block (PPTX overlay shapes, with image-relative boxes, text, and fill/line colors; see `content-model.md`), place each element straight from that metadata; for a flattened source, read the annotations from the rendered image under the part-4 confidence gate and place them against the base image by eye.
    - **Make the overlay interactive** per the site-wide interaction layer: hover (and keyboard focus) highlights a region and its label; a click-toggle legend lists the groupings; every region is keyboard-focusable; the pan/zoom lightbox moves the base image and the overlay together.
    - **Carry the same provenance badge and view-original toggle** as a reconstructed chart (`provenance` set, a `confidence` tier, `source_image` = the base image), so the reader can always swap in the untouched original.

3. **Enhanced original.** When ANY label is unreadable, the structure is dense (detailed geography, many nodes), or the annotations are freeform and un-placeable, use the enhanced-original viewer (pan/zoom lightbox, caption preserved). A lossy redraw that drops or approximates labels, and a guessed overlay, are both fidelity failures, not a nice try.

**2b. Geo-pin overlay (location maps whose labels are loose text).** A common slide pattern defeats path 2 directly: a geographic base map whose site/location labels were loose TEXT BOXES on the slide, so extraction recovers the label STRINGS (they land in the text layer) but not their positions. When the labeled things are real, geocodable places (hospitals, offices, cities), rebuild the overlay from GEOGRAPHY instead of from the lost layout:
    - **Coordinates**: assign each place its public city coordinates (lat/lon). These are facts about the world, not guesses about the slide - which is what makes this path honest where "place the labels by eye" would be fabrication.
    - **Projection, fitted to the map image itself**: map lat/lon to image percent-coordinates through a transform calibrated against landmarks READ OFF THE BASE IMAGE (lake centers, coastline notches, border corners - 10+ anchors spread across the extent). Expect a plain affine fit to FAIL on country-scale maps (most are conic projections: a linear fit puts Pacific-coast cities in the ocean); a quadratic in (lon, lat) fitted by least squares over the anchors converges where affine and guessed standard-parallel conic fits do not. `scripts/fit_map_projection.py` runs this fit and prints coefficients, per-anchor residuals, and a paste-ready JS `projPct()`.
    - **Verify by render loop, not by residuals**: render the pins and grade them against the map's own geography (a pin in the ocean is a defect regardless of the fit's numbers); correct individual outliers with small per-site nudges recorded in the code.
    - **De-cluster for interaction**: dense metros stack pins that intercept each other's hover - run a collision-relaxation pass (push pairs apart to a minimum separation of about one pin diameter) so every pin stays individually hoverable and focusable.
    - **Namespace the pin classes** (`.map-pin`, never `.pin`) per the component-namespacing rule in `interactive-features.md`.
    - **Disclose the provenance in the visible caption**: pin positions are computed from city coordinates, NOT recovered from the source layout. Sync the pins with the same filter control as the accompanying directory/list, and keep the enhanced-original lightbox on the base image.

**The side-text description is an ACCESSIBLE COMPLEMENT, never the REPLACEMENT.** A textual list of the regions and their labels (as `alt`, a caption, or a `<details>` list) accompanies the visual overlay for screen-reader and no-JS access; it never STANDS IN for the overlay. Demoting an annotated map to a flat base image beside a bulleted list of its regions (dropping the visual overlay) is the exact defect the overlay-recreation path prevents.

`photo` and `screenshot` images with NO author annotations always render as originals (lightbox-enabled, caption preserved). `decorative` images may be omitted from the output ONLY with a skip entry the coverage reconciliation can read (e.g. an HTML comment `decorative-skip: <alt> (page N) - repeated logo`).

## 6. Model round-trip

The protocol UPDATES the model JSON so downstream stages (design, authoring, and the Phase 5-style coverage reconciliation) work from one source of truth:

1. Every image block gains its `classification`.
2. Every accepted reconstruction adds a new `chart` block (provenance `reconstructed-from-image`, `confidence`, `source_image`, `axis`, `caption` from the figure caption) placed immediately after its source image block; the image block stays in the model (it powers the view-original toggle and the audit).
3. Every `low`-tier decision and every `decorative` drop is recorded where reconciliation can find it (the skip-comment convention above, or a note appended to the model's coverage `skip_reasons`).
4. For an accepted annotated-figure overlay (part 5, path 2), the base image block STAYS in the model and records the overlay decision: the recreated annotations (from the extractor's `annotations` metadata, or read from the image) plus `provenance`, `confidence`, and `source_image`, with the per-annotation worksheet comment adjacent in the output. A `low`-tier annotated figure records its enhanced-original decision the same way a `low` chart does.

Nothing is deleted from the model. The reconciliation rule stays: every visual the coverage manifest counts must end up rendered, reconstructed, or explicitly skipped with a reason.

## 7. Scanned-page transcription and OCR verification

For every `image` block with `origin: "scanned-page"`, the agent reads the page image and reconciles it with the OCR blocks the extractor emitted for that page (`provenance: "ocr"`):

- **Verify low-confidence OCR**: every block the extractor counted in `ocr_low_confidence` (its `ocr_confidence` is below the threshold) is checked word-by-word against the page image and corrected in place; a corrected block's provenance becomes `agent-read`.
- **Verify ALL numeric content regardless of confidence**: numbers in OCR'd tables, figure values, currency amounts, dates, and captions are always compared against the pixels. OCR confidence scores do not certify digits; the agent's read does.
- **Fill gaps**: content the OCR missed (or that no OCR engine was available to read) is transcribed as new `paragraph` / `table` blocks with `provenance: "agent-read"`, inserted in reading order.
- **Route figures**: a chart, map, diagram, or photo region visible on the scanned page enters the classification pass (part 1) - crop context from the page image, then apply the worksheet and confidence gate exactly as for any other figure.
- **Truthfulness**: transcription follows the worksheet's rules - unreadable words are written `<unreadable>`, never guessed; the page image ships in the output (lightbox-enabled) so the reader can always consult the original.

A scanned page is complete when its text, tables, and figures are all either verified/transcribed or explicitly marked unreadable - the same no-silent-loss rule as everywhere else in this skill.

## Coverage reconciliation (output format)

The verification stage closes the loop between what extraction FOUND and what the output SHOWS. Compare the model's `coverage` manifest against the authored `.html` and produce a one-line-per-item accounting, embedded as an HTML comment at the end of the output and summarized to the user. Every visual the manifest counts must resolve to exactly one of `rendered`, `reconstructed`, `overlay-reconstructed` (an annotated figure whose base image is kept and whose annotations are recreated as an interactive overlay, high/medium confidence), or `skipped` (with a reason); a `low`-confidence annotated figure resolves to `rendered` (enhanced original) with a one-line reason. OCR-provenance content additionally resolves to `verified-ocr` or `agent-read`.

```text
COVERAGE RECONCILIATION - <source path>
manifest: images found F / kept K / skipped S; native charts C;
          vector regions rasterized R / skipped Rs; scanned pages P
          (OCR'd O, agent-read A, low-confidence L)
- [rendered]      image page 4 "photo" (lightbox)
- [reconstructed] chart from image page 2 "Figure 1: ..." (confidence medium,
                  worksheet comment adjacent, view-original toggle)
- [overlay-reconstructed] map page 3 "Specialist coverage" (annotated; 5 regions
                  recreated as an interactive overlay over the base image,
                  confidence high, view-original toggle)
- [skipped]       image page 1 "logo" - decorative (repeated asset)
- [verified-ocr]  table page 1 (numeric values confirmed against the page image)
- [agent-read]    paragraph page 1 (transcribed; OCR had merged two paragraphs)
verdict: ACCOUNTED - 0 unaccounted
```

The verdict is binary: ANY unaccounted visual (counted in the manifest but neither present in the output nor carrying a skip line) FAILS verification. Two companion gates ride on the same listing:

- **Data fidelity**: every `chart` in the output traces to `source-data` / `native-chart` provenance or to a worksheet (`reconstructed-from-image`); a chart with neither is fabricated and FAILS.
- **OCR verification**: no `provenance: "ocr"` numeric content reaches the output without the part-7 verification pass having confirmed or corrected it; unverified low-confidence OCR text never appears silently.

## Common failure modes this protocol exists to prevent

- Embedding a data-bearing figure as a static picture because "it's just an image" - classify first; charts get worksheets.
- Eyeballing bar heights into a chart without a worksheet - unaudited numbers are fabrication, even when they look plausible.
- "Improving" a blurry figure by approximating a cleaner version - low confidence means enhanced original, never invented data.
- Rebuilding a map that drops half the labels - label-lossy redraws fail part 5; use the lightbox.
- Trusting OCR digits because the confidence score was high - numeric content is always agent-verified (part 7).
