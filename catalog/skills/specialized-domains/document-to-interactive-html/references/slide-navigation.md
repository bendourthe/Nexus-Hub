# Presentation navigation contract

Use this contract when presentation is included alongside the scrolling page. `dual-view-handbooks.md` owns inclusion, theme/depth choices, source coverage, slide-count limits, and final acceptance. The legacy `nav=slides` field is a compatibility hint, not permission to replace reading mode. All CSS, JavaScript, fonts, and assets remain in one offline file.

## 1. Entry, exit, and stage

- Start in reading view unless an explicit slide deep link is loaded. Title and global top-menu **Presentation Mode** actions always call entry with index zero. **Present chapter** names and opens its specific target. Any resume action is separately labeled.
- Use a modal dialog or equivalent accessible presentation region. Make the inactive view inert, pause its animation, and keep its filter state independent. Save reading position and opener focus before entry; restore both on exit. Close a nested inspector first on Escape, then the presentation on the next Escape.
- Keep exactly one active slide, with namespaced classes and unique IDs for duplicated figure/gradient/clip definitions. Size the desktop stage to the available viewport minus header/footer controls and safe areas. Reading canvas width does not dictate deck aspect ratio. Preserve readable text and complete imagery at every supported size.
- Fullscreen is optional enhancement: request it on a supported element such as `document.documentElement`; handle rejection by keeping the fitted presentation usable. Observe native fullscreen exit and restore consistent reading/focus state. Repeated entry and exit must not leak listeners or leave scrolling locked.
- Record `presentation.enabled`, resolved theme/depth, stable theme sequence, source-to-slide mapping, initial slide, and supported compact breakpoint in retained authoring inputs. The legacy scorer keys on `data-nav="slides"`, `.slide-stage`, `.slide-rail`, and `.slide-counter` for its old standalone draft contract. Do not claim that it recognizes the new presentation fields; inspect both views in a browser.

## 2. Fit and source-count ceiling

Follow the source-count ceiling in `dual-view-handbooks.md`. Do not split a source slide into additional continuation slides to fix overflow. Recompose the layout, remove redundant wording without dropping facts, improve figure allocation, or expose clearly labeled within-slide detail. Do not hide overflow or shrink text below readable floors. An impossible count/coverage/fit combination remains an explicit unresolved constraint, not a success claim.

Check every slide across the desktop sizes and breakpoint boundaries in the shared contract. A single passing 1366x768 screenshot does not imply other aspect ratios fit. Compact presentation can deliberately reflow vertically; declare that breakpoint. Large tables or map directories may scroll locally with visible affordances and full keyboard/touch access. Desktop slide content itself must fit without a vertical scrollbar. Keep native scrolling available inside declared controls and theme their scrollbars; do not intercept their arrow keys.

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

The complete reading page is visible without JavaScript. Keep the additional presentation region hidden until explicitly opened by a functioning runtime; a missing or broken runtime must neither blank the reading page nor duplicate it with a stacked slide copy. Presentation fragment hiding and scroll locking apply only to an active presentation, never the initial reading view.

Default print shows the complete reading page once with controls and presentation hidden. If an explicit presentation-print action exists, it prints one logical slide per page with fragments visible and reading content/chrome hidden. Verify both paths that are offered; do not merely inspect stylesheet declarations.

## 8. Interaction budget in slide mode

The site-wide five-point minimum interaction budget (`references/interactive-features.md`) is satisfied as follows - slide mode re-expresses two points and leaves three untouched:

1. **Section navigation with active state** -> the progress rail + slide counter (rule 3). The rail IS the section nav; its active segment is the active state.
2. **Scroll-triggered reveals** -> slide-entry reveals and fragment steps (rule 4; the trigger grammar is Phase 3's).
3. **Hover / focus affordances** -> unchanged.
4. **Lightbox on every non-decorative image** -> unchanged (the lightbox opens above the stage; `Escape` closes it first, then returns focus to the deck per rule 3).
5. **The signature interaction** -> unchanged, or fragment-stepped where its scroll-keyed original maps onto steps (Phase 3's table governs the mapping).

## Design-record fields for presentation

Record the enabled view, theme/depth, source mapping, logical slide count, declared component scroll regions, and compact breakpoint according to `dual-view-handbooks.md`. Keep authoring metadata out of executive-facing slide copy.

## Verification (binary, per slide-mode output)

- [ ] Reading is the initial view; included presentation and option provenance are recorded, and both global entry controls start slide 1.
- [ ] Every mode class carries the `slide-` prefix; no bare `.stage` / `.deck` / `.rail` / `.counter` selector exists.
- [ ] Exactly one presentation slide is active; its available stage excludes chrome, and inactive views are inert.
- [ ] At 1366x768 no `.slide-inner` overflows its stage except declared scrollable regions, each with a visible affordance and a design-record note.
- [ ] All keyboard, touch, and pointer inputs from the rule 3 table work; deck keys disengage inside interactive charts and re-engage on `Escape`.
- [ ] A step input mid-transition is neither dropped nor double-applied.
- [ ] Fragment state is idempotent: `Home`, `End`, rail jumps, and deep links all land on fully-resolved states.
- [ ] The hash tracks `#slide-<n>`; loading with a hash opens that slide with prior fragments resolved; back/forward walk slide history.
- [ ] Off-screen slides are `inert` + `aria-hidden`; slide changes announce via the polite live region; focus moves to the active heading.
- [ ] Under `prefers-reduced-motion: reduce`, transitions are instant cuts (verified by emulating the preference, not by reading the code).
- [ ] With JavaScript disabled, the document reads top-to-bottom as stacked sections; default print includes reading content once; explicit presentation print, if offered, yields one slide per page.
- [ ] The rendered-size floors (16 / 13 / 12px) hold inside slides at all four QA viewports.
