# Cursor Usage Monitor Visual Contract

**Version:** v3.15.9
**Brand meter color:** `#4682B4`
**Verified:** 2026-08-04

## Decision

The monitor uses `#4682B4` for included-usage meter fills and neutral brand accents, a theme-colored monochrome Cursor status glyph, and the supplied grayscale Cursor geometry in the warning panel and package icon. Warning states always pair color with severity text and iconography. No meter, warning, or stale state relies on color alone.

The maintainer supplied 480x480 and 48x48 PNG references. Their filenames identify Icons8, and the official Icons8 CDN returns byte-equivalent geometry under icon ID `DiGZkjCzyZXn`. Phase 3 preserves those official bytes and records their hashes. Phase 5 owns deterministic vector normalization, icon-font generation, and the 256x256 package derivative.

## Source Asset Inventory

| Asset | Provenance and license | Verified dimensions / geometry | Integrity | Packaged use |
|---|---|---|---|---|
| `extensions/cursor-usage-monitor/icons/cursor-ai-480.png` | Maintainer-supplied Icons8 Cursor AI mark, re-fetched from official Icons8 CDN; free use requires attribution unless covered by a paid Icons8 license | 480x480 RGBA PNG with transparent background; centered grayscale faceted cube | SHA-256 `5706468F30FC4BC45C96F8909B94FA110CC5014D4DDB7E1A3F360D51F75CF459` | Source for a downscaled transparent 256x256 package icon |
| `extensions/cursor-usage-monitor/icons/cursor-ai-48.png` | Same Icons8 icon ID and attribution requirement | 48x48 RGBA PNG with transparent background; compact pixel-aligned rendering | SHA-256 `2804DC1CD9720988D3E561114D6C3FA39B554AACED40C92AF1BC848133699DAB` | Warning-panel mark and compact geometry reference |
| `extensions/cursor-usage-monitor/icons/README.md` | Nexus-Hub provenance record | Source URLs, hashes, dimensions, use and attribution gate | Text review plus contract tests | Shipped source notice; package notice is generated in Phase 5 |

Icons8's public free-use guidance requires a backlink unless the user has a paid license. The extension therefore must include an attribution link in `THIRD_PARTY_NOTICES.md` and the warning view before packaging, or replace the requirement with maintainer-supplied paid-license evidence.

## Geometry and Derivation

The 48px raster is a reference, not a status-bar image. VS Code status-bar custom icons use an icon font, so Phase 5 will:

1. Trace the compact mark into a single monochrome silhouette inside `viewBox="0 0 20 20"`.
2. Use `fill="currentColor"` and remove embedded raster images, scripts, external references, transforms, and hard-coded theme colors.
3. Compare the normalized silhouette against both supplied PNGs at 20px and 48px.
4. Scale and flip the 20x20 path into a 1024-unit icon-font glyph at a Cursor-specific private-use codepoint.
5. Commit only the normalized SVG and generated WOFF2 needed at runtime; intermediate TTF/SVG font artifacts stay generated or ignored.

The package icon is a transparent 256x256 downscale of the 480px source, never an upscale of the 48px raster. Resampling must preserve the original grayscale geometry and alpha channel without adding gradients, checkerboards, shadows, borders, or a background.

The warning panel may use `cursor-ai-48.png` byte-for-byte at its native dimensions or render it smaller through CSS. It must not enlarge the 48px raster beyond its native size.

## Color and Theme States

| Surface | Light theme | Dark theme | High contrast |
|---|---|---|---|
| Status-bar glyph | VS Code status-bar foreground through `currentColor` icon font | VS Code status-bar foreground through `currentColor` icon font | System foreground; geometry remains legible without grayscale facets |
| Usage-bar fill | `#4682B4` on a neutral track with numeric text | `#4682B4` on a neutral dark track with numeric text | Forced-color-safe border plus numeric label; fill is secondary |
| Warning panel mark | Grayscale mark on a theme-token background | Grayscale mark on a theme-token background | Decorative image may be hidden; title and severity remain |
| Warning severity | Icon plus `Moderate`, `High`, or `Critical` text | Icon plus explicit severity text | System warning/error border, distinct icon, and text |
| Stale state | `Stale` label, age, and reason | Same text contract | Same text contract |

`#4682B4` is the meter fill, not the warning severity palette. Warning colors use VS Code semantic tokens and always retain text/icon equivalents.

## Meter and Dashboard Contract

