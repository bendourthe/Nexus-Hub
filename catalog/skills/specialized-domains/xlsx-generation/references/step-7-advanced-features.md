### Step 7: Advanced Features

Production Excel files often require features beyond basic data and formatting: autofilters for interactive exploration, freeze panes for navigation, print configuration for physical output, protection for controlled access, and VBA macro preservation for existing automation.

**Autofilters**:

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active

headers = ["Product", "Category", "Revenue", "Region", "Status"]
ws.append(headers)

data = [
    ["Widget A", "Electronics", 15000, "North", "Active"],
    ["Widget B", "Hardware", 22000, "South", "Active"],
    ["Widget C", "Software", 8500, "East", "Inactive"],
    ["Widget D", "Electronics", 31200, "West", "Active"],
    ["Widget E", "Hardware", 12000, "North", "Pending"],
]
for row in data:
    ws.append(row)

# Enable autofilter on the data range
ws.auto_filter.ref = f"A1:E{len(data) + 1}"

# Pre-apply a filter (visible when file is opened)
# Note: openpyxl sets the filter definition but Excel applies it on open
ws.auto_filter.add_filter_column(4, ["Active"])  # Column E (0-indexed: 4)
ws.auto_filter.add_sort_condition("C2:C6")       # Sort by Revenue

wb.save("autofilter.xlsx")
```

**Freeze Panes**:

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active

# Freeze the top row (header) and first column
ws.freeze_panes = "B2"
# "B2" means: freeze everything above row 2 and left of column B
# Result: row 1 and column A stay visible when scrolling

# Other common freeze configurations:
# ws.freeze_panes = "A2"   # Freeze top row only
# ws.freeze_panes = "B1"   # Freeze first column only
# ws.freeze_panes = "C3"   # Freeze rows 1-2 and columns A-B
# ws.freeze_panes = None    # Remove freeze panes

# Write headers and data
ws.append(["ID", "Name", "Revenue", "Cost", "Profit"])
for i in range(1, 101):
    ws.append([i, f"Product {i}", i * 100, i * 60, i * 40])

wb.save("freeze_panes.xlsx")
```

**Print Setup and Page Layout**:

```python
from openpyxl import Workbook
from openpyxl.worksheet.page import PageMargins

wb = Workbook()
ws = wb.active

# Page setup
ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
ws.page_setup.fitToWidth = 1   # Fit all columns on one page width
ws.page_setup.fitToHeight = 0  # Allow multiple pages vertically
ws.page_setup.scale = 85       # 85% scale (ignored if fitTo is set)

# Margins (in inches)
ws.page_margins = PageMargins(
    left=0.5, right=0.5,
    top=0.75, bottom=0.75,
    header=0.3, footer=0.3,
)

# Header and footer
ws.oddHeader.center.text = "Quarterly Sales Report"
ws.oddHeader.right.text = "&D"   # Current date
ws.oddFooter.center.text = "Page &P of &N"  # Page X of Y
ws.oddFooter.left.text = "Confidential"

# Print titles: repeat row 1 on every printed page
ws.print_title_rows = "1:1"
# Repeat columns A-B on every page
ws.print_title_cols = "A:B"

# Print area: only print a specific range
ws.print_area = "A1:F50"

# Page breaks
ws.page_breaks.append(openpyxl.worksheet.pagebreak.Break(id=25))  # After row 25

# Gridlines and headings
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_options.gridLines = True       # Print gridlines
ws.print_options.horizontalCentered = True  # Center on page

wb.save("print_setup.xlsx")
```

**Password Protection**:

```python
from openpyxl import Workbook
from openpyxl.worksheet.protection import SheetProtection

wb = Workbook()
ws = wb.active

# Write data
ws.append(["Product", "Price", "Discount", "Final Price"])
ws.append(["Widget A", 100, 0.1, "=B2*(1-C2)"])
ws.append(["Widget B", 200, 0.15, "=B3*(1-C3)"])

# Protect the sheet with a password
ws.protection = SheetProtection(
    sheet=True,
    password=os.getenv("SHEET_PASSWORD", "changeme"),
    formatCells=False,      # Allow formatting
    formatColumns=False,    # Allow column width changes
    formatRows=False,       # Allow row height changes
    insertColumns=False,
    insertRows=False,
    insertHyperlinks=False,
    deleteColumns=True,     # Prevent column deletion
    deleteRows=True,        # Prevent row deletion
    selectLockedCells=False,
    sort=False,             # Allow sorting
    autoFilter=False,       # Allow filtering
    pivotTables=True,       # Prevent pivot table changes
    selectUnlockedCells=False,
)

# Unlock specific cells that users can edit (discount column)
from openpyxl.styles import Protection

unlocked = Protection(locked=False)
for row in range(2, 4):
    ws.cell(row=row, column=3).protection = unlocked

# Protect the workbook structure (prevent adding/removing sheets)
wb.security.workbookPassword = os.getenv("WORKBOOK_PASSWORD", "changeme")
wb.security.lockStructure = True

wb.save("protected.xlsx")
```

**VBA Macro Preservation**:

```python
from openpyxl import load_workbook

# Load a macro-enabled workbook (.xlsm) while preserving VBA
wb = load_workbook("template_with_macros.xlsm", keep_vba=True)
ws = wb.active

# Modify data without affecting macros
ws["A1"] = "Updated by automation"
ws["B1"] = 42

# Save as .xlsm to preserve macros
# IMPORTANT: Saving as .xlsx will strip all VBA code
wb.save("updated_with_macros.xlsm")
```

```python
# xlsxwriter: create a new .xlsm file with VBA from a binary
import xlsxwriter

wb = xlsxwriter.Workbook("new_macros.xlsm")
ws = wb.add_worksheet()

ws.write("A1", "Click the button to run the macro")

# Add VBA project from a .bin file extracted from an existing .xlsm
# Extract with: python -c "import zipfile; z=zipfile.ZipFile('source.xlsm'); z.extract('xl/vbaProject.bin')"
wb.add_vba_project("xl/vbaProject.bin")

# Optionally add a button that triggers a macro
# ws.insert_button("B3", {"macro": "MyMacro", "caption": "Run Report", "width": 128, "height": 30})

wb.close()
```

**Images and Embedded Objects**:

```python
from openpyxl import Workbook
from openpyxl.drawing.image import Image

wb = Workbook()
ws = wb.active

# Add an image
img = Image("company_logo.png")
img.width = 200   # Pixels
img.height = 80
ws.add_image(img, "A1")

# Add a second image positioned elsewhere
chart_img = Image("exported_chart.png")
chart_img.width = 600
chart_img.height = 400
ws.add_image(chart_img, "D5")

# Write data below the logo
ws["A6"] = "Report starts here"

wb.save("with_images.xlsx")
```

**Hyperlinks**:

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active

# External URL
ws["A1"] = "Visit Website"
ws["A1"].hyperlink = "https://example.com"
ws["A1"].style = "Hyperlink"  # Built-in hyperlink style

# Link to another sheet in the same workbook
ws2 = wb.create_sheet("Details")
ws["A2"] = "Go to Details"
ws["A2"].hyperlink = "#Details!A1"
ws["A2"].style = "Hyperlink"

# Link to a file
ws["A3"] = "Open Document"
ws["A3"].hyperlink = "file:///C:/reports/summary.pdf"
ws["A3"].style = "Hyperlink"

# Email link
ws["A4"] = "Send Email"
ws["A4"].hyperlink = "mailto:reports@example.com?subject=Monthly%20Report"
ws["A4"].style = "Hyperlink"

wb.save("hyperlinks.xlsx")
```
