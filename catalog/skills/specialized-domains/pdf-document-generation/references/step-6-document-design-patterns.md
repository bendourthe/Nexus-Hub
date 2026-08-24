### Step 6: Document Design Patterns

Production PDF documents require structural elements beyond raw content: cover pages, tables of contents, page numbering, watermarks, and navigational bookmarks. These patterns apply across all libraries.

**Cover Page** (ReportLab):

```python
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER


def build_cover_page(elements: list, title: str, subtitle: str, author: str) -> None:
    """Append cover page elements to the document flow."""
    cover_title = ParagraphStyle(
        "CoverTitle",
        fontSize=36,
        fontName="Helvetica-Bold",
        textColor=HexColor("#1a1a2e"),
        alignment=TA_CENTER,
        spaceAfter=10 * mm,
    )
    cover_subtitle = ParagraphStyle(
        "CoverSubtitle",
        fontSize=16,
        fontName="Helvetica",
        textColor=HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=20 * mm,
    )
    cover_author = ParagraphStyle(
        "CoverAuthor",
        fontSize=12,
        fontName="Helvetica",
        textColor=HexColor("#888888"),
        alignment=TA_CENTER,
    )

    elements.append(Spacer(1, 80 * mm))
    elements.append(Paragraph(title, cover_title))
    elements.append(Paragraph(subtitle, cover_subtitle))
    elements.append(Paragraph(f"Prepared by: {author}", cover_author))
    elements.append(PageBreak())
```

**Table of Contents** (ReportLab):

```python
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, TableOfContents,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def create_report_with_toc(output_path: str, chapters: list[dict]) -> None:
    """Generate a report with an auto-generated table of contents.

    Each chapter: {"title": str, "level": int, "content": list[Flowable]}
    """
    doc = BaseDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()

    # TOC styles for each heading level
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCLevel0", fontName="Helvetica-Bold", fontSize=12,
            leftIndent=0, spaceBefore=6,
        ),
        ParagraphStyle(
            "TOCLevel1", fontName="Helvetica", fontSize=10,
            leftIndent=20, spaceBefore=3,
        ),
        ParagraphStyle(
            "TOCLevel2", fontName="Helvetica", fontSize=9,
            leftIndent=40, spaceBefore=2,
        ),
    ]

    frame = Frame(
        20 * mm, 20 * mm,
        A4[0] - 40 * mm, A4[1] - 50 * mm,
        id="main",
    )
    template = PageTemplate(id="standard", frames=[frame])
    doc.addPageTemplates([template])

    elements = []

    # TOC page
    elements.append(Paragraph("Table of Contents", styles["Heading1"]))
    elements.append(toc)
    elements.append(PageBreak())

    # Chapter content
    heading_styles = {
        0: ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18),
        1: ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14),
        2: ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12),
    }

    for chapter in chapters:
        level = chapter.get("level", 0)
        heading = Paragraph(chapter["title"], heading_styles[level])
        # Notify the TOC about this heading
        doc.notify("TOCEntry", (level, chapter["title"], doc.page))
        elements.append(heading)
        elements.extend(chapter["content"])

    doc.multiBuild(elements)
```

**Watermarks** (ReportLab canvas-level):

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color


def add_watermark(canvas, doc, text="DRAFT", opacity=0.08):
    """Draw a diagonal watermark across the page."""
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 72)
    canvas.setFillColor(Color(0, 0, 0, alpha=opacity))
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, text)
    canvas.restoreState()


def header_footer_with_watermark(canvas, doc):
    """Combined header, footer, and watermark callback."""
    add_watermark(canvas, doc, text="CONFIDENTIAL", opacity=0.06)
    # Add regular header/footer
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()
```

**Bookmarks and Outlines** (PDFKit):

```javascript
function addBookmarkedSections(doc, sections) {
  for (const section of sections) {
    // Create an outline entry (bookmark) pointing to the current position
    const outlineRef = doc.outline.addItem(section.title);

    doc
      .fontSize(18)
      .font("Helvetica-Bold")
      .text(section.title);

    doc
      .fontSize(10)
      .font("Helvetica")
      .text(section.body)
      .moveDown(2);

    // Nested bookmarks for subsections
    if (section.subsections) {
      for (const sub of section.subsections) {
        outlineRef.addItem(sub.title);
        doc.fontSize(14).font("Helvetica-Bold").text(sub.title);
        doc.fontSize(10).font("Helvetica").text(sub.body).moveDown(1);
      }
    }

    doc.addPage();
  }
}
```

**Page Numbering with "Page X of Y"** (Puppeteer):

Puppeteer's `footerTemplate` supports built-in CSS classes that are replaced at render time:

```javascript
const footerTemplate = `
  <div style="font-size:8px; color:#666; width:100%;
              text-align:center; padding: 5mm 0;">
    Page <span class="pageNumber"></span>
    of <span class="totalPages"></span>
  </div>`;

// Available template variables:
// <span class="date"></span>        - formatted print date
// <span class="title"></span>       - document title
// <span class="url"></span>         - document URL
// <span class="pageNumber"></span>  - current page number
// <span class="totalPages"></span>  - total page count
```
