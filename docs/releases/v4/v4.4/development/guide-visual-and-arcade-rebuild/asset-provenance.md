# v4.4.1 Asset Provenance Ledger

**Plan**: [v4.4.1-guide-visual-and-arcade-rebuild.md](../../plans/v4.4.1-guide-visual-and-arcade-rebuild.md)
**Phase**: 1, sub-task 1.3 (decision task)
**Acquisition date**: 2026-09-01
**Status**: APPROVED 2026-09-01. All five platform marks are approved at the exact sanitized SHA-256 values in section 1, so Phase 2 is unblocked.

Every byte a later phase inlines into `guides/website/nexus-hub-guide.html` must appear in this ledger with a matching hash. Phase 2 adds a test that extracts each embedded mark and compares its SHA-256 against the staged file *before* any normalization, so a silent substitution or a post-approval edit fails the suite rather than shipping.

## 1. Platform marks -- staged and APPROVED

Staged under [`assets/`](assets/). All five are true vector geometry: no raster payload, no external reference, no script, no event handler, no `foreignObject`, no `@import`.

| Mark | Staged file | Sanitized bytes | Sanitized SHA-256 |
|---|---|---:|---|
| Claude | `assets/claude.svg` | 1,140 | `874e05685d2f0a473a5c28735771ba6720423b2c8f3d2e99d420c08c1afd5ed3` |
| ChatGPT | `assets/chatgpt.svg` | 1,755 | `a0dccb37b2ed50f509b96fa9617996e65904860a3a29ef9b85f178c23e7ff645` |
| Gemini | `assets/gemini.svg` | 8,871 | `05f04ef9063c1b00e4032d549aa3ad79c039322fd98b95a9d0873ff842b02752` |
| Cursor | `assets/cursor.svg` | 559 | `63cf5e9127a91ce040742594b577911d911dfd9e4ddd1a586f2b781aa8713fd1` |
| GitHub Copilot | `assets/github-copilot.svg` | 1,852 | `a323c872cac8605929e002c283cfa296a6b4d16c212492e10efb74e49feaa020` |
| | **total** | **14,177** | (within the 30,000-byte Phase 2 allocation) |

### 1.1 Claude

| Field | Value |
|---|---|
| Source | `https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg` |
| Source revision | Wikimedia file timestamp `2026-04-28T11:13:49Z` |
| Original bytes / SHA-256 | 1,155 / `5de1221c77cc91e748066fd642ad0eee1c1fa65328814f5178166f901e599709` |
| Author / owner as stated upstream | "Claude Logo Symbol"; the mark is Anthropic's |
| Stated licence | CC0 (`Copyrighted: True` is also asserted on the same record, which is internally inconsistent -- see the risk note) |
| Trademark note | The Claude mark is a trademark of Anthropic. Use here is nominative: it identifies a platform Nexus-Hub is compatible with, and implies no endorsement. |
| Sanitization performed | removed the host `class="w-full"`; collapsed whitespace. The vendor `fill="hsl(14.8, 63.1%, 59.6%)"` brand colour is retained VERBATIM rather than converted to hex, so the shipped bytes carry the vendor's own stated value. |
| Colour handling | full-colour, single brand fill; legible on both themes without a variant |

### 1.2 ChatGPT

| Field | Value |
|---|---|
| Source | `https://upload.wikimedia.org/wikipedia/commons/e/ef/ChatGPT-Logo.svg` |
| Source revision | Wikimedia file timestamp `2024-02-14T00:20:31Z` |
| Original bytes / SHA-256 | 1,739 / `a66ba245fc68677ae1a47a5f726d60d691e4c8d5942028328dc2beb3b8ceb4dc` |
| Author / owner as stated upstream | OpenAI |
| Stated licence | Public domain (`Copyrighted: False`; below the threshold of originality) |
| Trademark note | Upstream record explicitly flags `Restrictions: trademarked`. The mark is a trademark of OpenAI; use here is nominative. |
| Sanitization performed | removed the XML declaration; normalized single quotes to double quotes; collapsed whitespace; added `fill="currentColor"` |
| Colour handling | monochrome. `currentColor` lets the guide's CSS supply the theme colour, so no second variant file is needed. |

### 1.3 Gemini

