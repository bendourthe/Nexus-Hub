### Step 8: Testing and Validation

PDF output must be validated for content correctness, visual fidelity, file size, and cross-viewer compatibility. Unlike web pages, PDFs cannot be inspected in a browser DevTools panel, so you need specialized tools and strategies.

**Content Extraction for Assertions** (Python, using pdfplumber):

```python
import pdfplumber
from pathlib import Path


def extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract all text content from a PDF for assertion testing."""
    text_parts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_pdf_tables(pdf_path: str | Path, page_number: int = 0) -> list[list]:
    """Extract table data from a specific page."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[page_number]
        tables = page.extract_tables()
        return tables


def get_pdf_metadata(pdf_path: str | Path) -> dict:
    """Extract PDF metadata (title, author, page count, dimensions)."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        return {
            "page_count": len(pdf.pages),
            "metadata": pdf.metadata,
            "pages": [
                {
                    "width": page.width,
                    "height": page.height,
                    "page_number": page.page_number,
                }
                for page in pdf.pages
            ],
        }
```

**Pytest Fixtures and Assertions for PDF Content**:

```python
import pytest
from pathlib import Path
from decimal import Decimal


@pytest.fixture
def invoice_data():
    return {
        "number": "INV-2025-001",
        "client_name": "Globex Corporation",
        "line_items": [
            {"description": "Consulting", "quantity": 40, "unit_price": 150.00, "total": 6000.00},
            {"description": "Development", "quantity": 80, "unit_price": 200.00, "total": 16000.00},
        ],
        "total": 22000.00,
    }


@pytest.fixture
def generated_invoice(tmp_path, invoice_data):
    output_path = tmp_path / "test_invoice.pdf"
    create_invoice(
        invoice_number=invoice_data["number"],
        client_name=invoice_data["client_name"],
        line_items=invoice_data["line_items"],
        output_path=output_path,
    )
    return output_path


def test_invoice_contains_invoice_number(generated_invoice, invoice_data):
    text = extract_pdf_text(generated_invoice)
    assert invoice_data["number"] in text


def test_invoice_contains_client_name(generated_invoice, invoice_data):
    text = extract_pdf_text(generated_invoice)
    assert invoice_data["client_name"] in text


def test_invoice_contains_line_items(generated_invoice, invoice_data):
    text = extract_pdf_text(generated_invoice)
    for item in invoice_data["line_items"]:
        assert item["description"] in text


def test_invoice_contains_total(generated_invoice, invoice_data):
    text = extract_pdf_text(generated_invoice)
    formatted_total = f"${invoice_data['total']:,.2f}"
    assert formatted_total in text


def test_invoice_page_count(generated_invoice):
    meta = get_pdf_metadata(generated_invoice)
    assert meta["page_count"] == 1


def test_invoice_page_size_is_a4(generated_invoice):
    meta = get_pdf_metadata(generated_invoice)
    page = meta["pages"][0]
    # A4 in PDF points: 595.28 x 841.89 (allow small tolerance)
    assert abs(page["width"] - 595.28) < 1
    assert abs(page["height"] - 841.89) < 1


def test_invoice_file_size_is_reasonable(generated_invoice):
    size_kb = generated_invoice.stat().st_size / 1024
    assert size_kb < 500, f"Invoice PDF is {size_kb:.1f} KB, expected under 500 KB"
```

**Visual Regression Testing** (comparing rendered pages as images):

```python
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import hashlib


def pdf_to_images(pdf_path: str | Path, dpi: int = 150) -> list[Image.Image]:
    """Convert each PDF page to a PIL Image for visual comparison."""
    return convert_from_path(str(pdf_path), dpi=dpi)


def image_hash(image: Image.Image) -> str:
    """Compute a perceptual hash for quick equality checks."""
    # Resize to a small thumbnail and hash the pixel data
    thumb = image.resize((64, 64)).convert("L")
    return hashlib.sha256(thumb.tobytes()).hexdigest()


def compare_pdf_visual(
    actual_path: str | Path,
    expected_path: str | Path,
    dpi: int = 150,
    pixel_threshold: float = 0.01,
) -> list[dict]:
    """Compare two PDFs page by page and report visual differences.

    Returns a list of diffs. Empty list means the PDFs are visually identical.
    pixel_threshold: fraction of pixels that may differ (0.01 = 1%).
    """
    actual_images = pdf_to_images(actual_path, dpi)
    expected_images = pdf_to_images(expected_path, dpi)
    diffs = []

    if len(actual_images) != len(expected_images):
        diffs.append({
            "type": "page_count_mismatch",
            "actual": len(actual_images),
            "expected": len(expected_images),
        })
        return diffs

    for page_num, (actual_img, expected_img) in enumerate(
        zip(actual_images, expected_images), start=1
    ):
        if actual_img.size != expected_img.size:
            diffs.append({
                "type": "size_mismatch",
                "page": page_num,
                "actual": actual_img.size,
                "expected": expected_img.size,
            })
            continue

        # Pixel-level comparison
        import numpy as np
        actual_arr = np.array(actual_img)
        expected_arr = np.array(expected_img)
        diff_pixels = np.sum(actual_arr != expected_arr)
        total_pixels = actual_arr.size
        diff_ratio = diff_pixels / total_pixels

        if diff_ratio > pixel_threshold:
            diffs.append({
                "type": "visual_difference",
                "page": page_num,
                "diff_ratio": diff_ratio,
            })

    return diffs


def test_invoice_visual_regression(generated_invoice, tmp_path):
    """Compare generated invoice against a known-good reference PDF.

    To update the reference: copy a manually verified PDF to
    tests/fixtures/invoice_reference.pdf
    """
    reference_path = Path("tests/fixtures/invoice_reference.pdf")
    if not reference_path.exists():
        pytest.skip("No reference PDF found. Generate one and save to tests/fixtures/.")

    diffs = compare_pdf_visual(generated_invoice, reference_path)
    assert diffs == [], f"Visual differences detected: {diffs}"
```

