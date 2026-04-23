---
name: deep-research-compilation
description: Compile multiple research reports (.docx/.md/.pdf/.pptx/.html/.txt/URLs) into one unified document (.docx, .pdf, or .md) with deduplicated inline [N] citations linking to a References section.
summary_l0: "Compile multi-source research into one document with managed citations"
overview_l1: "This skill compiles multiple research reports into a single unified document. Use it when combining deep-research output from multiple runs, consolidating literature reviews, merging partial reports from different contributors, or assembling a branded reference document from heterogeneous sources. Key capabilities include multi-format ingestion (.docx/.md/.pdf/.pptx/.html/URLs/.txt), reference extraction and deduplication by DOI, normalized URL, or fuzzy title match, citation renumbering against a single canonical reference list, unified outline synthesis that merges overlapping sections across inputs, and output emission in Word (branded template with superscript [N] bookmark hyperlinks), PDF (converted from the Word output), or Markdown (with clickable anchor links). The expected output is a single, well-structured document whose inline citations all resolve to a References section whose entries are clickable. Trigger phrases: compile research, merge reports, consolidate literature review, combine research documents, deep research compilation, unified report with citations, branded word report, reference deduplication, citation renumbering."
---

# Deep Research Compilation

Structured guidance for compiling multi-source research into a single unified document with managed citations. Use this skill when a user has several related reports and wants them merged into one coherent deliverable with consistent inline citations and a deduplicated References section.

## When to Use This Skill

Use this skill for:

- Consolidating multiple deep-research responses from different runs or providers into a single report.
- Merging partial reports authored by different contributors into one coherent document.
- Building a literature review from multiple source documents that each carry their own references.
- Producing a branded, citation-rich Word report when the input mix includes `.docx`, `.pdf`, `.md`, `.pptx`, `.html`, live URLs, or `.txt` files.
- Generating multiple output formats (Word, PDF, Markdown) from the same synthesized content without regenerating each separately.

**Trigger phrases**: "compile these reports", "merge my research", "combine these documents with references", "consolidate my deep research output", "build a unified report from these sources", "compile deep research", "merge my literature review".

## What This Skill Does

Provides a compilation workflow covering:

