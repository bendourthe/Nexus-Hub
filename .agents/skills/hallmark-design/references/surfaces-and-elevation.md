# Surfaces and Elevation

Judgment first: `hallmark-design` gate 8/9 (constrained palette, scarce accent) and gate 22 (cards need a reason) decide whether a surface exists. This file is the recipe once a surface is warranted.

## Three layers, not a stack of shadows

Name three roles and stop:

| Role | Job | Recipe |
|---|---|---|
| `bg` | Page or app chrome | Flat fill. No shadow. |
| `surface` | Grouped content that sits on `bg` | 1px `border` token when luminance is close to `bg`; optional short shadow if the border is not enough. |
| `overlay` | Modal, popover, menu | Scrim `rgb(0 0 0 / 0.4)` (or the project's overlay token) plus a stronger shadow than `surface`. |

A fourth "floating FAB" layer is allowed. A sixth nested card-in-card-in-card is not.

## Shadow recipe

Prefer two stacked shadows over one heavy drop:

- Raised card: `0 1px 2px rgb(0 0 0 / 0.06), 0 8px 24px rgb(0 0 0 / 0.08)`.
- Overlay: `0 2px 8px rgb(0 0 0 / 0.12), 0 16px 48px rgb(0 0 0 / 0.16)`.

Escape: a dense data table does not need a card shadow; a 1px row divider is enough. Escape: a project token file already defines `--shadow-*`; use those names, do not invent a parallel stack.

Do not combine a thick colored outline, a glow, and a drop shadow on the same control. Pick border *or* shadow unless the control is the single primary action.

## Hairline borders

`1px` (or `1px` logical `border-width`) using the `border` role from `color-systems`. `2px` only on the focused or selected state, and even then `accessibility-engineering` owns whether that ring is the focus indicator.

Dark-on-dark surfaces: raise the border token's L until the edge is visible; do not "fix" a disappearing card by adding a second shadow.
