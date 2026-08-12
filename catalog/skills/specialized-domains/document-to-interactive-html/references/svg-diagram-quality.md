# SVG Diagram Quality Contract

The authoring rules for hand-written inline SVG diagrams, and the checks that verify them. It exists because an authored SVG is CODE, and its coordinates are unchecked code: a diagram can be well-formed, offline, correctly sized, and still ship as unrecognizable artwork. A real run (2026-08-10) shipped a dashed loop-back arrow whose arrowhead floated disconnected from its line, connectors that lost their arrowheads entirely partway down a pipeline, a label sitting directly on top of the dashed curve it annotated, and a pinned scrollytelling graphic taller than the viewport, so its bottom two stages were never visible.

Five rules. `scripts/visual_qa_score.py` enforces rules 1, 4, and part of 5 deterministically; rules 2 and 3 are verified by the geometry self-check in rule 5 and graded from screenshots against the criteria stated here.

## 1. Arrowheads are `<marker>` elements

An arrowhead is declared once as a `<marker>` in `<defs>` and attached with `marker-end` (or `marker-start` / `marker-mid`). It is never a separate hand-placed triangle path.

A hand-placed triangle is a second object that merely happens to sit near the end of a line. The moment the geometry shifts - a node moves, a viewBox changes, a curve's control points are retuned - the triangle stays where it was and the arrow visibly comes apart. That is exactly the 2026-08-10 defect: a dashed loop-back curve ending at `(96,40)` with an independent `M96 40 l -5 -8 l 10 0 z` triangle beside it. A marker cannot detach, because it is positioned by the path it belongs to.

Markers must set `orient="auto"` so the head rotates to the path's tangent, and `markerUnits="strokeWidth"` so it scales with the line rather than staying a fixed size when the stroke thickens. Set `refX` so the marker's TIP lands on the path's endpoint; otherwise the head overshoots into whatever the line was pointing at.

```xml
<!-- CORRECT - one marker definition, reused, cannot detach -->
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7"
          orient="auto" markerUnits="strokeWidth">
    <path d="M0 0 L10 5 L0 10 z" fill="currentColor"/>
  </marker>
</defs>
<path d="M150 66 L150 96" stroke="currentColor" fill="none" marker-end="url(#arrow)"/>

<!-- WRONG - a floating triangle that detaches the first time geometry moves -->
<path d="M424 46 C 424 18, 120 18, 96 40" fill="none" stroke="#4f6d8a" stroke-dasharray="4 4"/>
<path d="M96 40 l -5 -8 l 10 0 z" fill="#4f6d8a"/>
```

Observable criterion: no small closed filled triangle path exists anywhere in the document (three vertices, a `z`, bounding box under ~24 user units), and every connector that expresses direction carries a `marker-*` attribute. Severity HIGH - a broken arrow is the most visually damaging defect in this class, and it is the one a reader notices first.

Apply the arrowhead consistently. A pipeline whose first connector has a head and whose remaining three do not reads as an incomplete drawing, not as a deliberate choice.

## 2. Dash patterns must not collide with markers or text

No `stroke-dasharray` segment may pass within a label's bounding box. A dashed line crossing text fragments both: the dashes break up the glyphs and the glyphs break up the dashes, and the result reads as neither.

Fix it by moving the label clear of the path, or by carving the path around the label - never by hoping the two miss each other.

```xml
<!-- WRONG on two counts: the label sits ON the path (the curve's midpoint is
     (286.5, 245) and the label is centred at (288, 248) - the same 2 user
     units), AND it is rotated, which is a readability defect in itself. -->
<path class="loopback" d="M270 368 C 292 368, 292 122, 270 122"/>
<text x="288" y="248" transform="rotate(90 288 248)" text-anchor="middle">re-plan</text>

<!-- CORRECT - widen the viewBox, keep the label HORIZONTAL and clear of the
     path, wrapping onto a second line with tspan when the space is narrow -->
<path class="loopback" d="M272 368 C 320 368, 320 122, 272 122" marker-end="url(#arrow)"/>
<text x="336" y="238" text-anchor="middle">
  <tspan x="336" dy="0">target not met?</tspan>
  <tspan x="336" dy="1.2em">re-plan</tspan>
</text>
```

Verify by evaluating the curve, not by looking at it. For a cubic Bezier the midpoint is `(P0 + 3*P1 + 3*P2 + P3) / 8`; compare it against the label's box. Two numbers settle what a glance cannot.

**Do not rotate label text.** Rotation is not a space-saving technique to apply carefully - it is a readability defect, and a reviewer reads it as one immediately. A reader should never have to tilt their head to follow a diagram. When a label does not fit horizontally, widen the `viewBox` and wrap onto a second line with `tspan`; both are cheap, and the viewBox costs nothing at render time because the SVG scales to its container either way. Reserve `rotate()` for the genuinely unavoidable case - a dense axis of many long category labels - and never for a single annotation.

## 3. Connectors terminate on node edges

Every connector's endpoints lie on the BOUNDARY of the two shapes it joins, computed from those shapes' geometry. Not their centers, not an arbitrary nearby coordinate, and not a value tuned until it looked close.

For a box at `x, y, width, height`, the bottom-edge midpoint is `(x + width/2, y + height)` and the top-edge midpoint is `(x + width/2, y)`. A connector between two vertically stacked boxes runs from the first expression to the second. Deriving the endpoints this way means a node can be moved by editing one rect and the connectors still land correctly.

