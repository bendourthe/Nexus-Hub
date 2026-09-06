# Motion, Zoom, and Reflow

Read this when the surface animates, autoplays, uses parallax, or must work at large text and narrow widths.

## Reduced motion

Query: `prefers-reduced-motion: reduce`.

Under that setting:

- **Decorative** motion (background loops, hover wiggles, page-load flourishes, parallax, marquee) MUST not run. Use a static end state, or `animation: none`, or a cross-fade of 0.01s if a library requires a transition.
- **Essential** motion that communicates meaning (a progress bar advancing, a spinner that is the only busy indicator) MAY remain, but provide a non-motion text status as well (`aria-busy`, "Saving...").
- Autoplaying video and animation longer than 5 seconds MUST have a pause control (WCAG 2.2.2). Reduced-motion users get pause-by-default.

`hallmark-design` owns the optional durations and easing once motion is allowed. This skill owns the requirement to stop or simplify it. Do not copy those recipe values here.

Implementation stays in the project's styling system:

```css
@media (prefers-reduced-motion: reduce) {
  .flourish { animation: none; transition: none; }
}
```

Tailwind: `motion-reduce:animate-none` (or the project's equivalent). Do not add a new animation library to satisfy this.

WCAG 2.3.1 Three Flashes: nothing flashes more than three times per second.

## Zoom and text spacing

WCAG 1.4.4 Resize Text: content remains readable and operable at **200%** browser zoom (or equivalent text size) without requiring assistive technology. Horizontal scroll as the *only* way to read a paragraph is a fail.

WCAG 1.4.12 Text Spacing: increasing line height to 1.5 times the font size, paragraph spacing to 2 times, and letter/word spacing to the specified minima must not clip or overlap text. Avoid fixed-height containers around text that will clip when spacing grows.

Do not use `px` for `font-size` on body copy if the project's system already uses `rem`. If the project is all `px`, do not rewrite the whole type scale in this skill; flag clipping at 200% as a finding and let `web-typography` own the scale change.

## Reflow

WCAG 1.4.10 Reflow: at a width of **320 CSS pixels**, content reflows into a single column (or the project's stacked layout) so the user does not have to scroll in two dimensions to read. Exceptions: two-axis content such as maps, diagrams, data tables, toolbars that are explicitly scrollable, and video.

`layout-and-spacing` owns breakpoint structure and spatial grouping. This skill only checks that those breakpoints actually produce a 320px-wide reading experience without a second scrollbar on the viewport.

Fixed `width` on a content container (e.g. `width: 960px` on main) is a reflow failure. `max-width` plus fluid width is not.

## Pinch zoom

Do not set `user-scalable=no` or `maximum-scale=1` in the viewport meta tag. That traps users who need magnification and fails 1.4.4 in practice on mobile.

## Motion as information

If a color or animation is the only way to show "in progress" or "failed", add text or an icon. This skill's contrast handoff to `color-systems` covers the color half; the motion half is: a spinner without accessible text is a missing name (`aria-label="Loading"` on the status graphic, or visible "Loading" text).
