# Roles and Theming

## Role names

A UI palette is a set of jobs, not a box of crayons.

| Role | Job |
|---|---|
| `bg` / `fg` | Page or surface background and default text |
| `muted-fg` | Secondary text; still measured against `bg` |
| `accent` | The one primary action / link color |
| `danger` | Destructive / error |
| `border` | Non-text UI; still measured when it identifies a control |
| `focus` | Focus ring; measured as non-text contrast |

You may have `accent-muted` for backgrounds behind accent text. You may not have six "primary" hues.

## Restraint

If every button is a different saturated color, none of them is primary. Default buttons are `fg` on `bg` with a border; the one primary is `accent`. Danger is reserved for destroy/abort.

This overlaps `hallmark-design`'s "accent is scarce" gate. This skill states it as a **token** rule (do not add roles). Hallmark states it as a **visual** gate. Do not copy Hallmark's full anti-slop list here.

## Light and dark

Same role names. Dark theme is not "invert every hex". Re-step L so `fg` stays lighter than `bg` in dark mode, then **re-measure** every pair you ship (links on tinted surfaces fail first).

`color-scheme: light dark` on `:root` lets form controls follow the theme. Pair it with your tokens; do not rely on it alone for branded chrome.

## When the user already has tokens

Stop. `brand-styling` or `theme-tokens` apply those files. This skill may still *measure* pairs in the running UI and propose L adjustments as a patch to their tokens, rather than replacing their JSON with a generated OKLCH rainbow.
