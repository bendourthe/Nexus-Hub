# Interactive Features and the Enrichment Pass

This document is the design contract for the output. It has two layers: the PRIMARY path - the agent authoring a unique, interactive WEBSITE from the content model, with dynamic charts and a bespoke design - and an OPTIONAL deterministic baseline (`scripts/build_presentation.py` + `assets/presentation-template.html`), whose plain, slide-based features are cataloged further down for when a fast, reproducible draft is wanted.

Everything here holds the two non-negotiable guarantees: the output is a single self-contained file that opens with zero external network requests (see `[[html-output-conventions]]`), and it reads as intentionally designed rather than AI-generated (see `[[hallmark-design]]`). The default output is a navigable website, not a static slide deck.

## Authoring the Interactive Website (primary path)

The default deliverable is a unique, interactive, single-file website authored from the content model - not a slide deck. Aim for a clear, engaging, dynamic interface.

### Structure

- Open with a concise overview / landing area, then organize the content into scannable sections.
- Provide real navigation: in-page anchors, a sticky section nav, tabs, or routed views - pick what fits the content. Avoid a forced one-screen-per-slide sequence.
- Make it responsive (phone to projector) and keyboard-accessible, with visible focus states.
- **Use the viewport width deliberately.** The 45-85 character reading measure is for long-form body prose only, not a page-wide wrapper. Give headings, hero / display text, charts, tables, and section backgrounds the room to use the available width; full-bleed bands and multi-column zones are encouraged. A page locked into a single narrow centered column (headings and all) while cards or charts sit at full width beside it reads as broken. Decide the measure per element, never once for the page.

### Dynamic, manipulable charts

Every figure that carries real data (a `chart` block in the content model, or a numeric table worth charting) becomes an INTERACTIVE chart the reader can manipulate - built entirely from inlined vanilla JavaScript, with no charting library and no CDN (the offline guarantee is absolute). At minimum, support:

- **Zoom and pan**: mouse wheel / pinch to zoom, drag to pan, and a reset control.
- **Series toggle**: click a legend entry to hide/show that series; the axes rescale to the visible data.
- **Axis control**: let the reader adjust the visible x / y range (drag-select a region to zoom into it, or min/max inputs).
- **Readout**: hover (and keyboard focus) shows the value at a point.

Implementation approach (no library): render to a `<canvas>` (or an inline SVG you update), keep the data plus the current view state (`xMin/xMax/yMin/yMax`, the hidden-series set) in a small JS object, and redraw on interaction. Bar, line, area, scatter, and pie/doughnut all follow the same redraw-on-state pattern. Always include an accessible label and a text+swatch legend so color is never the sole carrier of meaning. Use the source's REAL numbers; never invent values or round data away.

### Real visuals

If the source has figures, tables, or images, they appear in the site: images inline as base64; numeric data as the interactive charts above; large tables as sortable / filterable tables where that helps the reader.

### Prominence preservation

Respect the source's visual hierarchy. A visual the author made dominant stays dominant in the site; do not flatten a hero image into a uniform thumbnail grid. Each `image` block carries prominence signals from the extractor: `page_fraction` (0..1, the share of the source page / slide it occupied) and native `width` / `height` (see `references/content-model.md`).

- **Rank each section's visuals** by `page_fraction`, falling back to relative `width * height`, then to whether the image is the sole / primary visual of its section.
- **Heroes render as heroes.** A visual that dominates its source - roughly `page_fraction >= 0.5`, OR the single primary visual of a section, OR (when `page_fraction` is absent) markedly larger than its siblings - gets a prominent treatment: its own full-width band or a wide column, sized to be seen, not shrunk into a row of equal thumbnails.
- **Group only genuinely-secondary visuals.** Several small images of comparable, low `page_fraction` (logos, a strip of thumbnails, incidental screenshots) may become a gallery / grid - but size the grid so each image is legible, never a postage stamp.
- **Never flatten a hero.** A single dominant image must not be demoted to thumbnail size beside unrelated cards; that width mismatch is the exact fidelity loss this rule prevents.
- **Native resolution end to end.** Render from the native-resolution asset, and in any lightbox / zoom show that SAME full-resolution `data_uri` - never an upscaled thumbnail. This reinforces the figure-reconstruction lightbox rule; build the viewer once.
- **When the signals are absent** (`page_fraction` null and no `width` / `height`, e.g. a standalone image or a DOCX inline image), fall back to the image's role in its section: a section's only image is its hero; a run of comparable images is a gallery.

