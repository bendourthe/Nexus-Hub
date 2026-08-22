# Plan -- /presentify + document-to-interactive-html (documents to a self-contained interactive HTML presentation)

**Project**: Nexus-Hub
**Version**: v3.9.0
**Slug**: presentify-interactive-html
**Plan Type**: Feature / NEW skill + command (specialized-domains; local-first parsing + LLM-native HTML; self-contained single-file output)
**Created**: 2026-06-24
**Goal**: Add a `/presentify` command backed by a new `document-to-interactive-html` skill that ingests one OR many source documents in any mix of formats (PDF, Word .docx, Excel .xlsx, PowerPoint .pptx) and synthesizes a SINGLE self-contained, offline, interactive, captivating HTML presentation -- a single PPTX becomes a far more visually appealing and interactive deck that follows the same flow, a single report becomes a presentation OF that report, and multiple/mixed documents become one presentation compiling all sources -- using local-only parsing and LLM-native HTML generation, composing existing extraction and design skills, with zero new outbound call, generation-as-service, scraping-as-service, or credential.

## Overview

This plan delivers a genuine catalog gap: Nexus-Hub already has the pieces to READ each document format (`pptx-generation`, `docx-generation`, `xlsx-generation`, `pdf-document-generation`, plus the Anthropic `docx`/`pdf`/`pptx`/`xlsx` skills) and the pieces to BUILD captivating self-contained HTML (`html-output-conventions`, `hallmark-design`, `theme-tokens`, `brand-styling`, the `generative-art` viewer pattern, the `guides/website/nexus-hub-guide.html` reference implementation), but nothing that connects ingestion to an interactive-presentation output. `document-to-interactive-html` is that connector, and `/presentify` is its entry point.

The architecture is deliberately COMPOSITIONAL, not a reinvention. Parsing reuses the document-extraction capability the existing format skills already teach; theming reuses `theme-tokens` + `brand-styling`; the design bar is the `hallmark-design` anti-"looks-AI-generated" discipline; the output discipline is `html-output-conventions` (one self-contained file, all CSS/JS inlined, works offline). The skill's unique value is (1) a normalized content model that extraction across four formats maps into, (2) a reusable interactive-presentation HTML template plus a deterministic baseline builder, and (3) the method for elevating that baseline into a captivating, interactive deck.

This feature is local-first by construction and therefore clean against the AGENTS.md MCP Registry Policy decision tree: document parsing runs on LOCAL libraries (`python-pptx`, `python-docx`, `openpyxl`/`pandas`, `pdfplumber` or `pypdf`), lazy-imported with a clear `pip install` hint on `ImportError`; HTML generation is LLM-native (the agent authors the HTML, guided by the bundled template); no document, prompt, or query text ever leaves the machine; and there is no external/SaaS call, no generation-as-service, and no scraping-as-service. That posture is also exactly what a confidential report or internal spreadsheet requires.

Delivery is one new skill folder (`catalog/skills/specialized-domains/document-to-interactive-html/`) with a Tier-3 bundle (`scripts/`, `references/`, `assets/`), one new command (`catalog/commands/presentify.md`), the three catalog registries, and the CLAUDE.md / AGENTS.md skill-index rows + headline counts. Phasing is by cohesion so the executable bundle (extraction, then template/builder) is built before the SKILL.md that must reference every bundled file (the orphan-bundle audit forces this order), then the command + registration, then a worked-example verification + the full validator chain.

Success looks like: `/presentify <file...>` (or a folder) produces a single `.html` that opens offline with zero external requests, follows the source flow for a single deck or presents/compiles a report or multi-source set, carries section/slide navigation + an outline + progress + fullscreen + keyboard control + reduced-motion support, renders spreadsheet data as inline SVG/canvas charts, and clears the `hallmark-design` anti-slop bar; the skill is conformant (pushy description with verbatim trigger phrases and a SKIP clause, quoted `summary_l0` <= 15 words and `overview_l1` <= 150 words, all required body sections in order, body <= 500 lines with overflow in `references/`, every bundle file referenced); the command is pushy and scoped; the three registries plus the CLAUDE.md / AGENTS.md index rows and headline counts are updated and consistent; the full validator chain (`make validate`, `make lint`, `make test`) is green and a sample output passes a self-contained-HTML well-formedness + offline check; CHANGELOG `## [Unreleased]` and `docs/v3/v3.9/known-gaps.md` are updated; all content is ASCII-only and conformant to the Markdown style guide; and the Reverse-Engineering Attribution Rule holds (generic naming; no upstream product names in any distributed artifact).

## Constitution Check

