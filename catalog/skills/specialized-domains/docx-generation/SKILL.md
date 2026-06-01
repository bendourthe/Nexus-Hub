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

Choosing the right DOCX library depends on your language ecosystem, whether you need template-based or programmatic generation, and the complexity of your formatting requirements.

**Decision Matrix**:

| Library | Language | Approach | Strengths | Limitations |
|---------|----------|----------|-----------|-------------|
| python-docx | Python | Programmatic | Full control, styles, images, tables | No template support, verbose for complex layouts |
| docxtpl | Python | Template | Jinja2 in DOCX, designer-friendly | Requires python-docx, limited to template patterns |
| Pandoc | CLI/Any | Conversion | Markdown/HTML to DOCX, reference docs | External binary, limited fine-grained control |
| docx (npm) | Node.js | Programmatic | TypeScript types, declarative API | Steeper learning curve, newer ecosystem |
| officegen | Node.js | Programmatic | Simple API, quick prototyping | Unmaintained, limited style support |
| OpenXML SDK | C#/.NET | Programmatic | Full OOXML access, enterprise standard | Verbose, requires OOXML specification knowledge |

**When to Use Each**:

- **python-docx**: You need full programmatic control and are in a Python stack. Best for custom document builders where every element is data-driven.
- **docxtpl**: You have a Word template designed by a non-developer and need to fill it with data. Best for report generation, contracts, and invoices where layout is fixed but content varies.
- **Pandoc**: You already have content in Markdown, HTML, or reStructuredText and need to produce styled DOCX output. Best for documentation pipelines and static site generators.
- **docx (npm)**: You are in a Node.js/TypeScript stack and need programmatic generation with type safety. Best for serverless document generation APIs.
- **officegen**: You need a quick prototype in Node.js with minimal setup. Not recommended for production due to maintenance status.
- **OpenXML SDK**: You are in a .NET enterprise environment and need full OOXML specification compliance. Best for complex enterprise document workflows.

**Installation Commands**:

```bash
# Python: python-docx (programmatic generation)
pip install python-docx

# Python: docxtpl (template-based generation, includes python-docx)
pip install docxtpl

# Python: both together for hybrid workflows
pip install python-docx docxtpl Pillow

# Node.js: docx (TypeScript-first programmatic generation)
npm install docx

# Node.js: officegen (legacy, quick prototyping only)
npm install officegen

# CLI: Pandoc (Markdown/HTML to DOCX conversion)
# macOS
brew install pandoc
# Ubuntu/Debian
sudo apt-get install pandoc
# Windows
choco install pandoc

# .NET: OpenXML SDK
dotnet add package DocumentFormat.OpenXml
```

**Hybrid Approach**: For many production systems, the best strategy combines docxtpl for layout-heavy documents (where a designer creates the Word template) with python-docx for fully dynamic documents (where structure itself varies based on data). Use Pandoc as a preprocessing step when source content is in Markdown.

### Step 2: Python python-docx Fundamentals

python-docx provides full programmatic control over Word document creation. Understanding the document object model is essential for building reliable generators.

**Document Object Model**:

```
Document
├── Sections (page layout, orientation, margins)
│   ├── Header
│   └── Footer
├── Paragraphs
│   ├── Runs (text fragments with formatting)
│   └── Paragraph Format (alignment, spacing, indentation)
├── Tables
│   ├── Rows
│   │   └── Cells
│   │       └── Paragraphs (cells contain paragraphs, not raw text)
│   └── Table Style
└── Inline Shapes (images embedded in paragraphs)
```

**Core Document Creation**:

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT

def create_report(title: str, author: str, content: list[dict]) -> Document:
    """Create a structured report document.

    Args:
        title: Report title for the cover page and headers.
        author: Author name for the document properties.
        content: List of section dicts with 'heading', 'level', and 'body' keys.

    Returns:
        A Document object ready to be saved.
    """
    doc = Document()

    # Set document properties
    doc.core_properties.title = title
    doc.core_properties.author = author

    # Configure default section (first section always exists)
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1.25)
    section.right_margin = Inches(1.25)

    # Title
    title_para = doc.add_heading(title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Author line
    author_para = doc.add_paragraph()
    author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = author_para.add_run(f"Prepared by: {author}")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_page_break()

    # Content sections
    for section_data in content:
        heading_level = section_data.get("level", 1)
        doc.add_heading(section_data["heading"], level=heading_level)

        body = section_data.get("body", "")
        if isinstance(body, str):
            doc.add_paragraph(body)
        elif isinstance(body, list):
            for paragraph_text in body:
                doc.add_paragraph(paragraph_text)

    return doc
```

**Working with Paragraphs and Runs**:

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_formatted_paragraph(
    doc: Document,
    text_segments: list[dict],
    alignment: int = WD_ALIGN_PARAGRAPH.LEFT,
    space_before: Pt | None = None,
    space_after: Pt | None = None,
    line_spacing: float | None = None,
) -> None:
    """Add a paragraph with mixed formatting using multiple runs.

    Each segment dict has keys: 'text', and optional 'bold', 'italic',
    'underline', 'font_size', 'font_name', 'color' (hex string like 'FF0000').
    """
    para = doc.add_paragraph()
    para.alignment = alignment

    if space_before is not None:
        para.paragraph_format.space_before = space_before
    if space_after is not None:
        para.paragraph_format.space_after = space_after
    if line_spacing is not None:
        para.paragraph_format.line_spacing = line_spacing

    for segment in text_segments:
        run = para.add_run(segment["text"])
        run.bold = segment.get("bold", False)
        run.italic = segment.get("italic", False)
        run.underline = segment.get("underline", False)

        if "font_size" in segment:
            run.font.size = Pt(segment["font_size"])
        if "font_name" in segment:
            run.font.name = segment["font_name"]
        if "color" in segment:
            hex_color = segment["color"].lstrip("#")
            run.font.color.rgb = RGBColor(
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            )


# Usage
doc = Document()
add_formatted_paragraph(doc, [
    {"text": "Important: ", "bold": True, "color": "CC0000", "font_size": 12},
    {"text": "This report contains ", "font_size": 12},
    {"text": "confidential", "italic": True, "underline": True, "font_size": 12},
    {"text": " information.", "font_size": 12},
])
```

**Tables with Merged Cells and Styling**:

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_data_table(
    doc: Document,
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[float] | None = None,
    header_bg_color: str = "2B579A",
    header_text_color: str = "FFFFFF",
    stripe_color: str = "F2F2F2",
) -> None:
    """Add a formatted data table with header styling and row striping.

    Args:
        doc: Target document.
        headers: Column header labels.
        rows: List of row data (each row is a list of cell strings).
        col_widths: Column widths in inches (optional).
        header_bg_color: Hex color for header row background.
        header_text_color: Hex color for header row text.
        stripe_color: Hex color for alternating row backgrounds.
    """
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    # Set column widths if provided
    if col_widths:
        for i, width in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(width)

    # Style header row
    header_row = table.rows[0]
    for i, header_text in enumerate(headers):
        cell = header_row.cells[i]
        cell.text = ""
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(header_text)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(
            int(header_text_color[0:2], 16),
            int(header_text_color[2:4], 16),
            int(header_text_color[4:6], 16),
        )
        _set_cell_shading(cell, header_bg_color)

    # Populate data rows with alternating stripe
    for row_idx, row_data in enumerate(rows):
        row = table.rows[row_idx + 1]
        for col_idx, cell_text in enumerate(row_data):
            cell = row.cells[col_idx]
            cell.text = cell_text
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in cell.paragraphs[0].runs:
                run.font.size = Pt(9)
        if row_idx % 2 == 1:
            for cell in row.cells:
                _set_cell_shading(cell, stripe_color)


def _set_cell_shading(cell, hex_color: str) -> None:
    """Apply background shading to a table cell."""
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), hex_color)
    shading.set(qn("w:val"), "clear")
    cell._tc.get_or_add_tcPr().append(shading)
