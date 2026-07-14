---
description: Turn one or more inputs - documents (PDF, Word, Excel, PowerPoint), source code and config, Markdown/text, CSV, standalone images, or a whole folder/repository - into a SINGLE self-contained, offline, UNIQUE interactive website (not a static slide deck). Use to "presentify this", "turn this PowerPoint into an interactive website", "make an interactive site from these docs", "turn this folder into an interactive site", "presentify this repo/codebase", "convert this PDF/Word/Excel into an interactive website", "compile these documents into one interactive site". SKIP - generating a NEW document from scratch (use the *-generation skills), a one-off static chart, or a plain HTML page with no interactivity.
---

# /presentify Command

Turn existing documents into a single self-contained, offline, UNIQUE interactive website - not a static slide deck. One PowerPoint becomes a more interactive, more dynamic site that follows the same flow; one report (Word or PDF) becomes a navigable interactive site presenting it; several mixed documents compile into one attributed site. The output opens from a single file with zero external network requests, renders the source's real figures as INTERACTIVE charts (zoom, pan, filter series, adjust axes), carries a clear navigable structure, and uses a fresh, creative design every run that leads with uniqueness and interactivity rather than reusing one house look. When you do not name a style, the command asks you to choose a design direction first - three standard presets (Corporate & Professional, Creative & Expressive, Technical & Precise), a fourth "surprise me" option that lets the agent invent something unique for this run, and a fifth "other" to describe your own - then brainstorms concrete tokens for the chosen direction, announces it in one line, and authors to it. Name a style up front (`presentify <inputs> using the style <description>`, the natural form of `--style`) and it binds instead, skipping the menu; if the menu cannot be answered (a non-interactive run) the agent takes the creative/unique path automatically. Use `--theme` to pin an exact palette or brand. After the style, the command asks for the output aspect - full-width (fills a 16:9 screen), standard webpage width, portrait, or your own - or bind it up front with `--layout`.

This is a thin entry point over the `document-to-interactive-html` skill. The full method (extract -> design -> author the interactive site -> verify), the per-format coverage, and the offline / anti-slop discipline live in that skill; this command resolves inputs and options, then delegates.

## Usage

```
/presentify <file-or-folder...> [using the style <description> | --style <description>] [--theme <name-or-path>] [--layout <full|standard|portrait|description>] [--out <path>] [--mode <auto|deck|report|compile>]
```

- **Inputs** (required): one or more files - documents (`.pdf`, `.docx`, `.xlsx`, `.pptx`), source code and config, Markdown / plain text, CSV / TSV, standalone images - or a directory / repository. A directory is walked RECURSIVELY (ignoring VCS / dependency / build directories and lockfiles, honoring a root `.gitignore` best-effort, skipping binaries, capped by `--max-files` and `--max-text-bytes`). A single directory input builds a repository site (a synthesized overview, a navigable file tree, README / docs first, and source code grouped by top-level directory). Multiple inputs may mix formats freely.
- **`--style`** (optional): a style / color-scheme direction in plain words (e.g. `"dark, minimal"`, `"editorial, warm"`, `"high-contrast, playful"`, `"match brand #1a73e8"`). The natural-language form `using the style <description>` is equivalent. A named style binds the design and skips the menu below; the agent still brainstorms any axes the words leave open. Omit it and the command offers the design-direction menu instead.
- **`--theme`** (optional): for an exact palette/brand, a curated `theme-tokens` theme name or a path to a theme / brand-token JSON (a `brand-styling` `tokens.json`). Ask the user for brand tokens before inventing colors; do not guess a brand.
- **`--layout`** (optional): the output aspect / canvas - one of `full` (fills a 16:9 screen edge to edge), `standard` (a typical centered webpage column), `portrait` (a tall, narrow, reading- / mobile-oriented canvas), or a free-text description (the natural form `using the layout <description>` is equivalent). A named layout binds the canvas and skips the aspect menu below. Omit it and the command offers the aspect menu after the style choice; in a non-interactive run it auto-picks by content (a deck defaults to `full`, a report / repository to `standard`).
- **`--out`** (optional): the output `.html` path. Defaults to a `.html` alongside the inputs (or alongside the folder for a folder input).
- **`--mode`** (optional): overrides the auto-detected mode (below). Defaults to `auto`.

