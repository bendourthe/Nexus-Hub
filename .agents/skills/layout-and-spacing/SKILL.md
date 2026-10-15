---
name: layout-and-spacing
description: "Own grouping, spacing scales, breakpoints, and RTL mirroring. Use for layout, spacing, density, alignment, disclosure, or responsive structure. SKIP: focus order (accessibility-engineering) and component architecture (frontend-ui-engineering)."
summary_l0: "Structure UI spatially with grouping, spacing scales, and adaptive breakpoints"
overview_l1: "This skill owns spatial structure: grouping and proximity, alignment and visual reading order, spacing scales and density, progressive disclosure, responsive breakpoints, and logical CSS properties for RTL mirroring. Focus order and heading semantics belong to accessibility-engineering. Truncation mechanics belong to web-typography; this skill decides whether the layout has room or needs an expansion affordance. Component architecture and state belong to frontend-ui-engineering. Match the project's existing styling system."
---

# Layout and Spacing

Decide how UI occupies space: what sits together, how far apart, which axis it follows, and how that structure changes at a narrower viewport or in a right-to-left locale. Values are recipes with escape conditions, not taste sermons.

Match the project's spacing tokens (Tailwind `gap-4`, a `--space-*` scale, theme spacing). Do not invent a parallel scale.

## When to Use This Skill

Use when:

- The user mentions layout, spacing, density, alignment, grouping, grid, stack, breakpoints, progressive disclosure, or RTL mirroring.
- A screen feels cramped, sparse, or spatially random.
- A layout must adapt across viewports or writing directions.

**When NOT to use:**

- Keyboard focus order and semantic structure: `accessibility-engineering`. Visual order is this skill; Tab order is that one.
- How text wraps, truncates, or sizes: `web-typography`. This skill only says whether the *container* has room or needs a "show more" / wrap affordance.
- Component trees, data fetching, and state: `frontend-ui-engineering`.
- Visual polish (radius, elevation, optional motion): `hallmark-design`.

## Quick Reference

| Topic | Read when | File |
|---|---|---|
| Grouping, proximity, alignment | Clusters feel unrelated or a row is accidentally centered | `references/grouping-and-alignment.md` |
| Breakpoints, density, logical properties | Responsive or RTL work | `references/adaptive-breakpoints.md` |

## Instructions

### 1. Group by meaning, then space the groups

Controls that are one action live closer than controls that are different actions. A primary button and its cancel sit in one cluster; a destructive action is separated (gap of two steps on the scale, or a divider), not packed in the same 8px row.

Inside a cluster, use one consistent gap (one step on the project's scale). Between clusters, use a larger step. Do not apply the same gap everywhere; uniform rhythm is how unrelated blocks fuse.

See `references/grouping-and-alignment.md`.

### 2. Align to a reading edge

Default body and forms to the start edge (`text-start`, `align-items: start` / `items-start`), not center. Centering a long reading column or a form with labels is a layout miss unless the surface is a short empty state or a marketing hero the product already uses.

Visual reading order follows the writing direction. In LTR, earlier content is toward the start (left); in RTL it is toward the right. Implement that with **logical properties** (`margin-inline-start`, `padding-inline`, `inset-inline-end`, `ps-` / `pe-` in Tailwind), not `margin-left`. Physical left/right mirroring by hand will drift. Spatial RTL is this skill; `accessibility-engineering` still owns focus order in the DOM.

### 3. Use one spacing scale and two densities at most

Pick the project's scale (4px/8px base is common; use whatever is already in tokens). Name sizes by role, not by pixel in new code: `space-xs` for icon-to-label, `space-sm` inside a control, `space-md` inside a card, `space-lg` between cards, `space-xl` between page sections.

A screen has at most two densities: a compact table/toolbar and a comfortable form/article. Mixing four paddings on one view is noise.

Escape: data-dense admin tables may use the compact density throughout. Marketing pages may use the large section gap throughout. Do not mix both on the same band of content.

### 4. Disclose progressively

Show the primary path. Secondary controls (advanced options, rarely used filters) stay behind a closed disclosure, tab, or "Advanced" link. Do not dump every setting into the first viewport.

A disclosed region is still in the DOM or is rendered on open; do not only CSS-hide focusable controls in a closed drawer without matching `accessibility-engineering`'s inert/hidden rules. This skill decides *whether* it is disclosed; that skill decides *how* it is exposed to AT.

### 5. Breakpoints are structural, not decorative

Define a small set of widths (the project's existing ones; if none, `640` / `768` / `1024` / `1280` CSS pixels is a common set) and change **structure** at those points: stack vs row, 1 vs 2 vs 3 columns, drawer vs side panel. Do not tweak font size at every 40px.

Mobile-first: base styles are the narrow layout; `min-width` media queries add columns. `accessibility-engineering` checks 320px reflow; this skill supplies the stacked structure that makes that check pass.

If a piece of text does not fit, do not silently truncate here. Either give the layout more room (column span, wrap, allow the block to grow) or add an expansion affordance. Truncation ellipsis and `line-clamp` belong to `web-typography`.

### 6. Report

Name the spacing tokens you used. If the project has none, say so and use one ad-hoc scale consistently in the files you touched, without renaming the rest of the codebase.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Center everything; it looks balanced." | Centered forms and long text raise eye-travel cost and fight forms that have start-edge labels. Balance is not the same as a start-aligned reading column. |
| "One 16px gap everywhere is consistent." | Same gap between a label and its field as between two unrelated sections glues the page into one blob. Groups need two gap sizes. |
| "I used left and right so RTL can be a follow-up." | Follow-up never happens. Logical properties cost the same as physical ones and prevent a mirrored-but-broken Arabic layout. |
| "Truncation with ellipsis saves the layout." | If the layout has no room, that is a layout failure. Ellipsis is a typography mechanic; using it to hide an overflow you created is the wrong owner. |
| "Focus order is the same as visual order, so this skill covers both." | CSS `order` and Grid placement can reverse visual order while Tab follows the DOM. `accessibility-engineering` owns Tab; this skill owns the spatial arrangement. |

## Verification

- [ ] Related actions share a smaller gap than unrelated sections (at least two steps on the scale).
- [ ] Reading text and forms align to the start edge unless the surface is a short empty state or an existing centered marketing block.
- [ ] Spacing uses the project's tokens (or one documented ad-hoc scale if none exist); no random pixel values mixed with tokens in the same view.
- [ ] Secondary controls are behind a disclosure, not all visible on first paint, unless the view is a settings page whose job is to show them.
- [ ] Narrow breakpoint is a stacked structure (`min-width` enhancements), not a squeezed row with horizontal page scroll.
- [ ] Inline spacing uses logical properties (`*-inline-*`, `ps`/`pe`), not `left`/`right`, unless the value is truly physical (a box-shadow offset that must not flip).
- [ ] Overflowing text was given room or an expansion control; `line-clamp` was not used as the first layout fix.
- [ ] Component architecture was not redesigned in this pass (`frontend-ui-engineering` owns that).

## Related Skills

- `accessibility-engineering` -- focus order, names, hit areas; this skill owns spatial grouping only
- `web-typography` -- truncation, measure, wrapping; this skill owns container room
- `frontend-ui-engineering` -- components and state
- `interface-copy` -- the words in empty states and disclosures
- `hallmark-design` -- visual polish after structure is set
- `interface-review` -- coordinating review
