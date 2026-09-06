### Step 8: Pandas Integration and Data Pipelines

Pandas provides the fastest path from data analysis to Excel output. The `DataFrame.to_excel()` method delegates to openpyxl or xlsxwriter under the hood, while `pd.read_excel()` handles ingestion.

**Basic DataFrame to Excel**:

```python
import pandas as pd

# Create sample data
df = pd.DataFrame({
    "Product": ["Widget A", "Widget B", "Widget C", "Widget D"],
    "Revenue": [15000.50, 22000.75, 8500.00, 31200.25],
    "Cost": [8000, 12000, 5000, 18000],
    "Units Sold": [150, 220, 85, 312],
    "Date": pd.to_datetime(["2026-01-15", "2026-02-01", "2026-02-15", "2026-03-01"]),
})
df["Profit"] = df["Revenue"] - df["Cost"]
df["Margin"] = df["Profit"] / df["Revenue"]

# Simple export
df.to_excel("basic_export.xlsx", index=False, sheet_name="Sales")

# Export with xlsxwriter engine for better formatting control
df.to_excel(
    "formatted_export.xlsx",
    index=False,
    sheet_name="Sales",
    engine="xlsxwriter",
    float_format="%.2f",
)
```

**Multi-Sheet Export**:

```python
import pandas as pd

# Multiple DataFrames to separate sheets
sales_df = pd.DataFrame({
    "Product": ["Widget A", "Widget B"],
    "Revenue": [15000, 22000],
})

inventory_df = pd.DataFrame({
    "Product": ["Widget A", "Widget B"],
    "Stock": [500, 300],
    "Reorder Point": [100, 50],
})

summary_df = pd.DataFrame({
    "Metric": ["Total Revenue", "Total Stock", "Products"],
    "Value": [37000, 800, 2],
})

# Use ExcelWriter for multi-sheet output
with pd.ExcelWriter("multi_sheet.xlsx", engine="openpyxl") as writer:
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
    sales_df.to_excel(writer, sheet_name="Sales", index=False)
    inventory_df.to_excel(writer, sheet_name="Inventory", index=False)
```

**Styled Export with xlsxwriter Engine**:

```python
import pandas as pd

df = pd.DataFrame({
    "Product": ["Widget A", "Widget B", "Widget C", "Widget D"],
    "Revenue": [15000, 22000, 8500, 31200],
    "Cost": [8000, 12000, 5000, 18000],
    "Margin": [0.4667, 0.4545, 0.4118, 0.4231],
})

with pd.ExcelWriter("styled_pandas.xlsx", engine="xlsxwriter") as writer:
    df.to_excel(writer, sheet_name="Report", index=False, startrow=1)

    wb = writer.book
    ws = writer.sheets["Report"]

    # Title row
    title_fmt = wb.add_format({
        "bold": True, "font_size": 16, "font_color": "#2F5496",
    })
    ws.write("A1", "Sales Performance Report", title_fmt)

    # Header formatting
    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#2F5496", "font_color": "#FFFFFF",
        "border": 1, "align": "center",
    })
    for col_num, header in enumerate(df.columns):
        ws.write(1, col_num, header, header_fmt)

    # Column formats
    currency_fmt = wb.add_format({"num_format": "$#,##0", "border": 1})
    percent_fmt = wb.add_format({"num_format": "0.0%", "border": 1})

    ws.set_column("A:A", 20)
    ws.set_column("B:C", 15, currency_fmt)
    ws.set_column("D:D", 12, percent_fmt)

    # Conditional formatting on margin column
    red_fmt = wb.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
    green_fmt = wb.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})

    ws.conditional_format("D3:D6", {
        "type": "cell", "criteria": "<", "value": 0.45, "format": red_fmt,
    })
    ws.conditional_format("D3:D6", {
        "type": "cell", "criteria": ">=", "value": 0.45, "format": green_fmt,
    })

    # Add a chart
    chart = wb.add_chart({"type": "column"})
    chart.add_series({
        "name": "Revenue",
        "categories": "=Report!$A$3:$A$6",
        "values": "=Report!$B$3:$B$6",
        "fill": {"color": "#2F5496"},
    })
    chart.set_title({"name": "Revenue by Product"})
    chart.set_size({"width": 500, "height": 300})
    ws.insert_chart("F3", chart)
```

**Pandas Styler for Conditional Formatting**:

```python
import pandas as pd

df = pd.DataFrame({
    "Product": ["Widget A", "Widget B", "Widget C", "Widget D"],
    "Revenue": [15000, 22000, 8500, 31200],
    "Cost": [8000, 12000, 5000, 18000],
    "Profit": [7000, 10000, 3500, 13200],
    "Margin": [0.4667, 0.4545, 0.4118, 0.4231],
})

def highlight_negative(val):
    """Highlight negative values in red."""
    color = "color: #9C0006; background-color: #FFC7CE" if val < 0 else ""
    return color

def highlight_high_margin(val):
    """Highlight margins above 45% in green."""
    if val > 0.45:
        return "color: #006100; background-color: #C6EFCE"
    return ""

# Apply styles
styled = (
    df.style
    .format({
        "Revenue": "${:,.0f}",
        "Cost": "${:,.0f}",
        "Profit": "${:,.0f}",
        "Margin": "{:.1%}",
    })
    .map(highlight_negative, subset=["Profit"])
    .map(highlight_high_margin, subset=["Margin"])
    .bar(subset=["Revenue"], color="#D6E4F0", vmin=0)
    .set_caption("Sales Performance Report")
    .set_table_styles([
        {"selector": "th", "props": [
            ("background-color", "#2F5496"),
            ("color", "white"),
            ("font-weight", "bold"),
        ]},
    ])
)

# Export to Excel (uses openpyxl engine)
styled.to_excel("styler_export.xlsx", engine="openpyxl", index=False)
```

