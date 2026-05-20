---
description: Compile multiple research reports (.docx/.md/.pdf/.pptx/.html/URL/.txt) into one unified document (.docx/.pdf/.md) matching a user-selected template, with deduplicated inline [N] citations linking to a References section. The agent inspects the template at runtime and writes a throwaway python-docx program tailored to that template's styles -- no persistent generator script.
---

# Compile Deep Research Command

Compile multiple research reports into a single unified document. You (the agent) ingest heterogeneous inputs, inspect the user-selected template to build a style profile, synthesize content with deduplicated inline `[N]` citations, and author a one-shot python-docx program per invocation that produces a `.docx` whose appearance is driven entirely by that style profile. Also emits `.md` (with clickable anchor citations) and `.pdf` (via `docx2pdf` or `libreoffice --headless`).

**BEFORE ANYTHING ELSE**: activate the `deep-research-compilation` skill. The skill contains the full playbook -- proven OOXML patterns, template inspection procedure, synthesis rules, reference deduplication, validation checks. This command is the orchestrator; the skill is the how-to.

Also read `catalog/style-guides/compile-deep-research.md` in the project root (or `~/.nexus-hub/style-guides/compile-deep-research.md` for global installs) for target metrics and the merged-markdown style rules. This style guide is reference content, not a slash command - it lives outside `catalog/commands/` so it does not surface in the slash menu.

## Phase 1: Resolve Input Sources

**CRITICAL RULE**: get explicit user confirmation on the input list before proceeding. Never silently auto-discover inputs.

Accepted source types:
- `.docx`, `.md`, `.markdown`, `.pdf`, `.pptx`, `.html`, `.htm`, `.txt`
- Raw URLs beginning with `http://` or `https://`

Workflow:

1. **If inputs were provided after the command invocation** (e.g. `/compile-deep-research a.docx b.md https://example.com/article`), resolve each:
   - For paths, verify they exist relative to the project root. If not found, search `docs/`, `reports/`, and common subdirs.
   - For URLs, accept as-is (no existence check now; fetched during Phase 4).
2. **If no inputs were provided**, ask:
   > "Which reports should I compile? Paste paths (relative to the project root) or URLs, one per line."
3. **Present the resolved input list** for confirmation:
   > I will compile these sources:
   > 1. `reports/market-analysis.docx`
   > 2. `reports/clinical-context.md`
   > 3. https://example.com/deep-research-output
   >
   > Proceed? [Y]es / [E]dit list / [C]ancel
4. **Reject unknown extensions** with a clear message: "Unsupported format: `.xyz`. Accepted: docx, md, pdf, pptx, html, txt, or a raw URL."
5. **Scope check**: local paths must resolve inside the project root. URLs are always allowed.

## Phase 2: Select Template

**CRITICAL RULE**: always present templates to the user and wait for an explicit selection. Never silently default -- this was the v1 bug.

1. Scan template directories in priority order:
   - `<project_root>/.claude/templates/documentation/` (project-scoped)
   - `~/.nexus-hub/templates/documentation/` (global, installed by Nexus-Hub installer)
   - Accept a user-supplied absolute or relative path as an override.
2. Present the discovered templates, with the default marker on `branded-report-template.docx`:
   > Available templates:
   >   1. **branded-report-template.docx** (global, default) -- teal Consolas title, Calibri Light headings
   >   2. company-branded-template.docx (project) -- if present
   >   3. Provide my own path
   >   4. No template (blank document -- minimal styling)
   >
   > Which template should I use? Enter a number or a path:
3. **Wait for user input.** Do not proceed without it.
4. If the user provides a custom path, validate it exists and is a `.docx`; reject otherwise.
5. Store the resolved template path for Phase 5.

## Phase 3: Select Output Format

Ask explicitly:

> Which format(s) should I produce?
>
> 1. Word (.docx) -- branded title page, full style fidelity to the template
> 2. PDF (.pdf) -- same as Word, exported to PDF via docx2pdf / libreoffice
> 3. Markdown (.md) -- title heading instead of title page; clickable anchor citations
> 4. All three -- produce all formats in one run
>
> Enter a number:

If PDF is in the selection, verify converters are available (`python -c "import docx2pdf"` or `which libreoffice`). Warn but do not block -- the generator handles the fallback and emits a clear error if neither is available.

