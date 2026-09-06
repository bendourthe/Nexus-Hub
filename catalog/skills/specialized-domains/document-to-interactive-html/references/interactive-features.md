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

**Mixed-scale series (BINARY).** When one chart carries series of very different ranges (an inventory line topping out near 40 beside a cumulative-patients series reaching 179), NEVER draw a value clamped flat at the axis maximum - a flat-topped bar at y-max reads as a real measurement and is therefore fabricated data. Instead: (1) series whose range dwarfs the primary axis carry `startHidden` and begin toggled off, so the default view matches the source figure; (2) every legend toggle re-fits the axis to the maximum of the VISIBLE series (nice-rounded, and the y-max input reflects the refit); (3) a value may only ever render at its true position. State the start-hidden behavior in the chart's hint line so the reader knows the extra series exist.

**Component CSS namespacing (BINARY).** Every class an authored component introduces is prefixed with the component's name: `.map-pin`, `.chart-legend`, `.lightbox-cap` - never bare generic nouns (`.pin`, `.card`, `.tip`, `.legend` used twice). Two features that each picked an "obvious" name collide silently: a map-pin's `width:14px` once applied to the cinematic stage's `.pin` sticky wrapper and crushed every hero canvas to a 10px strip with zero console errors. The rule is preventive, not curative - by the time the collision is visible it has already shipped past change-local checks.

**Scorer contract (emit during authoring, not as repair).** `scripts/visual_qa_score.py` parses specific markup shapes; a page authored without them burns a full QA iteration on format repair. Emit from the start: `data-aspect="<full|standard|portrait>"` on `<body>`; `--page-max` and `--gutter` canvas custom properties; design-record `placement:` lines in the exact `section | role | embedded | why` or `section | none: reason` form; hero-figure caps as the literal strings `max-height: 80vh` and `object-fit: contain`; and color custom-property names that reflect where the color is used - the contrast check pairs foregrounds and backgrounds by NAME heuristics (`fg`/`ink`/`text` vs `paper`/`surface`/`bg`/`base`), so a foreground that only ever sits on a dark band must not carry a name that pairs it with paper surfaces (call it `--band-hi`, not `--band-fg`).

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

**Measurable image-box rules (the Phase 5 QA gate checks these).** Prominence is bounded, not unbounded: a visual is sized to its source role AND kept inside the layout so nothing breaks at 100% zoom.

- **Hero height cap.** A hero occupies a full-width band or wide column, but its RENDERED height is capped (about `<= 80vh`) so it never fills the whole viewport at 100% zoom. Metric: rendered image height over viewport height stays at or below ~0.8.
- **Secondary cap (the inverse of the contact sheet).** A secondary image (low `page_fraction`, or low relative area) is capped to a legible gallery-tile size and MUST NOT be enlarged past a hero. A low-prominence image ballooned to hero scale is as much a fidelity loss as a hero shrunk to a thumbnail. Metric: a low-`page_fraction` block renders no wider than its section's hero (secondary rendered width at or below hero rendered width).
- **Object-fit / crop policy.** Use `object-fit: contain` (with letterboxing or a matched background) for any image whose meaningful content would be clipped by `cover`; reserve `cover` for genuinely decorative backdrops where no content is lost. Cropping away a chart axis, a labeled map region, or a face is a defect. Metric: for a non-decorative image the rendered aspect ratio matches the native `width:height` within a small tolerance, so there is no crop and no distortion (the ratio of `rendered_ratio` to `native_ratio` sits within about 2 percent of 1).
- **No oversized tile.** In a gallery of comparable-prominence images, each tile is bounded to a legible-but-capped box; none is enlarged to hero scale. Metric: every gallery tile's rendered width sits within a single bounded range (no tile exceeds the committed tile cap).

### Spacing and density

Complement the horizontal width discipline with vertical discipline: no dead, half-empty screens.

- **Size every section to its content.** Do not stretch a section to a fixed one-screen height that leaves half a viewport empty. Section height follows content, not a slide grid.
- **Use a consistent vertical rhythm** from the committed spacing token, not large unmotivated gaps between blocks.
- **Compact or pair sparse sections.** A section with a single chart or a short list either gets a deliberately compact band or is paired with an adjacent related element (its caption, a stat, the source figure, a related image) rather than floating alone in whitespace.
- **Reserve generous whitespace for intentional emphasis** (a hero, a section transition), never as the page-wide default that produces the empty look.
- **Dead-space ceiling around image bands.** An image band's surrounding empty area should not exceed a stated fraction of the band (roughly `<= 30%` whitespace); a sparse image section is paired or compacted per the rules above rather than floated alone in a mostly-empty band. Metric: the empty area within an image band over the band area stays at or below ~0.3 at 100% zoom.

This is the vertical partner to "use the viewport width on purpose": decide density per section, and let content, not a fixed slide frame, set the height.

### Output aspect (the canvas)

