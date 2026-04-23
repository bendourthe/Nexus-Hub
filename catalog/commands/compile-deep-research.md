---
description: Compile multiple research reports (.docx/.md/.pdf/.pptx/.html/URL/.txt) into one unified document (.docx/.pdf/.md) with deduplicated inline [N] citations linking to a References section.
---

# Compile Deep Research Command

Compile multiple research reports into a single unified document. The command ingests `.docx`, `.md`, `.pdf`, `.pptx`, `.html`, raw URLs, or `.txt` files; extracts their content and references; deduplicates references; renumbers inline `[N]` citations against a single canonical list; synthesizes a unified outline; and emits the result in Word, PDF, Markdown, or all three formats. The Word variant uses a branded template with a teal `#215868` Consolas small-caps title page, Calibri Light small-caps headings, an auto-refreshing Table of Contents, and superscript `[N]` bookmark hyperlinks. The Markdown variant substitutes a title heading for the title page and uses `<sup>[[N]](#refN)</sup>` clickable citations with `<a id="refN">` anchor targets.

**BEFORE WRITING ANY CONTENT**: Read the style guide at `catalog/commands/compile-deep-research-style-guide.md` in the project root (or `~/.devai-hub/catalog/commands/compile-deep-research-style-guide.md` for global installs).

## Phase 1: Resolve Input Sources

**CRITICAL RULE**: You MUST get explicit user confirmation on the input list before proceeding. Never silently auto-discover inputs.

Accepted source types:
- `.docx`, `.md`, `.markdown`, `.pdf`, `.pptx`, `.html`, `.htm`, `.txt`
- Raw URLs beginning with `http://` or `https://`

Workflow:
1. **If inputs were provided after the command invocation** (e.g. `/compile-deep-research report_a.docx report_b.pdf https://example.com/post`), resolve each one:
   - For paths, verify they exist relative to the project root. Search `docs/`, `reports/`, or common subdirs if the exact path is not found.
   - For URLs, accept as-is (no existence check at this stage; `httpx` will fetch during extract).
2. **If no inputs were provided**, ask the user:
   > "Which reports should I compile? Paste paths (relative to the project root) or URLs, one per line."
3. **Present the resolved input list** and ask for confirmation:
   > I will compile these sources:
   > 1. `reports/market-analysis.docx`
   > 2. `reports/clinical-context.md`
   > 3. https://example.com/deep-research-output
   >
   > Proceed? [Y]es / [E]dit list / [C]ancel

4. **Reject unknown extensions** with a clear message: "Unsupported format: `.xyz`. Accepted: docx, md, pdf, pptx, html, txt, or a raw URL."

5. **Scope check**: all local paths must resolve inside the project root. URLs are always allowed.

## Phase 2: Select Output Format

Ask the user explicitly:

> Which format should I produce?
> 1. Word (.docx) — branded title page, full style fidelity
> 2. PDF (.pdf) — same Word output, exported to PDF
> 3. Markdown (.md) — same structure, title heading instead of title page
> 4. All three — produce all formats in one run
>
> Enter a number:

Map the choice to `--format docx|pdf|md|all`. If the user picks PDF or "all", verify `docx2pdf` or LibreOffice is available (`which libreoffice` or `pip show docx2pdf`); warn but do not block — the script will fall back or emit a clear error.

## Phase 3: Ingest and Extract

Create an output directory: `docs/<version>/reports/` (use the version from `CHANGELOG.md` first line, or `package.json`/`pyproject.toml`/`Cargo.toml`, or `vUnknown`).

Invoke the extractor:

```bash
python scripts/compile_deep_research.py --mode extract \
    --inputs <path1> <path2> <url3> ... \
    --out "<out_dir>/ingest.json"
```

Read `ingest.json` and present a summary to the user:

> Extracted content from 3 sources:
> - `reports/market-analysis.docx`: 7 sections, 12 references, 18 inline citations
> - `reports/clinical-context.md`: 5 sections, 8 references, 11 inline citations
> - https://example.com/deep-research-output: 9 sections, 14 references, 23 inline citations
>
> Total: 34 references across 21 sections, 52 inline citations.

If any source extracted 0 sections or yielded parsing errors, stop and ask the user how to handle it (skip the source, provide a clean copy, or abort).

## Phase 4: Deduplicate References

```bash
python scripts/compile_deep_research.py --mode dedupe \
    --in "<out_dir>/ingest.json" \
    --out "<out_dir>/refs.json"
```

Present the dedupe summary:

> Reference deduplication:
> - Total input refs: 34
> - Canonical refs: 28
> - Duplicates collapsed: 6
>
> Proceed with 28 canonical references? [Y]es / [R]eview collapses / [C]ancel

**If the user chooses [R]eview**: open `refs.json`, show any canonical entry that collapsed 2+ input refs with side-by-side diff of the merged texts, and let the user split merges they disagree with (re-run dedupe with a higher fuzzy threshold or an explicit `--skip-fuzzy` flag in a future version; for now, manual edits to `refs.json` are acceptable).

## Phase 5: Synthesize the Unified Outline

This is AI work, not scripted. Read every section from `ingest.json` and produce the unified structure:

1. **Title page / title heading** — one canonical title for the compiled document (ask the user if none of the input titles is obviously correct).
2. **Document's Purpose** (H1) — 1-2 paragraphs explaining what the compiled document covers, why it was assembled, and who the audience is. Followed by a metadata table (Authors, Last Updated).
3. **Table of Contents** — inserted by the script; do not emit a `# Table of Contents` heading.
4. **Executive Summary** (H1) — one opening paragraph + one H2 per topic covered in the body. Self-contained (a reader should understand the document's conclusions from this section alone). 300-500 words.
5. **3-7 body H1 sections** — one per major theme in the merged material. Name them after the actual topics (e.g. "Clinical Evidence", "Competitive Landscape", "Regulatory Roadmap") — not generic labels.
6. **Conclusion** (H1) — 1-3 paragraphs synthesizing takeaways and recommended next steps. No new content.
7. **References** (H1) — emitted by the script from `refs.json`; do not hand-author this section in the merged markdown.

Merge overlapping sections across inputs. If three inputs each have an "Executive Summary" and a "Competitive Landscape" section, the compiled document has one of each — not three.

## Phase 6: Write the Merged Markdown

Write to `<out_dir>/<ReportTitle>_merged.md`:

- Every sentence that cited a source keeps its citation, but with the canonical `[N]` number (use the `renumbering` map in `refs.json` to rewrite local numbers).
- No `# Table of Contents` heading.
- Wrap the Document's Purpose + metadata prose in `<!-- PRE-TOC -->...<!-- /PRE-TOC -->` so it renders before the TOC.
- Emit a `# References` section listing canonical references as `[N] <text>. <URL>` (the script strips this section and re-emits it with hanging-indent + bookmark styling).

**Writing rules**:
- Every H1 and H2 opens with 1-3 sentences of prose. Never start with a table, list, or sub-heading.
- Paragraphs 3-5 sentences max.
- Every analytical claim that came with a citation retains its citation.
- `<ReportTitle>` is sanitized: spaces → underscores, strip `\/:*?"<>|`.

## Phase 7: Preview and Confirm

Parse the merged markdown for H1/H2/H3 headings and present:

> Compiled document structure:
>
> **Metadata:**
> - Title: `[title]`
> - Subtitle: `[subtitle]`
> - Author: `[author]`
> - Date: `[date]`
> - Format(s): `[format]`
> - Canonical references: `[N]`
> - Inline citations: `[M]`
>
> **Table of Contents (preview):**
> ```
> 1. Document's Purpose
> 2. Executive Summary
>    2.1. [Topic Area 1]
>    2.2. [Topic Area 2]
> 3. [Body Section 1]
>    3.1. [Subtopic]
>    3.2. [Subtopic]
> 4. [Body Section 2]
>    ...
> N. Conclusion
> N+1. References (`[R]` entries)
> ```
>
> Does this structure look good?
> [Y]es, generate now / [E]dit / [C]ancel

If [E]dit, ask which sections to modify and loop back to Phase 5. **Maximum 3 edit iterations.**

## Phase 8: Generate the Output(s)

Invoke the generator:

```bash
python scripts/compile_deep_research.py --mode generate \
    --md-file "<out_dir>/<ReportTitle>_merged.md" \
    --refs-file "<out_dir>/refs.json" \
    --template "templates/documentation/branded-report-template.docx" \
    --title "<title>" \
    --subtitle "<subtitle>" \
    --date "<YYYY-MM-DD>" \
    --author "<Author Name>" \
    --format docx|pdf|md|all \
    --output-dir "<out_dir>"
```

**Path resolution**:
- On Windows, expand `~` to `%USERPROFILE%`.
- Check `<project_root>/scripts/compile_deep_research.py` first; fall back to `~/.devai-hub/scripts/compile_deep_research.py`.
- Same for `templates/documentation/branded-report-template.docx`.

**Error handling**:
- Missing `python-docx`: `pip install python-docx`.
- Missing `pypdf`, `python-pptx`, `beautifulsoup4`, `httpx`, or `rapidfuzz`: the script prints the exact install command for each.
- PDF conversion fails: the script tries `docx2pdf` first, then `libreoffice --headless`; if both fail, it prints a clear error and leaves the `.docx` in place for manual export.

## Phase 9: Validate and Confirm

Run validation on each produced file:

```bash
python scripts/compile_deep_research.py --mode validate --file "<out_dir>/<ReportTitle>.docx"
python scripts/compile_deep_research.py --mode validate --file "<out_dir>/<ReportTitle>.md"
python scripts/compile_deep_research.py --mode validate --file "<out_dir>/<ReportTitle>.pdf"
```

The validator reports:
- Citations found (inline `[N]` anchors).
- Bookmarks found (`_RefN` in docx, `<a id="refN">` in md).
- Broken anchors (citation points nowhere).
- Orphan bookmarks (reference unused by any citation).

**If broken anchors are reported**: the merged markdown has a citation to a number not present in `refs.json`. Inspect the mismatch and re-run from Phase 6 with a fix.

Present the result to the user:

> Compiled document(s):
> - `<out_dir>/<ReportTitle>.docx` (N pages, validated: ok)
> - `<out_dir>/<ReportTitle>.pdf` (N pages)
> - `<out_dir>/<ReportTitle>.md` (validated: ok)
>
> Source artifacts (kept for re-generation):
> - `<out_dir>/<ReportTitle>_merged.md`
> - `<out_dir>/ingest.json`
> - `<out_dir>/refs.json`
>
> What next?
> 1. Open the Word document
> 2. Open the PDF
> 3. Open the Markdown
> 4. Regenerate with edits
> 5. Done

On Windows, open via `start "<path>"`; on macOS via `open`; on Linux via `xdg-open`. Only open after explicit user selection.
