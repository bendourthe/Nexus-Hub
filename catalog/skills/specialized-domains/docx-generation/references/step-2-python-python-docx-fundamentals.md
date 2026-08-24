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