```

**Adding Images**:

```python
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
from io import BytesIO

def add_image_with_caption(
    doc: Document,
    image_path: str | Path | BytesIO,
    caption: str,
    width: float = 5.0,
    alignment: int = WD_ALIGN_PARAGRAPH.CENTER,
) -> None:
    """Add an image with a centered caption below it.

    Args:
        doc: Target document.
        image_path: File path or BytesIO stream for the image.
        caption: Caption text displayed below the image.
        width: Image width in inches.
        alignment: Paragraph alignment for both image and caption.
    """
    # Image paragraph
    img_para = doc.add_paragraph()
    img_para.alignment = alignment
    run = img_para.add_run()
    run.add_picture(str(image_path) if isinstance(image_path, Path) else image_path, width=Inches(width))

    # Caption paragraph
    caption_para = doc.add_paragraph()
    caption_para.alignment = alignment
    caption_run = caption_para.add_run(caption)
    caption_run.italic = True
    caption_run.font.size = Pt(9)
    caption_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
```

**Critical Rules for python-docx**:

- Always create runs explicitly when you need formatting control. `paragraph.text = "..."` creates a single run that loses any existing formatting
- Table cells contain paragraphs, not raw text. Access `cell.paragraphs[0]` to format cell content
- Images are inline shapes attached to runs, not paragraphs. Create a run first, then call `run.add_picture()`
- python-docx does not support generating a Table of Contents natively. You must insert the TOC field code and the TOC is populated when the document is opened in Word
- Saving to the same file that is open in Word will raise a `PermissionError`. Always use a temporary file or ensure the document is closed

### Step 3: Template-Based Generation with docxtpl

docxtpl combines python-docx with Jinja2 templating to fill Word templates with data. This approach is ideal when a designer creates the document layout in Word and developers populate it programmatically.

**Template Syntax in Word Documents**:

Place Jinja2 tags directly in your Word document (`.docx` file opened in Word or LibreOffice):

```
# Simple variable substitution
{{ company_name }}

# Loop over a list (use {%tr for table rows, {%p for paragraphs)
{%tr for item in line_items %}
{{ item.description }}    {{ item.quantity }}    {{ item.price }}
{%tr endfor %}

# Conditional sections
{%p if include_disclaimer %}
This document contains confidential information...
{%p endif %}

# Filters
{{ amount | currency }}
{{ date | format_date }}

# Rich text (preserves formatting from the context)
{{ executive_summary | richtext }}
```

**Basic Template Rendering**:

```python
from docxtpl import DocxTemplate, RichText, InlineImage
from docx.shared import Mm, Pt
from pathlib import Path
from datetime import date

def render_contract(
    template_path: str | Path,
    output_path: str | Path,
    context: dict,
) -> Path:
    """Render a contract document from a Word template.

    Args:
        template_path: Path to the .docx template file.
        output_path: Path where the rendered document will be saved.
        context: Dictionary of variables to inject into the template.

    Returns:
        Path to the saved document.
    """
    tpl = DocxTemplate(str(template_path))
    tpl.render(context)
    output = Path(output_path)
    tpl.save(str(output))
    return output


# Usage
context = {
    "company_name": "Acme Corporation",
    "client_name": "Widget Industries",
    "contract_date": date.today().strftime("%B %d, %Y"),
    "contract_number": "CTR-2026-0042",
    "effective_date": "April 1, 2026",
    "termination_date": "March 31, 2027",
    "line_items": [
        {"description": "Consulting Services", "quantity": 120, "unit": "hours", "rate": 250.00, "total": 30000.00},
        {"description": "Software License", "quantity": 1, "unit": "annual", "rate": 12000.00, "total": 12000.00},
        {"description": "Support Package", "quantity": 12, "unit": "months", "rate": 500.00, "total": 6000.00},
    ],
    "grand_total": 48000.00,
    "payment_terms": "Net 30",
    "include_nda_clause": True,
    "include_sla_appendix": False,
}

render_contract("templates/contract_template.docx", "output/contract_CTR-2026-0042.docx", context)
```

**Rich Text and Inline Images**:

```python
from docxtpl import DocxTemplate, RichText, InlineImage
from docx.shared import Mm, Pt, RGBColor

def build_rich_context(tpl: DocxTemplate, data: dict) -> dict:
    """Build a context dictionary with rich text and inline images.

    Rich text allows mixing fonts, colors, and styles within a single
    template variable. Inline images are sized and positioned within
    the document flow.
    """
    # Rich text with mixed formatting
    summary = RichText()
    summary.add("Status: ", bold=True, font="Calibri", size=Pt(11))
    if data["status"] == "approved":
        summary.add("APPROVED", bold=True, color=RGBColor(0x00, 0x80, 0x00), size=Pt(11))
    else:
        summary.add("PENDING", bold=True, color=RGBColor(0xFF, 0x80, 0x00), size=Pt(11))
    summary.add(f" on {data['status_date']}", size=Pt(11))

    # Inline image from file
    logo = InlineImage(tpl, str(data["logo_path"]), width=Mm(30))

    # Inline image from bytes (useful for chart images generated at runtime)
    chart = None
    if data.get("chart_bytes"):
        from io import BytesIO
        chart = InlineImage(tpl, BytesIO(data["chart_bytes"]), width=Mm(120))

    return {
        "status_summary": summary,
        "company_logo": logo,
        "performance_chart": chart,
        **data,
    }
```

**Custom Jinja2 Filters**:

```python
from docxtpl import DocxTemplate
from jinja2 import Environment
from decimal import Decimal
from datetime import date, datetime

