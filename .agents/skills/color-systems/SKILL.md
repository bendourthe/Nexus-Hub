---
name: color-systems
description: "Build palettes in OKLCH, measure contrast pairs, and map gamut fallbacks. Use for color system, palette, contrast pair, or OKLCH. SKIP: applying supplied tokens (theme-tokens, brand-styling) and contrast severity (accessibility-engineering)."
summary_l0: "Construct OKLCH palettes and remediate measured contrast pairs"
overview_l1: "This skill owns color construction and repair: OKLCH over HSL for even lightness steps, palette generation, measuring a rendered contrast pair, remediating a miss, gamut mapping and sRGB fallbacks, semantic roles and theming, and the restraint that coloring every action leaves nothing primary. accessibility-engineering decides when contrast is required and how severe a miss is. theme-tokens and brand-styling apply tokens the user already has. Match the project's styling system."
---

# Color Systems

Build a palette, measure the pair the user actually sees, and change the colors until the owning accessibility grade is met. Do not invent a second contrast policy. `accessibility-engineering` already decided whether contrast applies and how bad a miss is; this skill supplies the number and the new tokens.

## When to Use This Skill

Use when the user mentions a color system, palette, OKLCH, contrast pair, gamut, semantic color roles, light/dark theme tokens, or remediating a failed contrast check.

**When NOT to use:**

- Applying a curated or brand JSON the user already has: `theme-tokens` or `brand-styling`.
- Deciding that contrast is required or assigning blocker vs advisory: `accessibility-engineering`. If that skill is unavailable, mark severity as not covered, still measure the ratio, and do not guess a grade.
- Anti-slop "no purple gradient" taste: `hallmark-design`. This skill will still refuse to paint every button a unique hue (restraint below).

## Quick Reference

| Topic | File |
|---|---|
| Why OKLCH, how to step L and C | `references/oklch-palettes.md` |
| Measuring the rendered pair (WCAG 2 formula) | `references/contrast-measurement.md` |
| Gamut, P3, fallbacks | `references/gamut-and-fallbacks.md` |
| Roles, themes, restraint | `references/roles-and-theming.md` |

## Instructions

### 1. Prefer OKLCH for new scales

HSL lightness is not perceptually even: the same `L` on yellow and on blue does not look equally bright. OKLCH lightness is built to match perceived brightness, so a 10-step scale can share one L ramp across hues.

Recipe: pick a hue, pick a chroma the sRGB screen can hold, then step L (for example 0.97 down to 0.15) to get 50-950 style ramps. Drop chroma at the lightest and darkest steps; keeping max chroma there is how you fall out of gamut. See `references/oklch-palettes.md`.

If the project is hex-only and the user did not ask to migrate, derive states with `color-mix(in oklch, var(--accent) 80%, white)` rather than rewriting the whole token file.

### 2. Measure the rendered pair

Do not contrast-check the token in Figma isolation if the UI composites on a different background, uses opacity, or places text on a gradient/image.

1. Read computed foreground and the background behind it (include alpha by compositing onto what is actually under the text).
2. Convert to sRGB 0-1, apply the sRGB linearization, then relative luminance `L = 0.2126 R + 0.7152 G + 0.0722 B`.
3. Contrast ratio `(lighter + 0.05) / (darker + 0.05)`.

That is the WCAG 2 ratio. APCA (Lc) is optional extra signal and is **not** a WCAG 2 substitute. Details in `references/contrast-measurement.md`.

Hand the ratio to `accessibility-engineering`'s severity table. Do not duplicate that table here.

### 3. Remediate by changing L, then C, then hue last

To raise contrast: move text L away from background L in OKLCH (darker text on light bg, lighter text on dark bg). Keep hue unless the brand color cannot meet the grade at any L, in which case darken/lighten the brand token or use the `fg` role on that surface instead of the brand hue.

If the browser gamut-mapped a high-chroma color and the measured pair still fails, lower chroma until the color is in-gamut *and* the ratio meets the grade. Do not crank chroma to "make it pop" on a fail.

### 4. Roles, not a rainbow

Name tokens by role (`bg`, `fg`, `muted-fg`, `accent`, `danger`, `border`), not by hue (`blue-500` as the only name). A second accent is allowed; a fifth "primary" is not. Coloring every action equally leaves no primary. See `references/roles-and-theming.md`.

Light and dark themes should share role names and flip L ramps, not invent new role sets.

### 5. Fallbacks

`oklch()` is widely supported in current evergreen browsers. If the project's support table includes engines without it, keep an sRGB hex (or `rgb()`) before the `oklch()` in the same cascade, or gate with `@supports`. Do not emit P3-only values with no sRGB fallback. See `references/gamut-and-fallbacks.md`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I eyed it; it's fine." | Measurement is this skill's job. Eyeballing is how a failing pair ships as if it met the grade `accessibility-engineering` assigned. |
| "I'll copy the WCAG thresholds into this skill so I don't have to load two." | Two copies drift. Severity lives in `accessibility-engineering`. |
| "HSL is simpler so I'll generate the ramp there." | Equal HSL L is not equal brightness. The ramp will look uneven and you will hand-tweak every hue. |
| "APCA is newer so I'll ignore WCAG 2." | WCAG 2 is what this catalog's accessibility skill grades. APCA may inform a design, it does not replace that grade. |
| "Every button should have a unique color for clarity." | Then nothing is primary. Roles plus one accent; danger is the exception. |

## Verification

- [ ] New ramps are stepped in OKLCH (or `color-mix(in oklch, ...)`) unless the user forbade a format change.
- [ ] Each reported pair is a **rendered** pair (computed colors, compositing included), not a token in isolation.
- [ ] The WCAG 2 ratio was computed; severity was taken from `accessibility-engineering` or marked not covered if that skill is missing.
- [ ] Remediation changed L (and C if out of gamut) and kept role names stable.
- [ ] sRGB fallback exists if the project supports engines without `oklch()`.
- [ ] Not every action has a distinct hue; accent and danger are limited.
- [ ] `theme-tokens` / `brand-styling` were used instead when the user already supplied tokens.

## Related Skills

- `accessibility-engineering` -- when contrast is required and how severe a miss is
- `web-typography` -- size/weight after a pair is measured (large-text bucket is that skill plus a11y, not a color cheat)
- `hallmark-design` -- anti-slop color taste (gradients, rainbow UI)
- `theme-tokens` -- apply a bundled generic theme JSON
- `brand-styling` -- apply the user's brand JSON
- `interface-review` -- coordinating review
