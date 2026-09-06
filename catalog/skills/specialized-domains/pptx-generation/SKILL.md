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

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll position every shape with absolute coordinates, layouts are fiddly" | Hard-coded coordinates break the moment the template theme or slide size changes, and brand consistency drifts slide to slide. Using master-slide placeholders is what keeps a 40-slide deck on-brand. |
| "The deck looks right when I open it, no need to assert content" | Visual inspection misses the slide whose data field silently rendered empty because the placeholder name changed. Extracting and asserting text content is the only check that scales past a handful of slides. |
| "Embedding full-resolution images is fine" | Unoptimized images balloon a deck to tens of megabytes that will not email or upload; resizing before embedding keeps the file within budget. |
| "The chart shows numbers, so the data is correct" | A chart can render with the wrong series mapped to the wrong axis and still look plausible. Re-reading the chart XML and asserting the series values is what catches a swapped column. |

## Verification

- [ ] The generated file opens as a valid PPTX (a ZIP archive with the required OOXML parts)
- [ ] Slide count matches the expected number of data items
- [ ] A content-extraction test asserts the expected text appears on each slide (not visual inspection)
- [ ] Table dimensions (rows, columns) match the input data
- [ ] Speaker notes are populated where expected and hyperlinks resolve to valid URLs
- [ ] Output file size stays within budget (images optimized before embedding)
- [ ] A LibreOffice headless conversion runs in CI for visual regression

## Related Skills

- [[docx-generation]] -- the Word-document counterpart sharing the same library-selection approach
- [[pdf-document-generation]] -- export the deck to fixed-layout PDF for distribution
- [[xlsx-generation]] -- generate the source spreadsheets that feed the chart data
- [[python-expert]] -- Python language patterns for presentation generation backends
- [[creative-generation]] -- slide content ideation and structured deck direction upstream of generation