def register_custom_filters(tpl: DocxTemplate) -> None:
    """Register custom Jinja2 filters for document templates.

    Filters transform variable values during rendering. Register them
    on the template's Jinja2 environment before calling render().
    """
    env: Environment = tpl.jinja_env

    def currency_filter(value: float | Decimal, symbol: str = "$", decimals: int = 2) -> str:
        formatted = f"{float(value):,.{decimals}f}"
        return f"{symbol}{formatted}"

    def date_filter(value: date | datetime | str, fmt: str = "%B %d, %Y") -> str:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime(fmt)

    def percentage_filter(value: float, decimals: int = 1) -> str:
        return f"{value:.{decimals}f}%"

    def title_case_filter(value: str) -> str:
        return value.title()

    env.filters["currency"] = currency_filter
    env.filters["format_date"] = date_filter
    env.filters["percentage"] = percentage_filter
    env.filters["title_case"] = title_case_filter


# Usage in template: {{ grand_total | currency }}  ->  $48,000.00
# Usage in template: {{ contract_date | format_date }}  ->  March 26, 2026
```

**Subdocuments (Composing Multiple Templates)**:

```python
from docxtpl import DocxTemplate
from pathlib import Path

def render_composite_document(
    master_template: str | Path,
    subdoc_templates: list[dict],
    global_context: dict,
    output_path: str | Path,
) -> Path:
    """Render a master document that includes subdocuments.

    Each subdocument is a separate .docx template rendered with its own
    context and inserted into the master template at a placeholder.

    Args:
        master_template: Path to the master .docx template.
        subdoc_templates: List of dicts with 'placeholder', 'template_path', and 'context'.
        global_context: Variables shared across all templates.
        output_path: Path for the final rendered document.
    """
    tpl = DocxTemplate(str(master_template))

    context = dict(global_context)
    for subdoc_info in subdoc_templates:
        sub = tpl.new_subdoc(str(subdoc_info["template_path"]))
        context[subdoc_info["placeholder"]] = sub

    tpl.render(context)
    output = Path(output_path)
    tpl.save(str(output))
    return output


# Master template contains: {{ appendix_a }}
# This inserts the entire rendered subdocument at that position
render_composite_document(
    master_template="templates/main_report.docx",
    subdoc_templates=[
        {
            "placeholder": "appendix_a",
            "template_path": "templates/appendix_technical.docx",
            "context": {"findings": technical_findings},
        },
        {
            "placeholder": "appendix_b",
            "template_path": "templates/appendix_financial.docx",
            "context": {"budget_data": budget_rows},
        },
    ],
    global_context={"report_title": "Annual Review 2026", "author": "Compliance Team"},
    output_path="output/annual_review_2026.docx",
)
```

**Critical Rules for docxtpl**:

- Use `{%tr ... %}` for table row loops and `{%p ... %}` for paragraph-level loops. Using `{% ... %}` without the `tr` or `p` prefix breaks the XML structure
- Never place two Jinja2 tags in the same Word run if they span structural boundaries (paragraphs, table rows). Each tag should be its own text run in the template
- Rich text variables must be declared as `RichText` objects in the context. Plain strings passed to a `{{ var | richtext }}` filter will fail
- Test templates with edge cases: empty lists (loops produce no output), `None` values (use `{{ var | default("N/A") }}`), and very long strings (may overflow table cells)
- Subdocuments inherit the master document's styles. If the subdocument template uses custom styles not present in the master, those styles will be lost

### Step 4: JavaScript DOCX Generation

The `docx` npm package provides a TypeScript-first declarative API for building Word documents in Node.js. It uses a builder pattern where you compose document elements as nested objects.

**Core Document Structure**:

```typescript
import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  Header,
  Footer,
  PageNumber,
  NumberFormat,
  ImageRun,
  ShadingType,
  convertInchesToTwip,
  Tab,
  TabStopPosition,
  TabStopType,
} from "docx";
import * as fs from "fs";
import * as path from "path";

interface ReportSection {
  heading: string;
  level: (typeof HeadingLevel)[keyof typeof HeadingLevel];
  paragraphs: string[];
}

function createReport(
  title: string,
  author: string,
  sections: ReportSection[],
): Document {
  const children: Paragraph[] = [];

  // Title
  children.push(
    new Paragraph({
      text: title,
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
    }),
  );

  // Author line
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({
          text: `Prepared by: ${author}`,
          size: 24, // half-points: 24 = 12pt
          color: "666666",
          font: "Calibri",
        }),
      ],
    }),
  );

  // Sections
  for (const section of sections) {
    children.push(
      new Paragraph({
        text: section.heading,
        heading: section.level,
        spacing: { before: 240, after: 120 },
      }),
    );
    for (const text of section.paragraphs) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text,
              size: 22, // 11pt
              font: "Calibri",
            }),
          ],
          spacing: { after: 120 },
        }),
      );
    }
  }

  return new Document({
    creator: author,
    title,
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(1),
              bottom: convertInchesToTwip(1),
              left: convertInchesToTwip(1.25),
              right: convertInchesToTwip(1.25),
            },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [
                  new TextRun({
                    text: title,
                    italics: true,
                    size: 18,
                    color: "999999",
                  }),
                ],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({ text: "Page ", size: 18 }),
                  new TextRun({
                    children: [PageNumber.CURRENT],
                    size: 18,
                  }),
                  new TextRun({ text: " of ", size: 18 }),
                  new TextRun({
                    children: [PageNumber.TOTAL_PAGES],
                    size: 18,
                  }),
                ],
              }),
            ],
          }),
        },
        children,
      },
    ],
  });
}

// Save to file
async function saveDocument(doc: Document, filePath: string): Promise<void> {
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(filePath, buffer);
}
```

**Tables in the docx npm Package**:

```typescript
import {
  Table,
  TableRow,
  TableCell,
  Paragraph,
  TextRun,
  WidthType,
  AlignmentType,
  ShadingType,
  BorderStyle,
  convertInchesToTwip,
} from "docx";

interface TableData {
  headers: string[];
  rows: string[][];
}

function createStyledTable(data: TableData): Table {
  const headerCells = data.headers.map(
    (text) =>
      new TableCell({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text,
                bold: true,
                color: "FFFFFF",
                size: 20,
                font: "Calibri",
              }),
            ],
          }),
        ],
        shading: { fill: "2B579A", type: ShadingType.CLEAR },
        width: { size: 100 / data.headers.length, type: WidthType.PERCENTAGE },
      }),
  );

  const dataRows = data.rows.map(
    (row, rowIdx) =>
      new TableRow({
        children: row.map(
          (cellText) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    new TextRun({
                      text: cellText,
                      size: 18,
                      font: "Calibri",
                    }),
                  ],
                }),
              ],
              shading:
                rowIdx % 2 === 1
                  ? { fill: "F2F2F2", type: ShadingType.CLEAR }
                  : undefined,
            }),
        ),
      }),
  );

  return new Table({
    rows: [new TableRow({ children: headerCells }), ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  });
}
```

**Generating DOCX in Serverless / Express Endpoints**:

```typescript
import express from "express";
import { Document, Packer, Paragraph, HeadingLevel } from "docx";

