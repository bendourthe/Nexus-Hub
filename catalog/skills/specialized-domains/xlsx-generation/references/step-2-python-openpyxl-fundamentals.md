### Step 2: Python openpyxl Fundamentals

openpyxl is the most versatile Python library for Excel manipulation. It supports reading, writing, and modifying XLSX files with full formatting control.

**Workbook and Worksheet Basics**:

```python
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

# Create a new workbook
wb = Workbook()
ws = wb.active  # Get the default sheet
ws.title = "Sales Report"

# Add additional sheets
ws2 = wb.create_sheet("Summary")
ws3 = wb.create_sheet("Raw Data", 0)  # Insert at position 0

# Write data to cells
ws["A1"] = "Product"
ws["B1"] = "Revenue"
ws["C1"] = "Quarter"

# Write by row and column index (1-based)
ws.cell(row=2, column=1, value="Widget A")
ws.cell(row=2, column=2, value=15000.50)
ws.cell(row=2, column=3, value="Q1 2026")

# Write rows in bulk
data = [
    ["Widget B", 22000.75, "Q1 2026"],
    ["Widget C", 8500.00, "Q1 2026"],
    ["Widget D", 31200.25, "Q1 2026"],
]
for row in data:
    ws.append(row)

# Set column widths
ws.column_dimensions["A"].width = 20
ws.column_dimensions["B"].width = 15
ws.column_dimensions["C"].width = 12

# Set row height
ws.row_dimensions[1].height = 25

# Save the workbook
wb.save("sales_report.xlsx")
```

**Cell Data Types and Number Formats**:

```python
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from datetime import datetime, date
from decimal import Decimal

wb = Workbook()
ws = wb.active

# String values
ws["A1"] = "Revenue Report"

# Numeric values (integers and floats)
ws["A2"] = 42
ws["B2"] = 3.14159
ws["C2"] = Decimal("15000.50")  # Converted to float internally

# Date and datetime values
ws["A3"] = date(2026, 3, 15)
ws["A3"].number_format = "YYYY-MM-DD"

ws["B3"] = datetime(2026, 3, 15, 14, 30, 0)
ws["B3"].number_format = "YYYY-MM-DD HH:MM:SS"

# Currency formatting
ws["A4"] = 15000.50
ws["A4"].number_format = '"$"#,##0.00'

# Percentage formatting
ws["B4"] = 0.1575
ws["B4"].number_format = "0.00%"

# Accounting format (negative in parentheses)
ws["C4"] = -5000.00
ws["C4"].number_format = '_("$"* #,##0.00_);_("$"* (#,##0.00);_("$"* "-"??_);_(@_)'

# Custom number formats
ws["A5"] = 1234567
ws["A5"].number_format = "#,##0"  # Thousands separator

ws["B5"] = 0.5
ws["B5"].number_format = "0.0%"

# Boolean values
ws["A6"] = True  # Displays as TRUE in Excel

wb.save("data_types.xlsx")
```

**Cell Styling (Fonts, Fills, Borders, Alignment)**:

```python
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Border, Side, Alignment, NamedStyle
)

wb = Workbook()
ws = wb.active

# Font styling
header_font = Font(
    name="Calibri",
    size=14,
    bold=True,
    italic=False,
    color="FFFFFF",  # White text
)

body_font = Font(name="Calibri", size=11, color="333333")

# Fill (background color)
header_fill = PatternFill(
    start_color="2F5496",  # Dark blue
    end_color="2F5496",
    fill_type="solid",
)

alternating_fill = PatternFill(
    start_color="D6E4F0",  # Light blue
    end_color="D6E4F0",
    fill_type="solid",
)

# Borders
thin_border = Border(
    left=Side(style="thin", color="999999"),
    right=Side(style="thin", color="999999"),
    top=Side(style="thin", color="999999"),
    bottom=Side(style="thin", color="999999"),
)

header_border = Border(
    bottom=Side(style="medium", color="2F5496"),
)

# Alignment
center_align = Alignment(
    horizontal="center",
    vertical="center",
    wrap_text=True,
)

# Apply styles to header row
headers = ["Product", "Revenue", "Cost", "Profit", "Margin"]
for col_idx, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col_idx, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = center_align

# Apply alternating row colors
data_rows = [
    ["Widget A", 15000, 8000, 7000, 0.4667],
    ["Widget B", 22000, 12000, 10000, 0.4545],
    ["Widget C", 8500, 5000, 3500, 0.4118],
    ["Widget D", 31200, 18000, 13200, 0.4231],
]

for row_idx, row_data in enumerate(data_rows, 2):
    for col_idx, value in enumerate(row_data, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=value)
        cell.font = body_font
        cell.border = thin_border
        if row_idx % 2 == 0:
            cell.fill = alternating_fill
        # Format currency columns
        if col_idx in (2, 3, 4):
            cell.number_format = '"$"#,##0'
        # Format percentage column
        if col_idx == 5:
            cell.number_format = "0.0%"

wb.save("styled_report.xlsx")
```

**Named Styles for Reuse**:

```python
from openpyxl import Workbook
from openpyxl.styles import NamedStyle, Font, PatternFill, Border, Side, Alignment

wb = Workbook()

# Define reusable named styles
header_style = NamedStyle(name="header_style")
header_style.font = Font(bold=True, size=12, color="FFFFFF")
header_style.fill = PatternFill(start_color="2F5496", fill_type="solid")
header_style.alignment = Alignment(horizontal="center", vertical="center")
header_style.border = Border(
    bottom=Side(style="medium", color="1F3864")
)
wb.add_named_style(header_style)

currency_style = NamedStyle(name="currency_style")
currency_style.number_format = '"$"#,##0.00'
currency_style.font = Font(size=11)
currency_style.alignment = Alignment(horizontal="right")
wb.add_named_style(currency_style)

# Apply named styles by name
ws = wb.active
ws["A1"].style = "header_style"
ws["A1"].value = "Amount"
ws["A2"].style = "currency_style"
ws["A2"].value = 15000.50

wb.save("named_styles.xlsx")
```

**Merged Cells**:

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

wb = Workbook()
ws = wb.active

# Merge cells for a title row
ws.merge_cells("A1:E1")
ws["A1"] = "Quarterly Sales Report - Q1 2026"
ws["A1"].font = Font(size=16, bold=True)
ws["A1"].alignment = Alignment(horizontal="center")

# Merge cells for section headers
ws.merge_cells("A3:B3")
ws["A3"] = "Product Details"
ws["A3"].font = Font(bold=True)

ws.merge_cells("C3:E3")
ws["C3"] = "Financial Metrics"
ws["C3"].font = Font(bold=True)

# Unmerge if needed
# ws.unmerge_cells("A1:E1")

wb.save("merged_cells.xlsx")
```

**Loading and Modifying Existing Files**:

```python
from openpyxl import load_workbook

# Load an existing workbook
wb = load_workbook("template.xlsx")
ws = wb.active

# Read cell values
value = ws["A1"].value
print(f"Cell A1: {value}")

# Iterate over rows
for row in ws.iter_rows(min_row=2, max_col=5, values_only=True):
    product, revenue, cost, profit, margin = row
    print(f"{product}: ${revenue}")

# Modify cells
ws["F1"] = "Status"
for row_idx in range(2, ws.max_row + 1):
    profit = ws.cell(row=row_idx, column=4).value
    if profit and profit > 10000:
        ws.cell(row=row_idx, column=6, value="High")
    else:
        ws.cell(row=row_idx, column=6, value="Standard")

# Load with data_only to get calculated values instead of formulas
wb_values = load_workbook("report_with_formulas.xlsx", data_only=True)
# Note: data_only returns the cached value from the last Excel save,
# not a recalculated value. If the file was never opened in Excel,
# formula cells will return None.

wb.save("template_updated.xlsx")
```