**Read, Transform, Write Pipeline**:

```python
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill


def excel_etl_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    transformations: dict | None = None,
) -> dict:
    """Read an Excel file, apply transformations, and write a formatted output.

    Args:
        input_path: Path to the source Excel file.
        output_path: Path for the output Excel file.
        transformations: Optional dict of column_name -> callable transforms.

    Returns:
        Dict with row counts and sheet names processed.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Read all sheets
    all_sheets = pd.read_excel(input_path, sheet_name=None, engine="openpyxl")
    stats = {"sheets_processed": [], "total_rows": 0}

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in all_sheets.items():
            # Apply transformations
            if transformations:
                for col, transform_fn in transformations.items():
                    if col in df.columns:
                        df[col] = df[col].apply(transform_fn)

            # Remove fully empty rows
            df = df.dropna(how="all")

            # Write to output
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            stats["sheets_processed"].append(sheet_name)
            stats["total_rows"] += len(df)

    # Post-process: apply formatting with openpyxl
    wb = load_workbook(output_path)
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5496", fill_type="solid")

    for ws in wb.worksheets:
        # Style headers
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill

        # Auto-adjust column widths
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_length + 4, 50)

        # Freeze header row
        ws.freeze_panes = "A2"

        # Enable autofilter
        if ws.max_row > 1:
            ws.auto_filter.ref = ws.dimensions

    wb.save(output_path)
    return stats


# Usage:
# stats = excel_etl_pipeline(
#     "raw_data.xlsx",
#     "processed_report.xlsx",
#     transformations={
#         "revenue": lambda x: round(x, 2) if pd.notna(x) else 0,
#         "name": lambda x: str(x).strip().title() if pd.notna(x) else "",
#     },
# )
# print(f"Processed {stats['total_rows']} rows across {len(stats['sheets_processed'])} sheets")
```

**Batch Report Generation**:

```python
import pandas as pd
from pathlib import Path


def generate_regional_reports(
    data: pd.DataFrame,
    output_dir: str | Path,
    group_column: str = "Region",
) -> list[Path]:
    """Generate one Excel report per group (e.g., per region).

    Args:
        data: Source DataFrame with all regions.
        output_dir: Directory to write individual report files.
        group_column: Column name to group/split by.

    Returns:
        List of generated file paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    for group_name, group_df in data.groupby(group_column):
        safe_name = str(group_name).replace(" ", "_").lower()
        filepath = output_dir / f"report_{safe_name}.xlsx"

        with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
            # Summary sheet
            summary = group_df.describe()
            summary.to_excel(writer, sheet_name="Summary")

            # Detail sheet
            group_df.to_excel(writer, sheet_name="Detail", index=False)

            # Format the detail sheet
            wb = writer.book
            ws = writer.sheets["Detail"]

            header_fmt = wb.add_format({
                "bold": True, "bg_color": "#2F5496",
                "font_color": "#FFFFFF", "border": 1,
            })

            for col_num, col_name in enumerate(group_df.columns):
                ws.write(0, col_num, col_name, header_fmt)
                # Auto-fit column width
                max_len = max(
                    group_df[col_name].astype(str).map(len).max(),
                    len(col_name),
                )
                ws.set_column(col_num, col_num, min(max_len + 2, 40))

        generated_files.append(filepath)

    return generated_files


# Usage:
# df = pd.DataFrame({
#     "Region": ["North", "North", "South", "South", "East", "East"],
#     "Product": ["A", "B", "A", "B", "A", "B"],
#     "Revenue": [15000, 22000, 18000, 12000, 25000, 19000],
# })
# files = generate_regional_reports(df, "output/regional_reports")
# for f in files:
#     print(f"Generated: {f}")
```

**Common Pitfalls and Best Practices**:

- **Floating-point precision**: Use `Decimal` for financial data in Python. openpyxl converts to float internally, so round before writing: `float(Decimal("15000.50").quantize(Decimal("0.01")))`
- **Date handling**: Always pass `datetime` or `date` objects, not strings. Set `number_format` explicitly to control display
- **Memory with large files**: Use xlsxwriter's `constant_memory` mode or ExcelJS streaming API for datasets over 100,000 rows
- **Formula evaluation**: XLSX libraries write formula text, not computed values. The formulas are evaluated only when the file is opened in Excel. If you need pre-computed values, calculate them in Python and write the results
- **data_only mode in openpyxl**: Returns the last cached value from when the file was saved by Excel. If the file was never opened in Excel, formula cells return `None`
- **String length limit**: Excel cells support a maximum of 32,767 characters. Truncate long strings before writing
- **Sheet name limits**: Sheet names cannot exceed 31 characters and cannot contain `\ / * ? : [ ]`
- **Column limit**: XLSX supports up to 16,384 columns (XFD). Validate wide DataFrames before export
- **File locking**: On Windows, Excel locks open files. Catch `PermissionError` and prompt users to close the file
- **Encoding**: XLSX is UTF-8 internally. Special characters, CJK text, and emoji work without extra configuration
