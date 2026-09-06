### Step 1: Library Selection

Choose a PPTX generation library based on your runtime environment, feature requirements, and integration constraints. The following decision matrix compares the four primary options.

**Library Comparison Matrix**:

| Criteria | python-pptx | PptxGenJS | Apache POI | LibreOffice (CLI) |
|----------|-------------|-----------|------------|-------------------|
| Language | Python | JavaScript/TypeScript | Java/Kotlin | Any (CLI wrapper) |
| License | MIT | MIT | Apache 2.0 | MPL 2.0 |
| Template support | Full (load/modify .pptx) | Limited (no template loading) | Full (load/modify .pptx) | Full (via UNO API) |
| Chart support | Native (OOXML charts) | Built-in chart types | Native (OOXML charts) | Full (via template) |
| Table support | Full with merged cells | Full with styling | Full with merged cells | Full |
| Image support | PNG, JPEG, SVG (via EMF) | PNG, JPEG, SVG, GIF | PNG, JPEG, EMF, WMF | All formats |
| Master slides | Read and modify | Create from scratch only | Read and modify | Read and modify |
| File size | Small (efficient XML) | Small | Medium (Java overhead) | Depends on conversion |
| Dependencies | Pure Python | Zero dependencies (browser/Node) | JVM required | LibreOffice installation |
| Maturity | Stable, widely used | Active, growing | Very mature | Very mature |
| Best for | Backend report generation | Browser/Node slide builders | Enterprise Java stacks | Converting other formats |

**Decision Guide**:

- **Choose python-pptx** when you have a Python backend, need to load and modify existing templates, require native OOXML chart support, or are building data pipeline report generators
- **Choose PptxGenJS** when you need browser-side generation, are building a Node.js service, want zero-dependency simplicity, or need to generate slides from a web application
- **Choose Apache POI** when you are in a Java/Kotlin ecosystem, need enterprise-grade OOXML manipulation, or must integrate with existing Java reporting infrastructure
- **Choose LibreOffice CLI** when you need to convert other formats (HTML, Markdown, ODP) to PPTX, require a headless server-side converter, or need PDF export from slides

**Installation**:

```bash
# python-pptx (Python)
pip install python-pptx
# or with uv
uv pip install python-pptx

# PptxGenJS (Node.js)
npm install pptxgenjs
# or browser via CDN
# <script src="https://cdn.jsdelivr.net/npm/pptxgenjs/dist/pptxgenjs.bundle.js"></script>

# Apache POI (Maven)
# <dependency>
#   <groupId>org.apache.poi</groupId>
#   <artifactId>poi-ooxml</artifactId>
#   <version>5.2.5</version>
# </dependency>

# LibreOffice CLI (system package)
# apt install libreoffice-impress   # Debian/Ubuntu
# brew install --cask libreoffice   # macOS
```
