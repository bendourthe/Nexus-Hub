---
description: Generate a professional Word (.docx) or PowerPoint (.pptx) report from one or more Markdown files, using a template from the project or global templates directory.
---

# Generate Word Report Command

Generate a professional Word document or PowerPoint presentation from one or more Markdown files. The command discovers available templates, lets you select one, analyzes your content for optimal structure, and produces a formatted report saved to the project's `docs/<version>/` directory.

## Phase 1: Resolve Input Files

Determine what content to include in the report:

1. **If file path(s) were provided after the command invocation** (e.g., the user typed a filename like `analysis.md` or multiple files like `analysis.md review.md`):
   - Verify each file exists relative to the project root.
   - If a file does not exist, search the project for it (check `docs/`, subdirectories).
   - Confirm the resolved list with the user.

2. **If no files were provided**:
   - Ask the user:
     > "Which file(s) should I include in the report? You can specify:
     > - A single file (e.g., `docs/v0.6.2/analysis.md`)
     > - Multiple files separated by spaces
     > - A directory (all `.md` files in that directory will be included)"
   - If a directory was given, use the Glob tool to find all `*.md` files within it (non-recursive).
   - Present the resolved file list and ask for confirmation before proceeding.

3. **Validate inputs**:
   - All files must exist and be readable.
   - Supported input formats: `.md` (Markdown). If non-Markdown files are specified, inform the user that only Markdown is currently supported.

## Phase 2: Discover and Select Template

Scan for available document templates in the following locations, in priority order:

1. `<project_root>/.claude/templates/documentation/` (project-specific, version-controlled)
2. `~/.devai-hub/templates/documentation/` (globally installed by the DevAI-Hub installer)

Merge the two lists, deduplicating by filename (project-level wins on conflict).

**Template selection logic:**

- **If exactly one template is found**: Use it. Inform the user which template was selected.
- **If multiple templates are found**: Present a numbered list grouped by type:

  ```
  Available templates:
  Word (.docx):
    1. generic-word-report-template.docx
    2. Corporate Report Template.docx
  PowerPoint (.pptx):
    3. Presentation Template.pptx

  Select a template [1-3] or press Enter for default (1):
  ```

- **If no templates are found at all**: Inform the user and proceed without a template (a default blank document style will be used).
- **Default**: If the user presses Enter without selecting, use `generic-word-report-template.docx`.

The selected template's file extension determines the output format:
- `.docx` template produces a Word document
- `.pptx` template produces a PowerPoint presentation

## Phase 3: Determine Version and Output Path

1. **Detect the project version** using the same logic as the `analyze-codebase` command:
   - Read the `CHANGELOG.md` in the project root. Extract the most recent version tag (e.g., `v0.6.2`).
   - If no changelog, check `package.json`, `pyproject.toml`, `Cargo.toml` for a version field.
   - If no version can be determined, use `vUnknown`.

2. **Construct the output path** based on the template type:
   - For `.docx`: `<project_root>/docs/<version>/reports/<ReportTitle>.docx`
   - For `.pptx`: `<project_root>/docs/<version>/presentations/<ReportTitle>.pptx`
   - `<ReportTitle>` is derived from the first H1 heading found in the input files, sanitized for filesystem use (spaces replaced with underscores, special characters removed). Falls back to the first input filename stem if no H1 is found.

3. **Create the output directory** if it does not exist.

4. **Handle existing output**:
   - If a file already exists at the output path, ask:
     > "A report already exists at this path. [O]verwrite / [R]ename with timestamp / [C]ancel?"
   - If Rename: append `_YYYYMMDD_HHMMSS` before the extension.

## Phase 4: Content Analysis and Synthesis

**CRITICAL**: This phase is the most important. You must do the intellectual work of merging, deduplicating, and restructuring content BEFORE passing anything to the script. The script is a mechanical formatter, not a content editor. Do NOT skip or rush this phase.

### Step 4.1: Read All Input Files

Read every resolved input file completely. Hold all content in working memory.

### Step 4.2: Content Inventory