```xml
<!-- CORRECT - box 1 is y=14 h=52, box 2 is y=96; the connector spans 66 -> 96 -->
<rect x="30" y="14"  width="240" height="52"/>
<path d="M150 66 L150 96" marker-end="url(#arrow)"/>
<rect x="30" y="96" width="240" height="52"/>
```

## 4. Viewport fit for pinned and sticky graphics

A pinned scrollytelling graphic must fit ENTIRELY inside its sticky viewport slot. A graphic taller than the slot loses its bottom, and because the container is sticky the reader can never scroll to the missing part - the graphic is pinned, so the hidden region stays hidden for the whole section.

Constrain the height explicitly against the sticky offset, and choose a viewBox aspect that shows every node at once on a 1080p display. Remember that the usable height is the viewport minus the sticky offset minus browser chrome, which on a 1080p laptop at 125% scaling is closer to 700px than to 1080px.

```css
/* BEST - pin the height to the slot and derive the width from it, so the graphic
   fills the slot exactly instead of letterboxing inside a too-tall box */
.rail-sticky{ position: sticky; top: 5.5rem; }
.rail-sticky svg{
  display: block;
  height: calc(100vh - 7.5rem);   /* the sticky offset plus breathing room */
  width: auto;                    /* derived from the capped height */
  max-width: 100%;                /* and never wider than its track */
  margin-inline: auto;
}

/* ALSO CORRECT - a max-height cap; preserveAspectRatio letterboxes rather than crops */
.rail-sticky svg{ width: 100%; height: auto; max-height: calc(100vh - 7rem); }

/* WRONG - a 300x470 viewBox at width:100% in a 500px track renders 783px tall,
   so the bottom two stages fall outside a 700px slot and cannot be scrolled to */
.rail-sticky svg{ width: 100%; height: auto; }
```

The first form is preferred: `height` + `width: auto` + `max-width: 100%` makes the graphic exactly fill its slot, whereas a `max-height` cap on a `width: 100%` element letterboxes inside a box that is still full-width. Note the `max-width: 100%` - without it, deriving width from a capped height can push the graphic WIDER than its track and scroll the page sideways.

Observable criterion: every `<svg>` inside a `position: sticky` / `position: fixed` container is height-constrained, by either a `max-height` or a viewport-relative `height`. Severity HIGH - content that cannot be reached by any user action is not a styling preference.

## 5. Geometry self-check before shipping

After authoring, verify the drawing numerically rather than trusting how it reads in the source. Authored SVG is code, and these are the assertions:

- Every coordinate lies inside the `viewBox`. A node at `y=470` in a `0 0 300 470` box sits exactly on the edge and its stroke is half clipped.
- Every `marker-*="url(#id)"` resolves to a defined `<marker>`, and every defined marker is referenced. A dangling reference renders NO arrowhead, silently.
- No label's bounding box intersects a path (rule 2). Compute the curve; do not eyeball it.
- Connector endpoints match the box-edge expressions (rule 3).
- Text colors come from the page's palette tokens rather than hardcoded hexes. A literal hex in a presentation attribute is invisible to the CSS contrast check in `references/responsive-typography.md` rule 6, so it silently keeps a value the palette has since abandoned - this is how the 2026-08-10 diagrams kept an accent measuring 3.17:1 after the token itself was corrected.

Note that SVG text is exempt from the pixel font floors in `references/responsive-typography.md` rule 4, because its declared size is in viewBox user units and the rendered size depends on the scale factor. That exemption is not a licence for illegible labels: compute the effective rendered size as `declared_size * (rendered_width / viewBox_width)` and hold it to the same 13px secondary floor.

## Verification

- [ ] No hand-placed triangle arrowhead paths remain; every directional connector uses `marker-end` with `orient="auto"` and `markerUnits="strokeWidth"`.
- [ ] Arrowheads are applied consistently - no diagram where some connectors have heads and others do not.
- [ ] No `stroke-dasharray` path passes within a label's bounding box, verified by computing the curve.
- [ ] No label text is rotated. Where a label did not fit horizontally, the viewBox was widened or the label wrapped with `tspan` instead.
- [ ] Connector endpoints are derived from the joined shapes' edge geometry.
- [ ] Every `<svg>` in a sticky or fixed container carries a `max-height`, and all nodes are visible at once on a 1080p display.
- [ ] Every marker reference resolves; every defined marker is used; all coordinates lie inside the viewBox.
- [ ] `python scripts/visual_qa_score.py <out.html>` reports no HIGH-severity `svg-arrowhead`, `svg-viewport-fit`, or `svg-marker-integrity` finding.

## Related

- `references/responsive-typography.md` - the fluid-layout and readability contract; it owns type and space in HTML flow and defers SVG label legibility to rule 5 here.
- `references/visual-qa-rubric.md` - criterion 8 (`diagram integrity`) grades this contract, pairing the structural checks with the agent-vision judgment that every arrow reads as one object.
- `references/figure-reconstruction.md` - governs SVG REBUILT from a source figure (maps, diagrams) and its label-survival gate; this file governs SVG authored fresh.
- `scripts/visual_qa_score.py` - the deterministic scorer implementing rules 1, 4, and the marker half of rule 5.
