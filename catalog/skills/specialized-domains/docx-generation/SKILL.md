---
name: docx-generation
description: Word document generation and manipulation expertise for creating, editing, and templating professional DOCX files programmatically. Use when building document generators, automating contracts and reports, creating mail merge pipelines, or manipulating Word documents.
summary_l0: "Generate professional Word documents with templates, styles, and multi-library support"
overview_l1: "This skill provides comprehensive expertise in programmatic Word document generation across Python, JavaScript, and .NET ecosystems. Use it when building automated document generators, creating template-driven reports, implementing mail merge pipelines, generating contracts with conditional clauses, producing batch documents from data sources, or manipulating existing DOCX files. Key capabilities include library selection and trade-off analysis (python-docx, docxtpl, Pandoc, officegen, docx for Node.js, OpenXML SDK), document structure fundamentals, Jinja2-based DOCX templating with loops and conditionals, JavaScript DOCX generation with typed APIs, professional design patterns (cover pages, table of contents, watermarks, page numbering), advanced formatting, data-driven mail merge and batch generation, and document testing strategies. The expected output is production-ready code that generates correctly formatted, cross-platform-compatible Word documents from structured data. Trigger phrases: docx generation, Word document, python-docx, docxtpl, mail merge, document template, report generator, contract automation, Word template, OpenXML, batch documents, DOCX manipulation."
---

# DOCX Generation

Structured guidance for programmatic Word document creation, manipulation, and templating. Covers library selection, document structure fundamentals, template-based generation, JavaScript alternatives, professional design patterns, advanced formatting, mail merge pipelines, and testing strategies for document output.

## When to Use This Skill

Use this skill for:

- Building automated report generators that output Word documents
- Creating template-driven contracts, proposals, or invoices
- Implementing mail merge pipelines that produce personalized documents from data sources
- Generating batch documents (certificates, letters, compliance reports) from structured data
- Manipulating existing DOCX files to insert content, update styles, or extract data
- Converting Markdown, HTML, or other formats to professionally styled Word documents
- Building document generation microservices or CLI tools

**Trigger phrases**: "docx", "Word document", "python-docx", "docxtpl", "mail merge", "document template", "report generator", "contract automation", "Word template", "officegen", "OpenXML", "document builder", "batch documents", "DOCX manipulation", "document generation"

## What This Skill Does

Provides document generation patterns including:

- **Library Selection**: Decision matrix for python-docx, docxtpl, Pandoc, officegen, docx (npm), and OpenXML SDK
- **Python Fundamentals**: Document creation with python-docx covering paragraphs, runs, styles, tables, images, and sections
- **Template-Based Generation**: Jinja2-powered DOCX templating with docxtpl for loops, conditionals, images, and subdocuments
- **JavaScript Generation**: Node.js DOCX creation with the docx library covering typed paragraph builders, tables, and headers/footers
- **Design Patterns**: Cover pages, table of contents, headers/footers, page numbering, watermarks, and style hierarchies
- **Advanced Formatting**: Custom styles, theme colors, paragraph spacing, character formatting, section breaks, columns, and footnotes
- **Mail Merge**: Data-driven batch generation with variable substitution, conditional sections, and multi-document output
- **Testing**: Content extraction, style verification, cross-platform rendering validation, and document comparison

## Instructions

### Step 1: Library Selection

Full walkthrough: [step-1-library-selection.md](references/step-1-library-selection.md) (load this step when you reach it).

### Step 2: Python python-docx Fundamentals

Full walkthrough: [step-2-python-python-docx-fundamentals.md](references/step-2-python-python-docx-fundamentals.md) (load this step when you reach it).

### Step 3: Template-Based Generation with docxtpl

Full walkthrough: [step-3-template-based-generation-with-docxtpl.md](references/step-3-template-based-generation-with-docxtpl.md) (load this step when you reach it).

### Step 4: JavaScript DOCX Generation

Full walkthrough: [step-4-javascript-docx-generation.md](references/step-4-javascript-docx-generation.md) (load this step when you reach it).

