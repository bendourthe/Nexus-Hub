# Hit Areas and Pointer Targets

Read this when the surface has icon buttons, table-row actions, chips, pagination, or any dense toolbar.

## The number this skill requires

WCAG 2.2 Success Criterion 2.5.8 Target Size (Minimum) is **24 by 24 CSS pixels** for the target, with listed exceptions (inline in text, user-agent control, essential layout, and a 24px-square exclusive space around a smaller visual).

This skill's default for **primary and standalone actions** is **44 by 44 CSS pixels** (the WCAG 2.5.5 AAA size, and the common mobile platform guideline). Dense toolbars may drop to 24px if 44px will not fit, but not below 24px without an exception.

The target is the **hit area**, not the visible glyph. A 16px icon can sit inside a 44px button. Padding is the usual way to get there.

## Spacing as compensation

If two visual targets are smaller than 24px, they still pass 2.5.8 when each has an exclusive 24px square that does not intersect the other's. That means gap between hit boxes, not just margin on the icon graphic.

Do not overlap hit areas. A table-row "delete" icon whose clickable box covers the "edit" icon next to it is a fail even if both glyphs look 16px.

## Exceptions this skill accepts

- Links and buttons **in running text** inherit the line's hit area; do not force 24px on every inline link.
- The **page scrollbar** and other UA controls.
- A target whose size is **essential** to the information (a point on a map). Then provide an alternative (a list of the same points).
- Disabled controls are not required to meet the size (they are not targets).

## Pointer and motor extras

WCAG 2.5.2 Pointer Cancellation: activation happens on **up** (click/pointerup), and the user can abort by dragging off. Do not fire the destructive action on `pointerdown` / `mousedown`.

WCAG 2.5.1 Pointer Gestures: a path-based gesture (swipe to delete, pinch only) MUST have a single-pointer alternative (a Delete button).

WCAG 2.5.7 Dragging Movements (2.2): anything that can only be done by dragging needs a single-pointer alternative (buttons, numeric inputs).

Label the hit area in CSS using the project's system: Tailwind `min-h-11 min-w-11` (2.75rem = 44px at default root), or `padding` on the button, or an extra wrapping `<button>` rather than stretching a `<span>` with a click handler.

## Touch vs mouse

Do not ship a 24px target on a touch-first screen and a 16px target on "desktop" without checking the desktop user who tabs and clicks the same control. One size that meets 24px everywhere is simpler than two breakpoints that drift.

If a tooltip or overflow menu is the only way to reach an action, the **opener** still needs a 24px target. Hidden actions that appear only on row hover fail keyboard users and fail small-target users unless a focus-visible equivalent exists.
