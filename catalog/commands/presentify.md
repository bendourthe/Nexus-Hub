---
description: Convert existing documents, code, data or repositories into one offline interactive reading website with included Presentation Mode by default. Use for presentify, interactive handbooks, presentation mode, slide navigation, and PDF/Word/Excel/PowerPoint-to-website requests. SKIP new document creation, one-off static charts, or simple HTML edits.
---

# /presentify Command

Produce one self-contained interactive reading website. Presentation Mode is included by default, with a title-page and global-menu entry that starts at slide 1. The user may opt out. The complete extraction, source fidelity, design, authoring and verification method belongs to `document-to-interactive-html`; this command resolves options and delegates.

## Usage

```text
/presentify <file-or-folder...> [using the style <description> | --style <description>] [--theme <name-or-path>] [--layout <full|standard|portrait|description>] [--presentation <yes|no>] [--presentation-theme <light|dark|mixed>] [--presentation-depth <concise|balanced|deep-dive>] [--nav <scroll|slides>] [--images <none|stock|ai|both>] [--interactivity <restrained|balanced|rich|cinematic>] [--verbosity <distilled|balanced|comprehensive>] [--qa-depth <light|standard|deep>] [--out <path>] [--mode <auto|deck|report|compile>]
```

## Dispatch

1. Resolve input paths without reading document content. Preserve one source's order or compile multiple sources with attribution. Folders/repositories use the existing bounded recursive extractor and its exclusions; extractor limits and optional-format dependency failures are unchanged.
2. Load `document-to-interactive-html` and its `references/presentation-intake.md`. That is the single owner of precedence, defaults, legacy aliases and conditional theme/depth questions. Run its `scripts/resolve_presentation.py` with explicit options, current-session answers and approved project settings. Record provenance; ask only unresolved axes. A pending interactive answer is not authorization to generate.
3. Round 1 batches design direction, scrolling canvas, interactivity, additional imagery and presentation inclusion. Keep the independent design-direction question. Canvas offers full-width scrolling, standard scrolling column, portrait scrolling canvas and free text. After Yes, ask only unresolved theme and depth together. No skips both. Round 2 remains after extraction: three content-derived color schemes plus Other with a 5-swatch preview and independent page verbosity. Approved `tokens.json`, `--theme`, or an already resolved answer suppresses its own question.
4. Delegate extraction, figure reconstruction, content intent, authored design and retained assembly to the skill. `references/content-intent.md` owns the content brief and source-placeholder check; placeholders remain explicitly unresolved rather than invented. Save source inputs, figure worksheets, asset ledger, authored fragments, CSS, project tokens, source-to-page-to-slide/state mapping and resolved themes. New standalone design may be fresh; maintained handbook branding stays stable.
5. Run the skill's factual, functional, structural and semantic-visual checks. A structural-only score is not a production pass. Inspect every reading section and enabled slide/state, including source fidelity, viewport fit, motion, interaction, offline operation and final renamed-file behavior. Respect the logical-slide ceiling; never add slides or shrink text to hide overflow. Unavailable required rendering or exhausted repair budget remains a qualified non-pass.
6. Deliver the final HTML filename and minimal share list. Retain private source/model/assets/build/QA inputs separately, with a working source/output map. PPTX export is optional and runs through `pptx-generation` only when requested; do not delete source folders because HTML opens standalone.

## Option boundaries

- `--style` and the natural `using the style` form select design direction; `--theme` pins a palette or brand-token JSON. `--layout` selects the reading canvas. Presentation uses its own responsive compositions.
- `--presentation yes|no` selects inclusion. Explicit No wins over `--nav slides` and theme/depth flags. A theme or depth flag alone implies Yes. Non-interactive defaults are Yes, mixed themes and balanced depth; saved project policies and opt-outs take precedence.
- Legacy `--nav slides`, `as slides`, and `using slide navigation` include presentation with a migration note; `--nav scroll` binds reading start without opting out. Global Presentation Mode entry resets to slide 1; chapter targets remain separate. Existing single-mode HTML remains readable and scorable.
- `--mode auto|deck|report|compile` organizes sources. `--verbosity distilled|balanced|comprehensive` controls source-to-page coverage; `--presentation-depth` independently controls page-to-deck coverage. Comprehensive source intent binds deep-dive presentation unless an explicit conflicting choice is resolved. `--qa-depth` changes review scope, not content depth. Invalid values follow the shared usage-note/question-or-default behavior.
- `--images none|stock|ai|both` selects additional imagery. Procedural SVG/CSS remains the always-on baseline: the old none meant no visuals; current none means nothing added. Legacy `procedural` -> `none`, `auto`/`mix` -> `both`. Stock and LOCAL AI remain opt-in, stock preferred, with existing build-time consent and provenance requirements. Hosted generation is not used. Non-interactive output stays fully offline.
- `--interactivity restrained|balanced|rich|cinematic` preserves its current meaning. Cinematic remains opt-in and cost-gated; reduced motion is honored in both views. Supplied references, motion decisions, source ceilings and imagery boundaries survive retries.
- `--out` names the final artifact. If multiple input locations make the destination ambiguous, resolve that location before writing. Preserve user edits through the retained builder's ownership checks.

## Runtime helper manifest

All paths below are relative to the delegated `document-to-interactive-html` skill directory. Resolve that directory once and derive helper paths from it. Do not search for a helper by name or assume it lives beside this command.

| Helper | Path |
|---|---|
| Local extractor | `scripts/extract_content.py` |
| Presentation option resolver | `scripts/resolve_presentation.py` |
| Design sampler | `scripts/design_seed.py` |
| Consent-gated stock media | `scripts/fetch_stock_media.py` |
| Local AI images | `scripts/generate_local_image.py` |
| Map projection fitter | `scripts/fit_map_projection.py` |
| Render environment probe | `scripts/ensure_render_env.py` |
| Structural scorer | `scripts/visual_qa_score.py` |
| Retained assembly or legacy plain draft | `scripts/build_presentation.py` |

## Output

Output budget: everything produced in one reply, reasoning included, counts toward a single limit. Write the deliverable once in the output space; keep analysis focused on source understanding and composition. Start at the documented default effort and raise it only for a measured quality gain. This governs the deliverable, not tool logs; Output Minimization still applies to logs.

A rich-level proposal to use cinematic scroll-scrub must be confirmed after its size/cost estimate; it is never silently selected. Headless runs retain their documented offline fallback.

One offline `.html` containing the reading page and, unless explicitly disabled, its presentation. All runtime assets are embedded. A valid opt-out still runs page QA plus deck/CTA absence checks; other deck checks are N/A. Share requested final artifacts only, and keep editable sources and QA evidence available for regeneration.