const app = express();
app.use(express.json());

app.post("/api/generate-report", async (req, res) => {
  const { title, sections } = req.body;

  const doc = new Document({
    sections: [
      {
        children: [
          new Paragraph({ text: title, heading: HeadingLevel.HEADING_1 }),
          ...sections.map(
            (s: { text: string }) => new Paragraph({ text: s.text }),
          ),
        ],
      },
    ],
  });

  const buffer = await Packer.toBuffer(doc);

  res.setHeader(
    "Content-Type",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  );
  res.setHeader("Content-Disposition", `attachment; filename="${title}.docx"`);
  res.send(Buffer.from(buffer));
});
```

**Critical Rules for JavaScript DOCX Generation**:

- Sizes in the docx npm package are in half-points (not points). A 12pt font is `size: 24`
- Use `convertInchesToTwip()` for margins and dimensions. One inch is 1440 twips
- The `Packer.toBuffer()` method is async. Always `await` it
- Table cells must contain at least one `Paragraph`. Empty cells cause invalid documents
- Images require the file bytes passed as a `Buffer` to `ImageRun`, not a file path

### Step 5: Document Design Patterns

Professional documents follow consistent design conventions. These patterns apply regardless of which library you use.

**Cover Page Pattern**:

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import date

def add_cover_page(
    doc: Document,
    title: str,
    subtitle: str,
    organization: str,
    author: str,
    doc_date: date | None = None,
    logo_path: str | None = None,
    version: str | None = None,
) -> None:
    """Add a professional cover page to the document.

    The cover page uses the first section and adds a page break after.
    """
    if doc_date is None:
        doc_date = date.today()

    # Logo (top center)
    if logo_path:
        logo_para = doc.add_paragraph()
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = logo_para.add_run()
        run.add_picture(logo_path, width=Inches(2))

    # Spacer
    for _ in range(4):
        doc.add_paragraph()

    # Title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(title)
    title_run.bold = True
    title_run.font.size = Pt(28)
    title_run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    title_run.font.name = "Calibri Light"

    # Subtitle
    subtitle_para = doc.add_paragraph()
    subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle_para.add_run(subtitle)
    sub_run.font.size = Pt(16)
    sub_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    sub_run.font.name = "Calibri"

    # Spacer
    for _ in range(6):
        doc.add_paragraph()

    # Metadata block
    meta_lines = [
        organization,
        f"Prepared by: {author}",
        doc_date.strftime("%B %d, %Y"),
    ]
    if version:
        meta_lines.append(f"Version: {version}")

    for line in meta_lines:
        meta_para = doc.add_paragraph()
        meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta_run = meta_para.add_run(line)
        meta_run.font.size = Pt(11)
        meta_run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    doc.add_page_break()
```

**Table of Contents Field Code**:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_table_of_contents(doc: Document, title: str = "Table of Contents") -> None:
    """Insert a Table of Contents field code.

    The TOC is a field code that Word evaluates when the document is opened.
    It will not display content in python-docx or PDF converters; it requires
    Word or LibreOffice to update field codes on open.
    """
    doc.add_heading(title, level=1)

    paragraph = doc.add_paragraph()
    run = paragraph.add_run()

    # Begin field
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_char_begin)

    # Field instruction: TOC with heading levels 1-3, hyperlinks
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = r' TOC \o "1-3" \h \z \u '
    run._r.append(instr_text)

    # Separate
    fld_char_separate = OxmlElement("w:fldChar")
    fld_char_separate.set(qn("w:fldCharType"), "separate")
    run._r.append(fld_char_separate)

    # Placeholder text (replaced when Word updates fields)
    placeholder = OxmlElement("w:t")
    placeholder.text = "Right-click and select 'Update Field' to generate Table of Contents"
    run._r.append(placeholder)

    # End field
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_end)

    doc.add_page_break()
```

**Headers and Footers with Page Numbers**:

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def configure_headers_footers(
    doc: Document,
    header_text: str,
    footer_text: str | None = None,
    show_page_numbers: bool = True,
    different_first_page: bool = True,
) -> None:
    """Configure headers and footers for all sections.

    Args:
        doc: Target document.
        header_text: Text displayed in the header (right-aligned).
        footer_text: Optional left-aligned footer text.
        show_page_numbers: Whether to show 'Page X of Y' in the footer.
        different_first_page: If True, the first page has no header/footer
            (useful when the first page is a cover page).
    """
    for section in doc.sections:
        section.different_first_page_header_footer = different_first_page

        # Default header (all pages except first if different_first_page is True)
        header = section.header
        header.is_linked_to_previous = False
        header_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        header_para.text = ""
        header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = header_para.add_run(header_text)
        run.italic = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

        # Default footer
        footer = section.footer
        footer.is_linked_to_previous = False
        footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        footer_para.text = ""

        if footer_text:
            left_run = footer_para.add_run(footer_text)
            left_run.font.size = Pt(8)
            left_run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

        if show_page_numbers:
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _add_page_number_field(footer_para)


def _add_page_number_field(paragraph) -> None:
    """Insert 'Page X of Y' using Word field codes."""
    run = paragraph.add_run()
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    run2 = paragraph.add_run("Page ")
    run2.font.size = Pt(8)

    # Current page number field
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run3 = paragraph.add_run()
    run3._r.append(fld_begin)

    instr = OxmlElement("w:instrText")
    instr.text = " PAGE "
    run4 = paragraph.add_run()
    run4._r.append(instr)

    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    run5 = paragraph.add_run()
    run5._r.append(fld_sep)

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run6 = paragraph.add_run()
    run6._r.append(fld_end)

    run7 = paragraph.add_run(" of ")
    run7.font.size = Pt(8)

    # Total pages field
    fld_begin2 = OxmlElement("w:fldChar")
    fld_begin2.set(qn("w:fldCharType"), "begin")
    run8 = paragraph.add_run()
    run8._r.append(fld_begin2)

    instr2 = OxmlElement("w:instrText")
    instr2.text = " NUMPAGES "
    run9 = paragraph.add_run()
    run9._r.append(instr2)

    fld_sep2 = OxmlElement("w:fldChar")
    fld_sep2.set(qn("w:fldCharType"), "separate")
    run10 = paragraph.add_run()
    run10._r.append(fld_sep2)

    fld_end2 = OxmlElement("w:fldChar")
    fld_end2.set(qn("w:fldCharType"), "end")
    run11 = paragraph.add_run()
    run11._r.append(fld_end2)
```

