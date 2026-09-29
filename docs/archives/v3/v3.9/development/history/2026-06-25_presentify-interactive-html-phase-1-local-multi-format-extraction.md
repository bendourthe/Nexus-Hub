# Session History - v3.9.0 presentify-interactive-html Phase 1: Local multi-format extraction

**Date**: 2026-06-25
**Plan**: [`../../plans/presentify-interactive-html.md`](../../plans/presentify-interactive-html.md) Phase 1 (content-model schema + lazy-import extractor + extraction runbook + stabilization)
**Branch**: `develop`
**Outcome**: Complete. All four sub-tasks (1.1-1.4) done; Phase 1 exit checklist satisfied; quality gate GO. This is the first of four phases; the skill is intentionally not yet registered (no SKILL.md until Phase 3), so the release-readiness workflow was NOT triggered.

## Goal

Define a normalized content model and a local, lazy-import extractor that turns any single document or mix of documents (PDF, .docx, .xlsx, .pptx) into that model, preserving structure (sections, headings, prose, nested bullets, tables), chartable spreadsheet data, images, speaker notes, and per-source attribution + ordering for the multi-file case. Local-only parsing, zero network calls, no new outbound dependency forced on the catalog.

## What shipped

- **`catalog/skills/specialized-domains/document-to-interactive-html/references/content-model.md`** (new): the normalized "content model" schema - the single stable contract between extraction and the Phase 2 builder. Defines the top-level object (`schema_version`, `title`, `sources` manifest, ordered `sections`), the section object (`heading`, `subheading`, `kind` in {title, content, section-break, data, quote, image, appendix}, `source_index`, `blocks`), and the eight block kinds (paragraph, bullets with integer `depth`, table, image as base64 data URI, chart as typed data series, code, quote, notes). Specifies the per-format mapping (PPTX one-section-per-slide "preserve the flow"; DOCX/PDF heading-segmented "present the report" with a synthesized agenda; XLSX numeric-range-to-chart) and the multi-file merge (labeled run per source, section-break boundaries, synthesized overview). Forward-compat rule: unknown block types are ignored, not errors.
- **`catalog/skills/specialized-domains/document-to-interactive-html/scripts/extract_content.py`** (new, ~470 lines): the cross-platform extractor. Dispatches by file extension, expands a folder argument to its supported files (sorted, non-recursive), and emits deterministic content-model JSON to `--out`. Per-format extractors use `python-pptx`, `python-docx`, `openpyxl`, and `pdfplumber` (with a `pypdf` text-only fallback). Every parser is lazy-imported INSIDE the function that needs it; a missing required library prints `Error: <lib> not installed. Please run: pip install <lib>` to stderr and exits non-zero (no traceback) via a `SystemExit`-raising `_missing()` helper. Images are carried as base64 data URIs with a `--max-image-bytes` budget (default 2 MB), downscaled via optional Pillow or skipped-with-warning when over budget. All synthesis (title section, report agenda, multi-file boundaries + overview) is centralized in `build_model()` so the three input modes stay coherent. ruff-clean, type-hinted, no bare excepts, zero network imports.
- **`catalog/skills/specialized-domains/document-to-interactive-html/references/extraction-runbook.md`** (new): per-format coverage doc (library + `pip install` line, what maps to which block, gotchas) for PPTX/DOCX/XLSX/PDF, plus the image base64 budget, determinism guarantees, multi-file behavior, and the explicit v1 out-of-scope list (scanned-PDF OCR, video/audio, native pptx/docx charts, PDF images). This file is the Tier-3 reference SKILL.md will link to in Phase 3.

## Key decisions / troubleshooting