For each file, identify and track:
- All H1 headings (document titles)
- All H2 headings (major section names)
- Executive summaries, introductions, or overview sections
- All Markdown tables (lines starting with `|`)
- All Mermaid diagram blocks (fenced with ` ```mermaid `)
- All `---` separator lines (these will be removed)

Identify which sections appear in multiple files (duplicates). For example, if three files each have an "Executive Summary", note this overlap explicitly.

### Step 4.3: Synthesize a Single Merged Markdown Document

Write a NEW Markdown document from scratch. Do NOT concatenate the original files. Instead, synthesize a clean, structured report following these rules:

1. **Exactly one H1**: The report title. This is the ONLY H1 in the entire document.
2. **Exactly one executive summary**: Synthesized from all sources. Write a fresh paragraph that combines the key points from every source's executive summary. Do NOT copy-paste from any single source.
3. **Deduplicate all sections**: If "Architecture Overview" appears in three files, write it ONCE, drawing the best and most complete content from each source. Merge complementary information, resolve contradictions, and eliminate repetition.
4. **Remove all `---` separator lines**: They do not render correctly in Word.
5. **Preserve all Markdown tables**: Every table from every source must appear exactly once in the merged document, in GFM format (`| col | col |` with `|---|---|` separator rows). Do not duplicate tables that contain the same data.
6. **Replace each Mermaid block with a figure placeholder**: For each ` ```mermaid ` code block found in any source file, extract the Mermaid source and replace it inline with:
   ```
   [Figure N: short description of what the diagram shows]
   ```
   Assign figure numbers sequentially starting from 1.
7. **Use a clean heading hierarchy**: H1 for the title only, H2 for major sections, H3 for subsections, H4 for sub-subsections. Never use H1 for anything other than the report title.
8. **Do not include YAML frontmatter** or metadata lines like `**Author**:` or `**Date**:` in the body (these are handled by the script's title page).
9. **Target length**: The merged document should be significantly shorter than the sum of all inputs. If 5 files total 4,600 lines, the merged output should be roughly 1,000-2,000 lines (the unique, non-redundant content).

### Step 4.4: Write the Figures Manifest

Write a JSON file at: `<output_directory>/<ReportTitle>_figures.json`

Format:
```json
[
  {
    "figure_number": 1,
    "title": "Short human-readable title",
    "description": "One-sentence description of what this diagram shows",
    "mermaid_source": "graph TD\n  A --> B\n  ..."
  }
]
```

Include one entry per Mermaid diagram extracted in Step 4.3. If no Mermaid diagrams were found, write an empty array `[]`.

### Step 4.5: Write the Merged Markdown File

Save the synthesized document from Step 4.3 to: `<output_directory>/<ReportTitle>_merged.md`

### Step 4.6: Present the Synthesis Plan

Show the user a summary before proceeding:

> "I have synthesized the content from [M] source files into a single merged report:
> - **Title**: [detected title]
> - **Subtitle**: [detected subtitle]
> - **Sections**: [N] H2 sections (merged from [total H2s across all sources] original sections)
> - **Duplicates removed**: [list of section names that appeared in multiple files and were merged]
> - **Tables**: [N] tables preserved
> - **Figures**: [N] Mermaid diagrams extracted (companion PPTX will contain [N] slides)
> - **Template**: [template name]
> - **Word output**: [output path]
> - **Figures output**: [figures PPTX path]
>
> Proceed? [Y]es / [N]o / [E]dit title/subtitle"

## Phase 5: Generate the Documents

Call the Python report generator script with the SINGLE merged file from Step 4.5. **Never pass the original input files directly.**

### Word Document:

```bash
python ~/.devai-hub/scripts/generate_report.py \
  --type generic-word \
  --md-files "<output_directory>/<ReportTitle>_merged.md" \
  --title "<title>" \
  --subtitle "<subtitle>" \
  --template "<template_path>" \
  --figures-json "<output_directory>/<ReportTitle>_figures.json" \
  --output "<output_path>"
```

This produces both the Word document AND a companion `<ReportTitle>_Figures.pptx` in the same directory (if the figures manifest is non-empty).

### For PowerPoint output (if a .pptx template was selected):

```bash
python ~/.devai-hub/scripts/generate_report.py \
  --type generic-pptx \
  --md-files "<output_directory>/<ReportTitle>_merged.md" \
  --title "<title>" \
  --subtitle "<subtitle>" \
  --template "<template_path>" \
  --output "<output_path>"
```

### Path resolution:

- On Windows, expand `~` to `%USERPROFILE%` (e.g., `C:\Users\<username>\.devai-hub\scripts\generate_report.py`).
- On macOS/Linux, `~` expands normally.
- If the script is not found at the global location, check the project's own `scripts/generate_report.py` as a fallback (for development use within the DevAI-Hub repo itself).

### Error handling:

- If Python is not available: inform the user that Python 3 is required.
- If `python-docx` is not installed: inform the user to run `pip install python-docx`.
- If `python-pptx` is not installed (and PPTX output was requested): inform the user to run `pip install python-pptx`.
- Capture stderr from the script and present any errors clearly to the user.

## Phase 6: Confirm Output and Next Steps

After successful generation, confirm:

1. **Word document path** (or PowerPoint path).
2. **Companion figures PPTX path** (if figures were generated).
3. **Merged Markdown source path** (`_merged.md`, useful for review or re-generation).
4. **Template used** (or "built-in default style" if none).
5. **Sections included** (count of H2 headings in the merged document).
6. **Figures extracted** (count of Mermaid diagrams, with companion PPTX slide count).
7. **Version detected** and how it was determined.

Present next steps:

```
What would you like to do next?
1. Open the Word report
2. Open the companion figures file (to create diagrams)
3. Generate with a different template
4. Generate with different files
5. Regenerate with modifications
6. Done
```

- **Option 1/2**: On Windows, run `start "<path>"`. On macOS, use `open "<path>"`. On Linux, use `xdg-open "<path>"`.
- Do not take any action until the user selects an option.

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. Perform the following refinement loop up to **3 times**:

1. **Completeness**: Does the merged document contain all unique content from every input file? Are any important sections, tables, or findings missing?
2. **Deduplication**: Are there any remaining sections that say essentially the same thing? Did the executive summary get properly synthesized (not copy-pasted)?
3. **Structure**: Does the heading hierarchy make sense? Is there exactly one H1? Do H2 sections flow logically?
4. **Figures**: Were all Mermaid diagrams extracted? Do the figure placeholders in the Markdown match the figures manifest JSON?
5. **Script output**: Did the script exit successfully? Were both the Word document and companion PPTX generated?
6. **Stop**: If you are confident the result is correct, or if you have reached the maximum iteration count.
