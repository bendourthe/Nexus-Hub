# Visual-QA Rubric (per-segment grading)

The measurable pass criteria the Step 9 visual-QA loop grades each output segment against, assembled from Phases 1-4 plus baseline readability. It is the single source of truth the loop scores against, the fan-out template (`assets/visual-qa-workflow.js`) fans out over, and the deterministic scorer (`scripts/visual_qa_score.py`) checks.

Two kinds of check run against every segment:

- **STRUCTURAL** - deterministic, checkable from the rendered DOM, the computed CSS, or the markup by `scripts/visual_qa_score.py` (headless-optional). These certify the measurable metrics without a human eye.
- **AGENT-VISION** - a judgment the agent makes by reading a screenshot and comparing it to the SOURCE segment (crop of meaningful content, dead space, annotation placement vs the source, imagery relevance, contrast and legibility). These cannot be certified structurally.

The loop runs BOTH kinds when a headless browser and the agent's vision are available; without a browser it degrades to the STRUCTURAL subset with a one-line note (see the degradation contract below). It never hard-fails on a missing browser.

## Segmenting the page

A "segment" is one top-level content band or section: a slide section, a hero, a figure with its overlay, an image band, or a data section. Grade each segment independently against the applicable criteria, then roll the findings up to the page-level pass bar. Per-segment grading is deliberate: a single whole-page pass misses per-segment defects (a ballooned image in one section, a dropped overlay in another), which is exactly how the four observed defects reached production.

**The regression smoke-set (every iteration, every edit).** Independent of which segments an iteration changed, EVERY re-render pass - including a post-delivery touch-up - captures the fixed smoke-set: the hero at load, one divider (or band transition) mid-scroll, and one interactive chart. Change-local rendering cannot see cross-component damage: a generic CSS class or shared JS hook added for one section can break a section nobody re-looks at, with zero console errors (a map-pin class collision once blanked the entire cinematic hero while the edited map section verified clean). The smoke-set is three screenshots; skip it and the loop's guarantee quietly becomes "the parts I remembered to look at".

## The twelve criteria

Each criterion lists what it checks, the observable metric, the check kind, and the severity of a failure. Criteria 1-5 came from v3.15.4 Phases 1-4; criteria 6-7 grade the `references/responsive-typography.md` contract and criterion 8 the `references/svg-diagram-quality.md` contract, both added in v3.16.5; criterion 9 was added by the v3.16.5 errata after a real render session found three defect classes no contract covered; criterion 10 (v3.16.6) grades the coverage-depth choice the round-2 intake records; criterion 11 (v3.16.7) was added after a class-collision regression blanked a JS-painted stage with zero console errors and a clean structural pass; criterion 12 (v3.18.3) grades the `nav=slides` contract and is N/A on every scrolling page.

