---
name: document-to-interactive-html
description: Turn one or more documents (PDF, Word, Excel, PowerPoint) into a SINGLE self-contained, offline, interactive HTML presentation using local-only parsing and LLM-native HTML generation. Use this skill whenever the user says "turn this PowerPoint into an interactive presentation", "make an interactive HTML deck from these docs", "presentify this report", "turn these documents into a presentation", "convert this PDF/Word/Excel into an interactive presentation", or wants a captivating navigable deck built FROM existing documents (a single deck preserves its flow, a single report becomes a presentation of the report, multiple files compile into one). SKIP: generating a NEW .pptx/.docx/.xlsx/.pdf from scratch (use the pptx-generation / docx-generation / xlsx-generation / pdf-document-generation skills), one-off static charts or data exports, or a plain HTML document with no presentation flow or interactivity.
summary_l0: "Turn one or more documents into a self-contained interactive HTML presentation"
overview_l1: "This skill converts one or more source documents (PDF, Word, Excel, PowerPoint) into a single self-contained, offline, interactive HTML presentation. It composes two local stages: a lazy-import Python extractor maps each format into a normalized content model, then a deterministic builder injects that model into a self-contained template, inlining base64 images and rendering spreadsheet data as inline SVG charts with no charting library and no CDN. The agent then runs an enrichment pass to elevate the plain baseline into a captivating deck. Three modes: a single PowerPoint preserves its slide flow, a single report becomes a paced presentation of that report, and multiple or mixed files compile into one attributed deck. Parsing is local-only; HTML generation is LLM-native; no document leaves the machine and the output opens with zero external network requests."
---

# Document to Interactive HTML

Turn existing documents into a single self-contained, offline, interactive HTML presentation. The pipeline is deliberately compositional: a local extractor reads any mix of PDF / Word / Excel / PowerPoint into one normalized content model, a deterministic builder turns that model into a plain but correct offline deck, and the agent runs an enrichment pass to make the result captivating. Nothing leaves the machine, the output has zero external dependencies, and the deck carries full navigation, an outline, progress, fullscreen, keyboard control, reduced-motion support, and inline charts.

This skill is the connector between Nexus-Hub's document-reading skills (`[[pptx-generation]]`, `[[docx-generation]]`, `[[xlsx-generation]]`, `[[pdf-document-generation]]`) and its self-contained-HTML design discipline (`[[html-output-conventions]]`, `[[hallmark-design]]`, `[[theme-tokens]]`, `[[brand-styling]]`). It does not reinvent either side; it wires ingestion to an interactive-presentation output.

## When to Use This Skill

Use this skill when:

- The user wants an existing PowerPoint turned into a more interactive, more visually considered deck that follows the same flow.
- The user wants a report (Word or PDF) presented as a paced deck: a title, an agenda, one section per heading, data surfaced as charts.
- The user has several documents (any mix of formats) and wants them compiled into one presentation with per-source attribution.
- The user wants a spreadsheet's data shown as charts inside a navigable deck rather than as a static export.
- The deck must work offline, open from a single file, and contain no external requests (a confidential report, an air-gapped demo, an email attachment).

**Trigger phrases**: "turn this PowerPoint into an interactive presentation", "presentify this report", "make an interactive HTML deck from these docs", "turn these documents into a presentation", "convert this PDF/Word/Excel into an interactive presentation", "build a deck from this report", "compile these documents into one presentation".

**When NOT to use**:

- Generating a brand-new document from scratch: use `[[pptx-generation]]`, `[[docx-generation]]`, `[[xlsx-generation]]`, or `[[pdf-document-generation]]`. This skill presents documents that already exist; it does not author source documents.
- A one-off static chart or a data export with no presentation flow.
- A plain HTML document (a README, a long-form article) that has no slide model or interactivity. Use `[[html-output-conventions]]` directly for non-presentation HTML.
- Scanned / image-only PDFs that need OCR, or video / audio embedding: both are out of scope for v1 (see `references/extraction-runbook.md`).

## The Pipeline

Two local stages plus one agent stage. The contract between the stages is the normalized content model defined in `references/content-model.md`; the builder never reads a source format directly, so the model is the single stable interface.

