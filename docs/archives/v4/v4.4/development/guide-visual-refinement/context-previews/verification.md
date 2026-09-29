# Interactive context previews

Date: 2026-09-05

## Requested example

The worked prompt repairs a checkout screen: align Back and Place order, correct the button styling, and add Change delivery. It references checkout-layout.svg, checkout-guidelines.pdf, and assets/checkout/.

Separate Attachments and Context folder boxes sit below the prompt. The image opens an enlarged vector screenshot with three visible defects. The illustrative PDF preview shows a made-up guideline cover and a five-item implementation checklist. The folder opens an explorer with expandable brand, icons, and illustrations directories. These are embedded teaching previews, not external files or uploads.

## Design and interaction

Reuse the guide's dark/light tokens, typefaces, border treatment, and spacing. Keep native buttons, a native modal dialog, native folder disclosures, and a single shared SVG screenshot. No new libraries or network calls are introduced. Opening moves focus to Close; Escape and Close restore it to the clicked item. Page-navigation shortcuts do not fire inside a preview. The enlarged image supports keyboard scrolling on narrow screens.

## Verification

- Focused suite: 128 passed, one skipped. See [test output](focused-tests.txt).
- [Browser checks](checks.json): six widths (320, 420, 760, 761, 1024, 1440 pixels), both themes, and 36 preview openings; no page errors or horizontal page overflow, with Escape and focus return verified.
- [Image keyboard check](keyboard-image.json): Tab reaches the scrollable image and ArrowRight pans it. [PDF scroll check](pdf-scroll.json): the final checklist paragraph is reachable and Close remains visible.
- [CSS comparison](css-compaction.json): stylesheet whitespace compaction preserves every unrelated CSS rule. Quoted values and comments remain intact; context-specific rules intentionally change.
- [Content comparison](content-check.json): content outside the context example and its new previews, section order, and original IDs remain unchanged.
- Guide size: 399,465 normalized UTF-8 bytes, below the existing 400,000-byte gate.
- [Full guide suite](guide-suite-before-retests.txt): 339 passed, five failed, one skipped. Four failures were resolved by retaining spacing required by literal CSS tests and updating stale expectations from the previously requested Next-section removal and session dialogue. [Final retests](retests.txt): 32 passed.
- One inherited failure remains: [Agentic Platforms has two pixels of internal overflow at 320 pixels](baseline-overflow.json), reproduced on both the prior revision and the final guide. The full suite was not rerun after the four fixes; those checks were covered by the final retests.

## Visual evidence

- [Desktop composer](composer-dark-1440.png) and [mobile light composer](composer-light-420.png).
- [Enlarged screenshot](image-1440.png).
- [Guideline cover and checklist](pdf-1440.png), with [mobile preview](pdf-420.png).
- [Asset explorer](folder-1440.png), with [mobile explorer](folder-420.png).
