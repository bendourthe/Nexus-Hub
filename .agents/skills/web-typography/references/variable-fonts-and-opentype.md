# Variable Fonts and OpenType

## Axes: properties first

| Axis | CSS property | Notes |
|---|---|---|
| Weight (`wght`) | `font-weight` | 100-900; variable files often accept the whole range |
| Width (`wdth`) | `font-stretch` / `font-width` | Percent; `condensed` keywords where they map |
| Italic / slant | `font-style: italic` or `oblique` | Prefer a true italic face if the file has one |
| Optical size (`opsz`) | `font-optical-sizing: auto` | Let the UA pick; pin only if a size looks wrong |
| Other registered or custom | `font-variation-settings` | Last resort; reset unused axes when overriding |

Do not write `font-variation-settings: "wght" 500` when `font-weight: 500` works. Variation-settings does not inherit the same way and is easy to clobber.

## Features: variant properties first

| Goal | Property |
|---|---|
| Ligatures on/off | `font-variant-ligatures` |
| Tabular vs proportional numbers | `font-variant-numeric: tabular-nums` / `proportional-nums` |
| Oldstyle numbers | `font-variant-numeric: oldstyle-nums` |
| Small caps | `font-variant-caps: small-caps` |
| Kerning | `font-kerning: normal` (usually default) |

`font-feature-settings: "tnum" 1` is the escape when a feature has no property. Comment why.

Tables and prices use tabular nums so digits line up. Running prose uses proportional nums. Mixing them in one number is a fail.

## Italic vs fake oblique

If the family has an italic file or an italic axis, use it for emphasis. `font-style: italic` on a roman-only file synthesizes a slant that reads as cheap. Prefer `<em>`/`<i>` with a real italic face, or weight/color emphasis if there is no italic (still a language of `interface-copy` for the words).

## Performance

One variable file replacing four static weights is usually a win. Two variable files (roman + italic) is normal. A variable file plus the same weights as static files is a miss unless you are mid-migration.
