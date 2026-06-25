---
name: document-to-interactive-html
description: Turn one or more documents (PDF, Word, Excel, PowerPoint) into a SINGLE self-contained, offline, UNIQUE interactive website (NOT a static slide deck) using local-only parsing and LLM-native HTML generation. Use this skill whenever the user says "presentify this", "turn this PowerPoint into an interactive website", "make an interactive site from these docs", "turn these documents into an interactive presentation", "convert this PDF/Word/Excel into an interactive website", or wants an engaging, navigable, dynamic web experience built FROM existing documents - with real figures rendered as INTERACTIVE charts (zoom, pan, filter series, adjust axes), a fresh bespoke design each run, and an optional caller-specified style or color scheme. SKIP: generating a NEW .pptx/.docx/.xlsx/.pdf from scratch (use the pptx-generation / docx-generation / xlsx-generation / pdf-document-generation skills), one-off static charts or data exports, or a plain HTML document with no interactivity.
summary_l0: "Turn one or more documents into a unique, interactive, self-contained website"
overview_l1: "This skill converts one or more source documents (PDF, Word, Excel, PowerPoint) into a single self-contained, offline, UNIQUE interactive website - not a static slide deck. A lazy-import Python extractor maps each format into a normalized content model; the agent then authors a bespoke interactive web experience from that model, with a clear, intuitive, navigable structure, real figures rendered as INTERACTIVE charts (zoom, pan, filter series, adjust axes) built from inlined vanilla JavaScript with no CDN, intentional motion, and a fresh design every run that can also honor a caller-specified style or color scheme. A bundled deterministic builder offers an optional plain baseline. Three modes: a single PowerPoint preserves its flow, a single report becomes a navigable site of itself, and multiple or mixed files compile into one attributed site. Parsing is local-only; generation is LLM-native; nothing leaves the machine and the output opens with zero external network requests."
---

# Document to Interactive HTML

Turn existing documents into a single self-contained, offline, UNIQUE interactive website - not a static slide deck. The pipeline is compositional: a local extractor reads any mix of PDF / Word / Excel / PowerPoint into one normalized content model, and the agent then authors a bespoke interactive web experience from that model. The whole point is to move AWAY from PowerPoint-style static decks toward an engaging, dynamic interface: a clear, intuitive, navigable structure (sections, in-page navigation, scroll or routed views - whatever fits the content), real figures rendered as INTERACTIVE charts the reader can manipulate (zoom, pan, toggle series, adjust axis limits), intentional motion, and a design that is fresh each run. Nothing leaves the machine and the output has zero external dependencies.

A bundled deterministic builder (`scripts/build_presentation.py`) is available as an OPTIONAL plain baseline - a fast, reproducible, simple sectioned page - but it is not the goal and its output is intentionally minimal. The primary, default path is LLM-native authoring of a unique interactive site; reach for the builder only when a caller explicitly wants a quick deterministic draft to elevate.

This skill is the connector between Nexus-Hub's document-reading skills (`[[pptx-generation]]`, `[[docx-generation]]`, `[[xlsx-generation]]`, `[[pdf-document-generation]]`) and its self-contained-HTML design discipline (`[[html-output-conventions]]`, `[[hallmark-design]]`, `[[theme-tokens]]`, `[[brand-styling]]`). It does not reinvent either side; it wires ingestion to a unique interactive-website output.

## When to Use This Skill

Use this skill when:

- The user wants an existing PowerPoint turned into a more interactive, more dynamic website that follows the same flow.
- The user wants a report (Word or PDF) presented as a navigable interactive site: an overview, an intuitive section structure from the headings, data surfaced as interactive charts.
- The user has several documents (any mix of formats) and wants them compiled into one interactive site with per-source attribution.
- The user wants a spreadsheet's data shown as interactive, manipulable charts (zoom, filter, axis controls) inside a navigable site rather than a static export.
- The site must work offline, open from a single file, and contain no external requests (a confidential report, an air-gapped demo, an email attachment).

**Trigger phrases**: "presentify this", "turn this PowerPoint into an interactive website", "make an interactive site from these docs", "turn these documents into an interactive presentation", "convert this PDF/Word/Excel into an interactive website", "build an interactive site from this report", "compile these documents into one interactive site".

**When NOT to use**:

- Generating a brand-new document from scratch: use `[[pptx-generation]]`, `[[docx-generation]]`, `[[xlsx-generation]]`, or `[[pdf-document-generation]]`. This skill presents documents that already exist; it does not author source documents.
- A one-off static chart or a data export with no presentation flow.
- A plain HTML document (a README, a long-form article) that has no slide model or interactivity. Use `[[html-output-conventions]]` directly for non-presentation HTML.
- Scanned / image-only PDFs that need OCR, or video / audio embedding: both are out of scope for v1 (see `references/extraction-runbook.md`).

## The Pipeline

A local extraction stage, then LLM-native authoring. The contract is the normalized content model in `references/content-model.md`; nothing reads a source format directly after extraction, so the model is the single stable interface.

```
inputs (.pptx/.docx/.xlsx/.pdf, or a folder)
   |
   |  scripts/extract_content.py   (local, lazy-import parsers)
   v
content-model JSON  (references/content-model.md)
   |
   |  LLM-native authoring  (PRIMARY: a unique interactive website;
   |                         references/interactive-features.md + [[hallmark-design]])
   v
unique interactive .html  (self-contained, offline, dynamic JS charts)

   (optional)  scripts/build_presentation.py  ->  a plain deterministic baseline,
               only when a fast, simple, reproducible draft is explicitly wanted
```

## Instructions

1. **Detect the inputs and the mode.** Inspect the input paths and pick the mode (auto-detected, overridable). In every mode the output is a navigable website, not a slide sequence:
    - One `.pptx` -> **preserve the flow**: keep the source's content order, but render it as an interactive site (sections + in-page navigation), better designed and more dynamic than the original.
    - One `.docx` / `.pdf` / `.xlsx` -> **present the source**: a clear landing/overview, an intuitive section structure from the headings, and data surfaced as interactive charts.
    - Two or more files (any mix), or a folder -> **compile the sources**: each source is a labeled, attributed area of the site, optionally preceded by a synthesized overview. Preserve per-source attribution.
2. **Extract to the content model.** Run the local extractor:

    ```bash
    python scripts/extract_content.py <input...> -o model.json [--title "..."] [--max-image-bytes N]
    ```

    It dispatches by extension, lazy-imports each parser (so a missing library prints `pip install <lib>` and exits non-zero rather than crashing), carries images inline as base64 within a size budget, preserves source / section / block order, and merges multi-file input with a `sources` manifest. `chart` blocks carry the real data series (categories + values), so the charts you build use the source's actual numbers, never invented ones. Per-format coverage and the image budget are in `references/extraction-runbook.md`; the JSON shape is `references/content-model.md`.
3. **Choose the design and style - fresh each run.** Do NOT reuse a fixed template look; author a bespoke design for this content so two runs do not look alike (a recognizable house style is the templated look `[[hallmark-design]]` rejects). If the caller specified a style or color scheme - a `[[theme-tokens]]` set name, a `[[brand-styling]]` brand `tokens.json`, or plain words like "dark, minimal, editorial, playful, high-contrast" - honor it as the design direction. Pull brand tokens via `[[theme-tokens]]` / `[[brand-styling]]`; ask the user for brand tokens before inventing a brand's colors.
4. **Author the interactive website (PRIMARY path).** From the content model, write ONE self-contained `.html` that is a genuine interactive web experience, not a deck:
    - **Structure**: a clear, intuitive, navigable layout - an overview/landing, a section nav (in-page anchors, a sticky nav, tabs, or routed views; choose what fits), and scannable sections. Not a forced one-screen-per-slide sequence.
    - **Interactive charts**: render every figure that has real data as an INTERACTIVE chart built from inlined vanilla JavaScript (no CDN, no external library) - the reader can zoom, pan, toggle/hide series via a legend, and adjust axis limits. Use `<canvas>` or inline SVG plus a small inlined JS controller. See `references/interactive-features.md` for the dynamic-chart patterns.
    - **Real visuals**: if the source carries figures, tables, or images, they appear in the site (images inline as base64; data as the interactive charts above; tables as sortable/filterable where it helps).
    - **Motion + responsiveness**: intentional, purposeful motion guarded by `prefers-reduced-motion`; responsive from phone to projector.
    - Hold `[[html-output-conventions]]` (one self-contained file, everything inlined, works offline) and `[[hallmark-design]]` (unique, non-templated, anti-slop) throughout.
