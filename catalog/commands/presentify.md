---
description: Turn one or more documents (PDF, Word, Excel, PowerPoint) into a SINGLE self-contained, offline, interactive HTML presentation. Use to "presentify this report", "turn this PowerPoint into an interactive presentation", "make an interactive HTML deck from these docs", "turn these documents into a presentation", "convert this PDF/Word/Excel into an interactive presentation", "compile these documents into one deck". SKIP - generating a NEW document from scratch (use the *-generation skills), a one-off static chart, or a plain HTML page with no presentation flow or interactivity.
---

# /presentify Command

Turn existing documents into a single self-contained, offline, interactive HTML presentation. One PowerPoint becomes a more interactive, more visually considered deck that follows the same flow; one report (Word or PDF) becomes a paced presentation OF that report; several mixed documents compile into one attributed deck. The output opens from a single file with zero external network requests, renders spreadsheet data as inline charts, and carries full navigation, an outline, progress, fullscreen, keyboard control, and reduced-motion support.

This is a thin entry point over the `document-to-interactive-html` skill. The full method (extract -> theme -> build -> enrichment -> verify), the per-format coverage, and the offline / anti-slop discipline live in that skill; this command resolves inputs and options, then delegates.

## Usage

```
/presentify <file-or-folder...> [--theme <name-or-path>] [--out <path>] [--mode <auto|deck|report|compile>]
```

- **Inputs** (required): one or more files (`.pdf`, `.docx`, `.xlsx`, `.pptx`) or a folder containing them. A folder expands to its supported files sorted by name. Multiple inputs may mix formats freely.
- **`--theme`** (optional): a curated `theme-tokens` theme name or a path to a theme / brand-token JSON (a `brand-styling` `tokens.json`). Defaults to the skill's bundled theme. Ask the user for brand tokens before inventing colors; do not guess a brand.
- **`--out`** (optional): the output `.html` path. Defaults to a `.html` alongside the inputs (or alongside the folder for a folder input).
- **`--mode`** (optional): overrides the auto-detected presentation mode (below). Defaults to `auto`.

## Modes (auto-detected, overridable)

The mode is inferred from the inputs and can be forced with `--mode`:

- **`deck`** - a single `.pptx`: **preserve the flow**. One slide maps to one section in slide order; keep that order, only make it more interactive and better designed. Do not re-sequence a deck the author already structured.
- **`report`** - a single `.docx` / `.pdf` / `.xlsx`: **present the report**. Synthesize a title and an agenda, one section per heading, and surface data as inline charts. This is where narrative restructuring does the most work.
- **`compile`** - two or more files (any mix), or a folder: **compile the sources**. Each source contributes a labeled run of sections introduced by a section-break, optionally preceded by a synthesized overview that names all sources. Preserve per-source attribution; do not blend two sources into an indistinguishable middle.

## Delegation

Dispatch to the skill, passing the resolved inputs, theme, output path, and mode through unchanged:

```
/presentify <inputs...> -> document-to-interactive-html (Instructions)
```

The skill runs its workflow: detect inputs and mode -> run `scripts/extract_content.py` to the normalized content model -> select the theme via `theme-tokens` / `brand-styling` -> run `scripts/build_presentation.py` for the deterministic baseline -> run the LLM enrichment pass per the skill's `references/interactive-features.md` and `hallmark-design` -> verify the output is self-contained and opens offline with zero external requests per `html-output-conventions`.

Heavy logic stays in the `document-to-interactive-html` skill; this file only resolves inputs and options and delegates. Do not duplicate the extraction or build method here.

## Output

A single `.html` at `--out` (or alongside the inputs). It is fully self-contained: all CSS and JS inline, images as base64, charts as inline SVG, and no external network requests. Confirm the output location with the user when it is ambiguous (for example, multiple input folders).

## Notes

- Local-only and private by construction: parsing runs on local libraries (lazy-imported, with a `pip install` hint when one is missing), HTML generation is the agent's own work, and no document leaves the machine.
- Out of scope for v1: scanned / image-only PDF OCR, video / audio embedding, and native PowerPoint / Word chart objects (deliver chartable data via an `.xlsx` input). See the skill's `references/extraction-runbook.md`.
