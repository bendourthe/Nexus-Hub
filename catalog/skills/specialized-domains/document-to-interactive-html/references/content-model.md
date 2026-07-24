# Normalized Content Model

This document defines the intermediate representation (the "content model") that every supported source format maps into. It is the single stable contract between extraction (`scripts/extract_content.py`) and presentation building (`scripts/build_presentation.py`): the builder consumes this model and never reads the source format directly, so a new input format only needs a new extractor that emits this shape.

The model is plain JSON. It is described here in prose plus a commented example; it is NOT a runtime dependency (no JSON Schema file is required at runtime). The extractor emits an object that conforms to this description, and the builder reads it back.

## Top-level object

A content model is a single JSON object with three required fields and three optional fields.

- `schema_version` (optional integer, default `1`): the model version. Present so the builder can reject a model it does not understand. The current extractor emits `2`. **Compatibility rule**: every v2 addition is ADDITIVE and optional - a v1 consumer that ignores unknown fields (exactly as it must ignore unknown block types) reads a v2 model correctly, and a v2 consumer treats every new field as absent-by-default when reading a v1 model. A consumer MUST NOT reject a model solely because `schema_version` is higher than it knows, as long as the required v1 fields are present.
- `title` (string, required): the presentation title. For a single source this is the document title; for multiple sources it is a synthesized umbrella title.
- `sources` (array, required): an ordered list of source descriptors, one per input document, in input order. Each entry is `{ "path": string, "format": string, "title": string }` where `format` is one of `pptx`, `docx`, `xlsx`, `pdf`, `code`, `markdown`, `text`, `csv` (the last four are the universal-ingestion formats). The order of this list defines multi-file ordering and is the attribution lookup for each section (see `source_index` below). **v2 optional field**: `deck_like` (boolean) - set `true` on a PDF source whose pages are landscape-oriented with low text density (a PDF exported from slides), so the mode auto-detect treats it as deck-like (preserve page order as slide flow).
- `sections` (array, required): an ordered list of section objects (defined below). Order is significant and is preserved end to end.
- `coverage` (object, optional, v2): the extraction coverage manifest the authoring stage reconciles against. Shape: `{ "per_source": [ <entry>, ... ] }` with one entry per source, in `sources` order. Each entry carries `path` (string) plus integer counts `images_found`, `images_kept`, `images_skipped`, `native_charts`, `tables`, `vector_regions_rasterized`, `vector_regions_skipped`, `scanned_pages_detected`, `ocr_pages`, `ocr_low_confidence`, `agent_read_pages`, and `skip_reasons` (array of human-readable strings, one per skipped item or aggregated skip decision, e.g. `"repeated-asset: image on 4 pages kept once (page 1)"`). Verification rule: every visual the manifest counts as found must be accounted for in the output - rendered, reconstructed, or explicitly skipped with a reason. **v3 optional sub-object**: `walk` (present only for a directory / repository input) records the recursive-walk accounting: `{ "root": string, "files_included": int, "gitignored": int, "binary_skipped": int, "dirs_ignored": int, "file_count_capped": int, "notes": [string] }`, where `notes` is a bounded, human-readable list of the ignore / cap decisions. The walk manifest is informational (it explains what the walk did NOT include); the per-source manifest still governs the per-file visual reconciliation.
- `tree` (object, optional, v3): present only for a directory / repository input, a nested representation of the ingested layout the authoring stage renders as a file-tree overview. Each node is `{ "name": string, "kind": "dir" | "file", "children": [ <node>, ... ] }`; a `file` node omits `children`. Only ingested (non-ignored) files appear, so the tree reflects what the site actually presents, not the raw on-disk directory.

Commented example (JSON does not allow comments; the `//` lines are illustrative only and must be removed in real output):

