---
description: Turn one or more documents (PDF, Word, Excel, PowerPoint) into a SINGLE self-contained, offline, UNIQUE interactive website (not a static slide deck). Use to "presentify this", "turn this PowerPoint into an interactive website", "make an interactive site from these docs", "turn these documents into an interactive presentation", "convert this PDF/Word/Excel into an interactive website", "compile these documents into one interactive site". SKIP - generating a NEW document from scratch (use the *-generation skills), a one-off static chart, or a plain HTML page with no interactivity.
---

# /presentify Command

Turn existing documents into a single self-contained, offline, UNIQUE interactive website - not a static slide deck. One PowerPoint becomes a more interactive, more dynamic site that follows the same flow; one report (Word or PDF) becomes a navigable interactive site presenting it; several mixed documents compile into one attributed site. The output opens from a single file with zero external network requests, renders the source's real figures as INTERACTIVE charts (zoom, pan, filter series, adjust axes), carries a clear navigable structure, and uses a fresh, creative design every run that leads with uniqueness and interactivity rather than reusing one house look. When you do not name a style, the command asks you to choose a design direction first - three standard presets (Corporate & Professional, Creative & Expressive, Technical & Precise), a fourth "surprise me" option that lets the agent invent something unique for this run, and a fifth "other" to describe your own - then brainstorms concrete tokens for the chosen direction, announces it in one line, and authors to it. Name a style up front (`presentify <inputs> using the style <description>`, the natural form of `--style`) and it binds instead, skipping the menu; if the menu cannot be answered (a non-interactive run) the agent takes the creative/unique path automatically. Use `--theme` to pin an exact palette or brand.

This is a thin entry point over the `document-to-interactive-html` skill. The full method (extract -> design -> author the interactive site -> verify), the per-format coverage, and the offline / anti-slop discipline live in that skill; this command resolves inputs and options, then delegates.

## Usage

```
/presentify <file-or-folder...> [using the style <description> | --style <description>] [--theme <name-or-path>] [--out <path>] [--mode <auto|deck|report|compile>]
```

- **Inputs** (required): one or more files (`.pdf`, `.docx`, `.xlsx`, `.pptx`) or a folder containing them. A folder expands to its supported files sorted by name. Multiple inputs may mix formats freely.
- **`--style`** (optional): a style / color-scheme direction in plain words (e.g. `"dark, minimal"`, `"editorial, warm"`, `"high-contrast, playful"`, `"match brand #1a73e8"`). The natural-language form `using the style <description>` is equivalent. A named style binds the design and skips the menu below; the agent still brainstorms any axes the words leave open. Omit it and the command offers the design-direction menu instead.
- **`--theme`** (optional): for an exact palette/brand, a curated `theme-tokens` theme name or a path to a theme / brand-token JSON (a `brand-styling` `tokens.json`). Ask the user for brand tokens before inventing colors; do not guess a brand.
- **`--out`** (optional): the output `.html` path. Defaults to a `.html` alongside the inputs (or alongside the folder for a folder input).
- **`--mode`** (optional): overrides the auto-detected mode (below). Defaults to `auto`.

## Choosing the design (when no style is given)

When no style is named, `/presentify` resolves the design direction before authoring instead of silently picking one. It asks you to choose from five options:

1. **Corporate & Professional** - polished, restrained, business-ready.
2. **Creative & Expressive** - bold, artistic, unexpected.
3. **Technical & Precise** - clean, structured, data-forward.
4. **Surprise me** - the agent invents a unique, creative, interactive direction for this run.
5. **Other** - describe your own style (the same as naming a `--style`).

The agent then brainstorms concrete design tokens (palette, type, layout, motion) for the chosen direction, leading with creativity, interactivity, and uniqueness, and announces the committed direction in one line before it builds. The document's character informs the design but does not dictate it: a finance report is not mechanically forced into a corporate look. If the menu cannot be answered (a non-interactive or headless run), the agent falls back to "surprise me" and takes the creative/unique path automatically - it never blocks. A named `--style` / `using the style <description>` / `--theme` skips the menu entirely.

## Modes (auto-detected, overridable)

The mode is inferred from the inputs and can be forced with `--mode`:

- **`deck`** - a single `.pptx`: **preserve the flow**. Keep the source's content order, but render it as a navigable interactive site, more dynamic than the original. Do not re-sequence a deck the author already structured.
- **`report`** - a single `.docx` / `.pdf` / `.xlsx`: **present the source**. An overview, an intuitive section structure from the headings, and data surfaced as interactive charts. This is where structuring does the most work.
- **`compile`** - two or more files (any mix), or a folder: **compile the sources**. Each source becomes a labeled, attributed area of one site, optionally preceded by a synthesized overview that names all sources. Preserve per-source attribution; do not blend two sources into an indistinguishable middle.

## Delegation

Dispatch to the skill, passing the resolved inputs, theme, output path, and mode through unchanged:

```
/presentify <inputs...> -> document-to-interactive-html (Instructions)
```

The skill runs its workflow: detect inputs and mode -> run `scripts/extract_content.py` to the normalized content model -> resolve the design direction (a named `--style` / `using the style` / `--theme` binds; otherwise offer the five-option style menu and fall back to the creative/unique path if it cannot be answered), then brainstorm concrete design tokens for the chosen direction - leading with creativity, interactivity, and uniqueness, deliberately diverging from the default "AI-generated" look, using `theme-tokens` / `brand-styling` for an exact brand - and commit to it, announced in one line -> author a unique interactive website that uses the viewport width on purpose (the narrow reading measure is for body prose only, not a page-wide column) with dynamic, manipulable charts per the skill's `references/interactive-features.md` and `hallmark-design` (optionally starting from the `scripts/build_presentation.py` plain baseline) -> verify the output is self-contained, interactive, and opens offline with zero external requests per `html-output-conventions`.

Heavy logic stays in the `document-to-interactive-html` skill; this file only resolves inputs and options and delegates. Do not duplicate the extraction or build method here.

## Output

A single `.html` at `--out` (or alongside the inputs) - a navigable interactive website, not a slide deck. It is fully self-contained: all CSS and JS inline, images as base64, the source's real figures as interactive (zoom / pan / filter) charts built from inlined JS, and no external network requests. Confirm the output location with the user when it is ambiguous (for example, multiple input folders).

## Notes

- Local-only and private by construction: parsing runs on local libraries (lazy-imported, with a `pip install` hint when one is missing), HTML generation is the agent's own work, and no document leaves the machine.
- With no style named, the agent asks you to choose a design direction first (three standard presets, a "surprise me" creative option, or "other"), then brainstorms concrete tokens for it and announces the committed direction in one line before authoring; pass `--style` / `using the style <description>` / `--theme` to bind a direction and skip the menu. Each run leads with creativity, interactivity, and uniqueness and deliberately differs from the default dark / monospace-label / amber-accent / card-grid look, so outputs do not all look alike; the document's character informs the design but does not dictate it.
- The layout uses the window width on purpose: the narrow reading measure applies to body prose only, so headings and hero text are not trapped in a half-width column while cards or charts sit at full width.
- Out of scope for v1: scanned / image-only PDF OCR, video / audio embedding, and native PowerPoint / Word chart objects (deliver chartable data via an `.xlsx` input). See the skill's `references/extraction-runbook.md`.
