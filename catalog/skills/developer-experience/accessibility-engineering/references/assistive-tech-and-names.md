# Assistive Technology and Accessible Names

Read this when building icon-only controls, custom widgets, images, live updates, or anything that currently "looks labelled" but may not be named for AT.

## Accessible name computation (what AT actually reads)

For a given element the name is the first non-empty of:

1. `aria-labelledby` (IDs of other elements; concatenated in listed order)
2. `aria-label`
3. Native labelling: `<label>` for inputs, descendant text for buttons and links, `alt` for `<img>`, `<title>` for `<svg>` only as a last resort
4. `title` attribute (poorly supported as a name; do not rely on it)

If all of those are empty, the control has **no name**. An icon font glyph, a background-image, or an SVG without `<title>`/`aria-label` produces silence or "button".

Never put a name in both `aria-label` and visible text unless they are identical. Divergent names are a WCAG 2.5.3 Label in Name failure (voice-control users say the visible text and it does not match).

## When to use ARIA

ARIA adds a name or a role the host language does not provide. It does not add keyboard behavior, focus, or disabled semantics unless you also implement them.

Use ARIA when:

- A group of native controls needs a group name (`role="group"` + `aria-labelledby`)
- A live update needs `aria-live` / `role="status"` / `role="alert"`
- A custom widget has no HTML equivalent (grid, tree) -- last resort

Do not use ARIA when:

- `<button>`, `<a href>`, `<nav>`, `<main>`, `<header>`, `<footer>`, `<ul>` already express the role
- You are tempted to put `role="button"` on a `<div>` instead of using `<button>`
- You are duplicating a visible `<label>` with `aria-label`

`aria-hidden="true"` removes the subtree from the accessibility tree. Never hide a focusable element: a user can Tab to something AT cannot name. Hide decorative SVGs and duplicated text, not the actual control.

## Images, icons, and SVG

| Case | Markup |
|---|---|
| Informative image (photo, chart, diagram) | `<img alt="...">` describing the content, not "image of" |
| Decorative image | `<img alt="">` or CSS background |
| Adjacent text already describes it | `alt=""` so AT does not hear the same sentence twice |
| SVG icon inside a named button | `aria-hidden="true"` on the SVG; the button's text or `aria-label` is the name |
| Standalone informative SVG | `role="img"` + `aria-labelledby` pointing at a `<title>` inside the SVG |

Icon-only button: the accessible name is a verb phrase that matches the action ("Save", "Delete comment", "Open settings"), not the icon's shape ("gear", "trash can glyph").

## Live regions

- `role="status"` / `aria-live="polite"`: non-urgent updates (save succeeded, 3 results). AT finishes the current utterance first.
- `role="alert"` / `aria-live="assertive"`: urgent errors. Use sparingly; assertive interrupts.
- The region must exist in the DOM **before** the text is injected. Creating the node and the text in the same paint is often silent.
- Do not mark a whole page as live.

## Page structure for AT

Landmarks: one `<main>`, one `<header>` (banner), `<nav>` labelled when there are several (`aria-label="Footer"`). Screen-reader users jump by landmark; three unlabelled `<nav>` elements are indistinguishable.

`lang` on `<html>` matches the page language. A phrase in another language gets `lang` on the element.

Dynamic view changes in an SPA: when the primary heading of the new view is rendered, focus it (`tabindex="-1"` on the `h1`) so AT and keyboard users are not left on a leftover control from the previous route.

## Custom widgets and roles

If you set `role="combobox"`, `role="listbox"`, `role="dialog"`, or `role="tablist"`, you own the full pattern: states (`aria-expanded`, `aria-selected`, `aria-checked`), properties (`aria-controls`, `aria-haspopup`), and the keyboard map in `references/focus-and-keyboard.md`. A role without the matching states is a lie in the accessibility tree and is worse than no role.

Prefer native elements until a real gap exists. The cost of a correct combobox is higher than styling a native `<select>`.