```
inputs (.pptx/.docx/.xlsx/.pdf, or a folder)
   |
   |  scripts/extract_content.py   (local, lazy-import parsers)
   v
content-model JSON  (references/content-model.md)
   |
   |  scripts/build_presentation.py  (deterministic; assets/presentation-template.html + assets/theme.json)
   v
baseline .html  (self-contained, offline, inline SVG charts)
   |
   |  enrichment pass  (LLM-native; references/interactive-features.md + hallmark-design)
   v
captivating interactive .html
```

## Instructions

1. **Detect the inputs and the mode.** Inspect the input paths and pick the mode (it is auto-detected and overridable):
    - One `.pptx` -> **preserve the flow**: one slide maps to one section in slide order; keep that order, only make it more interactive and better designed.
    - One `.docx` / `.pdf` / `.xlsx` -> **present the report**: synthesize a title and agenda, one section per heading, and surface data as inline charts.
    - Two or more files (any mix), or a folder -> **compile the sources**: each source contributes a labeled run of sections introduced by a section-break, optionally preceded by a synthesized overview. Preserve per-source attribution.
2. **Extract to the content model.** Run the local extractor:

    ```bash
    python scripts/extract_content.py <input...> -o model.json [--title "..."] [--max-image-bytes N]
    ```

    It dispatches by extension, lazy-imports each parser (so a missing library prints `pip install <lib>` and exits non-zero rather than crashing), carries images inline as base64 within a size budget, preserves slide / section / block order, and merges multi-file input with a `sources` manifest. Per-format coverage, gotchas, and the image budget are documented in `references/extraction-runbook.md`; the emitted JSON shape is `references/content-model.md`.
3. **Select a theme.** The builder defaults to `assets/theme.json`. To restyle, pass `--theme <path>` with either a curated `[[theme-tokens]]` theme JSON (brand-neutral) or a `[[brand-styling]]` per-brand `tokens.json` (the builder reads the shared palette / fonts / spacing keys and ignores brand-only fields). Ask the user for brand tokens before inventing colors; do not guess a brand.
4. **Build the baseline deck.** Run the deterministic builder:

    ```bash
    python scripts/build_presentation.py model.json -o deck.html [--theme theme.json]
    ```

    It populates `assets/presentation-template.html` from the content model, renders each block kind (paragraph, nested bullets, table, base64 image, quote, code, hidden speaker notes), draws `chart` blocks as inline SVG (bar / line / pie / doughnut, no library, no CDN), merges the theme, and runs a post-write self-check that fails if the output contains any external `http(s)` / `cdn` reference. The result is correct and fully offline, but plain.
5. **Run the enrichment pass.** This is the LLM-native step and the reason the output is captivating rather than templated. Following `references/interactive-features.md` and `[[hallmark-design]]`: choose a narrative structure (especially turn a dense report into an agenda plus paced reveals), tighten copy to presentation grade without inventing facts, pick the right chart per data shape (override a `chart_type_hint` when the data wants a different form), add intentional emphasis and purposeful motion, then run the `[[hallmark-design]]` anti-slop gates and clear every failing one. Never introduce an external dependency and never break the offline guarantee.
6. **Verify self-contained and offline.** Per `[[html-output-conventions]]`, confirm the final `.html` opens with zero external network requests (grep the file for external `http(s)` / `cdn` references outside comments; expect none), is well-formed and ASCII-safe, and that every source section is represented with charts rendering inline. The interactive feature set (navigation, outline, progress, fullscreen, keyboard map, reduced-motion, print path) is cataloged in `references/interactive-features.md`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just inline a CDN chart library (Chart.js, D3) for nicer charts" | This breaks the single non-negotiable guarantee: a CDN reference makes the deck fail offline and leaks a network request. The builder renders inline SVG charts with no library precisely so the output stays self-contained. A CDN font or script is the same failure. |
| "I'll skip extraction and just eyeball the PDF / paste the slides" | Eyeballing loses tables, data series, speaker notes, and ordering, and it is not deterministic. Run `scripts/extract_content.py` so the content model captures structure the eye skips, and so a re-run is reproducible. |
| "The baseline build looks fine, I'll ship it" | The deterministic baseline is correct but plain by design. Shipping it without the enrichment pass fails the `[[hallmark-design]]` bar (templated layout, report-grade copy on slides, wrong chart for the data). The enrichment pass is mandatory, not optional polish. |
| "It's a slide deck, I'll re-sequence it to flow better" | In single-deck mode the author already chose the order; preserving it is the explicit guarantee. Re-sequence reports (which are flat), not decks. Reordering a PowerPoint silently breaks the "follows the same flow" contract. |
| "I'll embed the brand's web font via @import for the real look" | An `@import` of a font CDN is an external request that breaks offline. System font stacks only; a custom font must be base64-embedded as `@font-face`, never fetched. |
| "Multiple sources, I'll merge them into one smooth narrative" | Compiling sources requires per-source attribution: each source gets a labeled run introduced by a section-break. Blending two sources into an indistinguishable middle loses the provenance the multi-file mode exists to preserve. |
| "A missing parser library means I should hardcode an import or vendor it" | Every parser is lazy-imported on purpose so one missing library never blocks the others. If extraction reports `pip install <lib>`, install that library; do not move imports to module top level or bundle a parser. |

