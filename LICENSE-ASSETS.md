# Brand Asset License

This file documents the licensing and attribution of the brand assets shipped under [`assets/`](assets/).

## Asset inventory

| File | Brand | Format | Dimensions | Usage |
|---|---|---|---|---|
| `assets/nexus_hub_banner.png` | Nexus-Hub | PNG, RGB | 1983 x 793 | README hero, social previews, banner mentions |
| `assets/nexus_hub_primary.png` | Nexus-Hub | PNG, RGBA | 919 x 919 | Square mark for app icons, badges, small inline references |
| `assets/nexus_banner.png` | Nexus | PNG, RGB | 1983 x 793 | Sibling-project banner, used in stacked cross-link visualizations linking Nexus-Hub to [Nexus](https://github.com/bendourthe/Nexus-AI) |
| `assets/nexus_primary.png` | Nexus | PNG, RGBA | 430 x 430 | Sibling-project square mark, reserved for compact contexts where the banner would be too wide |
| `assets/nexus_monochrome.png` | Shared mark (Nexus / Nexus-Hub) | PNG, RGBA | 507 x 477 | Monochrome variant for dark contexts, print, single-color displays |
| `assets/nexus_monochrome_full.png` | Shared mark (Nexus / Nexus-Hub) | PNG, RGBA | 620 x 596 | Monochrome variant with full square treatment |
| `assets/sibling_arrow.svg` | Generated graphic | SVG, vector | 160 x 60 (viewBox) | Decorative double-headed arrow rendered between the Nexus-Hub and Nexus banners in the README cross-link block. Neutral-gray stroke (#9aa4ad) reads on both light and dark GitHub themes. |

## License

All brand assets in [`assets/`](assets/) are authored by Benjamin Dourthe and are reused from the sibling [`bendourthe/Nexus-AI`](https://github.com/bendourthe/Nexus-AI) project where applicable. Both projects share the same author, so the cross-repo reuse is internal-only and does not introduce a third-party attribution requirement.

These assets are licensed under the same terms as the rest of this repository (see [`LICENSE`](LICENSE)).

## Brand usage notes

- **Banner**: the wide `nexus_hub_banner.png` is the canonical README hero and the preferred surface in any horizontal layout (a tagline strip, a blog post header, a social card). The sibling `nexus_banner.png` is the same shape and resolution for the Nexus brand, used in stacked cross-link visualizations so the two project banners read as a related pair rather than competing layouts.
- **Square primary**: `nexus_hub_primary.png` is the canonical square mark. Use it for inline references, app icons, GitHub social preview, and anywhere a 1:1 aspect ratio is required.
- **Monochrome**: prefer `nexus_monochrome.png` for single-color displays (printed material, low-color terminals via image-to-ansi tooling, etc.); `nexus_monochrome_full.png` adds the rounded-square frame.
- **Sibling brand**: `nexus_primary.png` is the [Nexus](https://github.com/bendourthe/Nexus-AI) square variant. Its color treatment differs from `nexus_hub_primary.png` (different cyan and gradient stops -- darker, more electric-blue vs. the cyan / teal of Nexus-Hub) so the two marks are visually distinguishable when placed adjacent -- see the "How Nexus-Hub fits with Nexus" section in [`README.md`](README.md), which currently uses the banner pair `nexus_hub_banner.png` and `nexus_banner.png` stacked vertically.

## Modifying or redistributing

If you fork this repository for an unrelated project, please replace these brand assets with your own. The mark is associated with Nexus-Hub and Nexus specifically, not with the underlying code.
