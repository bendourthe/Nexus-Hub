# Focus and Keyboard

Read this when the surface has buttons, links, custom widgets, dialogs, menus, or skip links.

## Tab sequence

Tab and Shift+Tab move among interactive elements in **DOM order**. If visual order and DOM order disagree, a keyboard user hits controls in a sequence that does not match the screen. Fix the DOM (or CSS `order` that scrambled it), not with `tabindex="2"`.

Rules:

- No `tabindex` greater than `0`. Positive values create a second, author-defined sequence that fights the natural one and is a WCAG 2.4.3 failure in practice.
- `tabindex="0"` adds a non-interactive element to the sequence. Use it only when the element must be reachable by Tab and is not natively focusable (`<div>` that is a gridcell, a custom listbox). Prefer a native control.
- `tabindex="-1"` takes an element out of the sequence but allows `element.focus()`. Use it for the first heading inside a dialog, a skip-link target, and the invoker restoration target.

Skip link: the first focusable node in the document is a link whose target is the main content (`#main`). It may be visually hidden until focused. The target has `tabindex="-1"` so it can receive focus.

## Keys per control type

| Control | Activation | Movement |
|---|---|---|
| Button, link | Enter and Space (link: Enter is enough; Space must not scroll if the link is a button-styled control) | Tab |
| Checkbox / switch | Space toggles | Tab |
| Radio group | Space selects the focused radio; Arrow keys move within the group | Tab lands on the selected radio only |
| Native `<select>` | UA handles it | Do not replace without matching this |
| Tabs (composite) | Arrow keys move among tabs; Tab leaves the tab list into the selected panel | `tabindex="0"` on the active tab, `-1` on the others |
| Menu | Arrow keys; Enter/Space activates; Escape closes | Tab should not walk every item if Arrow navigation is implemented; pick one model and stick to it |
| Dialog | Tab cycles inside; Escape closes | See trap below |

A `div` with `onClick` and no keyboard handler is not a button. Use `<button type="button">`.

## Visible focus

WCAG 2.4.7 (Focus Visible) and 2.4.13 (Focus Appearance, AAA) both require that the focused control can be found by looking at the screen.

Minimum this skill enforces:

- The focused control has a visible indicator that is not color-alone (a ring or offset outline).
- `outline: none` / `outline: 0` / `outline: transparent` is forbidden unless a replacement indicator of at least 2px thickness is applied on `:focus-visible`.
- The indicator is not clipped by `overflow: hidden` on an ancestor, and is not covered by a sticky header (WCAG 2.4.11 Focus Not Obscured (Minimum): at least part of the focused item remains visible).

`:focus-visible` is the right hook: it shows the ring for keyboard focus and not for every mouse click, which is why teams used to strip outlines.

Match the project's tokens. If the design system has `--focus-ring`, use it. If not, a 2px solid ring with `outline-offset: 2px` using an existing contrast-safe accent is enough. Do not invent a new color here; if the ring fails contrast, grade it (blocker) and hand measurement to `color-systems`.

## Focus order vs visual order

`layout-and-spacing` owns whether the *layout* reads left-to-right or in another spatial sequence. This skill owns whether **Tab** follows that reading. If CSS Grid or Flex `order` rearranged items, either restore source order or reorder the DOM to match the visual sequence.

## Overlay focus trap

When a modal dialog (or equivalent: full-screen drawer, onboarding modal) is open:

1. Focus moves to the dialog container or its first heading/control on open.
2. Tab from the last focusable node wraps to the first; Shift+Tab from the first wraps to the last.
3. Escape closes the dialog.
4. On close, focus returns to the element that opened it. If that node is gone, focus a sensible fallback (the landmark that contained it), not `document.body`.
5. Content outside the dialog is not reachable: `inert` on the background is the modern approach; `aria-modal="true"` plus `role="dialog"` plus a labelled name (`aria-labelledby` to the title) are required on the dialog itself.

Non-modal popovers (date picker anchored to a field) MUST NOT trap. Tab should leave them. Escape still closes them.

A loading overlay that intercepts clicks but is not in the tab order is a keyboard trap of a different kind: the user can Tab "through" it into controls they cannot activate. While the overlay is up, either make it a dialog with an announced status, or disable underlying controls with `disabled` / `inert`.

## Roving tabindex (composite widgets)

For tabs, menus, toolbars, and grids, only one member is in the tab sequence (`tabindex="0"`). Arrow keys move the roving tab. This keeps Tab presses on the page in the order of *widgets*, not every inner button. Implement it only for true composite widgets; a row of independent buttons should each be in the tab sequence.
