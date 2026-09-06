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