- Render separate `Cursor Models` and `Other Models` meters. Never merge their percentages or denominators.
- Every percentage meter has `role="meter"`, an accessible name, numeric percentage, used amount and unit when known, reset context, source, and freshness.
- Unknown denominators use an absolute-usage treatment and never render a percentage or invented maximum.
- On-demand spend renders as a **third bar** measured against its spend limit (v3.15.12 Phase 2; supersedes the v3.15.9 rule that on-demand was currency text only). Its headline and every numeric label stay in **currency**; the percentage exists solely as bar geometry and `aria-valuetext`. It is still never a token meter, and token, request, percentage, and money units are never converted into one another.
- The on-demand bar is dropped, not approximated, whenever a fraction would be meaningless: no limit reported, a limit in a different currency from the spend, or a non-positive limit. Those cases fall back to an absolute-spend treatment that says the shared limit is unavailable.
- An over-limit bar clamps its fill at 100 and states that it is over the shared limit. It never overflows its track or renders a width above 100.
- Teams spend limits are labeled `Shared team context`; they are never a personal meter or `$limit / member_count`. The on-demand bar therefore carries an explicit annotation naming the sharing scope and the reset date taken from the payload's billing cycle, never a hardcoded day. Measuring personal spend against a shared limit is permitted **only** with that annotation present.
- Percentages render with up to one decimal, trailing `.0` trimmed, and the same formatter drives the dashboard, status bar, and hover so one pool cannot read `1.7%` in one surface and `2%` in another. Plain rounding overstated a nearly-untouched allowance.
- Use VS Code theme tokens for text, backgrounds, borders, focus rings, buttons, and tracks.
- Respect `prefers-reduced-motion`; no decorative animation is required.
- Webview CSP blocks remote scripts, styles, fonts, and images. Attribution opens only on an explicit user action.

## Package and Accessibility Checks

- `icon.png` must be at least 128x128; Phase 5 target is transparent 256x256 RGBA.
- The generated VSIX must include `icon.png`, the normalized status SVG, `cursor-ai-48.png`, the WOFF2 font, warning icon, and `THIRD_PARTY_NOTICES.md`.
- Tests must verify source hashes before generating derivatives so upstream CDN drift cannot silently alter branding.
- Status glyph and warning icon have non-color semantics.
- Keyboard focus is visible for every interactive dashboard/settings element.
- Decorative logo images use empty alt text when the adjacent heading already names Cursor; otherwise use concise alt text.
- Interactive light/dark/high-contrast screenshots remain a live-smoke requirement for Phase 5 or release readiness.

## License and Trademark Gate

The artwork is sourced from Icons8 icon ID `DiGZkjCzyZXn`; attribution is required for free use unless a paid license is documented. Cursor retains ownership of its name and marks. The package name and description must say it is an independent Nexus-Hub monitor, must not use Cursor's mark as Nexus-Hub's identity, and must not imply endorsement.

No source PNG is evidence of a paid license. Packaging is blocked until either:

- `THIRD_PARTY_NOTICES.md` and the warning view contain the required Icons8 backlink; or
- the maintainer supplies paid-license evidence and the notice records that basis.

## Mechanical Acceptance Results

- [x] Meter fill is locked to `#4682B4`.
- [x] The 480x480 RGBA source exists and matches SHA-256 `5706468F30FC4BC45C96F8909B94FA110CC5014D4DDB7E1A3F360D51F75CF459`.
- [x] The 48x48 RGBA source exists and matches SHA-256 `2804DC1CD9720988D3E561114D6C3FA39B554AACED40C92AF1BC848133699DAB`.
- [x] Source URLs and the Icons8 attribution requirement are recorded.
- [x] The package-icon plan uses the 480px source and targets transparent 256x256 output.
- [x] The status-glyph plan requires a single `currentColor` 20x20 vector and generated WOFF2.
- [x] Final normalized SVG, WOFF2, package icon, and package notice are generated in Phase 5.
- [ ] Interactive light/dark/high-contrast smoke is completed in Phase 6 live-smoke checklist or release readiness.

## Sources

- [Icons8 Cursor AI icon](https://icons8.com/icon/DiGZkjCzyZXn/cursor-ai)
- [Icons8 image CDN and attribution guidance](https://img.icons8.com/)
- [VS Code extension manifest and icon requirements](https://code.visualstudio.com/api/references/extension-manifest)
- [Cursor models and pricing](https://cursor.com/docs/models-and-pricing)