```json
{
  "schema_version": 2,
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
    - `overview`: a synthesized landing section for a directory / repository input (the repository name, a short description drawn from the README when present, and a bullets summary of the top-level areas). Typically the first section for a repository input. Unknown kinds already fall back to `content` in the builder, so a v1 / v2 builder renders it as a content section.
- `source_index` (integer, required): the zero-based index into the top-level `sources` array that this section came from. This is how multi-file attribution is preserved. A synthesized section (an agenda or overview the extractor generates rather than reads from a source) uses the index of the source it summarizes, or `0` when it summarizes all sources.
- `blocks` (array, required): an ordered list of block objects (defined below). May be empty (for example, a `title` or `section-break` section).

## Block kinds

Every entry in a section's `blocks` array is an object whose `type` field selects one of the following shapes. Order within `blocks` is preserved.

- `paragraph`: a run of prose.
    - `{ "type": "paragraph", "text": string }`
    - **v2 optional fields**: `provenance` (one of `text-layer` (the default when absent), `ocr`, `agent-read`) and `ocr_confidence` (number 0-1, present when provenance is `ocr`) - so fidelity checks know which text was recovered by OCR or agent-vision reading and must be verified against the page image.
- `bullets`: a (possibly nested) list. Nesting is expressed by an integer `depth` on each item (0 = top level, 1 = one level in, and so on) rather than by nesting arrays, so the builder can render it with a single pass.
    - `{ "type": "bullets", "items": [ { "text": string, "depth": integer }, ... ] }`
- `table`: a tabular block with an optional header row.
    - `{ "type": "table", "header": [string, ...], "rows": [ [string, ...], ... ] }`
    - `header` may be an empty array when the source table has no header row. Every row is an array of cell strings; cells are stringified (numbers become their string form).
    - **v2 optional fields**: `provenance` and `ocr_confidence`, with the same semantics as on `paragraph`. Numeric content in an `ocr`-provenance table must ALWAYS be verified against the page image during authoring, regardless of confidence.
- `image`: a raster figure. Bytes are carried inline as a base64 `data:` URI so the final HTML is self-contained (see `references/extraction-runbook.md` for the size budget and how bytes are extracted per format). `alt` is required for accessibility even when synthesized.
    - `{ "type": "image", "data_uri": string, "alt": string }`
    - `data_uri` has the form `data:image/<subtype>;base64,<...>`.
    - **v2 optional fields**: `caption` (string; nearby caption text when detected, e.g. a "Figure 3: ..." line directly below the figure), `page` (integer; 1-based source page or slide number), `origin` (one of `embedded-raster` - a raster embedded in a PDF page; `rasterized-region` - a vector-figure region rendered to a bitmap; `shape-picture` - a PPTX picture shape; `inline-image` - a DOCX inline image; `scanned-page` - a full-page image of a scanned PDF page for agent-vision reading; `standalone-image` - an image supplied as its own input file, e.g. a `.png` / `.jpg` / `.svg` in an ingested folder), and `classification` (string, default empty; filled by the figure-reconstruction protocol - one of `chart`, `map`, `diagram`, `table-image`, `photo`, `screenshot`, `decorative`).
    - **v3 optional prominence fields**: `width` and `height` (integers; the image's NATIVE pixel dimensions, computed from the original bytes before any budget downscale; absent when Pillow is unavailable or the bytes will not decode, e.g. SVG), and `page_fraction` (number 0..1, 3 decimals; the share of the source page / slide AREA the image occupied). `page_fraction` is set where source geometry exists (PDF embedded rasters and rasterized regions via their bbox, PPTX pictures via shape-vs-slide area) and is ABSENT for DOCX inline images, Markdown-embedded images, standalone image files, and scanned-page renders. The authoring stage uses these to preserve source prominence: a visual with a high `page_fraction` (roughly >= 0.5) or the sole / primary visual of its section is rendered as a hero, never flattened into a uniform thumbnail grid (see `references/interactive-features.md`).
    - **v3 optional annotation metadata** (`annotations`, PPTX only): an array of author-added overlay shapes captured OVER a picture (region rectangles / shaded zones, callout labels, leader lines, pins), for the overlay-recreation pattern in `references/figure-reconstruction.md` part 5. Each entry is `{ "shape_type": string, "bbox": [x, y, w, h], "text"?: string, "fill"?: "#RRGGBB", "line"?: "#RRGGBB", "group"?: string }`, where `bbox` is normalized to the underlying image's PLACED RECTANGLE (image-relative, 0..1, so the overlay scales with the image), `shape_type` is the PPTX shape-type name (e.g. `AUTO_SHAPE`, `TEXT_BOX`, `LINE`), `fill` / `line` are solid RGB colors (absent for theme-colored or unset fills, never guessed), and `group` is the enclosing group's name when the shape was grouped. Present ONLY for PPTX pictures that carry overlay shapes (a non-picture shape whose center lies inside the picture and is smaller than it); ABSENT for flattened sources (a PDF page image, or a PPTX whose annotations are baked into one picture), where the agent reads the annotations from the rendered image under the figure-reconstruction confidence gate.
- `chart`: a typed data series derived from a spreadsheet range (or any numeric source). The builder renders it as an inline SVG or canvas chart with no charting library. `chart_type_hint` is advisory; the builder or the enrichment pass may override it for the data shape.
    - `{ "type": "chart", "chart_type_hint": string, "categories": [string, ...], "series": [ { "name": string, "values": [number, ...] }, ... ] }`
    - `chart_type_hint` is one of `bar`, `line`, `pie`, `doughnut`. `categories` labels the x-axis (or the slices for pie/doughnut). Each series `values` array aligns positionally with `categories`.
    - **v2 optional fields**:
        - `provenance` (one of `source-data` - derived from a spreadsheet range; `native-chart` - extracted from a native PPTX/DOCX chart part with the source's real series values; `reconstructed-from-image` - rebuilt by the figure-reconstruction protocol from a static figure image).
        - `confidence` (one of `high`, `medium`, `low`; REQUIRED when provenance is `reconstructed-from-image` - the protocol's confidence-gate tier).
        - `source_image` (string; a base64 `data:` URI of the original figure image, powering the view-original toggle on reconstructed charts).
        - `caption` (string; the chart's own title or a nearby caption line when present).
        - `axis` (object with optional `x_label`, `y_label`, `y_min`, `y_max`, `unit`) - so reconstructions preserve the source's scales and units faithfully.
- `code`: a preformatted code or monospace block.
    - `{ "type": "code", "text": string, "language": string }`
    - `language` may be an empty string when unknown.
    - **v3 optional fields**: `path` (string; the repository-relative source path, set when the block comes from the source-code / config extractor) and `truncated` (boolean; `true` when a large source file was cut to the text-byte cap, in which case `text` ends with a clear truncation marker line). The authoring stage should offer the source file at native fidelity (offline syntax highlighting) and note the truncation when present.
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
- Body text frames map to `paragraph` blocks, or to a single `bullets` block when the frame has list levels (the paragraph indent level becomes the item `depth`). Grouped shapes are recursed into (depth-capped), so text, tables, and pictures inside groups are extracted in order.
- Slide tables map to `table` blocks; embedded pictures map to `image` blocks (base64, `origin: "shape-picture"`, `page` = the 1-based slide number).
- Native chart shapes map to `chart` blocks with `provenance: "native-chart"` and the chart's real categories and series values; the chart title (when present) becomes the block's `caption`. A chart whose data cannot be read lands in the coverage manifest's `skip_reasons`, never as silent loss.
- The slide's notes-slide text maps to a single `notes` block on that section.

### Word (.docx) and PDF (.pdf) -- present the report

- Heading-styled paragraphs (Word `Heading 1`/`Heading 2`, or detected headings in PDF - the page's largest-font short line near the top, falling back to the first short line) define section boundaries: each heading starts a new `section` whose `heading` is the heading text.
- Body paragraphs between headings map to `paragraph` blocks; list paragraphs map to `bullets` (with `depth` from the list level); tables map to `table` blocks; inline images map to `image` blocks (`origin: "inline-image"` for DOCX).
- Native DOCX chart parts (read from the OOXML package) map to `chart` blocks with `provenance: "native-chart"`.
- PDF visuals (v2): embedded raster images map to `image` blocks (`origin: "embedded-raster"`, `page` set, `caption` attached when a caption line sits directly below); vector-figure regions (plots, maps, diagrams drawn as vectors) are detected, rasterized via the optional local renderer, and map to `image` blocks (`origin: "rasterized-region"`); identical images repeated across 3+ pages (logos, footers) are kept once and counted in `coverage.skip_reasons` as `repeated-asset`.
- Scanned / image-only PDF pages (v2): detected pages emit OCR-recovered `paragraph` / `table` blocks (`provenance: "ocr"`, `ocr_confidence` set) when a local OCR engine is available, and ALWAYS emit a full-page `image` block (`origin: "scanned-page"`) for agent-vision reading, so no content is lost without OCR.
- A deck-exported PDF (landscape, low text density) sets `deck_like: true` on its source entry.
- The document title maps to the top-level `title` and to a leading `kind: "title"` section.
- A synthesized agenda is added as a `kind: "section-break"` (or `content`) section near the front, listing the section headings as a `bullets` block. This is what turns a flat report into "a presentation OF the report" and is generated by the extractor, not read from the source. Its `source_index` points at the source it summarizes.

### Excel (.xlsx) -- chart the data

- Each worksheet maps to one `section`, in workbook order, usually `kind: "data"`. The sheet name is the `heading`.
- A contiguous range with a label row/column and numeric body maps to a `chart` block with `provenance: "source-data"`: the label row becomes `categories`, each labeled numeric column (or row) becomes a series `{ name, values }`, and `chart_type_hint` is inferred (a small category count with one series leans `pie`/`doughnut`; multiple series or a time-like first column leans `line`; otherwise `bar`).
- Ranges that are not cleanly numeric map to `table` blocks instead, so no data is silently dropped.

### Source code and config (.py, .js, .ts, .go, .rs, .java, .sh, .sql, .json, .yaml, .toml, ...) -- present the file

- Each source-code or config file maps to one `section` whose `heading` is the repository-relative path and whose single block is a `code` block. `language` is inferred from the file extension (or a known basename such as `Dockerfile` / `Makefile`); `path` carries the repository-relative path.
- A file larger than the text-byte cap (`--max-text-bytes`) is TRUNCATED, not dropped: the `code` block's `text` ends with a clear truncation marker and `truncated` is `true`.
- The section `kind` is `content`.

### Markdown and plain text (.md, .markdown, .txt, .rst, .log) -- present the document

- Markdown is segmented into `section`s by ATX (`#`) and setext headings: the heading text becomes the section `heading`, body paragraphs become `paragraph` blocks, lists become `bullets` (with `depth` from the marker indent), fenced code becomes `code` blocks (language from the fence info string), pipe tables become `table` blocks, and image references to LOCAL files become `image` blocks (resolved relative to the Markdown file, through the base64 budget path). A remote image URL is not fetched; it is recorded as a caption note only.
- Plain text (`.txt`, `.rst`, `.log`) maps to one `section` of blank-line-separated `paragraph` blocks; `.rst` promotes underlined titles to the `heading` on a best-effort basis. The in-house Markdown / text parser is intentionally minimal (documented in the runbook); it is not a full CommonMark implementation.

