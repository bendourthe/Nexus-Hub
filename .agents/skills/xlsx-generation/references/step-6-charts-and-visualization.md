### Step 6: Charts and Visualization

Both openpyxl and xlsxwriter support creating Excel-native charts. Charts are embedded in the worksheet and update dynamically when the underlying data changes.

**openpyxl Charts**:

```python
from openpyxl import Workbook
from openpyxl.chart import (
    BarChart, LineChart, PieChart, ScatterChart, Reference
)
from openpyxl.chart.series import SeriesLabel
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Chart Data"

# Write data
headers = ["Month", "Revenue", "Cost", "Profit"]
data = [
    ["Jan", 15000, 8000, 7000],
    ["Feb", 18000, 9500, 8500],
    ["Mar", 22000, 11000, 11000],
    ["Apr", 19000, 10000, 9000],
    ["May", 25000, 12500, 12500],
    ["Jun", 28000, 14000, 14000],
]

ws.append(headers)
for row in data:
    ws.append(row)

# --- Bar Chart ---
bar_chart = BarChart()
bar_chart.type = "col"  # "col" for vertical, "bar" for horizontal
bar_chart.title = "Monthly Revenue and Cost"
bar_chart.x_axis.title = "Month"
bar_chart.y_axis.title = "Amount ($)"
bar_chart.style = 10
bar_chart.width = 20
bar_chart.height = 12

# Data references (min_col/max_col are 1-based)
categories = Reference(ws, min_col=1, min_row=2, max_row=7)  # Month labels
revenue_data = Reference(ws, min_col=2, min_row=1, max_row=7)  # Include header
cost_data = Reference(ws, min_col=3, min_row=1, max_row=7)

bar_chart.add_data(revenue_data, titles_from_data=True)
bar_chart.add_data(cost_data, titles_from_data=True)
bar_chart.set_categories(categories)

# Customize series colors
bar_chart.series[0].graphicalProperties.solidFill = "2F5496"  # Blue
bar_chart.series[1].graphicalProperties.solidFill = "C00000"  # Red

ws.add_chart(bar_chart, "F2")

# --- Line Chart ---
line_chart = LineChart()
line_chart.title = "Profit Trend"
line_chart.x_axis.title = "Month"
line_chart.y_axis.title = "Profit ($)"
line_chart.style = 10
line_chart.width = 20
line_chart.height = 12

profit_data = Reference(ws, min_col=4, min_row=1, max_row=7)
line_chart.add_data(profit_data, titles_from_data=True)
line_chart.set_categories(categories)

# Add data labels
line_chart.series[0].graphicalProperties.line.width = 25000  # EMUs
line_chart.series[0].dLbls = DataLabelList()
line_chart.series[0].dLbls.showVal = True

ws.add_chart(line_chart, "F18")

# --- Pie Chart ---
pie_ws = wb.create_sheet("Pie Chart")
pie_ws["A1"] = "Category"
pie_ws["B1"] = "Amount"
pie_data_rows = [
    ["Electronics", 45000],
    ["Hardware", 30000],
    ["Software", 25000],
    ["Services", 15000],
]
for row in pie_data_rows:
    pie_ws.append(row)

pie_chart = PieChart()
pie_chart.title = "Revenue by Category"
pie_chart.width = 18
pie_chart.height = 14

pie_labels = Reference(pie_ws, min_col=1, min_row=2, max_row=5)
pie_values = Reference(pie_ws, min_col=2, min_row=1, max_row=5)
pie_chart.add_data(pie_values, titles_from_data=True)
pie_chart.set_categories(pie_labels)

# Show percentage labels
pie_chart.series[0].dLbls = DataLabelList()
pie_chart.series[0].dLbls.showPercent = True
pie_chart.series[0].dLbls.showCatName = True
pie_chart.series[0].dLbls.showVal = False

pie_ws.add_chart(pie_chart, "D2")

# --- Scatter Chart ---
scatter_ws = wb.create_sheet("Scatter")
scatter_ws.append(["Ad Spend", "Revenue"])
scatter_data_rows = [
    [1000, 12000], [2000, 18000], [3000, 22000],
    [4000, 28000], [5000, 32000], [6000, 35000],
]
for row in scatter_data_rows:
    scatter_ws.append(row)

scatter_chart = ScatterChart()
scatter_chart.title = "Ad Spend vs Revenue"
scatter_chart.x_axis.title = "Ad Spend ($)"
scatter_chart.y_axis.title = "Revenue ($)"
scatter_chart.width = 18
scatter_chart.height = 14

x_values = Reference(scatter_ws, min_col=1, min_row=2, max_row=7)
y_values = Reference(scatter_ws, min_col=2, min_row=2, max_row=7)
series = scatter_chart.series
from openpyxl.chart import Series
s = Series(y_values, x_values, title="Revenue")
scatter_chart.series.append(s)

# Add trendline
from openpyxl.chart.trendline import Trendline
s.trendline = Trendline(trendlineType="linear", dispRSqr=True, dispEq=True)

scatter_ws.add_chart(scatter_chart, "D2")

wb.save("charts.xlsx")
```

**xlsxwriter Charts**:

```python
import xlsxwriter

wb = xlsxwriter.Workbook("xlsxwriter_charts.xlsx")
ws = wb.add_worksheet("Data")

# Write data
headers = ["Month", "Revenue", "Cost", "Profit"]
data = [
    ["Jan", 15000, 8000, 7000],
    ["Feb", 18000, 9500, 8500],
    ["Mar", 22000, 11000, 11000],
    ["Apr", 19000, 10000, 9000],
    ["May", 25000, 12500, 12500],
    ["Jun", 28000, 14000, 14000],
]

bold = wb.add_format({"bold": True})
for col, h in enumerate(headers):
    ws.write(0, col, h, bold)
for r, row in enumerate(data, 1):
    for c, val in enumerate(row):
        ws.write(r, c, val)

# --- Clustered Bar Chart ---
bar_chart = wb.add_chart({"type": "column"})

bar_chart.add_series({
    "name": "=Data!$B$1",
    "categories": "=Data!$A$2:$A$7",
    "values": "=Data!$B$2:$B$7",
    "fill": {"color": "#2F5496"},
    "gap": 150,
})
bar_chart.add_series({
    "name": "=Data!$C$1",
    "values": "=Data!$C$2:$C$7",
    "fill": {"color": "#C00000"},
})

bar_chart.set_title({"name": "Monthly Revenue and Cost"})
bar_chart.set_x_axis({"name": "Month"})
bar_chart.set_y_axis({"name": "Amount ($)", "num_format": "$#,##0"})
bar_chart.set_size({"width": 720, "height": 400})
bar_chart.set_legend({"position": "bottom"})

ws.insert_chart("F2", bar_chart)

# --- Combo Chart (Bar + Line) ---
combo_chart = wb.add_chart({"type": "column"})

combo_chart.add_series({
    "name": "Revenue",
    "categories": "=Data!$A$2:$A$7",
    "values": "=Data!$B$2:$B$7",
    "fill": {"color": "#2F5496"},
})

# Add a line series on a secondary axis
line_series = wb.add_chart({"type": "line"})
line_series.add_series({
    "name": "Profit",
    "categories": "=Data!$A$2:$A$7",
    "values": "=Data!$D$2:$D$7",
    "line": {"color": "#00B050", "width": 2.5},
    "marker": {"type": "circle", "size": 6},
    "y2_axis": True,
})

combo_chart.combine(line_series)
combo_chart.set_title({"name": "Revenue (Bars) vs Profit (Line)"})
combo_chart.set_y_axis({"name": "Revenue ($)"})
combo_chart.set_y2_axis({"name": "Profit ($)"})
combo_chart.set_size({"width": 720, "height": 400})

ws.insert_chart("F22", combo_chart)

# --- Stacked Area Chart ---
area_chart = wb.add_chart({"type": "area", "subtype": "stacked"})
area_chart.add_series({
    "name": "Cost",
    "categories": "=Data!$A$2:$A$7",
    "values": "=Data!$C$2:$C$7",
    "fill": {"color": "#FFC000"},
})
area_chart.add_series({
    "name": "Profit",
    "values": "=Data!$D$2:$D$7",
    "fill": {"color": "#00B050"},
})
area_chart.set_title({"name": "Revenue Composition"})
area_chart.set_size({"width": 720, "height": 400})

ws.insert_chart("F42", area_chart)

wb.close()
```

**Data-Driven Chart Generation Helper**:

```python
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference


def add_chart_from_data(
    wb: Workbook,
    sheet_name: str,
    chart_type: str,
    title: str,
    data_range: tuple[int, int, int, int],
    category_col: int,
    anchor_cell: str = "A1",
    width: int = 18,
    height: int = 12,
) -> None:
    """Add a chart to a worksheet from a data range.

    Args:
        wb: The workbook containing the data.
        sheet_name: Name of the sheet with data.
        chart_type: One of "bar", "line", "pie".
        title: Chart title.
        data_range: Tuple of (min_col, min_row, max_col, max_row) for data series.
        category_col: Column number for category labels.
        anchor_cell: Cell where the chart top-left corner is placed.
        width: Chart width in cm.
        height: Chart height in cm.
    """
    ws = wb[sheet_name]
    min_col, min_row, max_col, max_row = data_range

    chart_classes = {
        "bar": BarChart,
        "line": LineChart,
        "pie": PieChart,
    }

    chart_cls = chart_classes.get(chart_type)
    if chart_cls is None:
        raise ValueError(f"Unsupported chart type: {chart_type}. Use: {list(chart_classes.keys())}")

    chart = chart_cls()
    chart.title = title
    chart.width = width
    chart.height = height

    data_ref = Reference(ws, min_col=min_col, min_row=min_row, max_col=max_col, max_row=max_row)
    categories = Reference(ws, min_col=category_col, min_row=min_row + 1, max_row=max_row)

    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(categories)

    target_ws = ws
    target_ws.add_chart(chart, anchor_cell)


# Usage:
# wb = Workbook()
# ws = wb.active
# ws.append(["Month", "Revenue", "Cost"])
# for row in [["Jan", 15000, 8000], ["Feb", 18000, 9500]]:
#     ws.append(row)
# add_chart_from_data(wb, ws.title, "bar", "Revenue vs Cost", (2, 1, 3, 3), 1, "E2")
# wb.save("dynamic_chart.xlsx")
```
