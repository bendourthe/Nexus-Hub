---
name: pptx-generation
description: PowerPoint presentation generation expertise for creating, editing, and designing professional slide decks programmatically. Use when building presentation generators, automating report decks, or creating slide templates with consistent branding.
summary_l0: "Generate professional PowerPoint presentations with slide design, charts, and multi-library support"
overview_l1: "This skill provides comprehensive expertise in programmatic PowerPoint presentation generation across multiple languages and libraries. Use it when building automated slide deck generators, creating report presentations from data, designing reusable slide templates with consistent branding, adding charts and data visualizations to slides, populating existing templates with dynamic content, or batch-generating presentations from datasets. Key capabilities include library selection (python-pptx, PptxGenJS, Apache POI, LibreOffice), slide layout design patterns, chart and data visualization integration (bar, line, pie, scatter, combo charts), master slide and theme management for brand consistency, template-based generation with placeholder population, batch deck generation from structured data, speaker notes and animation configuration, and testing strategies for slide content verification. The expected output is production-ready PowerPoint files with professional layouts, consistent branding, accurate data visualizations, and optimized file sizes. Trigger phrases: pptx generation, PowerPoint automation, slide deck generator, presentation builder, python-pptx, PptxGenJS, slide template, chart slides, batch presentations, master slides."
---

# PPTX Generation

Structured guidance for building systems that generate professional PowerPoint presentations programmatically. Covers library selection, slide layout design, chart integration, master slide management, template-based generation, batch processing, and quality assurance strategies for automated presentation pipelines.

## When to Use This Skill

Use this skill for:

- Building automated presentation generators from structured data
- Creating report decks (financial summaries, analytics dashboards, project status updates)
- Designing reusable slide templates with consistent corporate branding
- Adding charts, tables, and data visualizations to slides programmatically
- Populating existing PowerPoint templates with dynamic content
- Batch-generating personalized slide decks from datasets (mail merge pattern)
- Integrating presentation generation into CI/CD pipelines or reporting workflows
- Converting Markdown, JSON, or database records into formatted slide decks

**Trigger phrases**: "pptx", "PowerPoint generation", "slide deck", "presentation builder", "python-pptx", "PptxGenJS", "slide template", "chart slides", "automated reports", "batch presentations", "slide layouts", "master slides", "branding deck", "report generator", "slide automation"

## What This Skill Does

Provides presentation generation patterns including:

- **Library Selection**: Decision matrix for python-pptx, PptxGenJS, Apache POI, and LibreOffice approaches
- **Slide Design**: Layout patterns for title, content, two-column, section divider, and closing slides
- **Charts and Data**: Bar, line, pie, scatter, and combo charts with data-driven generation
- **Master Slides**: Theme management, color schemes, font families, and brand consistency
- **Templates**: Loading existing .pptx templates, populating placeholders, and extending layouts
- **Batch Generation**: Mail merge patterns, data-driven deck creation, and parallel processing
- **Quality Assurance**: Slide count verification, content extraction, visual validation, and file size optimization

## Instructions

For handbook, presentation or cross-format document work, apply `[[hallmark-design]]` and its `references/cross-format-patterns.md` to the composition, and `[[anti-slop-editing]]` to prose. These are the existing design/prose owners; format-specific rendering and verification remain here. Do not transfer app-specific layout bans into every document format.

For an explicitly requested retained-handbook export, follow [retained-handbook-export.md](references/retained-handbook-export.md): shared storyboard/figures, native effects, source budget, aspect fit, actual playback and standalone package verification. HTML documentation refresh alone does not request this export.

When that storyboard requires automatic builds, use the existing native template or the bounded [native fade recipe](references/native-motion.md) and [native_motion.py](scripts/native_motion.py) from the retained exporter. A slide crossfade does not animate process steps or plotted chart series. Missing native playback is a review gap; omitting required effects is an implementation failure.

### Step 1: Library Selection

Full walkthrough: [step-1-library-selection.md](references/step-1-library-selection.md) (load this step when you reach it).

### Step 2: Python python-pptx Fundamentals

Full walkthrough: [step-2-python-python-pptx-fundamentals.md](references/step-2-python-python-pptx-fundamentals.md) (load this step when you reach it).

### Step 3: JavaScript PptxGenJS

Full walkthrough: [step-3-javascript-pptxgenjs.md](references/step-3-javascript-pptxgenjs.md) (load this step when you reach it).

### Step 4: Slide Design Patterns

Full walkthrough: [step-4-slide-design-patterns.md](references/step-4-slide-design-patterns.md) (load this step when you reach it).

### Step 5: Charts and Data Visualization

Full walkthrough: [step-5-charts-and-data-visualization.md](references/step-5-charts-and-data-visualization.md) (load this step when you reach it).

### Step 6: Advanced Features

Full walkthrough: [step-6-advanced-features.md](references/step-6-advanced-features.md) (load this step when you reach it).

### Step 7: Template-Based Generation

Full walkthrough: [step-7-template-based-generation.md](references/step-7-template-based-generation.md) (load this step when you reach it).

### Step 8: Testing and Quality Assurance

Full walkthrough: [step-8-testing-and-quality-assurance.md](references/step-8-testing-and-quality-assurance.md) (load this step when you reach it).

## Font Sizes

This skill owns the slide font-size rule. Other skills reference it and do not restate it.

