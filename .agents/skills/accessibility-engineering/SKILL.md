---
name: accessibility-engineering
description: "Ship accessible UI: names, keyboard, focus, forms, hit areas, motion, zoom. Use for accessibility, a11y, keyboard navigation, screen reader, ARIA, focus, or WCAG. SKIP: general frontend (frontend-ui-engineering) and visual polish (hallmark-design)."
summary_l0: "Ship and audit accessible UI against keyboard, name, and WCAG rules"
overview_l1: "This skill owns accessible interaction: semantic structure and accessible names, keyboard operability and visible focus, focus order and overlay trapping, form labelling and error association, assistive-technology behavior, minimum hit areas, and reduced-motion plus zoom/reflow. It decides when contrast is required and how severe a failure is; color-systems measures and remediates the rendered pair. It owns heading semantics; web-typography owns how those headings look. Match the project's existing styling system. SKIP general frontend architecture and visual polish."
---

# Accessibility Engineering

Ship UI that a keyboard user, a screen-reader user, and a pointer user can all operate, and audit existing UI against the same bar. This skill is value-level: name the attribute, the key, the size, or the criterion. Principle-only advice ("be accessible") is a miss.

Match the project's existing styling system (Tailwind, plain CSS, CSS Modules, CSS-in-JS). Do not introduce a new utility vocabulary to satisfy these rules.

## When to Use This Skill

Use when:

- The user mentions accessibility, a11y, WCAG, ARIA, screen readers, keyboard navigation, focus states, skip links, or hit areas.
- A new control, form, dialog, menu, or page is being implemented and must be operable without a mouse.
- An audit or review is asked to check whether the UI is accessible.

**When NOT to use:**

- Component architecture, routing, and state management belong to `frontend-ui-engineering`. Hand off; do not restate those rules.
- Visual polish (elevation, radius, icon stroke, optional motion recipes) belongs to `hallmark-design`.
- Measuring a rendered color pair and changing the colors belongs to `color-systems`. This skill decides whether contrast is required and how severe a miss is.
- Visual heading size, measure, and truncation belong to `web-typography`. This skill owns the heading *outline* (levels, one `h1`, no skipped ranks).

## Quick Reference

| Topic | Read when | File |
|---|---|---|
| Keyboard, focus ring, order, overlay traps | Any interactive control or dialog | `references/focus-and-keyboard.md` |
| Labels, errors, required fields, live regions | Any form or validation | `references/forms-and-errors.md` |
| Accessible names, roles, screen-reader text | Icon-only controls, custom widgets, images | `references/assistive-tech-and-names.md` |
| Pointer target size and spacing | Toolbars, icon buttons, dense tables | `references/hit-areas.md` |
| Reduced motion, 200% zoom, 320px reflow | Animation, small viewports, text resize | `references/motion-zoom-reflow.md` |

## Instructions

### 1. Identify the surface and the project's styling system

Name the files under review. Note whether styles are Tailwind classes, global CSS, modules, or CSS-in-JS. All later edits stay inside that system.

### 2. Fix semantics and accessible names first

A control the browser already understands needs no ARIA. Prefer native `<button>`, `<a href>`, `<label>`, `<input>`, headings, and lists.

Every operable control MUST have an accessible name. Computation order (first non-empty wins): `aria-labelledby` -> `aria-label` -> associated `<label>` / native text / `alt`. An icon-only button with no name is a failure even if the glyph is obvious to a sighted user.

Heading outline: exactly one `h1` per page (or per distinct view in an SPA), then `h2`...`h6` with no skipped rank. A styled `<div>` or `<p>` is not a heading. Visual size of that heading is `web-typography`'s rule; do not restate it here.

Images: informative images have `alt` that names the content; decorative images have `alt=""`. Do not put the same sentence in both visible text and `alt`.

### 3. Make it work from the keyboard

Every action that a pointer can take MUST be reachable and operable with Tab, Shift+Tab, Enter, Space, and (for composite widgets) Arrow keys. See `references/focus-and-keyboard.md`.

Visible focus is mandatory. Never `outline: none` (or `outline: 0`) without a replacement that is at least as visible as the UA ring. A 2px solid offset ring that uses a token already in the palette is the default replacement.

Focus order follows DOM order. Do not use `tabindex` greater than `0`. `tabindex="0"` is for an element that must be in the tab sequence but is not natively focusable. `tabindex="-1"` is for programmatic focus only (dialogs, skip targets).

Modals, drawers, and menus that take over the page MUST trap focus inside while open, restore focus to the invoker on close, and close on Escape. Background content is `inert` or `aria-hidden="true"` (never both on the same node in a way that hides the dialog from AT).

### 4. Label forms and associate errors

Every input has a visible `<label>` bound with `for`/`id` or wrapping the control. Placeholder is not a label.

Required fields use the native `required` attribute plus visible text ("required"), not color alone.