1. **Full-width compliance** (Phase 1). When the resolved aspect is full-width, the widest top-level content band's rendered width is at least ~95% of a 1920px viewport (after the defined gutters), and NO global zoom, `transform: scale()`, or `zoom` is used to simulate width. Metric: band width / viewport at or above 0.95. Kind: STRUCTURAL. Severity: HIGH (a full-width run that renders a narrow centered column is the Phase 1 defect). N/A when the resolved aspect is not full-width.
2. **Image sizing** (Phase 2). No image breaks its prominence box: a hero's rendered height stays at or below ~80vh; a low-`page_fraction` secondary renders no wider than its section's hero (no balloon); no meaningful content is cropped (rendered aspect ratio matches the native ratio within ~2%); no image band carries dead space beyond ~30% of the band. Metrics: rendered box vs viewport, aspect-distortion ratio, whitespace fraction. Kind: STRUCTURAL for the caps (the `max-height` and `object-fit: contain` rules are present, the rendered box is within the cap); AGENT-VISION for "meaningful content cropped" and "dead space". Severity: HIGH for a hero filling the whole viewport or a cropped chart axis / labeled region / face; MEDIUM for dead space.
3. **Annotation fidelity** (Phase 3). For an annotated source figure, the built segment reproduces the source's regions and labels as a registered overlay over the base image, not a flat image beside a textual list. Metric: the overlay is present with a region element and a label per source annotation, and a view-original toggle; the placement is compared against the SOURCE figure. Kind: STRUCTURAL for overlay presence, region and label count, and the view-original toggle (from the DOM); AGENT-VISION for placement fidelity vs the source. Severity: HIGH (a dropped overlay demoted to side text is the Phase 3 defect). A LOW-confidence figure that CORRECTLY degraded to the enhanced-original viewer plus a textual complement is a PASS on this criterion, never a fail (the confidence gate did its job).
4. **Imagery integration and placement** (Phase 4, extended by v3.16.5 Phase 5). A consented `stock` / `ai` / `both` run made a PLACEMENT DECISION for every section - a role plus a reason, or an explicit decline with a reason - and integrated a relevant, license-verified asset for each placement it kept. Metrics, per segment: (a) every proposed placement got its asset OR carries a recorded reason; (b) each embedded asset is contextually RELEVANT to the section's actual copy - does the image depict the subject, or is it a generic stock photo standing in for one?; (c) a `background` placement keeps its overlaid text at AA contrast, measured against the composited scrim (the recipe in `references/interactive-features.md` mandates a scrim at or above ~82% so the static `contrast` check stays valid; below ~75% no static check can certify the text and it must move off the image); (d) a `hero` placement earns its prominence from the CONTENT centring on it, not from a hero looking impressive. Kind: STRUCTURAL for the embedded-asset count and for the record's integrity - the deterministic checker reads the `IMAGERY PLACEMENTS` block and fails a page that has assets but no block (the pass left no decision trail), a record claiming more embedded assets than the page contains (the record does not match the page), or a decline with no reason; AGENT-VISION for relevance, for the composited contrast over a background image, and for whether a hero deserves to be one. Severity: HIGH for silent zero-integration, a missing decision trail, or a record that contradicts the page; MEDIUM for a loosely-relevant asset or an unexplained decline. N/A for a `none` / non-consented / non-interactive run (those stay on the procedural baseline by design, and emit no placement pass).
5. **Readability and layout integrity** (at 100% zoom). No horizontal page overflow; text is legible (contrast within the `[[hallmark-design]]` accessibility gate, no overlap or clipping); every chart draws; no table overflows its container; the page is well-formed and opens offline. Metrics: no element wider than the viewport at 100%; contrast within the gate; no broken chart or overflowing table. Kind: STRUCTURAL for horizontal overflow, offline-cleanliness, and well-formedness; AGENT-VISION for contrast, legibility, and broken renders. Severity: HIGH for a broken render, unreadable text, or horizontal overflow.

6. **Fluid layout and composition** (`references/responsive-typography.md` rules 1-3 and 8-11). Macro spacing is viewport-proportional, wrapping serves the viewport rather than a fixed column, and width and height are EARNED rather than defaulted. Metrics: no band / grid container declares a fixed `padding` / `gap` at or above 24px (STRUCTURAL, `fluid-spacing`); and in the 1920px screenshot, **no text block sits beside empty space wider than roughly a third of its own band** without either widening toward its maximum measure or the band reflowing to multi-column (AGENT-VISION). The named failure to look for: "prose stranded beside dead space" - a measure-capped paragraph in a wide track with a dead corridor down one side, which reads as broken even though the paragraph obeys the measure. The v3.16.7 composition metrics grade the INVERSE family (text correctly sized and measured while using half its track, and sections viewport-tall for no reason), all from the RENDER PROBES in Step 9 rather than from the markup: no desktop display heading resolves above two lines without a recorded wrap plan; no display-text block uses under 70% of an otherwise empty track; no display heading carries an avoidable one-word final line; no `content-height` section declares a viewport-height minimum; and no text region's rectangle intersects a graphic region that should stay separate. Kind: STRUCTURAL for the spacing declarations and the section-height classification; RENDER PROBE for line count, width utilization, orphans, and rectangle intersection; AGENT-VISION for the stranded-prose judgment. Severity: HIGH for stranded prose, a text-graphic collision, or more than two fixed macro dimensions; MEDIUM for a single under-utilized track, one orphan, or one unearned viewport-height section. Note the trap this criterion carries in both directions: a SMALLER section is not automatically better, so a large density reduction is checked for crowding, clipping, and collision before it is accepted.
7. **Readability floors** (`references/responsive-typography.md` rules 4-6). Every rendered text size clears its role floor, emphasis tokens are distinguishable, and contrast clears AA. Metrics: font sizes at or above 16px (body prose) / 13px (secondary) / 12px (interactive) at BOTH the clamp minimum and 1920px (STRUCTURAL, `font-floor`); inline tokens declare a color AND a family / weight change on the unqualified base rule (STRUCTURAL, `emphasis-token`); declared ink / background pairs clear 4.5:1 (STRUCTURAL, `contrast`). The AGENT-VISION half asks two questions of the screenshot that no parser can answer: **is the secondary text readable at 100% zoom on a 27-inch display** (margin notes, captions, footer link lists, credits - not squinted at, read), and **are emphasis tokens discernible at a glance** (can you find every command name in a paragraph without hunting)? Kind: STRUCTURAL for the three deterministic checks; AGENT-VISION for the two glance judgments plus status-badge contrast (excluded from the automated set because its floor depends on rendered size). Severity: HIGH for any floor violation, indistinguishable tokens, or a foreground unusable on every background; MEDIUM for a single failing foreground / background combination.