### CSV / TSV (.csv, .tsv) -- chart or tabulate the data

- A CSV / TSV file maps to one `section` (`kind: "data"`, heading = the file stem or repository-relative path). The delimiter is sniffed (`.tsv` forces tab). The parsed grid goes through the SAME grid-to-block logic as Excel: a header row plus a numeric body becomes a `chart` block (`provenance: "source-data"`, inferred `chart_type_hint`); a non-numeric grid becomes a `table` block. A row / column cap guards pathological files (over-cap rows are dropped and counted in coverage).

### Standalone images (.png, .jpg, .jpeg, .gif, .webp, .svg) -- present the image

- An image supplied as its own input file maps to one `section` (`kind: "image"`) whose single block is an `image` block with `origin: "standalone-image"` (no `page`; `page_fraction` is null - there is no page geometry). Raster images go through the base64 budget / downscale path; `.svg` is embedded as `image/svg+xml` markup (not rasterized), bypassing the raster downscale path.

### Directory / repository input -- compile the project

- A directory argument is walked RECURSIVELY (see the runbook for the ignore list, the `.gitignore` best-effort matcher, the binary sniff, and the `--max-files` / `--max-text-bytes` caps). Each ingested file becomes its own source (with its class as `format`), so per-source attribution and the per-source coverage manifest work unchanged.
- The model gains a top-level `tree` (the ingested layout) and a leading `kind: "overview"` section. Body sections are ordered legibly: README / top-level docs first, then remaining Markdown / docs, then source code grouped by top-level directory (a `section-break` per top-level directory carrying its name), then data files and standalone images, then the document formats. The top-level `coverage.walk` object records what the walk excluded and why.

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
