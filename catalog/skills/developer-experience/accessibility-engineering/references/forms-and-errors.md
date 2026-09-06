# Forms and Error Association

Read this when the surface collects input, validates, or shows field-level or form-level errors.

## Labelling

Every control that takes input has a persistent accessible name from a visible label.

Accepted patterns:

- `<label for="email">Email</label><input id="email">` (preferred; click-to-focus works)
- `<label>Email <input></label>` (wrapping; still a real `<label>`)
- Visible heading or legend text referenced with `aria-labelledby` when the design cannot use `<label>` (segmented controls, search fields with a visible heading)

Rejected patterns:

- Placeholder as the only label. Placeholder is a hint, disappears, and is often ignored by AT.
- A `<span>` next to the input with no programmatic association.
- `aria-label` that duplicates a visible label and then drifts out of date. If the visible text exists, point at it with `for` or `aria-labelledby`.

Group related radios and checkboxes in `<fieldset>` with a `<legend>`. The legend is the group name; each radio still has its own label.

## Required and optional

- Use the native `required` attribute on fields that block submit.
- Visible text: "required" in the label, or a documented convention ("all fields required unless marked optional") stated once at the top of the form.
- Do not use color-only markers (a red asterisk with no text and no `required`).
- Optional fields are unmarked, or marked "optional" in the label. Mixing "required" stars on some fields and silence on others is fine if the star has text.

## Instructions and formatting hints

Put format hints in visible text bound with `aria-describedby`, not only in placeholder.

```html
<label for="phone">Phone</label>
<input id="phone" aria-describedby="phone-hint" autocomplete="tel">
<p id="phone-hint">Include country code, for example +1 415 555 0100.</p>
```

`autocomplete` values (`email`, `name`, `tel`, `current-password`, `one-time-code`, `street-address`) MUST match the field's purpose. Wrong autocomplete is a WCAG 1.3.5 miss and a password-manager miss.

## Errors: associate, don't just paint red

On a failed submit:

1. Set `aria-invalid="true"` on each invalid control.
2. Render an error message with a stable `id`.
3. Add that id to the control's `aria-describedby` (append; do not drop the hint id).
4. Move focus to the first invalid field. Do not only scroll.
5. Announce a summary if there are several errors: an `aria-live="assertive"` (or `role="alert"`) region that says how many fields failed, placed at the top of the form.

The error text says what is wrong and how to fix it. "Invalid" is not enough. "Enter an email that includes @" is enough.

Inline validation on blur is allowed. Do not announce every keystroke (`aria-live` on each character). Live regions fire on the completed invalid/valid transition, not on input events.

## Disabled, readonly, and submit

- `disabled` fields are skipped in the tab sequence and often omitted by AT. If the user must read the value, use `readonly` instead of `disabled`.
- The submit button stays enabled unless the product has a documented reason; disabling submit until the form is "perfect" traps keyboard users who cannot reach the error summary.
- After a successful submit, move focus to a confirmation heading or status (`role="status"`) so AT users know the action completed.

## Custom widgets that replace native inputs

If you replace `<select>`, `<input type="date">`, or a file input with a custom widget, you inherit the entire keyboard contract of the native control plus an accessible name and a value that AT can read (`aria-valuetext`, selected option text, or a visually hidden native input kept in sync). Prefer the native control. A custom combobox that does not implement the expected Arrow/Enter/Escape behavior is a blocker, not a visual nit.
