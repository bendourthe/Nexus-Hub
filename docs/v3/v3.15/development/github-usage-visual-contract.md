# GitHub Usage Monitor Visual Contract

**Version:** v3.15.8
**Brand meter color:** `#651DA8`
**Verified:** 2026-08-02

## Decision

The monitor uses a theme-colored monochrome GitHub status glyph, the maintainer-supplied purple gradient mark in the warning panel, and `#651DA8` for usage-bar fills and neutral brand accents. Warning states always pair color with text and iconography. The 14x14 gradient bitmap must not be blindly enlarged into the packaged extension icon.

## Source Asset Inventory

| Asset | Provenance | Verified dimensions / geometry | Integrity | Approved use | Distribution state |
|---|---|---|---|---|---|
| `%USERPROFILE%/Downloads/Github-Logo--Streamline-Flex-Gradient.png` | Maintainer-supplied local file; filename identifies Streamline Flex, but no separate license grant was supplied | `14x14` PNG with transparent background; purple-blue gradient Octocat silhouette | SHA-256 `DE9D1B04630AB8FC29B6E40D85B6018A6E0BD0F621BDC1BE2608663F9DFD90D8` | Warning-panel branding at native or integer-scaled display sizes where it remains crisp | Do not copy into the extension until redistribution permission is confirmed |
| Maintainer-supplied GitHub status SVG | Declared by the approved plan; source file is not present in the repository or Downloads as of 2026-08-02 | Required `viewBox="0 0 20 20"`; exact paths, fills, strokes, and hash are not independently verified because the file is unavailable | Pending source attachment | Source for the monochrome icon-font glyph after geometry inspection | Blocked until the exact file is supplied and its provenance is recorded |
| Packaged `icon.png` | Derived artifact, not yet generated | Minimum `128x128`; target `256x256` PNG | Must be reproducible from an approved high-resolution or vector source | VS Code Marketplace and VSIX extension icon | Blocked until a non-blurry approved source and license evidence exist |

## Geometry Contract

The status SVG must satisfy all of these checks before the icon-font pipeline consumes it:

- Root `viewBox` is exactly `0 0 20 20`.
- Geometry is a single-color silhouette or can be normalized to `currentColor` without changing the mark.
- No embedded bitmap, external URL, script, metadata payload, or hidden off-canvas geometry exists.
- Paths fit inside the view box without clipping at one device pixel.
- The normalized SVG is hashed and committed beside the generation script before the WOFF2 font is generated.

Because the actual SVG is unavailable, Phase 1 records these as mandatory acceptance checks rather than inventing or downloading substitute geometry.

## Derivation Contract

1. Inspect the supplied SVG source and record its hash, license status, and exact path count.
2. Normalize its monochrome geometry to `currentColor` and retain the `20x20` coordinate system.
3. Run a deterministic icon-font generator modeled on the Claude and Codex monitor pipelines. Commit the source SVG, generator, and generated WOFF2 together.
4. Produce `icon.png` at `256x256` from an approved vector or high-resolution source. Do not use nearest-neighbor or interpolated enlargement of the 14x14 PNG as the package icon.
5. Compare source and derivative at `16x16`, `20x20`, `32x32`, `128x128`, and `256x256`. Reject clipping, halos, broken transparency, softened edges, or a materially changed silhouette.

If no approved vector or high-resolution package-icon source is available, request one from the maintainer and keep packaging blocked. The 14x14 gradient mark may still be used inside the warning panel after redistribution approval because that use does not claim marketplace-icon fidelity.

## Color and Theme States

| Surface | Light theme | Dark theme | High contrast |
|---|---|---|---|
| Status-bar glyph | VS Code status-bar foreground via icon font; no baked color | VS Code status-bar foreground via icon font; no baked color | System foreground; glyph remains a filled silhouette with no gradient dependency |
| Usage-bar fill | `#651DA8` on a neutral track with readable numeric text | `#651DA8` on a neutral dark track with readable numeric text | System highlight or bordered fill when `#651DA8` does not meet forced-color requirements |
| Warning panel mark | Gradient mark may appear as secondary branding on a neutral background | Gradient mark may appear as secondary branding with sufficient edge contrast | Hide decorative gradient if forced colors erase it; retain GitHub label and warning icon |
| Warning severity | Icon plus explicit `Warning` or `Critical` text; color is supplemental | Icon plus explicit `Warning` or `Critical` text; color is supplemental | System warning colors plus text and icon |

`#651DA8` is the canonical meter fill, not a severity-only signal. Text contrast is evaluated against the panel background independently; white text is not placed directly over the narrow gradient bitmap.

## Accessibility Checks

- Every meter has a text label, used value, unit, source, freshness, and allowance state.
- Unknown allowances use absolute values and never render a percentage bar with an invented maximum.
- Warning and critical states use icons and words in addition to color.
- Light, dark, and high-contrast screenshots include the status bar, hover, dashboard, and warning panel.
- At 200 percent zoom, labels and values remain visible without overlap or truncation.
- Forced-colors mode retains a visible glyph outline or system foreground fill.

## License and Trademark Gate

The filename alone is not license evidence. Before either source asset is committed, the maintainer must confirm the redistribution right or provide the applicable Streamline license record. GitHub marks must follow GitHub logo and trademark guidance: do not imply GitHub endorsement, alter the Octocat into a different character, or use the mark as Nexus-Hub's own product identity. The extension name and description must state that it is an independent usage monitor.

## Mechanical Acceptance Criteria

- The visual contract contains `#651DA8` exactly.
- The source status SVG requirement contains `viewBox="0 0 20 20"` exactly.
- The source bitmap record contains `14x14` and its SHA-256.
- The package icon record contains minimum `128x128` and target `256x256`.
- The contract explicitly rejects enlarging the 14x14 bitmap into the package icon.
- The license/trademark gate is resolved before an asset enters a VSIX.

## Sources

- [VS Code extension manifest and icon requirements](https://code.visualstudio.com/api/references/extension-manifest)
- [GitHub Logos and Usage](https://github.com/logos)
- Existing local icon pipelines: `extensions/claude-usage-monitor/scripts/generate-icon-font.js` and `extensions/codex-usage-monitor/scripts/generate-icon-font.js`
