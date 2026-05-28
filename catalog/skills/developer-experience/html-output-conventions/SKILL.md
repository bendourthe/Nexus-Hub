---
name: html-output-conventions
description: Decide when a human-facing artifact should be HTML rather than Markdown, and produce it from four self-contained reference templates (grid comparison, annotated diff, interactive tuning, tabbed document)
summary_l0: "Prefer HTML over Markdown for human-facing artifacts that are read, compared, or interacted with, using four self-contained templates"
overview_l1: "This skill codifies when the agent should emit an HTML artifact instead of Markdown, and how. HTML wins when an artifact needs tables, SVG, interactive controls, or spatial data, when it runs past roughly 100 lines and becomes hard to scan as Markdown, when it should be shared as a link, or when it should round-trip state back to the agent (copy-as-JSON). Markdown stays the right choice for short notes, README front matter, and commit messages. The skill ships four self-contained reference templates the agent can adapt: a grid comparison layout for N-way comparisons, an annotated diff display with color-coded severity margins for code review, an interactive tuning interface with copy-as-JSON controls, and a tabbed organization layout for long documents. It composes with hallmark-design (which governs whether the chosen HTML actually looks designed rather than AI-generated). Use it on Coding-pillar review surfaces, the session replay timeline, and the operator-actions dashboard. Anti-patterns: ASCII diagrams (use SVG) and defaulting to Markdown when an HTML artifact would actually be read."
version: 1.0.0
author: Benjamin Dourthe
license: MIT
attribution: "Actionable conventions distilled from the public Claude Code 'unreasonable effectiveness of HTML' article; templates are original, self-contained implementations."
category: developer-experience
language: HTML
tags: [html, markdown, artifacts, code-review, accessibility, svg, templates, frontend]
tools_required: [Read, Write, Edit]
---

# HTML Output Conventions

Prefer HTML over Markdown for human-facing artifacts that will actually be read, compared, or interacted with. Markdown is the right default for short prose; it stops being the right default the moment an artifact needs a table, an SVG, an interactive control, spatial data, or simply runs long enough that a reader cannot scan it. This skill gives the agent a decision rule and four runnable templates so the choice is deliberate, not habitual.

This skill composes with `hallmark-design`: this skill decides *whether* a surface should be HTML; `hallmark-design` ensures the HTML actually looks designed rather than AI-generated. Run both on any human-facing surface.

## When to Use This Skill

Use this skill whenever the agent is about to produce a human-facing artifact and could choose HTML or Markdown: review outputs, specs, comparisons, incident reports, design prototypes, dashboards, and the session replay timeline.

## HTML vs Markdown decision table

| Artifact | Choose | Why |
|---|---|---|
| Spec or proposal with an N-way comparison (e.g. 6 candidate designs) | **HTML** | Grids and side-by-side layout beat a flat Markdown list; the reader scans columns. See `grid-comparison.html`. |
| Code-review output with per-change severity | **HTML** | Color-coded severity margins plus inline notes are not expressible in Markdown. See `annotated-diff.html`. |
| Design prototype with adjustable parameters | **HTML** | Interactive controls (sliders, checkboxes) and a copy-as-JSON round-trip require real HTML. See `interactive-tuning.html`. |
| Incident report or long multi-section document (> ~100 lines) | **HTML** | Past ~100 lines Markdown is hard to scan; tabs or anchored sections restore navigation. See `tabbed-document.html`. |
| Anything that should be shared as a link rather than pasted inline | **HTML** | A self-contained HTML file opens as a page; a long Markdown block is an attachment the reader must scroll. |
| Short note, status update, or answer under ~100 lines of prose | **Markdown** | No tables/controls needed; Markdown is faster to read and edit. |
| README front matter, inline code comments | **Markdown** | These surfaces are Markdown by convention; HTML would be noise. |
| Commit messages | **Markdown / plain text** | Git renders plain text; HTML is wrong here. |

Rule of thumb: if the artifact will be *read* (scanned, compared, navigated, or interacted with) rather than just *skimmed once*, and it has structure Markdown cannot carry, emit HTML.

## Reference templates

All four templates are self-contained (no external CSS/JS, no CDN) so they are runnable inline and shareable as a single file. Adapt the content; keep the structure and accessibility affordances.

1. **Grid comparison layout** -- `references/grid-comparison.html`. Responsive grid for comparing several options/designs/approaches with a shared attribute set. Use for "here are N candidates".
2. **Annotated diff display** -- `references/annotated-diff.html`. Code diff with color-coded severity margins (high/medium/low) and inline review notes. Severity is conveyed by both color and a text label, never color alone.
3. **Interactive tuning interface** -- `references/interactive-tuning.html`. Sliders and checkboxes inside a `<form data-nexus-artifact="true">` with a "Copy as JSON" button that serializes form state to the clipboard, so the reader can round-trip state back to the agent. The Nexus desktop shell's interactive-artifact wrapper consumes the same `data-nexus-artifact` marker.
4. **Tabbed document** -- `references/tabbed-document.html`. Accessible tabbed layout (ARIA roles, roving tabindex, arrow-key navigation) for long documents such as incident reports and multi-section specs.

## Anti-patterns

- **No ASCII diagrams.** When a diagram is needed, use inline SVG, not box-drawing characters. ASCII diagrams break on reflow, are inaccessible to screen readers, and read as a teletype artifact.
- **No defaulting to Markdown when an HTML artifact would actually be read.** If the content matches an HTML row in the decision table above, do not fall back to Markdown out of habit.
- **No color-only meaning.** Severity, status, and category must carry a text label or shape in addition to color (see the diff template).
- **No external dependencies in a shared artifact.** Keep templates self-contained so the file opens anywhere and persists cleanly.

## Where these artifacts persist (privacy)

HTML artifacts that are saved (a review report, an exported timeline, a persisted dashboard) live on the local host and inherit Nexus's "Privacy by construction" principle (see README.md, Design Principle 5): telemetry, traces, and logs are local-only by default, and secret patterns are redacted before any opt-in export. Do not embed secrets, tokens, or PII in a generated artifact, and do not add a remote fetch/telemetry beacon to a template -- a self-contained artifact has nothing to leak.

## Instructions

1. Identify the artifact and consult the decision table. If it is an HTML row, proceed; if Markdown, stop and emit Markdown.
2. Pick the closest reference template and adapt its content. Keep the layout system, accessibility affordances, and self-contained structure.
3. Run `hallmark-design` (`audit` verb) over the result so it does not read as AI-generated.
4. If the artifact is persisted, confirm the privacy note above: no secrets embedded, no outbound calls added.
5. Return the artifact (and, when shared as a file, note the path).

## Verification

- [ ] The HTML-vs-Markdown choice matches the decision table (and Markdown was chosen when appropriate).
- [ ] The artifact is self-contained: no external CSS/JS/CDN, no outbound network call.
- [ ] Accessibility holds: labels present, focus states visible, meaning is not color-only, tabs are keyboard-navigable.
- [ ] No ASCII diagram was used where a diagram was needed (SVG instead).
- [ ] `hallmark-design` audit passes over the output.
- [ ] No secrets or PII embedded; privacy note honored for persisted artifacts.

## Related Skills

- `hallmark-design` - ensures the chosen HTML looks designed rather than AI-generated; always compose with this skill.
- `ui-component-generation` - generate a component with a defined contract, then render it inside one of these templates.
- `frontend-ui-engineering` - page-level architecture when the artifact grows into an app surface.
- `technical-writer` - when Markdown is the right choice, this skill defers to writing conventions there.
