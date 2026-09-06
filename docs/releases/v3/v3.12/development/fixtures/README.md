# Phase 1 fixtures - presentify extraction fidelity (v3.12.0)

Fixture kit for Phase 1 of `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md`. It replays the failure case that motivated the plan (a PDF exported from PowerPoint whose photos, maps, and vector figures were dropped) plus the native-chart, grouped-shape, scanned-PDF, and regression cases.

## Files

- `gen_fixtures.py` - generates every fixture into `inputs/` (gitignored): `deck.pdf` (landscape PDF-from-slides proxy with a vector bar chart, a vector map, a photo, a repeated logo, and captions), `deck.pptx` (grouped shape + native chart + picture + table + notes), `report.docx` (headings, list, table, inline image, and an injected native chart part), `data.xlsx` (numeric range), and `scanned.pdf` (image-only pages with known text, a table, and a figure).
- `verify_phase1.py` - runs `extract_content.py` over the fixtures into `models/` (gitignored) and asserts the Phase 1 acceptance criteria: visual coverage, native-chart values, captions, repeated-asset dedup, deck-like detection, scanned-page OCR (tier A) and agent-vision fallback (tier B), graceful degradation with blocked optional libraries, determinism, and builder v2 compatibility.
- `enrich_models.py` - replays the Phase 2 protocol round-trip deterministically (classifications, the ground-truth chart reconstruction, the scanned fixture's OCR corrections) so `models/*_enriched.json` - the inputs to the budget demo and the worked example - regenerate from the kit alone.
- `budget_demo.py` / `verify_budget_demo.py` - the Phase 3 chart-free interaction-budget demo (built from `scanned_enriched.json`) and its 11-check structural verification; the demo also carries the scanned run's coverage reconciliation.
- `verify_design_seed.py` - the Phase 4 design-entropy engine verification (divergence rule, seeding, history cap/recovery, preset subsets, attractor guard).

## Usage

```bash
python gen_fixtures.py
python verify_phase1.py
python enrich_models.py
python budget_demo.py && python verify_budget_demo.py
python verify_design_seed.py
```

Requires: python-pptx, python-docx, openpyxl, pdfplumber, pypdf, pypdfium2, Pillow, reportlab, and (for the OCR tier) rapidocr-onnxruntime. `verify_phase1.py` prints one `PASS`/`FAIL` line per check and exits non-zero on any failure.
