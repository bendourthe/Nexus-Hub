# Gamut and Fallbacks

## Out of gamut is normal at high chroma

OKLCH can name colors a typical sRGB panel cannot show. CSS Color 4 gamut mapping (what browsers do) keeps lightness and hue and reduces chroma until the color fits the output device. The displayed color may look duller than the source you wrote. That is expected, not a bug in the monitor.

If two steps in a ramp look the same, you are probably past the gamut boundary. Lower C for those steps until they separate again.

## Display P3

`color(display-p3 ...)` or a high-C `oklch()` may use a wider gamut on capable screens. Always pair with an sRGB-reachable color the cascade can use when P3 is absent:

```css
.button {
  background: #0052cc; /* sRGB fallback */
  background: oklch(0.45 0.16 260);
}
```

Or `@supports (color: oklch(0.5 0.1 0))`.

Do not ship P3-only tokens in a product that still lists Safari versions or embedded WebViews without checking support tables for that product.

## `color-mix` space

`color-mix(in oklch, var(--accent), white)` and `in oklab` are the interpolation spaces that avoid gray mud in the middle. `in srgb` is the escape when you must match a legacy gradient exactly.

## Print and forced colors

`forced-colors: active` (Windows High Contrast and similar) can replace your palette. Do not fight it with `!important` on every token. Ensure semantic HTML so system colors still map (that mapping is mostly `accessibility-engineering` plus UA). This skill's job is: do not assume your OKLCH tokens still exist in that mode.
