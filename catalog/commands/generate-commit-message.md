---
description: Analyze the current git changes and generate a comprehensive, structured commit message.
---
# Generate Commit Message Command

Analyze the current git changes and generate a comprehensive, structured commit message.

## Steps

1.  **Analyze Changes**:
    *   Run `git diff --name-status` to see which files changed.
    *   Run `git diff` to see the actual code changes (limit output if huge).
    *   Run `git diff --cached` to see staged changes.

2.  **Categorize**:
    *   Determine the type of change: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
    *   Identify the scope (e.g., `installer`, `catalog`, `api`).

3.  **Draft Message**:
    *   **Title**: Conventional Commit format (`<type>(<scope>): <short summary>`). Limits to 50 chars.
        - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
        - Scope: Optional, e.g., `(auth)`, `(api)`, `(installer)`.
        - Description: Concise summary in imperative mood (e.g., "add feature" not "added feature").
    *   **Body structure (CRITICAL for non-trivial commits)**: After the subject line and a 1-2 sentence intro paragraph stating *what* was delivered and *why*, organize the body as **labeled sections with bullets**, NOT as multiple flowing paragraphs separated by blank lines. Each section header ends in a colon and groups bullets by component, module, or theme (e.g., `Reporting package (`src/reporting/`):`, `Packaging and paths:`, `Desktop UI:`). Always treat **Tests** and **Known gaps** / **Deviations** as their own dedicated sections at the end. For trivial 1-2 file commits, a single short paragraph body is fine; for any commit touching multiple components, use sectioned bullets.
    *   **Why grouped sections beat flowing paragraphs**: a multi-paragraph commit body forces reviewers to scan dense prose to find the change for a specific component. Grouped bullets put the section headers in scannable position, let reviewers jump to the package they care about, and make the structure of the change visible at a glance. Section headers also surface in `git log --oneline` follow-up reads.
    *   **No hard-wrapping (CRITICAL)**: Every paragraph and every bullet point in the body and footer MUST be written as a single continuous line in the source, regardless of length. Do NOT insert line breaks at any column width (50, 72, 80, 100, etc.). Let the editor or terminal handle visual wrapping. Blank lines still separate sections, paragraphs, and bullets; the rule applies *within* each paragraph or bullet, never *between* them. The subject line is the only exception (its 50-character limit is a hard cap, not a wrap).
    *   **Whitespace**: exactly **one** blank line between sections; never two or more. Within a section, bullets are contiguous (no blank lines between them). One blank line after the subject line, one blank line before each new section header.
    *   **Encoding**: Use ASCII characters only. No em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.
    *   **Footer**: Note any breaking changes or issue references.
        - **DO NOT** add `Co-Authored-By` lines or AI attribution footers

## Output
Provide the commit message in a code block for easy copying.

Example (sectioned-bullet style for a multi-component commit; note that every paragraph and every bullet is a single continuous line in the source - no mid-paragraph or mid-bullet line breaks):

