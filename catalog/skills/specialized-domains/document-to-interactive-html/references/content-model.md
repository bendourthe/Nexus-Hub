# Normalized Content Model

This document defines the intermediate representation (the "content model") that every supported source format maps into. It is the single stable contract between extraction (`scripts/extract_content.py`) and presentation building (`scripts/build_presentation.py`): the builder consumes this model and never reads the source format directly, so a new input format only needs a new extractor that emits this shape.

The model is plain JSON. It is described here in prose plus a commented example; it is NOT a runtime dependency (no JSON Schema file is required at runtime). The extractor emits an object that conforms to this description, and the builder reads it back.

## Top-level object

A content model is a single JSON object with three required fields and one optional field.

- `schema_version` (optional integer, default `1`): the model version. Present so the builder can reject a model it does not understand. Omit or set to `1` for the current shape.
- `title` (string, required): the presentation title. For a single source this is the document title; for multiple sources it is a synthesized umbrella title.
- `sources` (array, required): an ordered list of source descriptors, one per input document, in input order. Each entry is `{ "path": string, "format": string, "title": string }` where `format` is one of `pptx`, `docx`, `xlsx`, `pdf`. The order of this list defines multi-file ordering and is the attribution lookup for each section (see `source_index` below).
- `sections` (array, required): an ordered list of section objects (defined below). Order is significant and is preserved end to end.

Commented example (JSON does not allow comments; the `//` lines are illustrative only and must be removed in real output):

```json
{
  "schema_version": 1,
  "title": "Q3 Review",                  // umbrella title
  "sources": [
    { "path": "q3-deck.pptx",  "format": "pptx", "title": "Q3 Deck" },
    { "path": "q3-report.docx", "format": "docx", "title": "Q3 Report" }
  ],
  "sections": [
    {
      "heading": "Q3 Review",            // first section is usually the title slide
      "subheading": "Quarterly results",
      "kind": "title",
      "source_index": 0,                  // index into sources[]
      "blocks": []
    },
    {
      "heading": "Revenue by region",
      "subheading": null,
      "kind": "data",
      "source_index": 1,
      "blocks": [
        {
          "type": "chart",
          "chart_type_hint": "bar",
          "categories": ["NA", "EMEA", "APAC"],
          "series": [ { "name": "Revenue", "values": [120, 85, 60] } ]
        }
      ]
    }
  ]
}
```

## Section object

Each entry in `sections` is an object with these fields.

- `heading` (string, required): the section or slide title. May be an empty string when a source slide has no title, but the field is always present.
- `subheading` (string or null, optional): a secondary line under the heading. Use `null` when absent.
- `kind` (string, required): one of the following, which the builder uses to pick a layout.
    - `title`: the opening title section (document title + subtitle). Typically the first section.
    - `content`: the default section, a heading plus a mix of prose, bullets, tables, images.
    - `section-break`: a divider that introduces a new part (or, in multi-file mode, a new source). Usually heading-only.
    - `data`: a data-forward section dominated by one or more `chart` or `table` blocks (the usual mapping for a spreadsheet sheet).
    - `quote`: a section built around a pulled quotation.
    - `image`: a section dominated by a single image (a full-bleed figure).
    - `appendix`: supplementary material placed after the main flow (for example, overflow tables or collected speaker notes).
- `source_index` (integer, required): the zero-based index into the top-level `sources` array that this section came from. This is how multi-file attribution is preserved. A synthesized section (an agenda or overview the extractor generates rather than reads from a source) uses the index of the source it summarizes, or `0` when it summarizes all sources.
- `blocks` (array, required): an ordered list of block objects (defined below). May be empty (for example, a `title` or `section-break` section).

## Block kinds

Every entry in a section's `blocks` array is an object whose `type` field selects one of the following shapes. Order within `blocks` is preserved.

- `paragraph`: a run of prose.
    - `{ "type": "paragraph", "text": string }`
- `bullets`: a (possibly nested) list. Nesting is expressed by an integer `depth` on each item (0 = top level, 1 = one level in, and so on) rather than by nesting arrays, so the builder can render it with a single pass.
    - `{ "type": "bullets", "items": [ { "text": string, "depth": integer }, ... ] }`
- `table`: a tabular block with an optional header row.
    - `{ "type": "table", "header": [string, ...], "rows": [ [string, ...], ... ] }`
    - `header` may be an empty array when the source table has no header row. Every row is an array of cell strings; cells are stringified (numbers become their string form).
- `image`: a raster figure. Bytes are carried inline as a base64 `data:` URI so the final HTML is self-contained (see `references/extraction-runbook.md` for the size budget and how bytes are extracted per format). `alt` is required for accessibility even when synthesized.
    - `{ "type": "image", "data_uri": string, "alt": string }`
    - `data_uri` has the form `data:image/<subtype>;base64,<...>`.
