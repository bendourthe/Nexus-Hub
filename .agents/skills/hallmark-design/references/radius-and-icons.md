# Radius and Icons

## Radius scale

Pick one scale per product and reuse it. A workable default when the project has none:

| Token | Value | Use |
|---|---|---|
| `radius-sm` | 6px | Inputs, small buttons, chips' inner corners |
| `radius-md` | 10px | Cards, menus, dialogs |
| `radius-lg` | 16px | Large sheets, marketing panels |
| `radius-full` | 9999px | Avatars, circular icon buttons, pill chips only |

Mixing a 4px input with a 24px button on the same form is the slop tell this recipe exists to stop.

Nested corners: inner radius = outer radius minus the padding that separates them (optical nesting). If that would go below 2px, square the inner corners instead of inventing a fifth token.

Escape: a design-system file already publishes `--radius-*`. Map to those; do not add a competing scale.

## Icon stroke and optical size

One stroke weight per view. Default: 1.5px or 2px at a 24px optical size. Do not mix 1px hairline icons with 3px chunky icons in one toolbar.

Optical sizes:

- 16px inline with body or 14px UI text.
- 20px to 24px inside buttons and nav items.
- 32px and above only as an empty-state illustration, not as a dense toolbar glyph.

Filled vs outline: outline is the default. Fill the current/selected item only. Mixing random filled and outline glyphs in one row reads as two icon sets.

Align the glyph to the adjacent label's cap height. Centering an icon in a 44px hit area (sized by `accessibility-engineering`) is correct for the tap target; the *glyph* still sits on the text centerline when a label is present.

Escape: the product ships a single icon font or SVG sprite with a fixed viewBox. Keep that viewBox; do not restroke third-party logos.
