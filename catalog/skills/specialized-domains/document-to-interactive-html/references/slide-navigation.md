# Slide Navigation Contract (`nav=slides`)

The authoring contract for the slide navigation mode resolved in Step 2's canvas question. When the design record carries `nav=slides`, Step 6 authors the output as a keyboard-advanced deck of viewport-fitted slides instead of a scrolling page, and this file is the contract that authoring builds to. It is self-contained: every rule is stated here with the pattern that satisfies it and the observable criterion a reviewer or the structural scorer applies. A design record with no `nav` field means `nav=scroll`, and none of this file applies.

Two boundaries frame everything below. First, the output is still ONE self-contained offline `.html` under every existing guarantee (no CDN, no external requests, base64 assets, reduced-motion guarded); slide mode changes how the reader ADVANCES, not what the file is. Second, the file is authored for exactly ONE mode: there is no runtime scroll / slides toggle, so the runtime in this contract ships only in a `nav=slides` output and a scrolling output carries none of it.

"Step" throughout means fragment-then-slide: a forward input reveals the active slide's next fragment if one remains hidden, and advances to the next slide otherwise (rule 4).

## 1. Stage and sizing

The document body declares the mode and hosts one stage section per slide:

```html
<body data-nav="slides">
  <div class="slide-deck" role="presentation">
    <section class="slide-stage" id="slide-1" aria-labelledby="slide-1-h">
      <div class="slide-inner">
        <h2 id="slide-1-h">Title</h2>
        ...
      </div>
    </section>
    ...
  </div>
</body>
```

- **Mode marker (BINARY)**: `<body data-nav="slides">` is present exactly when the design record says `nav=slides`. This attribute is the hook the QA loop and the structural scorer key on (Phase 4), so its absence on a slide-mode page, or its presence on a scrolling page, is a defect.
- **Stage sizing (BINARY)**: each `.slide-stage` is `100svw` wide and `100svh` tall - SMALL-viewport units, because `100vh` overshoots under mobile browser chrome and produces a stage the reader cannot see the bottom of. Exactly one slide is visible at a time.
- **No page scroll (BINARY)**: the scroll container (`html, body` or the `.slide-deck` wrapper) carries `overflow: hidden`. The page never exposes a document scrollbar. Slides transition by `transform` and/or `opacity` only - never by scrolling a strip into view with `scroll-behavior`, which re-introduces the scroll anchor semantics this mode exists to replace. Under `prefers-reduced-motion: reduce`, transitions are instant cuts (rule 6).
- **CSS namespacing**: every class this mode introduces carries the `slide-` component prefix (`.slide-deck`, `.slide-stage`, `.slide-inner`, `.slide-counter`, `.slide-rail`, `.slide-hit-prev`, `.slide-hit-next`, `.slide-live`). Never a bare `.stage`, `.deck`, `.rail`, `.counter`, or `.inner` - the skill's namespacing rule exists because a bare generic class once collided across components with zero console errors, and this mode adds a whole family of structural wrappers to a page that already has some.
- **Safe-area from the resolved aspect**: the Round 1 canvas choice shapes the content box INSIDE the stage. For the default deck option (16:9), `.slide-inner` is a 16:9 content box centered in the stage - `aspect-ratio: 16 / 9` capped by `min(100svw, calc(100svh * 16 / 9))` - so on a non-16:9 screen the composition holds and the surplus becomes letterbox margin painted with the page background, never stretched or cropped content. When Round 1 resolved a different aspect (e.g. `--layout portrait --nav slides`), the same construction uses that ratio.
- **Typography is the existing contract, unchanged**: the root `clamp()` scale, the fluid macro spacing, and the hard rendered-size floors (16px body / 13px secondary / 12px interactive) from `references/responsive-typography.md` apply INSIDE slides exactly as they do on a scrolling page, checked at all four QA viewports (2560x1300 / 1920x1080 / 1366x768 / 390x844). Slide mode is never a licence to shrink text to make content fit - overflow is resolved by rule 2, not by the font size.

## 2. Overflow: split, never scroll (BINARY)

A slide's content must FIT its stage at the 1366x768 viewport with the root clamp at its minimum. That viewport is the check because it is where the root clamp pins and text is at its largest relative to the stage, so a slide that fits there fits everywhere the floors allow.

- **Content that cannot fit splits into continuation slides during authoring**: "Topic (1/2)", "Topic (2/2)" - the heading repeats with the counter suffix, and the split point falls at a semantic boundary (between list items, between a figure and its discussion), never mid-sentence or mid-figure.
- **An inner scrollbar is FORBIDDEN**, with one narrow exception: an explicitly-declared scrollable region (a long data table, a code block) inside an otherwise-fitting slide. A declared region must carry a visible scroll affordance (a fade-out edge plus a scroll hint, not a bare cut-off) and a design-record note naming the slide and the reason. An author who cannot split records the exception; silence is the defect.
- This is the slide-mode analogue of the vertical-density rule: a scrolling page must not float sparse content in dead space, and a deck must not hide overflow behind an undeclared scrollbar. The inverse also holds - a slide carrying one thin point pairs onto a shared slide rather than presenting a mostly-empty stage (Step 6 states this per-slide density rule).

