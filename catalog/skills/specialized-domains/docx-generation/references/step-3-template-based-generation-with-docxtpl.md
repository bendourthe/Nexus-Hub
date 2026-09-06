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
