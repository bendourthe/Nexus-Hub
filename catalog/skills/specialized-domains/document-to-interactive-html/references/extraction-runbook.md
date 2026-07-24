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
    - Slide tables become `table` blocks (the table's `first_row` flag decides whether row 0 is a header). Embedded pictures become base64 `image` blocks (`origin: "shape-picture"`, `page` = slide number). The notes-slide text becomes one `notes` block (hidden by default in the output).
    - Grouped shapes ARE recursed into (depth-capped at 8), so text, tables, and pictures inside groups extract in order.
    - Author-added overlay shapes drawn OVER a picture (a region rectangle or shaded zone, a callout label, a leader line) are captured as an `annotations` array on that image block, NOT as separate text blocks: a non-picture shape whose CENTER lies inside a picture and whose area is smaller than the picture attaches to that image with an image-relative `bbox` ([x, y, w, h], 0..1 within the picture's placed rectangle), its `text`, its solid `fill` / `line` colors, and its enclosing `group` name when grouped. This feeds the overlay-recreation path in `references/figure-reconstruction.md` (part 5). A shape BESIDE (not over) a picture stays normal content.
    - Native PowerPoint chart shapes become `chart` blocks with `provenance: "native-chart"`, the source's real categories and series values, a `chart_type_hint` mapped from the chart type, and the chart title as `caption`. An unreadable chart lands in `coverage.skip_reasons`, never as silent loss.
- Gotchas:
    - SmartArt and WordArt are not extracted as text.
    - A chart data point with an empty cache is recorded as `0.0` with a stderr warning; verify against the source when that warning fires.
    - Pictures placed as picture-filled placeholders (rather than picture shapes) are not extracted as images.
    - Overlay-annotation detection is geometric (center-inside plus smaller-than-picture), so a full-slide background picture with body text on top captures that text as annotations. Theme-colored (non-RGB) fills / lines are omitted from an annotation rather than guessed. Annotation capture is PPTX-only; flattened sources route through the agent-vision overlay path (see the PDF section and `references/figure-reconstruction.md`).

## Word (.docx)

- Library: `python-docx` (`pip install python-docx`).
- Mapping:
    - `Title`-styled text sets the document title (top-level `title` and the synthesized leading title section).
    - `Heading N`-styled paragraphs start new sections (`kind: "content"`), with the heading text as the section `heading`.
    - Body paragraphs become `paragraph` blocks; list paragraphs (a `w:numPr` numbering or a `List*` style) become `bullets` items, with the list level mapped to `depth`. Consecutive list items are merged into one `bullets` block.
    - Tables become `table` blocks (row 0 is treated as the header). Inline images are resolved by relationship id and become base64 `image` blocks (`origin: "inline-image"`) at their paragraph position.
    - Native Word chart parts are read directly from the OOXML package (the drawing's chart relationship id resolves to `word/charts/chart*.xml`, parsed with the standard library) and become `chart` blocks with `provenance: "native-chart"`. A malformed chart part degrades to a `coverage.skip_reasons` entry.
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

- Libraries:
    - `pdfplumber` (`pip install pdfplumber`), preferred for layout, tables, headings, captions, and figure-region detection. `pypdf` (`pip install pypdf`) is an automatic fallback for text + embedded-image extraction when `pdfplumber` is absent; if neither is installed the extractor prints the `pdfplumber` install hint and exits non-zero.
    - `pypdf` (optional alongside pdfplumber): supplies the decoded bytes of embedded raster images. Absent => embedded-image extraction is skipped with a warning and a `coverage.skip_reasons` entry; text and tables still extract.
    - `pypdfium2` (`pip install pypdfium2`, optional): the local renderer used to rasterize vector-figure regions and scanned pages. Absent => those visuals are skipped with ONE warning naming the affected pages; nothing else fails.
    - OCR engine (optional, for scanned pages): `rapidocr-onnxruntime` (`pip install rapidocr-onnxruntime`; pip-only, bundled detection + recognition, no system binary) preferred, or `pytesseract` when the Tesseract binary is already installed. Absent => scanned pages still ship as full-page image blocks for agent-vision reading, so no content is lost.
- Mapping:
    - Each page becomes one section. The heading is detected typographically (the page's largest-font short line in the top 45% of the page, when it beats the page's median font size); the first-short-line heuristic is the fallback, then `Page N`. The first promoted (non-`Page N`) heading becomes the document title.
    - Page text is split on blank lines into `paragraph` blocks; detected tables become `table` blocks.
    - Embedded raster images become base64 `image` blocks (`origin: "embedded-raster"`, `page` set). An identical image repeated on 3+ pages (a logo, a footer graphic) is kept once and skipped elsewhere with a `repeated-asset` coverage entry.
    - Vector-figure regions (plots, maps, diagrams drawn as vector strokes - the norm in PDFs exported from PowerPoint) are detected by clustering drawing objects into low-text-density bounding boxes, rasterized at 2x via `pypdfium2`, and emitted as `image` blocks (`origin: "rasterized-region"`).
    - A short caption line sitting directly below a figure (a "Figure N: ..." cue, or a short line under the figure's footprint) is attached as the block's `caption`.
    - Scanned / image-only pages (near-empty text layer, image-dominated area) take the two-tier path: tier A runs the local OCR engine over the rendered page and emits `paragraph` / `table` blocks with `provenance: "ocr"` and per-block `ocr_confidence`; tier B ALWAYS emits a full-page `image` block (`origin: "scanned-page"`) so the authoring agent can read and verify the page directly. Low-confidence OCR blocks are counted in `coverage.ocr_low_confidence` for mandatory verification.
    - A PDF whose pages are mostly landscape with low text density is tagged `deck_like: true` on its source entry (a PDF exported from slides; the mode auto-detect preserves page order as slide flow).
    - Every visual found / kept / skipped is counted in the model's per-source `coverage` manifest with reasons.
- Gotchas:
    - PDF has no reliable heading structure; the typographic heuristic is much better than first-short-line on deck exports but is still approximate on dense reports.
    - Multi-column PDFs may interleave columns in the extracted text order; complex layouts are not reflowed.
    - Figure images are placed after the page's text and tables, ordered by their vertical position; exact text/figure interleaving within a page is not reconstructed.
    - Caption text also remains inside the page's paragraph text (it is attached, not moved); the authoring stage should prefer the block `caption` and drop the duplicate line.
    - OCR table recovery is geometry-based (aligned multi-cell rows) and works best on well-separated columns; the `pytesseract` path recovers paragraphs only. The scanned-page image block plus the figure-reconstruction protocol's transcription pass are the accuracy backstop either way.
    - Author-added annotations on a PDF figure (region overlays, callout labels on a map) are BAKED into the page's pixels, so the extractor does NOT recover them as structured `annotations` metadata (unlike PPTX overlay shapes). The base figure ships as an `embedded-raster` or `rasterized-region` image, and the agent recreates its annotations from the rendered image via the overlay-recreation path in `references/figure-reconstruction.md` (part 5), under the confidence gate.

## Source code and config (universal ingestion)

- No third-party library: files are read with the standard library.
- Extensions map to a syntax-highlight `language` via an in-script table (`.py` -> `python`, `.ts` -> `typescript`, `.go` -> `go`, `.rs` -> `rust`, `.sh` -> `bash`, `.sql` -> `sql`, `.json`/`.yaml`/`.toml`/`.ini` -> the config language, and so on); known extensionless basenames (`Dockerfile`, `Makefile`, `CMakeLists.txt`, `Rakefile`, `Gemfile`) are recognized too.
- Each file becomes one `content` section whose `heading` is the repository-relative path and whose single `code` block carries the source, `language`, and `path`.
- A file larger than `--max-text-bytes` (default 300000) is TRUNCATED (not dropped): the `code` block ends with a `... [truncated at the text-byte cap] ...` marker and `truncated: true`.
- Gotchas: files are decoded as UTF-8 with a latin-1 `errors="replace"` fallback (a fallback is noted in `coverage.skip_reasons`); the walk skips files that sniff as binary; no secret redaction is performed, so do not point the walk at a repository holding plaintext secrets (dotfiles such as `.env` have no recognized extension and are not ingested, but a `secrets.yaml` would be).

## Markdown and plain text (universal ingestion)

- No third-party library: an intentionally-minimal in-house parser (not a full CommonMark implementation).
- Markdown (`.md`, `.markdown`, `.mdown`, `.mkd`): ATX (`#`) and setext headings start sections; blank-line-separated prose becomes `paragraph` blocks; `-`/`*`/`+`/ordered items become a `bullets` block (indent / 2 -> `depth`); fenced code (```` ``` ````/`~~~`) becomes a `code` block (language from the info string); pipe tables (a header row plus a `---` separator row) become `table` blocks; a standalone `![alt](path)` line becomes an `image` block when `path` is LOCAL (resolved relative to the Markdown file), and a remote `http(s)` image is recorded as a `[Image: ... (remote: ...)]` note, never fetched.
- Plain text (`.txt`, `.text`, `.rst`, `.log`): one section of blank-line-separated paragraphs; `.rst` promotes an underlined first-line title on a best-effort basis.
- Gotchas: nested list depth is approximated from leading whitespace (2 spaces per level); reference-style links, footnotes, and HTML blocks are passed through as prose; the parser is deliberately small, so complex Markdown may render as paragraphs rather than its richest form.

## CSV / TSV (universal ingestion)

- Library: the standard-library `csv` module.
- The delimiter is sniffed (a `.tsv` file forces tab). The parsed grid goes through the SAME grid-to-block logic as Excel: a header row plus a numeric body becomes a `chart` block (`provenance: "source-data"`, inferred `chart_type_hint`); a non-numeric grid becomes a `table` block. Numeric-looking cells (including thousands separators) are coerced to numbers before the chart / table decision.
- Caps: at most 2000 rows and 64 columns are read; an over-cap file is recorded in `coverage.skip_reasons` as `csv-cap`.

## Standalone images (universal ingestion)

- An image supplied as its own input file (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg`) becomes one `image` section with `origin: "standalone-image"` and no `page`.
- Raster images go through the base64 budget / Pillow downscale path (below); `.svg` is embedded as an `image/svg+xml` data URI (its markup, not a rasterization), bypassing the raster path.

## Directory / repository walk (universal ingestion)

- A directory argument is walked RECURSIVELY (`os.walk`), collecting only files whose extension / basename maps to a supported format. When the SOLE input is one directory, repository assembly runs (a synthesized `overview` section, a `tree`, README / docs first, code grouped by top-level directory, then data and images); otherwise a directory contributes its files to the normal multi-file merge.
- Excluded by default (each counted in `coverage.walk`): tooling / VCS directories (`.git`, `.hg`, `.svn`, `.idea`, `.vscode`, ...), dependency / build output (`node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `target`, `vendor`, `site-packages`, ...), lockfiles (`package-lock.json`, `poetry.lock`, `Cargo.lock`, ...), files whose bytes sniff as binary (NUL byte or a high non-text ratio in the first 4 KB) when their format is a text format, and everything a root `.gitignore` matches.
- `.gitignore` matching is BEST-EFFORT: it reads the walk root's `.gitignore`, supports leading-`/` anchoring, basename globs, and path globs via `fnmatch`, but does NOT implement negation (`!pattern`) or the full `**` semantics git uses. Treat it as a convenience, not a faithful git implementation.
- Caps: `--max-files` (default 400) bounds the total files ingested (extras are dropped, counted as `file_count_capped`); `--max-text-bytes` (default 300000) truncates large text / code files. A capped or trimmed walk prints one stderr summary; nothing is silently dropped.
- The `coverage.walk` object records `files_included`, `gitignored`, `binary_skipped`, `dirs_ignored`, `file_count_capped`, and a bounded `notes` list. The per-source `coverage` manifest still governs per-file visual reconciliation.

## Image handling and the base64 budget

- Images are carried inline as base64 `data:` URIs in `image` blocks so the final HTML is fully self-contained and works offline.
- The per-image budget defaults to 2,000,000 bytes and is tunable with `--max-image-bytes N`. Lower it to keep the output small for many-image decks; raise it to preserve full-resolution figures.
- When an image exceeds the budget, the extractor attempts a downscale via `Pillow` (`pip install Pillow`) to a JPEG within budget. `Pillow` is optional: if it is absent (or the image still cannot fit), the image is skipped with a warning to stderr, never an error - the rest of the extraction proceeds.

## Determinism

- Output ordering is fully deterministic: sources in input order, sections in source order, blocks in document order. A directory input is walked RECURSIVELY and its included files are sorted by repository-relative path, so re-running on the same tree yields byte-identical JSON.
- The extractor never injects non-ASCII characters of its own; source text is preserved as valid UTF-8 in the JSON output.
- Re-running the extractor on the same inputs produces byte-identical JSON.

## Multi-file behavior

- Inputs are processed in the order given on the command line. A folder argument expands to its supported files, walked recursively and sorted by repository-relative path (see the directory / repository walk section above); a single-directory input additionally triggers repository assembly.
- Each source contributes a labeled, contiguous run of sections; within a source, that source's own order is preserved.
- Every section carries a `source_index` pointing at its entry in the top-level `sources` manifest, so attribution survives the merge.
- A `section-break` is inserted at each source boundary (its heading is the source title), and a synthesized overview title section listing all sources is prepended. This is the "compile multiple sources into one presentation" behavior.

## Out of scope

- Video and audio EMBEDDED IN A SOURCE document. The extractor ignores media in any input format and never carries it into the output (source-embedded media would break the offline / size guarantee). This limit is the EXTRACTOR's only: output-side, license-free stock VIDEO is supported by the imagery stock tier via `scripts/fetch_stock_media.py` (Pexels-only, opt-in, consent-gated, base64-embedded within the media budget), NOT by the extractor - see "Tier 2 - license-free stock" in `references/interactive-features.md`.
- Full layout reflow of complex multi-column PDFs; column interleaving in text order is possible.
- Formerly out of scope, now implemented (v2): PDF embedded-image extraction, PDF vector-figure region capture, native PPTX/DOCX chart objects, and scanned-PDF reading via the two-tier local-OCR + agent-vision path (see the PDF section above).