**Watermark Pattern**:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_watermark(doc: Document, text: str = "DRAFT", color: str = "C0C0C0") -> None:
    """Add a diagonal text watermark to all pages.

    Watermarks are implemented as VML shapes in the default header.
    This works in Word and most DOCX renderers.
    """
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()

        # VML shape for watermark
        pict = OxmlElement("w:pict")
        shape = OxmlElement("v:shape")
        shape.set("id", "watermark")
        shape.set("style", (
            "position:absolute;margin-left:0;margin-top:0;"
            "width:500pt;height:200pt;rotation:315;"
            "z-index:-251657216;mso-position-horizontal:center;"
            "mso-position-vertical:center;"
            "mso-position-horizontal-relative:margin;"
            "mso-position-vertical-relative:margin"
        ))
        shape.set("fillcolor", f"#{color}")
        shape.set("stroked", "f")

        textpath = OxmlElement("v:textpath")
        textpath.set("string", text)
        textpath.set("style", "font-family:Calibri;font-size:1pt")
        shape.append(textpath)
        pict.append(shape)

        run = paragraph.add_run()
        run._r.append(pict)
```

**Style Hierarchy**: Word documents have a three-level style hierarchy. Document defaults define the base font and paragraph formatting for the entire document. Named styles (Heading 1, Normal, etc.) inherit from document defaults and can override any property. Direct formatting (applied via runs and paragraph format objects) overrides named styles. Best practice is to define named styles for repeatable formatting and minimize direct formatting, which makes documents easier to maintain and restyle.

### Step 6: Advanced Formatting

Complex documents require fine-grained control over styles, spacing, columns, and structural elements beyond basic paragraphs and tables.

**Custom Style Definitions**:

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH

def define_custom_styles(doc: Document) -> None:
    """Define a set of custom styles for consistent document formatting.

    Custom styles are added to the document's style catalog and can be
    applied by name to any paragraph or run.
    """
    styles = doc.styles

    # Body text style
    body_style = styles.add_style("Custom Body", WD_STYLE_TYPE.PARAGRAPH)
    body_style.base_style = styles["Normal"]
    body_style.font.name = "Calibri"
    body_style.font.size = Pt(11)
    body_style.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    body_style.paragraph_format.space_after = Pt(6)
    body_style.paragraph_format.space_before = Pt(0)
    body_style.paragraph_format.line_spacing = 1.15

    # Callout / highlight box style
    callout_style = styles.add_style("Callout", WD_STYLE_TYPE.PARAGRAPH)
    callout_style.base_style = styles["Normal"]
    callout_style.font.name = "Calibri"
    callout_style.font.size = Pt(10)
    callout_style.font.italic = True
    callout_style.font.color.rgb = RGBColor(0x1A, 0x5B, 0x9C)
    callout_style.paragraph_format.left_indent = Inches(0.5)
    callout_style.paragraph_format.space_before = Pt(12)
    callout_style.paragraph_format.space_after = Pt(12)

    # Code block style (monospace)
    code_style = styles.add_style("Code Block", WD_STYLE_TYPE.PARAGRAPH)
    code_style.base_style = styles["Normal"]
    code_style.font.name = "Consolas"
    code_style.font.size = Pt(9)
    code_style.font.color.rgb = RGBColor(0x2D, 0x2D, 0x2D)
    code_style.paragraph_format.space_before = Pt(4)
    code_style.paragraph_format.space_after = Pt(4)
    code_style.paragraph_format.left_indent = Inches(0.25)

    # Table header character style
    if "Table Header Char" not in [s.name for s in styles]:
        th_style = styles.add_style("Table Header Char", WD_STYLE_TYPE.CHARACTER)
        th_style.font.bold = True
        th_style.font.size = Pt(10)
        th_style.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Caption style
    caption_style = styles.add_style("Figure Caption", WD_STYLE_TYPE.PARAGRAPH)
    caption_style.base_style = styles["Normal"]
    caption_style.font.size = Pt(9)
    caption_style.font.italic = True
    caption_style.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    caption_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_style.paragraph_format.space_before = Pt(4)
    caption_style.paragraph_format.space_after = Pt(12)


# Usage: apply custom styles by name
doc = Document()
define_custom_styles(doc)
doc.add_paragraph("This is body text.", style="Custom Body")
doc.add_paragraph("Note: important callout here.", style="Callout")
doc.add_paragraph("def hello():\n    print('world')", style="Code Block")
```

**Section Breaks and Multi-Layout Documents**:

```python
from docx import Document
from docx.shared import Inches
from docx.enum.section import WD_ORIENT

def add_landscape_section(doc: Document) -> None:
    """Add a new landscape-oriented section.

    Useful for wide tables, charts, or diagrams that do not fit
    in portrait orientation. The section break is inserted automatically.
    """
    new_section = doc.add_section()
    new_section.orientation = WD_ORIENT.LANDSCAPE
    # Swap width and height for landscape
    new_section.page_width = Inches(11)
    new_section.page_height = Inches(8.5)
    new_section.top_margin = Inches(1)
    new_section.bottom_margin = Inches(1)
    new_section.left_margin = Inches(1)
    new_section.right_margin = Inches(1)


def add_portrait_section(doc: Document) -> None:
    """Return to portrait orientation after a landscape section."""
    new_section = doc.add_section()
    new_section.orientation = WD_ORIENT.PORTRAIT
    new_section.page_width = Inches(8.5)
    new_section.page_height = Inches(11)
    new_section.top_margin = Inches(1)
    new_section.bottom_margin = Inches(1)
    new_section.left_margin = Inches(1.25)
    new_section.right_margin = Inches(1.25)


# Usage: portrait -> landscape (wide table) -> portrait
doc = Document()
doc.add_heading("Introduction", level=1)
doc.add_paragraph("Regular portrait content here.")

add_landscape_section(doc)
doc.add_heading("Wide Data Table", level=1)
# Add your wide table here

add_portrait_section(doc)
doc.add_heading("Conclusion", level=1)
doc.add_paragraph("Back to portrait orientation.")
```

**Columns Layout**:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_columns(doc: Document, num_columns: int = 2, spacing: float = 0.5) -> None:
    """Configure the current section for multi-column layout.

    Args:
        doc: Target document.
        num_columns: Number of text columns (typically 2 or 3).
        spacing: Space between columns in inches.
    """
    section = doc.sections[-1]
    sect_pr = section._sectPr

    cols = sect_pr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sect_pr.append(cols)

    cols.set(qn("w:num"), str(num_columns))
    cols.set(qn("w:space"), str(int(spacing * 1440)))  # inches to twips
```

**Footnotes**:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_footnote(paragraph, text: str) -> None:
    """Add a footnote to a paragraph.

    Footnotes require manipulating the OOXML directly since python-docx
    does not provide a high-level API for footnotes.
    """
    # Get or create the footnotes part
    doc = paragraph.part.document
    footnotes_part = doc.part._package.part_related_by(
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
    ) if hasattr(doc.part._package, "part_related_by") else None

    # For a simpler approach, use a superscript reference and an endnote section
    run = paragraph.add_run()
    rpr = run._r.get_or_add_rPr()
    vertAlign = OxmlElement("w:vertAlign")
    vertAlign.set(qn("w:val"), "superscript")
    rpr.append(vertAlign)
    run.text = "*"

    # The actual footnote text is often easier to implement as an endnote
    # section at the bottom of the document for python-docx compatibility
```

