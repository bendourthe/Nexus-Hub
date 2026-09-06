# Phase 5 worked example - presentify fidelity + same-preset divergence (v3.12.0)

The end-to-end proof for `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md` Phase 5: the full upgraded presentify flow run TWICE on the PDF-from-PowerPoint fixture with the SAME preset (`technical`), plus the scanned-fixture run (the Phase 3 budget demo, extended with its coverage reconciliation).

## Files

- `design-history.json` - the shared entropy history; both briefs were rolled and committed against it, so run B was mechanically pushed away from run A.
- `brief-a.json` / `brief-b.json` - the two committed technical-preset briefs. A: light teal / duotone-graphic / grotesk-editorial / bento-mosaic / minimal-fade / sticky-figure-scrollytelling. B: dark cyan-slate / high-contrast-editorial / mono-technical / offset-column-rhythm / crisp-instant / filterable-grid. They share 0 of the {hue family, layout signature, type voice} triple.
- `build_worked_example.py` - the committed builder that authors both runs from the enriched fixture model (`../fixtures/models/deck_pdf_enriched.json`; regenerate via the fixtures kit if missing). `?static=1` pre-reveals content for headless screenshots (QA hook only).
- `run-a.html` / `run-b.html` - the two outputs (committed evidence, v3.9 precedent). Each carries: the reconstructed Revenue chart (canvas; wheel y-zoom, y-range inputs, legend toggle, hover readout, reset) with the medium-confidence provenance badge, the FIGURE WORKSHEET comment (readings 120/135/150/170, nearest 5), and the original figure alongside + in the pan/zoom lightbox; the map and photo as lightboxed originals; the decorative-logo skip; the five-point interaction budget; the DESIGN RECORD comment with the roll's seed; and the COVERAGE RECONCILIATION comment (verdict: ACCOUNTED - 0 unaccounted).
- `run-a.png` / `run-b.png` / `*-mobile.png` - headless Edge renders (desktop 1400px, mobile 480px) used for the visual-QA pass and the side-by-side divergence proof.
- `verify_worked_example.py` - the structural verification (fidelity gates, budget, divergence, evidence presence).

## Reconciliation listing (both runs; embedded in each HTML)

```text
COVERAGE RECONCILIATION - deck.pdf
manifest: images found 8 / kept 4 / skipped 4; native charts 0;
          vector regions rasterized 2 / skipped 0; scanned pages 0
- [skipped]       image page 1 "logo" - decorative (repeated-asset: on 5 pages, kept once)
- [reconstructed] chart from image page 2 "Figure 1: Revenue by quarter (USD millions)"
                  (confidence medium, worksheet adjacent, view-original + original alongside)
- [rendered]      image page 3 map (enhanced original, lightbox)
- [rendered]      image page 4 photo (lightbox)
verdict: ACCOUNTED - 0 unaccounted
```

The scanned-fixture run's reconciliation (2 scanned pages OCR'd + verified, table 42/37 confirmed, page-2 illustrative figure DECLINED for reconstruction) is embedded in `../fixtures/models/budget-demo.html`, built by `../fixtures/budget_demo.py`.

## Regenerate

```bash
cd ../fixtures && python gen_fixtures.py && python verify_phase1.py && python enrich_models.py
cd ../worked-example && python build_worked_example.py && python verify_worked_example.py
```
