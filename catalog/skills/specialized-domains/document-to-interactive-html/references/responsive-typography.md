# Responsive Typography and Fluid Layout Contract

The canonical fluid-layout and readability contract every presentify output is authored to and graded against. It exists because a page can pass every structural check in `references/visual-qa-rubric.md` and still be obviously wrong to a human in one glance: prose trapped in a narrow column while half the viewport sits empty, margin notes and footers rendered too small to read, and inline command names indistinguishable from the prose around them. Those three defect classes were observed together in a real run (2026-08-10) and are what this contract makes checkable.

Eleven rules, each with the CSS pattern that satisfies it and the observable criterion the scorer or the grading agent applies. `scripts/visual_qa_score.py` enforces rules 1, 4, 5, 6, and 7 deterministically; rules 2 and 3 are graded from screenshots against the criteria stated here, and rules 8 through 11 (added v3.16.7) are graded from the rendered line-count, width-utilization, and section-height probes in Step 9.

Rules 1 through 7 catch text that is too small, too fixed, or stranded. Rules 8 through 11 catch the inverse family, observed 2026-08-13: text that is correctly sized and correctly measured while using half its track, and sections that are viewport-tall for no reason. Both families read as broken to a human, and neither is visible to a font-floor check.

## 1. Fluid space, never fixed space

Every MACRO-layout dimension - band padding, grid gaps, column widths, gutters, section rhythm - is a `clamp()` of viewport-relative units, never a bare `px` or `rem` constant. MICRO-spacing inside a component (a chip's inline padding, a list item's margin, a hairline rule) may stay `rem`-based, because it should track the type size rather than the window.

```css
/* CORRECT - the band breathes with the viewport */
:root{
  --gutter: clamp(1.25rem, 4vw, 2.5rem);
  --band-y: clamp(3.5rem, 7vh, 7rem);
  --grid-gap: clamp(1.25rem, 3vw, 3.5rem);
}
.band{ padding-inline: var(--gutter); }
.band-y{ padding-block: var(--band-y); }
.editorial{ display: grid; gap: var(--grid-gap); }

/* WRONG - a fixed macro gap; identical on a phone and a 32-inch display */
footer .cols{ display: grid; gap: 2rem; }
```

One footgun worth naming, because it produces a horizontal scrollbar rather than an obviously wrong layout: a band with BOTH `width: 100%` and `padding-inline` overflows its parent unless `box-sizing: border-box` is in effect, since the default `content-box` adds the padding on top of the 100%. Set `*{ box-sizing: border-box }` once (every well-formed page here does) or drop the redundant `width: 100%` - a block-level band already fills its container.

Observable criterion: no top-level band, grid, or column container declares a fixed `padding` / `gap` at or above 24px (1.5rem at the 16px root). At or above that size the dimension is macro spacing and must be fluid. The scorer flags each occurrence and escalates to HIGH severity past two, because one stray fixed gap is a slip while three is a layout authored without the contract.

## 2. Wrapping serves the viewport, not a fixed column

The 45-85 character reading measure is a PER-ELEMENT cap on long-form prose. It is not a page width, and it is not a licence to leave the rest of the track empty. Grid TRACKS must widen or reflow with the viewport (`minmax()` with `auto-fit` or `fr`, container queries where they help), so a prose element sitting in a wide track either widens toward its maximum measure or the band reflows so the surplus width does real work.

The failure this rule kills, observed 2026-08-10: a paragraph hard-capped at 68ch (about 590px) inside a 1fr track 1277px wide, stranding roughly 690px of dead space beside every line of body copy. The paragraph obeyed the measure and the band still read as broken.

In a MULTI-COLUMN zone, fluid `fr` shares beat `ch` caps outright, and the measure does not belong there at all. A `ch`-capped column inside a wide grid produces one of two rejected looks: a dead middle band with the aside stranded at the far edge, or prose compacted to the left of its own track. Give the columns fractional shares and put the margin notes ADJACENT to the prose they annotate.