Observable criterion: at 1366x768, no `.slide-inner` has `scrollHeight > clientHeight` unless it contains a declared scrollable region, and every declared region is named in the design record.

## 3. Inputs: keyboard, touch, pointer

The full input map, all wired to the same step function:

| Input | Action |
|---|---|
| `ArrowRight`, `ArrowDown`, `PageDown`, `Space` | next step (fragment, then slide) |
| `ArrowLeft`, `ArrowUp`, `PageUp` | previous step (re-hide fragment, then previous slide) |
| `Home` / `End` | first / last slide (fragments resolved per rule 4) |
| Touch swipe left / right | next / previous step |
| Click on `.slide-hit-next` / `.slide-hit-prev` zones | next / previous step |
| Click on a `.slide-rail` segment | jump to that slide |

- **On-screen chrome (BINARY)**: the page renders a slide counter ("7 / 24") and a clickable progress rail with one segment per slide, the active segment visibly distinct. The previous / next hit zones are real focusable controls (`<button>`), not bare div click targets. All chrome classes carry the `slide-` prefix.
- **Native behavior is not fought (BINARY)**: when focus is inside an interactive chart, a declared scrollable region, or a form control, deck keys DISENGAGE - arrows pan the chart or scroll the table as they natively would. `Escape` returns focus to the deck (the active `.slide-stage`), after which deck keys re-engage. The runtime checks `event.target` containment rather than swallowing keys globally; a deck that hijacks arrow keys inside its own interactive charts breaks the interactivity guarantee the page exists to provide.
- **Input during a transition (BINARY)**: a step input arriving while a fragment or slide transition is mid-flight either queues (runs after the current transition settles) or fast-forwards (jumps the current transition to its end state, then applies the step). It is NEVER dropped and NEVER double-applied. The cheap correct implementation is fast-forward: keep the target state authoritative, snap to it, step once.

## 4. Fragment stepping

Fragments are the within-slide build model - the slide-mode replacement for scroll-progress reveals, and the substrate Phase 3's animation grammar and the cinematic camera map onto.

- **Markup**: an element that reveals as a build step carries `data-fragment="<n>"`, with `n` an integer giving the reveal order within its slide. Duplicate `n` values reveal together as one step.
- **Semantics (BINARY)**: on a forward step, the lowest-numbered hidden fragment of the active slide reveals; when none remain hidden, the deck advances to the next slide. On a backward step, the highest-numbered visible fragment re-hides; when none are visible, the deck moves to the previous slide WITH all of that slide's fragments visible (the reader re-enters where they left).
- **One fragment per discrete state**: a chart build stage, a sequential list reveal, and a cinematic camera keyframe are each ONE fragment. A slide with no fragments advances immediately on a forward step.
- **Idempotence (BINARY)**: fragment visibility is a pure function of the deck's (slide index, fragment index) state, never an accumulation of transitions that happened to run. Arriving at slide N via `Home`, `End`, a rail click, or a deep link shows the correct fully-resolved state - every fragment on slides before N visible, every fragment on slides after N hidden, slide N's fragments per the entry direction (all hidden entering forward, all visible entering backward or via a direct jump that lands mid-deck from a later slide). A half-build after a jump is a defect.

```js
function applyState(deck, s, f) {           // authoritative; called on every step, jump, and hashchange
  deck.slides.forEach((slide, i) => {
    slide.fragments.forEach((el, j) => {
      el.classList.toggle('slide-frag-on', i < s || (i === s && j < f));
    });
  });
}
```

- Fragment reveal effects follow the Phase 3 animation grammar (`references/interactive-features.md`, "Slide-mode animation grammar"): data-bearing motion is entry-triggered or fragment-stepped, never looped.

## 5. Deep links and history

- **Stable ids (BINARY)**: every `.slide-stage` carries `id="slide-<n>"` with `n` its 1-based position. The URL hash tracks the active slide as `#slide-<n>`, updated on every slide change (`history.pushState` on discrete navigation so back/forward walk slide history; fragment steps within a slide do NOT push history entries - they would make the back button re-hide builds one by one, which reads as a broken back button).
- **Loading with a hash (BINARY)**: opening the file at `#slide-7` shows slide 7 with slides 1-6 fully revealed and slides 8+ fully hidden, per rule 4's idempotence. A malformed hash falls back to slide 1; a well-formed but out-of-range slide number clamps to the nearest existing slide. Either way the deck opens on a real slide - never a blank stage.
- **Browser back / forward** move through visited slides. `hashchange` is handled through the same `applyState` path as keyboard input, so an external hash edit is indistinguishable from navigation.

## 6. Accessibility