5. **(Optional) Plain baseline.** Only when a caller explicitly wants a fast, simple, reproducible draft, run `python scripts/build_presentation.py model.json -o draft.html [--theme theme.json]` for a minimal deterministic sectioned page, then elevate it into the interactive site above. This is a convenience, not the default; its output is plain by design (static inline SVG, fixed layout) and does not by itself meet the interactive-website bar.
6. **Verify self-contained, offline, and interactive.** Per `[[html-output-conventions]]`, confirm the final `.html` opens with zero external network requests (grep for external `http(s)` / `cdn` references outside comments; expect none), is well-formed and ASCII-safe, every source section is represented, and the charts are genuinely interactive (zoom / pan / series-toggle / axis controls respond). Then clear the `[[hallmark-design]]` anti-slop gates.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll output a slide deck / a slideshow of full-screen slides" | The deliverable is a unique interactive WEBSITE, not a static slide sequence. A one-screen-per-slide deck is exactly the PowerPoint experience this skill moves away from. Build a navigable site. |
| "A static SVG or a screenshot of the chart is good enough" | If a figure carries real data, render it as an INTERACTIVE chart (zoom, pan, toggle series, adjust axes) from inlined JS. A static image throws away the main advantage over the original PDF/PPTX. Static is a fallback only when interactivity is genuinely impossible. |
| "I'll reuse my usual template / house design" | A recognizable fixed look across runs is the templated 'AI-generated' signature `[[hallmark-design]]` rejects. Author a fresh, content-appropriate design each run; honor a caller-specified style when one is given. |
| "I'll just inline a CDN chart library (Chart.js, D3, Plotly) for interactivity" | A CDN reference breaks the offline guarantee and leaks a network request. Build interactivity from inlined vanilla JS with no external library. A CDN font or script is the same failure. |
| "I'll skip extraction and just eyeball the PDF / paste the slides" | Eyeballing loses tables, data series, speaker notes, and ordering, and is not reproducible. Run `scripts/extract_content.py` so the content model captures the structure the eye skips - and the real numbers your charts must use. |
| "The deterministic builder's output looks fine, I'll ship that" | `build_presentation.py` is an OPTIONAL plain draft (static SVG, fixed layout); it does not meet the interactive-website bar. It is a starting point to elevate, never the final deliverable. |
| "I'll embed the brand's web font via @import for the real look" | An `@import` of a font CDN is an external request that breaks offline. System font stacks only; a custom font must be base64-embedded as `@font-face`, never fetched. |
| "Multiple sources, I'll merge them into one smooth narrative" | Compiling sources requires per-source attribution: each source is a labeled, attributed area. Blending two sources into an indistinguishable middle loses the provenance the multi-file mode exists to preserve. |
| "A missing parser library means I should hardcode an import or vendor it" | Every parser is lazy-imported on purpose so one missing library never blocks the others. If extraction reports `pip install <lib>`, install it; do not move imports to module top level or bundle a parser. |

## Verification

Binary checklist - each item describes an observable artifact or state.

- [ ] The output `.html` exists at the requested path and opens in a browser.
- [ ] Opening it issues ZERO external network requests (DevTools network tab is empty, or `grep -Ei 'https?://|cdn' out.html` finds nothing outside comments).
- [ ] The output is a navigable WEBSITE (an overview plus section navigation that works), not a static one-screen-per-slide deck.
- [ ] Every figure with real data renders as an INTERACTIVE chart: zoom / pan, series toggle via the legend, and axis adjustment all respond - and the numbers match the source.
- [ ] Every source section from the content model is represented; embedded images display from inline `data:` URIs.
- [ ] The design is bespoke for this content (not a recognizable fixed template), and any caller-specified style or color scheme is applied.
- [ ] Motion is purposeful and `prefers-reduced-motion` is honored; the layout is responsive.
- [ ] In single-source mode the content order matches the source; in multi-source mode each source is a labeled, attributed area.
- [ ] The HTML is well-formed (tag balance) and ASCII-safe, and it clears the `[[hallmark-design]]` anti-slop gates.
- [ ] `make validate` passes (orphan-bundle audit clean, JSON integrity green).

"The site looks nice" is not a verification criterion. The verification is: does it open offline with no external requests, is it a navigable interactive website (not a deck), are the charts genuinely manipulable on real data, and does it clear the hallmark-design gates.

## Bundled Resources

The skill ships a Tier-3 bundle; load each file on demand rather than inlining it here.

- `scripts/extract_content.py` - the local, lazy-import multi-format extractor (PDF / Word / Excel / PowerPoint -> content-model JSON).
- `scripts/build_presentation.py` - the OPTIONAL deterministic baseline builder (content model + template + theme -> one self-contained plain `.html` with static inline SVG charts). A convenience draft to elevate, not the default path; the primary deliverable is the LLM-authored unique interactive site.
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
- [[brand-styling]] -- supplies a per-brand `tokens.json` as a `--theme` override when the site must be on-brand.