8. **Diagram integrity** (`references/svg-diagram-quality.md`). An authored inline SVG reads as intended artwork rather than as fragments. Metrics: no hand-placed triangle arrowhead path exists outside a `<marker>` and arrowheads are applied consistently across a diagram's connectors (STRUCTURAL, `svg-arrowhead`); every `<svg>` in a `position: sticky` / `fixed` container carries a `max-height` (STRUCTURAL, `svg-viewport-fit`); every marker reference resolves and every defined marker is used (STRUCTURAL, `svg-marker-integrity`). The AGENT-VISION half is what a parser cannot judge: **every arrow reads as ONE object** (line and head visibly attached, pointing along the line's tangent), **the whole diagram is visible in one sticky viewport** with no node below the fold, and **no label collides with a line** (a dashed path crossing text fragments both). Kind: STRUCTURAL for the three checks; AGENT-VISION for the three glance judgments plus SVG label legibility, whose effective size is `declared_size * (rendered_width / viewBox_width)` and is held to the same 13px secondary floor. Severity: HIGH for a detached arrowhead, an unconstrained pinned graphic, or a dangling marker reference (no head renders at all); MEDIUM for inconsistently applied heads or a defined-but-unused marker. N/A when the page carries no inline SVG.

9. **Render-surfaced defects** (`references/responsive-typography.md` rule 7). Three classes that are invisible in markup read as prose and obvious within a second of a rendered screenshot, each nevertheless decidable from the CSS. Metrics: at most ONE sticky layer pins per offset (a sticky table header beneath a sticky nav stacks two bars and the lower covers what it labels); every in-page anchor target declares a `scroll-margin-top` clearing the sticky layer (otherwise a jump lands the heading underneath the nav, so navigation appears to mis-target every section); and a command block wraps or scrolls rather than clipping (a clipped line loses its tail silently, which is worse than an obviously broken command). Kind: STRUCTURAL (`render-only-defects`). Severity: HIGH for each - all three break something the reader cannot work around. N/A when the page has no sticky layer, no in-page anchors, and no `pre` block.

10. **Coverage-depth match** (v3.16.6). The built page's depth matches the coverage-depth (verbosity) level and section-count target the design record declares. Metric: compare the RENDERED SECTION STRUCTURE (top-level headings / nav entries) against the recorded level and target - a `distilled` page must not sprawl (section count near the recorded low-bound target; no appendix-grade sections), a `comprehensive` page must not have silently dropped topics (cross-check against the model's coverage manifest), and `balanced` covers every major topic without appendix-grade sections. Grade against section structure, NEVER raw word counts (a long section is a style property, not a depth violation). When the design record carries no verbosity level (a pre-verbosity page re-entering the loop), grade the page as `balanced` AND raise a MEDIUM finding that the record is incomplete. Depth never excuses a fluid-layout or readability violation: criteria 6-7 apply in full to a comprehensive page, which earns MORE sections, not denser smaller text. Kind: AGENT-VISION only - deliberately NO deterministic check in `scripts/visual_qa_score.py` (maintainer decision 2026-08-11: word / section-count bands are crude and false-positive; enforcement is record + rubric). Severity: HIGH when the page plainly contradicts the recorded level (a comprehensive run with dropped topics, a distilled run that reproduces the whole source); MEDIUM for a soft mismatch or a missing / incomplete record. This criterion is never N/A: a defaulted `balanced` run is still graded against `balanced`. Unlike criteria 1-9 it is a PAGE-level judgment (depth lives in the section structure, not inside any one band): grade it once per iteration and record it against a `page` segment id.