*GATE: Must pass before Phase 1. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.9/constitution.md` or repo root - skipping the formal check (informational, not blocking; `/constitution` can establish project principles later). The plan is nonetheless aligned with the standing governance that functions as Nexus-Hub's de-facto constitution (the `AGENTS.md` MCP Registry Policy, the Reverse-Engineering Attribution Rule, and the three-tier skill-loading + skill-authoring norms): the feature is a tier-1/tier-2 capability (local-only parsing + LLM-native generation), so it does not touch the "generation-as-service" / "scraping-as-service" hard-no list; it introduces no outbound call, no SaaS dependency, and no credential; heavy logic ships in the Tier-3 bundle so the SKILL.md body stays under the 500-line norm; and all distributed content uses generic descriptive naming. The single dependency consideration -- the local parsing libraries -- is handled by lazy import with a `pip install` hint, matching the precedent set by the existing `*-generation` skills, so it adds no hard install-time requirement to the catalog.

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Local multi-format extraction | A normalized content-model schema (`references/content-model.md`) and a local, lazy-import extractor (`scripts/extract_content.py`) that maps PDF / Word / Excel / PowerPoint -- single or multi-file -- into that model, plus an extraction runbook | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 2 | Self-contained interactive HTML template + builder | A reusable offline presentation template (`assets/presentation-template.html` + `assets/theme.json`), a deterministic baseline builder (`scripts/build_presentation.py`) that inlines content + base64 images + inline SVG/canvas charts, and the interactive-feature + enrichment design spec (`references/interactive-features.md`) | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 3 | SKILL.md, command, and registration | Conformant `SKILL.md` (pushy description, quoted summaries, required sections, references every bundle file), `catalog/commands/presentify.md`, the three registries, and the CLAUDE.md / AGENTS.md index rows + headline counts | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |
| 4 | Worked example, validation, docs | A sample run (a sample PPTX and a sample report) verifying the captivating-and-interactive bar offline, the full validator chain green, CHANGELOG `## [Unreleased]` + `docs/v3/v3.9/known-gaps.md` updated | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |

The "Rec. model / effort" column is a best-effort planning-time assessment, recorded as platform-agnostic tier intent plus the concretely-enumerated Claude Code model (the session model, Opus 4.8). Live model re-enumeration is deferred to implementation time; `/implement` re-confirms each phase's recommendation against the then-current live model set before building, and may upshift effort if a phase's checks fail repeatedly.

## Phase 1: Local multi-format extraction

**Goal**: Define a normalized content model and a local, lazy-import extractor that turns any single document or mix of documents (PDF, .docx, .xlsx, .pptx) into that model, preserving structure (sections, headings, prose, nested bullets, tables), chartable data series from spreadsheets, images, speaker notes, and per-source attribution + ordering for the multi-file case.
**Prerequisites**: None.
**Stability Gate**: `references/content-model.md` defines the schema; `scripts/extract_content.py` dispatches by extension, extracts each supported format, merges multi-file input with a source manifest, lazy-imports every parser with a `pip install` hint on `ImportError`, and emits content-model JSON that validates against the schema; the extraction runbook documents per-format coverage and gotchas; no parser is imported at module top level (so a missing library degrades to a clear message, not a crash); validators green.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: robust extraction across four heterogeneous formats with messy real-world inputs (merged cells, nested lists, multi-column PDFs, embedded images, speaker notes) plus a clean normalized schema is error-prone design work; silent data loss and a schema that cannot represent a real report are the high-risk failure modes. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 1.1 -- Define the normalized content-model schema

