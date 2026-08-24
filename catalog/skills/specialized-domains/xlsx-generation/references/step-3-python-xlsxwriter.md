### Step 3: Python xlsxwriter

xlsxwriter is a write-only library optimized for performance and feature richness. It produces XLSX files without needing to read existing ones, making it ideal for report generation pipelines.

**Basic Setup and Formatting**:

```python
import xlsxwriter

wb = xlsxwriter.Workbook("report.xlsx")
ws = wb.add_worksheet("Sales")

# Define reusable formats
header_fmt = wb.add_format({
    "bold": True,
    "font_size": 12,
    "font_color": "#FFFFFF",
    "bg_color": "#2F5496",
    "border": 1,
    "align": "center",
    "valign": "vcenter",
    "text_wrap": True,
})

currency_fmt = wb.add_format({
    "num_format": "$#,##0.00",
    "font_size": 11,
    "border": 1,
})

percent_fmt = wb.add_format({
    "num_format": "0.0%",
    "font_size": 11,
    "border": 1,
})

date_fmt = wb.add_format({
    "num_format": "yyyy-mm-dd",
    "border": 1,
})

# Write header row
headers = ["Product", "Revenue", "Cost", "Profit", "Margin", "Date"]
for col, header in enumerate(headers):
    ws.write(0, col, header, header_fmt)

# Write data rows
data = [
    ["Widget A", 15000.50, 8000, 7000.50, 0.4667, "2026-03-15"],
    ["Widget B", 22000.75, 12000, 10000.75, 0.4545, "2026-03-16"],
    ["Widget C", 8500.00, 5000, 3500.00, 0.4118, "2026-03-17"],
]

for row_idx, row_data in enumerate(data, 1):
    ws.write(row_idx, 0, row_data[0])             # String
    ws.write(row_idx, 1, row_data[1], currency_fmt) # Currency
    ws.write(row_idx, 2, row_data[2], currency_fmt) # Currency
    ws.write(row_idx, 3, row_data[3], currency_fmt) # Currency
    ws.write(row_idx, 4, row_data[4], percent_fmt)  # Percentage
    ws.write(row_idx, 5, row_data[5], date_fmt)     # Date

# Set column widths
ws.set_column("A:A", 20)
ws.set_column("B:D", 15)
ws.set_column("E:E", 10)
ws.set_column("F:F", 14)

# Set row heights
ws.set_row(0, 25)

wb.close()  # xlsxwriter uses close(), not save()
```

**Conditional Formatting**:

```python
import xlsxwriter

wb = xlsxwriter.Workbook("conditional.xlsx")
ws = wb.add_worksheet()

# Write sample data
headers = ["Product", "Revenue", "Target", "Variance"]
for col, h in enumerate(headers):
    ws.write(0, col, h)

data = [
    ["Widget A", 15000, 12000, 3000],
    ["Widget B", 8000, 12000, -4000],
    ["Widget C", 22000, 12000, 10000],
    ["Widget D", 11000, 12000, -1000],
]
for r, row in enumerate(data, 1):
    for c, val in enumerate(row):
        ws.write(r, c, val)

# Color scale: green (high) to red (low) on revenue column
ws.conditional_format("B2:B5", {
    "type": "3_color_scale",
    "min_color": "#F8696B",   # Red
    "mid_color": "#FFEB84",   # Yellow
    "max_color": "#63BE7B",   # Green
})

# Data bar on revenue column
ws.conditional_format("B2:B5", {
    "type": "data_bar",
    "bar_color": "#2F5496",
})

# Icon set on variance column
ws.conditional_format("D2:D5", {
    "type": "icon_set",
    "icon_style": "3_traffic_lights",
    "icons": [
        {"criteria": ">=", "type": "number", "value": 5000},
        {"criteria": ">=", "type": "number", "value": 0},
        {"criteria": "<",  "type": "number", "value": 0},
    ],
})

# Cell-based conditional format: highlight negative variance in red
red_fmt = wb.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
ws.conditional_format("D2:D5", {
    "type": "cell",
    "criteria": "<",
    "value": 0,
    "format": red_fmt,
})

# Highlight cells above average
green_fmt = wb.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
ws.conditional_format("B2:B5", {
    "type": "average",
    "criteria": "above",
    "format": green_fmt,
})

# Formula-based: highlight entire row where variance is negative
row_red_fmt = wb.add_format({"bg_color": "#FFC7CE"})
ws.conditional_format("A2:D5", {
    "type": "formula",
    "criteria": "=$D2<0",
    "format": row_red_fmt,
})

wb.close()
```

