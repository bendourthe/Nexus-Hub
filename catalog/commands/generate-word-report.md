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

## Phase 4: Analyze Content and Plan Report Structure

Before generating, read and analyze the combined content of all input files:

1. **Identify the document title**: Use the first H1 heading (`#`) found across all input files.
2. **Identify the subtitle**: Look for metadata patterns like `**Subtitle**:`, `**Version**:`, or derive from content context (e.g., "Codebase Analysis Report" if the content is an analysis).
3. **Count sections**: Count H2 (`##`) headings to estimate document length and complexity.
4. **Determine logical ordering** (if multiple files are being combined):
   - Executive summaries and overviews first
   - Detailed analysis sections in the middle
   - Appendices, references, and supplementary material last
   - If the files have a natural sequence (e.g., numbered sections), preserve that order

5. **For PowerPoint output**: Translate the document structure into a slide outline:
   - Each H1 becomes a section divider slide
   - Each H2 becomes a content slide (title + body)
   - Bullet points map to slide body
   - Code blocks render in monospace text boxes
   - Large sections may need splitting across multiple slides

6. **Present the plan to the user**:
   > "I will generate a [Word report / PowerPoint presentation] with the following structure:
   > - **Title**: [detected title]
   > - **Subtitle**: [detected subtitle]
   > - **Sections**: [N] sections from [M] source file(s)
   > - **Template**: [template name]
   > - **Output**: [output path]
   >
   > Proceed? [Y]es / [N]o / [E]dit title/subtitle"

## Phase 5: Generate the Document

Execute the Python report generator script:

### For Word (.docx):

```bash
python ~/.devai-hub/scripts/generate_report.py \
  --type generic-word \
  --md-files <file1.md> [<file2.md> ...] \
  --title "<title>" \
  --subtitle "<subtitle>" \
  --template "<template_path>" \
  --output "<output_path>"
```

### For PowerPoint (.pptx):

```bash
python ~/.devai-hub/scripts/generate_report.py \
  --type generic-pptx \
  --md-files <file1.md> [<file2.md> ...] \
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

1. **Full path** of the file(s) written (both `.md` and `.docx`/`.pptx`).
2. **Template used** (or "built-in default style" if none).
3. **Sections included** (count of major sections).
4. **Version detected** and how it was determined.

Present next steps:

```
What would you like to do next?
1. Open the file (Windows: opens in Word/PowerPoint)
2. Generate with a different template
3. Generate with different files
4. Regenerate with modifications
5. Done
```

- **Option 1**: On Windows, run `start "<output_path>"` to open the file in its default application. On macOS, use `open "<output_path>"`. On Linux, use `xdg-open "<output_path>"`.
- Do not take any action until the user selects an option.

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. Perform the following refinement loop up to **3 times**:

1. **Completeness**: Was all content from every specified input file included? Are any sections missing or truncated? Did the script exit successfully with no errors?
2. **Structure**: Does the heading hierarchy in the output make sense? Are code blocks, tables, and lists rendered correctly?
3. **Metadata**: Is the title, subtitle, author, and date correct? Does the output path match the expected version directory?
4. **Stop**: If you are confident the result is correct, or if you have reached the maximum iteration count.