11. **Painted-surface integrity** (v3.16.7). Every JS-painted surface (a cinematic stage canvas, a chart canvas, a dynamically-populated overlay) actually painted at its intended size. Metrics, via one `page.evaluate()` per capture: each such element's `clientWidth` is within a few px of its container's content width; a small pixel sample after settle is not uniformly blank; and for scrub stages, the load-time state is fully legible (title/canvas visible before any scrolling). Kind: RENDER PROBE (deterministic in the browser, invisible to the static scorer and to console-error listeners - a canvas squeezed by a CSS collision or never drawn throws nothing). Severity: HIGH (a blank or collapsed stage is a broken page). Graded on the smoke-set segments every iteration; N/A only for a page with no JS-painted surface.

12. **Slide-mode integrity** (v3.18.3, `references/slide-navigation.md`). N/A unless the design record says `nav=slides` - a scrolling page skips this criterion entirely rather than failing it, and a design record with no `nav` field means `scroll`. Four metric groups:

    (a) **Slide fit.** No slide's content overflows its stage at ANY of the four QA viewports, and the **1366x768 leg is checked explicitly** because that is where the root clamp pins and text is largest relative to the stage - a slide that fits there fits everywhere the floors allow. No clipped text, and no inner scrollbar except an explicitly-declared scrollable region carrying a visible affordance and a design-record note. Metric: per slide, `scrollHeight <= clientHeight` on `.slide-inner` at each viewport, plus the declared-exception list. Kind: RENDER PROBE for the per-slide measurement; STRUCTURAL (`slide-fit`) for the stage-sizing and scroll-lock declarations. Severity: HIGH (undeclared overflow hides content the reader cannot reach).

    (b) **Fragment integrity.** Every declared fragment state is visually distinct from its predecessor, its end state matches the state table the scrollytelling contract still requires, and deep-linking to a mid-deck slide shows RESOLVED fragment state (prior slides fully revealed, later slides fully hidden) rather than a half-build. Metric: capture each slide's first, one mid, and last fragment state and diff them; load the page at `#slide-<n>` and confirm the resolved state. Kind: RENDER PROBE for state distinctness and deep-link resolution; STRUCTURAL (`slide-fragments`) for index positivity, uniqueness, and contiguity from 1 within each slide. Severity: HIGH for a half-build after a jump or a fragment that never reveals; MEDIUM for two visually indistinguishable steps.

    (c) **Ambient-loop discipline.** At most ONE ambient system per slide, at background-layer amplitude only, paused while its slide is inactive, and ABSENT under reduced motion (disabled entirely, not slowed). Nothing data-bearing loops: a chart build, a numeric transition, or any motion carrying meaning must be entry-triggered or fragment-stepped, because looping data motion fabricates the impression of live data. Metric: count infinite animations per slide; confirm `animation-play-state` is paused off-slide; emulate `prefers-reduced-motion: reduce` and confirm no ambient animation runs. Kind: STRUCTURAL (`slide-ambient`) for the reduced-motion guard; RENDER PROBE for the pause-when-inactive behavior and the per-slide count; AGENT-VISION for the amplitude judgment (is this background texture, or foreground distraction?) and for whether a looped effect is carrying meaning. Severity: HIGH for a looped data-bearing effect or an ambient loop surviving reduced motion; MEDIUM for a second ambient system on one slide or an over-amplitude drift.

    (d) **Navigation chrome.** The progress rail, the slide counter, and both hit zones are present, focus-visible, and correct - the rail's active segment tracks the active slide, the counter reads the true position, and the hit zones are real focusable controls with accessible names. Metric: presence by documented class name, `aria-current` on the active rail segment, counter text against the active index, and a visible focus ring on each control. Kind: STRUCTURAL (`slide-chrome`) for presence; RENDER PROBE for active-state correctness and focus visibility. Severity: HIGH for absent chrome (a keyboard-only deck with no position indicator or pointer path); MEDIUM for a stale active state.

    A fifth structural check has no visual metric and sits outside the four groups because it guards the criterion itself: the design record's `nav` field must AGREE with the markup (`slide-record`, STRUCTURAL, HIGH). It runs UNGATED, unlike everything else here. A page whose record says slides while the markup lost its `data-nav` attribute would otherwise skip every check above and score a clean pass - a fail-open outcome strictly worse than having no checks at all.


## The four QA layers and their gates (v3.16.7)

The twelve criteria above are two of four layers. Naming all four matters because without the vocabulary, "QA passed" silently means whichever layers happened to run - and a real session (2026-08-13) shipped an audience mismatch, an oversized estimate, a redundant argument, and decorative visuals from a run whose structural and behavioral checks were all green. Those layers ask whether the page WORKS. Nothing was asking whether it served its reader's decision.

