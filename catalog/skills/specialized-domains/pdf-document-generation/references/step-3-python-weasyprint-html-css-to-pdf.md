### Step 3: Python WeasyPrint (HTML/CSS to PDF)

WeasyPrint converts HTML and CSS into PDF using the CSS Paged Media specification. If your document content is already structured as HTML (or can be rendered from a template engine like Jinja2), WeasyPrint produces high-quality PDF output with minimal code.

**Basic HTML-to-PDF Conversion**:

```python
import weasyprint
from pathlib import Path


def html_string_to_pdf(html_content: str, output_path: str | Path) -> None:
    """Convert an HTML string to PDF."""
    doc = weasyprint.HTML(string=html_content)
    doc.write_pdf(str(output_path))


def html_file_to_pdf(html_path: str | Path, output_path: str | Path) -> None:
    """Convert an HTML file to PDF, resolving relative asset paths."""
    doc = weasyprint.HTML(filename=str(html_path))
    doc.write_pdf(str(output_path))


def url_to_pdf(url: str, output_path: str | Path) -> None:
    """Convert a web page to PDF."""
    doc = weasyprint.HTML(url=url)
    doc.write_pdf(str(output_path))
```

**Jinja2 Template Rendering with WeasyPrint**:

```python
from jinja2 import Environment, FileSystemLoader
import weasyprint
from pathlib import Path
from decimal import Decimal


def render_invoice_pdf(
    template_dir: str | Path,
    invoice_data: dict,
    output_path: str | Path,
) -> None:
    """Render an invoice from a Jinja2 HTML template to PDF.

    invoice_data keys: number, date, client_name, client_address,
                       line_items (list of dicts), total.
    """
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("invoice.html")
    html_content = template.render(**invoice_data)

    # Base URL allows WeasyPrint to resolve relative CSS/image paths
    base_url = str(Path(template_dir).resolve())
    doc = weasyprint.HTML(string=html_content, base_url=base_url)
    doc.write_pdf(str(output_path))
```

**Invoice HTML Template** (`invoice.html`):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    @page {
      size: A4;
      margin: 20mm 20mm 25mm 20mm;

      @top-right {
        content: "Invoice #{{ number }}";
        font-size: 8pt;
        color: #888;
      }
      @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #888;
      }
    }

    body {
      font-family: "Helvetica Neue", Arial, sans-serif;
      font-size: 10pt;
      line-height: 1.5;
      color: #1a1a2e;
    }

    .header { margin-bottom: 20mm; }
    .header h1 { font-size: 22pt; margin: 0; }
    .header .subtitle { color: #666; font-size: 9pt; }

    table.line-items {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10mm;
    }
    table.line-items th {
      background: #1a1a2e;
      color: white;
      padding: 6px 10px;
      text-align: left;
      font-size: 9pt;
    }
    table.line-items td {
      padding: 6px 10px;
      border-bottom: 0.5px solid #ddd;
      font-size: 9pt;
    }
    table.line-items tr:nth-child(even) td {
      background: #f8f8f8;
    }
    .text-right { text-align: right; }
    .total-row td {
      font-weight: bold;
      border-top: 2px solid #1a1a2e;
      border-bottom: none;
    }

    .terms {
      margin-top: 15mm;
      font-size: 9pt;
      color: #555;
      page-break-inside: avoid;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>ACME Corporation</h1>
    <p class="subtitle">123 Business Ave, Suite 100</p>
  </div>

  <p><strong>Invoice #{{ number }}</strong> &mdash; {{ date }}</p>
  <p>Bill to: {{ client_name }}<br>{{ client_address }}</p>

  <table class="line-items">
    <thead>
      <tr>
        <th>Description</th>
        <th class="text-right">Qty</th>
        <th class="text-right">Unit Price</th>
        <th class="text-right">Total</th>
      </tr>
    </thead>
    <tbody>
      {% for item in line_items %}
      <tr>
        <td>{{ item.description }}</td>
        <td class="text-right">{{ item.quantity }}</td>
        <td class="text-right">${{ "%.2f"|format(item.unit_price) }}</td>
        <td class="text-right">${{ "%.2f"|format(item.total) }}</td>
      </tr>
      {% endfor %}
      <tr class="total-row">
        <td colspan="3" class="text-right">Grand Total:</td>
        <td class="text-right">${{ "%.2f"|format(total) }}</td>
      </tr>
    </tbody>
  </table>

  <div class="terms">
    <p><strong>Payment Terms:</strong> Net 30 days. Please reference invoice number in payment.</p>
  </div>
</body>
</html>
```

**CSS Paged Media Features**:

```css
/* Force page breaks before specific elements */
h1.chapter-title {
  page-break-before: always;
}

/* Prevent orphaned content */
p {
  orphans: 3;
  widows: 3;
}

/* Avoid breaking inside a table row or figure */
tr, figure {
  page-break-inside: avoid;
}

/* Named pages for different sections */
@page cover {
  margin: 0;
  @top-right { content: none; }
  @bottom-center { content: none; }
}
.cover-page {
  page: cover;
}

/* Landscape pages for wide tables */
@page landscape {
  size: A4 landscape;
}
.wide-table-section {
  page: landscape;
}

/* Print-specific adjustments */
@media print {
  nav, .no-print { display: none; }
  a[href]::after { content: " (" attr(href) ")"; font-size: 8pt; color: #666; }
}
```

**Custom Stylesheets as Separate Files**:

```python
import weasyprint

def html_to_pdf_with_styles(
    html_content: str,
    css_paths: list[str],
    output_path: str,
) -> None:
    """Convert HTML to PDF with external stylesheets."""
    stylesheets = [weasyprint.CSS(filename=path) for path in css_paths]
    doc = weasyprint.HTML(string=html_content)
    doc.write_pdf(output_path, stylesheets=stylesheets)
```
