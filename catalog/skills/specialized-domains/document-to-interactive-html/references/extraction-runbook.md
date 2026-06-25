# Extraction Runbook

This runbook documents what `scripts/extract_content.py` captures (and what it does not) for each supported source format, the libraries it uses, the image budget, the determinism guarantees, and the multi-file behavior. It is the per-format reference the SKILL.md body links to instead of inlining; pair it with `references/content-model.md`, which defines the target schema.

The extractor is local-only and makes no network calls. Every parser is lazy-imported inside the function that needs it, so you install only the libraries your inputs require, and a missing library for one format never blocks another. A missing required library prints `Error: <lib> not installed. Please run: pip install <lib>` to stderr and exits non-zero (no traceback).

## PowerPoint (.pptx)

- Library: `python-pptx` (`pip install python-pptx`).
- Mapping:
    - One slide maps to exactly one section, in slide order. Slide order is preserved end to end, which is the "follows the same flow" guarantee for the single-deck mode.
    - The slide title placeholder becomes the section `heading`; a subtitle placeholder becomes `subheading`.
    - The first slide is `kind: "title"`; a title-only divider slide is `kind: "section-break"`; the rest are `kind: "content"`.
    - A body text frame with a single top-level paragraph becomes a `paragraph` block; a multi-paragraph or indented text frame becomes a `bullets` block, with each paragraph's indent level mapped to the item `depth`.
    - Slide tables become `table` blocks (the table's `first_row` flag decides whether row 0 is a header). Embedded pictures become base64 `image` blocks. The notes-slide text becomes one `notes` block (hidden by default in the output).
- Gotchas:
    - Grouped shapes are not recursed into; text inside a group may be missed. Ungroup in the source if that text matters.
    - Native PowerPoint chart shapes are not extracted in v1 (see out-of-scope below); deliver chartable data via a spreadsheet input instead.
    - SmartArt and WordArt are not extracted as text.

## Word (.docx)

- Library: `python-docx` (`pip install python-docx`).
- Mapping:
    - `Title`-styled text sets the document title (top-level `title` and the synthesized leading title section).
    - `Heading N`-styled paragraphs start new sections (`kind: "content"`), with the heading text as the section `heading`.
    - Body paragraphs become `paragraph` blocks; list paragraphs (a `w:numPr` numbering or a `List*` style) become `bullets` items, with the list level mapped to `depth`. Consecutive list items are merged into one `bullets` block.
    - Tables become `table` blocks (row 0 is treated as the header). Inline images are resolved by relationship id and become base64 `image` blocks at their paragraph position.
    - Content that appears before the first heading is collected into an implicit `Overview` section so nothing is dropped.
    - When the document has two or more content sections, a synthesized `Agenda` section (`kind: "section-break"`) listing the section headings is inserted near the front. This is what turns a flat report into "a presentation OF the report".
- Gotchas:
    - Text inside text boxes, headers, and footers is not extracted (only the main document body).
    - Linked (not embedded) images are skipped because their bytes are not in the file.
    - Heading detection relies on Word heading styles; a document that fakes headings with bold body text will not be segmented (it lands in one `Overview` section).

## Excel (.xlsx)

- Library: `openpyxl` (`pip install openpyxl`).
- Mapping:
    - Each worksheet becomes one section (`kind: "data"`), in workbook order, with the sheet name as the `heading`.
    - The used range is trimmed of empty rows/columns. If the trimmed grid has a header row and a numeric body, it becomes a `chart` block: the first column is `categories`, each fully numeric column is a series, and a `chart_type_hint` is inferred (one series with up to 6 categories leans `pie`; more than 12 categories leans `line`; otherwise `bar`).
    - A range that is not cleanly numeric becomes a `table` block instead, so no data is silently dropped.
- Gotchas:
    - The workbook is opened with `data_only=True`, so formula cells contribute their last cached value. A file saved by a tool that did not cache values (some headless writers) yields `None` for formulas; open and save once in Excel/LibreOffice to populate the cache.
    - A series column must be entirely numeric to be charted; a single stray text cell demotes that column out of the series. Mixed sheets fall back to a table.
    - Only one contiguous grid per sheet is interpreted; a sheet holding several separate tables is treated as one grid. Split multi-table sheets across worksheets for clean charts.
    - Merged cells report their value only in the top-left cell; other covered cells read as empty.

## PDF (.pdf)

- Library: `pdfplumber` (`pip install pdfplumber`), preferred for layout and table detection. `pypdf` (`pip install pypdf`) is an automatic fallback for text-only extraction when `pdfplumber` is absent; if neither is installed the extractor prints the `pdfplumber` install hint and exits non-zero.
- Mapping:
    - Each page becomes one section. The page's first short line (<= 80 characters) is promoted to the section `heading`; otherwise the heading is `Page N`.
    - Page text is split on blank lines into `paragraph` blocks. With `pdfplumber`, detected tables become `table` blocks.
    - The first promoted (non-`Page N`) heading becomes the document title.
- Gotchas:
    - PDF has no reliable heading structure, so the short-first-line heuristic can mis-promote a body line or miss a real heading. Treat PDF segmentation as approximate.
    - Multi-column PDFs may interleave columns in the extracted text order; complex layouts are not reflowed.
    - PDF image extraction is out of scope for v1 (see below); the value from a PDF is its text and tables.
    - A scanned (image-only) PDF yields little or no text because there is no text layer.

## Image handling and the base64 budget

- Images are carried inline as base64 `data:` URIs in `image` blocks so the final HTML is fully self-contained and works offline.
- The per-image budget defaults to 2,000,000 bytes and is tunable with `--max-image-bytes N`. Lower it to keep the output small for many-image decks; raise it to preserve full-resolution figures.
- When an image exceeds the budget, the extractor attempts a downscale via `Pillow` (`pip install Pillow`) to a JPEG within budget. `Pillow` is optional: if it is absent (or the image still cannot fit), the image is skipped with a warning to stderr, never an error - the rest of the extraction proceeds.

## Determinism

- Output ordering is fully deterministic: sources in input order, sections in source order, blocks in document order. Folder inputs are expanded to their supported files sorted by name (non-recursive).
- The extractor never injects non-ASCII characters of its own; source text is preserved as valid UTF-8 in the JSON output.
- Re-running the extractor on the same inputs produces byte-identical JSON.

## Multi-file behavior

- Inputs are processed in the order given on the command line. A folder argument expands to its supported files sorted by name.
- Each source contributes a labeled, contiguous run of sections; within a source, that source's own order is preserved.
- Every section carries a `source_index` pointing at its entry in the top-level `sources` manifest, so attribution survives the merge.
- A `section-break` is inserted at each source boundary (its heading is the source title), and a synthesized overview title section listing all sources is prepended. This is the "compile multiple sources into one presentation" behavior.

## Out of scope for v1

- Scanned-PDF / image-only PDF OCR. There is no text recognition; a PDF with no text layer yields no text. Run OCR upstream if you need it.
- Video and audio embedding. Media in any source format is ignored.
- Native PowerPoint and Word chart objects. Chartable data is sourced from spreadsheet (.xlsx) inputs, which map cleanly to `chart` blocks.
- PDF image extraction. PDF contributes text and tables only.