- **Off-screen slides are inert (BINARY)**: every non-active `.slide-stage` carries both `inert` and `aria-hidden="true"`, so hidden content is unreachable by Tab and invisible to the accessibility tree. The active slide carries neither.
- **Announcements (BINARY)**: a visually-hidden `aria-live="polite"` region (`.slide-live`) announces each slide change as "<slide title>, slide <n> of <total>". Fragment reveals do not announce (they are within-slide presentation, and announcing every build spams the screen reader).
- **Focus follows navigation (BINARY)**: on a slide change, focus moves to the active slide's heading (`tabindex="-1"` on the heading, `.focus({ preventScroll: true })`). All deck chrome - hit zones, rail segments - is keyboard-focusable with visible focus states and accessible names ("Next slide", "Go to slide 7"). Style the heading's programmatic focus deliberately: suppress the default ring on the non-interactive heading (`.slide-stage h2[tabindex="-1"]:focus { outline: none }`) while keeping `:focus-visible` rings on every interactive control - otherwise every slide change paints a browser-default outline box around the title, which reads as a defect in QA.
- **Reduced motion (BINARY)**: under `prefers-reduced-motion: reduce`, slide and fragment transitions become instant cuts (no transform/opacity tween), and ambient loops (Phase 3) are disabled entirely - not slowed. The deck remains fully navigable; motion is presentation, never the mechanism.
- Color, contrast, and the emphasis-token rules are the existing contracts, unchanged.

## 7. No-JS and print fallback (BINARY)

The document must remain readable with the runtime absent or broken - a parsing error in the inlined JS must never produce a blank page.

- **Author CSS no-JS-first**: the stacked, source-order layout is the stylesheet's default; slide positioning, `overflow: hidden`, and fragment hiding apply only under a class the runtime adds on boot (`document.documentElement.classList.add('slide-js')`). Without JS, every slide renders as a normal stacked section in source order, fragments visible, nothing hidden or inert. Gating visibility on `.slide-js` (rather than removing styles on failure) is the load-bearing detail: a runtime that never boots never hides anything.
- **Print**: a `@media print` rule renders one slide per page (`.slide-stage { page-break-after: always; break-after: page; }`), fragments visible, chrome (`.slide-rail`, `.slide-counter`, hit zones) hidden.

Observable criterion: opening the file with JavaScript disabled shows every slide's full content, top to bottom, in source order.

## 8. Interaction budget in slide mode

The site-wide five-point minimum interaction budget (`references/interactive-features.md`) is satisfied as follows - slide mode re-expresses two points and leaves three untouched:

1. **Section navigation with active state** -> the progress rail + slide counter (rule 3). The rail IS the section nav; its active segment is the active state.
2. **Scroll-triggered reveals** -> slide-entry reveals and fragment steps (rule 4; the trigger grammar is Phase 3's).
3. **Hover / focus affordances** -> unchanged.
4. **Lightbox on every non-decorative image** -> unchanged (the lightbox opens above the stage; `Escape` closes it first, then returns focus to the deck per rule 3).
5. **The signature interaction** -> unchanged, or fragment-stepped where its scroll-keyed original maps onto steps (Phase 3's table governs the mapping).

## Design-record fields for slide mode

Beyond the `nav=slides` value and its provenance (recorded in Step 2), a slide-mode design record names: the slide count, every continuation split ("Topic (1/2)"), every declared scrollable-region exception with its reason (rule 2), and any slide whose content forced a deviation. The QA loop (Phase 4) verifies the record against the page.

## Verification (binary, per slide-mode output)

- [ ] `<body data-nav="slides">` present; design record says `nav=slides` with provenance.
- [ ] Every mode class carries the `slide-` prefix; no bare `.stage` / `.deck` / `.rail` / `.counter` selector exists.
- [ ] Each `.slide-stage` is `100svw x 100svh`; the scroll container has `overflow: hidden` under `.slide-js`; exactly one slide visible.
- [ ] At 1366x768 no `.slide-inner` overflows its stage except declared scrollable regions, each with a visible affordance and a design-record note.
- [ ] All keyboard, touch, and pointer inputs from the rule 3 table work; deck keys disengage inside interactive charts and re-engage on `Escape`.
- [ ] A step input mid-transition is neither dropped nor double-applied.
- [ ] Fragment state is idempotent: `Home`, `End`, rail jumps, and deep links all land on fully-resolved states.
- [ ] The hash tracks `#slide-<n>`; loading with a hash opens that slide with prior fragments resolved; back/forward walk slide history.
- [ ] Off-screen slides are `inert` + `aria-hidden`; slide changes announce via the polite live region; focus moves to the active heading.
- [ ] Under `prefers-reduced-motion: reduce`, transitions are instant cuts (verified by emulating the preference, not by reading the code).
- [ ] With JavaScript disabled, the document reads top-to-bottom as stacked sections; `@media print` yields one slide per page.
- [ ] The rendered-size floors (16 / 13 / 12px) hold inside slides at all four QA viewports.