**Bulleted and Numbered Lists**:

```python
from docx import Document
from docx.shared import Pt, Inches

def add_bullet_list(doc: Document, items: list[str], level: int = 0) -> None:
    """Add a bulleted list to the document.

    Args:
        doc: Target document.
        items: List of text items.
        level: Indentation level (0 = top-level, 1 = sub-item, etc.).
    """
    for item in items:
        para = doc.add_paragraph(item, style="List Bullet")
        if level > 0:
            para.paragraph_format.left_indent = Inches(0.5 * level)


def add_numbered_list(doc: Document, items: list[str], level: int = 0) -> None:
    """Add a numbered list to the document.

    Args:
        doc: Target document.
        items: List of text items.
        level: Indentation level (0 = top-level, 1 = sub-item, etc.).
    """
    for item in items:
        para = doc.add_paragraph(item, style="List Number")
        if level > 0:
            para.paragraph_format.left_indent = Inches(0.5 * level)


# Usage
doc = Document()
doc.add_heading("Key Findings", level=2)
add_bullet_list(doc, [
    "Revenue increased 15% year over year",
    "Customer retention rate improved to 94%",
    "Three new market segments identified",
])

doc.add_heading("Action Items", level=2)
add_numbered_list(doc, [
    "Finalize Q3 budget allocation by April 15",
    "Schedule stakeholder review meeting",
    "Submit compliance documentation to legal",
])
```

### Step 7: Mail Merge and Batch Generation

Data-driven document generation produces personalized documents at scale. Common use cases include contracts, certificates, letters, invoices, and compliance reports.

**Batch Document Generator**:

```python
from docxtpl import DocxTemplate
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import csv
import logging

logger = logging.getLogger(__name__)

@dataclass
class BatchResult:
    total: int
    succeeded: int
    failed: int
    errors: list[dict]
    output_paths: list[Path]

def generate_batch_documents(
    template_path: str | Path,
    data_source: str | Path,
    output_dir: str | Path,
    filename_pattern: str = "{index:04d}_{name}",
    max_workers: int = 4,
) -> BatchResult:
    """Generate multiple documents from a template and data source.

    Args:
        template_path: Path to the .docx template.
        data_source: Path to a JSON or CSV file containing row data.
        output_dir: Directory where generated documents are saved.
        filename_pattern: Pattern for output filenames. Supports {index}, {name},
            and any key from the data row.
        max_workers: Number of parallel workers for generation.

    Returns:
        BatchResult with counts and paths of generated documents.
    """
    template_path = Path(template_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    data_path = Path(data_source)
    if data_path.suffix == ".json":
        with open(data_path) as f:
            records = json.load(f)
    elif data_path.suffix == ".csv":
        with open(data_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)
    else:
        raise ValueError(f"Unsupported data format: {data_path.suffix}. Use .json or .csv")

    results = BatchResult(total=len(records), succeeded=0, failed=0, errors=[], output_paths=[])

    for index, record in enumerate(records):
        try:
            # Each iteration loads a fresh template to avoid state leakage
            tpl = DocxTemplate(str(template_path))

            context = {**record, "index": index}

            # Generate filename
            safe_name = record.get("name", f"doc_{index}").replace(" ", "_").replace("/", "_")
            filename = filename_pattern.format(index=index, name=safe_name, **record)
            output_path = output_dir / f"{filename}.docx"

            tpl.render(context)
            tpl.save(str(output_path))

            results.output_paths.append(output_path)
            results.succeeded += 1
            logger.info("Generated document %d/%d: %s", index + 1, results.total, output_path.name)

        except Exception as exc:
            results.failed += 1
            results.errors.append({
                "index": index,
                "record": record,
                "error": str(exc),
            })
            logger.error("Failed to generate document %d: %s", index, exc)

    return results


# Usage
result = generate_batch_documents(
    template_path="templates/certificate.docx",
    data_source="data/graduates.csv",
    output_dir="output/certificates",
    filename_pattern="{index:04d}_{name}",
)
print(f"Generated {result.succeeded}/{result.total} documents, {result.failed} failures")
```

**Conditional Sections in Templates**:

```
{# In the Word template, use paragraph-level conditionals for optional sections #}

{%p if contract_type == "enterprise" %}
ENTERPRISE SERVICE LEVEL AGREEMENT

This Enterprise SLA provides guaranteed 99.99% uptime with dedicated support
and a named account manager assigned to {{ client_name }}.
{%p endif %}

{%p if contract_type == "standard" %}
STANDARD SERVICE LEVEL AGREEMENT

This Standard SLA provides 99.9% uptime with business-hours support.
{%p endif %}

{%p if include_data_processing_addendum %}
DATA PROCESSING ADDENDUM

This addendum governs the processing of personal data under the agreement
between {{ company_name }} and {{ client_name }}, effective {{ effective_date }}.
{%p endif %}
```

**Mail Merge from Database**:

```python
from docxtpl import DocxTemplate
from pathlib import Path
import asyncio
import asyncpg

async def mail_merge_from_database(
    template_path: str | Path,
    output_dir: str | Path,
    db_url: str,
    query: str,
    filename_column: str = "id",
) -> list[Path]:
    """Generate documents by querying a database for merge data.

    Args:
        template_path: Path to the .docx template.
        output_dir: Directory for generated documents.
        db_url: PostgreSQL connection string.
        query: SQL query that returns one row per document.
        filename_column: Column used to name each output file.

    Returns:
        List of paths to generated documents.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    conn = await asyncpg.connect(db_url)
    try:
        rows = await conn.fetch(query)
        for row in rows:
            context = dict(row)
            tpl = DocxTemplate(str(template_path))
            tpl.render(context)

            filename = f"{context[filename_column]}.docx"
            output_path = output_dir / filename
            tpl.save(str(output_path))
            generated.append(output_path)
    finally:
        await conn.close()

    return generated


# Usage
# asyncio.run(mail_merge_from_database(
#     template_path="templates/invoice.docx",
#     output_dir="output/invoices",
#     db_url="postgresql://user:pass@localhost/billing",
#     query="SELECT * FROM invoices WHERE status = 'pending' AND issue_date = CURRENT_DATE",
#     filename_column="invoice_number",
# ))
```

**Merging Multiple DOCX Files**:

```python
from docx import Document
from docxcompose.composer import Composer
from pathlib import Path

def merge_documents(
    source_paths: list[str | Path],
    output_path: str | Path,
    add_page_breaks: bool = True,
) -> Path:
    """Merge multiple DOCX files into a single document.

    Requires the docxcompose package: pip install docxcompose

    Args:
        source_paths: Ordered list of .docx files to merge.
        output_path: Path for the combined document.
        add_page_breaks: Whether to insert a page break between documents.

    Returns:
        Path to the merged document.
    """
    if not source_paths:
        raise ValueError("At least one source document is required")

    base_doc = Document(str(source_paths[0]))
    composer = Composer(base_doc)

    for doc_path in source_paths[1:]:
        if add_page_breaks:
            composer.doc.add_page_break()
        sub_doc = Document(str(doc_path))
        composer.append(sub_doc)

    output = Path(output_path)
    composer.save(str(output))
    return output
```

**Critical Rules for Batch Generation**:

- Always load a fresh `DocxTemplate` instance for each document. Reusing a template after `render()` carries over state from the previous render
- Sanitize filenames derived from data fields. Remove or replace characters that are invalid in file paths (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`)
- For large batches (1000+ documents), generate sequentially rather than loading all templates into memory at once. Each `DocxTemplate` instance holds the full document in memory
- Validate your data source before starting the batch. A missing required field in row 500 wastes the time spent on rows 1-499 if the process aborts
- Log progress and errors to a file so that failed documents can be retried without re-generating successful ones

### Step 8: Testing and Validation

Document generation code requires testing strategies beyond typical unit tests. You must verify content correctness, style accuracy, structural integrity, and cross-platform rendering.

**Content Extraction for Assertions**:

```python
from docx import Document
from pathlib import Path

def extract_text(doc_path: str | Path) -> str:
    """Extract all text content from a DOCX file as a single string."""
    doc = Document(str(doc_path))
    parts: list[str] = []
    for para in doc.paragraphs:
        parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def extract_paragraphs(doc_path: str | Path) -> list[dict]:
    """Extract paragraphs with their style names and formatting metadata."""
    doc = Document(str(doc_path))
    results: list[dict] = []
    for para in doc.paragraphs:
        results.append({
            "text": para.text,
            "style": para.style.name if para.style else None,
            "alignment": str(para.alignment) if para.alignment else None,
            "runs": [
                {
                    "text": run.text,
                    "bold": run.bold,
                    "italic": run.italic,
                    "font_name": run.font.name,
                    "font_size": str(run.font.size) if run.font.size else None,
                }
                for run in para.runs
            ],
        })
    return results


def extract_table_data(doc_path: str | Path) -> list[list[list[str]]]:
    """Extract all tables as nested lists: tables -> rows -> cells."""
    doc = Document(str(doc_path))
    tables: list[list[list[str]]] = []
    for table in doc.tables:
        table_data: list[list[str]] = []
        for row in table.rows:
            table_data.append([cell.text for cell in row.cells])
        tables.append(table_data)
    return tables


def count_images(doc_path: str | Path) -> int:
    """Count the number of inline images in the document."""
    doc = Document(str(doc_path))
    return len(doc.inline_shapes)
```

**Pytest Test Suite for Document Generation**:

```python
import pytest
from pathlib import Path
from decimal import Decimal
from datetime import date

# Import your generator functions
# from my_project.generators import create_report, render_contract

FIXTURES_DIR = Path(__file__).parent / "fixtures"
OUTPUT_DIR = Path(__file__).parent / "output"


@pytest.fixture(autouse=True)
def setup_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield


class TestReportGeneration:
    def test_report_contains_title(self, tmp_path: Path) -> None:
        """The report title must appear as the first heading."""
        output = tmp_path / "report.docx"
        doc = create_report(
            title="Q3 Performance Review",
            author="Test Author",
            content=[{"heading": "Summary", "level": 1, "body": "Test content."}],
        )
        doc.save(str(output))

        paragraphs = extract_paragraphs(output)
        title_para = paragraphs[0]
        assert title_para["text"] == "Q3 Performance Review"
        assert title_para["style"] == "Title"

    def test_report_sections_in_order(self, tmp_path: Path) -> None:
        """All sections must appear in the order provided."""
        output = tmp_path / "report.docx"
        sections = [
            {"heading": "Introduction", "level": 1, "body": "Intro text."},
            {"heading": "Analysis", "level": 1, "body": "Analysis text."},
            {"heading": "Conclusion", "level": 1, "body": "Conclusion text."},
        ]
        doc = create_report(title="Test", author="Author", content=sections)
        doc.save(str(output))

        text = extract_text(output)
        intro_pos = text.index("Introduction")
        analysis_pos = text.index("Analysis")
        conclusion_pos = text.index("Conclusion")
        assert intro_pos < analysis_pos < conclusion_pos

    def test_report_has_correct_author_metadata(self, tmp_path: Path) -> None:
        """Document properties must reflect the author parameter."""
        output = tmp_path / "report.docx"
        doc = create_report(title="Test", author="Jane Doe", content=[])
        doc.save(str(output))

        from docx import Document
        doc_check = Document(str(output))
        assert doc_check.core_properties.author == "Jane Doe"

    def test_empty_content_produces_valid_document(self, tmp_path: Path) -> None:
        """An empty content list must still produce a valid DOCX file."""
        output = tmp_path / "report.docx"
        doc = create_report(title="Empty Report", author="Author", content=[])
        doc.save(str(output))

        # Verify the file is a valid DOCX (ZIP with expected structure)
        import zipfile
        assert zipfile.is_zipfile(str(output))
        with zipfile.ZipFile(str(output)) as zf:
            assert "word/document.xml" in zf.namelist()
            assert "[Content_Types].xml" in zf.namelist()


class TestContractTemplate:
    def test_contract_variables_substituted(self, tmp_path: Path) -> None:
        """All template variables must be replaced in the output."""
        output = tmp_path / "contract.docx"
        render_contract(
            template_path=FIXTURES_DIR / "contract_template.docx",
            output_path=output,
            context={
                "company_name": "Acme Corp",
                "client_name": "Widget Co",
                "contract_date": "January 1, 2026",
                "line_items": [],
                "grand_total": 0,
            },
        )
        text = extract_text(output)
        assert "Acme Corp" in text
        assert "Widget Co" in text
        assert "{{" not in text, "Unreplaced template variables found"

    def test_line_items_table_populated(self, tmp_path: Path) -> None:
        """The line items table must contain one row per item."""
        output = tmp_path / "contract.docx"
        items = [
            {"description": "Service A", "quantity": 10, "rate": 100.00, "total": 1000.00},
            {"description": "Service B", "quantity": 5, "rate": 200.00, "total": 1000.00},
        ]
        render_contract(
            template_path=FIXTURES_DIR / "contract_template.docx",
            output_path=output,
            context={
                "company_name": "Test",
                "client_name": "Test",
                "contract_date": "January 1, 2026",
                "line_items": items,
                "grand_total": 2000.00,
            },
        )
        tables = extract_table_data(output)
        # Find the table that contains line items (has "Service A" in it)
        line_item_table = None
        for table in tables:
            for row in table:
                if "Service A" in row:
                    line_item_table = table
                    break
        assert line_item_table is not None, "Line items table not found"
        # Subtract 1 for header row
        data_rows = [r for r in line_item_table if "Service A" in r or "Service B" in r]
        assert len(data_rows) == 2

    def test_conditional_section_included(self, tmp_path: Path) -> None:
        """Conditional sections must appear when their flag is True."""
        output = tmp_path / "contract.docx"
        render_contract(
            template_path=FIXTURES_DIR / "contract_template.docx",
            output_path=output,
            context={
                "company_name": "Test",
                "client_name": "Test",
                "contract_date": "January 1, 2026",
                "line_items": [],
                "grand_total": 0,
                "include_nda_clause": True,
            },
        )
        text = extract_text(output)
        assert "NON-DISCLOSURE" in text.upper() or "NDA" in text.upper()

    def test_conditional_section_excluded(self, tmp_path: Path) -> None:
        """Conditional sections must not appear when their flag is False."""
        output = tmp_path / "contract.docx"
        render_contract(
            template_path=FIXTURES_DIR / "contract_template.docx",
            output_path=output,
            context={
                "company_name": "Test",
                "client_name": "Test",
                "contract_date": "January 1, 2026",
                "line_items": [],
                "grand_total": 0,
                "include_nda_clause": False,
            },
        )
        text = extract_text(output)
        assert "NON-DISCLOSURE" not in text.upper()


class TestBatchGeneration:
    def test_batch_produces_correct_count(self, tmp_path: Path) -> None:
        """Batch generation must produce one document per data record."""
        data_path = tmp_path / "data.json"
        data_path.write_text(json.dumps([
            {"name": "Alice Johnson", "title": "Certificate of Completion"},
            {"name": "Bob Smith", "title": "Certificate of Completion"},
            {"name": "Carol Davis", "title": "Certificate of Completion"},
        ]))
        result = generate_batch_documents(
            template_path=FIXTURES_DIR / "certificate_template.docx",
            data_source=data_path,
            output_dir=tmp_path / "output",
        )
        assert result.succeeded == 3
        assert result.failed == 0
        assert len(result.output_paths) == 3

    def test_batch_handles_missing_field_gracefully(self, tmp_path: Path) -> None:
        """Missing fields in data records must be reported as errors, not crashes."""
        data_path = tmp_path / "data.json"
        data_path.write_text(json.dumps([
            {"name": "Alice Johnson"},  # missing required 'title' field
        ]))
        result = generate_batch_documents(
            template_path=FIXTURES_DIR / "certificate_template.docx",
            data_source=data_path,
            output_dir=tmp_path / "output",
        )
        # Depending on template, this may succeed with empty field or fail
        assert result.total == 1
        assert (result.succeeded + result.failed) == 1


class TestDocumentStructure:
    def test_docx_is_valid_zip(self, tmp_path: Path) -> None:
        """Every generated DOCX must be a valid ZIP archive with required entries."""
        import zipfile
        output = tmp_path / "test.docx"
        doc = Document()
        doc.add_paragraph("Test content")
        doc.save(str(output))

        assert zipfile.is_zipfile(str(output))
        with zipfile.ZipFile(str(output)) as zf:
            names = zf.namelist()
            assert "[Content_Types].xml" in names
            assert "word/document.xml" in names

    def test_styles_preserved_after_generation(self, tmp_path: Path) -> None:
        """Custom styles applied during generation must persist in the saved file."""
        output = tmp_path / "styled.docx"
        doc = Document()
        define_custom_styles(doc)
        doc.add_paragraph("Styled text", style="Custom Body")
        doc.save(str(output))

        doc_check = Document(str(output))
        styles = [s.name for s in doc_check.styles]
        assert "Custom Body" in styles
```

**Document Comparison Utility**:

```python
from docx import Document
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DocumentDiff:
    paragraphs_added: list[str]
    paragraphs_removed: list[str]
    paragraphs_changed: list[dict]
    tables_added: int
    tables_removed: int
    images_added: int
    images_removed: int

def compare_documents(doc_a_path: str | Path, doc_b_path: str | Path) -> DocumentDiff:
    """Compare two DOCX files and return structural differences.

    This is a content-level comparison, not a formatting comparison.
    Useful for regression testing document generators.
    """
    doc_a = Document(str(doc_a_path))
    doc_b = Document(str(doc_b_path))

    texts_a = [p.text for p in doc_a.paragraphs]
    texts_b = [p.text for p in doc_b.paragraphs]

    set_a = set(texts_a)
    set_b = set(texts_b)

    return DocumentDiff(
        paragraphs_added=sorted(set_b - set_a),
        paragraphs_removed=sorted(set_a - set_b),
        paragraphs_changed=[],  # Would require fuzzy matching for real diff
        tables_added=max(0, len(doc_b.tables) - len(doc_a.tables)),
        tables_removed=max(0, len(doc_a.tables) - len(doc_b.tables)),
        images_added=max(0, len(doc_b.inline_shapes) - len(doc_a.inline_shapes)),
        images_removed=max(0, len(doc_a.inline_shapes) - len(doc_b.inline_shapes)),
    )
```

**Cross-Platform Validation Checklist**:

- Verify that documents open without errors in Microsoft Word (Windows and macOS)
- Verify rendering in LibreOffice Writer (Linux compatibility)
- Check that field codes (TOC, page numbers) update correctly when "Update Fields" is triggered
- Validate that images render at the correct size and do not overflow page margins
- Test with the Word Online viewer for web-based access scenarios
- Verify that documents pass the OOXML Validator if strict compliance is required

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

## Quality Checklist

- [ ] Library selection justified with a documented trade-off analysis for the project
- [ ] Document templates stored in version control with sample rendering tests
- [ ] All template variables validated against the data schema before rendering
- [ ] Custom styles defined in a central function and applied by name (no scattered direct formatting)
- [ ] Headers, footers, and page numbers configured for all sections
- [ ] Images sized appropriately and tested for page overflow
- [ ] Batch generation handles errors per-record without aborting the entire batch
- [ ] Output documents validated as structurally correct ZIP archives with required OOXML entries
- [ ] Content extraction tests verify that all data fields appear in the rendered output
- [ ] No unreplaced template tags (`{{`, `{%`) remain in generated documents
- [ ] Cross-platform rendering verified in Word, LibreOffice, and Word Online
- [ ] Document properties (title, author, subject) set correctly
- [ ] Unicode and multi-byte characters render correctly in all text positions
- [ ] File sizes are reasonable (images optimized, no unnecessary embedded resources)
- [ ] CI pipeline includes a template rendering smoke test with sample data

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
