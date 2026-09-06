### Step 7: Advanced Features

Production PDF workflows often require interactive form fields, digital signatures for legal validity, archival-format compliance, accessibility for screen readers, and encryption for document security.

**PDF Form Fields** (ReportLab):

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as canvas_module


def create_form_pdf(output_path: str) -> None:
    """Create a PDF with interactive form fields."""
    c = canvas_module.Canvas(output_path, pagesize=A4)
    form = c.acroForm

    c.setFont("Helvetica", 12)
    c.drawString(20 * mm, A4[1] - 30 * mm, "Contract Agreement Form")

    # Text input field
    c.drawString(20 * mm, A4[1] - 50 * mm, "Full Name:")
    form.textfield(
        name="full_name",
        tooltip="Enter your full legal name",
        x=60 * mm,
        y=A4[1] - 53 * mm,
        width=100 * mm,
        height=8 * mm,
        borderStyle="inset",
        forceBorder=True,
    )

    # Checkbox
    c.drawString(20 * mm, A4[1] - 70 * mm, "I agree to the terms:")
    form.checkbox(
        name="agree_terms",
        tooltip="Check to agree",
        x=75 * mm,
        y=A4[1] - 73 * mm,
        size=5 * mm,
        buttonStyle="check",
        borderColor=None,
        fillColor=None,
        forceBorder=True,
    )

    # Dropdown selection
    c.drawString(20 * mm, A4[1] - 90 * mm, "Contract Type:")
    form.choice(
        name="contract_type",
        tooltip="Select contract type",
        options=["Fixed Price", "Time and Materials", "Retainer"],
        value="Fixed Price",
        x=60 * mm,
        y=A4[1] - 93 * mm,
        width=80 * mm,
        height=8 * mm,
        forceBorder=True,
    )

    # Date field (text input with format hint)
    c.drawString(20 * mm, A4[1] - 110 * mm, "Effective Date:")
    form.textfield(
        name="effective_date",
        tooltip="YYYY-MM-DD",
        x=60 * mm,
        y=A4[1] - 113 * mm,
        width=50 * mm,
        height=8 * mm,
        forceBorder=True,
    )

    # Multi-line text area
    c.drawString(20 * mm, A4[1] - 130 * mm, "Additional Notes:")
    form.textfield(
        name="notes",
        tooltip="Enter any additional notes",
        x=20 * mm,
        y=A4[1] - 170 * mm,
        width=170 * mm,
        height=30 * mm,
        fieldFlags="multiline",
        forceBorder=True,
    )

    c.save()
```

**Digital Signatures** (using pyHanko for PAdES-compliant signatures):

```python
from pyhanko.sign import signers, fields
from pyhanko.sign.general import load_cert_list
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pathlib import Path


def sign_pdf(
    input_path: str | Path,
    output_path: str | Path,
    pfx_path: str | Path,
    pfx_password: str,
    signer_name: str,
    reason: str = "Document approval",
    location: str = "Remote",
) -> None:
    """Apply a PAdES-B digital signature to a PDF document.

    Requires a PKCS#12 (.pfx/.p12) file containing the signing certificate
    and private key.
    """
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=str(pfx_path),
        passphrase=pfx_password.encode(),
    )

    with open(input_path, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)

        # Add a signature field if one does not already exist
        fields.append_signature_field(
            writer,
            sig_field_spec=fields.SigFieldSpec(
                sig_field_name="Signature1",
                on_page=0,
                box=(50, 50, 250, 100),  # x1, y1, x2, y2 in PDF points
            ),
        )

        meta = signers.PdfSignatureMetadata(
            field_name="Signature1",
            name=signer_name,
            reason=reason,
            location=location,
        )

        with open(output_path, "wb") as outf:
            signers.sign_pdf(
                writer,
                signature_meta=meta,
                signer=signer,
                output=outf,
            )
```

**PDF/A Compliance** (ReportLab):

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def create_pdfa_document(output_path: str, content_elements: list) -> None:
    """Create a PDF/A-1b compliant document for long-term archival.

    PDF/A requirements:
    - All fonts must be embedded (ReportLab embeds by default with TTF)
    - No JavaScript or executable content
    - No encryption
    - Color spaces must be explicitly defined
    - XMP metadata is required
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        title="Archived Report",
        author="ACME Corporation",
        subject="Archival Document",
    )

    # ReportLab does not produce PDF/A natively.
    # Use reportlab + pikepdf or pdfa-pillar for post-processing:
    doc.build(content_elements)

    # Post-process with pikepdf to add PDF/A metadata
    import pikepdf

    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["dc:title"] = "Archived Report"
            meta["dc:creator"] = ["ACME Corporation"]
            meta["pdfaid:part"] = "1"
            meta["pdfaid:conformance"] = "B"
        pdf.save(output_path)
```

**Accessibility Tagging** (marked content for screen readers):

```python
def create_tagged_content(canvas, doc):
    """Add tagged (accessible) content to a PDF.

    Tagged PDF associates structural tags (H1, P, Table, etc.) with content,
    enabling screen readers to navigate the document logically.

    Note: Full tagged PDF support requires low-level PDF manipulation.
    For production accessible PDFs, WeasyPrint + post-processing or
    Puppeteer (which inherits HTML semantics) are more practical than
    hand-tagging with ReportLab.
    """
    # ReportLab canvas supports basic marked content
    canvas.beginMarkedContent("H1")
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(72, 750, "Quarterly Report")
    canvas.endMarkedContent()

    canvas.beginMarkedContent("P")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(72, 720, "This section summarizes Q4 performance metrics.")
    canvas.endMarkedContent()
```

**Practical approach to accessible PDFs**: The most reliable way to produce accessible PDFs is to start with well-structured semantic HTML (proper heading hierarchy, table headers with `<th scope>`, alt text on images, `lang` attribute) and convert it to PDF using Puppeteer or WeasyPrint. The HTML semantics carry over into the PDF structure, producing a document that screen readers can navigate. Post-process with a tool like PAC (PDF Accessibility Checker) to verify WCAG compliance.

**Encryption and Permissions** (pikepdf):

```python
import pikepdf


def encrypt_pdf(
    input_path: str,
    output_path: str,
    user_password: str = "",
    owner_password: str = "",
    allow_printing: bool = True,
    allow_copying: bool = False,
    allow_modification: bool = False,
) -> None:
    """Encrypt a PDF with password protection and permission controls.

    user_password: required to open the document (empty string = no open password)
    owner_password: required to change permissions or remove encryption
    """
    permissions = pikepdf.Permissions(
        print_lowres=allow_printing,
        print_highres=allow_printing,
        extract=allow_copying,
        modify_annotation=allow_modification,
        modify_form=allow_modification,
        modify_assembly=allow_modification,
        modify_other=allow_modification,
    )

    with pikepdf.open(input_path) as pdf:
        pdf.save(
            output_path,
            encryption=pikepdf.Encryption(
                user=user_password,
                owner=owner_password,
                R=6,               # AES-256 encryption (PDF 2.0)
                allow=permissions,
            ),
        )
```