The failure mode to avoid is the "contact sheet": taking a slide that was dominated by two or three large photos and rendering it as a dense, uniform grid of small tiles. Preserve the source's emphasis and enhance it with the lightbox and motion; do not erase it.

### Spacing and density

Complement the horizontal width discipline with vertical discipline: no dead, half-empty screens.

- **Size every section to its content.** Do not stretch a section to a fixed one-screen height that leaves half a viewport empty. Section height follows content, not a slide grid.
- **Use a consistent vertical rhythm** from the committed spacing token, not large unmotivated gaps between blocks.
- **Compact or pair sparse sections.** A section with a single chart or a short list either gets a deliberately compact band or is paired with an adjacent related element (its caption, a stat, the source figure, a related image) rather than floating alone in whitespace.
- **Reserve generous whitespace for intentional emphasis** (a hero, a section transition), never as the page-wide default that produces the empty look.

This is the vertical partner to "use the viewport width on purpose": decide density per section, and let content, not a fixed slide frame, set the height.

### Output aspect (the canvas)

The output aspect is resolved right after the style direction (a named `--layout` binds and skips the menu; otherwise the aspect menu is offered; see the command and SKILL.md). It governs the page's CSS canvas and composes WITH the per-element width discipline and the design tokens - it never overrides them. Record the resolved aspect (and whether it was auto-picked) in the design-record HTML comment.

Four options, mirroring the style menu:

- **Full-width** - the site fills a 16:9 screen edge to edge, so opening it fullscreen occupies most of a typical widescreen display. CSS: a wide page container (`max-width: 100%` or a very large cap) with generous side gutters, full-bleed bands, and multi-column content zones; hero and section backgrounds span the viewport. Best for deck-like sources.
- **Standard** - a typical centered webpage column (`max-width` about 72-90rem, centered, comfortable side margins). Sections stack in a readable central measure with occasional wider break-outs for charts / tables. Best for reports and repositories.
- **Portrait** - a tall, narrow, reading- / mobile-oriented canvas (`max-width` about 40-52rem). Single-column, strong vertical rhythm, large tap targets; charts and tables scroll within their own container rather than forcing the page wide. Best for long-form reading and phone-first delivery.
- **Other** - a caller description (equivalent to `--layout <description>`); interpret it into concrete canvas decisions and record them.

**Non-interactive fallback (content-aware):** when the menu cannot be answered, pick by source - a deck-like source (a `.pptx`, or a PDF whose source entry carries `deck_like: true`) defaults to Full-width; a report, a repository, or a text-dominant source defaults to Standard. Record the chosen aspect and that it was auto-picked.

### Site-wide interaction layer

Charts are not the only carrier of dynamism - a source with zero chartable data must STILL produce a page that responds to the reader. This layer is the interactivity vocabulary for everything that is not a chart. All patterns are inlined vanilla JS/CSS (no library, no CDN), keyboard-accessible, and guarded by `prefers-reduced-motion`.