The output aspect is one of the four high-level design choices resolved TOGETHER in a single batched round UP FRONT, before extraction (a named `--layout` binds and drops it from the round; otherwise it is offered as part of that batch; see the command and SKILL.md's Step 2). It governs the page's CSS canvas and composes WITH the per-element width discipline and the design tokens - it never overrides them. Record the resolved aspect (and whether it was auto-picked) in the design-record HTML comment.

Four options, mirroring the style menu:

- **Full-width** - a true edge-to-edge canvas that fills the viewport natively, with no global zoom. It is a concrete, measurable contract, not a vibe:

    - **Page shell**: the shell spans the viewport. Use `--page-max: 100%` (or a very large cap such as `120rem`, and only when the content is genuinely sparse) plus named side-gutter tokens (`--gutter: clamp(1.5rem, 4vw, 5rem)`). It is NOT a fixed centered `max-width` column.
    - **Full-bleed bands**: top-level section bands, heroes, and section backgrounds are full-bleed (they span `100vw`), and the content zones inside them use multi-column or wide grids.
    - **Per-element measure (load-bearing)**: the 45-85ch reading `--measure` is set PER LONG-FORM-PROSE ELEMENT only. It MUST NOT be applied to the page wrapper, to headings, to hero / display text, to charts, to tables, or to image bands. Applying it to the wrapper is what produces the narrow-column defect.
    - **Success metric (verification and the Phase 5 gate)**: at a 1920px viewport, the widest top-level content band's rendered width is at least ~95% of the viewport width (after subtracting the defined gutters), and NO global zoom, `transform: scale()`, or `zoom` is used to simulate width.

    Best for deck-like sources.
- **Standard** - a typical centered webpage column (`max-width` about 72-90rem, centered, comfortable side margins). Sections stack in a readable central measure with occasional wider break-outs for charts / tables. Best for reports and repositories.
- **Portrait** - a tall, narrow, reading- / mobile-oriented canvas (`max-width` about 40-52rem). Single-column, strong vertical rhythm, large tap targets; charts and tables scroll within their own container rather than forcing the page wide. Best for long-form reading and phone-first delivery.
- **Other** - a caller description (equivalent to `--layout <description>`); interpret it into concrete canvas decisions and record them.

**Failure to avoid (full-width):** a narrow centered column with large empty side margins that only looks right at 200% browser zoom is the exact defect this contract prevents. If the reader has to zoom the browser to fill the screen, the page is not full-width.

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

### Interactivity spectrum (restrained / balanced / rich)

The interactivity level is one of the four high-level design choices resolved TOGETHER in the single up-front batched round, before extraction (`--interactivity` binds it; otherwise it is offered as part of that batch; see the command and SKILL.md's Step 2), and it selects HOW MUCH of the layer above is in play. The three levels are a spectrum from a credible, journalistic-report stillness to a full scrollytelling narrative. All three honor the same non-negotiables: offline / no-CDN, keyboard-accessible, and reduced-motion-guarded.

- **RESTRAINED** - user-initiated interaction only. In play: pattern 3 (hover + focus affordances), pattern 6 (expand / collapse), anchor navigation with active-state tracking (a non-animated highlight, not scroll-triggered motion), pattern 5 (the image lightbox), chart readouts, and click-toggle legends. NOT in play: pattern 1 scroll-triggered reveals, pattern 4 scroll-fired counters, and every scrollytelling pattern below. This is the credible end for a report or a white paper, where scroll-driven movement reads as gimmicky. Observable criterion: scrolling the page produces NO content motion; every animation is the direct result of a click, hover, focus, or keypress. It still satisfies the five budget POINTS - point 2 ("scroll-triggered reveals OR an equivalent scroll-responsive treatment") is met by the active-state nav highlight with content always visible, and point 5's signature interaction is a user-initiated one (an accordion, a filterable grid, a click-toggle).
- **BALANCED** - the current minimum interaction budget, unchanged. Adds pattern 1 (scroll-triggered reveals), pattern 2 (active-section nav tracking, optional reading-progress bar), pattern 4 (animated counters), pattern 5 (lightbox), and pattern 7 (micro-transitions). Observable criterion: sections reveal on scroll, the nav tracks the active section, and at least one signature move is present. This is the default for a deck or a data story.
- **RICH** - scrollytelling. Everything BALANCED ships, plus at least one pattern from the scrollytelling catalog below (a pinned / sticky graphic sequence, a full-bleed image-to-text transition, parallax layers, a progress-driven timeline, or a before / after slider). Observable criterion: at least one pinned / sticky-graphic sequence OR a progress-driven scroll narrative is present on top of the balanced layer. RICH still honors the offline / no-CDN / reduced-motion guarantees: under `prefers-reduced-motion: reduce`, every scrollytelling effect degrades to a static, linearly-readable form (below), so a rich page and a restrained page are nearly indistinguishable for a reduced-motion user - by design.

- **CINEMATIC** (v3.16.5, opt-in) - a scroll-scrubbed stage. Everything RICH ships, plus scroll drives a continuous camera movement through the document's own sections rather than triggering discrete reveals: page scroll maps to a clip's `currentTime`, sections chain with frame-accurate seams, and each section can hold a `linger` so its copy is readable instead of sliding past. It is a SPECIALIZATION of RICH, not a replacement - interactive charts stay interactive and the five-point minimum interaction budget still applies in full, so a cinematic page that shipped a static chart has failed the budget rather than transcended it.

    Two surfacing paths and no others: an explicit choice (`--interactivity cinematic`, or the fourth option in the up-front interactivity menu), or a CONFIRMED proposal under `rich` - after extraction, when the content genuinely suits a continuous fly-through (a strong linear narrative, a journey / place / product structure), the agent may propose scroll-scrub as the run's signature scrollytelling pattern, present the size / cost estimate, and get a yes or no. Never silently auto-picked, and never selected in a headless or non-interactive run.

    Cinematic carries a size / cost gate the other levels do not, because its assets are the largest thing this skill embeds and the output must stay one offline file. State clip count, projected base64 size impact, key requirements, and QA-depth cost, then get a go / no-go BEFORE generating or embedding anything. The full protocol - the asset boundary (no hosted generation, ever), the seam rule, the pacing knobs, the stills-only fallback, and the accessibility floor - is `references/scroll-scrub.md`; the engine implementing it is `assets/scroll-scrub-engine.js`.

Mapping summary: RESTRAINED = user-initiated patterns (3, 6, lightbox, anchor nav) with no scroll motion; BALANCED = RESTRAINED plus scroll-triggered patterns (1, 2, 4, 7); RICH = BALANCED plus one or more scrollytelling patterns; CINEMATIC = RICH plus the scroll-scrubbed stage, opt-in and size-gated. The non-interactive fallback picks the level from the content (a deck or data story -> BALANCED; a report -> RESTRAINED) and records it in the design-record comment. In slide mode (`nav=slides`), every scroll-keyed pattern each level ships is re-expressed per the "Slide-mode animation grammar" below; RESTRAINED needs no adaptation.

### Scrollytelling pattern catalog (RICH level)

Each pattern is inlined vanilla JS / CSS - no external library, no CDN - and each carries an accessibility note. The unifying rule: content is NEVER gated behind JS or behind the scroll effect, and every effect has a static, linearly-readable fallback under `prefers-reduced-motion: reduce`.

1. **Pinned / sticky graphic with scroll steps** - a media column that stays fixed (`position: sticky; top: 0`) while a column of text "steps" scrolls past it; an `IntersectionObserver` on each step swaps the pinned graphic's state (a highlighted data series, a map layer, a zoom level). Sketch:

    ```js
    const steps = document.querySelectorAll('.step');
    const obs = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) setGraphicState(e.target.dataset.state);
    }), {rootMargin: '-45% 0px -45% 0px'});  // fire near viewport middle
    steps.forEach(s => obs.observe(s));
    ```

    Accessibility: each step is real, self-contained prose (the sequence reads linearly with the graphic absent); the pinned graphic carries a text alternative for its final / most-complete state; under reduced motion, drop the pinning (the graphic renders inline once at its most-complete state and the steps read as an ordinary list).

2. **Full-bleed image-to-text transition** - a full-viewport image that cross-fades or scales into the following text block as it scrolls out. Implement with a sticky image layer whose `opacity` / `transform` is driven by the section's scroll progress (an `IntersectionObserver` threshold list, or a `requestAnimationFrame`-throttled `scroll` read of the section's bounding rect). Accessibility: the image is either decorative (`alt=""`, `aria-hidden`) or carries real `alt`; the following text is present and readable regardless of the transition; under reduced motion the image simply ends, then the text begins (no cross-fade).

3. **Parallax layers** - a background layer translates slower than the foreground for depth. Drive `transform: translate3d(0, <offset>, 0)` from scroll position, throttled with `requestAnimationFrame`; set `will-change: transform` only on the moving layer and only while it is on screen. Sketch:

    ```js
    let ticking = false;
    addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        layer.style.transform = `translate3d(0, ${scrollY * 0.3}px, 0)`;
        ticking = false;
      });
    });
    ```

    Accessibility: parallax is a known vestibular-motion trigger, so DISABLE it entirely under `prefers-reduced-motion: reduce` (guard the listener behind the media query and leave the layer static) - do not merely shorten it; never parallax text the reader must follow, only decorative background layers.

4. **Progress-driven timeline** - a vertical timeline whose active node tracks the scroll position (an `IntersectionObserver` per node setting an `.active` state) with a progress line that fills via a `requestAnimationFrame`-throttled scroll read. Accessibility: the timeline is a real ordered list (`<ol>`) that reads top-to-bottom without JS; the fill line is `aria-hidden` (decorative); the active node also sets `aria-current="step"`.

5. **Before / after comparison slider** - two stacked images with a draggable divider driven by a native `<input type="range">`; the top image is revealed by a `clip-path: inset(0 <100 - value>% 0 0)` bound to the input value. Sketch:

    ```html
    <div class="ba"><img class="after" ...><img class="before" ...>
      <input type="range" min="0" max="100" value="50" aria-label="Reveal before/after">
    </div>
    ```

    ```js
    range.addEventListener('input', () => {
      before.style.clipPath = `inset(0 ${100 - range.value}% 0 0)`;
    });
    ```

    Accessibility: the range input is keyboard-operable (arrow keys move the divider) and labelled; both images carry `alt`; the comparison works without a pointer and needs no motion guard (it is user-driven, not scroll-driven).

### Slide-mode animation grammar (nav=slides)

When the design record says `nav=slides`, there is no scroll, so every scroll-keyed pattern above must be re-expressed. This grammar is the normative mapping. RESTRAINED needs no adaptation in slide mode - it never had scroll-triggered motion, and its user-initiated patterns work identically on a slide. BALANCED, RICH, and CINEMATIC use the three trigger classes below. The slide runtime, fragment contract, and reduced-motion baseline these classes plug into are `references/slide-navigation.md`.

Three slide-native trigger classes, and only three - an author never invents a fourth:

1. **Entry-triggered (once per activation)** - replaces scroll-triggered reveals and animated counters: the effect runs when its slide becomes active. Counters count up on FIRST activation; a re-activated slide shows final values immediately, because a re-run of a numeric build can misread as new data arriving. The general re-entry rule (BINARY): an entry-triggered effect may re-run on re-activation only if it is idempotent AND non-data-bearing (a fade may re-run; anything numeric or chart-shaped runs once per session and thereafter renders settled).
2. **Fragment-stepped** - replaces every progress-driven pattern: each discrete state becomes a `data-fragment` step advanced by arrow keys per the slide-navigation fragment contract (ordered reveal, backward re-hide, idempotent under deep entry). The scrollytelling STATE TABLE requirement carries over UNCHANGED: each step still declares its prose claim, its visual change, and its takeaway - the trigger moved from scroll progress to a keystroke, the narrative discipline did not.
3. **Ambient loop (permanent)** - replaces atmosphere-class scroll animation ONLY: moving background illustrations, parallax texture layers, gradient drift, particle fields, slow procedural motion. These become smooth, seamless, infinitely-repeating CSS/JS animations that run while their slide is active, PAUSE when the slide is inactive (`animation-play-state: paused`, or the loop's rAF gated on the active class - an off-screen loop burns battery for nobody), and are DISABLED entirely under `prefers-reduced-motion: reduce` - removed, not slowed.

The appropriateness rule for class 3 is BINARY: ambient conversion applies ONLY to non-data-bearing, non-narrative animation. A chart build, a numeric transition, or any effect whose motion carries MEANING must be class 1 or 2, never a loop - looping data motion fabricates the impression of live data. Amplitude discipline: ambient loops are subtle (background-layer opacity/position drift), never foreground distraction, and at most ONE ambient system runs per slide.

The mapping table. Every pattern named in this reference has a row; none is left to judgment:

| Scroll-keyed pattern (source) | Slide-mode expression | Class |
|---|---|---|
| Scroll-triggered reveal (pattern 1) | Runs on slide activation; multi-part reveals become fragments | Entry-triggered |
| Active-section nav + reading-progress bar (pattern 2) | The progress rail + slide counter ARE the nav; the active rail segment is the active state | (chrome, per the slide-navigation contract - no animation to adapt) |
| Animated counters (pattern 4) | Count up on first activation; final values on re-entry | Entry-triggered |
| Hover / focus affordances (pattern 3) | Unchanged - they are user-initiated | (none needed) |
| Expand / collapse (pattern 6) | Unchanged in trigger, but bounded by the overflow rule: expansion that would overflow the stage becomes a declared scrollable region or splits into a fragment/continuation - never an undeclared inner scrollbar | (none needed; overflow rule applies) |
| Micro-transitions (pattern 7) | Unchanged - they are user-initiated | (none needed) |
| Image lightbox (pattern 5 of the budget) | Unchanged | (none needed) |
| Pinned / sticky graphic with scroll steps (catalog 1) | Each step's graphic state becomes one fragment; the graphic swaps state per keystroke | Fragment-stepped |
| Full-bleed image-to-text transition (catalog 2) | The image is one fragment state, the text the next - or a single entry-triggered cross-fade when the pair is not narratively staged | Fragment-stepped or entry-triggered |
| Parallax layers (catalog 3) | Background-layer drift as a slow seamless loop, active-slide only | Ambient loop |
| Progress-driven timeline (catalog 4) | Each node is one fragment; `aria-current` moves per keystroke | Fragment-stepped |
| Before / after comparison slider (catalog 5) | Unchanged - user-initiated patterns need no adaptation | (none needed) |
| Marquee / atmospheric texture (any decorative drifting layer) | Slow seamless loop, background amplitude, active-slide only | Ambient loop |
| Scroll-scrubbed stage (CINEMATIC) | Fragment-stepped camera with ambient hold states - the full protocol is the "Cinematic without scroll" section of `references/scroll-scrub.md` | Fragment-stepped + ambient |

Fallback rule (BINARY): a pattern with no row above defaults to **entry-triggered-once** - the safest expression, the one that can never fabricate data or loop a narrative - and the design record notes the pattern and the fallback. The author never invents a fourth trigger class for it.

Reduced motion in slide mode, restated as one rule set: ambient loops are DISABLED entirely (not slowed), fragment transitions become instant cuts, and entry-triggered reveals render visible-immediately. A reduced-motion slide deck is a sequence of settled, fully-legible stages - by design, the same posture as the scrolling page.

### Design direction (choose the direction up front, then brainstorm after extraction - creativity-first)

The design DIRECTION is chosen up front, as one of the four batched design choices resolved before extraction; the concrete-token brainstorm below then runs after the content is extracted. The goal each run is a UNIQUE, creative, interactive design; "fit the document type" is never the rule. "Be unique" is not enough on its own either: the agent has a strong default attractor it returns to unless forced off it, and that sameness is what makes a run read as AI-generated. Make this a real, deliberate stage, not an afterthought during authoring.

**Resolve the direction in order.**

1. **A named style binds.** When `--style` words (or the natural `using the style <description>` phrasing), a `[[theme-tokens]]` set, or a `[[brand-styling]]` brand `tokens.json` is supplied, that is the binding direction: honor it instead of offering the menu (a partial `--style` still leaves the unspecified axes to brainstorm). Ask the user for brand tokens before inventing a brand's colors.
2. **Otherwise, offer the design-direction choice as part of the up-front batch.** With no style named, ask the user to choose it together with the other three choices (output aspect, interactivity, imagery) in the single batched round before extraction:
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

### Scrollytelling pattern: the scroll-scrubbed stage (CINEMATIC only)

A sticky viewport behind the section copy, in which scroll position drives a clip's playhead rather than a CSS transition. The reader scrolls and the camera moves continuously; the copy sits above the stage and remains linearly readable.

- **Offline and single-file, or not at all.** Clips load from `data:` URIs or Blob object URLs so the authored `.html` stays ONE file. HTTP byte-range serving of sibling `.mp4` files is explicitly not the primary path - a page that needs `clip-01.mp4` beside it is not a self-contained output, and the offline guarantee is the whole point of this skill's output contract.
- **Stills-only is the BASE mode; video is the enhancement.** Under `prefers-reduced-motion: reduce` the engine creates no video element at all - not created-and-paused, not created-muted: not created - and scroll drives a still cross-dissolve plus a gentle scale. Built in that direction because a reduced-motion path added afterwards is the one that regresses.
- **Accessibility floor**: the stage is `aria-hidden` decorative, the section copy lives outside it and reads in order, anchor jumps land correctly with `scroll-margin-top` applying as everywhere else, and no control is scroll-only.
- **Pacing**: per-section `scroll` (how much page distance the section consumes) and `linger` (a mid-scene hold where progress advances but the clip barely moves, so the copy can be read).
- **Mobile**: scroll events are coalesced onto one animation frame and superseded seeks are dropped rather than queued, because a touch device fires scroll far faster than a video can seek; clips are primed once on first touch, since iOS refuses a programmatic seek before user interaction.

Cost caution: this is the most expensive pattern in the catalog in bytes and in reader tolerance. It is reachable only through the CINEMATIC level's opt-in and its size / cost gate.

## Imagery tiers (procedural / stock / AI)

Imagery is what turns a well-typeset reflow into a designed, journalistic web story - but MOST of the professional look needs no external image at all. It is typography, layout, color, restraint, and original inline SVG / CSS. That is why Tier 1 is both the always-on default and a large share of the value. The three tiers are resolved by the imagery question (`--images`, or the menu):

- **Tier 1 - procedural visuals** - original inline SVG / CSS. The zero-outbound default and the non-interactive fallback.
- **Tier 2 - license-free stock** (opt-in, consent-gated for the build-time fetch) - openly-licensed images / video, base64-embedded.
- **Tier 3 - local AI-generated images** (opt-in) - a LOCAL commercially-clean model; no hosted service.

The offline guarantee is absolute across all three: EVERY visual - procedural, stock, or AI - is emitted as inline SVG / CSS or a base64 `data:` URI. Any fetch or generation happens ONLY at authoring (build) time; nothing external is referenced from the delivered HTML. The default run, and every non-interactive / headless run, uses Tier 1 only - there is no silent outbound path.

**Priority among the non-default tiers (stock-first, minimize AI).** When the user opts BEYOND procedural, PREFER real, license-free, free-for-commercial-use STOCK media (Tier 2) whose relevance is derived from the content (per-section / topic keywords), and MINIMIZE AI-generated images. Tier 3 (local AI) remains offered but is the LAST RESORT: reach for it only when relevant stock cannot be found for a placement, or the user explicitly asks for AI. This is a priority ORDER among the non-default tiers, not a change to the default - Tier 1 procedural stays the always-on default and the non-interactive fallback, and the offline / consent-gated guarantees are unchanged. Rationale: real commercial-free stock is provably licensed and content-relevant, while AI output may not be copyrightable (see Tier 3) and reads as generic; prefer the real photograph over the synthesized one whenever a relevant, license-clean asset exists.

### Tier 1 - procedural visuals (default)

The agent authors ORIGINAL visuals, inlined as SVG / CSS, with no external asset and no CDN. This is the default imagery tier and the non-interactive fallback, and it is commercial-safe BY CONSTRUCTION (original work) and fully offline. See `[[generative-art]]` for the procedural / generative vocabulary and `[[ui-component-generation]]` for authoring UI visuals directly with the agent's own output rather than fetching them.

The procedural vocabulary:

- **Backgrounds**: full-bleed color fields and gradient / mesh backgrounds behind hero and section text.
- **Dividers**: duotone / halftone treatments and rule-line motifs as section transitions.
- **Editorial devices**: rule lines, drop caps, pull-quotes, and big callout numbers.
- **Textures and illustrations**: generative textures and simple thematic illustrations (geometric, line-art, or a data-motif) tuned to the content's subject and the committed palette.

The rules that keep Tier 1 safe and coherent:

- **Decorative or supportive, never load-bearing.** A procedural visual never carries information the text does not, so the page stays complete under reduced contrast, monochrome, or print. Anything that conveys data is a chart (per "Dynamic, manipulable charts"), not a background.
- **Contrast stays within the accessibility gate.** A background field or gradient must keep body and heading text contrast within the `[[hallmark-design]]` accessibility gate; darken / lighten or add a scrim rather than let a gradient wash out text.
- **Token coherence.** Every procedural visual follows the committed design tokens (palette, type scale, motion signature) so the visuals and the type read as one system, not as bolted-on decoration.
- **Content-relevant, not cliche.** Motifs match the subject: a clinical topic gets restrained clinical / data motifs, not a stock-photo cliche; a launch gets bolder generative texture. Relevance beats ornament.

Tier 1 is the zero-outbound default: it needs no network, no dependency, and no credential, and it is what every non-interactive run ships.

### Tier 2 - license-free stock (opt-in, consent-gated)

When the user picks the `stock` imagery tier AND consents to the build-time network use, the authoring stage derives short relevance keywords from the content (per section / topic) and runs the bundled helper `scripts/fetch_stock_media.py` to fetch openly-licensed, free-for-commercial-use images / video, verify each license, capture attribution, and base64-embed the result. The output still opens offline with zero external requests: the fetch happens ONLY at build time and every asset is inlined as a `data:` URI. This tier is NEVER the default and NEVER runs in a non-interactive / headless run.

**Image-starved-section detection (where to fetch).** A consented `stock` / `mix` run does not scatter decoration; it targets the sections that actually need an image. After the structure is drafted, run a detection pass:

- **Identify the starved sections.** A section is image-starved when it carries NO source visual (no extracted image, chart, or reconstructed figure) AND would be materially clearer with one, meaning it has a concrete subject a relevant photograph or illustration would support (a place, an object, a process, a domain). A section already carrying a source figure, a pure-data / chart section, and a section with no concrete visual subject (an abstract summary, a table of numbers) are NOT starved and get no fetched image.
- **Derive per-section keywords.** For each starved section, derive SHORT relevance keywords from the section's TOPIC (its heading and gist), never from the raw source document text: two to four words that name the subject (for example "coastal wind turbines", "microscope laboratory"). Routing only short content-derived keywords, never the document, is what keeps the compiling-content trap (below) closed.
- **Fetch one relevant asset per starved section.** Run `scripts/fetch_stock_media.py --consent` per starved section (Openverse-first, then Wikimedia; Pexels when a key is configured), take ONE highly-relevant, license-verified asset, and place it per the Phase 2 prominence + sizing rules (it is an accent, not a hero, unless the section genuinely centers on it). Prefer CC0 / public-domain. Record provenance + credits per "Visual provenance and credits".
- **Relevance and restraint.** Integrate an asset ONLY when it is genuinely relevant and helpful; a loosely-related or purely decorative stock photo is worse than none because it reads as filler. Skipping a section for lack of a relevant, license-clean asset is a valid outcome; record the per-section reason (see the gate below).

### Placement roles (what an image is FOR, v3.16.5 Phase 5)

Detecting that a section is starved says an image would help; it does not say what the image is DOING there. Every placement carries one of four roles, and the role determines the sizing, the treatment, and what "correct" looks like:

| Role | What it is | Treatment |
|---|---|---|
| **hero / header** | A section-opening full-bleed or wide visual that sets the section's subject | Full-bleed band or wide column; respects the Phase 2 prominence rules (a hero is a hero because the CONTENT centers on it, not because a hero looks impressive) |
| **background** | A low-contrast treated backdrop behind a band, with text over it | MUST carry the ink-contrast overlay recipe below; the text's AA contrast is measured against the composited result, not against the overlay color |
| **contextual illustration** | A figure beside prose it concretely depicts | Sized as an accent next to its prose, never competing with a real source figure in the same section |
| **gallery** | Genuinely-secondary visuals grouped for legibility | The existing secondary-grouping rule; a gallery is where non-dominant visuals go, and it is never a place to hide a dominant one |

**The background overlay recipe (mandatory for the background role).** Text over an image is the easiest way to ship unreadable type, and it fails differently in every image, so the overlay is not optional and not eyeballed. Composite a solid scrim between the image and the text, then verify the text's contrast against the SCRIM color rather than against the image:

```css
.band-bg{ position: relative; isolation: isolate; }
.band-bg > img{
  position: absolute; inset: 0; width: 100%; height: 100%;
  object-fit: cover; z-index: -2;
}
.band-bg::before{                     /* the scrim - an opaque-enough known color */
  content: ""; position: absolute; inset: 0; z-index: -1;
  background: color-mix(in srgb, var(--base) 82%, transparent);
}
```

At 82% the composited background is within a couple of percent of `--base`, so the existing `contrast` check on `--ink` against `--base` remains valid. Drop below roughly 75% and it no longer is: the image starts showing through enough to move the effective background per-pixel, and no static check can certify the text any more. If a design genuinely needs a lighter scrim, the text must move off the image instead.

**Deciding placements (inside the render loop, not before it).** The placement pass runs during the Phase 3 loop's FIRST iteration, because that is the first point at which the page can be seen: a section that looked starved in the model may already read as full, and a band that looked fine may be visibly empty. For EVERY section, produce one of two outcomes - never silence:

- **A placement**: its role, and one line on why THIS content benefits from an image in THAT role.
- **An explicit decline**: `no image: <reason>`. "The section has no concrete visual subject" and "no license-clean asset depicted the subject" are both complete reasons. A decline is a valid, common, and often correct outcome.

**Check relevance BEFORE embedding.** For each candidate, ask whether the image actually depicts the section's subject. A generic techy stock photo next to a section about test coverage does not depict test coverage; it depicts a stock photo. Reject it. Re-query ONCE with tightened keywords, then drop the placement with its reason rather than embedding filler - a loosely-related image is worse than none, because it reads as padding and teaches the reader to skip images.

**Record every decision in the design record**, in a parseable block so the deterministic checker can verify the record against the page rather than trusting it:

```
IMAGERY PLACEMENTS
  placement: intro | hero | embedded | the section opens on the coastline the report surveys
  placement: method | background | embedded | a laboratory backdrop; scrim at 82% keeps body text AA
  placement: results | contextual | embedded | the apparatus the paragraph describes
  placement: summary | none: no concrete visual subject - it summarises the three sections above
  placement: appendix | none: no license-clean asset depicted the subject after one re-query
```

One `placement:` line per section, `|`-separated, with `embedded` or `none: <reason>` in the status field. `scripts/visual_qa_score.py` reads this block: a consented run with NO block at all means the pass never ran, and a block claiming more embedded assets than the page actually contains means the record is fabricated. Both are HIGH-severity findings.

All existing invariants apply unchanged: consent still gates every fetch, the commercial-use allow-list still fails safe, every asset is still base64-embedded, and every non-original visual still appears in the visible "Image credits" section with its license and attribution.

**Integration gate (a consented run must not silently add nothing).** A consented `stock` / `mix` / `ai` run MUST, for EACH image-starved section, either integrate at least one relevant, license-verified asset OR record a per-section reason (no relevant license-clean asset found, or the section did not warrant an image). A consented stock / mix run that produced ZERO integrated assets across all starved sections with NO recorded reason FAILS verification: that silent zero-integration is the exact defect this tier exists to prevent (the fetch helper always records a degrade reason, so a "no reason" state is itself the bug). The offline and license-safety gates are unchanged: every asset stays base64-embedded, the commercial-use allow-list still fails safe, and a non-commercial asset is never embedded. `mix` = a procedural base plus real stock accents FIRST, and local AI (Tier 3) only where stock cannot serve a placement (the unchanged priority).

The consent gate is the load-bearing invariant. `fetch_stock_media.py` performs NO network call unless `--consent` is passed; without it, it prints a notice, writes an empty degraded manifest, and exits with the degrade code (3), and the authoring stage stays on Tier 1. The helper also degrades (never raises) on a missing library, a missing API key, a network error, or zero results.

Sources (the helper queries one `--source`, Openverse by default):

- **Openverse** (default, keyless) - a CC / public-domain aggregator with per-file license metadata. The primary source.
- **Wikimedia Commons** (keyless) - per-file CC / PD license read from the file's `extmetadata`.
- **Pexels** (needs `PEXELS_API_KEY` in the environment, never hardcoded; absent key => the source is skipped) - a blanket-license platform.
- **Coverr / Mixkit** - accepted on the CLI for interface parity, but this helper has no keyless search API for them, so they degrade with a note. Prefer Openverse / Wikimedia; a video need is best served by a configured Pexels key.

**Stock video (Pexels-only, gated).** Video is offered when the `stock` (or mix) tier is chosen, but it is gated more tightly than images: `fetch_stock_media.py --kind video` runs only with explicit build-time `--consent`, and video specifically requires `--source pexels` and a Pexels key resolved by `_resolve_pexels_key` (the `PEXELS_API_KEY` environment variable, or `~/.nexus-hub/config/media.env`) - Openverse and Wikimedia have NO license-clean keyless video path (the helper raises for them, pointing the pipeline at Pexels, then degrades). When the key, the consent, or a relevant result is absent, the run DEGRADES to images-only (or Tier 1) with a one-line note - it never blocks and never hotlinks (every clip is base64-embedded like any other asset, and the `https`-only SSRF guard applies). Size caution: a base64-embedded clip is heavy, so stock video counts against the media budget and is reserved for a SMALL number of genuinely high-value placements (a hero loop, one section accent), never a page of autoplaying clips; keep each clip short and muted and honor `prefers-reduced-motion`.

**First-time video setup (bring-your-own-key).** Stock IMAGES work with zero setup (Openverse is keyless), so this guidance NEVER fires for an images-only choice. Stock VIDEO needs a free Pexels key, and we cannot auto-provision one (a Pexels key is tied to the user's own free account; shipping a shared embedded key is a terms-of-service violation and a secret-handling hazard). So the FIRST time the resolved imagery tier includes video and no key is found (neither `PEXELS_API_KEY` nor `~/.nexus-hub/config/media.env`), give a ONE-LINE note that stock images need no setup but stock video needs a free Pexels key, and ask the user to run `nexus-hub setup-media` in their TERMINAL - a guided, hidden-input, one-time setup that stores the key securely. Do NOT ask the user to paste the key into the chat: that would record the secret in the transcript; the terminal helper keeps it local. The run does NOT block - it proceeds with stock images and/or procedural visuals and notes that video was skipped pending the key, so the user can re-run for video after setup. A stored key does NOT bypass consent: both the key AND explicit build-time consent are still required before any fetch.

Per-source license rules (encoded in the helper, enforced before any asset is embedded):

- **Openverse / Wikimedia (CC / PD per file)**: keep the license id and, for **CC-BY / CC-BY-SA**, build the required attribution string (title, author, license label, source name). **CC0 / Public Domain Mark** need no attribution but are still credited for auditability.
- **Pexels / Coverr / Mixkit (blanket license)**: commercial use is allowed with no per-asset attribution required, but the asset still gets a source credit.

The commercial-use gate is an allow-list, so it fails safe: only `cc0`, `pdm`, `by`, `by-sa` (plus the blanket-license sources) pass; ANY code carrying a NonCommercial (`nc`) or NoDerivatives (`nd`) term is rejected, and any unrecognized license is skipped with a noted reason. A non-commercial asset is never embedded.

The compiling-content trap (why CC0 / PD is preferred): the custom licenses of Unsplash, Pexels, and Pixabay permit commercial use of individual assets but restrict "compiling photos to replicate a similar or competing service". Presentify embeds a few content-relevant assets into a single delivered page; it is NOT a stock-media service, routes only short content-derived keywords (never the source document), and never redistributes a media library. Prefer CC0 / public-domain from Openverse / Wikimedia, and never present the tool as a stock-image service. Per the Attribution Rule, source names appear only in the credits, as a licensing necessity.

Keeping attribution offline-clean: the visible "Image credits" section carries the human-readable attribution (title, author, license label, source name) with NO raw `http(s)` URL, so the delivered HTML still passes the offline external-reference self-check; the asset URL and license URL live in the adjacent HTML comment and in the credits manifest (both machine-readable, both outside the grep). The helper emits its manifest as an array of credit entries (the `assets` array), which is exactly the credits-manifest shape the "Visual provenance and credits" convention below consumes: the authoring stage renders the "Image credits" section from it and drops each adjacent comment.

### Tier 3 - local AI-generated images (opt-in, local-only)

When the user picks the `ai` imagery tier, the authoring stage builds a prompt from the content and the committed style tokens (subject, mood, palette) and runs the bundled helper `scripts/generate_local_image.py` to generate an original image with a LOCAL model runtime, base64-embed it, and record the model + license + copyright caveat. The output still opens offline with zero external requests.

The hard constraint is LOCAL generation only. A third-party generation API (DALL-E, Midjourney, hosted Stable Diffusion, FLUX Pro, ...) is OUT OF SCOPE by policy - generation-as-service is a hard-no on the MCP / capability policy. The helper makes NO network call and imports no hosted-API client; it forces the model runtime into offline mode BEFORE importing it, so a missing runtime or missing weights degrades to a setup hint rather than triggering an implicit weight download. Model weights are obtained by the user out-of-band; the script never downloads them.

Models and runtimes:

- **Models** (commercially-clean, locally runnable): FLUX.1 schnell (Apache-2.0, the default) or SDXL base (CreativeML Open RAIL++-M). A model whose license is not free-for-commercial-use is rejected.
- **Runtimes** (either, both optional and opt-in): `diffusers` + `torch` (loaded with `local_files_only=True` and `HF_HUB_OFFLINE=1` so no download is attempted), or a user-configured LOCAL CLI via `NEXUS_LOCAL_IMAGE_CMD` (run via subprocess, never a shell; declare its model license via `NEXUS_LOCAL_IMAGE_LICENSE`).

The heavy dependency is opt-in: when no local runtime or weights are present, the helper prints a setup hint and degrades to Tier 1 - it never raises and never falls back to a hosted API.

Copyright caveat: purely AI-generated output may not be copyrightable. The helper records `note: "AI-generated; may not be copyrightable"` in each asset's provenance, and the credits section surfaces the model, its license, and this caveat. Like Tier 2, the helper emits the `assets` array credits-manifest shape the "Visual provenance and credits" convention below consumes.

### Visual provenance and credits

Every visual added to the output carries PROVENANCE, and every non-original visual is CREDITED. This one convention serves all three tiers, so licensing is auditable and attribution is always present when a license requires it. It is the shared contract the Tier 2 and Tier 3 helpers emit into and the verification step reconciles against.

Per-tier provenance:

- **Tier 1 (procedural)**: `original (generated)` - authored by the agent, no external source.
- **Tier 2 (stock)**: the source name, the asset URL, the license id (e.g. `CC0`, `CC-BY-4.0`, `Pexels License`), the license URL, and the author / attribution text.
- **Tier 3 (AI)**: the model name, the model license (e.g. `Apache-2.0`, `Open-RAIL-M`), and the note `AI-generated; may not be copyrightable`.

Provenance is recorded in TWO places:

1. **An HTML comment adjacent to the visual**, so the source of any single visual is greppable in place. Use a one-line `credit:` JSON object (below) immediately before the visual's element.
2. **A visible "Image credits" section near the end of the output**, listing every NON-ORIGINAL asset with its license and attribution. CC-BY / CC-BY-SA assets MUST show the full attribution string here (it is a license requirement); CC0 / public-domain / no-attribution assets are still listed for auditability. On a Tier-1-only page there is nothing to attribute, so the section states that all visuals are original (generated).

The credits data shape (one entry per visual; the adjacent comment carries one object, the credits section renders the array):

```json
{
  "tier": "procedural | stock | ai",
  "provenance": "original (generated)",           // tier 1 only
  "source": "Openverse",                           // tier 2: aggregator / site name
  "url": "https://.../asset",                      // tier 2: asset page or file URL
  "license": "CC-BY-4.0",                          // tier 2/3: SPDX-like id
  "license_url": "https://creativecommons.org/licenses/by/4.0/",
  "author": "Jane Doe",                            // tier 2: creator
  "title": "Cooling towers at dusk",              // tier 2: asset title
  "attribution": "\"Cooling towers at dusk\" by Jane Doe, CC BY 4.0",  // tier 2: built string, required for CC-BY
  "model": "FLUX.1 schnell",                       // tier 3: model name
  "note": "AI-generated; may not be copyrightable" // tier 3
}
```

The Tier 2 / Tier 3 helper scripts emit a JSON manifest that is an array of these entries (the `credits manifest`); the authoring stage renders the "Image credits" section from it and drops each adjacent comment. This provenance ledger is parallel to, and does not replace, the Step 7 coverage-reconciliation comment (which accounts for SOURCE visuals): coverage reconciliation answers "is every source visual represented?", the credits ledger answers "does every ADDED visual have a free-for-commercial-use license and required attribution?". Verification reconciles the rendered credits section against the adjacent comments: any non-original visual missing from the credits, or any visual with no provenance at all, is a failure.

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

## Two authoring rules from maintainer review (v3.16.5 errata E9)

**Key-value cells render as bullet lists, never comma-run sentences.** A cell describing what a step reads, writes, and outputs is a LIST of facts, and a reader scans it to find one of them. Written as a comma-run sentence it has to be read start to finish to answer any question about it. Give each key its own bullet, and give every one a CONCRETE example value rather than a category name - `docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md` teaches what "a plan file path" does not.

```html
<!-- CORRECT - scannable, with real values -->
<ul>
  <li><b>Reads</b> <code>docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md</code></li>
  <li><b>Writes</b> <code>tests/skills/test_presentify_visual_qa.py</code></li>
  <li><b>Outputs</b> coverage 93% against an 80% threshold</li>
</ul>

<!-- WRONG - a comma-run that must be parsed linearly to answer anything -->
<p>Reads the plan file, writes the test file, and outputs a coverage number.</p>
```

**Interactive-control colors stay NEUTRAL and visually distinct from chart data-series colors.** A slider, input, or toggle painted in a series color reads as part of the data: the reader cannot tell whether an accent-colored handle is a control or a value. Reserve the data-series colors for data, give controls a neutral ink or surface treatment, and use the accent only for focus and active states.

## Attribution

All naming in the template, the builder, and this document is generic and descriptive (per the Reverse-Engineering Attribution Rule): no upstream product, repository, or library brand appears in any distributed artifact. The interactive patterns here are an original, self-contained implementation.