**Objective**: Specify the intermediate representation every format maps into, so the builder in Phase 2 has one stable contract regardless of source format or count.

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/references/content-model.md`. Define a JSON schema (described in prose + a commented JSON example, not a runtime dependency) for a normalized "presentation content model" that any of the four source formats maps into. Required shape: a top-level object with `title`, `sources` (an ordered list of `{path, format, title}` for attribution and multi-file ordering), and `sections` (an ordered list). Each section has a `heading`, an optional `subheading`, a `kind` (one of `title`, `content`, `section-break`, `data`, `quote`, `image`, `appendix`), and a `blocks` list. A block is one of: `paragraph` (text), `bullets` (nested list items with depth), `table` (header row + rows), `image` (a reference plus alt text -- see 1.2 for how bytes are carried), `chart` (a typed data series: `{chart_type_hint, categories, series:[{name, values}]}` derived from spreadsheet ranges), `code`, `quote`, or `notes` (speaker notes, hidden by default in the output). Define how a single PPTX maps (one section per slide, slide notes -> `notes`, preserving slide order = "follows the same flow"), how a report (PDF/Word) maps (headings -> sections, body -> paragraphs/bullets/tables, a generated agenda/section-break set = "a presentation OF the report"), and how multi-file input merges (each source contributes a labeled run of sections in input order, with an optional synthesized overview section). Apply the Reverse-Engineering Attribution Rule (generic naming). Constraints: ASCII-only; follow `catalog/style-guides/markdown.md`. Acceptance: the schema covers all block kinds above, specifies the per-format mapping and the multi-file merge, and is self-contained enough that 1.2 can implement against it without further design.

#### 1.2 -- Implement the local extractor (`scripts/extract_content.py`)

**Objective**: Build the cross-platform Python extractor that produces content-model JSON from one or more input files, using only local libraries, lazy-imported.

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/scripts/extract_content.py` (a single cross-platform `.py`, so no `.sh`/`.ps1` parity files are needed). It accepts one or more input paths (files or a folder) and an output JSON path, dispatches by file extension, and emits the content model from 1.1. Per-format extractors: `.pptx` via `python-pptx` (slides -> sections, shapes/text frames -> blocks, tables -> table blocks, notes slides -> `notes`, embedded images -> image blocks); `.docx` via `python-docx` (heading styles -> section boundaries, paragraphs/lists -> paragraph/bullets, tables -> table blocks, inline images -> image blocks); `.xlsx` via `openpyxl` (or `pandas` if already needed) (sheets -> sections, contiguous numeric ranges -> `chart` data-series blocks with a `chart_type_hint`, other ranges -> table blocks); `.pdf` via `pdfplumber` (preferred for layout/tables) or `pypdf` fallback (pages/headings -> sections, text -> paragraphs, detected tables -> table blocks). CRITICAL: import every third-party parser LAZILY inside the function that needs it, wrapped so an `ImportError` prints `Error: <lib> not installed. Please run: pip install <lib>` and exits non-zero (model after `scripts/generate_report.py`); never import a parser at module top level. Images: extract bytes and carry them as base64 data URIs in the image block (so the final HTML is self-contained) with a size guard (downscale or warn above a configurable byte budget). Multi-file: process inputs in the given order, tag each section with its source, and emit one merged model with the `sources` manifest. Provide `--help`, deterministic output (stable ordering), and clear stderr diagnostics. Constraints: follow `catalog/rules/python/` (type hints, `ruff`-clean style, no bare `except`); ASCII-only source; no network call of any kind. Acceptance: running the script against a sample of each format yields content-model JSON that validates against 1.1; a missing library produces the documented `pip install` message and a non-zero exit, not a traceback; multi-file input merges in order with correct per-source attribution.

#### 1.3 -- Write the extraction runbook (`references/extraction-runbook.md`)

