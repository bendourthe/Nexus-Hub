# Motion Recipes

`accessibility-engineering` owns the reduced-motion **requirement**: decorative motion MUST stop or become static under `prefers-reduced-motion: reduce`. This file is the optional recipe used only after that requirement is met and a transition is actually warranted (gate 25: purposeful, not entrance-on-everything).

## Durations

| Change | Duration |
|---|---|
| Color, opacity, focus ring | 150ms |
| Control press (`translate` / `scale`) | 200ms |
| Overlay / menu enter | 280ms to 320ms |
| Overlay exit | 180ms to 220ms (faster than enter) |

Never `0ms` on a state the user must notice (it looks like a snap bug). Never 700ms+ on chrome; that is a loading wait, not a micro-interaction.

## Easing

- Enter / land: `cubic-bezier(0.2, 0, 0, 1)` (decelerate).
- Exit / leave: `cubic-bezier(0.4, 0, 1, 1)` (accelerate).
- Indeterminate progress only: `linear`.

`ease` and `ease-in-out` on every property is the default look this recipe is replacing.

## Transforms that read as deliberate

Allowed:

- Press: `translateY(1px)` on text buttons, `scale(0.98)` on icon-only buttons.
- Overlay enter: `translateY(8px)` plus opacity 0 to 1, or `scale(0.98)` plus opacity, not both plus rotate.
- Focus: do not animate the ring's presence with a bounce; a 150ms color/opacity change is enough. The ring itself is `accessibility-engineering`.

Not allowed as default decoration:

- Rotate, skew, or `translateY(-20px)` on every card as it scrolls into view.
- Bounce / spring overshoot on dialogs.
- Staggered delays that make a list "rain in" (`animation-delay: calc(i * 80ms)` on each row).

## Reduced-motion branch

```css
@media (prefers-reduced-motion: reduce) {
  .optional-motion {
    animation: none;
    transition: none;
  }
}
```

Instant open/closed state remains. Do not keep a 300ms fade and call it accessible. If the motion conveys meaning (a spinner for in-progress), `accessibility-engineering` already allowed that exception; do not add extra transforms on top.
