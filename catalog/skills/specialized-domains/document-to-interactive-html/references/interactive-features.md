# Interactive Features and the Enrichment Pass

This document is the design contract for the output. It has two layers: the PRIMARY path - the agent authoring a unique, interactive WEBSITE from the content model, with dynamic charts and a bespoke design - and an OPTIONAL deterministic baseline (`scripts/build_presentation.py` + `assets/presentation-template.html`), whose plain, slide-based features are cataloged further down for when a fast, reproducible draft is wanted.

Everything here holds the two non-negotiable guarantees: the output is a single self-contained file that opens with zero external network requests (see `[[html-output-conventions]]`), and it reads as intentionally designed rather than AI-generated (see `[[hallmark-design]]`). The default output is a navigable website, not a static slide deck.

## Authoring the Interactive Website (primary path)

The default deliverable is a unique, interactive, single-file website authored from the content model - not a slide deck. Aim for a clear, engaging, dynamic interface.

### Structure

- Open with a concise overview / landing area, then organize the content into scannable sections.
- Provide real navigation: in-page anchors, a sticky section nav, tabs, or routed views - pick what fits the content. Avoid a forced one-screen-per-slide sequence.
- Make it responsive (phone to projector) and keyboard-accessible, with visible focus states.

### Dynamic, manipulable charts

Every figure that carries real data (a `chart` block in the content model, or a numeric table worth charting) becomes an INTERACTIVE chart the reader can manipulate - built entirely from inlined vanilla JavaScript, with no charting library and no CDN (the offline guarantee is absolute). At minimum, support:

- **Zoom and pan**: mouse wheel / pinch to zoom, drag to pan, and a reset control.
- **Series toggle**: click a legend entry to hide/show that series; the axes rescale to the visible data.
- **Axis control**: let the reader adjust the visible x / y range (drag-select a region to zoom into it, or min/max inputs).
- **Readout**: hover (and keyboard focus) shows the value at a point.

Implementation approach (no library): render to a `<canvas>` (or an inline SVG you update), keep the data plus the current view state (`xMin/xMax/yMin/yMax`, the hidden-series set) in a small JS object, and redraw on interaction. Bar, line, area, scatter, and pie/doughnut all follow the same redraw-on-state pattern. Always include an accessible label and a text+swatch legend so color is never the sole carrier of meaning. Use the source's REAL numbers; never invent values or round data away.

### Real visuals

If the source has figures, tables, or images, they appear in the site: images inline as base64; numeric data as the interactive charts above; large tables as sortable / filterable tables where that helps the reader.

### Unique design and caller-specified style

- Author a fresh, content-appropriate design each run. A recognizable fixed house style across runs is the templated 'AI-generated' signature `[[hallmark-design]]` rejects.
- If the caller specified a style or color scheme - a `[[theme-tokens]]` set, a `[[brand-styling]]` brand `tokens.json`, or plain words ("dark", "minimal", "editorial", "playful", "high-contrast", a brand color) - treat it as the binding design direction. Ask for brand tokens before inventing a brand's colors.
- Keep all fonts as system stacks (or base64 `@font-face`); never fetch a web font.

## Optional Baseline: the deterministic builder's features

The sections below describe the OPTIONAL `scripts/build_presentation.py` baseline and its slide-based template - a plain, reproducible draft, not the primary deliverable. Use them when a caller explicitly wants a fast deterministic draft to elevate into the interactive website above.

### Interactive Feature Catalog (baseline template)

The template carries all of the following with inline CSS and JS only. The builder injects content; it never adds or removes a feature.

- **Slide model**: each content-model section becomes one `.slide`. Exactly one slide is active at a time; the rest are hidden from layout and from assistive tech (`aria-hidden`).
- **Navigation**: on-screen Prev / Next buttons (placed bottom-right, deliberately not a centered control bar), plus a full keyboard map (below). Prev is disabled on the first slide and Next on the last, so the bounds are visible rather than silent.
- **Outline panel**: a slide-in panel, built at load time from the headings present in the DOM, that jumps to any slide. Title and section-break entries are emphasized so the structure is scannable. The current slide is marked with `aria-current`.
- **Progress indicator**: a thin top bar that fills from 0 to 100 percent across the deck, plus a `current / total` counter.
- **Fullscreen**: a control and the `F` key toggle the Fullscreen API; the button reflects state with `aria-pressed`.
- **Deep links**: the active slide is mirrored to the URL hash (`#s3`), so a link opens on a specific slide and a reload restores position.
- **Transitions**: a short horizontal slide-in, directional (forward vs back). Wrapped in `@media (prefers-reduced-motion: no-preference)`, so a reduced-motion user gets instant, motion-free slide changes.
- **Responsive and projector modes**: padding and the reading measure scale by viewport. Below 760px the chrome simplifies for phones; above 1700px the measure widens and side padding grows for large projector displays.
- **Print / PDF path**: an `@media print` block stacks every slide vertically with page breaks and drops the chrome, so "Print to PDF" yields a clean handout. Speaker notes are shown in print.

### Keyboard map

| Key | Action |
|---|---|
| Right arrow, Space, Page Down | Next slide |
| Left arrow, Page Up | Previous slide |
| Home / End | First / last slide |
| `O` | Toggle the outline panel |
| `N` or `S` | Toggle speaker notes |
| `F` | Toggle fullscreen |
| Escape | Close the outline panel |

### Speaker notes

A `notes` block renders into an `<aside class="notes">` that is hidden by default (`body:not(.notes-on) .notes { display: none }`) and revealed by the `N` / `S` toggle. Notes never appear on the slide face during normal navigation, so a deck can carry presenter context without leaking it to the audience. They are intentionally shown in the print path for a presenter handout.

### Inline chart types and when to use each