**Objective**: Document what each format extractor does and does not capture, so the SKILL.md body can link to it instead of inlining it (Tier-3 discipline).

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/references/extraction-runbook.md`. Document, per format (.pptx/.docx/.xlsx/.pdf): which library is used and the `pip install` line, what maps to which content-model block, known gotchas (PDF multi-column flow, scanned/image-only PDFs needing OCR which is OUT of scope, merged Excel cells, PowerPoint grouped shapes, embedded vs linked images), the image base64 size budget and how to tune it, and the deterministic-ordering guarantees. Include a short "multi-file" subsection on ordering and the synthesized overview. State explicitly that scanned-PDF OCR and video/audio embedding are out of scope for v1. Constraints: ASCII-only; Markdown style guide; this file MUST be referenced from SKILL.md in Phase 3 (orphan-bundle audit). Acceptance: every format the extractor supports has a runbook subsection with library, mapping, gotchas, and the out-of-scope note.

#### 1.4 -- Testing and stabilization

**Objective**: Validate the Phase 1 extractor against real sample files and iterate until stable.

**Prompt**:
> Validate Phase 1. Create or obtain a tiny sample of each format (a 3-slide `.pptx`, a 2-page `.docx` report, a 1-sheet `.xlsx` with a numeric range, a short `.pdf`) under a scratch fixtures path (NOT inside the distributed skill bundle's `assets/` -- keep demo inputs out of the catalog; use a `docs/v3/v3.9/development/` fixtures area or a temp dir). Run `extract_content.py` on each individually and on a mixed multi-file set; confirm: (1) output validates against the `references/content-model.md` schema; (2) slide order is preserved for the PPTX (the "same flow" guarantee); (3) the XLSX numeric range becomes a `chart` block; (4) images arrive as base64 data URIs within the size budget; (5) a deliberately-uninstalled library yields the `pip install` message and non-zero exit, not a traceback; (6) multi-file attribution + ordering are correct. Run `ruff check` on the script if available. Fix any failure and re-run until stable. Then run `/session history` to document Phase 1.

---

## Phase 2: Self-contained interactive HTML template + builder

**Goal**: Build the reusable, offline, single-file presentation template and a deterministic baseline builder that injects the content model into it (inlining CSS/JS, base64 images, and inline SVG/canvas charts), plus the design spec that defines the interactive feature set and the LLM enrichment pass that takes the baseline to "captivating".
**Prerequisites**: Phase 1 complete (the builder consumes the content model).
**Stability Gate**: `assets/presentation-template.html` is a self-contained scaffold (all CSS/JS inline, zero external requests) with section/slide navigation, an outline panel, progress, fullscreen, keyboard control, transitions, reduced-motion support, and responsive layout; `assets/theme.json` defines default tokens with a documented `theme-tokens`/`brand-styling` override hook; `scripts/build_presentation.py` turns a content-model JSON into one `.html` that opens offline with no external requests and renders charts inline; `references/interactive-features.md` specifies the feature catalog and the enrichment pass; a baseline build of a sample model opens offline and is well-formed; validators green.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: this is the captivating-and-interactive core -- a bespoke self-contained design system, inline charting, and an explicit anti-"looks-AI-generated" bar -- where slop output and an accidental external dependency (a CDN font/script that breaks offline) are the high-risk failure modes; it must hold the `html-output-conventions` self-contained discipline and the `hallmark-design` gates. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 2.1 -- Build the self-contained presentation template (`assets/presentation-template.html`)

**Objective**: Author the reusable offline scaffold the builder populates, holding the design system and all interactivity, with zero external dependencies.

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/assets/presentation-template.html`. It is a single self-contained HTML file (the `guides/website/nexus-hub-guide.html` and `generative-art` viewer pattern): all CSS in a `<style>` block, all JS in a `<script>` block, NO external network requests (no CDN fonts/scripts/styles -- use system font stacks). Include: a design-token CSS `:root` block (palette, type scale, spacing, radius) driven from a small inlined config object so a theme can be swapped; a section/slide model (each section a block toggled active); navigation (on-screen prev/next, keyboard arrows, an outline panel that jumps to any section, a progress indicator, a fullscreen control); slide transitions with a `prefers-reduced-motion` guard; responsive layout for projector + laptop + mobile; a print-friendly path; and clearly-marked content-injection placeholders the builder replaces. Follow `html-output-conventions` (self-contained discipline) and `hallmark-design` (avoid the templated/AI-generated look: intentional type, spacing, and motion; the four-verbs gate). Apply the Reverse-Engineering Attribution Rule. Constraints: ASCII-only; offline-only (a grep for `http://`/`https://`/`cdn` in the asset must be empty except in comments); this file MUST be referenced from SKILL.md in Phase 3. Acceptance: the template opens standalone in a browser with no network, the nav/outline/progress/fullscreen/keyboard controls work, reduced-motion is honored, and there are clearly-named injection placeholders.

#### 2.2 -- Define the theme tokens and brand override hook (`assets/theme.json`)

**Objective**: Provide a default theme and a documented path to override it from `theme-tokens` / `brand-styling`.

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/assets/theme.json` holding the default presentation theme tokens (palette, font stacks, type scale, spacing, accent, dark/light intent) consumed by the template's config object. Document (in the file's header comment or in `references/interactive-features.md`) how a caller supplies an alternate theme: by selecting a curated set via `[[theme-tokens]]` or by supplying brand tokens via `[[brand-styling]]` (a per-brand token JSON), which the builder merges over the default. Keep the schema small and obvious. Constraints: ASCII-only; valid JSON; this file MUST be referenced from SKILL.md. Acceptance: `theme.json` is valid JSON, covers the tokens the template reads, and the override path via theme-tokens/brand-styling is documented.

#### 2.3 -- Implement the baseline builder (`scripts/build_presentation.py`)

**Objective**: Deterministically turn a content-model JSON into one self-contained `.html` by populating the template, inlining images as base64 and spreadsheet data as inline charts.

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/scripts/build_presentation.py` (single cross-platform `.py`). Inputs: a content-model JSON (from Phase 1), the template (`assets/presentation-template.html`), an optional theme JSON (default `assets/theme.json`, overridable), and an output `.html` path. It maps each content-model section to a template section, renders each block kind (paragraph, nested bullets, table, base64 image, quote, code, hidden speaker notes), and renders `chart` blocks as INLINE SVG (or canvas) drawn from the data series -- no charting library, no CDN -- supporting at least bar, line, and pie/doughnut via the `chart_type_hint`. It merges the theme over the template defaults and writes ONE self-contained `.html` with everything inlined. No standard-library-only stance is required, but it MUST make no network call and add no external reference to the output. Provide `--help`, deterministic output, and a post-write self-check that fails if the output contains an external `http(s)`/`cdn` reference. Constraints: follow `catalog/rules/python/`; ASCII-only source; the output HTML opens offline. Acceptance: building a sample content model produces a single `.html` that opens with no network requests, renders an XLSX-derived series as an inline chart, shows base64 images, and passes the no-external-reference self-check.

#### 2.4 -- Write the interactive-features + enrichment design spec (`references/interactive-features.md`)

