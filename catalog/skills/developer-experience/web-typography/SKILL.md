---
name: web-typography
description: "Own web font loading, type scales, wrapping, and truncation. Use for typography, fonts, line-height, letter-spacing, measure, or variable fonts. SKIP: heading semantics (accessibility-engineering) and the words (interface-copy)."
summary_l0: "Load, scale, wrap, and truncate web type without restating heading semantics"
overview_l1: "This skill owns how text renders: font formats and loading, variable-font axes and OpenType features via real CSS properties, named type scales, visual heading size, line-height and letter-spacing by role, measure, wrapping, widows, truncation, smart punctuation, and mixed-direction runs. accessibility-engineering owns heading ranks and when contrast is required. color-systems measures the pair. layout-and-spacing owns container room and spatial RTL. interface-copy owns the words. Match the project's existing styling system."
---

# Web Typography

Control how text is loaded, sized, spaced, wrapped, and cut off. Give a number or a named token plus the escape condition. Do not restate heading *ranks* (one `h1`, no skipped levels): that is `accessibility-engineering`. Do not rewrite the words: that is `interface-copy`.

## When to Use This Skill

Use when the user mentions typography, type scale, fonts, variable fonts, line-height, letter-spacing, measure, wrapping, truncation, `font-display`, or OpenType features.

**When NOT to use:**

- Heading outline and contrast severity: `accessibility-engineering`.
- Measuring or changing colors: `color-systems`.
- Whether the layout has room: `layout-and-spacing`.
- Source wording: `interface-copy`.

## Quick Reference

| Topic | File |
|---|---|
| Formats, loading, `font-display`, metric matching | `references/font-loading.md` |
| Variable axes and CSS properties vs raw tags | `references/variable-fonts-and-opentype.md` |
| Scale, heading size, leading, tracking, measure | `references/spacing-and-sizing.md` |
| Wrap, clamp, punctuation, mixed direction | `references/wrapping-and-punctuation.md` |
| Property-to-utility cheat sheet | `references/property-utility-cheatsheet.md` |

## Instructions

### 1. Load fewer faces, on purpose

Prefer `woff2`. One family for UI plus an optional mono is enough unless the product already ships more. Subset if the project already has a subsetting step; do not add a build tool just for this pass.

`font-display: swap` is the default for body UI (text appears immediately). `optional` is for nice-to-have display faces on marketing. `block` is almost never right for UI. See `references/font-loading.md`.

### 2. Prefer CSS properties over raw feature tags

If a CSS property exists, use it: `font-weight`, `font-stretch` / `font-width`, `font-style`, `font-variation-settings` only for axes with no property. `font-feature-settings` is a last resort; `font-variant-*` (`numeric`, `ligatures`, `caps`) is preferred. Details in `references/variable-fonts-and-opentype.md`.

### 3. Name sizes by role, then map to a scale

Use the project's type tokens. If none exist, a 1.25 modular scale from a 16px / `1rem` body is a reasonable default (body, small, h3, h2, h1). Do not pick four unrelated pixel sizes on one view.

Visual heading size must still descend: the `h1` looks larger than `h2`, and so on. The *element* chosen for that size is `accessibility-engineering`'s rule. Styling an `h2` to look like a display `h1` without changing the rank is allowed when the outline is already correct; do not skip ranks to get a size.

Line-height: body 1.5 to 1.6; UI labels 1.25 to 1.4; display headings 1.1 to 1.25. Escape: a single-line button label can be `line-height: 1` inside a padded hit area that `accessibility-engineering` already sized.

Letter-spacing: body at 0. Extra tracking on small caps or on very large display type (0.02-0.04em) is optional. Negative tracking on body copy is a no.

Measure: body columns 45-75 characters (`max-width: 65ch` is a solid default). Full-viewport paragraphs fail this. Escape: code blocks, tables, and URLs may exceed it.

### 4. Wrap first, truncate last

`overflow-wrap: anywhere` (or `break-word` where the project already uses it) on user-generated strings. `text-wrap: pretty` on headings and short marketing lines (escape: very long running articles where the extra layout cost is measurable). `text-wrap: balance` on two-line headings, not on body.

Truncation (`text-overflow: ellipsis`, `line-clamp`) only after `layout-and-spacing` has decided the container cannot grow and there is an expansion affordance or a title attribute / tooltip is insufficient for AT. Truncation without an accessible full string is an `accessibility-engineering` miss; supply the full text in a name or a disclosed region.

### 5. Punctuation and mixed direction

In product UI, use the locale's quotes and separators. Do not force ASCII hyphens into a French UI or curly quotes into a codebase whose style guide is ASCII for Markdown. `lang` on the page is `accessibility-engineering`; this skill sets `hyphens: auto` only when `lang` is present and the line length is narrow.

A phrase in another direction gets `dir="auto"` or an explicit `dir` on that span. Do not set `unicode-bidi: bidi-override` unless you are repairing a known broken string.

### 6. Contrast of the glyphs

If text fails contrast, do not "fix" it by thickening a weight blindly. Grade via `accessibility-engineering`, measure via `color-systems`, then change color or (if the design allows) increase size into the large-text bucket *only when that skill says size is an accepted mitigation*.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The heading looks bigger, so the outline is fine." | Visual size is this skill; skipped ranks are `accessibility-engineering`. A huge `div` is not an `h1`. |
| "Ellipsis keeps the row tidy." | If the row has no room, that is layout. Clamping body copy hides meaning from everyone who cannot hover. |
| "I'll set liga via font-feature-settings because I always do." | `font-variant-ligatures` is the property. Raw tags fight the cascade and are harder to turn off. |
| "Swap causes a flash, so I'll use block." | Invisible text for seconds is worse than a swap flash for UI. Use `optional` if the face is decorative. |

## Verification

- [ ] Faces are `woff2` (plus an existing fallback stack); `font-display` is `swap` or a documented exception.
- [ ] Sizes come from tokens or one modular scale, not ad-hoc pixels mixed in the same view.
- [ ] Body line-height is 1.5-1.6; display headings are tighter; body tracking is 0.
- [ ] Body measure is within 45-75ch or a documented exception (tables, code).
- [ ] Truncation is used only after a layout affordance decision, with the full string available to AT.
- [ ] Variable axes use CSS properties where they exist.
- [ ] Heading *ranks* were not changed to chase a visual size (`accessibility-engineering` owns ranks).
- [ ] The words themselves were not rewritten (`interface-copy`).

## Related Skills

- `accessibility-engineering` -- heading ranks, contrast severity, names
- `color-systems` -- measure and remediate the pair
- `layout-and-spacing` -- container room, spatial RTL
- `interface-copy` -- the source strings
- `theme-tokens` / `brand-styling` -- apply a supplied font pairing, do not invent one if the user already has tokens
- `interface-review` -- coordinating review