| Field | Value |
|---|---|
| Source | `https://upload.wikimedia.org/wikipedia/commons/1/1d/Google_Gemini_icon_2025.svg` |
| Source revision | Wikimedia file timestamp `2025-07-28T01:49:52Z` |
| Original bytes / SHA-256 | 8,712 / `cda2df6631d5fa227de3fa04ed78cf354f910ba92a9f086e7455655c10ad9d09` |
| Author / owner as stated upstream | Google LLC |
| Stated licence | Public domain (`Copyrighted: False`) |
| Trademark note | Upstream record flags `Restrictions: trademarked`. The mark is a trademark of Google LLC; use here is nominative. |
| Sanitization performed | removed the XML declaration; **namespaced all 13 identifiers to `nxp-gm-*`** and rewrote every `url(#...)` reference, because the upstream ids (`maskme`, `prefix__filter0_f_2001_67`, ...) are generic enough to collide with another inlined asset. The alpha `<mask>` and five `feGaussianBlur` filters are RETAINED: they are declarative rendering, not executable content. |
| Colour handling | full-colour gradients (`#4893FC`, `#969DFF`, `#BD99FE`); legible on both themes without a variant |
| Cost note | the largest mark at 8,871 bytes and the only one carrying blur filters, so it dominates both the byte and the raster cost of the rail |

### 1.4 Cursor

**A better source than the plan's local candidates was found, and it changes the recommendation.**

| Field | Value |
|---|---|
| Source | official Cursor brand archive `https://ptht05hbb1ssoooe.public.blob.vercel-storage.com/assets/brand/cursor-brand-assets.zip`, linked from `https://cursor.com/brand`; entry `General Logos/Cube/SVG/CUBE_2D_DARK.svg` |
| Source revision | archive entry mtime `2025-09-23T21:36:52`; archive 1,900,360 bytes, 148 entries |
| Original bytes / SHA-256 | 793 / `cd0e3e5d8991a4cdd4577f8896cd063105207665165c73e25a1ff918dd367eb7` |
| Author / owner | Anysphere (Cursor) |
| Stated use terms | The brand page states one explicit guideline: "Refer to us as Cursor. Not Cursor AI or Cursor Code." No licence text, permission grant, or restriction language is published. |
| Trademark note | The Cursor mark is a trademark of Anysphere; use here is nominative. The naming guideline is satisfied: the rail label is exactly `Cursor`. |
| Sanitization performed | removed the XML declaration and the Illustrator generator comment; removed `id="Ebene_1"`; **removed the `<defs><style>.st0{fill:...}</style></defs>` block and replaced the class reference with `fill="currentColor"`**; collapsed whitespace |
| Colour handling | monochrome, themed by `currentColor` |

**Why one file replaces the two sanctioned variants, and why that is provably safe.** The archive ships `CUBE_2D_LIGHT.svg` (fill `#26251e`) and `CUBE_2D_DARK.svg` (fill `#edecec`). A byte comparison showed the two files are **identical apart from that single fill hex** (verified: normalizing each fill to the same token makes the files equal). A single mark with `fill="currentColor"` therefore reproduces either sanctioned variant exactly, with the guide's CSS supplying `#26251e` in light theme and `#edecec` in dark. This is a documented substitution of form, not of geometry.

**The two local candidates named in the plan were rejected, with reasons.** `~/Downloads/cursor-vector-logo-seeklogo/cursor-seeklogo.svg` (1,382 bytes) carries gradient ids of the form `lobe-icons-cursorundefined-fill-0`, which identify it as derived from the third-party LobeHub icon set rather than Cursor's own brand archive, despite the `seeklogo` filename. Its fills are `#000`/`#555`, so it is invisible on a dark background and would need a hand-authored light variant with no sanctioned counterpart. The companion `cursor-seeklogo.png` (82,577 bytes) is a raster and is disqualified by the single-file byte budget. The official 793-byte cube is smaller, has first-party provenance, and ships vendor-sanctioned light and dark variants, so it wins on every axis the plan names.

### 1.5 GitHub Copilot

| Field | Value |
|---|---|
| Source | `https://upload.wikimedia.org/wikipedia/commons/d/d0/Codicons_%E2%80%93_copilot-large.svg` |
| Source revision | Wikimedia file timestamp `2025-01-08T19:20:07Z` |
| Original bytes / SHA-256 | 1,875 / `e38dd77ed17b3946710a9f5bf8693e758c37c03c2788dd73c841f50351f9c921` |
| Author / owner as stated upstream | Microsoft Corporation (the Codicons icon set) |
| Stated licence | **CC BY 4.0 -- attribution REQUIRED** |
| Trademark note | Upstream record flags `Restrictions: trademarked`. The mark is a trademark of Microsoft/GitHub; use here is nominative. |
| Sanitization performed | removed fixed `width`/`height` so CSS owns the optical box; collapsed whitespace. The upstream `fill="currentColor"` is retained unchanged. |
| Colour handling | monochrome, themed by `currentColor` |

