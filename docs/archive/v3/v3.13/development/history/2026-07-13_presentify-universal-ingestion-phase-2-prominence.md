# Session History -- presentify universal ingestion, Phase 2 (image prominence)

**Date**: 2026-07-13
**Version**: v3.13.0
**Plan**: `docs/v3/v3.13/plans/v3.13.0-presentify-universal-ingestion.md`
**Phase**: 2 of 5 -- Image prominence preservation
**Branch**: `feat/presentify-robustness` (off `develop`)

## Goal

Stop the output from flattening a source's dominant visuals into a uniform thumbnail grid. Give the authoring stage objective prominence signals from the extractor, and a binding rule that keeps a hero image a hero at native resolution.

## What was built

### Extractor prominence signals (`scripts/extract_content.py`)

- `_image_dimensions(blob)`: native `(width, height)` via Pillow, computed from the ORIGINAL bytes (before any budget downscale) so the signal reflects source resolution; `(None, None)` when Pillow is absent or the bytes will not decode (e.g. SVG).
- `_image_block(...)` extended with a `page_fraction` parameter; it now sets `width` / `height` (when decodable) and `page_fraction` (rounded to 3 dp, clamped to [0, 1]) on every image block.
- Callers compute `page_fraction` where source geometry exists:
    - PPTX pictures: `shape.width * shape.height / (slide_width * slide_height)` (slide area computed once per deck).
    - PDF embedded rasters: pdfplumber image bbox area / page area (when the bbox is known).
    - PDF rasterized regions: region bbox area / page area.
    - DOCX inline, Markdown-inline, standalone image files, and scanned-page renders: `page_fraction` absent (no reliable page geometry); native `width` / `height` still populate for rasters.

### Content model (`references/content-model.md`)

- Documented `width`, `height`, and `page_fraction` as additive v3 optional fields on `image` blocks, including which formats populate `page_fraction` and how the authoring stage uses them.

### Authoring rule (`references/interactive-features.md` + `SKILL.md`)

- New "Prominence preservation" subsection: rank a section's visuals by `page_fraction` (fall back to `width * height`, then section role); a dominant visual (`page_fraction >= 0.5`, or the sole / primary visual, or markedly larger than siblings) renders as a hero (full-width band or wide column); only genuinely-secondary visuals become a legible gallery; never flatten a hero; native resolution end to end (the lightbox shows the same full-resolution `data_uri`). The failure mode named explicitly: the "contact sheet".
- SKILL.md: a prominence bullet in the authoring step, a "tidy uniform thumbnail grid" rationalization row, and a binary Verification item.

## Verification

- Sink unit-check of `_image_block`: `page_fraction` rounds to 3 dp, clamps to [0, 1], is absent when `None`; SVG block carries no `width` / `height`.
- Fixture (`mixed-repo`): `pixel.png` -> `width`/`height` = 1x1; `logo.svg` and the README inline SVG -> null dims; standalone `page_fraction` null (correct, no page geometry).
- Determinism: two runs byte-identical (`cmp`).
- `python -m ruff check`: all checks passed. `py_compile`: OK.
- SKILL.md body: 188 lines (within the 500 norm). Edited docs ASCII-verified. Bundle audit: 0 errors.

## Notes / limitations

- The PDF/PPTX `page_fraction` geometry path was validated by code + the sink unit-check, not end to end on a real deck, because `pdfplumber` is not installed on this dev host (the PDF path falls back to `pypdf`, which has no bbox geometry). Full end-to-end prominence rendering on a real deck-PDF is part of the Phase 5 worked example (which requires `pdfplumber` / `python-pptx` and a headless browser).
- The full-repo `validate_unicode_safety.py` / `validate_no_personal_paths.py` scans time out on this host; edited files are directly ASCII-verified and Phase 1 established the repo-wide 0-error baseline.

## Next

Phase 3 -- spacing / density discipline (no dead vertical space) + output-aspect control (`--layout` flag + a full-width / standard / portrait / other menu asked like the style menu).
