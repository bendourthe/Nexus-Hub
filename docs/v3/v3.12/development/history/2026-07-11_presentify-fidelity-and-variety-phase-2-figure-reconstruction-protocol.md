# Session History - presentify-fidelity-and-variety Phase 2: Faithful figure reconstruction protocol (LLM-native)

**Date**: 2026-07-11
**Plan**: `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md`
**Phase**: 2 of 6 (non-final)
**Model**: Fable 5, high effort (matched the plan's recommendation; no routing delta)

## What was done

- **2.1 Protocol reference** (`references/figure-reconstruction.md`, new): seven parts - classification taxonomy with downstream handling table; the read-the-figure worksheet template (copied verbatim into runs, embedded as an HTML comment beside each reconstruction); six fidelity cross-checks; the three-tier confidence gate (high / medium / low with per-tier output contracts and the all-tiers fabrication prohibition); map/diagram label-faithful-only rebuild rules plus photo/screenshot/decorative handling; the model round-trip (classifications + reconstructed chart blocks written back; nothing deleted); the scanned-page transcription/OCR-verification pass (verify low-confidence blocks, verify ALL numerics regardless of confidence, transcribe gaps as `agent-read`, route on-page figures into classification). Ends with the failure-mode list the protocol prevents.
- **2.2 Wiring**: SKILL.md pipeline diagram gained the reconstruction stage; new mandatory Instructions Step 3 (steps renumbered 3-7 -> 4-8, internal step references fixed); three new Common Rationalizations rows (embed-as-is, eyeball-the-bars, approximate-a-nicer-version); four new binary Verification items (classification coverage, worksheet/provenance/confidence/toggle, low-tier handling, OCR numeric verification); Bundled Resources lists the new reference. `catalog/commands/presentify.md` delegation summary now names the classify-and-reconstruct stage. SKILL.md is 173 lines (norm <= 500).
- **2.3 Protocol exercised on the Phase 1 fixtures** (agent vision over decoded figure images, evidence below).

## Test results (plan 2.3 confirmations)

1. **Classification**: every deck.pdf image block classified - logo `decorative` (skip entry recorded), page-2 region `chart`, page-3 region `map`, page-4 raster `photo`; scanned pages handled by part 7 instead. PASS.
2. **Worksheet vs ground truth**: page-2 chart worksheet (bar; categorical Q1-Q4; y ticks 0/50/100/150, linear; single series; precision "nearest 5 against gridlines") read 120/135/150/170 - EXACT match to fixture ground truth; cross-checks passed (extrema, count, containment with the Q4-above-last-tick interpolation noted); graded `medium` (interpolated values dominate), reconstruction emitted with provenance/confidence/source_image/axis per schema v2. PASS.
3. **Degraded figure**: the chart downscaled to 110px and re-upscaled (ticks/labels illegible blurs) landed in `low` - enhanced original, NO reconstruction. PASS.
4. **Map**: unlabeled outline + four site markers - simple structure with zero labels to lose, SVG-rebuild eligible per part 5 (enhanced original equally valid); no lossy redraw performed. PASS.
5. **Schema round-trip**: enrichment applied to the fixture models (`models/deck_pdf_enriched.json`, `models/scanned_enriched.json`, gitignored artifacts); assertions confirm 1 reconstructed chart with ground-truth values, 0 unclassified images, and the enriched v2 model builds with `build_presentation.py` (exit 0). PASS.
6. **Scanned transcription**: 3 OCR corrections applied against the page images ("QUARTERLYUPDATE" -> "QUARTERLY UPDATE"; the merged, space-squeezed two-paragraph block split and corrected; "REVENUEFIGURE" -> "REVENUE FIGURE"; all re-tagged `agent-read`), table numerics 42/37 verified against pixels, and page 2's axis-less "illustrative" bar figure was DECLINED for reconstruction (0 fabricated charts - reconstructing it would have invented numbers). PASS.

## Troubleshooting (1 iteration)

- **IMPL fix (cross-phase)**: exercising the protocol exposed a Phase 1 defect - `_pdf_figure_regions` crops were tight to the drawing objects, so axis tick labels (0/50/100/150, Q1-Q4) fell OUTSIDE the rasterized chart crop, making faithful reading impossible. Fixed in `extract_content.py` with `_expand_region_with_labels` (single-pass, bounded: grow the crop to include text within 28pt of the original bbox, plus a 6pt margin; caption matching still uses the original bbox). Full Phase 1 verifier re-ran 45/45 green after the fix; ruff clean.

## Deviations

- The extractor crop fix above is Phase 1 surface touched during Phase 2 - a defect fix required by this phase's acceptance criteria (worksheets need readable ticks), not scope creep. No other deviations.

## Known-gaps delta

- No new gaps. Ledger header updated (Phase 2 complete; crop-fix note). DF-1/2/3, WN-1/2, MT-1 unchanged.

## Next steps

- Phase 3: site-wide interaction layer (catalog + five-point minimum interaction budget in `references/interactive-features.md`, enforced in SKILL.md verification and the visual-QA loop).