| Layer | Grades | Gate | When it runs |
|---|---|---|---|
| 1. Content QA | Audience, purpose, assumptions, completeness, readability, claim support | **Gate A** | Before visual authoring |
| 2. Semantic-visual QA | Message, encoding, state changes, fit with the prose | **Gate B** | After the visual plan, before detailed styling |
| 3. Structural QA | Valid HTML, floors, contrast, image sizing, offline integrity, responsive layout | criteria 1-11 (structural) | On the generated file |
| 4. Behavioral QA | Navigation, scroll states, hover, focus, reduced motion, lightboxes, console errors, runtime requests | criteria 1-11 (render / agent-vision) | In a real browser at the four viewports |

Layers 3 and 4 are the mature core of the Step 9 loop and are LABELLED here, not rebuilt. Layers 1 and 2 are new.

**BINARY: a document cannot receive a final pass when only layers 3 and 4 have run.** A structural-and-behavioral pass on an artifact that addresses the wrong reader is a certified wrong answer.

### Gate A - content intent (before visual authoring)

Checks, against the `content_intent` block in the design record (see `references/content-intent.md` part 1):

- The source relationship is explicit, and under `standalone` no outline section evaluates the source draft or carries production-history metadata.
- The audience and the decision to enable are named.
- User assumptions are recorded, and no outline heading or lead sentence negates an `accepted` one.
- The scope class matches every estimate the outline promises.
- The required decision coverage is complete.
- Excluded framing does not appear in the outline.
- The recommendation can be supported by the evidence the outline plans to carry.

**Failure behavior: revise the OUTLINE, before any HTML is written.** That placement is the whole value of the gate; the same finding after authoring costs a rebuild.

### Gate B - semantic visual (after the visual plan, before detailed styling)

Checks, against the `visual_contracts` block (see `references/content-intent.md` part 3):

- Every major visual has a question and ONE intended takeaway.
- Every encoding (position, color, size, sequence, connection) has a stated meaning.
- Every interactive state maps to a prose state, per the section's state table.
- Qualitative visuals imply no unsupported precision.
- The static fallback retains the explanation.
- The visual is materially better than concise prose or a simple table (the subtractive test).

**Failure behavior: redesign or REMOVE the visual.** Removal is an explicitly permitted outcome, and the gate is not doing its job if it only ever demands more visual work.

### Gate E - decision readiness (last, optional, reader-level)

Run using ONLY the visible artifact, as a final human-readable confidence check:

- A reader can explain what the subject does.
- A reader can identify the viable options.
- A reader can understand the effort estimate and its assumptions.
- A reader can explain the recommendation and the conditions that would change it.
- A reader can identify the proposed proof step.
- No undefined technical term blocks comprehension.

**Failure behavior: revise CONTENT even when all technical QA has passed.** Gate E stays OPTIONAL and reader-level by design. It is a judgment about persuasion and comprehension, and putting a subjective judgment on the blocking path would make the release gate unfalsifiable; Gates A and B are where the checkable half of this concern is enforced.

## Per-segment score schema

Each segment yields one entry per applicable criterion:

```json
{
  "segment": "<id or heading>",
  "criterion": "full-width | image-sizing | annotation-fidelity | imagery-integration | readability-layout | fluid-spacing | font-floor | emphasis-token | contrast | svg-arrowhead | svg-viewport-fit | svg-marker-integrity | render-only-defects | coverage-depth | painted-canvas",
  "status": "pass | fail | n/a",
  "severity": "high | medium | low",
  "kind": "structural | agent-vision",
  "evidence": "<measured value, DOM observation, or screenshot note>"
}
```

`severity` is present only when `status` is `fail`. `evidence` records the concrete basis: a measured fraction (`band 0.61 of viewport`), a DOM observation (`fig-annotated has 0 regions`), or a screenshot note (`chart axis cropped on the right`).

## Page-level pass bar (binary)

The page PASSES when there is NO open finding with `severity: high`. A `medium` or `low` finding is recorded and surfaced for the fix pass (the loop tries to clear it within the iteration cap) but does not by itself block. A criterion that is `n/a` for the run does not count against the page (full-width when the aspect is not full; imagery-integration for a procedural run; annotation-fidelity when there is no annotated figure; slide-mode integrity on every scrolling page). A LOW-confidence annotated figure that shipped the enhanced-original plus textual complement is a PASS on annotation-fidelity.

