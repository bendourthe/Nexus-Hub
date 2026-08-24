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
