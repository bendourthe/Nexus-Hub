# GitHub Billing Usage Visual Contract

**Version:** v3.15.8
**Brand meter color:** `#008080`
**Verified:** 2026-08-02

## Decision

The monitor uses a theme-colored monochrome GitHub status glyph, the maintainer-supplied Streamline purple gradient mark in the warning panel, and `#008080` for usage-bar fills and neutral brand accents. Warning states always pair color with explicit severity text and iconography. The 14x14 gradient bitmap is preserved byte-for-byte for alert branding and is not used as the package-icon source.

The meter color was `#651DA8` through Phase 3 and was changed to teal `#008080` on maintainer request during Phase 4. The change is scoped to meter fills and the dashboard accent rule; the supplied gradient artwork and the vector-derived package icon keep their original purple stops, because those are the maintainer-supplied mark rather than a UI accent. Teal also reads better on dark themes: `#008080` clears 3:1 against both a white and a black backdrop, where the previous purple cleared it only against white.

## Source Asset Inventory

| Asset | Provenance and license | Verified dimensions / geometry | Integrity | Packaged use |
|---|---|---|---|---|
| `github-142-svgrepo-com.svg` | Maintainer-supplied SVG Repo asset; exact source page identifies the asset as CC0 | `viewBox="0 0 20 20"`; one visible path inside non-rendering translation wrappers; no scripts, images, or external references | SHA-256 `76B15E4712E3B279E0A063A1E21794DC4E665FFC54B261A014E73F9A78D72B05` | Normalized into `extensions/github-usage-monitor/icons/github.svg` for status glyph and vector derivatives |
| `Github-Logo--Streamline-Flex-Gradient.png` | Maintainer-supplied Streamline Flex Gradient asset; Streamline free-license attribution is included in the package notice and warning view | `14x14` RGBA PNG with transparent background | SHA-256 `DE9D1B04630AB8FC29B6E40D85B6018A6E0BD0F621BDC1BE2608663F9DFD90D8` | Copied byte-for-byte to `extensions/github-usage-monitor/icons/github-gradient.png` for warning-panel branding |
| `extensions/github-usage-monitor/icon.png` | Generated locally from the normalized CC0 vector silhouette with a three-stop gradient sampled from the supplied reference | `256x256` RGBA PNG with transparent background | SHA-256 `4FDF86BFE7CF22C81CD6ADF2859975883E444C69A9057F41CF66405C3C2CD556` | VS Code Marketplace and VSIX extension icon |

## Geometry and Derivation

The source wrapper translations combine to `translate(-84, -7399)`. Phase 3 applied that transform directly to the path coordinates, removed the wrapper groups, changed the fill to `currentColor`, and committed a single normalized path within the original 20x20 view box. The normalized SVG hash is `BA379E7165614DEA760B29E5616098A10FB6369771BD3857431E7BA2D5783950`.

`scripts/generate-icon-font.js` scales and flips the normalized 20x20 path into a 1024-unit font glyph at `U+E102`, then writes `fonts/github-icons.woff2`. `scripts/generate-package-icon.js` injects the approved gradient into the same vector geometry and rasterizes a transparent 256x256 PNG with Sharp. Neither pipeline reads or enlarges the 14x14 warning raster.

## Color and Theme States

| Surface | Light theme | Dark theme | High contrast |
|---|---|---|---|
| Status-bar glyph | VS Code status-bar foreground through the icon font | VS Code status-bar foreground through the icon font | System foreground; the filled silhouette has no gradient dependency |
| Usage-bar fill | `#008080` on a neutral track with numeric text | `#008080` on a neutral dark track with numeric text | Semantic labels and values remain present even when forced colors replace the fill |
| Warning panel mark | Gradient mark is secondary branding on the panel background | Gradient mark remains secondary to severity text | Decorative image has empty alt text; GitHub title, severity word, and warning icon retain meaning |
| Warning severity | Icon plus `Moderate`, `High`, or `Critical` text | Icon plus explicit severity text | System warning/error border plus text and distinct icon |

## Accessibility and Package Checks

- Every percentage meter has `role="meter"`, an accessible label, numeric value, used amount, unit, allowance source, reset, owner, source, and freshness context.
- Unknown allowances use a bordered absolute-usage treatment and never render a percentage or invented maximum.
- Dashboard and settings controls are keyboard-focusable and expose visible `:focus-visible` outlines.
- Dashboard layout uses VS Code theme tokens, responsive breakpoints, and `prefers-reduced-motion`; warning severity is not color-only.
- Webview CSP blocks external loads. The only external URL is a user-activated attribution link; no remote image, font, style, or script is fetched.
- The generated VSIX includes `icon.png`, `icons/github.svg`, `icons/github-gradient.png`, `icons/warning.svg`, `fonts/github-icons.woff2`, and `THIRD_PARTY_NOTICES.md`; it excludes tests, coverage, source maps, and dependencies.
- Automated structural smoke tests cover light/dark/high-contrast-compatible theme tokens and semantic fallback. Interactive Extension Development Host screenshots remain a recorded manual verification gap because this session cannot observe the VS Code GUI.

## License and Trademark Gate

The status source is published as CC0 by SVG Repo. The Streamline free icon is used with the required "Free icon from Streamline" attribution in `THIRD_PARTY_NOTICES.md` and the warning view. The extension is titled "GitHub Usage Monitor" (see the dated correction below) and described as an independent monitor covering Actions minutes and storage plus Copilot billing for one configured billing owner; no text claims endorsement. The mark remains an Octocat silhouette and is not presented as Nexus-Hub's product identity.

> **Correction, 2026-08-09 (v3.16.3 Phase 1).** The line above previously read: the extension is titled "GitHub Billing Usage" (renamed from "GitHub Usage Monitor" in v3.15.12 Phase 3). v3.16.3 **reverted** that rename. The name is "GitHub Usage Monitor" again, chosen for consistency with the Claude, Codex, and Cursor usage monitors, which a user reads as one family; the v3.15.12 concern that "usage monitor" under-describes the coverage is now carried by the description and the panel subtitle, which name Actions minutes and storage *and* Copilot billing explicitly. Both decisions are deliberately left visible rather than one overwriting the other. The extension id `nexus-hub.github-usage-monitor` was never changed in either direction. v3.16.3 also moved the command ids and configuration keys to the `githubUsageMonitor.*` prefix, with a one-time migration on first activation; the old `githubUsage.*` keys stay readable for one release, and their deletion is a v3.17.0 follow-up.

## Mechanical Acceptance Results

- [x] The usage-bar fill contains `#008080` exactly.
- [x] The normalized status SVG contains `viewBox="0 0 20 20"`, one path, no wrapper group, and no external load.
- [x] The supplied bitmap remains `14x14` with its original SHA-256.
- [x] The package icon is a transparent `256x256` vector-derived PNG, not a raster upscale.
- [x] Redistribution terms and required attribution are recorded in the package.
- [x] Font, gradient artwork, package icon, and notice are included in the VSIX.

## Sources

- [SVG Repo asset page and CC0 license](https://www.svgrepo.com/svg/512317/github%20142.svg)
- [Streamline free license](https://help.streamlinehq.com/en/articles/5354376-streamline-free-license)
- [Streamline attribution guidance](https://help.streamlinehq.com/en/articles/5354403-how-to-create-an-attribution-link/)
- [Streamline GitHub Flex Gradient asset](https://www.streamlinehq.com/icons/download/github--27759)
- [VS Code extension manifest and icon requirements](https://code.visualstudio.com/api/references/extension-manifest)
- [GitHub Logos and Usage](https://github.com/logos)
