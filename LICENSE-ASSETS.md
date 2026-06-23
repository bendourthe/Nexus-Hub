# Brand Asset License

This file documents the licensing and attribution of the brand assets shipped under [`assets/`](assets/).

## Asset inventory

| File | Brand | Format | Dimensions | Usage |
|---|---|---|---|---|
| `assets/nexus-hub-banner.png` | Nexus-Hub | PNG, RGB | 1981 x 793 | README hero, social previews, banner mentions |
| `assets/nexus-hub-primary.png` | Nexus-Hub | PNG, RGBA | 1254 x 1254 | Square mark (framed) for app icons, badges, small inline references |
| `assets/nexus-hub-primary_no-background.png` | Nexus-Hub | PNG, RGBA (transparent) | 1024 x 1024 | Transparent square mark for colored / dark backgrounds; embedded as the single reusable logo symbol in the interactive guide |
| `assets/nexus-hub-primary_no-background.svg` | Nexus-Hub | SVG wrapper (embedded raster) | 1024 x 1024 | Same transparent artwork as the PNG, wrapped in an SVG container for convenient HTML/CSS embedding (not a path-based vector) |
| `assets/nexus-ai-banner.png` | Nexus-AI | PNG, RGB | 1983 x 793 | Sibling-project banner, used in stacked cross-link visualizations linking Nexus-Hub to [Nexus-AI](https://github.com/bendourthe/Nexus-AI) |
| `assets/nexus-ai-primary.png` | Nexus-AI | PNG, RGBA | 1254 x 1254 | Sibling-project square mark (framed) for compact contexts where the banner would be too wide |
| `assets/nexus-ai-primary_no-background.png` | Nexus-AI | PNG, RGBA (transparent) | 1024 x 1024 | Transparent sibling-project square mark for colored / dark backgrounds |
| `assets/nexus-ai-primary_no-background.svg` | Nexus-AI | SVG wrapper (embedded raster) | 1024 x 1024 | Transparent sibling-project square mark wrapped in an SVG container |
| `assets/sibling_arrow.svg` | Generated graphic | SVG, vector | 160 x 60 (viewBox) | Decorative double-headed arrow rendered between the Nexus-Hub and Nexus banners in the README cross-link block. Neutral-gray stroke (#9aa4ad) reads on both light and dark GitHub themes. |

## License

All brand assets in [`assets/`](assets/) are authored by Benjamin Dourthe and are reused from the sibling [`bendourthe/Nexus-AI`](https://github.com/bendourthe/Nexus-AI) project where applicable. Both projects share the same author, so the cross-repo reuse is internal-only and does not introduce a third-party attribution requirement.

These assets are licensed under the same terms as the rest of this repository (see [`LICENSE`](LICENSE)).

## Brand usage notes

- **Banner**: the wide `nexus-hub-banner.png` is the canonical README hero and the preferred surface in any horizontal layout (a tagline strip, a blog post header, a social card). The sibling `nexus-ai-banner.png` is the same shape and resolution for the Nexus-AI brand, used in stacked cross-link visualizations so the two project banners read as a related pair rather than competing layouts.
- **Square primary**: `nexus-hub-primary.png` is the canonical framed square mark. Use it for inline references, app icons, GitHub social preview, and anywhere a 1:1 aspect ratio is required against a light surface.
- **Transparent / no-background**: prefer `nexus-hub-primary_no-background.png` (or its SVG-wrapped twin `nexus-hub-primary_no-background.svg`) wherever the mark sits on a colored or dark surface. The interactive guide ([`guides/website/nexus-hub-guide.html`](guides/website/nexus-hub-guide.html)) embeds this transparent mark as its single reusable `<symbol>` logo, so the logo reads cleanly on the dark hero background at every size. The Nexus-AI equivalents are `nexus-ai-primary_no-background.png` / `.svg`.
- **Sibling brand**: `nexus-ai-primary.png` is the [Nexus-AI](https://github.com/bendourthe/Nexus-AI) square variant. Its color treatment differs from `nexus-hub-primary.png` (different cyan and gradient stops -- darker, more electric-blue vs. the cyan / teal of Nexus-Hub) so the two marks are visually distinguishable when placed adjacent -- see the "How Nexus-Hub fits with Nexus" section in [`README.md`](README.md), which uses the banner pair `nexus-hub-banner.png` and `nexus-ai-banner.png`.

## Modifying or redistributing

If you fork this repository for an unrelated project, please replace these brand assets with your own. The mark is associated with Nexus-Hub and Nexus specifically, not with the underlying code.
