# Adaptive Breakpoints and Logical Properties

Read this when the layout must change with viewport width, container width, or writing direction.

## Breakpoint discipline

Use the project's existing breakpoints. If the project has none, add as few as will change structure:

| Role | Typical `min-width` | What may change |
|---|---|---|
| Compact | (base, no query) | Single column, stacked actions, drawers instead of sidebars |
| Comfortable | 768px | Two columns, label beside field if the form is short |
| Wide | 1024px or 1280px | Persistent nav, extra column, table instead of card list |

Do not add a breakpoint whose only job is a 4px padding change. That is density fidgeting, not adaptation.

Prefer **container queries** (`@container`) when a card must adapt inside a variable-width slot (dashboard widgets). Viewport queries remain correct for page chrome (nav, grid of the whole main). Mixing them is fine; mixing five of each is not.

## Density at breakpoints

A comfortable form on desktop may become compact on a phone by reducing padding one step, not by shrinking type (that is `web-typography` and `accessibility-engineering` zoom). Keep tap targets at the sizes `accessibility-engineering` requires; compact density never means 16px icon-only buttons with no padding.

## Logical properties (RTL spatial mirroring)

Inline axis follows writing direction. Block axis (top/bottom) usually does not flip.

Use:

- `margin-inline-start` / `ms-*` instead of `margin-left`
- `padding-inline` / `px-*` when both sides should flip together
- `inset-inline-end` for a close button on the "trailing" edge
- `text-start` instead of `text-left`
- `border-inline-start` for a start-edge accent bar

Do not flip:

- Box-shadow X offsets that represent a light source (physical)
- Background images that are photographs (physical)
- Maps and canvases that are geographic (physical)

A row of `[icon][label]` becomes `[label][icon]` in RTL if you used a flex row with default `row` and start alignment; that is correct. If the icon must stay on the "outside" toward the viewport edge, use `flex-direction: row` plus `margin-inline-start: auto` on the trailing item rather than `float: right`.

`dir="rtl"` on a subtree (a Hebrew quote inside an English page) should flip only that subtree. Page chrome stays with the document `dir`.

## Overflow is a layout decision first

If a sidebar + content row overflows at 320-640px, the structural fix is stacking, not `overflow-x: auto` on the whole page. Inner tables and code blocks may scroll on the inline axis; the page's reading column may not.

When a title is longer than its column: wrap first. If wrapping breaks an adjacent action row, move the actions under the title (stack) at the compact breakpoint. Only after the container has been given a real structure should `web-typography` apply a clamp.
