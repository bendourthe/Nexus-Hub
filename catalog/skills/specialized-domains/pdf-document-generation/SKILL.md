---
name: pdf-document-generation
description: Generate professional PDF documents programmatically using Python and JavaScript libraries with precise layout control, typography, and multi-format support. Use when building invoice generators, report pipelines, contract templates, certificate systems, HTML-to-PDF converters, or any workflow that produces PDF output from structured data.
summary_l0: "Generate professional PDF documents with layout design, typography, and multi-library support"
overview_l1: "This skill provides comprehensive guidance for generating PDF documents programmatically across Python and JavaScript ecosystems. Use it when building invoice generators, report rendering pipelines, contract or certificate templates, HTML-to-PDF conversion services, or any system that produces PDF output from structured data. Key capabilities include library selection (ReportLab, WeasyPrint, PDFKit, Puppeteer, jsPDF), document layout design, typography management (font embedding, Unicode support, text wrapping), table rendering with cell spanning and overflow handling, image and vector graphics, cover pages and table of contents, page numbering and watermarks, form fields and digital signatures, PDF/A archival compliance, accessibility tagging, encryption controls, and testing strategies for PDF output validation. The expected output is production-quality PDF generation code with proper font handling, layout precision, and cross-viewer compatibility. Trigger phrases: PDF generation, generate PDF, create PDF, invoice PDF, report PDF, HTML to PDF, WeasyPrint, ReportLab, PDFKit, jsPDF, PDF template, PDF forms, digital signature PDF, PDF/A, accessible PDF."
---

# PDF Document Generation

Structured guidance for generating professional PDF documents programmatically using Python and JavaScript libraries. Covers library selection, document layout, typography, tables, images, HTML-to-PDF conversion, advanced features like form fields and digital signatures, and testing strategies for validating PDF output across viewers and use cases.

## When to Use This Skill

Use this skill for:

- Building invoice, receipt, or statement generators from structured data
- Creating report rendering pipelines that produce PDF output
- Generating contracts, certificates, or legal documents from templates
- Converting HTML/CSS content to PDF with precise layout control
- Adding form fields, digital signatures, or encryption to PDF documents
- Implementing PDF/A archival compliance or accessibility tagging
- Building batch PDF generation systems for high-volume document workflows
- Testing and validating PDF output for content correctness and visual fidelity

**Trigger phrases**: "PDF generation", "generate PDF", "create PDF", "invoice PDF", "report PDF", "HTML to PDF", "WeasyPrint", "ReportLab", "PDFKit", "Puppeteer PDF", "jsPDF", "PDF template", "PDF layout", "PDF forms", "digital signature", "PDF/A", "accessible PDF", "watermark", "table of contents PDF", "cover page"

## What This Skill Does

Provides PDF generation patterns including:

- **Library Selection**: Decision matrix for choosing between ReportLab, WeasyPrint, Puppeteer, PDFKit, and jsPDF based on project requirements
- **Python ReportLab**: Low-level PDF construction with platypus layouts, paragraph styles, tables, images, and multi-page templates
- **Python WeasyPrint**: HTML/CSS-to-PDF rendering with print media queries, custom stylesheets, and page break control
- **JavaScript PDFKit**: Node.js PDF generation with text, vector graphics, custom fonts, and streaming output
- **Puppeteer/Playwright**: Headless Chrome rendering for pixel-perfect HTML-to-PDF conversion with headers, footers, and waiting strategies
- **Document Design**: Cover pages, table of contents, page numbering, watermarks, bookmarks, and outline hierarchies
- **Advanced Features**: Form fields, digital signatures, PDF/A compliance, accessibility tagging, encryption, and permission controls
- **Testing and Validation**: Visual regression testing, content extraction for assertions, file size optimization, and cross-viewer compatibility

## Instructions

### Step 1: Library Selection Guide

Full walkthrough: [step-1-library-selection-guide.md](references/step-1-library-selection-guide.md) (load this step when you reach it).

### Step 2: Python ReportLab Fundamentals

Full walkthrough: [step-2-python-reportlab-fundamentals.md](references/step-2-python-reportlab-fundamentals.md) (load this step when you reach it).

### Step 3: Python WeasyPrint (HTML/CSS to PDF)

Full walkthrough: [step-3-python-weasyprint-html-css-to-pdf.md](references/step-3-python-weasyprint-html-css-to-pdf.md) (load this step when you reach it).

### Step 4: JavaScript PDFKit (Node.js)

Full walkthrough: [step-4-javascript-pdfkit-node-js.md](references/step-4-javascript-pdfkit-node-js.md) (load this step when you reach it).

### Step 5: Puppeteer/Playwright HTML-to-PDF

Full walkthrough: [step-5-puppeteer-playwright-html-to-pdf.md](references/step-5-puppeteer-playwright-html-to-pdf.md) (load this step when you reach it).

### Step 6: Document Design Patterns

Full walkthrough: [step-6-document-design-patterns.md](references/step-6-document-design-patterns.md) (load this step when you reach it).

### Step 7: Advanced Features

Full walkthrough: [step-7-advanced-features.md](references/step-7-advanced-features.md) (load this step when you reach it).

### Step 8: Testing and Validation

Full walkthrough: [step-8-testing-and-validation.md](references/step-8-testing-and-validation.md) (load this step when you reach it).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The default font is fine, no need to embed it" | A non-embedded font renders with a substitute on any viewer that lacks it, so the carefully laid-out invoice reflows and the alignment breaks. Embedding the font is the only guarantee the PDF looks identical everywhere. |
| "It renders fine in Chrome, ship it" | Chrome's PDF viewer is forgiving; Acrobat, Preview, and a PDF/A validator are not. A PDF that passes a Chrome spot-check can still be malformed or fail archival compliance. Validate structure with QPDF, not eyeballs. |
| "Unicode text just works, I'll skip the encoding test" | A core PDF font silently drops glyphs outside Latin-1, so accented names and CJK text vanish without an error. Only a font that covers the character set plus an extraction test catches the missing glyphs. |
| "Accessibility tagging is optional for an internal report" | An untagged PDF is unreadable to a screen reader and fails the accessibility audit that compliance later demands. Tagging during generation is far cheaper than retrofitting it. |

## Verification

- [ ] All fonts used are embedded in the output (verified with `pdffonts` or PyMuPDF)
- [ ] A content-extraction test (pdfplumber / PyMuPDF) confirms expected text, tables, and metadata are present
- [ ] The PDF passes structural validation: `qpdf --check <file>` reports no errors
- [ ] Unicode and multi-byte text render correctly (extraction returns the original characters)
- [ ] Output file size stays within the documented budget (images optimized, no bloat)
- [ ] Rendering is spot-checked in at least two viewers (e.g. Acrobat and Chrome)

## Related Skills

- [[docx-generation]] -- the editable-Word counterpart when output must remain user-editable
- [[pptx-generation]] -- slide-deck generation sharing the same library-selection approach
- [[python-expert]] -- Python language patterns for PDF generation backends
- [[integration-test-generator]] -- integration testing for PDF rendering pipelines
- [[technical-writer]] -- content strategy and information architecture for generated documents
