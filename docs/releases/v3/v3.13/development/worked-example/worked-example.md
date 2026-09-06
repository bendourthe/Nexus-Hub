# Worked Example -- mixed repository -> interactive site (v3.13.0 Phase 4)

This is the end-to-end worked example for the presentify universal-ingestion overhaul, run on the `mixed-repo` fixture (`docs/v3/v3.13/development/fixtures/mixed-repo/`).

## Artifacts

- `mixed-repo-model.json` - the content model emitted by `extract_content.py` on the fixture directory (deterministic; 13 sections, `tree` present).
- `mixed-repo-site.html` - a self-contained, offline, interactive site authored from that model (standard aspect, content-aware auto-pick for a repository input).

## Pipeline exercised

`extract_content.py <mixed-repo dir>` -> content model -> author interactive site.

The single-directory input triggered repository assembly: a synthesized `overview` section, a `tree`, README / docs first, then source code grouped by top-level directory, then data and images.

## Coverage reconciliation (model vs. output)

Walk manifest (`coverage.walk`): 8 files included, 1 gitignored, 1 directory ignored, 0 over the file cap.

| Source file | Ingested as | Rendered in the site |
|---|---|---|
| `README.md` | markdown -> heading-delimited sections (paragraph, bullets, table, fenced code, inline SVG image) | README section (rendered) |
| `data/notes.txt` | text -> paragraph blocks | Release-notes section |
| `data/metrics.csv` | csv -> chart block (`source-data`, Revenue + Cost over Q1-Q4) | Interactive inline-SVG bar chart (hover readout + legend toggle) |
| `src/app.py` | code (`python`, path set) | Code section, offline-highlighted |
| `src/lib/helper.go` | code (`go`, path set) | Code section, offline-highlighted |
| `src/util.js` | code (`javascript`, path set) | Code section, offline-highlighted |
| `assets/logo.svg` | image (`standalone-image`, `image/svg+xml`) | Gallery + lightbox |
| `assets/pixel.png` | image (`standalone-image`, native dims 1x1) | Gallery + lightbox |
| `secret.txt` | EXCLUDED (`.gitignore`) | not present (gitignored: 1) |
| `node_modules/pkg/index.js` | EXCLUDED (ignored dir) | not present (dirs_ignored: 1) |

Verdict: ACCOUNTED - every walked-and-included file appears in the output; every excluded path is in `coverage.walk` with a reason. 0 unaccounted.

## Static offline review (no-browser degradation)

No headless browser is available on this dev host, so the skill's documented degradation applies: a static structural review instead of a rendered screenshot pass.

- External requests: NONE (0 CDN / `@import` / external `<script src>` / `<link>`; no literal `http(s)://` outside the base64 payloads). Opens fully offline.
- Well-formed: 8 `<section>`s, no unclosed or stray tags (checked with `html.parser`).
- Self-contained: all CSS / JS inline; images as base64 `data:` URIs (3 occurrences).
- Behaviors present: repository overview, sticky file-tree nav with active-section tracking (`IntersectionObserver`), scroll reveals (reduced-motion-guarded), offline keyword highlighting on code, an interactive bar chart on the real CSV values (hover readout + series toggle), and an image lightbox (Escape / backdrop close, focus restore). Standard aspect (centered ~78rem column); sections sized to content (no dead screens).

## Deferred to a browser-capable / library-complete run (Phase 5)

- The rendered screenshot pass (the full visual-QA loop with captured states) needs a headless browser.
- The deck-PDF prominence path (native `page_fraction` from `pdfplumber` bboxes, hero-vs-gallery rendering on the real Supira deck) needs `pdfplumber` / `python-pptx`, which are not installed on this host (the PDF path falls back to `pypdf`, without bbox geometry).

These are tracked as the Phase 5 worked-example / known-gaps items; the extraction correctness and offline self-containment demonstrated here are the new machinery this plan added.