```css
/* CORRECT - fractional shares, notes adjacent, no measure inside the zone */
.editorial{
  display: grid;
  gap: var(--grid-gap);
  grid-template-columns: minmax(0, 2fr) minmax(16rem, 1fr);
}

/* WRONG - a ch cap inside a multi-column zone; the surplus becomes dead space */
.editorial{ grid-template-columns: minmax(0, 1fr) minmax(0, 19rem); }
p.measure{ max-width: 68ch; }
```

State the precedence explicitly, because it is the opposite of the usual advice: **on wide screens, filling the window wins over line-length caps.** The 45-85ch measure applies to SINGLE-COLUMN long-form prose only. It is not a page width, and inside a multi-column zone it is a defect.

One caveat on the mobile collapse: when such a grid drops to a single column, keep `minmax(0, 1fr)` rather than a bare `1fr`. `1fr` means `minmax(auto, 1fr)`, and that `auto` minimum is the content's min-content, so one unshrinkable child (a long `<pre>` line) stretches the track past the viewport and the page scrolls sideways. The alternative fix is to make the child itself shrinkable, which is what rule 5 of the diagram contract and the `pre-wrap` rule below do.

Add `text-wrap: balance` to headings (it evens ragged multi-line titles) and `text-wrap: pretty` to prose as a progressive enhancement - both degrade silently in browsers that lack them.

Observable criterion (AGENT-VISION): in the 1920px screenshot, no text block sits beside empty space wider than roughly one third of its own band without either widening toward its maximum measure or the band reflowing to multi-column.

## 3. Scale the ROOT, not the elements

Viewport-proportional scaling belongs on the **root element**, in one declaration. Every `rem`- and `ch`-derived dimension on the page then scales with the window for free: type, spacing, gutters, and grid tracks alike.

```css
/* CORRECT - one declaration scales the entire page */
html{ font-size: clamp(1rem, 0.5vw + 0.55rem, 1.6rem); }   /* 16 -> 25.6px */
body{ font-size: 1rem; }
footer b{ font-size: 0.8125rem; }   /* 13px at the clamp floor, 20.8px at the cap */
```

Two failure modes this replaces, both observed:

1. **The clamp on `body`, children in `rem`.** `rem` resolves against the ROOT, not `body`, so every child silently falls back to the 16px default and the scale is fluid in exactly one rule. That is how a run shipped an 11.2px footer heading under a correct-looking `body` declaration.
2. **Per-element `clamp()` sizes.** They cap out independently, so a large display renders laptop-sized text no matter how many individual sizes you bump. Three rounds of per-element increases failed to fix perceived smallness on a 2560px display before the root-scaling change fixed it in one line.

A modular scale is still useful, and still declared once as `:root` custom properties - but it now RIDES the scaling root rather than trying to reproduce it per step. Keep the step values as plain `rem` multiples; the root supplies the fluidity.

```css
:root{
  --step--2: 0.8125rem;   /* 13px at the root floor */
  --step-0:  1rem;
  --step-2:  1.5rem;
}
```

Two consequences worth stating, because both are easy to get wrong:

- **`rem` macro spacing is now fluid**, so rule 1's preference for `clamp()` is satisfied by a `rem` value under a scaling root: `2.5rem` of band padding is 40px at a 16px root and 64px at a 25.6px one. `scripts/visual_qa_score.py` treats `rem` as fluid exactly when the root is.
- **Everything derived from `rem` must be re-checked at the scaled root**, including the gutter and therefore the full-width band fraction. A `2.75rem` gutter is 44px at a 16px root and 50.6px at 18.4px, which moved one calibration page's band from a passing 0.954 to a failing 0.947. Compute at the real root, not at 16px.

## 4. Minimum rendered sizes (hard floors)

Three floors, checked at BOTH the `clamp()` minimum and the value resolved at a 1920px viewport. Checking only the resolved 1920px value is the trap: on a 1366px laptop the clamp is usually still pinned at its minimum, so the minimum IS the size most readers get.

Under root scaling (rule 3) this becomes the contract's sharpest edge, and it is the one a render session is most likely to miss. **Root scaling does nothing below the root clamp's minimum.** With `clamp(1rem, 0.5vw + 0.55rem, 1.6rem)` the root is pinned at 16px for every viewport at or below 1366px, so every `rem`-based size bottoms out exactly where it did before scaling was added. A page verified only at 2560px and 1920px - where scaling is active and everything looks generous - can carry a full set of sub-floor sizes at 1366px. One did: 14 distinct element classes, none visible at the widths that were checked. Evaluate every floor at the ROOT's clamp minimum, not just at the element's own.