1. Pick every font size from PowerPoint's standard list: 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 44, 48, 54, 60, 66, 72, 80, 88, 96.
2. Never go below 12 pt (captions, footers, table cells, chart labels and source lines included) unless the user explicitly asks for a smaller size.
3. Never use an odd or fractional value such as 13, 15, 10.5 or 21.5. If text does not fit, change the layout (shorter copy, wider box, split the slide) or step to the next standard size.
4. Start from these defaults: title 36 to 44, headings 24 to 28, body 18 to 24, captions and footers 12 to 14.
5. After saving, run `python scripts/check_font_sizes.py <deck.pptx>` (exit 0 clean, 1 violation, 2 usage error). It reads explicit sizes on slides and charts only. A size the user explicitly asked for is passed with `--allow <pt>`.

## Existing-Deliverable Revision

Once a deliverable exists, the user may have edited it, so revising it follows `user-edit-preservation`, which owns this procedure:

1. Before changing the file, run `edit_guard.py check <file>` from that skill. On any exit other than 0, do not write: run `diff` (with no record, exit 4, run `diff <file> --against <your own generated copy>`, for example `out/deck.pptx`), and end your turn with that skill's three-part reply (what the user changed, suggestions on their edits or "None", and your plan ending in a question). Write only after the user says yes.
2. Edit the current file: open it with the library and change only the targeted slides. Do not rerun the generator over it.
3. If a rebuild is unavoidable, save to a working path (for example `deck.revised.pptx`), merge the user's edits in from `edit_guard.py diff`, show the result, and ask before replacing the original.
4. Never save or copy directly onto a file the user can open (their folder, OneDrive, SharePoint, or a shared drive).
5. After every save, run `edit_guard.py record <file> --from write`.

Every example under `references/` that saves over a file which may already exist calls `guard_existing()` first and `record_saved()` after:

```python
import subprocess
import sys
from pathlib import Path

# The installed user-edit-preservation skill folder (for example ~/.claude/skills/ on Claude Code).
EDIT_GUARD = Path("~/.claude/skills/user-edit-preservation/scripts/edit_guard.py").expanduser()


def guard_existing(path) -> None:
    """Refuse to overwrite a file the user changed since it was last recorded (or never recorded)."""
    if Path(path).exists() and subprocess.run([sys.executable, str(EDIT_GUARD), "check", str(path)]).returncode:
        raise SystemExit(f"{path} changed or cannot be verified: follow user-edit-preservation before saving")


def record_saved(path) -> None:
    """Record what the agent just wrote, so a later user edit is detectable."""
    subprocess.run([sys.executable, str(EDIT_GUARD), "record", str(path), "--from", "write"], check=False)
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll position every shape with absolute coordinates, layouts are fiddly" | Hard-coded coordinates break the moment the template theme or slide size changes, and brand consistency drifts slide to slide. Using master-slide placeholders is what keeps a 40-slide deck on-brand. |
| "The deck looks right when I open it, no need to assert content" | Visual inspection misses the slide whose data field silently rendered empty because the placeholder name changed. Extracting and asserting text content is the only check that scales past a handful of slides. |
| "Embedding full-resolution images is fine" | Unoptimized images balloon a deck to tens of megabytes that will not email or upload; resizing before embedding keeps the file within budget. |
| "The chart shows numbers, so the data is correct" | A chart can render with the wrong series mapped to the wrong axis and still look plausible. Re-reading the chart XML and asserting the series values is what catches a swapped column. |
| "13 pt fits the box better than 12 or 14" | Odd sizes look unintentional, drift slide to slide and break the deck's type scale. Pick 12 or 14 and adjust the layout instead. |
| "A 10 pt footnote is fine, nobody reads it" | Text below 12 pt is hard to read when projected or shared on a call. Keep it at 12 or cut the text. |
| "The deck has fade transitions, so the required motion is covered" | A transition can reveal a fully drawn static chart and process. Verify the planned native shape/series effects and automatic triggers, then inspect timed native playback. |

## Verification

- [ ] The generated file opens normally in the target presentation application without repair; ZIP/XML parsing is recorded separately as package validation
- [ ] Slide count matches the expected number of data items
- [ ] A content-extraction test asserts the expected text appears on each slide (not visual inspection)
- [ ] Table dimensions (rows, columns) match the input data
- [ ] Speaker notes are populated where expected and hyperlinks resolve to valid URLs
- [ ] Every font size in the generated deck is in the standard slide list and at least 12 pt (or explicitly requested): `python scripts/check_font_sizes.py <deck.pptx>` exits 0
- [ ] Output file size stays within budget (images optimized before embedding)
- [ ] A LibreOffice headless conversion runs in CI for visual regression
- [ ] When retained motion is required, its process/comparison and chart-series effects exist with automatic triggers, and native timed playback confirms the intended sequence; unavailable playback remains explicitly unverified

## Related Skills

- [[docx-generation]] -- the Word-document counterpart sharing the same library-selection approach
- [[pdf-document-generation]] -- export the deck to fixed-layout PDF for distribution
- [[xlsx-generation]] -- generate the source spreadsheets that feed the chart data
- [[python-expert]] -- Python language patterns for presentation generation backends
- [[creative-generation]] -- slide content ideation and structured deck direction upstream of generation
