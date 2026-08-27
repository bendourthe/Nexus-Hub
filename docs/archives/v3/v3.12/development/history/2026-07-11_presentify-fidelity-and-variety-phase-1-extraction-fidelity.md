# Session History - presentify-fidelity-and-variety Phase 1: Extraction fidelity (extractor + content model v2)

**Date**: 2026-07-11
**Plan**: `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md`
**Phase**: 1 of 6 (non-final)
**Model**: Fable 5, high effort (matched the plan's recommendation; no routing delta)

## What was done

- **1.1 Content model v2** (`references/content-model.md`): documented the additive-only v2 fields - image `caption`/`page`/`origin`/`classification`; chart `provenance`/`confidence`/`source_image`/`axis`/`caption`; paragraph/table `provenance` (`text-layer`/`ocr`/`agent-read`) + `ocr_confidence`; source `deck_like`; top-level `coverage` manifest (`{"per_source": [...]}`) - plus the explicit compatibility rule (v1 consumers ignore unknown fields; consumers must not reject higher versions) and per-format mapping updates. Example bumped to `schema_version: 2`.
- **1.2 PDF visuals** (`scripts/extract_content.py`, rewritten): embedded raster extraction (pypdf bytes + pdfplumber bboxes, magic-byte MIME sniffing), content-hash dedup of images repeated on 3+ pages (kept once, aggregated `repeated-asset` reason, per-instance skip counts), vector-figure region detection (drawing-object clustering with padding merge, backdrop/table/raster-overlap/text-density filters, per-page cap), rasterization at 2x via optional `pypdfium2` (single aggregated warning + pip hint when absent), caption pairing (cue-first regex, overlap + gap window, axis-tick-row filter).
- **1.3 Native charts + groups**: PPTX group recursion (depth-capped 8); native PPTX chart extraction via python-pptx (real categories/series, chart-type mapping, title as caption, None-cache warning); native DOCX chart parts parsed from OOXML with stdlib ElementTree (idx-sorted point caches); unreadable charts land in `coverage.skip_reasons`, never silent.
- **1.4 Deck-PDF sectioning**: typographic heading promotion (largest-font short line in the top 45% beating 1.15x page median; fallback preserved), heading line removed from body text, `deck_like` source tag (>= 80% landscape pages + < 800 avg chars/page). Runbook PDF section rewritten; out-of-scope list updated (media stays out; images/charts/OCR moved to implemented).
- **1.5 Scanned-page two-tier path**: detection (near-empty text layer + image-dominated area, boilerplate tolerance), tier A local OCR (`rapidocr-onnxruntime` preferred / `pytesseract` accepted; reading-order geometry grouping; aligned-row table heuristic; per-block `ocr_confidence` with a 0.80 low-confidence counter), tier B always-on full-page `scanned-page` image block (renderer preferred, dominant embedded raster fallback), `ocr_pages`/`agent_read_pages` accounting.
- **Builder compat**: `build_presentation.py` accepts schema_version 1 and 2 (was: v1 only - would have rejected every new model).
- **1.6 Fixtures + validation**: committed fixture kit at `docs/v3/v3.12/development/fixtures/` (generator, verifier, README, .gitignore; binaries gitignored per the v3.9 worked-example pattern). Five synthetic fixtures with ground truth; `verify_phase1.py` = 45 binary checks.

## Test results

- Fixture verifier: **45/45 PASS** (one iteration: the caption window was widened 28pt -> 44pt and an axis-tick-row filter added after the tick-label line beat the "Figure 1:" caption on the first run).
- Ruff: check clean on all touched Python; extractor + fixture scripts ruff-format-normalized.
- Repo validators: bundle audit 0 errors (1 pre-existing unrelated warning), unicode-safety 0 errors, personal-paths / supply-chain / workflow-security / solution-frontmatter / version-sync / base-parity all exit 0; compression accuracy gate PASSED.
- Pytest sweep: nexus-skill-server 43, nexus-code-search 200, nexus-web-fetch 29, nexus-skill-scanner 87 all pass. Failures elsewhere (1 compressor, 5 repo installer/session-query, 99 bash-invoking hook tests) **reproduce identically on clean HEAD with the phase stashed** - pre-existing host/environment issues (bash-on-Windows family), recorded as WN-1 in `docs/v3/v3.12/known-gaps.md`; CI authoritative.

## Deviations

- `# DEVIATION` (scope pull-forward): two one-line truth-fixes taken from Phase 2's doc scope - the SKILL.md "When NOT to use" bullet and the presentify command's out-of-scope note - because Phase 1's extractor made their v1 claims false. The full SKILL.md protocol wiring remains Phase 2 work.
- `ruff format` normalization of `build_presentation.py` deliberately NOT applied (pre-existing formatting; only the schema-version block was edited) - recorded as WN-2 for the Phase 6 refactor pass.

## Known-gaps delta

- Added `docs/v3/v3.12/known-gaps.md`: DF-1 (approximate text/figure interleaving), DF-2 (caption duplicated in body text), DF-3 (geometry-based OCR tables; pytesseract paragraphs-only), WN-1 (pre-existing local test failures; CI authoritative), WN-2 (builder ruff-format), MT-1 (no pytest suite for the extractor; fixture verifier is the gate - Phase 6.3 decides CI promotion).

## Environment notes

- Installed locally for validation: python-pptx, openpyxl, pdfplumber, pypdf, pypdfium2, reportlab, rapidocr-onnxruntime (all lazy-imported by the extractor; none are hard requirements).
- Degradation paths tested via import blocking (`sys.modules[name] = None`), not uninstalls: no-OCR, no-renderer, and no-PDF-parser runs all behave per contract.

## Next steps

- Phase 2: author `references/figure-reconstruction.md` (classification, read-the-figure worksheet, cross-checks, confidence gate, scanned-page transcription/verification) and wire it into SKILL.md as a mandatory step.
- Phase 5 will reconcile the coverage manifest against authored output end-to-end; Phase 6 reconciles DF-v39-presentify-1/-2/-3 as resolved in the v3.9 ledger and revisits WN-2/MT-1.