**Data Validation**:

```python
import xlsxwriter

wb = xlsxwriter.Workbook("validation.xlsx")
ws = wb.add_worksheet()

# Dropdown list validation
ws.write("A1", "Status")
ws.data_validation("A2:A100", {
    "validate": "list",
    "source": ["Active", "Inactive", "Pending", "Archived"],
    "input_title": "Select Status",
    "input_message": "Choose a status from the dropdown.",
    "error_title": "Invalid Status",
    "error_message": "Please select a valid status from the list.",
})

# Numeric range validation
ws.write("B1", "Quantity")
ws.data_validation("B2:B100", {
    "validate": "integer",
    "criteria": "between",
    "minimum": 1,
    "maximum": 10000,
    "input_title": "Enter Quantity",
    "input_message": "Quantity must be between 1 and 10,000.",
    "error_type": "stop",
})

# Date range validation
ws.write("C1", "Due Date")
ws.data_validation("C2:C100", {
    "validate": "date",
    "criteria": ">=",
    "value": "2026-01-01",
    "input_title": "Enter Date",
    "input_message": "Date must be on or after 2026-01-01.",
})

# Custom formula validation (value must be unique in column)
ws.write("D1", "Code")
ws.data_validation("D2:D100", {
    "validate": "custom",
    "value": "=COUNTIF($D:$D,D2)<=1",
    "input_title": "Unique Code",
    "input_message": "Enter a unique product code.",
    "error_title": "Duplicate",
    "error_message": "This code already exists in the column.",
})

wb.close()
```

**Sparklines**:

```python
import xlsxwriter

wb = xlsxwriter.Workbook("sparklines.xlsx")
ws = wb.add_worksheet()

# Monthly revenue data
ws.write_row("A1", ["Product", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Trend"])
ws.write_row("A2", ["Widget A", 100, 120, 115, 140, 155, 170])
ws.write_row("A3", ["Widget B", 200, 190, 210, 195, 220, 240])
ws.write_row("A4", ["Widget C", 50, 60, 55, 70, 65, 80])

# Add sparklines in the Trend column
ws.add_sparkline("H2", {
    "range": "B2:G2",
    "type": "line",
    "markers": True,
    "high_point": True,
    "low_point": True,
})

ws.add_sparkline("H3", {
    "range": "B3:G3",
    "type": "column",
    "high_point": True,
})

ws.add_sparkline("H4", {
    "range": "B4:G4",
    "type": "win_loss",
})

ws.set_column("H:H", 20)
wb.close()
```

**Memory-Optimized Writing for Large Datasets**:

```python
import xlsxwriter

# Enable constant_memory mode for large datasets
# Rows are flushed to disk and cannot be revisited
wb = xlsxwriter.Workbook("large_dataset.xlsx", {"constant_memory": True})
ws = wb.add_worksheet()

header_fmt = wb.add_format({"bold": True, "bg_color": "#2F5496", "font_color": "#FFFFFF"})

headers = ["ID", "Name", "Value", "Category", "Timestamp"]
for col, h in enumerate(headers):
    ws.write(0, col, h, header_fmt)

# Write 1 million rows efficiently
for row in range(1, 1_000_001):
    ws.write_number(row, 0, row)
    ws.write_string(row, 1, f"Item {row}")
    ws.write_number(row, 2, row * 1.5)
    ws.write_string(row, 3, f"Cat-{row % 10}")
    ws.write_string(row, 4, "2026-03-15T10:30:00")

wb.close()
```