**Objective**: Catalog the interactive features and define the LLM enrichment pass that elevates the deterministic baseline to a captivating deck (the part that is LLM-native, not scripted).

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/references/interactive-features.md`. Document the interactive feature catalog (navigation model, outline, progress, fullscreen, keyboard map, transitions, reduced-motion, responsive/projector modes, inline chart types and when to use each, speaker-notes handling, print/PDF path) and the THEME override path (theme-tokens / brand-styling). Then define the "enrichment pass": the deterministic builder produces a correct, plain baseline; the agent then elevates it to captivating per `hallmark-design` -- choosing a narrative section structure (especially turning a dense report into an agenda + paced reveals), tightening copy into presentation-grade phrasing, picking the right chart per data shape, adding intentional emphasis/motion, and running the hallmark-design anti-slop gates -- WITHOUT introducing any external dependency or breaking the offline guarantee. State the decision rule for single-deck "preserve the flow" vs report "present the report" vs multi-file "compile the sources". Apply the Reverse-Engineering Attribution Rule. Constraints: ASCII-only; Markdown style guide; this file MUST be referenced from SKILL.md. Acceptance: the feature catalog, the theme-override path, and the enrichment pass (tied to hallmark-design and the three input modes) are all documented.

#### 2.5 -- Testing and stabilization

**Objective**: Build a sample presentation end-to-end (extract -> build) and verify the offline + interactivity + well-formedness bar.

**Prompt**:
> Validate Phase 2. Using a Phase 1 sample content model, run `build_presentation.py` to produce a sample `.html`. Confirm: (1) it opens in a browser with NO network requests (check devtools network or grep the file for external `http(s)`/`cdn` references -- expect none outside comments); (2) navigation, outline, progress, fullscreen, keyboard arrows, and reduced-motion all work; (3) an XLSX-derived series renders as an inline chart; (4) base64 images display; (5) the HTML is well-formed (tag balance) and ASCII-safe; (6) the builder's no-external-reference self-check passes. Spot-check the output against the `hallmark-design` gates (does it read as intentional, not templated?). Fix any failure and re-run until stable. Then run `/session history` to document Phase 2.

---

## Phase 3: SKILL.md, command, and registration

**Goal**: Author the conformant SKILL.md (referencing every bundle file so the orphan-bundle audit passes), the pushy `/presentify` command, and the full registration surface (the three registries plus the CLAUDE.md / AGENTS.md index rows and headline counts).
**Prerequisites**: Phases 1 and 2 complete (SKILL.md must reference the existing `scripts/`, `references/`, `assets/` files).
**Stability Gate**: `SKILL.md` exists with a pushy description (verbatim trigger phrases + a SKIP clause), quoted `summary_l0` (<= 15 words) and `overview_l1` (<= 150 words), the required body sections in order (intro, When to Use + When NOT, Instructions, Common Rationalizations table, binary Verification checklist, Related Skills), a body under 500 lines (overflow already in `references/`), and a reference to every file under `scripts/`/`references/`/`assets/`; `catalog/commands/presentify.md` exists and is pushy; the three registries and the CLAUDE.md / AGENTS.md index rows + headline counts are updated and consistent; `make validate` (JSON integrity + orphan-bundle audit) is green.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: authoring against a known contract plus careful but mechanical JSON-registry edits; the failure modes (a non-conformant description that under-triggers, an orphan bundle file, a count mismatch across registries) are caught by validators, so medium effort on the strong tier per the no-degradation default. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 3.1 -- Author SKILL.md

**Objective**: Write the conformant, pushy SKILL.md that teaches the method and references the whole bundle.

**Prompt**:
> Create `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md`. Frontmatter: `name: document-to-interactive-html`; a PUSHY `description` (first sentence states the action; second lists verbatim trigger phrases -- "turn this PowerPoint into an interactive presentation", "make an interactive HTML deck from these docs", "presentify this report", "turn these documents into a presentation", "convert this PDF/Word/Excel into an interactive presentation"; third is a SKIP clause -- e.g. SKIP: generating a NEW .pptx/.docx (use the `*-generation` skills), one-off static charts, or a plain HTML doc with no presentation/interactivity); `summary_l0` (quoted, <= 15 words, e.g. "Turn one or more documents into a self-contained interactive HTML presentation"); `overview_l1` (quoted, <= 150 words). Body sections IN ORDER: a brief intro; "When to Use This Skill" with an explicit "When NOT to use"; "Instructions" (a numbered workflow: detect inputs -> run `scripts/extract_content.py` to the content model -> select theme via `[[theme-tokens]]`/`[[brand-styling]]` -> run `scripts/build_presentation.py` for the baseline -> run the enrichment pass per `references/interactive-features.md` and `[[hallmark-design]]` -> verify offline + self-contained per `[[html-output-conventions]]`; cover the three modes: single deck preserves flow, single report becomes a presentation, multi-file compiles sources); "Common Rationalizations" (a table whose rows cite concrete failure modes -- e.g. "I'll just inline a CDN chart library" -> breaks the offline guarantee; "I'll skip extraction and eyeball the PDF" -> loses tables and data; "the baseline render is fine" -> fails the hallmark-design bar); "Verification" (a BINARY checklist of observable artifacts: the `.html` exists at the output path, opens with zero network requests, every source section is represented, charts render inline, `make validate` passes); "Related Skills" (cross-link `[[pptx-generation]]`, `[[docx-generation]]`, `[[xlsx-generation]]`, `[[pdf-document-generation]]`, `[[html-output-conventions]]`, `[[hallmark-design]]`, `[[theme-tokens]]`, `[[brand-styling]]`). Reference EVERY bundle file (`scripts/extract_content.py`, `scripts/build_presentation.py`, `references/content-model.md`, `references/extraction-runbook.md`, `references/interactive-features.md`, `assets/presentation-template.html`, `assets/theme.json`) so the orphan-bundle audit passes. Keep the body under 500 lines (push detail to the existing references). Constraints: ASCII-only; Markdown style guide; Reverse-Engineering Attribution Rule. Acceptance: frontmatter fields present and within limits; all required sections in order; every bundle file referenced; body < 500 lines.

#### 3.2 -- Author the `/presentify` command

**Objective**: Write the pushy command entry point that scopes inputs and options and delegates to the skill.

**Prompt**:
> Create `catalog/commands/presentify.md` (no frontmatter needed; same authoring conventions as other commands). Make the description pushy with the same trigger surface as the skill. Define usage: `/presentify <file-or-folder...>` accepting one or more PDFs/.docx/.xlsx/.pptx (or a folder), with options for theme/brand (a theme-tokens set name or a brand-token JSON path), an output path (default alongside the inputs), and a single-deck "preserve flow" vs report/compile intent that is auto-detected but overridable. The body delegates to the `document-to-interactive-html` skill's Instructions and states the three modes (single deck, single report, multi-file compile). If a style-guide companion is warranted, place it at `catalog/style-guides/presentify.md` (NOT in `catalog/commands/`, or it surfaces as a slash command) and reference it; otherwise omit. Constraints: ASCII-only; Markdown style guide. Acceptance: the command file exists, is pushy, documents single + multi-file + folder inputs and the theme/output options, and delegates to the skill rather than duplicating the method.

#### 3.3 -- Update the registries and index rows

**Objective**: Register the new skill and command across every required surface, keeping counts consistent.

**Prompt**:
> Register the new skill and command. (1) `data/SKILL_INDEX.md`: add a row `| document-to-interactive-html | specialized-domains | "<summary_l0>" | catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md |`. (2) `data/skills.json`: add an entry following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category `specialized-domains`, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security scores defaulting 100/100/95). (3) `data/marketplace.json`: increment the `specialized-domains` category `skill_count` by 1, increment `statistics.total_skills` by 1, and increment `total_commands` by 1 if that field exists. (4) Headline counts: read the CURRENT canonical skill count (from `data/skills.json`) and command count, then bump the prose in `README.md`, `AGENTS.md`, and the CLAUDE.md skill-index header (currently "256 skills" -> 257 and "15 commands" -> 16, but confirm against the actual current values first), and add the new skill's row to the skill-index table in CLAUDE.md and AGENTS.md (note: the CLAUDE.md tables are user-global instruction copies; update the project AGENTS.md skill index and the data/SKILL_INDEX.md, which are the authoritative repo surfaces). Do NOT hand-edit any other `data/` file. Constraints: ASCII-only; valid JSON (no trailing commas). Acceptance: all four registry/index surfaces include the new skill; `marketplace.json` counts are incremented; the new command is reflected in any command count; JSON remains valid.

#### 3.4 -- Testing and stabilization

**Objective**: Validate the authoring + registration and iterate until green.

**Prompt**:
> Validate Phase 3. Run `make validate` (or the Windows fallback `python scripts/validate_skills.py --verbose`) and confirm: (1) JSON catalog integrity passes; (2) the orphan-bundle audit is clean -- every file under the skill's `scripts/`/`references/`/`assets/` is referenced from SKILL.md; (3) the new skill resolves in `data/skills.json` / `data/SKILL_INDEX.md` and the `marketplace.json` counts match; (4) the dangling-wikilink audit passes (all `[[...]]` Related Skills resolve); (5) `summary_l0` <= 15 words and `overview_l1` <= 150 words; (6) the SKILL.md body is under 500 lines; (7) all added content is ASCII-only. Run `make lint` (ShellCheck -- no shell scripts were added, so this should be a no-op pass). Fix any failure and re-run until green. Then run `/session history` to document Phase 3.

---

## Phase 4: Worked example, validation, and docs

**Goal**: Prove the captivating-and-interactive bar end-to-end with a real sample run, pass the full validator chain, and finalize the release-tracking docs.
**Prerequisites**: Phases 1-3 complete.
**Stability Gate**: a sample PPTX and a sample report each convert to a self-contained `.html` that opens offline with zero external requests and clears the `hallmark-design` bar; `make validate`, `make lint`, and `make test` are green; the Reverse-Engineering Attribution grep is clean; CHANGELOG `## [Unreleased]` carries the feature entry and `docs/v3/v3.9/known-gaps.md` records any deferrals (e.g. scanned-PDF OCR out of scope).
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: an end-to-end exercise plus validation and bookkeeping; lower design risk than Phases 1-2, but the offline-self-contained and anti-slop judgments still want the strong tier. `/implement` re-confirms against the then-current models; it may upshift effort if the sample output repeatedly fails the offline or hallmark gates.