## Choosing the design (when no style is given)

When no style is named, `/presentify` resolves the design direction before authoring instead of silently picking one. It asks you to choose from five options:

1. **Corporate & Professional** - polished, restrained, business-ready.
2. **Creative & Expressive** - bold, artistic, unexpected.
3. **Technical & Precise** - clean, structured, data-forward.
4. **Surprise me** - the agent invents a unique, creative, interactive direction for this run.
5. **Other** - describe your own style (the same as naming a `--style`).

The agent then rolls a seeded design brief from the skill's entropy sampler (`scripts/design_seed.py` - preset-constrained axis pools plus a persisted run history that pushes each run away from the last three, so choosing the same preset twice still yields a different palette, type voice, and layout) and adapts it into concrete design tokens for the chosen direction, leading with creativity, interactivity, and uniqueness, announcing the committed direction (with the roll's seed) in one line before it builds. The document's character informs the design but does not dictate it: a finance report is not mechanically forced into a corporate look. If the menu cannot be answered (a non-interactive or headless run), the agent falls back to "surprise me" and takes the creative/unique path automatically - it never blocks. A named `--style` / `using the style <description>` / `--theme` skips the menu entirely.

## Choosing the output aspect (when no layout is given)

After the style direction is resolved, `/presentify` resolves the output aspect - the shape of the page's canvas - the same way it resolves the style: it asks you to choose from four options.

1. **Full-width** - the site fills a 16:9 screen edge to edge, so opening it fullscreen occupies most of a typical widescreen display. Best for deck-like sources.
2. **Standard** - a typical centered webpage column width. Best for reports and repositories.
3. **Portrait** - a tall, narrow, reading- / mobile-oriented canvas. Best for long-form reading and phone-first delivery.
4. **Other** - describe your own need (the same as naming a `--layout <description>`).

The aspect governs the CSS canvas (page width, section bands, grid columns) and composes with the per-element width discipline and the design tokens; it never overrides them. If the menu cannot be answered (a non-interactive run), the agent auto-picks by content - a deck-like source defaults to full-width, a report / repository / text-dominant source to standard - and records the choice. A named `--layout` / `using the layout <description>` skips the aspect menu entirely.

## Modes (auto-detected, overridable)

The mode is inferred from the inputs and can be forced with `--mode`:

- **`deck`** - a single `.pptx`: **preserve the flow**. Keep the source's content order, but render it as a navigable interactive site, more dynamic than the original. Do not re-sequence a deck the author already structured.
- **`report`** - a single `.docx` / `.pdf` / `.xlsx`: **present the source**. An overview, an intuitive section structure from the headings, and data surfaced as interactive charts. This is where structuring does the most work.
- **`compile`** - two or more files (any mix), or a folder: **compile the sources**. Each source becomes a labeled, attributed area of one site, optionally preceded by a synthesized overview that names all sources. Preserve per-source attribution; do not blend two sources into an indistinguishable middle.
- **`project` / repository** (a single directory input): a specialization of `compile` for a codebase or mixed folder. The extractor walks the tree recursively and emits a synthesized `overview` section plus a `tree`; the site leads with the overview and a navigable file tree, then README / docs, then source code grouped by top-level directory (rendered as offline-highlighted code sections), then data (CSV as interactive charts / tables) and standalone images. Use it to turn a whole repo into one navigable interactive site.

## Delegation

Dispatch to the skill, passing the resolved inputs, theme, output path, and mode through unchanged:

```
/presentify <inputs...> -> document-to-interactive-html (Instructions)
```