```text
feat(v0.3.0): phase 6 docxtpl report engine and Analyze page

Lands the Phase 6 deliverables from `desktop-ingestion-and-reports.md`: a docxtpl-driven report engine, a desktop Analyze page that picks ingest runs and generates Supira-branded docx files, and a Settings tab for swapping in a custom template.

Reporting package (`src/reporting/`):
- `snapshot.py`: immutable Pydantic snapshot of confirmed extractions, plus a `build_snapshot` walker over `ingest_runs` / `source_artifacts` / `ingest_units` / `extractions`.
- `renderer.py`: `ReportRenderer.render(snapshot, template_path)` runs `docxtpl.DocxTemplate.render` against a full context dict, then appends deterministic per-run / per-artifact / per-unit sections via python-docx so reports stay populated even when the template carries no Jinja placeholders.
- Output paths follow `%LOCALAPPDATA%\...\reports\<report_id>\YYYYMMDD-HHMMSS.docx`.

Packaging and paths:
- Bundles `assets/report_template_default.docx` (verbatim copy of the Supira branding template).
- Adds `default_report_template_path` / `user_report_template_path` / `report_template_path` / `reports_dir` / `run_report_dir` helpers in `installer/gui/utils/paths.py`.
- PyInstaller spec collects `docxtpl` and `docx` and ships the bundled template under `<bundle>/assets/`.

Desktop UI:
- Replaces the `AnalyzePage` stub with the run-picker plus Generate report flow (engine / reviewer / template / renderer factory injected via constructor).
- Adds `ReportTab` in `installer/gui/settings_qt.py` that browses for a `.docx`, copies it to `%LOCALAPPDATA%\...\report_template.docx` on Save, and offers Reset to bundled default.

Tests:
- 51 new tests across `tests/reporting/test_snapshot.py`, `tests/reporting/test_renderer.py`, `tests/reporting/test_render_integration.py`, `tests/installer/test_analyze_page.py`, `tests/installer/test_settings_report_tab.py`, plus extensions to `tests/installer/test_paths.py`.
- Total suite: 495 passed, 4 skipped, coverage 86.99% (snapshot 97%, renderer 93%).

Known gaps (tracked as DF in `docs/v0.3.0/known-gaps.md`):
- Bundled template ships without `{{ jinja }}` placeholders; renderer falls back to python-docx append pass.
- Report template config stored as a copied file rather than a `routing.yaml` block.
- `AnalyzePage` not yet wired into `MainWindow`'s engine and run providers (deferred to Phase 8).
```

Notice the structure: title, **one** intro paragraph, then **labeled sections** (`Reporting package:`, `Packaging and paths:`, `Desktop UI:`, `Tests:`, `Known gaps:`) each containing contiguous bullets. Exactly one blank line between sections; never two. No flowing-paragraph body sections.

Counter-example - DO NOT produce a multi-paragraph flowing-prose body like this, even with the no-hard-wrap rule honored:

```text
feat(v0.3.0): phase 6 docxtpl report engine and analyze page

Lands the Phase 6 deliverables from desktop-ingestion-and-reports.md: a docxtpl-driven report engine, a desktop Analyze page that picks ingest runs and generates Supira-branded docx files, and a Settings tab for swapping in a custom template.

Adds the `src/reporting/` package with `snapshot.py` (immutable Pydantic snapshot of confirmed extractions plus a `build_snapshot` walker) and `renderer.py` (`ReportRenderer.render` that runs `docxtpl.DocxTemplate.render` against a context dict then appends deterministic per-run / per-artifact / per-unit sections via python-docx). Output paths follow `%LOCALAPPDATA%\...\reports\<report_id>\YYYYMMDD-HHMMSS.docx`.

Bundles `assets/report_template_default.docx` and adds path helpers in `installer/gui/utils/paths.py`. The PyInstaller spec collects `docxtpl` + `docx`. `.gitattributes` marks docx / pptx / xlsx binary so OneDrive cannot LF-corrupt them.

Replaces the `AnalyzePage` stub with the run-picker plus Generate report flow and the new `ReportTab` in `installer/gui/settings_qt.py` that browses for a `.docx`, copies it to `%LOCALAPPDATA%\...\report_template.docx` on Save.

Test suite expansion: 51 new tests across `tests/reporting/test_*.py` and `tests/installer/test_*.py`. Total suite: 495 passed, 4 skipped, coverage 86.99%.

Three deviations tracked as DF in `docs/v0.3.0/known-gaps.md`: bundled template ships without Jinja placeholders, report template config stored as a copied file, and AnalyzePage not yet wired into MainWindow.
```

The counter-example uses six flowing paragraphs separated by blank lines instead of named sections with bullets. Reviewers must read each paragraph linearly to find a specific component; in the sectioned style, they jump straight to `Reporting package:` or `Tests:` and skim the bullets there. The agent must produce sectioned-bullet output for any commit touching multiple components, not the flowing-paragraph shape - even when the prose is well-written and unwrapped.

**Important**: The generated commit message must never include `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures. The commit message represents the developer's work, not the tool that helped write it.

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Is it complete?
    *   Are there any obvious errors?
    *   Does it meet the user's requirements?
2.  **Refine**:
    *   Fix any issues found.
    *   Add missing components.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