- `chart`: a typed data series derived from a spreadsheet range (or any numeric source). The builder renders it as an inline SVG or canvas chart with no charting library. `chart_type_hint` is advisory; the builder or the enrichment pass may override it for the data shape.
    - `{ "type": "chart", "chart_type_hint": string, "categories": [string, ...], "series": [ { "name": string, "values": [number, ...] }, ... ] }`
    - `chart_type_hint` is one of `bar`, `line`, `pie`, `doughnut`. `categories` labels the x-axis (or the slices for pie/doughnut). Each series `values` array aligns positionally with `categories`.
- `code`: a preformatted code or monospace block.
    - `{ "type": "code", "text": string, "language": string }`
    - `language` may be an empty string when unknown.
- `quote`: a pulled quotation with optional attribution.
    - `{ "type": "quote", "text": string, "attribution": string }`
    - `attribution` may be an empty string.
- `notes`: speaker notes. The builder renders these hidden by default (a presenter-only view), so they never appear on the slide face.
    - `{ "type": "notes", "text": string }`

A block of an unknown `type` MUST be ignored by the builder (forward compatibility), not treated as an error.

## Per-format mapping

Each extractor maps its format into the model as follows. The full per-format coverage, library choice, and gotchas live in `references/extraction-runbook.md`; this section fixes the structural mapping the builder relies on.

### PowerPoint (.pptx) -- preserve the flow

- One slide maps to exactly one `section`, in slide order. Preserving slide order is the "follows the same flow" guarantee for the single-deck mode.
- The slide title placeholder maps to the section `heading`; a subtitle placeholder maps to `subheading`.
- The first slide is `kind: "title"`; slides whose only content is a title (a divider slide) are `kind: "section-break"`; the rest are `kind: "content"` (or `data` when dominated by a chart/table).
- Body text frames map to `paragraph` blocks, or to a single `bullets` block when the frame has list levels (the paragraph indent level becomes the item `depth`).
- Slide tables map to `table` blocks; embedded pictures map to `image` blocks (base64).
- The slide's notes-slide text maps to a single `notes` block on that section.

### Word (.docx) and PDF (.pdf) -- present the report

- Heading-styled paragraphs (Word `Heading 1`/`Heading 2`, or detected headings in PDF) define section boundaries: each heading starts a new `section` whose `heading` is the heading text.
- Body paragraphs between headings map to `paragraph` blocks; list paragraphs map to `bullets` (with `depth` from the list level); tables map to `table` blocks; inline images map to `image` blocks.
- The document title maps to the top-level `title` and to a leading `kind: "title"` section.
- A synthesized agenda is added as a `kind: "section-break"` (or `content`) section near the front, listing the section headings as a `bullets` block. This is what turns a flat report into "a presentation OF the report" and is generated by the extractor, not read from the source. Its `source_index` points at the source it summarizes.

### Excel (.xlsx) -- chart the data

- Each worksheet maps to one `section`, in workbook order, usually `kind: "data"`. The sheet name is the `heading`.
- A contiguous range with a label row/column and numeric body maps to a `chart` block: the label row becomes `categories`, each labeled numeric column (or row) becomes a series `{ name, values }`, and `chart_type_hint` is inferred (a small category count with one series leans `pie`/`doughnut`; multiple series or a time-like first column leans `line`; otherwise `bar`).
- Ranges that are not cleanly numeric map to `table` blocks instead, so no data is silently dropped.

## Multi-file merge

When more than one input is given, the extractor processes inputs in the order received and produces one merged model.

- Each source contributes a labeled, contiguous run of sections in input order. Within a source, that source's own section order is preserved.
- Every section's `source_index` points at its originating entry in `sources`, so the builder can label or group by source.
- A `section-break` section is inserted at the boundary into each new source, with the source title as its `heading`, so the compiled deck reads as distinct parts rather than a blur.
- The extractor MAY prepend a synthesized overview section (`kind: "title"` or `section-break`) that names all sources; its `source_index` is `0`. This is the "compile all sources into one" behavior.
- The top-level `title` is synthesized for the multi-file case (for example, from the first source title or a generic umbrella label).

## Determinism and encoding

- Output ordering is deterministic: sources in input order, sections in source order, blocks in document order. No set/dict iteration is allowed to leak nondeterministic order into the output.
- All string content is ASCII-safe in the model where the source allows; non-ASCII source text is preserved as valid UTF-8 in the JSON (JSON is UTF-8), but the extractor never injects non-ASCII of its own.
- The model is the only contract: anything the builder needs about a source must be representable as one of the block kinds above. If a real document needs something none of these kinds can hold, that is a schema gap to resolve here before extending the extractor.