| Text role | Floor | Applies to |
|---|---|---|
| Body prose | 16px | `body`, bare `p`, long-form article text |
| Secondary text | 13px | margin notes, captions, footer link lists, credits, eyebrow labels, stat sublabels |
| Interactive text | 12px | anything clickable or focusable - buttons, links in controls, chips, tab labels |

Nothing renders below 12px. The 2026-08-10 defects (unreadable margin notes at 11.5px and a 11.2px footer) sat just under the secondary floor, which is why the floor is stated as a number rather than "small but readable".

SVG text inside a scaled `viewBox` is exempt from these floors, because its declared `font-size` is in user units and the rendered size depends on the SVG's scale factor. The scorer identifies such rules by the presence of a `fill:` declaration in the same block (SVG text is colored with `fill`, HTML text with `color`) and skips them. Diagram label legibility is governed by `references/svg-diagram-quality.md` rule 5 instead, which holds SVG labels to the same 13px secondary floor after scaling the declared size by the render factor.

## 5. Emphasis tokens must be visually distinct

An inline token that carries meaning - a command name, a file path, a flag, a key term - must differ from surrounding prose on BOTH axes at once:

1. A COLOR step: at least two discernible steps from the body ink, while still clearing WCAG AA (4.5:1) against its background.
2. A FAMILY or WEIGHT change: monospace, or semibold at minimum.

One axis alone is not enough. A muted `<code>` that only changes family reads as prose at a glance, which is how `/review` became invisible inside a margin note in the 2026-08-10 run. A colored token with no family change is easily mistaken for a link.

```css
/* CORRECT - family AND an AA-checked accent color */
code{ font-family: var(--f-mono); font-size: .92em; color: var(--accent); }

/* WRONG - family only; the token disappears into the paragraph */
code{ font-family: var(--f-mono); font-size: .9em; }
```

Observable criterion: at least one rule targeting inline tokens (`code`, `kbd`, `samp`, `.token`) declares a `color`, and at least one declares a `font-family` or `font-weight`. Failing this is HIGH severity, because an unreadable command name in a technical document defeats the document.

## 6. Contrast floors, validated rather than eyeballed

Body and secondary text clear WCAG AA (4.5:1) against their background. Large display text (at or above 24px, or 18.66px bold) clears 3:1. A muted-ink-on-dark palette is exactly the case where a designed-by-feel value lands near 4:1 and looks fine to the author on a bright monitor.

The scorer computes the true WCAG relative-luminance ratio for each declared foreground / background custom-property pair and grades by how badly a color fails:

- The PRIMARY body pair (the main ink against the main base) below 4.5:1 is HIGH severity.
- A foreground that fails against EVERY declared background is HIGH severity, since it cannot be used as text anywhere on the page.
- A single foreground / background combination failing while other combinations pass is MEDIUM: the color is usable, just not on that surface.

Semantic status colors (names matching `ok`, `warn`, `stop`, `error`, `success`, `info`) are excluded from the automated foreground set, because they typically appear as large or bordered badge text whose applicable floor is 3:1 rather than 4.5:1 and whose rendered size the scorer cannot know. Grade those from the screenshot instead.

## 7. Three defects only a render surfaces

None of these is a typography rule, and none is findable in markup alone. All three were shipped by pages that passed every static check, and all three are obvious within a second of looking at a rendered screenshot.

**Sticky under sticky.** At most ONE sticky layer per scroll context. A `position: sticky` table header pinning beneath an already-sticky page nav produces two stacked bars, and the lower one often covers the content it was meant to label. If a second layer is genuinely needed, offset it by the upper layer's height (`top: calc(var(--nav-h) + 0px)`) and verify by scrolling, not by reading the CSS.

```css
/* WRONG - both pin to the top of the viewport and overlap */
#nav{ position: sticky; top: 0; }
thead th{ position: sticky; top: 0; }

/* CORRECT - the lower layer clears the upper one */
:root{ --nav-h: 3.25rem; }
#nav{ position: sticky; top: 0; height: var(--nav-h); }
thead th{ position: sticky; top: var(--nav-h); }
```