- **`SystemExit` vs `Exception` is the lazy-import contract.** Per-file extraction in `build_model()` is wrapped in `except Exception` so one corrupt file in a multi-file batch degrades to a warning instead of aborting the run. The missing-library handler raises `SystemExit` (a `BaseException`, not an `Exception`), so it is never swallowed by that guard and still exits non-zero with the documented `pip install` message - verified by a forced-`ImportError` subprocess test.
- **Synthesis centralized in `build_model()`, not the per-format extractors.** Each extractor returns only raw `(detected_title, sections)`. The title-section / report-agenda / multi-file-boundary synthesis lives in one place that can see the whole picture, so a single PPTX preserves its own title slide (no double title), a single report gets a synthesized title + agenda, and a multi-file set gets one overview + per-source section-breaks - without re-deriving the logic per format.
- **PDF heading bug found and fixed during 1.4.** The first `_pdf_page_section` split page text on blank lines first, then promoted the first chunk as a heading. The sample PDF returned `heading\nbody` with a single newline, so the whole page collapsed into one sub-80-char chunk and was promoted entirely to the heading, leaving zero paragraph blocks. Fixed to detect the heading from the first *line*, then paragraph-ize the remainder by blank lines. Re-ran: paragraphs captured. (`re` then became unused and was removed to keep ruff clean.)
- **PDF exercised the `pypdf` fallback for real.** `pdfplumber` is not installed on the dev host, so the PDF test ran the `pypdf` text-only fallback path end to end - confirming the documented degrade-not-crash behavior is real, not just theoretical.
- **No installer edit and no registry edit this phase.** Per-skill `scripts/` / `references/` subdirectories are auto-copied recursively by both installers (AGENTS.md "Distribution channels" row 1), so no `installer.{sh,ps1}` copy step is needed. With no SKILL.md yet, the skill is not counted (orphan audit scanned 256 skills, unchanged) and the three registries are untouched - registration is Phase 3's job.

## Verification (quality gate: GO)

- `make` is not on PATH (WN-v33-1), so gates were run via their documented equivalents.
- **Acceptance tests** (scratch fixtures: a 3-slide PPTX, a 2-page DOCX report, a 1-sheet XLSX, a 2-page PDF, plus a mixed PPTX+XLSX set): all 7 groups PASS - schema conformance for every model; PPTX slide order preserved (`Quarterly Review`, `Highlights`, `Metrics`) with the first slide `kind: title`, speaker notes + table + base64 image captured; DOCX synthesized title + agenda, headings became sections, inline image + bullet list captured; XLSX numeric range became a `chart` block (`categories` NA/EMEA/APAC, series Q1/Q2); PDF produced sections + paragraphs via the pypdf fallback; multi-file merged in order with correct `source_index` attribution and per-source section-breaks; re-run produced a byte-identical model (determinism); a forced missing-`pptx` import exited non-zero with the `pip install python-pptx` message and no traceback.
- **CLI**: `--help` renders; an end-to-end mixed run wrote valid JSON (2 sources, 7 sections); a no-supported-input run warned and exited 2 cleanly (no traceback).
- **ruff** (`python -m ruff check`): All checks passed. **py_compile**: OK.
- **Project validators**: orphan-bundle audit (`--bundles-only`) PASS (0 errors); `validate_no_personal_paths.py`, `validate_unicode_safety.py`, `scan_supply_chain_iocs.py`, `validate_workflow_security.py` all exit 0 with no mention of the new skill. The pre-existing `--verbose` 250-char description "FAIL" set is a repo baseline on other skills and is not what `make validate` gates on.
- **No network**: grep for `socket`/`urllib`/`http`/`requests`/`urlopen`/`httpx` in the extractor returns nothing.
- **ASCII + no personal paths**: all three committed files are ASCII-only and free of personal-path tokens.

## Files changed

- `catalog/skills/specialized-domains/document-to-interactive-html/references/content-model.md` (created)
- `catalog/skills/specialized-domains/document-to-interactive-html/scripts/extract_content.py` (created)
- `catalog/skills/specialized-domains/document-to-interactive-html/references/extraction-runbook.md` (created)
- `docs/v3/v3.9/known-gaps.md` (Phase 1 deferrals DF-v39-presentify-1..4 + notes added; counts updated)
- `docs/v3/v3.9/plans/presentify-interactive-html.md` (Phase 1 exit checklist checked off)
- `docs/archive/v3/v3.9/development/history/2026-06-25_presentify-interactive-html-phase-1-local-multi-format-extraction.md` (this file)

## Next

Phase 2 (Self-contained interactive HTML template + builder): author `assets/presentation-template.html` (offline, self-contained, nav/outline/progress/fullscreen/keyboard/reduced-motion) and `assets/theme.json`, implement `scripts/build_presentation.py` (content model -> one offline `.html` with inline base64 images and inline SVG/canvas charts), and write `references/interactive-features.md` (feature catalog + the hallmark-design enrichment pass + the three input modes). Run with `/implement phase 2 of presentify-interactive-html`. The DEVLOG and CHANGELOG entries remain deferred to the `/update release` step (consistent with the adoption-plan phases in this version); registration of the skill is deferred to Phase 3.
