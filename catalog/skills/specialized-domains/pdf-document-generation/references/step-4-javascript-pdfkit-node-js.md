### Step 4: JavaScript PDFKit (Node.js)

PDFKit is a JavaScript library for creating PDF documents in Node.js and the browser. It uses a coordinate-based drawing model similar to ReportLab's canvas API, with support for text, vector graphics, images, and custom fonts.

**Basic Document Creation**:

```javascript
const PDFDocument = require("pdfkit");
const fs = require("fs");

function createInvoice(invoiceData, outputPath) {
  const doc = new PDFDocument({
    size: "A4",
    margins: { top: 72, bottom: 72, left: 72, right: 72 },
    info: {
      Title: `Invoice ${invoiceData.number}`,
      Author: "ACME Corporation",
      Subject: "Invoice",
      CreationDate: new Date(),
    },
  });

  const stream = fs.createWriteStream(outputPath);
  doc.pipe(stream);

  // Company header
  doc
    .fontSize(22)
    .fillColor("#1a1a2e")
    .text("ACME Corporation", { align: "left" });
  doc
    .fontSize(9)
    .fillColor("#666666")
    .text("123 Business Ave, Suite 100")
    .text("contact@acme.example.com")
    .moveDown(2);

  // Invoice metadata
  doc
    .fontSize(14)
    .fillColor("#1a1a2e")
    .text(`Invoice #${invoiceData.number}`)
    .fontSize(10)
    .fillColor("#333333")
    .text(`Bill to: ${invoiceData.clientName}`)
    .text(`Date: ${invoiceData.date}`)
    .moveDown(1.5);

  // Table header
  const tableTop = doc.y;
  const col = { desc: 72, qty: 340, price: 400, total: 470 };

  doc
    .rect(72, tableTop, 468, 20)
    .fill("#1a1a2e");
  doc
    .fontSize(9)
    .fillColor("#ffffff")
    .text("Description", col.desc + 6, tableTop + 5)
    .text("Qty", col.qty, tableTop + 5, { width: 50, align: "right" })
    .text("Unit Price", col.price, tableTop + 5, { width: 60, align: "right" })
    .text("Total", col.total, tableTop + 5, { width: 60, align: "right" });

  // Table rows
  let rowY = tableTop + 24;
  doc.fillColor("#333333").fontSize(9);

  for (const [index, item] of invoiceData.lineItems.entries()) {
    const bgColor = index % 2 === 0 ? "#f8f8f8" : "#ffffff";
    doc.rect(72, rowY - 3, 468, 18).fill(bgColor);
    doc
      .fillColor("#333333")
      .text(item.description, col.desc + 6, rowY)
      .text(String(item.quantity), col.qty, rowY, { width: 50, align: "right" })
      .text(`$${item.unitPrice.toFixed(2)}`, col.price, rowY, { width: 60, align: "right" })
      .text(`$${item.total.toFixed(2)}`, col.total, rowY, { width: 60, align: "right" });
    rowY += 20;
  }

  // Total row
  doc
    .strokeColor("#1a1a2e")
    .lineWidth(1.5)
    .moveTo(col.price, rowY)
    .lineTo(540, rowY)
    .stroke();
  rowY += 6;
  doc
    .fontSize(10)
    .font("Helvetica-Bold")
    .text("Grand Total:", col.price, rowY, { width: 60, align: "right" })
    .text(`$${invoiceData.total.toFixed(2)}`, col.total, rowY, { width: 60, align: "right" });

  doc.end();

  return new Promise((resolve, reject) => {
    stream.on("finish", resolve);
    stream.on("error", reject);
  });
}
```

**Custom Fonts and Unicode**:

```javascript
const PDFDocument = require("pdfkit");
const fs = require("fs");
const path = require("path");

function createDocumentWithCustomFonts(outputPath) {
  const doc = new PDFDocument({ size: "A4" });
  doc.pipe(fs.createWriteStream(outputPath));

  // Register custom font families
  const fontsDir = path.join(__dirname, "fonts");
  doc.registerFont("Inter", path.join(fontsDir, "Inter-Regular.ttf"));
  doc.registerFont("Inter-Bold", path.join(fontsDir, "Inter-Bold.ttf"));
  doc.registerFont("Inter-Italic", path.join(fontsDir, "Inter-Italic.ttf"));
  doc.registerFont("NotoSansCJK", path.join(fontsDir, "NotoSansCJK-Regular.ttc"));

  // Use custom fonts
  doc.font("Inter-Bold").fontSize(18).text("Project Report");
  doc.font("Inter").fontSize(10).text("This document uses embedded Inter font.");

  // Unicode content (CJK characters require an appropriate font)
  doc.font("NotoSansCJK").fontSize(12).text("Japanese: PDF generation guide");

  doc.end();
}
```

**Vector Graphics**:

```javascript
function drawChart(doc, x, y, width, height, data) {
  // Background
  doc.rect(x, y, width, height).fill("#f0f0f0");

  // Simple bar chart
  const barWidth = (width - 20) / data.length - 5;
  const maxValue = Math.max(...data.map((d) => d.value));
  const chartHeight = height - 40;

  for (const [index, item] of data.entries()) {
    const barHeight = (item.value / maxValue) * chartHeight;
    const barX = x + 10 + index * (barWidth + 5);
    const barY = y + height - 20 - barHeight;

    doc.rect(barX, barY, barWidth, barHeight).fill(item.color || "#3366cc");

    // Label below bar
    doc
      .fontSize(7)
      .fillColor("#333")
      .text(item.label, barX, y + height - 15, {
        width: barWidth,
        align: "center",
      });
  }
}
```

**Streaming PDF to HTTP Response** (Express.js):

```javascript
const PDFDocument = require("pdfkit");

app.get("/api/invoices/:id/pdf", async (req, res) => {
  const invoice = await invoiceService.findById(req.params.id);
  if (!invoice) {
    return res.status(404).json({ error: "Invoice not found" });
  }

  res.setHeader("Content-Type", "application/pdf");
  res.setHeader(
    "Content-Disposition",
    `attachment; filename="invoice-${invoice.number}.pdf"`
  );

  const doc = new PDFDocument({ size: "A4" });
  doc.pipe(res);

  // Build document content...
  doc.fontSize(20).text(`Invoice #${invoice.number}`);
  // ... (rest of invoice rendering)

  doc.end();
});
```
