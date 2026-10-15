# OKLCH Palettes

## Why not HSL

HSL's lightness channel does not track perceived brightness. `hsl(60 100% 50%)` (yellow) and `hsl(240 100% 50%)` (blue) share `50%` and do not look equally bright. A generated gray ramp in HSL therefore looks uneven across hues, and you end up hand-correcting every step.

OKLCH uses lightness, chroma, and hue with a lightness axis that is built to be perceptually even. Equal L steps look like equal brightness steps across hues. That is why it is the default for **new** scales in this skill.

OKLCH does not make a palette accessible by itself. You still measure pairs.

## Coordinates

`oklch(L C H)` in modern CSS: L is 0-1 or 0%-100% (both appear in the wild; pick one per file and stay), C is chroma (0 is gray; many sRGB-safe UI colors sit under ~0.2, not 0.4+), H is hue angle 0-360.

## Recipe for a 11-step ramp (50-950 style)

1. Lock H to the brand hue.
2. Choose a mid chroma for step 500 (the "brand" stop).
3. Step L from ~0.97 (50) to ~0.15 (950).
4. Reduce C toward 0 at 50 and 950. High C at extreme L is the usual out-of-gamut case; the browser will map it by cutting chroma, and the step will not look like the number you wrote.

Hover/active: `color-mix(in oklch, var(--accent) 85%, black)` or mix with white. Mixing `in oklch` avoids the muddy midpoint `in srgb` often produces.

## What not to do

- Do not keep C constant across the whole ramp.
- Do not treat L as a contrast guarantee (a light accent on white can share a "high L" and still fail).
- Do not rewrite a shipped hex brand of record into a nearby OKLCH without checking the measured pair and the brand owner (`brand-styling` if they have tokens).
