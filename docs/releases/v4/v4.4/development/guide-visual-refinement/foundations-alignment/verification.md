# Foundations heading and box alignment

Date: 2026-09-05

## Changes

- All six section names share Home's teal uppercase label style and leading rule. Their descriptive subtitles share Home's prominent title styling and responsive fitting.
- Token text/image boxes and context prompt/attached-material boxes stretch to equal heights when side by side. Existing breakpoints keep them at natural heights when stacked.
- Reuse the existing spacing and typography tokens; preserve all teaching content, section order, IDs, and animations.

## Verification

- 59 affected tests pass: Foundations layout, context examples, headings, animation lifecycle, and the strict file-size contract. See [test output](tests.txt).
- [Layout measurements](geometry.json) cover seven widths (320, 420, 560, 760, 761, 1024, 1440 pixels) in both themes: no page errors, horizontal overflow, or overlapping heading pairs; all side-by-side box boundaries align within one pixel.
- Inspected [desktop tokens](fx-tokens-dark-1440.png), [desktop context](fx-context-dark-1440.png), [mobile tokens in light mode](fx-tokens-light-420.png), and [mobile context](fx-context-dark-420.png).
- [Content parity](content-parity.json) confirms unchanged v4.4.5 text, all 27 sections in order, and all original IDs.
- Guide size: 399,532 normalized UTF-8 bytes, below the existing 400,000-byte gate. Full repository CI was outside this targeted visual correction.
