# Document Style Rules

These rules bind every Word, PowerPoint, HTML, and Markdown document an agent generates or edits. This file is the single owner of the rules and their default values; skills link here instead of restating them.

## Table Header Color

- When table rows carry meaning colors (category, phase, status), the header row uses a neutral color that is not used in the rows and is not close to any of them.
- Default header: dark gray `#262626` with white bold text. Pure black is too dark.
- A header may take a row color only when every row in the table belongs to that same color group.

## Alternating Row Backgrounds

- Every table alternates row backgrounds for readability. Default: `#FFFFFF` and `#F2F2F2`.
- When rows are tinted by category, alternate between the category tint and a lighter version of it (about 55 percent toward white), so the category stays visible.

## Inline Enumerations

- Do not pack a list into a sentence, such as "X passes through three phases: a (...), b (...), and c (...)".
- Write an intro line ending with a colon, then one bullet per item, for example "Phase 1: exploration and definition (stages 0 to 2)".
- Put a "Label: value" fact that follows a sentence (such as "Quality system: ...") on its own line.

## Highlighted Lead-ins

- When a lead-in is bold, colored, or shaded ("Released device (PMA):"), the formatting covers the text and the colon only.
- The space after the colon is plain text in its own run. In Markdown, write `**Label:** value`, not `**Label**: value` or `**Label: **value`.

## Concise Structure

- Prefer bullets and tables over long paragraphs.
- Remove repeated explanations.

## Enforcement

- Generator defaults: `scripts/generate_report.py` (Word) applies the header, banding, and lead-in rules in code (`apply_table_style`, `add_lead_in`, and the Markdown bold lead-in fix); the `document-to-interactive-html` dual-view builder (`scripts/dual_view.py`) applies the header and banding rules in CSS, with a `--row-tint` custom property for category rows; the python-docx, python-pptx, and PptxGenJS table samples use the same defaults.
- Edit-pass detection: the `anti-slop-editing` detector (`scripts/detect_prose_cliches.py`) flags `inline-enumeration`, `trailing-label-fact`, and `lead-in-format-boundary` as advisory findings.
- Header and banding colors in a theme or brand never override these rules silently: a brand color fills a header only under the same-color-group exception above.
