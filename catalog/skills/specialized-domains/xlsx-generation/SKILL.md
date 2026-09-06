---
name: xlsx-generation
description: Excel spreadsheet generation and manipulation expertise for creating, reading, and automating XLSX files programmatically. Use when building report generators, automating financial models, creating data export pipelines, or manipulating spreadsheets.
summary_l0: "Generate and manipulate Excel spreadsheets with formulas, charts, and multi-library support"
overview_l1: "This skill provides comprehensive expertise in generating, reading, and manipulating Excel XLSX files programmatically across Python, JavaScript, and Java ecosystems. Use it when building report generators, data export pipelines, financial models, business dashboards as spreadsheets, converting query results into styled workbooks, or integrating spreadsheet output into ETL workflows. Key capabilities include library selection across openpyxl, xlsxwriter, ExcelJS, and Apache POI; workbook and worksheet creation with typed cell data; rich cell styling; conditional formatting and data validation; formula injection with named ranges and cross-sheet references; chart generation (bar, line, pie, scatter, combo); features such as autofilters, freeze panes, and password protection; and Pandas DataFrame-to-Excel pipelines. The expected output is production-ready XLSX files with correct formatting, formulas, charts, and data integrity suitable for business stakeholders. Trigger phrases: xlsx, Excel generation, spreadsheet, openpyxl, xlsxwriter, ExcelJS, Apache POI, Excel report, data export, Excel automation, cell formatting, Excel chart, DataFrame to Excel, spreadsheet pipeline."
---

# XLSX Generation

Structured guidance for generating, reading, and manipulating Excel XLSX files programmatically. Covers library selection, cell formatting, formulas, charts, advanced workbook features, and data pipeline integration across Python, JavaScript, and Java ecosystems.

## When to Use This Skill

Use this skill for:

- Building automated report generators that output styled Excel workbooks
- Creating data export pipelines that produce XLSX files from databases or APIs
- Generating financial models, budgets, or forecasts as spreadsheets
- Formatting business dashboards with conditional formatting, charts, and pivot-ready data
- Converting DataFrame analysis results into multi-sheet Excel deliverables
- Integrating spreadsheet output into ETL or CI/CD workflows
- Reading and transforming existing Excel files (extract data, update cells, merge workbooks)
- Producing Excel templates with data validation, dropdowns, and protected ranges

**Trigger phrases**: "xlsx", "Excel generation", "spreadsheet", "openpyxl", "xlsxwriter", "ExcelJS", "Apache POI", "Excel report", "data export", "Excel automation", "workbook", "worksheet", "cell formatting", "Excel chart", "pivot table", "Excel formula", "DataFrame to Excel", "spreadsheet pipeline"

## What This Skill Does

Provides Excel generation patterns including:

- **Library Selection**: Decision matrix for openpyxl, xlsxwriter, ExcelJS, Apache POI, and Pandas wrappers
- **Cell Formatting**: Fonts, fills, borders, alignment, number formats, merged cells, rich text
- **Formulas**: Cell references, named ranges, array formulas, cross-sheet formulas, formula auditing
- **Charts**: Bar, line, pie, scatter, combo charts with programmatic configuration and positioning
- **Data Validation**: Dropdown lists, numeric ranges, date constraints, custom formula validators
- **Advanced Features**: Autofilters, freeze panes, print setup, protection, VBA preservation, images
- **Pandas Integration**: DataFrame export, multi-sheet workbooks, Styler formatting, read/transform/write
- **Performance**: Streaming writes for large datasets, memory optimization, batch operations

## Instructions

### Step 1: Library Selection

Full walkthrough: [step-1-library-selection.md](references/step-1-library-selection.md) (load this step when you reach it).

### Step 2: Python openpyxl Fundamentals

Full walkthrough: [step-2-python-openpyxl-fundamentals.md](references/step-2-python-openpyxl-fundamentals.md) (load this step when you reach it).

### Step 3: Python xlsxwriter

Full walkthrough: [step-3-python-xlsxwriter.md](references/step-3-python-xlsxwriter.md) (load this step when you reach it).

### Step 4: JavaScript ExcelJS

Full walkthrough: [step-4-javascript-exceljs.md](references/step-4-javascript-exceljs.md) (load this step when you reach it).

### Step 5: Formulas and Calculations

Full walkthrough: [step-5-formulas-and-calculations.md](references/step-5-formulas-and-calculations.md) (load this step when you reach it).

### Step 6: Charts and Visualization

Full walkthrough: [step-6-charts-and-visualization.md](references/step-6-charts-and-visualization.md) (load this step when you reach it).

### Step 7: Advanced Features

Full walkthrough: [step-7-advanced-features.md](references/step-7-advanced-features.md) (load this step when you reach it).

### Step 8: Pandas Integration and Data Pipelines

Full walkthrough: [step-8-pandas-integration-and-data-pipelines.md](references/step-8-pandas-integration-and-data-pipelines.md) (load this step when you reach it).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll write the formula and read the result back, it's the same cell" | XLSX libraries write formula text, not computed values; the cell returns the formula or a stale cached value, not the sum you expect, until Excel opens it. Compute the value in Python if downstream code needs the number. |
| "Floats are fine for currency, the rounding is tiny" | openpyxl stores floats, so 0.1 + 0.2 lands as 0.30000000000000004 in a financial report a stakeholder audits. Use Decimal and round before writing the cell. |
| "Strings just write, no need to check length" | A field over 32,767 characters or a sheet name with a `/` raises mid-batch and aborts the export. Validating string and sheet-name limits up front keeps the batch running. |
| "The file looks right in Excel, no automated check needed" | Opening one file by hand does not scale and misses the row whose number_format silently displayed a date as a serial integer. Asserting cell values and formats programmatically is what catches it. |

## Verification

- [ ] The generated file opens as a valid XLSX (a ZIP archive with the required OOXML parts)
- [ ] A read-back test asserts expected cell values and number formats per sheet
- [ ] Financial values were rounded with Decimal before writing (no float artifacts)
- [ ] All sheet names are <=31 characters and contain none of `\ / * ? : [ ]`
- [ ] No string cell exceeds 32,767 characters and no export exceeds 16,384 columns
- [ ] Formulas requiring computed downstream values were pre-calculated in code, not left as formula text

## Related Skills

- [[docx-generation]] -- the Word-document counterpart sharing the same library-selection approach
- [[pptx-generation]] -- generate slide decks whose charts consume this spreadsheet data
- [[data-pipeline-design]] -- design the ETL pipeline that feeds DataFrame-to-Excel export
- [[python-expert]] -- Python language patterns for spreadsheet generation backends
- [[sql-expert]] -- write the queries whose results become styled Excel workbooks