## Verification

Binary checklist - each item describes an observable artifact or state.

- [ ] The output `.html` exists at the requested path and opens in a browser.
- [ ] Opening it issues ZERO external network requests (DevTools network tab is empty, or `grep -Ei 'https?://|cdn' deck.html` finds nothing outside comments).
- [ ] Every source section from the content model is represented as a slide in the deck.
- [ ] Each `chart` block renders as an inline SVG chart (no `<script src>`, no charting-library reference).
- [ ] Embedded images display from inline `data:` URIs (no external image `src`).
- [ ] Navigation works: prev/next, keyboard arrows, the outline panel, progress, and fullscreen all respond; reduced-motion is honored.
- [ ] In single-deck mode the slide order matches the source `.pptx`; in report mode an agenda and per-heading sections are present.
- [ ] The HTML is well-formed (tag balance) and ASCII-safe.
- [ ] The enrichment pass has run and the output clears the `[[hallmark-design]]` anti-slop gates (not the plain baseline).
- [ ] `make validate` passes (orphan-bundle audit clean, JSON integrity green).

"The deck looks nice" is not a verification criterion. The verification is: does it open offline with no external requests, is every source section present, do charts render inline, and does it clear the hallmark-design gates.

## Bundled Resources

The skill ships a Tier-3 bundle; load each file on demand rather than inlining it here.

- `scripts/extract_content.py` - the local, lazy-import multi-format extractor (PDF / Word / Excel / PowerPoint -> content-model JSON).
- `scripts/build_presentation.py` - the deterministic baseline builder (content model + template + theme -> one self-contained `.html` with inline SVG charts).
- `references/content-model.md` - the normalized content-model schema; the stable contract between the extractor and the builder.
- `references/extraction-runbook.md` - per-format coverage, library + `pip install` lines, gotchas, the base64 image budget, determinism, and the out-of-scope list (OCR, media, native chart objects).
- `references/interactive-features.md` - the interactive feature catalog, the theme-override path, and the enrichment pass tied to `[[hallmark-design]]` and the three input modes.
- `assets/presentation-template.html` - the self-contained offline scaffold (all CSS/JS inline, no external requests) the builder populates.
- `assets/theme.json` - the default theme tokens the template reads, overridable via `[[theme-tokens]]` / `[[brand-styling]]`.

## Related Skills

- [[pptx-generation]] -- reads / authors PowerPoint; the upstream skill for a `.pptx` source and for generating a NEW deck (the inverse direction).
- [[docx-generation]] -- reads / authors Word; the upstream skill for a `.docx` report source.
- [[xlsx-generation]] -- reads / authors Excel; the upstream skill for a `.xlsx` data source that becomes inline charts.
- [[pdf-document-generation]] -- reads / authors PDF; the upstream skill for a `.pdf` report source.
- [[html-output-conventions]] -- the self-contained, single-file HTML discipline the output must hold (everything inlined, works offline).
- [[hallmark-design]] -- the anti-"looks-AI-generated" gates the enrichment pass runs to take the baseline to captivating.
- [[theme-tokens]] -- supplies a curated brand-neutral theme as a `--theme` override for the builder.
- [[brand-styling]] -- supplies a per-brand `tokens.json` as a `--theme` override when the deck must be on-brand.
