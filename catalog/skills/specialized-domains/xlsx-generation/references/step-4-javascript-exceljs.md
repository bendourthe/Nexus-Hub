### Step 4: JavaScript ExcelJS

ExcelJS is the standard library for Excel generation in Node.js and TypeScript projects. It supports reading, writing, and streaming with comprehensive formatting options.

**Basic Workbook Creation**:

```javascript
const ExcelJS = require("exceljs");

async function createReport() {
  const wb = new ExcelJS.Workbook();
  wb.creator = "Report Generator";
  wb.created = new Date();

  const ws = wb.addWorksheet("Sales Report", {
    properties: { tabColor: { argb: "2F5496" } },
    pageSetup: {
      paperSize: 9, // A4
      orientation: "landscape",
      fitToPage: true,
    },
  });

  // Define columns with headers, keys, and widths
  ws.columns = [
    { header: "Product", key: "product", width: 25 },
    { header: "Revenue", key: "revenue", width: 15, style: { numFmt: "$#,##0.00" } },
    { header: "Cost", key: "cost", width: 15, style: { numFmt: "$#,##0.00" } },
    { header: "Profit", key: "profit", width: 15, style: { numFmt: "$#,##0.00" } },
    { header: "Margin", key: "margin", width: 12, style: { numFmt: "0.0%" } },
  ];

  // Add rows using key-value objects
  ws.addRow({ product: "Widget A", revenue: 15000.50, cost: 8000, profit: 7000.50, margin: 0.4667 });
  ws.addRow({ product: "Widget B", revenue: 22000.75, cost: 12000, profit: 10000.75, margin: 0.4545 });
  ws.addRow({ product: "Widget C", revenue: 8500.00, cost: 5000, profit: 3500.00, margin: 0.4118 });

  // Style the header row
  const headerRow = ws.getRow(1);
  headerRow.eachCell((cell) => {
    cell.font = { bold: true, size: 12, color: { argb: "FFFFFFFF" } };
    cell.fill = {
      type: "pattern",
      pattern: "solid",
      fgColor: { argb: "FF2F5496" },
    };
    cell.alignment = { horizontal: "center", vertical: "middle" };
    cell.border = {
      bottom: { style: "medium", color: { argb: "FF1F3864" } },
    };
  });
  headerRow.height = 25;

  await wb.xlsx.writeFile("sales_report.xlsx");
}

createReport();
```

**Cell Styling and Rich Text**:

```javascript
const ExcelJS = require("exceljs");

async function styledWorkbook() {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("Styled");

  // Rich text in a single cell
  ws.getCell("A1").value = {
    richText: [
      { font: { bold: true, size: 14, color: { argb: "FF2F5496" } }, text: "Q1 2026 " },
      { font: { italic: true, size: 14, color: { argb: "FF666666" } }, text: "Sales Report" },
    ],
  };

  // Conditional fill based on value
  const data = [
    { name: "Widget A", value: 15000 },
    { name: "Widget B", value: -3000 },
    { name: "Widget C", value: 22000 },
  ];

  data.forEach((item, idx) => {
    const row = idx + 3;
    ws.getCell(`A${row}`).value = item.name;
    const valueCell = ws.getCell(`B${row}`);
    valueCell.value = item.value;
    valueCell.numFmt = "$#,##0.00";

    if (item.value < 0) {
      valueCell.font = { color: { argb: "FF9C0006" } };
      valueCell.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: "FFFFC7CE" },
      };
    } else {
      valueCell.font = { color: { argb: "FF006100" } };
      valueCell.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: "FFC6EFCE" },
      };
    }
  });

  // Data validation dropdown
  ws.getCell("C3").dataValidation = {
    type: "list",
    allowBlank: true,
    formulae: ['"Active,Inactive,Pending"'],
    showErrorMessage: true,
    errorTitle: "Invalid",
    error: "Select a valid status.",
  };

  await wb.xlsx.writeFile("styled.xlsx");
}

styledWorkbook();
```

**Streaming Writes for Large Datasets**:

```javascript
const ExcelJS = require("exceljs");
const fs = require("fs");

async function streamLargeDataset() {
  const options = {
    filename: "large_dataset.xlsx",
    useStyles: true,
    useSharedStrings: false, // Disable for better performance
  };

  const wb = new ExcelJS.stream.xlsx.WorkbookWriter(options);
  const ws = wb.addWorksheet("Data");

  // Define columns
  ws.columns = [
    { header: "ID", key: "id", width: 10 },
    { header: "Name", key: "name", width: 25 },
    { header: "Value", key: "value", width: 15 },
    { header: "Category", key: "category", width: 15 },
  ];

  // Stream 500,000 rows without holding them all in memory
  for (let i = 1; i <= 500_000; i++) {
    ws.addRow({
      id: i,
      name: `Item ${i}`,
      value: Math.round(Math.random() * 10000) / 100,
      category: `Cat-${i % 10}`,
    }).commit(); // Flush row to disk immediately
  }

  ws.commit();
  await wb.commit();
}

streamLargeDataset();
```

**Adding Images**:

```javascript
const ExcelJS = require("exceljs");

async function addImages() {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("With Image");

  // Add image from file
  const logoId = wb.addImage({
    filename: "logo.png",
    extension: "png",
  });

  // Position image over a cell range
  ws.addImage(logoId, {
    tl: { col: 0, row: 0 },       // Top-left anchor
    br: { col: 3, row: 4 },       // Bottom-right anchor
    editAs: "oneCell",             // Resize behavior
  });

  // Add image from buffer
  const imageBuffer = fs.readFileSync("chart_screenshot.png");
  const chartId = wb.addImage({
    buffer: imageBuffer,
    extension: "png",
  });

  ws.addImage(chartId, "E1:K15");  // Shorthand range notation

  await wb.xlsx.writeFile("with_images.xlsx");
}
```