**Anchor targets need `scroll-margin-top`.** With a sticky nav, an in-page anchor jump lands the section's heading UNDER the nav, so the reader arrives at a section whose title they cannot see. The fix is one declaration on the scroll target, and it must account for the nav's real height.

```css
section[id]{ scroll-margin-top: calc(var(--nav-h) + 1rem); }
```

**Command blocks must not clip.** A long command or prompt line inside a `pre` block is silently cut off at the container edge - the reader sees a plausible-looking command that is missing its tail, which is worse than an obviously broken one. Wrap rather than clip.

```css
pre{ white-space: pre-wrap; overflow-wrap: anywhere; }
```

## 8. Display text needs a wrap plan, not a wrap accident

Rules 1 through 7 catch text that is too small, too fixed, or stranded beside dead space. They say nothing about text that is correctly sized, correctly measured, and ARTIFICIALLY NARROW inside its own track, which is the opposite failure and just as visible.

Observed 2026-08-13: a hero title used 58% to 70% of its desktop column because a `10.5ch` maximum forced it into three lines. Several section headings took three lines beside an unused track. And after a deliberate two-line desktop title was introduced with semantic spans, the mobile layout stranded "vs" alone on a fourth line, because one wrapping strategy was applied to every viewport.

Record a wrap plan for every hero title and major section heading:

- Target line count at large desktop (2560).
- Target line count at standard desktop (1920).
- Acceptable line count at laptop width (1366).
- Mobile fallback behavior, reviewed rather than inferred from the desktop markup.
- Words or phrases that must not become isolated lines.

```css
/* CORRECT - balance as enhancement, breakpoint rules for intentional phrasing */
h1{ text-wrap: balance; }
@media (max-width: 40rem){ h1 .brk{ display: contents; } }  /* mobile wraps naturally */
```

`text-wrap: balance` is a progressive ENHANCEMENT, not the plan: it evens a ragged rag, and it cannot express intentional phrasing or protect a specific word from isolation. Use semantic spans or breakpoint-specific display rules when a title needs deliberate phrasing, and define the mobile behavior separately whenever you do.

Observable criterion: no display heading has an avoidable one-word orphan; a desktop hero normally resolves to one or two lines; the mobile form was reviewed at 390px rather than assumed from the desktop markup.

## 9. Measure belongs to the text ROLE, not to the page

Rule 2 establishes that the 45 to 85 character measure is per-element and is a defect inside a multi-column zone. Rule 9 completes it: classify text by ROLE before assigning any width, because a single global character cap applied across roles produces arbitrary wrapping and dead space wherever the role does not want it.

Observed 2026-08-13: display answers in a Highlights section used about 54% to 60% of their column because a `32ch` cap intended to control READING length was applied to large DISPLAY text.

| Role | Width treatment |
|---|---|
| Long-form prose | The 45 to 85 character cap. **The only default recipient.** |
| Display answer / callout | Use the available track; control readability through type size and hierarchy. |
| Heading | Optimize phrase grouping and target line count (rule 8), not character count. |
| Multi-column text | Fractional tracks, no inner `ch` cap (rule 2). |
| Table or diagram label | Size to the component, not to the article measure. |

Observable criterion: on wide screens a display-text block uses at least 70% of its available track, unless the remaining area has a stated visual purpose (a deliberate asymmetry, a graphic, a pull quote). Long-form prose remains the only role that receives the character measure by default.

## 10. Section height is earned by content or interaction (BINARY)

A universal viewport-height minimum turns a navigable website back into a slide deck. Observed 2026-08-13: every standard section carried `min-height: 82svh`, so short sections kept large empty regions below their content, and scrollytelling steps used `58svh` each for state changes that needed far less scroll distance.

This one slips past rule 1 for a specific and instructive reason: `82svh` IS a viewport-relative value, so the fluid-spacing check reads it as correctly fluid. It is fluid and wrong. Fluidity was never the property that mattered here.

Classify every section:

