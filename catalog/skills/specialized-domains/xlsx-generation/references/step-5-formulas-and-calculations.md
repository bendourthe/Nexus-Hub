### Step 5: Formulas and Calculations

All major XLSX libraries support embedding Excel formulas in cells. Formulas are stored as text and evaluated by Excel when the file is opened.

**Cell Formulas in openpyxl**:

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active

# Simple formulas
ws["A1"] = "Revenue"
ws["A2"] = 15000
ws["A3"] = 22000
ws["A4"] = 8500
ws["A5"] = "=SUM(A2:A4)"            # Sum
ws["A6"] = "=AVERAGE(A2:A4)"        # Average
ws["A7"] = "=MAX(A2:A4)"            # Maximum
ws["A8"] = '=IF(A5>40000,"High","Low")'  # Conditional

# Cross-cell references
ws["B2"] = 8000   # Cost for row 2
ws["C2"] = "=A2-B2"  # Profit = Revenue - Cost
ws["D2"] = "=C2/A2"  # Margin = Profit / Revenue

# Fill formulas down a range
for row in range(2, 5):
    ws.cell(row=row, column=3).value = f"=A{row}-B{row}"
    ws.cell(row=row, column=4).value = f"=C{row}/A{row}"

# VLOOKUP and INDEX/MATCH
ws2 = wb.create_sheet("Lookup")
ws2["A1"] = "Product"
ws2["B1"] = "Category"
ws2["A2"] = "Widget A"
ws2["B2"] = "Electronics"
ws2["A3"] = "Widget B"
ws2["B3"] = "Hardware"

# Reference lookup from main sheet
ws["E2"] = "=VLOOKUP(A2,Lookup!A:B,2,FALSE)"
# Modern alternative: XLOOKUP (Excel 365+)
ws["F2"] = "=XLOOKUP(A2,Lookup!A:A,Lookup!B:B)"

wb.save("formulas.xlsx")
```

**Named Ranges**:

```python
from openpyxl import Workbook
from openpyxl.workbook.defined_name import DefinedName

wb = Workbook()
ws = wb.active
ws.title = "Data"

# Write data
ws["A1"] = "Revenue"
for row, val in enumerate([15000, 22000, 8500, 31200], 2):
    ws.cell(row=row, column=1, value=val)

# Create a named range
revenue_range = DefinedName("RevenueData", attr_text="Data!$A$2:$A$5")
wb.defined_names.add(revenue_range)

# Use the named range in formulas
ws["C1"] = "Total Revenue"
ws["C2"] = "=SUM(RevenueData)"
ws["C3"] = "Average Revenue"
ws["C4"] = "=AVERAGE(RevenueData)"

# Named range scoped to a specific sheet
local_range = DefinedName(
    "LocalTotal",
    attr_text="Data!$C$2",
    localSheetId=0,  # Sheet index
)
wb.defined_names.add(local_range)

# Print area as a named range
ws.print_area = "A1:C10"

# Print titles (repeat rows at top of each printed page)
ws.print_title_rows = "1:1"

wb.save("named_ranges.xlsx")
```

**Array Formulas and Dynamic Arrays**:

```python
from openpyxl import Workbook
from openpyxl.worksheet.formula import ArrayFormula

wb = Workbook()
ws = wb.active

# Data
ws["A1"] = "Price"
ws["B1"] = "Quantity"
ws["C1"] = "Total"
for row, (price, qty) in enumerate([(10, 5), (20, 3), (15, 8)], 2):
    ws.cell(row=row, column=1, value=price)
    ws.cell(row=row, column=2, value=qty)

# Legacy CSE array formula (Ctrl+Shift+Enter)
# Computes sum of element-wise multiplication
ws["D1"] = "Sum of Products"
ws["D2"] = ArrayFormula("D2", "=SUM(A2:A4*B2:B4)")

# Individual cell formulas (non-array, but referencing ranges)
ws["C2"] = "=A2*B2"
ws["C3"] = "=A3*B3"
ws["C4"] = "=A4*B4"

# Dynamic array formulas (Excel 365+, spill into adjacent cells)
# These work when opened in Excel; the library writes the formula to the anchor cell
ws2 = wb.create_sheet("Dynamic")
ws2["A1"] = "=SORT(Data!A2:A4)"            # Spills sorted values
ws2["C1"] = "=UNIQUE(Data!A2:A10)"          # Spills unique values
ws2["E1"] = "=FILTER(Data!A2:C4,Data!C2:C4>50)"  # Filtered results

wb.save("array_formulas.xlsx")
```

**Cross-Sheet References**:

```python
from openpyxl import Workbook

wb = Workbook()

# Create multiple sheets with data
regions = {
    "North": [10000, 12000, 15000],
    "South": [8000, 9000, 11000],
    "East": [14000, 13000, 16000],
    "West": [7000, 8500, 9500],
}

for region, values in regions.items():
    ws = wb.create_sheet(region)
    ws["A1"] = "Q1"
    ws["B1"] = "Q2"
    ws["C1"] = "Q3"
    for col, val in enumerate(values, 1):
        ws.cell(row=2, column=col, value=val)
    ws["D1"] = "Total"
    ws["D2"] = "=SUM(A2:C2)"

# Summary sheet with cross-sheet references
summary = wb.create_sheet("Summary", 0)
summary["A1"] = "Region"
summary["B1"] = "Q1"
summary["C1"] = "Q2"
summary["D1"] = "Q3"
summary["E1"] = "Total"

for row, region in enumerate(regions.keys(), 2):
    summary.cell(row=row, column=1, value=region)
    summary.cell(row=row, column=2).value = f"='{region}'!A2"
    summary.cell(row=row, column=3).value = f"='{region}'!B2"
    summary.cell(row=row, column=4).value = f"='{region}'!C2"
    summary.cell(row=row, column=5).value = f"='{region}'!D2"

# Grand total row
total_row = len(regions) + 2
summary.cell(row=total_row, column=1, value="Grand Total")
for col in range(2, 6):
    col_letter = chr(64 + col)  # B, C, D, E
    summary.cell(row=total_row, column=col).value = (
        f"=SUM({col_letter}2:{col_letter}{total_row - 1})"
    )

# Remove the default sheet
del wb["Sheet"]

wb.save("cross_sheet.xlsx")
```

**Formula Auditing and Validation**:

```python
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import re

def audit_formulas(filepath: str) -> list[dict]:
    """Scan a workbook and report all formula cells with their references."""
    wb = load_workbook(filepath)
    findings = []

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    formula = cell.value
                    # Extract cell references from the formula
                    refs = re.findall(
                        r"(?:'[^']+'\!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?",
                        formula,
                    )
                    findings.append({
                        "sheet": ws.title,
                        "cell": cell.coordinate,
                        "formula": formula,
                        "references": refs,
                    })

    return findings

# Usage
# results = audit_formulas("complex_report.xlsx")
# for f in results:
#     print(f"{f['sheet']}!{f['cell']}: {f['formula']} -> refs: {f['references']}")
```