- **Multi-format ingestion**: one parser per input format, producing a uniform internal record of sections + references + citations.
- **Reference deduplication**: collapse duplicates by DOI, then normalized URL (strips `utm_*`/`fbclid`/`gclid`/`ref` trackers), then fuzzy title match (`rapidfuzz.token_set_ratio >= 85%`, fallback to `difflib`). Emits a canonical `1..N` list plus a per-input renumbering map.
- **Citation renumbering**: every `[old_N]` in every input is rewritten against the canonical numbering so the merged document has a single coherent reference index.
- **Outline synthesis**: AI-driven merging of overlapping sections from across inputs into a single hierarchical structure (Document's Purpose → Executive Summary → 3-7 body H1s → Conclusion → References).
- **Multi-format output**: Word (branded template, teal `#215868` Consolas small-caps title, auto-TOC, superscript `[N]` bookmark hyperlinks, hanging-indent References), PDF (converted from the Word output via `docx2pdf` or `libreoffice --headless`), or Markdown (same structure with title heading instead of title page, `<sup>[[N]](#refN)</sup>` clickable citations, `<a id="refN">` anchor targets).
- **Validation**: post-generation check that every citation anchor resolves to a live bookmark (Word) or anchor (Markdown).

## Instructions

### Step 1: Input Classification

Route each input to its parser by extension (or by URL scheme for live links):

| Input | Parser |
|-------|--------|
| `.docx` | Raw XML extraction via `python-docx` + `zipfile` — preserves style-based heading detection, superscript citation detection, and bookmark-linked References. |
| `.md`, `.markdown` | Line-based regex — `#` heading levels, `\[N\]` inline citations, `# References` section demarcation, reference-link syntax `[N]: URL`. |
| `.pdf` | Text layer extraction via `pypdf`; heading heuristic from line length + capitalization. Rejects scanned PDFs with no text layer. |
| `.pptx` | Slide-by-slide text via `python-pptx`; slide titles become H1/H2. |
| `.html`, URL (`http(s)://`) | DOM walk via `beautifulsoup4`; URL inputs fetched via `httpx` with a 30-second timeout and redirect follow. |
| `.txt` | Heuristic headings (ALL-CAPS short lines, or underlined with `=`/`-`); References section parsed after an isolated `References` line. |

Unknown extensions are rejected with a clear error rather than silently misparsed.

### Step 2: Content Extraction

Every parser emits the same record shape:

```python
ExtractedSource(
    source: str,
    title: str,
    sections: list[Section(level, heading, content_md)],
    references: list[Ref(local_num, text, url, doi)],
    citations: list[Citation(section_idx, char_offset, local_num)],
)
```

The uniform shape lets downstream stages operate on any mix of input formats without branching.

### Step 3: Reference Deduplication

Keys in priority order:

1. **DOI** (case-insensitive exact match).
2. **Normalized URL** — lowercase host, strip `www.`, strip trailing slash, drop `utm_*`/`fbclid`/`gclid`/`ref*` query params, drop fragment.
3. **Title fingerprint** — lowercased, punctuation-stripped, first 80 chars, fuzzy match via `rapidfuzz.fuzz.token_set_ratio` (threshold 85%); falls back to `difflib.SequenceMatcher` when `rapidfuzz` is not installed.

Output: `refs.json` with:
- `canonical`: ordered list `[{num, text, url, doi}, ...]`.
- `renumbering`: `{source_path: {local_num: canonical_num}}` map.
- `stats`: `{total_input_refs, canonical_refs, duplicates_collapsed}`.

### Step 4: Citation Renumbering

Rewrite every `[old_N]` in every input's sections using the renumbering map. When a paragraph carries multiple citations `[old_N, old_M]`, replace with `[new_N, new_M]`; when two inputs used the same local number for different sources, the renumbering map guarantees each maps to its own canonical number.

### Step 5: Outline Synthesis

AI-driven, not scripted. Analyze every input's section structure and produce a unified outline:

1. Title page (Word/PDF) or title heading (Markdown).
2. **Document's Purpose** (H1) + metadata table (Authors, Last Updated).
3. **Table of Contents** (auto-generated in Word/PDF, manually built for Markdown).
4. **Executive Summary** (H1) with one H2 per topic area covered in the body.
5. **3-7 body H1 sections** named after the actual themes in the source material (not generic like "Background", "Analysis" — use the real topic names). Each H1 gets 3-8 H2 subsections, optionally H3.
6. **Conclusion** (H1).
7. **References** (H1) — emitted from `refs.json`, not from the merged markdown.

Merge overlapping sections: if three inputs each have an "Executive Summary" and a section on "Competitive Landscape", the synthesized document has one of each, not three.

### Step 6: Write the Merged Markdown

Write `<output_dir>/<ReportTitle>_merged.md`:

- Every sentence that carried a citation in the source retains one, but the citation numbers are canonical.
- No `# Table of Contents` heading — the script inserts the TOC.
- `<!-- PRE-TOC -->...<!-- /PRE-TOC -->` markers wrap the Document's Purpose section so it renders before the TOC.
- `# References` section lists canonical references in order; the script strips this and re-emits it from `refs.json` so the hanging-indent + bookmark styling is consistent.

### Step 7: Output-Format Routing

Ask the user to pick `.docx`, `.pdf`, `.md`, or `all`. Same content, same structure across all formats; the only difference is:

- `.docx` and `.pdf` have a full title page (title + subtitle + date in centered Consolas small-caps).
- `.md` replaces the title page with a top-level `# <title>` heading, an italic subtitle, and an italic date line.

### Step 8: Generation

Invoke the script with the chosen format:

```bash
python scripts/compile_deep_research.py --mode generate \
    --md-file "<out_dir>/<ReportTitle>_merged.md" \
    --refs-file "<out_dir>/refs.json" \
    --template "templates/documentation/branded-report-template.docx" \
    --title "<title>" --subtitle "<subtitle>" --date "<YYYY-MM-DD>" \
    --author "<Author Name>" \
    --format {docx|pdf|md|all} \
    --output-dir "<out_dir>"
```

After generation, run `--mode validate --file <output>` on each emitted file to verify that every citation anchor resolves.

## Critical Rules

- **Never fabricate citations.** If an input's section has no citations, the merged output for that material has none either.
- **Never silently drop references.** Every canonical reference must appear in the final References section, even if its inline citation count is zero (can happen after user-driven outline edits).
- **Never hardcode output formats.** Always ask the user which format to produce before calling the script.
- **Always run validate after generate.** Broken citation anchors are the single most common failure mode; catch them before handing the document to the user.
