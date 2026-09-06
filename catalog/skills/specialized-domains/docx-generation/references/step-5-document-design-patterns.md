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
