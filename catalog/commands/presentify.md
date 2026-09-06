---
description: Turn documents, PDFs, slides, data, code, or a repository into one offline interactive scrolling HTML with optional title-page Presentation Mode. Use for presentify, interactive handbooks, slide navigation, or presentation mode. SKIP new source-document generation, one-off static charts, and plain text edits.
---

# /presentify Command

Build one self-contained offline HTML that opens as a detailed scrolling page and, by default, includes Presentation Mode on the title and top menu. Both global entry buttons always start at slide 1; chapter entry is a separate action. Preserve the source's content and approved branding while rebuilding figures and interactions to the selected depth.

This is a thin dispatcher to `document-to-interactive-html`. Read its `references/dual-view-handbooks.md` for the authoritative intake, compatibility, depth, fidelity, design, and final verification contract. Direct skill calls use the same contract.

## Usage

```text
/presentify <file-or-folder...> [--style <description>] [--theme <name-or-path>] [--layout <full|standard|portrait|description>] [--presentation <yes|no>] [--presentation-theme <light|dark|mixed>] [--presentation-depth <concise|balanced|deep-dive>] [--nav <scroll|slides>] [--images <none|stock|ai|both>] [--interactivity <restrained|balanced|rich|cinematic>] [--verbosity <distilled|balanced|comprehensive>] [--qa-depth <light|standard|deep>] [--out <path>] [--mode <auto|deck|report|compile>]
```

## Resolve and delegate

1. Resolve input paths, output path, and source organization. Accept PDF, Word, Excel, PowerPoint, text/Markdown, CSV/TSV, images, code/configuration, or directories. Use the extractor's recursive walk, exclusion, and size limits. A slide-based PDF is a deck, not automatically a prose report. Preserve source order and attribution. Multiple inputs compile into one labeled site; a repository adds a navigable overview and file tree.
2. Resolve missing choices using the shared contract. Current flags and explicit session answers bind; retained approved project settings bind during maintenance. Do not ask again merely because an answer was not typed as a flag. An unrelated remembered preference never pre-answers network consent.
3. Offer only reading canvases in the output-format question: full-width scrolling, standard scrolling column, or portrait scrolling. Separately ask whether to include presentation (Yes recommended / No). Only when included, ask light-only / dark-only / random mixed themes and concise / balanced / deep-dive presentation depth. Main-page verbosity and QA depth remain independent. Ask content-derived color schemes and page coverage after extraction only when unresolved. Preserve the three content-derived scheme choices plus Other and 5-swatch previews; pin chosen colors through `--scheme-hint` when using the entropy sampler.
4. Keep `--style` (also `using the style ...`), exact `--theme` brand `tokens.json`, interactivity, imagery, verbosity, and output-path controls. Interactivity ranges from user-initiated restrained through balanced, rich, and opt-in cinematic; cinematic is never silently selected from rich: confirm a proposal when not already authorized. It follows `references/scroll-scrub.md` with its asset size/cost and reduced-motion requirements. Honor supplied brand references before rolling novel tokens. Do not force an approved project into a different look on every refresh.
5. Map legacy `--nav slides` to presentation included and initial reading view with a short compatibility notice; `--nav scroll` does not disable presentation. Theme or depth alone implies inclusion; explicit `--presentation no` takes precedence and records ignored presentation settings. `--layout` changes the reading canvas, not the deck aspect. These are agent-resolved options, not additional flags for the legacy baseline builder.
6. Delegate with the resolved options and provenance. Extract and verify the source, reconstruct recoverable figures, author both views from shared content, and run the shared coverage/design/functional acceptance checks. Existing deck output must have no more logical slides than its source. Do not use continuation slides, shrinking text, or clipped overflow to satisfy layout.

## Imagery and offline boundary

`--images` values are `none`, `stock`, `ai`, or `both`. Procedural inline SVG/CSS is the always-on visual baseline, so None is not a bare page. The old no-visuals meaning no longer exists. Legacy `procedural` -> `none`; `auto` / `mix` -> `both`. Source imagery is retained independently of this additional-imagery choice.

Stock or local-AI imagery is opt-in. Honor explicit authorization already provided in the session; never pre-answer consent from a recalled preference. When authorization is missing, capture it before a build-time fetch or generation. `stock` prefers verified free-for-commercial-use assets; `ai` uses local generation only; `both` prefers stock. Stock video requires Pexels with a configured `PEXELS_API_KEY` and authorization; missing support falls back with a reason. Direct missing-key setup to `nexus-hub setup-media`, never ask for a key in chat. Default and non-interactive runs remain fully offline with no fetch or generation. Every delivered asset is embedded; no hosted generation or CDN is used by this workflow.

## Verification and delivery

The agent authors and verifies the actual file. `--qa-depth` controls iteration budget, not whether a success claim needs evidence. Render both views and their interaction states; inspect every slide and reading section against source and positive references. Record final hashes and separate factual, visual, and functional results. Missing browser capability permits a clearly labeled draft, never an implied production-ready pass. Existing helper success alone does not certify this contract.

For a documentation refresh, `technical-documentation` owns `references/handbook-refresh.md`; preserve approved design settings, update both views against the actual candidate, and verify freshness. Do not run a new interview for already resolved choices.

### Runtime helper manifest

Every runtime helper lives in the DELEGATED skill's bundle, not in this command's package. A session that assumes otherwise guesses a filesystem path for a required QA step, which is exactly what happened once and is why this manifest exists. All paths are relative to `catalog/skills/specialized-domains/document-to-interactive-html/` (or to the installed skill directory on a user's machine):

| Helper | Path | Used by |
|---|---|---|
| Content extractor | `scripts/extract_content.py` | Step 3 |
| Design-entropy sampler | `scripts/design_seed.py` | Step 5 |
| Stock-media fetcher (consent-gated) | `scripts/fetch_stock_media.py` | Step 6, Tier 2 |
| Local AI image generator | `scripts/generate_local_image.py` | Step 6, Tier 3 |
| Map projection fitter | `scripts/fit_map_projection.py` | figure reconstruction, path 2b |
| Render-environment probe | `scripts/ensure_render_env.py` | Step 9, before the loop |
| Structural visual-QA scorer | `scripts/visual_qa_score.py` | Step 9, every iteration |
| Deterministic baseline builder (optional) | `scripts/build_presentation.py` | Step 7 |

Resolve the skill directory once at the start of a run and derive every helper path from it. Do not search for a helper by name, and do not assume a helper sits beside this command file.

## Output

Deliver the single HTML at `--out` or beside the inputs, plus retained authoring inputs and local verification evidence. The HTML itself opens offline without sibling-file dependencies. State any unresolved source ambiguity or unverified browser behavior; do not claim perfect first-pass generation or undetectable AI authorship.
