# Decision: Document Style Rules for Generated Documents

Status: implemented - one owning rule file, code defaults in the Word generator and the dual-view HTML builder, and three advisory detector patterns.

Maintainers use this record when a generated Word, PowerPoint, HTML, or Markdown document is flagged for its table colors, row banding, lead-in formatting, or packed enumerations, or when a skill wants to restate those rules. It covers where the rules live, which generators enforce them in code, and how the edit pass detects them.

**Date**: 2026-11-10. **Source**: the maintainer's request to add five document style rules (neutral table header, alternating rows, enumerations as bullets, lead-in formatting ending at the colon, concise structure) for every agent that generates or edits documents.

## Problem

Generated documents used a theme or brand color for table headers. When rows were tinted by category, the header could match or sit close to a row color, so it read as one more category. Banding used a blue-gray stripe that clashed with category tints. The Word generator bolded the space after a lead-in colon in nine places. Agents also packed lists into sentences after a colon. No single file stated these rules, so each document skill would have had to restate them.

## Decision

- `catalog/rules/documents/document-style.md` owns the five rules and their default values (`#262626` header with white bold text, `#FFFFFF`/`#F2F2F2` rows, category tint alternating with the tint 55 percent toward white). The installer copies `catalog/rules/` by folder, so the file reaches every platform that receives rules with no installer edit.
- `scripts/generate_report.py` enforces rules 1, 2, and 4 in code: `apply_table_style` picks a header no row tint uses or comes close to (RGB distance below 80 counts as close) and bands rows; `add_lead_in` emits a formatted `Label:` run and a plain space; Markdown `**Label**:` and `**Label: **` are normalized to `**Label:**`.
- `document-to-interactive-html/scripts/dual_view.py` carries the same header and banding defaults in its CSS, with a `--row-tint` custom property for category rows. The python-docx, python-pptx, and PptxGenJS table samples use the same defaults.
- The `anti-slop-editing` detector flags `inline-enumeration`, `trailing-label-fact`, and `lead-in-format-boundary` as advisory. The docx, pptx, html-output-conventions, writing-editing, anti-slop-editing, theme-tokens, and brand-styling skills link to the rule instead of copying it.

## Alternatives considered

- **Copy the rules into each document skill.** Rejected: seven copies drift on the first edit, and a review cannot tell which copy is current. One owner plus links matches the rule-ownership convention in `AGENTS.md`.
- **Put the rules in `catalog/style-guides/`.** Rejected: style guides are reference files an agent opens on demand, while `catalog/rules/` files load into agent context on the platforms that read rules, which is what "every agent applies them" needs.
- **Make the new detector patterns defects.** Rejected: `**Field**: value` metadata appears throughout existing plans and docs, so a defect class would fire hundreds of times on legitimate history and nobody would gate on it. Advisory informs the edit pass without blocking it.
- **Apply the HTML defaults in `assets/presentation-template.html`.** Deferred, not rejected: the `html-responsive-guard` hook blocks any edit to that template while its three existing `max-width: var(--measure)` text caps remain, and removing those caps changes the presentify layout, which is outside this change.

## Consequences

- Word reports from `generate_report.py` now render a dark-gray table header instead of blue, and every bold lead-in ends at its colon.
- The overview and distribution handbooks embed the dual-view CSS, so they were rebuilt and re-reviewed; any later change to that CSS invalidates their receipts the same way.
- The detector's advisory output now lists `lead-in-format-boundary` for existing `**Field**: value` metadata. No gate changes.
- HTML banding alternates by row position, while the Word generator restarts the alternation at each category; both satisfy the rule.
- `assets/presentation-template.html` and the other HTML reference templates keep their previous table styling until their text caps are fixed in a separate change.
