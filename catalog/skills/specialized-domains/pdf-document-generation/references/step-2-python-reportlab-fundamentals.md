### Step 2: Python ReportLab Fundamentals

ReportLab provides two layers: a low-level canvas API for absolute positioning and a high-level "platypus" (Page Layout and Typography Using Scripts) framework for flowable document construction. Production systems almost always use platypus because it handles page breaks, text wrapping, and multi-page layouts automatically.

**Basic Document with Platypus**:

```python
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from pathlib import Path


def create_invoice(
    invoice_number: str,
    client_name: str,
    line_items: list[dict],
    output_path: str | Path,
) -> None:
    """Generate a professional invoice PDF.

    Each line_item dict has keys: description, quantity, unit_price, total.
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=HexColor("#1a1a2e"),
        spaceAfter=6 * mm,
    )
    header_style = ParagraphStyle(
        "InvoiceHeader",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#555555"),
        spaceAfter=2 * mm,
    )
    body_style = ParagraphStyle(
        "InvoiceBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )

    elements: list = []

    # Company header
    elements.append(Paragraph("ACME Corporation", title_style))
    elements.append(Paragraph("123 Business Ave, Suite 100", header_style))
    elements.append(Paragraph("contact@acme.example.com", header_style))
    elements.append(Spacer(1, 10 * mm))

    # Invoice metadata
    elements.append(Paragraph(f"Invoice #{invoice_number}", styles["Heading2"]))
    elements.append(Paragraph(f"Bill to: {client_name}", body_style))
    elements.append(Spacer(1, 8 * mm))

    # Line items table
    table_data = [["Description", "Qty", "Unit Price", "Total"]]
    for item in line_items:
        table_data.append([
            item["description"],
            str(item["quantity"]),
            f"${item['unit_price']:.2f}",
            f"${item['total']:.2f}",
        ])

    # Summary row
    grand_total = sum(item["total"] for item in line_items)
    table_data.append(["", "", "Grand Total:", f"${grand_total:.2f}"])

    table = Table(table_data, colWidths=[80 * mm, 20 * mm, 30 * mm, 30 * mm])
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        # Body rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [HexColor("#f8f8f8"), HexColor("#ffffff")]),
        ("GRID", (0, 0), (-1, -2), 0.5, HexColor("#cccccc")),
        # Total row
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (2, -1), (-1, -1), 1.5, HexColor("#1a1a2e")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 15 * mm))

    # Payment terms
    elements.append(Paragraph("Payment Terms", styles["Heading3"]))
    elements.append(Paragraph(
        "Payment is due within 30 days of invoice date. "
        "Please reference the invoice number in your payment.",
        body_style,
    ))

    doc.build(elements)
```

**Page Templates with Headers and Footers**:

```python
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from datetime import date


def header_footer(canvas, doc):
    """Draw header and footer on every page."""
    canvas.saveState()

    # Header: company name and horizontal rule
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(20 * mm, A4[1] - 15 * mm, "ACME Corporation")
    canvas.setStrokeColorRGB(0.1, 0.1, 0.18)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, A4[1] - 17 * mm, A4[0] - 20 * mm, A4[1] - 17 * mm)

    # Footer: page number and date
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.4, 0.4, 0.4)
    canvas.drawString(20 * mm, 12 * mm, f"Generated {date.today().isoformat()}")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")

    canvas.restoreState()


def create_multi_page_report(output_path: str, content_elements: list) -> None:
    """Create a report with consistent headers and footers on every page."""
    doc = BaseDocTemplate(output_path, pagesize=A4)

    frame = Frame(
        20 * mm,                    # x
        20 * mm,                    # y
        A4[0] - 40 * mm,           # width
        A4[1] - 50 * mm,           # height (leaves room for header/footer)
        id="main_frame",
    )

    template = PageTemplate(
        id="standard",
        frames=[frame],
        onPage=header_footer,
    )
    doc.addPageTemplates([template])
    doc.build(content_elements)
```

**Embedding Images**:

```python
from reportlab.platypus import Image
from reportlab.lib.units import mm

# From file path
logo = Image("assets/logo.png", width=40 * mm, height=15 * mm)

# From URL or bytes (wrap in BytesIO)
from io import BytesIO
import httpx

response = httpx.get("https://example.com/chart.png", timeout=30)
chart_image = Image(BytesIO(response.content), width=160 * mm, height=100 * mm)
```

**Custom Fonts**:

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a TrueType font family
pdfmetrics.registerFont(TTFont("Inter", "fonts/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Bold", "fonts/Inter-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Italic", "fonts/Inter-Italic.ttf"))

# Map font family for automatic bold/italic selection in paragraphs
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Inter", normal="Inter", bold="Inter-Bold", italic="Inter-Italic")

# Use in ParagraphStyle
style = ParagraphStyle("CustomBody", fontName="Inter", fontSize=10, leading=14)
```