## The degradation contract (structural vs agent-vision)

The rendered path is the DEFAULT (v3.16.5). Degradation is a disclosed exception, reached only after the provisioning offer, never a silent fallback.

- **Step 0 - probe, then offer.** Run `scripts/ensure_render_env.py` BEFORE grading. It exits with a distinct code per state and prints the exact one-time provisioning commands. If the state is not ready, offer the install ONCE, up front. A browser is usually one consented command away, and skipping straight to the structural subset is how this repo shipped a stranded paragraph, an 11px footer, and a diagram in pieces from runs that believed they had passed.
- **Headless browser AND agent vision** (the default): grade both kinds. Capture **2560x1300**, 1920x1080, 1366x768, and 390x844 plus the interaction states, measure bands and boxes, AND compare each segment's screenshot to its SOURCE figure / section. Scroll with `behavior: 'instant'` and let the position settle first, or a mid-animation frame grades as a defect that is not there. **The same rule governs slide mode, where it bites harder**: a capture taken mid-transition shows two slides painted together while the deck's state is perfectly correct, and a capture taken during a timed build (a counting counter) records a value that was never the answer. Settle before capturing - wait for the transition to end, or emulate reduced motion so transitions are instant cuts - and poll for the settled value rather than sleeping a fixed interval against an animation's duration. Both defects were observed while building this contract, neither is real, and both would be filed on every slide-mode run.
- **Headless browser, no vision step**: grade the STRUCTURAL kind from the rendered DOM and computed CSS.
- **No headless browser** (only after the offer was declined or failed): degrade to the STRUCTURAL kind via the markup / computed-CSS heuristic (`scripts/visual_qa_score.py`, structural mode) and state the degradation in one line in the final report. NEVER hard-fail on a missing browser.

Why 1366x768 is not optional: the ROOT clamp is usually still pinned at its MINIMUM at that width, so the readability floors bite there and not at 1920px. Grading only wide viewports passes type that resolves correctly on a monitor and is unreadable on the laptop most readers use - one page carried 14 distinct sub-floor element classes at 1366px while passing cleanly at 2560 and 1920.

Why 2560x1300 is not optional either, for the opposite reason: root scaling is fully engaged only at that class of width, and size / spacing defects a 1920 render understates are plainly visible there. The two ends of the range catch different defects, so both are required.

Every capture carries computed-metric probes (resolved root font size, smallest rendered size per role, band content fraction, `scrollWidth` vs viewport, key bounding boxes). They cost one `page.evaluate()` and settle deterministically what a screenshot only raises.

When only the structural subset ran, label the page-level verdict "structural-only" so the reader knows the AGENT-VISION criteria (crop of meaningful content, dead space, annotation placement vs source, imagery relevance, contrast and legibility) were not graded. A structural-only pass is a weaker but valid gate, recorded as such.

## Related

- `references/interactive-features.md` - the Phase 1 full-width contract, the Phase 2 image-box rules, the Phase 4 imagery detection + integration gate, and the v3.16.5 Phase 5 placement-role taxonomy (hero / background / contextual / gallery) with its mandatory background-scrim recipe, whose metrics this rubric grades.
- `references/svg-diagram-quality.md` - the authored-SVG integrity contract criterion 8 grades: marker-based arrowheads, dash patterns clear of labels, connectors on node edges, viewport-fit for pinned graphics, and the numeric geometry self-check.
- `references/responsive-typography.md` - the fluid-layout and readability contract criteria 6-7 grade: macro-spacing fluidity, viewport-serving wrapping, the tokenized type scale, the rendered-size floors, the two-axis emphasis-token rule, and the validated contrast floors.
- `references/content-intent.md` - the content brief, decision-brief authoring rules, and visual contracts that Gates A, B, and E grade.
- `references/figure-reconstruction.md` - the Phase 3 annotated-figure overlay-recreation pattern and its confidence gate.
- `scripts/ensure_render_env.py` - the render-environment probe the loop runs FIRST, so a degraded environment is explicit and remediable rather than a silent fallback.
- `scripts/visual_qa_score.py` - the deterministic structural scorer that checks the STRUCTURAL subset headless-optional.
- `assets/visual-qa-workflow.js` - the Dynamic-Workflow template that fans the per-segment grading out (Dynamic Workflows when available, degrading to subagents then a single sequential pass).