### Sub-tasks

#### 4.1 -- Run the worked example (single deck + single report)

**Objective**: Exercise `/presentify` on representative inputs and capture the output as verification evidence (kept OUT of the distributed skill bundle).

**Prompt**:
> Run the worked example. Using the Phase 1 sample `.pptx` and the sample report (`.docx` or `.pdf`), run the full `/presentify` flow (extract -> theme -> build -> enrichment pass) to produce two sample `.html` decks. Save them as verification evidence under `docs/v3/v3.9/development/` (NOT inside the catalog skill bundle -- demo outputs are not distributed content). Confirm the single-PPTX output follows the original slide flow but is visibly more interactive/appealing, and the report output is a paced presentation of the report (agenda + sections + any data rendered as inline charts). Optionally capture a screenshot or short GIF via the `demo-capture` pattern. Acceptance: two sample decks exist under `docs/v3/v3.9/development/`, each opens offline, the PPTX one preserves flow, and the report one presents the report.

#### 4.2 -- Full validation + self-contained/offline + anti-slop verification

**Objective**: Run every gate against the sample outputs and the catalog changes.

**Prompt**:
> Verify everything. (1) For each sample `.html`: confirm zero external network requests (devtools network tab or a grep for external `http(s)`/`cdn` references outside comments), well-formed markup (tag balance), ASCII-safe content, and working navigation/outline/charts; run them against the `hallmark-design` anti-slop gates and note the verdict. (2) Run `make validate`, `make lint`, and `make test` and confirm all green. (3) Grep the full diff of the new skill + command + references + assets for any upstream product name and confirm the Reverse-Engineering Attribution Rule holds. Fix any failure and re-run until all gates pass. Acceptance: both sample decks pass the offline + well-formedness + anti-slop checks; the full validator chain is green; the attribution grep is clean.

