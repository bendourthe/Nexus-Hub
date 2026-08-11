# Responsive Typography and Fluid Layout Contract

The canonical fluid-layout and readability contract every presentify output is authored to and graded against. It exists because a page can pass every structural check in `references/visual-qa-rubric.md` and still be obviously wrong to a human in one glance: prose trapped in a narrow column while half the viewport sits empty, margin notes and footers rendered too small to read, and inline command names indistinguishable from the prose around them. Those three defect classes were observed together in a real run (2026-08-10) and are what this contract makes checkable.

Six rules, each with the CSS pattern that satisfies it and the observable criterion the scorer or the grading agent applies. `scripts/visual_qa_score.py` enforces rules 1, 4, 5, and 6 deterministically; rules 2 and 3 are graded from screenshots against the criteria stated here.

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

Observable criterion: no top-level band, grid, or column container declares a fixed `padding` / `gap` at or above 24px (1.5rem at the 16px root). At or above that size the dimension is macro spacing and must be fluid. The scorer flags each occurrence and escalates to HIGH severity past two, because one stray fixed gap is a slip while three is a layout authored without the contract.

## 2. Wrapping serves the viewport, not a fixed column

The 45-85 character reading measure is a PER-ELEMENT cap on long-form prose. It is not a page width, and it is not a licence to leave the rest of the track empty. Grid TRACKS must widen or reflow with the viewport (`minmax()` with `auto-fit` or `fr`, container queries where they help), so a prose element sitting in a wide track either widens toward its maximum measure or the band reflows so the surplus width does real work.

The failure this rule kills, observed 2026-08-10: a paragraph hard-capped at 68ch (about 590px) inside a 1fr track 1277px wide, stranding roughly 690px of dead space beside every line of body copy. The paragraph obeyed the measure and the band still read as broken.

```css
/* CORRECT - the side rail absorbs surplus width, and prose widens toward its max */
:root{ --measure: min(85ch, 100%); }
.editorial{
  display: grid;
  gap: var(--grid-gap);
  grid-template-columns: minmax(0, 1fr) minmax(0, clamp(17rem, 24vw, 30rem));
}
p.measure{ max-width: var(--measure); }

/* WRONG - a fixed rail plus a narrow measure leaves a dead corridor at 1920px */
.editorial{ grid-template-columns: minmax(0, 1fr) minmax(0, 19rem); }
p.measure{ max-width: 68ch; }
```

Add `text-wrap: balance` to headings (it evens ragged multi-line titles) and `text-wrap: pretty` to prose as a progressive enhancement - both degrade silently in browsers that lack them.

Observable criterion (AGENT-VISION): in the 1920px screenshot, no text block sits beside empty space wider than roughly one third of its own band without either widening toward its maximum measure or the band reflowing to multi-column.

## 3. Fluid type scale defined once, as custom properties

All font sizes derive from a single `clamp()`-based modular scale declared once as custom properties on `:root`. Sizes are then referenced by step token, never re-derived per selector.

This is not a style preference. It is the guard against a specific and easy mistake: putting the fluid `clamp()` on `body` and then sizing children in `rem`. Because `rem` resolves against the ROOT element and not `body`, every child silently falls back to the 16px browser default and the whole scale stops being fluid. That is precisely how the 2026-08-10 run shipped an 11.2px footer heading while its `body` rule looked correctly fluid.

```css
/* CORRECT - one scale, tokenized, floors baked into the clamp minimums */
:root{
  --step--2: clamp(0.8125rem, 0.78rem + 0.16vw, 0.9375rem);  /* 13 -> 15px  */
  --step--1: clamp(0.875rem,  0.83rem + 0.22vw, 1rem);       /* 14 -> 16px  */
  --step-0:  clamp(1rem,      0.94rem + 0.30vw, 1.1875rem);  /* 16 -> 19px  */
  --step-1:  clamp(1.125rem,  1.02rem + 0.50vw, 1.4375rem);
  --step-2:  clamp(1.3125rem, 1.10rem + 1.00vw, 1.9375rem);
}
body{ font-size: var(--step-0); }
footer b{ font-size: var(--step--2); }

/* WRONG - the clamp sits on body, so this child is a flat 11.2px forever */
body{ font-size: clamp(1rem, .55rem + .45vw, 1.125rem); }
footer b{ font-size: .7rem; }
```

## 4. Minimum rendered sizes (hard floors)

Three floors, checked at BOTH the `clamp()` minimum and the value resolved at a 1920px viewport. Checking only the resolved 1920px value is the trap: on a 1366px laptop the clamp is usually still pinned at its minimum, so the minimum IS the size most readers get.

| Text role | Floor | Applies to |
|---|---|---|
| Body prose | 16px | `body`, bare `p`, long-form article text |
| Secondary text | 13px | margin notes, captions, footer link lists, credits, eyebrow labels, stat sublabels |
| Interactive text | 12px | anything clickable or focusable - buttons, links in controls, chips, tab labels |

Nothing renders below 12px. The 2026-08-10 defects (unreadable margin notes at 11.5px and a 11.2px footer) sat just under the secondary floor, which is why the floor is stated as a number rather than "small but readable".

SVG text inside a scaled `viewBox` is exempt from these floors, because its declared `font-size` is in user units and the rendered size depends on the SVG's scale factor. The scorer identifies such rules by the presence of a `fill:` declaration in the same block (SVG text is colored with `fill`, HTML text with `color`) and skips them. Diagram label legibility is governed by the diagram-quality contract instead, not by this file.

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

## Verification

- [ ] No top-level band or grid container declares a fixed macro `padding` / `gap` at or above 24px.
- [ ] The type scale is declared once as `:root` custom properties, and `body` references a step token rather than carrying a bare `clamp()` that children cannot inherit.
- [ ] Every font size clears its role floor (16 / 13 / 12px) at BOTH the clamp minimum and at 1920px.
- [ ] Inline emphasis tokens declare both a color and a family or weight change, and the color clears AA.
- [ ] Every ink and accent custom property clears AA against the backgrounds it is used on; no foreground fails against all of them.
- [ ] `python scripts/visual_qa_score.py <out.html>` reports no HIGH-severity `fluid-spacing`, `font-floor`, `emphasis-token`, or `contrast` finding.

## Related

- `references/visual-qa-rubric.md` - the per-segment grading rubric; its `fluid-layout` and `readability-floors` criteria grade this contract from screenshots.
- `references/interactive-features.md` - the full-width canvas contract this composes with; that file governs how wide a band is, this file governs what happens to type and space inside it.
- `scripts/visual_qa_score.py` - the deterministic scorer implementing rules 1, 4, 5, and 6.