1. **Scroll-triggered section reveals** - `IntersectionObserver` adds a `.revealed` class once per element as it enters the viewport; CSS transitions opacity/transform (a short rise, 200-400ms), optionally staggered per child via `transition-delay`. Sketch: `new IntersectionObserver(es => es.forEach(e => e.isIntersecting && (e.target.classList.add("revealed"), obs.unobserve(e.target))), {threshold: 0.15})`. Accessibility: under `prefers-reduced-motion: reduce`, elements start fully visible (no observer needed); content must never be unreachable if JS fails - reveal styles apply only under a `.js` root class.
2. **Scroll-linked progress** - a sticky section nav whose active item tracks the section in view (a second `IntersectionObserver` with `rootMargin` tuned to the viewport middle), plus an optional thin reading-progress bar driven by `scroll` position (`requestAnimationFrame`-throttled). Accessibility: the active nav item carries `aria-current="true"`; the progress bar is `aria-hidden` (decorative).
3. **Hover and focus affordances** - every interactive-adjacent element visibly responds: cards lift or gain an accent border, image thumbnails hint zoomability (a subtle scale or overlay icon), table rows highlight. Sketch: `:hover` plus `:focus-visible` sharing one ruleset (`.card:hover, .card:focus-visible { transform: translateY(-2px); ... }`). Accessibility: EVERY hover state has a keyboard-focus twin; focus outlines are never suppressed without a visible replacement.
4. **Animated stat counters** - KPI-style numbers count up on first reveal (reuse the reveal observer), landing on the EXACT source value; duration ~800ms via `requestAnimationFrame`. Accessibility: under reduced motion the final value renders immediately; the element's accessible text is always the final value (animate a visual span, keep the real number in the DOM or `aria-label`).
5. **Image lightbox with pan/zoom** - every non-decorative image opens in an overlay viewer: wheel/pinch zoom, drag pan, a reset control, Escape and backdrop-click to close. This is the SAME component the figure-reconstruction protocol's enhanced-original viewer and view-original toggle use - build it once. Accessibility: the trigger is a real `<button>` (or the image wrapped in one); on open, focus moves into the dialog (`role="dialog"`, `aria-modal="true"`) and is trapped; on close, focus returns to the trigger.
6. **Expand/collapse structures** - tabs or accordions for dense subordinate content (appendices, per-source detail, long tables). Sketch: accordions as native `<details>/<summary>` (free keyboard support) styled to the design; tabs as buttons with `role="tab"` / `aria-selected` toggling `hidden` on panels. Accessibility: arrow-key navigation between tabs; state is always reflected in ARIA, not just classes.
7. **Micro-transitions on state change** - nav jumps use smooth scrolling (`scroll-behavior: smooth` under motion-ok), chart series toggles and tab switches animate briefly (~150ms), lightbox fades in. Accessibility: all durations collapse to 0 under `prefers-reduced-motion: reduce`.

### The minimum interaction budget (binary)

Every run MUST ship ALL FIVE of the following, functional offline with zero external requests, in at most ~60 KB of added inline JS (the interaction layer, excluding chart controllers and base64 payloads):

1. Working section navigation with active-state tracking (pattern 2).
2. Scroll-triggered reveals OR an equivalent scroll-responsive treatment (pattern 1).
3. Hover + keyboard-focus affordances on cards, images, and table rows (pattern 3).
4. A pan/zoom lightbox on EVERY non-decorative image (pattern 5).
5. At least ONE content-appropriate signature interaction chosen to fit the content: animated counters for a KPI-heavy source, tabs/accordions for a dense report, a comparison slider, a filterable grid, an annotated-figure hotspot layer... (patterns 4/6/7 or a bespoke move).

A page whose only interactivity is its charts FAILS the budget. A page with no charts at all still meets the budget through this layer - that is the point.

### Design direction (resolve the direction, then brainstorm - creativity-first)

Before writing any markup, resolve a design direction and commit to one. The goal each run is a UNIQUE, creative, interactive design; "fit the document type" is never the rule. "Be unique" is not enough on its own either: the agent has a strong default attractor it returns to unless forced off it, and that sameness is what makes a run read as AI-generated. Make this a real, deliberate stage, not an afterthought during authoring.

**Resolve the direction in order.**

1. **A named style binds.** When `--style` words (or the natural `using the style <description>` phrasing), a `[[theme-tokens]]` set, or a `[[brand-styling]]` brand `tokens.json` is supplied, that is the binding direction: honor it instead of offering the menu (a partial `--style` still leaves the unspecified axes to brainstorm). Ask the user for brand tokens before inventing a brand's colors.
2. **Otherwise, offer the design-direction menu first.** With no style named, ask the user to choose before authoring:
    1. **Corporate & Professional** - polished, restrained, business-ready.
    2. **Creative & Expressive** - bold, artistic, unexpected.
    3. **Technical & Precise** - clean, structured, data-forward.
    4. **Surprise me** - let the agent invent a unique, creative direction for this run.
    5. **Other** - the user describes their own style (equivalent to `--style`).

    If the menu cannot be answered (a non-interactive or headless run), fall back to option 4 and proceed with the creative/unique path - never block on the prompt.