**This is the one row that imposes an obligation on the shipped page.** CC BY 4.0 requires attribution, so requirement **H12** in the Phase 1 contract is not optional for this asset: Phase 2 must ship an accessible credits disclosure naming the Codicons set and Microsoft Corporation under CC BY 4.0. A rail that inlines this mark without that disclosure is a licence violation, not a cosmetic omission.

## 2. Safety verification performed

Every staged file was checked programmatically, and staging asserts on failure rather than warning:

- no `<script>`, no `on*=` event handler, no `<foreignObject>`, no `<image>`, no `@import`, no `xlink:href`
- no `http` occurrence other than the required `xmlns="http://www.w3.org/2000/svg"`, so the shipped page makes no runtime network call
- all retained identifiers namespaced where upstream ids were generic (Gemini only; the other four declare no ids)
- rendered in a real browser at 44 px in both themes: all five are legible, correctly coloured, and share one optical box

## 3. Output media for Phase 4 -- recorded as a Phase 4 blocker

The plan permits each media candidate to be either staged now or "recorded as a Phase 4 blocker", and permits locally generated original media provided provenance is recorded. These four are deliberately deferred to Phase 4, which is the phase that consumes them; deferring them blocks Phase 4 only and does not block Phase 2.

| Candidate | Intended staged name | Disposition |
|---|---|---|
| Model output, still image | `assets/model-output-image.svg` | **Phase 4 blocker.** To be generated as original procedural inline SVG in Phase 4, hashed into this ledger before embedding. No third-party source will be used. |
| Model output, moving image | `assets/model-output-video.gif` | **Phase 4 blocker.** To be generated locally as original frames. If the byte cost exceeds its Phase 4 allocation, the fallback is an animated inline SVG instead of a GIF, recorded here with its hash. |
| Moving-image poster | `assets/model-output-video-poster.svg` | **Phase 4 blocker.** Original procedural SVG, paired with the item above. |
| Model output, audio | `assets/model-output-audio.wav` | **Phase 4 blocker.** To be synthesized locally as an original waveform. An accessible text alternative is required alongside it. |

Phase 4 may not embed any of these until its bytes appear above with a SHA-256.

## 4. Approval record

| Mark | Approved | Approved hash | Date |
|---|---|---|---|
| Claude | **yes** | `874e05685d2f0a473a5c28735771ba6720423b2c8f3d2e99d420c08c1afd5ed3` | 2026-09-01 |
| ChatGPT | **yes** | `a0dccb37b2ed50f509b96fa9617996e65904860a3a29ef9b85f178c23e7ff645` | 2026-09-01 |
| Gemini | **yes** | `05f04ef9063c1b00e4032d549aa3ad79c039322fd98b95a9d0873ff842b02752` | 2026-09-01 |
| Cursor | **yes** | `63cf5e9127a91ce040742594b577911d911dfd9e4ddd1a586f2b781aa8713fd1` | 2026-09-01 |
| GitHub Copilot | **yes** | `a323c872cac8605929e002c283cfa296a6b4d16c212492e10efb74e49feaa020` | 2026-09-01 |

All five approved by the maintainer on 2026-09-01, after review of the rendered both-theme contact sheet and this ledger. The approval covers the two documented substitutions in section 1.4: the official Cursor brand archive in place of the plan's LobeHub-derived local candidates, and one `currentColor` file in place of the two sanctioned fill variants.

Phase 2 may inline ONLY these five hashes. Re-sanitizing, re-minifying, or re-fetching any mark changes its hash and re-opens this gate.

### 4.1 Approved attribution mechanism (requirement H12)

The CC BY 4.0 obligation on the GitHub Copilot codicon is satisfied by a **collapsed credits disclosure placed beside the platform rail**: a keyboard-accessible `<details>`/`<summary>` element titled "Trademarks and credits" that names the Codicons set and Microsoft Corporation under CC BY 4.0, and carries one nominative-use statement covering all five marks. It is visible on demand, costs no persistent layout in the Home hero, and keeps the attribution adjacent to the mark it covers.

Phase 2 must implement this disclosure in the same commit that inlines the marks, and must assert it exists. A rail without it is a licence violation rather than a cosmetic omission.