Errors: put the message next to the field, point `aria-describedby` at it, set `aria-invalid="true"` on the control, and move focus to the first invalid field on submit. See `references/forms-and-errors.md`.

### 5. Size hit areas; respect motion and zoom

Hit area: at least 24 by 24 CSS pixels (WCAG 2.2 Success Criterion 2.5.8 Target Size (Minimum)). Spacing between adjacent undersized targets can compensate only when the gap keeps the 24px square exclusive. Prefer 44 by 44 CSS pixels for primary actions. See `references/hit-areas.md`.

Honor `prefers-reduced-motion: reduce`: essential motion (a loading spinner that conveys progress) may remain; decorative motion MUST stop or become a static state. `hallmark-design` owns optional animation recipes *after* this requirement is met.

Text can resize to 200% without loss of content or function. Layout reflows at 320 CSS pixels width without two-axis scrolling except for content that requires two axes (maps, data tables, canvases). See `references/motion-zoom-reflow.md`.

### 6. Contrast: decide, then hand off measurement

Contrast is required on text, UI component boundaries that identify the control, and focus indicators.

Severity:

- Body text and interactive text below 4.5:1 (or large text below 3:1) is a **blocker**.
- Non-text UI (1.4.11) below 3:1 is a **blocker**.
- Placeholder-only contrast on an otherwise labelled field is **advisory** if the label itself meets 4.5:1.

Do not compute ratios in this skill. Load `color-systems` to measure the rendered pair and change the colors. If `color-systems` is unavailable, mark contrast measurement as not covered, name the missing skill, and continue with the rest of this checklist. Do not invent a formula from memory.

### 7. Report

For an implementation request: make the edits, then fill the Verification checklist.

For an audit: list each failure with `path:line`, the current markup, the required attribute or behavior, and the severity (blocker / major / advisory). One root cause, one finding, every location listed. Include a Considered-but-Rejected table of real candidates you inspected and chose not to report.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The icon is obvious; it does not need a name." | A screen reader announces an empty button. Sighted recognition is not an accessible name. Failure: unlabeled icon control. |
| "We hide the outline because it looks ugly." | Keyboard users cannot tell where they are. `outline: none` without a visible replacement fails 2.4.7. |
| "Focus trap is overkill for a small popover." | Tab escaping into the page behind the overlay lets the user edit content they cannot see. That is a dialog failure, not a polish miss. |
| "Placeholder text is the label." | Placeholder disappears on input and is often skipped by AT. The control then has no persistent name. |
| "Contrast looks fine on my monitor." | Looking is not measuring. This skill grades severity; `color-systems` measures. Shipping on gut feel ships 3.2:1 body text as if it were 4.5:1. |
| "ARIA roles make a div into a button." | A `div role="button"` still needs tabindex, Enter/Space handlers, and a name. Native `<button>` already has all three. Fake buttons miss one of them. |
| "Reduced motion is a nice-to-have." | Vestibular users can be made ill by parallax and autoplaying motion. Decorative animation that ignores `prefers-reduced-motion` is a 2.3.3 miss. |
| "This is a frontend task, so frontend-ui-engineering covers it." | That skill owns architecture and a short a11y checklist. Named attributes, trap behavior, and hit-area sizes live here. Using the generalist skill is how these values get dropped. |

## Verification

- [ ] Every operable control has a non-empty accessible name (inspect computed name, not the visible glyph).
- [ ] The page or view has exactly one `h1` and heading ranks do not skip.
- [ ] Tab order matches visual order; no `tabindex` > 0.
- [ ] A visible focus indicator is present on every focusable control (no bare `outline: none`).
- [ ] Modal overlays trap focus, restore it on close, and close on Escape.
- [ ] Every input has a `<label>` (or `aria-labelledby` pointing at visible text); placeholder is not the only name.
- [ ] Invalid fields expose `aria-invalid="true"` and `aria-describedby` pointing at the error text.
- [ ] Interactive targets are at least 24x24 CSS pixels, or are spaced so the 24px square does not overlap a neighbor.
- [ ] Decorative motion is disabled or static under `prefers-reduced-motion: reduce`.
- [ ] Layout remains usable at 200% text zoom and at 320px width without unexpected two-axis scroll.
- [ ] Contrast failures are graded here and either measured by `color-systems` or explicitly marked not covered if that skill is unavailable.
- [ ] Styles were written in the project's existing styling system.

## Related Skills

- `frontend-ui-engineering` -- component architecture, state, and responsive implementation; hand off those concerns, do not duplicate them
- `color-systems` -- measures and remediates the rendered contrast pair after this skill decides a miss is in scope
- `web-typography` -- visual heading size, measure, wrapping; this skill owns heading semantics only
- `layout-and-spacing` -- visual grouping and spatial order; this skill owns focus order and DOM semantics
- `interface-copy` -- source wording of labels and errors; this skill owns how those strings are exposed to AT
- `hallmark-design` -- optional motion recipes after reduced-motion requirements are met
- `interface-review` -- coordinating review that loads this skill as a delegate