## Phase 4: Ingest + Extract

**Output layout** (resolve these paths now; every subsequent phase writes to one of them):

- `<final_dir>` = `<project_root>/docs/compiled/` -- the user-facing final outputs (`.docx`, `.pdf`, `.md`). Create if missing.
- `<cache_dir>` = `<project_root>/.cache/compile-deep-research/<ReportTitle>/` -- intermediate artifacts (`merged.md`, `refs.json`, `style_profile.json`, `generate.py`, `ingest.json`). Create if missing. Recommend to the user that this path be gitignored; if `<project_root>/.gitignore` exists and does not already ignore `.cache/`, offer to add the entry (do not modify it without confirmation).

`<ReportTitle>` is sanitized for filesystem use: spaces -> underscores, strip `\/:*?"<>|`.

For each input in the list, extract a normalized record per the `deep-research-compilation` skill, **Step 2** (per-format recipes). Do not call any persistent script -- invoke Python inline via Bash or small helper files as needed.

Build an in-memory (or on-disk as `<cache_dir>/ingest.json`) array of:

```
[
  {"source": "...", "title": "...", "sections": [...], "references": [...], "citations": [...]},
  ...
]
```

Present a summary:

> Extracted content:
> - `reports/market-analysis.docx`: 7 sections, 12 references, 18 inline citations
> - `reports/clinical-context.md`: 5 sections, 8 references, 11 inline citations
> - https://example.com/deep-research-output: 9 sections, 14 references, 23 inline citations
>
> Total: 21 sections, 34 references, 52 inline citations.

If a source extracts 0 sections or raises a parse error, stop and ask the user how to handle it (skip, provide a clean copy, or abort).

## Phase 5: Analyze the Template

Per the skill's **Step 1**. Open the chosen template's `word/styles.xml`, `theme/theme1.xml`, `header*.xml`, `footer*.xml`, `settings.xml`, `numbering.xml`. Extract resolved properties for every style you will apply (Title, Subtitle, Heading1-4, Normal, Hyperlink, TableGrid, ListParagraph, TOCHeading). Detect header/footer structure (empty first page? bottom border? SDT-bound title/creator?).

Save the profile as `<cache_dir>/style_profile.json`. Summarize to the user in plain language:

> Template analyzed: `branded-report-template.docx`
> - Title: Consolas 32 pt `#215868` smallCaps, centered, with navy bottom rule.
> - Body: Calibri 11 pt, 1.15 line spacing.
> - H1-4: Calibri Light smallCaps `#215868`; H1 has a 1 pt teal underline.
> - Hyperlinks: `#2E74B5` underlined.
> - Metadata table: borderless sides, `#BFBFBF` horizontal row rules.
> - TOC: levels 1-3, dots leader.
> - Title page: empty header/footer; body uses `dc:title` in left header and `Page X of Y` in right footer.
>
> Output will match this styling exactly.

If the user notices the profile misread the template, allow them to point out specifics and re-inspect.

## Phase 6: Synthesize Unified Content

Per the skill's **Step 3** (synthesis rules) and **Step 4** (reference deduplication + renumbering).

1. Propose an outline: Title -> Document's Purpose -> Executive Summary (H2 per topic) -> 3-7 body H1s (named after real themes in the material) -> Conclusion -> References.
2. Build the canonical reference list and renumbering map. Save as `<cache_dir>/refs.json`.
3. Write the merged markdown with citations renumbered: `<cache_dir>/merged.md`. Wrap the Document's Purpose + metadata prose in `<!-- PRE-TOC -->...<!-- /PRE-TOC -->`.
4. Emit a `# References` section in the merged markdown listing canonical references in order (the generator will strip this and re-emit it with proper hanging-indent + bookmark styling).
5. Apply the style-guide metrics (target 700-1300 lines, 5-9 body H1s, 3-8 H2s per body H1, max 15 tables, 60-150 bullets).

## Phase 7: Preview + Confirm

Parse the merged markdown for H1/H2/H3 headings and present:

> Compiled document structure:
>
> **Metadata:**
> - Title: `<title>`
> - Subtitle: `<subtitle>`
> - Author: `<author>`
> - Date: `<date>`
> - Format(s): docx
> - Template: `branded-report-template.docx`
> - Canonical references: 28 (6 duplicates collapsed)
> - Inline citations: 52 placements across 21 unique references
>
> **Table of Contents (preview):**
> ```
> 1. Document's Purpose
> 2. Executive Summary
>    2.1. Topic A
>    2.2. Topic B
> 3. <Body Section 1>
>    3.1. <Subtopic>
>    3.2. <Subtopic>
> 4. <Body Section 2>
>    ...
> N. Conclusion
> N+1. References (28 entries)
> ```
>
> Does this structure look good?
> [Y]es, generate / [E]dit / [C]ancel

On **[E]dit**, ask which sections to modify and loop back to Phase 6. **Maximum 3 edit iterations.**

## Phase 8: Generate the Output(s)

Per the skill's **Steps 5-7**. The key architectural rule: **no persistent script**. Per invocation, you write `<cache_dir>/generate.py` that implements the OOXML patterns from the skill tailored to the current style profile + content, then run it via Bash. The generator writes its output to `<final_dir>/<ReportTitle>.docx`.

### For .docx (and .pdf, which requires .docx first)

1. Author `<cache_dir>/generate.py`. Use the proven OOXML patterns from the skill's **Step 5** (sections A-M). Inline the canonical refs + style profile as literals at the top of the script, or have it read them from sibling `refs.json` and `style_profile.json`. Either is fine; inlining gives the user a self-contained file.
2. Run it:
   ```bash
   python "<cache_dir>/generate.py"
   ```
3. Verify `<final_dir>/<ReportTitle>.docx` exists and is non-zero bytes.

### For .pdf

After the `.docx` is built, convert per the skill's **Step 7**. The PDF lands at `<final_dir>/<ReportTitle>.pdf`:
- Primary: `docx2pdf.convert(<final_dir>/<ReportTitle>.docx, <final_dir>/<ReportTitle>.pdf)` if the package imports.
- Fallback: `libreoffice --headless --convert-to pdf --outdir <final_dir> <final_dir>/<ReportTitle>.docx`.
- If neither works, emit a clear error and leave the `.docx` in place.

If only `.pdf` was requested, delete the intermediate `.docx` from `<final_dir>` after successful conversion.

### For .md

Per the skill's **Step 6**. Write directly with the Write tool to `<final_dir>/<ReportTitle>.md` -- no Python. Structure: title heading, italic subtitle + date, metadata table, manual linked TOC, body with `<sup>[[N]](#refN)</sup>` citations, References with `<a id="refN">` anchors and URL links.

## Phase 9: Validate + Iterate

Per the skill's **Step 8**. For each emitted file:

- `.docx`: inspect `word/document.xml` via zipfile; verify every `w:hyperlink w:anchor="_RefN"` has a matching `bookmarkStart`; verify heading paragraphs have `<w:pStyle>` referencing a heading style; verify the TOC SDT is present and well-formed.
- `.md`: regex-scan for `#refN` usages and `<a id="refN">` definitions; all must pair.
- `.pdf`: open with `pypdf.PdfReader`, confirm page count > 0.

If any **fatal** issue is reported (broken citation anchors, missing heading styles, missing TOC field), diagnose, edit `<cache_dir>/generate.py`, and re-run. **Maximum 3 iterations.** If still failing, stop and surface the raw issue list to the user.

Present the final result:

> **Compiled document(s)** (in `docs/compiled/`):
> - `<ReportTitle>.docx` (N pages, validated: ok)
> - `<ReportTitle>.pdf` (N pages)
> - `<ReportTitle>.md` (validated: ok)
>
> **Intermediate artifacts** (in `.cache/compile-deep-research/<ReportTitle>/`, safe to gitignore):
> - `merged.md` -- synthesized master with `[N]` placeholders, feeds both the `.docx` generator and the final `.md` output.
> - `refs.json` -- canonical references + per-input renumbering map.
> - `style_profile.json` -- extracted template styles.
> - `generate.py` -- re-runnable standalone Python; produces the `.docx` without going through this command again.
>
> What next?
> 1. Open the Word document
> 2. Open the PDF
> 3. Open the Markdown
> 4. Regenerate with edits (loops back to Phase 6)
> 5. Done

Open via `start "<path>"` (Windows), `open` (macOS), or `xdg-open` (Linux). Only open after explicit user selection.