**File Size Optimization Strategies**:

```python
import pikepdf


def optimize_pdf(input_path: str, output_path: str) -> dict:
    """Optimize a PDF for smaller file size.

    Returns a dict with before/after sizes.
    """
    original_size = Path(input_path).stat().st_size

    with pikepdf.open(input_path) as pdf:
        # Remove unused objects
        pdf.remove_unreferenced_resources()

        # Compress streams
        pdf.save(
            output_path,
            linearize=True,              # optimize for web viewing (fast first page)
            compress_streams=True,        # deflate all content streams
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            recompress_flate=True,        # recompress with better settings
        )

    optimized_size = Path(output_path).stat().st_size
    return {
        "original_bytes": original_size,
        "optimized_bytes": optimized_size,
        "reduction_pct": round(
            (1 - optimized_size / original_size) * 100, 1
        ),
    }
```

**Image Compression Within PDFs**: The single largest contributor to PDF file size is images. Before embedding images in a PDF, resize them to the target display resolution (typically 150-300 DPI at the printed size) and compress them as JPEG for photographs or PNG for diagrams with transparency. A 4000x3000 pixel photograph displayed at 100mm wide only needs ~590 pixels wide at 150 DPI. Embedding the full-resolution image wastes space without improving print quality.

```python
from PIL import Image as PILImage
from io import BytesIO


def prepare_image_for_pdf(
    image_path: str,
    max_width_mm: float,
    dpi: int = 150,
    jpeg_quality: int = 85,
) -> BytesIO:
    """Resize and compress an image for PDF embedding.

    Returns a BytesIO buffer containing the optimized JPEG.
    """
    target_width_px = int(max_width_mm / 25.4 * dpi)

    with PILImage.open(image_path) as img:
        # Only downscale, never upscale
        if img.width > target_width_px:
            ratio = target_width_px / img.width
            new_size = (target_width_px, int(img.height * ratio))
            img = img.resize(new_size, PILImage.LANCZOS)

        # Convert RGBA to RGB (JPEG does not support transparency)
        if img.mode == "RGBA":
            background = PILImage.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=jpeg_quality, optimize=True)
        buffer.seek(0)
        return buffer
```

**Cross-Viewer Compatibility Checklist**:

When validating PDF output, test in multiple viewers because each renderer has different capabilities and quirks:

| Viewer | Key Differences |
|---|---|
| Adobe Acrobat Reader | Full spec support; most reliable reference. Test form fields and signatures here. |
| Chrome/Edge built-in | No form fill support; limited annotation rendering. Tests basic layout and text. |
| Firefox built-in (pdf.js) | JavaScript-based renderer; may differ on complex gradients, transparency, and fonts. |
| Preview (macOS) | Good general rendering but may struggle with advanced features (JavaScript actions, certain form types). |
| Evince/Okular (Linux) | Poppler-based; handles most features well. Test Unicode and CJK font embedding here. |

**Automated validation script** (run as part of CI):

```python
import subprocess
from pathlib import Path


def validate_pdf_structure(pdf_path: str | Path) -> dict:
    """Validate PDF structure using QPDF (must be installed).

    QPDF checks for structural errors, linearization, and encryption status.
    Install: apt install qpdf (Linux), brew install qpdf (macOS).
    """
    result = subprocess.run(
        ["qpdf", "--check", str(pdf_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return {
        "valid": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def validate_pdf_a_compliance(pdf_path: str | Path) -> dict:
    """Validate PDF/A compliance using VeraPDF (must be installed).

    VeraPDF is the industry-standard open-source PDF/A validator.
    Install: https://verapdf.org/software/
    """
    result = subprocess.run(
        ["verapdf", "--format", "text", str(pdf_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "compliant": "PASS" in result.stdout,
        "output": result.stdout.strip(),
    }
```

**Summary of Testing Strategy**:

| Test Type | Tool | What It Validates |
|---|---|---|
| Content assertions | pdfplumber, PyMuPDF | Text, tables, metadata are present and correct |
| Visual regression | pdf2image + Pillow/numpy | Layout has not shifted between code changes |
| Structural validation | QPDF | PDF is well-formed and not corrupted |
| PDF/A compliance | VeraPDF | Meets archival standard requirements |
| Accessibility | PAC (PDF Accessibility Checker) | Screen reader compatibility, tag structure |
| File size | pathlib stat | Output stays within budget (avoids image bloat) |
| Cross-viewer | Manual spot-check matrix | Renders correctly in Acrobat, Chrome, Firefox, Preview |