The skill runs its workflow: detect inputs and mode -> run `scripts/extract_content.py` to the normalized content model (documents, source code / config, Markdown / text, CSV / TSV, standalone images, or a directory / repository walked recursively into a synthesized overview + file tree + grouped content) -> classify and faithfully reconstruct figures per the skill's `references/figure-reconstruction.md` (every image block classified; data-bearing figures get a read-the-figure worksheet, fidelity cross-checks, and a confidence gate - reconstructions carry provenance, a view-original toggle, and truthful numbers, while low-confidence figures ship as enhanced originals; scanned-page OCR text is verified against the page image) -> resolve the design direction (a named `--style` / `using the style` / `--theme` binds; otherwise offer the five-option style menu and fall back to the creative/unique path if it cannot be answered), then brainstorm concrete design tokens for the chosen direction - leading with creativity, interactivity, and uniqueness, deliberately diverging from the default "AI-generated" look, using `theme-tokens` / `brand-styling` for an exact brand - and commit to it, announced in one line -> resolve the output aspect (a named `--layout` binds; otherwise the aspect menu, with a content-aware non-interactive fallback) -> author a unique interactive website that uses the viewport width on purpose (the narrow reading measure is for body prose only, not a page-wide column), builds to the resolved aspect with a spacing/density discipline that avoids dead half-empty screens, preserves each visual's source prominence (a dominant figure stays a hero, not a thumbnail), with dynamic, manipulable charts AND the site-wide interaction layer's five-point minimum budget (active-state nav, scroll reveals, hover/focus affordances, lightboxes on every non-decorative image, one signature interaction) per the skill's `references/interactive-features.md` and `hallmark-design` (optionally starting from the `scripts/build_presentation.py` plain baseline) -> verify the output is self-contained, interactive, and opens offline with zero external requests per `html-output-conventions` -> run a post-generation visual-QA loop (render the page in a headless browser, screenshot key states, read the screenshots back to catch graphic defects such as overflowing tables, unreadable text, broken charts, or layout breakage, then fix and re-render until clean), delegating the render / screenshot to `browser-testing-with-devtools` and degrading gracefully to a static structural review when no headless browser is available.

Heavy logic stays in the `document-to-interactive-html` skill; this file only resolves inputs and options and delegates. Do not duplicate the extraction or build method here.

## Output

A single `.html` at `--out` (or alongside the inputs) - a navigable interactive website, not a slide deck. It is fully self-contained: all CSS and JS inline, images as base64, the source's real figures as interactive (zoom / pan / filter) charts built from inlined JS, and no external network requests. Confirm the output location with the user when it is ambiguous (for example, multiple input folders).

## Notes

- Local-only and private by construction: parsing runs on local libraries (lazy-imported, with a `pip install` hint when one is missing), HTML generation is the agent's own work, and no document leaves the machine.
- With no style named, the agent asks you to choose a design direction first (three standard presets, a "surprise me" creative option, or "other"), then brainstorms concrete tokens for it and announces the committed direction in one line before authoring; pass `--style` / `using the style <description>` / `--theme` to bind a direction and skip the menu. Each run leads with creativity, interactivity, and uniqueness and deliberately differs from the default dark / monospace-label / amber-accent / card-grid look, so outputs do not all look alike; the document's character informs the design but does not dictate it.
- The layout uses the window width on purpose: the narrow reading measure applies to body prose only, so headings and hero text are not trapped in a half-width column while cards or charts sit at full width. The output aspect (`--layout` or the aspect menu) sets the canvas - full-width / standard / portrait / other - and the site holds a vertical-density discipline so sections are sized to content with no dead, half-empty screens.
- Prominence is preserved: a visual that dominated its source (a large photo on a slide, the single figure on a page) stays a hero at native resolution rather than being flattened into a uniform thumbnail grid; only genuinely-secondary visuals are grouped.
- Supported inputs: documents (PDF / Word / Excel / PowerPoint, including scanned-PDF reading via local OCR + agent-vision fallback, PDF image and vector-figure extraction, and native PowerPoint / Word chart objects), source code and config, Markdown / plain text, CSV / TSV, standalone images, and whole directories / repositories (walked recursively). Out of scope: video / audio embedding. See the skill's `references/extraction-runbook.md`.
