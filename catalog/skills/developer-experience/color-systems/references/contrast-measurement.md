# Contrast Measurement

This file is the procedure. Thresholds and severity live in `accessibility-engineering`. If that skill is missing, compute the ratio anyway, report the number, and mark severity as not covered.

## What pair?

Foreground is the text or icon. Background is whatever is **behind that ink** after opacity: a parent `background-color`, a stacked semi-transparent layer composited on white/black/theme bg, or a sample of the pixels under the glyph if the fill is an image (pick a typical region, not the one lucky bright spot).

WCAG 2 evaluation uses the specified colors (computed style), not the anti-aliased pixels on a particular monitor.

## WCAG 2 contrast ratio

For sRGB components in 0-1 (`RsRGB` = R8bit/255):

- If `RsRGB <= 0.04045` then `R = RsRGB / 12.92`, else `R = ((RsRGB + 0.055) / 1.055) ^ 2.4` (same for G, B).
- Relative luminance `L = 0.2126 * R + 0.7152 * G + 0.0722 * B`.
- Contrast ratio = `(Lighter + 0.05) / (Darker + 0.05)`.

That formula is the one in WCAG 2.2 Understanding 1.4.3. Do not simplify to "subtract the hexes".

Wide-gamut specified colors should be converted into sRGB for this ratio when you are grading WCAG 2 (the success criteria's relative luminance definition is sRGB). If you cannot convert, fall back to the sRGB fallback token and measure that -- it is what older screens get.

## Tools

A browser contrast checker or a local script is fine. Record the two hex/oklch values you measured and the ratio to three significant digits (e.g. 4.52:1).

## APCA

APCA (Lc) is a perceptual lightness-contrast method aimed at future WCAG 3 work. It is directional (text vs background order matters) and font-size aware. It is useful as extra design signal. It is **not** the grade `accessibility-engineering` uses for WCAG 2. Do not report "passes APCA" as a replacement for a failed WCAG 2 ratio.

## Remediation loop

1. Note the grade the accessibility skill assigned (or "severity not covered").
2. Change OKLCH L of foreground (or background, if the surface token is allowed to move).
3. Re-measure.
4. If still failing and C is high, reduce C (in-gamut color, often higher realized contrast).
5. Stop when the ratio meets the grade, or report that the brand hue cannot meet it without a different role (use `fg` on that surface).