#### 4.3 -- CHANGELOG, known-gaps, and consolidation

**Objective**: Finalize the release-tracking docs for the v3.9.0 cycle.

**Prompt**:
> Finalize docs. (1) Add a `## [Unreleased]` entry to `CHANGELOG.md` (create the section if absent) under `### Added`, describing the new `/presentify` command + `document-to-interactive-html` skill: local-first multi-format extraction (PDF/Word/Excel/PowerPoint) into a normalized content model, a self-contained offline interactive-HTML builder with inline charts, and the enrichment pass; note it is local-only with lazy-imported parsers and no new outbound call, SaaS, generation-as-service, or credential; record the new headline counts (skills + commands). (2) Update `docs/v3/v3.9/known-gaps.md` (create if absent) with deferrals: scanned-PDF OCR, video/audio embedding, and any chart type not yet supported. (3) Confirm this plan's Definition of Done is fully met. Then run `/session history` to document Phase 4. Acceptance: CHANGELOG `## [Unreleased]` carries the feature entry with the new counts; `known-gaps.md` records the deferrals; the Definition of Done is satisfied.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - no constitution file; the feature is a tier-1/tier-2 local + LLM-native capability with no policy violation; parsing libraries are lazy-imported, not hard catalog dependencies) | | |

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed (1.1, 1.2, 1.3, 1.4)
- [x] `references/content-model.md` defines the schema, the per-format mapping, and the multi-file merge
- [x] `scripts/extract_content.py` extracts all four formats into the model, lazy-imports every parser with a `pip install` hint, and merges multi-file input with source attribution
- [x] A missing parser library yields the documented message + non-zero exit (no traceback)
- [x] Images carried as base64 within the size budget; slide order preserved for PPTX; XLSX numeric range -> chart block
- [x] `references/extraction-runbook.md` documents per-format coverage, gotchas, and the OCR/video out-of-scope note
- [x] Validators green; Python style (ruff) clean; no network call in the script
- [x] Session history generated for Phase 1

