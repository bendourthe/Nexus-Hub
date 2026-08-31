---
title: HTML Responsive Layout
category: html
priority: high
---

# HTML Responsive Layout Rules

## Text Width

- Never apply a fixed `px` or `ch` `max-width` directly to text-bearing elements or selectors. Let the responsive container govern available width so text follows the window.
- Use `text-wrap: balance` for short headings when balanced line breaks improve readability. Do not use a fixed text cap to force a preferred line break.

## Allowed Bounds

- One primary responsive container may use a `max-width` with fluid inline sizing and responsive gutters.
- A genuinely wide table, code sample, timeline, or chart may use `overflow-x: auto` on its immediate scrolling wrapper.
- Images, video, canvas, SVG, and other media may be bounded independently when their aspect ratio or composition requires it.
- Media-query conditions such as `@media (max-width: 48rem)` are breakpoints, not text-width declarations.

## Scope

- These rules bind every HTML artifact the harness produces, including documentation, `/presentify`, `document-to-interactive-html`, reports, and repository guides.
- Do not use a fixed text cap to compensate for missing container behavior, responsive spacing, or typography.