### Step 5: Document Design Patterns

Full walkthrough: [step-5-document-design-patterns.md](references/step-5-document-design-patterns.md) (load this step when you reach it).

### Step 6: Advanced Formatting

Full walkthrough: [step-6-advanced-formatting.md](references/step-6-advanced-formatting.md) (load this step when you reach it).

### Step 7: Mail Merge and Batch Generation

Full walkthrough: [step-7-mail-merge-and-batch-generation.md](references/step-7-mail-merge-and-batch-generation.md) (load this step when you reach it).

### Step 8: Testing and Validation

Full walkthrough: [step-8-testing-and-validation.md](references/step-8-testing-and-validation.md) (load this step when you reach it).

## Best Practices

- **Separate data from presentation**: Keep your document templates as pure layout with template variables. Business logic and data transformation belong in Python/JS code, not in Jinja2 expressions
- **Use named styles, not direct formatting**: Define styles once and apply by name. This makes global style changes trivial and keeps documents accessible
- **Validate templates on deployment**: Run a test render with sample data as part of your CI pipeline. A broken template discovered in production means failed document delivery
- **Handle Unicode correctly**: Ensure your data pipeline preserves Unicode throughout. Python strings are Unicode by default, but CSV files may use Latin-1 or Windows-1252 encoding
- **Set document properties**: Always set title, author, and subject in `core_properties`. These appear in file explorers and document management systems
- **Size images before insertion**: Resize images to their target dimensions before inserting them. Large images embedded at full resolution inflate the DOCX file size unnecessarily
- **Use temporary files for streaming**: When generating documents in web servers, write to a `tempfile.NamedTemporaryFile` and stream the response rather than holding the entire document in memory
- **Version your templates**: Store document templates in version control alongside the code that renders them. Template changes without corresponding code changes (or vice versa) cause rendering failures
- **Test with realistic data**: Use production-length strings, multi-byte characters, and maximum-size datasets in your test fixtures. Edge cases in document generation often involve text overflow and page layout
- **Log generation metadata**: Record which template version, data source, and generator version produced each document. This is essential for audit trails and debugging rendering issues

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll set paragraph.text directly, runs are extra work" | Assigning `.text` collapses the paragraph to one unformatted run and silently drops any bold, color, or size you set. Building explicit runs is the only way formatting survives. |
| "The template renders for the sample data, ship it" | The empty-list loop, the None value, and the long-string overflow are the cases that break in production, not the happy-path sample. A CI smoke render with edge-case data is what catches them. |
| "Reusing one DocxTemplate instance across the batch is faster" | A reused template carries state from the previous render, so row 2 inherits row 1's content. Loading a fresh DocxTemplate per record is the documented requirement, not an optimization to skip. |
| "It opens in my Word, that is enough verification" | A DOCX that renders in desktop Word can still break in LibreOffice or Word Online and may leave unreplaced `{{` tags a quick read misses. Validate the ZIP structure and assert no leftover tags. |

## Verification

- [ ] The generated file is a structurally valid DOCX (a ZIP archive containing the required OOXML parts)
- [ ] No unreplaced template tags (`{{` or `{%`) remain in any generated document
- [ ] A content-extraction test confirms every expected data field appears in the rendered output
- [ ] The batch generator records per-record failures without aborting the whole run
- [ ] Document properties (title, author, subject) are set on `core_properties`
- [ ] A CI smoke test renders the template with sample (including empty-list and None) data and passes

## Related Skills

- [[python-expert]] -- Python language patterns for document generation backends
- [[typescript-expert]] -- TypeScript patterns for Node.js DOCX generation
- [[api-design]] -- API design for document generation services
- [[integration-test-generator]] -- integration testing for template rendering pipelines
- [[technical-writer]] -- content strategy and information architecture for generated documents
- [[pdf-document-generation]] -- the PDF counterpart when output must be fixed-layout instead of editable

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets are not met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
