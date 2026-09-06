### Step 1: Library Selection Guide

Choosing the right PDF library depends on your language ecosystem, the complexity of your layouts, whether you need HTML/CSS input, and your deployment constraints. The following decision matrix covers the five most widely used libraries.

**Library Comparison Matrix**:

| Criterion | ReportLab (Python) | WeasyPrint (Python) | PDFKit (Node.js) | Puppeteer (Node.js) | jsPDF (Browser/Node) |
|---|---|---|---|---|---|
| Input format | Python API calls | HTML + CSS | JavaScript API calls | HTML + CSS | JavaScript API calls |
| Layout model | Absolute + flowable | CSS box model | Absolute positioning | Full browser rendering | Absolute positioning |
| Complex tables | Excellent | Good (HTML tables) | Manual positioning | Excellent (HTML tables) | Basic via plugin |
| Custom fonts | TTF embedding | WOFF/TTF via CSS | TTF/OTF embedding | System + web fonts | TTF embedding |
| Image support | PNG, JPEG, SVG | PNG, JPEG, SVG, GIF | PNG, JPEG | All browser formats | PNG, JPEG |
| PDF/A support | Yes (with pdfa module) | Limited | No | No | No |
| Form fields | Yes | No | No | No | No (plugin: AcroForm) |
| File size | Small (vector-native) | Medium | Small (vector-native) | Large (rasterized content) | Small |
| Server dependency | None | Cairo, Pango, GDK-Pixbuf | None | Headless Chromium (~300 MB) | None |
| Learning curve | Steep | Low (if you know CSS) | Moderate | Low (if you know HTML/CSS) | Moderate |
| Best for | Data-heavy reports, forms | Styled documents from HTML | Server-side Node.js docs | Pixel-perfect web-to-PDF | Client-side generation |

**Decision Flowchart**:

1. **Is the source content already HTML/CSS?** If yes, choose WeasyPrint (Python) or Puppeteer (Node.js). WeasyPrint is lighter weight and produces smaller files. Puppeteer handles JavaScript-rendered content and complex CSS (flexbox, grid).
2. **Do you need PDF form fields or PDF/A compliance?** If yes, choose ReportLab. It is the only library in this list with native support for both.
3. **Are you running in a browser environment?** If yes, choose jsPDF. It runs entirely client-side without a server round-trip.
4. **Do you need precise programmatic control over every element?** If yes, choose ReportLab (Python) or PDFKit (Node.js) depending on your language. Both offer coordinate-level placement.
5. **Do you need to render charts or dashboards that already exist as web pages?** If yes, choose Puppeteer or Playwright. They render exactly what a browser would show.

**Installation**:

```bash
# Python: ReportLab
pip install reportlab

# Python: WeasyPrint (requires system dependencies on Linux)
pip install weasyprint
# Debian/Ubuntu: apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0

# Node.js: PDFKit
npm install pdfkit

# Node.js: Puppeteer (downloads Chromium automatically)
npm install puppeteer

# Browser/Node.js: jsPDF
npm install jspdf
```