### Phase 2 Exit Checklist

- [x] All sub-tasks completed (2.1, 2.2, 2.3, 2.4)
- [x] `assets/presentation-template.html` is self-contained (no external requests), with nav/outline/progress/fullscreen/keyboard/transitions/reduced-motion/responsive
- [x] `assets/theme.json` is valid JSON with a documented theme-tokens/brand-styling override path
- [x] `scripts/build_presentation.py` produces one offline `.html` with inline base64 images and inline SVG/canvas charts, and passes its no-external-reference self-check
- [x] `references/interactive-features.md` documents the feature catalog, theme override, and the hallmark-design enrichment pass + the three input modes
- [x] A baseline build of a sample model opens offline and is well-formed (lxml parse PASS; all tag pairs balanced)
- [x] Validators green (`make validate` gates: bundles-only + quality + JSON integrity all pass; ruff clean on the builder)
- [x] Session history generated for Phase 2

### Phase 3 Exit Checklist

- [x] All sub-tasks completed (3.1, 3.2, 3.3)
- [x] `SKILL.md`: pushy description with verbatim triggers + SKIP; `summary_l0` <= 15 words (11); `overview_l1` <= 150 words (132); all required sections in order; body < 500 lines (128); every bundle file referenced
- [x] `catalog/commands/presentify.md` is pushy, documents single/multi/folder inputs + theme/output options, and delegates to the skill
- [x] `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` updated; counts incremented (skills 256 -> 257, specialized-domains 13 -> 14, commands 15 -> 16)
- [x] AGENTS.md + README.md headline counts updated and consistent (the CLAUDE.md skill table is a user-global copy, not edited; the authoritative repo surfaces are AGENTS.md and data/SKILL_INDEX.md)
- [x] Validators green: JSON integrity, orphan-bundle audit clean for this skill, dangling-wikilink resolve (all 8 Related Skills), quality pass 0/0; `make lint` no-op (no shell scripts added)
- [x] Session history generated for Phase 3 (`docs/archive/v3/v3.9/development/history/2026-06-25_presentify-interactive-html-phase-3-skill-command-and-registration.md`)

### Phase 4 Exit Checklist

- [x] All sub-tasks completed (4.1, 4.2, 4.3)
- [x] Sample PPTX -> interactive HTML preserves the original flow (5 slides in order); sample report -> a presentation of the report (synthesized title + agenda + 4 sections); both open offline
- [x] Each sample `.html` has zero external network requests (builder `assert_no_external` passed + grep clean), is well-formed (lxml) and ASCII-safe, and clears the hallmark-design anti-slop gate (gates 7/11/12/13/14/15/24/25/26/27 audited PASS)
- [x] `make validate` green (JSON integrity, orphan-bundle 0 errors, quality 0/0, personal-paths, unicode 0 errors, supply-chain, workflow-security, version-sync, base-parity, compression gate); `make lint` (shellcheck) exit 0; `make test` -- every suite that runs on the Windows dev host is green (extensions 574, hooks 441/14-skip, validators 200); installer + integrations subsuites do not complete here (carried WN-v36-1: bash mis-resolves the space-containing checkout path), authoritative on CI
- [x] Reverse-Engineering Attribution grep clean (only internal `[[hallmark-design]]` cross-links; no upstream product names)
- [x] CHANGELOG `## [Unreleased]` entry added with the new counts (257 skills / 16 commands / 23 hooks); `docs/v3/v3.9/known-gaps.md` records the deferrals (DF-v39-presentify-1..5)
- [x] Session history generated for Phase 4

---

## Definition of Done

- All four phases complete with their Exit Checklists satisfied.
- `/presentify` + `document-to-interactive-html` turn one or many mixed-format documents (PDF/Word/Excel/PowerPoint) into a SINGLE self-contained, offline, interactive HTML presentation: a single deck preserves the flow, a single report becomes a presentation of the report, and multiple sources are compiled into one.
- The output opens with zero external network requests, renders spreadsheet data as inline charts, carries full navigation/outline/progress/fullscreen/keyboard/reduced-motion controls, and clears the `hallmark-design` anti-slop bar.
- Parsing is local-only with lazy-imported libraries (a `pip install` hint on absence); HTML generation is LLM-native; no document leaves the machine; no new outbound call, generation-as-service, scraping-as-service, dependency-as-service, or credential is introduced.
- The skill is conformant (pushy description, quoted summaries within limits, required sections in order, body < 500 lines, every bundle file referenced), the command is pushy and scoped, and the three registries + CLAUDE.md/AGENTS.md index rows + headline counts are updated and consistent.
- The full validator chain (`make validate`, `make lint`, `make test`) is green; all content is ASCII-only and conformant to the Markdown style guide; and no upstream attribution appears in any distributed artifact.