These are the baseline builder's STATIC inline-SVG charts (no charting library, no canvas dependency, no CDN); the primary path renders the same data as the dynamic, manipulable charts described in "Dynamic, manipulable charts" above. The `chart_type_hint` on a `chart` block selects the renderer; the agent may override it for the data shape.

| Type | Use when | Notes |
|---|---|---|
| `bar` | Comparing a value across a handful of discrete categories; multiple series compared side by side. | Default. Grouped bars for multi-series. Honest zero baseline. |
| `line` | A trend across an ordered or time-like axis, or many categories (> ~12). | One polyline per series with point markers. |
| `pie` | Parts of a single whole, few slices (<= ~6), one series. | Uses the first series only. Avoid for more than ~6 slices. |
| `doughnut` | Same as pie, when a lighter ring reads better than a solid wheel. | Rendered as a stroked ring, so no background-color matching is needed. |

Every chart includes an accessible `role="img"` label, per-segment `<title>` tooltips, and a text + swatch legend (color is never the sole carrier of meaning). The inline SVG omits the SVG namespace attribute on purpose: it is implied for inline SVG inside an HTML document, and including the `w3.org` namespace URI would read as an external reference to the offline self-check.

## Theme Override Path

The builder reads `assets/theme.json` as the default theme and deep-merges an optional override file passed with `--theme`. The override is layered over the default, so a partial override (for example, only a palette) keeps the default fonts and spacing.

The theme schema is the `[[theme-tokens]]` contract, so any artifact that already speaks that schema is a drop-in override with no adapter:

- **Curated theme**: select one of the curated `[[theme-tokens]]` theme JSON files and pass it as `--theme path/to/theme.json`. Brand-neutral, no user assets required.
- **Brand tokens**: pass a `[[brand-styling]]` per-brand `tokens.json` (which extends the same schema with brand fields) as `--theme`. The builder reads the shared `palette` / `fonts` / `spacing` / `radius` / `shadow` keys and ignores brand-only fields it does not consume.

Tokens the builder consumes and maps to CSS custom properties:

```json
{
  "palette": {
    "primary": "#hex", "secondary": "#hex", "accent": "#hex",
    "background": "#hex", "foreground": "#hex", "muted": "#hex"
  },
  "fonts": { "heading": "<CSS stack>", "body": "<CSS stack>", "mono": "<CSS stack>" },
  "spacing": { "base": 8, "scale": [0.5, 1, 1.5, 2, 3, 4, 6, 8] },
  "radius": 6,
  "shadow": "<CSS shadow or 'none'>",
  "chart_palette": ["#hex", "..."]
}
```

`chart_palette` is an optional extension used to color multi-series charts. When an override omits it, the builder derives chart colors from `accent`, `primary`, `secondary`, and `muted`, so a plain `[[theme-tokens]]` file still charts correctly.

Font stacks must stay self-contained: use system font stacks (no web-font `@import`, no font CDN). A brand that ships a custom font would need it embedded as a base64 `@font-face` in a later iteration; that is out of scope for the baseline and must not become an external fetch.

## The Enrichment Pass

The builder gives you a correct, plain baseline. The enrichment pass is where the agent makes it captivating, working on the produced HTML and the upstream content model. It is LLM-native by design: there is no "make it nice" script, because that judgment is the agent's. The pass must never introduce an external dependency or break the offline guarantee.

Run these moves, then run the `[[hallmark-design]]` `audit` verb over the result and clear every failing gate:

1. **Choose a narrative structure.** A raw report is a flat wall of headings; a presentation has a shape. Add or reorder section-breaks so the deck has an arc (open, build, land). For a dense report this is the single highest-leverage move: introduce an agenda and pace the reveal.
2. **Tighten copy to presentation grade.** Source prose is written to be read at length; slide copy is written to be seen. Shorten paragraphs to claims, turn run-on sentences into parallel bullets, and cut restatement. Do not invent facts the source does not contain.
3. **Pick the right chart per data shape.** Override a `chart_type_hint` when the data wants a different form (a trend that arrived as `bar` should usually be `line`; a five-slice share-of-whole as `pie`). Prefer one clear chart over a dense table when the point is a comparison.
4. **Add intentional emphasis and motion.** Use the accent sparingly for the one thing that matters per slide. Keep motion purposeful (it already honors reduced-motion). Resist decorative entrance animation on every element.
5. **Hold the anti-slop gates.** No dead-centered hero, no row of identical cards, no unmotivated gradient, a real type scale, asymmetry where it aids hierarchy, accessible focus and contrast. These are the `[[hallmark-design]]` gates; the template starts compliant, and enrichment must keep it compliant.

## Input-mode Decision Rule

The same pipeline serves three intents; the mode is auto-detected from the inputs and is overridable. The enrichment pass adapts to the mode.

- **Single deck (one `.pptx`) -> preserve the flow.** One slide maps to one section in slide order. Keep that order; the deck should follow the same flow as the source, only more interactive and more visually considered. Do not re-sequence a slide deck the author already structured.
- **Single report (one `.docx` / `.pdf` / `.xlsx`) -> present the report.** A flat document becomes a paced presentation OF that report: a title, a synthesized agenda, one section per heading, and data surfaced as inline charts. This is where narrative restructuring (move 1) does the most work.
- **Multiple / mixed files -> compile the sources.** Each source contributes a labeled run of sections, introduced by a section-break carrying the source title, optionally preceded by a synthesized overview that names all sources. Preserve per-source attribution; do not blend two sources into an indistinguishable middle.

## Attribution

All naming in the template, the builder, and this document is generic and descriptive (per the Reverse-Engineering Attribution Rule): no upstream product, repository, or library brand appears in any distributed artifact. The interactive patterns here are an original, self-contained implementation.
