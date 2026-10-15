# Grouping and Alignment

Read this when a view looks randomly sprinkled, over-centered, or when two actions that belong together sit farther apart than two actions that do not.

## Proximity is meaning

Users infer a group from nearness. If "Save" is 48px from "Cancel" and 16px from "Delete", Delete looks like the partner of Save.

Recipe:

- **Intra-cluster gap**: one step on the scale (often 8px / `gap-2` / `--space-sm`).
- **Inter-cluster gap**: at least two steps larger (often 24px / `gap-6` / `--space-lg`).
- **Section gap**: one more step (often 40-48px / `gap-10`).

Escape: a compact toolbar of equal-weight icon buttons may use the intra-cluster gap only. Then hit-area spacing from `accessibility-engineering` still applies.

## Alignment recipes

| Surface | Default |
|---|---|
| Form labels and fields | Start-aligned; labels above fields on narrow, beside on wide if the project already does two-column forms |
| Page title + body | Start-aligned; title and body share the same inline start edge |
| Short empty state (icon, one sentence, one button) | Centered is allowed; keep the block narrow (`max-width` ~20rem) so it does not become a centered article |
| Numeric tables | Tabular numbers; align numeric columns end (right in LTR) so digits line up |
| Media + caption | Caption shares the media's start edge, not the viewport center |

Do not mix start-aligned body copy with a centered heading of the same column. The heading should share the body's edge.

## Grids vs stacks

Use a stack (column flex / block flow) for a single reading path. Use a grid when items are peers (cards, image gallery, key-value pairs).

A three-equal-card row as the only content of a landing band is a `hallmark-design` anti-slop issue; this skill's rule is narrower: if you do use a card grid, the gap between cards is the inter-cluster gap, and the grid collapses to one column at the narrow breakpoint rather than shrinking cards below a readable measure.

## Optical vs geometric center

Icons next to labels often need a 1-2px optical nudge because the glyph's bounding box is not the ink. Prefer `items-center` on the flex row and a consistent icon box (`size-4` / `size-5`) over per-icon magic margins. If a specific glyph still looks low, nudge that glyph only.

## Do not use layout to fake hierarchy

Larger padding is not a heading. If the block is a section, it needs a heading in the DOM (`accessibility-engineering` owns the rank). This skill only sets the space around that heading: closer to its section content than to the previous section (proximity).