3. **Roll the design brief - mechanical entropy FIRST, judgment second.** Unseeded taste converges: two same-preset runs drift to the same palette and layout because the agent samples its own prior - that is the "same preset, same look every run" failure this step exists to break. Once the preset is resolved, run the bundled sampler:

    ```bash
    python scripts/design_seed.py --preset <corporate|creative|technical|surprise> -o brief.json
    ```

    It rolls candidates from curated axis pools (12 hue families with light AND dark bases, moods, type voices, layout signatures, motion personalities, signature moves), constrained per preset so preset intent holds while the feel still varies; seeds from `os.urandom` (pass `--seed N` to reproduce a run); and rejects any candidate sharing 2+ of {hue family, layout signature, type voice} with the last 3 committed runs in the persisted history (`~/.nexus-hub/state/presentify-design-history.json`, `--history` to override). Treat the rolled brief as the COMMITTED starting tokens: adapt the exact hexes, pairings, and pacing to the content's character WITHIN the brief's register - do NOT re-roll until you like the answer, and do NOT silently swap axes back toward the attractor. Record the seed and the brief's one-line summary in the output's design-record comment, and after the run ships call `python scripts/design_seed.py --commit brief.json` so the history advances and the next run is pushed away from this one. Skip the roll ONLY when the script cannot execute (no Python on the host): then manually vary at least the hue family and the layout signature away from the last recorded run, and say so in one line.

**Let content inform, not dictate.** The content's character (subject, audience, tone, era, emotional register) is an INPUT that shades the design, not the rule that picks it. It can nudge palette and pacing - a quarterly finance report leans calmer, a product launch leans bolder - but lead with what makes this run distinctive, interactive, and engaging. Do not mechanically map document type to a fixed aesthetic: that reintroduces the sameness the menu and the surprise-me option exist to break.

**Adapt the brief across these axes (the roll picks the register; you tune within it).** The sampler fixes the high-entropy axes; the brainstorm's job is to make them serve THIS content - sharpen the palette's exact values, pick the pairing weights, decide where the layout signature bites hardest. The axes, for reference:

- **Palette mood**: not just light vs dark, but the emotional temperature (warm paper, cool clinical, high-contrast editorial, muted earthy, saturated playful). Constrain to one or two accents over a neutral base (`[[hallmark-design]]` gate 8).
- **Typographic voice**: the heading / body pairing and its personality (serif-display editorial, geometric-sans modern, mono-technical, humanist-warm). System stacks only, or base64 `@font-face`.
- **Layout system**: the structural signature (asymmetric two-column, editorial grid with pull-quotes, full-bleed bands, sidebar-anchored, magazine spreads). Not a stack of identical centered cards (gate 2).
- **Motion personality**: how the site moves (crisp and instant, slow and weighty, springy, none at all). Always guarded by `prefers-reduced-motion`.

**Diverge from the default attractor.** The look the agent drifts to by default is off-limits unless the content or the caller asks for it:

- a near-black background,
- monospace eyebrow / kicker labels (the "01 / FOUNDATIONS" tag),
- an amber / orange accent,
- evenly-spaced rows of identical cards,
- a dead-centered hero.

If the committed direction matches that description, it is almost certainly the attractor: pick something else. Aim also to differ from the previous run, so a sequence of outputs visibly varies.

**Commit to concrete tokens and record them.** Write the direction down before authoring: a name, the exact colors (hex), the font pairing (heading / body / mono), the spacing rhythm, the signature layout move, the motion signature, AND the roll's seed + one-line brief summary (so the run is reproducible and auditable). Embed it as an HTML comment at the top of the output and state it to the user in one line. Then author to those tokens; do not drift back to the attractor mid-build.

**Keep fonts self-contained.** Whatever the direction, keep all fonts as system stacks or base64 `@font-face`; never fetch a web font (it would break the offline guarantee). A named style or theme is resolved up front per "Resolve the direction in order" above and binds the look; the brainstorm only fills the axes it leaves open.

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
