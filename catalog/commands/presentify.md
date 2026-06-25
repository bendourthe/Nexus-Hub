---
description: Turn one or more documents (PDF, Word, Excel, PowerPoint) into a SINGLE self-contained, offline, UNIQUE interactive website (not a static slide deck). Use to "presentify this", "turn this PowerPoint into an interactive website", "make an interactive site from these docs", "turn these documents into an interactive presentation", "convert this PDF/Word/Excel into an interactive website", "compile these documents into one interactive site". SKIP - generating a NEW document from scratch (use the *-generation skills), a one-off static chart, or a plain HTML page with no interactivity.
---

# /presentify Command

Turn existing documents into a single self-contained, offline, UNIQUE interactive website - not a static slide deck. One PowerPoint becomes a more interactive, more dynamic site that follows the same flow; one report (Word or PDF) becomes a navigable interactive site presenting it; several mixed documents compile into one attributed site. The output opens from a single file with zero external network requests, renders the source's real figures as INTERACTIVE charts (zoom, pan, filter series, adjust axes), carries a clear navigable structure, and uses a fresh bespoke design each run (or one you specify).

This is a thin entry point over the `document-to-interactive-html` skill. The full method (extract -> design -> author the interactive site -> verify), the per-format coverage, and the offline / anti-slop discipline live in that skill; this command resolves inputs and options, then delegates.

## Usage

```
/presentify <file-or-folder...> [--style <description>] [--theme <name-or-path>] [--out <path>] [--mode <auto|deck|report|compile>]
```

- **Inputs** (required): one or more files (`.pdf`, `.docx`, `.xlsx`, `.pptx`) or a folder containing them. A folder expands to its supported files sorted by name. Multiple inputs may mix formats freely.
- **`--style`** (optional): a style / color-scheme direction in plain words (e.g. `"dark, minimal"`, `"editorial, warm"`, `"high-contrast, playful"`, `"match brand #1a73e8"`). The site's design is bespoke each run; `--style` steers the look and feel. Omit it and the agent chooses a fitting design.
- **`--theme`** (optional): for an exact palette/brand, a curated `theme-tokens` theme name or a path to a theme / brand-token JSON (a `brand-styling` `tokens.json`). Ask the user for brand tokens before inventing colors; do not guess a brand.
- **`--out`** (optional): the output `.html` path. Defaults to a `.html` alongside the inputs (or alongside the folder for a folder input).
- **`--mode`** (optional): overrides the auto-detected mode (below). Defaults to `auto`.

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

The skill runs its workflow: detect inputs and mode -> run `scripts/extract_content.py` to the normalized content model -> choose a bespoke design (honoring `--style` / `--theme`, with `theme-tokens` / `brand-styling` for an exact brand) -> author a unique interactive website with dynamic, manipulable charts per the skill's `references/interactive-features.md` and `hallmark-design` (optionally starting from the `scripts/build_presentation.py` plain baseline) -> verify the output is self-contained, interactive, and opens offline with zero external requests per `html-output-conventions`.

Heavy logic stays in the `document-to-interactive-html` skill; this file only resolves inputs and options and delegates. Do not duplicate the extraction or build method here.

## Output

A single `.html` at `--out` (or alongside the inputs) - a navigable interactive website, not a slide deck. It is fully self-contained: all CSS and JS inline, images as base64, the source's real figures as interactive (zoom / pan / filter) charts built from inlined JS, and no external network requests. Confirm the output location with the user when it is ambiguous (for example, multiple input folders).

## Notes

- Local-only and private by construction: parsing runs on local libraries (lazy-imported, with a `pip install` hint when one is missing), HTML generation is the agent's own work, and no document leaves the machine.
- Out of scope for v1: scanned / image-only PDF OCR, video / audio embedding, and native PowerPoint / Word chart objects (deliver chartable data via an `.xlsx` input). See the skill's `references/extraction-runbook.md`.
