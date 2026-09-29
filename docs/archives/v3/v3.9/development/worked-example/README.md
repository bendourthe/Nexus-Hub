# /presentify worked example (v3.9.0 Phase 4 verification evidence)

This directory is the Phase 4 worked example for the `/presentify` command and the `document-to-interactive-html` skill. It proves the end-to-end flow on representative inputs and is kept OUT of the distributed skill bundle (demo inputs and outputs are not catalog content).

The committed artifacts are the two output decks plus the scripts that regenerate everything:

- [`sample-deck.html`](sample-deck.html) - the single-PowerPoint "preserve the flow" mode.
- [`sample-report.html`](sample-report.html) - the single-report "present the report" mode.
- [`make_fixtures.py`](make_fixtures.py) - generates the two sample source documents.
- [`enrich.py`](enrich.py) - applies the enrichment pass (promotes a clean numeric table to the right chart type).

The sample binaries (`inputs/`) and intermediate content models (`models/`) are git-ignored because they are regenerable. Reproduce the full run with the commands below.

## Reproduce

Run from this directory. `SKILL` points at the installed skill bundle.

```bash
SKILL=../../../../catalog/skills/specialized-domains/document-to-interactive-html

# 1. Generate the sample inputs (a 5-slide deck and a 4-section report).
python make_fixtures.py

# 2. Extract each source into the normalized content model.
python "$SKILL/scripts/extract_content.py" inputs/sample-deck.pptx   -o models/deck.model.json
python "$SKILL/scripts/extract_content.py" inputs/sample-report.docx -o models/report.model.json

# 3. Enrichment pass: promote the numeric tables to charts (the agent's judgment, scripted for reproducibility).
python enrich.py models/deck.model.json   -o models/deck.enriched.json   --chart "Revenue by Region=bar"  --subtitle "FY26 Q3 - Operations and Growth"
python enrich.py models/report.model.json -o models/report.enriched.json --chart "Findings=line"

# 4. Build the two self-contained, offline decks.
python "$SKILL/scripts/build_presentation.py" models/deck.enriched.json   -o sample-deck.html
python "$SKILL/scripts/build_presentation.py" models/report.enriched.json -o sample-report.html
```

## What each mode demonstrates

### Single deck -- preserve the flow (`sample-deck.html`)

The source is a 5-slide PowerPoint (Quarterly Business Review). The output keeps the original slide order exactly (Title -> Agenda -> Revenue by Region -> Key Highlights -> Next Steps), so it "follows the same flow", but it is now an interactive HTML deck: keyboard and on-screen navigation, an auto-built outline, a progress bar, fullscreen, and reduced-motion-guarded transitions. The embedded slide image is carried inline as a base64 data URI, and the speaker notes are preserved (hidden by default). The enrichment pass promoted the same-unit "Revenue by Region" table (Q2 vs Q3 by region) into a grouped bar chart.

### Single report -- present the report (`sample-report.html`)

The source is a 4-section Word report (Operational Readiness Report). The extractor synthesized a leading title section and an Agenda section-break that lists the report's headings, turning a flat document into a paced presentation OF the report (Title -> Agenda -> Executive Summary -> Findings -> Recommendations -> Conclusion). The enrichment pass promoted the same-unit, time-series "incidents by quarter" table into a line chart. The mixed-unit reliability metrics were intentionally NOT charted (a single chart over incompatible units would mislead), which is the "pick the right chart for the data shape" discipline from `references/interactive-features.md`.

## Verification results

Both decks were verified programmatically (see the Phase 4 session history for the full run):

- **Offline / self-contained**: zero external fetch constructs (no off-host `src`/`href`, no `@import`, no `url(http...)`, no external script or stylesheet); no `w3.org` reference. The builder's own `assert_no_external` self-check passed on both.
- **Well-formed**: both parse with `lxml.html.fromstring` without error.
- **ASCII-only**: no byte above 0x7F in either file.
- **Content**: deck preserves the 5-slide order with a bar chart, a base64 image, and speaker notes; report leads with the synthesized title + agenda and renders a line chart across 6 sections.
- **hallmark-design anti-slop gate**: PASS. No unmotivated gradient (gate 7), softened ink on off-white rather than #000-on-#fff (gate 11), a modular type scale (gate 12), `max-width`-bounded measure (gate 13), deliberate line-height (gate 14), system font stacks with no web-font fetch (gate 15), no emoji bullets (gate 24), purposeful transitions honoring `prefers-reduced-motion` (gates 25, 27), and visible focus states (gate 26). The three `font-family` declarations are a justified three-role split (body sans, display, mono for code), not three competing body faces.
