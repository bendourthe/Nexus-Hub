# Worked example -- presentify imagery + interactivity (v3.13.0 follow-on)

Evidence for the imagery-and-interactivity follow-on. Two authored pages demonstrate the tiers end to end; Tier 3 is documented (its live path needs a GPU runtime).

## Tier 1 -- procedural, offline (`tier1-imagery-sample.html`)

Authored in Phase 1 from the `mixed-repo-model.json` fixture. It is the always-on default: original visuals only, zero outbound.

- **Direction**: "Warm Editorial Ledger" (light, editorial; diverges from the dark / mono-eyebrow / amber / card-grid attractor). Design-record comment records the palette, fonts, spacing, motion, aspect (standard), imagery tier (procedural), and interactivity level (balanced).
- **Procedural visuals (all original / generated)**: an inline-SVG hero gradient + dot-grid texture, a duotone section divider, a data-motif figure illustration, and editorial devices (a callout number, a pull-quote). Each carries an adjacent `<!-- credit: {"tier":"procedural","provenance":"original (generated)"} -->` comment.
- **Interactivity (balanced)**: sticky section nav with active-state tracking, scroll-triggered reveals, hover/focus affordances, an animated counter landing on the exact source total, and a pan/zoom lightbox on the procedural figure. An interactive grouped-bar chart renders the real CSV values (hover readout, legend series toggle, y-max control, reset).
- **Credits**: an "Image credits" section stating all visuals are original (generated); no external or third-party asset.
- **Static review**: zero external references (grep clean); well-formed (tag balance OK); ASCII-clean. Reduced-motion guarded. Not browser-rendered on this host (WN-1).

## Tier 2 -- license-free stock, live (`tier2-stock-sample.html` + `tier2-credits-manifest.json`)

Produced in Phase 4 by running `fetch_stock_media.py --query "laboratory microscope science" --count 2 --consent` against Openverse (live fetch on 2026-07-15; live results vary run to run), then authoring a page from the returned manifest.

- **Assets**: two Openverse images, both **CC BY 2.0** (a free-for-commercial-use license), verified by the helper's allow-list, downloaded within the size cap, and base64-embedded:
    - "Laboratory broadens student's horizons" by U.S. Army Combat Capabilities Development Command.
    - "Doctor with microscope, 1999" by Seattle Municipal Archives.
- **Attribution**: because both are CC-BY, the helper built a full attribution string for each; the visible "Image credits" section shows title + author + license + source (NO raw URL), while the raw asset / license URLs live in the adjacent `<!-- credit: {...} -->` comments and in `tier2-credits-manifest.json`.
- **Offline**: every image is a `data:` URI - the page makes zero external requests. Verified by stripping HTML comments and base64 payloads, then grepping for `https?://` / `cdn` -> NONE outside comments (the 6 in-comment URLs are the two assets' url / asset_url / license_url).
- **Interactivity (balanced)**: scroll reveals, hover/focus card affordances, and a pan/zoom lightbox on each image. The hero keeps a Tier-1 procedural gradient as its base.
- **Static review**: offline-clean, well-formed (tag balance OK), ASCII-clean.

## Tier 3 -- local AI-generated (documented)

Not exercised live on this host: `generate_local_image.py` needs a local `diffusers` + `torch` (+ GPU) runtime and locally-present weights, none of which are installed on the Windows dev host. The **degrade path** was verified (no runtime => exit 3, a setup hint, no network) and a static check confirmed the script imports no network / hosted-API client. The live generation path is a documented manual step on a GPU-capable host (recorded under MT-2); when run, it embeds a base64 PNG and records `model + license + "AI-generated; may not be copyrightable"` in the credits.

## Coverage summary

| Tier | Evidence | Offline | License / provenance | Live-verified |
|---|---|---|---|---|
| 1 - procedural | `tier1-imagery-sample.html` | Yes (grep clean) | original (generated) | authored + static review |
| 2 - stock | `tier2-stock-sample.html` + `tier2-credits-manifest.json` | Yes (grep clean) | 2x CC BY 2.0, attributed | live Openverse fetch |
| 3 - local AI | (documented) | Yes by design | model + license + caveat | degrade + static-import only (needs a GPU host) |
