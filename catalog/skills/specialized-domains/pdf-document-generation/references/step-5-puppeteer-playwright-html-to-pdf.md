### Step 5: Puppeteer/Playwright HTML-to-PDF

Puppeteer and Playwright launch a headless Chromium browser to render HTML and convert it to PDF. This approach produces pixel-perfect output that matches what a user sees in a browser, making it ideal for rendering complex layouts, charts (Chart.js, D3), and JavaScript-dependent content.

**Basic Puppeteer PDF Generation**:

```javascript
const puppeteer = require("puppeteer");

async function htmlToPdf(htmlContent, outputPath, options = {}) {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const page = await browser.newPage();
    await page.setContent(htmlContent, { waitUntil: "networkidle0" });

    await page.pdf({
      path: outputPath,
      format: "A4",
      printBackground: true,
      margin: {
        top: "20mm",
        bottom: "25mm",
        left: "20mm",
        right: "20mm",
      },
      displayHeaderFooter: true,
      headerTemplate: `
        <div style="font-size:8px; color:#888; width:100%; padding:0 20mm;">
          <span style="float:left;">ACME Corporation</span>
          <span style="float:right;">Confidential</span>
        </div>`,
      footerTemplate: `
        <div style="font-size:8px; color:#888; width:100%; text-align:center; padding:0 20mm;">
          Page <span class="pageNumber"></span> of <span class="totalPages"></span>
        </div>`,
      ...options,
    });
  } finally {
    await browser.close();
  }
}
```

**URL-to-PDF with Wait Strategies**:

```javascript
const puppeteer = require("puppeteer");

async function urlToPdf(url, outputPath, waitOptions = {}) {
  const browser = await puppeteer.launch({ headless: "new" });

  try {
    const page = await browser.newPage();

    // Set viewport for consistent rendering
    await page.setViewport({ width: 1200, height: 800 });

    await page.goto(url, {
      waitUntil: waitOptions.waitUntil || "networkidle0",
      timeout: waitOptions.timeout || 30000,
    });

    // Wait for specific content to be rendered (useful for JS-heavy pages)
    if (waitOptions.waitForSelector) {
      await page.waitForSelector(waitOptions.waitForSelector, {
        timeout: 10000,
      });
    }

    // Wait for custom "ready" signal from the page
    if (waitOptions.waitForReadySignal) {
      await page.waitForFunction(
        () => window.__PDF_READY === true,
        { timeout: 15000 }
      );
    }

    // Inject print-specific CSS
    await page.addStyleTag({
      content: `
        @media print {
          nav, .sidebar, .no-print { display: none !important; }
          body { font-size: 10pt; }
          a { color: inherit; text-decoration: none; }
        }
      `,
    });

    await page.pdf({
      path: outputPath,
      format: "A4",
      printBackground: true,
      margin: { top: "20mm", bottom: "20mm", left: "15mm", right: "15mm" },
    });
  } finally {
    await browser.close();
  }
}
```

**Playwright Equivalent** (Playwright has a nearly identical API and supports Chromium, Firefox, and WebKit):

```javascript
const { chromium } = require("playwright");

async function playwrightHtmlToPdf(htmlContent, outputPath) {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.setContent(htmlContent, { waitUntil: "networkidle" });

  await page.pdf({
    path: outputPath,
    format: "A4",
    printBackground: true,
    margin: { top: "20mm", bottom: "25mm", left: "20mm", right: "20mm" },
    displayHeaderFooter: true,
    headerTemplate: "<div></div>",
    footerTemplate: `
      <div style="font-size:8px; color:#888; width:100%; text-align:center;">
        Page <span class="pageNumber"></span> of <span class="totalPages"></span>
      </div>`,
  });

  await browser.close();
}
```

**Reusing a Browser Instance** (performance optimization for batch generation):

```javascript
const puppeteer = require("puppeteer");

class PdfGenerator {
  constructor() {
    this._browser = null;
  }

  async initialize() {
    this._browser = await puppeteer.launch({
      headless: "new",
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
    });
  }

  async generatePdf(htmlContent, options = {}) {
    if (!this._browser) {
      throw new Error("Browser not initialized. Call initialize() first.");
    }

    const page = await this._browser.newPage();
    try {
      await page.setContent(htmlContent, { waitUntil: "networkidle0" });
      const pdfBuffer = await page.pdf({
        format: options.format || "A4",
        printBackground: true,
        margin: options.margin || {
          top: "20mm", bottom: "20mm", left: "20mm", right: "20mm",
        },
      });
      return pdfBuffer;
    } finally {
      await page.close();
    }
  }

  async shutdown() {
    if (this._browser) {
      await this._browser.close();
      this._browser = null;
    }
  }
}

// Usage in a batch pipeline
async function generateBatchInvoices(invoices, templateFn) {
  const generator = new PdfGenerator();
  await generator.initialize();

  try {
    for (const invoice of invoices) {
      const html = templateFn(invoice);
      const pdfBuffer = await generator.generatePdf(html);
      fs.writeFileSync(`invoices/invoice-${invoice.number}.pdf`, pdfBuffer);
    }
  } finally {
    await generator.shutdown();
  }
}
```