| Class | Height source |
|---|---|
| `content-height` | Its content. **The default.** No viewport-height minimum. |
| `viewport-stage` | A deliberate opening or transition. |
| `scrollytelling-track` | Calculated from the number of MEANINGFUL states. |
| `pinned-comparison` | Enough to complete the state sequence, and no more. |

Observable criterion: a standard section declares no viewport-height minimum. A tall section names the interaction or content volume requiring the height, and removing its height rule demonstrably breaks the intended experience. If removing it changes nothing but the whitespace, it was never earned.

## 11. Density is a system, so revise it as one

When a page reads as too sparse or too dense, the cause is almost never one variable. The 2026-08-13 session's excess height came from heading width, heading scale, label-column width, section padding, grid gaps, line height, card minimum heights, and viewport-height rules acting together. Reducing one font size would have moved the empty space rather than removing it.

Revise these together, and report which ones changed:

1. Root type scale.
2. Display type scale and target line count (rule 8).
3. Text-role measure (rule 9).
4. Grid-track proportions.
5. Section and component gaps.
6. Line height.
7. Explicit or minimum heights (rule 10).
8. The relationship to adjacent graphics.

The coordinated pass on that page cut the 12-section body by 22.6% at 1920x1080 (18,015px to 13,936px), 25.3% at 2560x1300, 21.8% at 1366x768, and 7.6% at 390x844, with no content removed. The smaller mobile figure is correct rather than a shortfall: a narrow viewport genuinely needs more lines.

The pass NEVER resolves density by shrinking body text below its floor, so it composes with rule 4 rather than competing with it. Report explicitly that body prose stays at or above 16px, secondary at or above 13px, and interactive at or above 12px, at BOTH the clamp floor and 1920px.

Observable criterion: a density revision names the variables it changed together, and confirms the rule-4 floors still hold at both measurement points.

## Verification

- [ ] Every hero title and major section heading has a recorded wrap plan, and no display heading carries an avoidable one-word orphan.
- [ ] Display text, headings, and component labels are sized by ROLE; the character measure is applied only to long-form prose.
- [ ] On wide screens, no display-text block uses under 70% of its available track without a stated purpose for the remainder.
- [ ] Every section is classified, and no `content-height` section declares a viewport-height minimum.
- [ ] Any density revision names the variables changed together and confirms the role floors still hold.
- [ ] No top-level band or grid container declares a fixed macro `padding` / `gap` at or above 24px.
- [ ] Viewport-proportional scaling is on the ROOT in ONE declaration (`html{font-size:clamp(...)}`), not reproduced per element, and any modular scale rides that root as plain `rem` multiples.
- [ ] Every floor was evaluated at the ROOT clamp's minimum as well as at 1920px - root scaling does nothing below it, so a page verified only at wide viewports can carry a full set of sub-floor sizes.
- [ ] Every font size clears its role floor (16 / 13 / 12px) at BOTH the clamp minimum and at 1920px.
- [ ] Inline emphasis tokens declare both a color and a family or weight change, and the color clears AA.
- [ ] Every ink and accent custom property clears AA against the backgrounds it is used on; no foreground fails against all of them.
- [ ] At most one sticky layer pins per scroll context, and any second layer is offset by the first's height.
- [ ] Every in-page anchor target declares a `scroll-margin-top` that clears the sticky nav.
- [ ] Command / prompt blocks wrap (`white-space: pre-wrap; overflow-wrap: anywhere`) rather than clipping.
- [ ] `python scripts/visual_qa_score.py <out.html>` reports no HIGH-severity `fluid-spacing`, `font-floor`, `emphasis-token`, `contrast`, or `render-only-defects` finding.

## Related

- `references/visual-qa-rubric.md` - the per-segment grading rubric; its `fluid-layout` and `readability-floors` criteria grade this contract from screenshots.
- `references/interactive-features.md` - the full-width canvas contract this composes with; that file governs how wide a band is, this file governs what happens to type and space inside it.
- `references/svg-diagram-quality.md` - the authored-SVG integrity contract, which owns diagram label legibility (exempted from rule 4 here) and the marker / geometry rules.
- `scripts/visual_qa_score.py` - the deterministic scorer implementing rules 1, 4, 5, and 6.
