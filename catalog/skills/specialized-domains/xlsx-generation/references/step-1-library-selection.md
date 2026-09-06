### Step 1: Library Selection

Choosing the right library depends on whether you need read/write access, write-only performance, language ecosystem, and specific feature requirements.

**Decision Matrix**:

| Feature | openpyxl (Python) | xlsxwriter (Python) | ExcelJS (Node.js) | Apache POI (Java) | Pandas to_excel |
|---------|-------------------|---------------------|--------------------|--------------------|-----------------|
| Read XLSX | Yes | No | Yes | Yes | Yes (via openpyxl) |
| Write XLSX | Yes | Yes | Yes | Yes | Yes (via openpyxl/xlsxwriter) |
| Modify existing | Yes | No | Yes | Yes | No |
| Streaming write | Yes (write-only mode) | Yes (default) | Yes | Yes (SXSSF) | No |
| Formulas | Yes | Yes | Yes | Yes | Limited |
| Charts | Yes | Yes | Yes | Yes | No |
| Conditional formatting | Yes | Yes | Yes | Yes | Via Styler |
| VBA macro support | Yes (preserve) | Yes (xlsm) | No | Yes | No |
| Images | Yes | Yes | Yes | Yes | No |
| Memory efficiency | Moderate | High | Moderate | Low (HSSF) / High (SXSSF) | Low |
| Max rows | 1,048,576 | 1,048,576 | 1,048,576 | 1,048,576 | 1,048,576 |
| Install | `pip install openpyxl` | `pip install xlsxwriter` | `npm i exceljs` | Maven/Gradle | `pip install pandas openpyxl` |

**When to Use Each Library**:

- **openpyxl**: Default choice for Python when you need both read and write, or must modify existing files. Best for template-based report generation where you load a template and fill in data
- **xlsxwriter**: Best for Python write-only scenarios requiring maximum performance and feature richness (conditional formatting, sparklines, data validation). Cannot read or modify existing files
- **ExcelJS**: The standard choice for Node.js/TypeScript projects. Supports read, write, and streaming. Good feature coverage for most business requirements
- **Apache POI**: The Java ecosystem standard. Use XSSF for full-featured access or SXSSF for streaming large datasets. Heaviest memory footprint but most mature library
- **Pandas to_excel**: Best when your data is already in DataFrames. Not a standalone Excel library; delegates to openpyxl or xlsxwriter under the hood. Use for quick exports; switch to the underlying library when you need formatting control

**Installation and Setup**:

```python
# Python: openpyxl (read/write)
pip install openpyxl

# Python: xlsxwriter (write-only, high performance)
pip install xlsxwriter

# Python: Pandas with Excel support
pip install pandas openpyxl  # or pandas xlsxwriter
```

```bash
# Node.js: ExcelJS
npm install exceljs
```

```xml
<!-- Java: Apache POI (Maven) -->
<dependency>
    <groupId>org.apache.poi</groupId>
    <artifactId>poi-ooxml</artifactId>
    <version>5.2.5</version>
</dependency>
```

**Choosing Based on Use Case**:

```
Need to read existing XLSX?
  ├─ Yes → openpyxl (Python), ExcelJS (Node), POI (Java)
  └─ No → Write-only?
       ├─ Yes, large dataset → xlsxwriter (Python), SXSSF (Java)
       ├─ Yes, data already in DataFrame → pandas.to_excel
       └─ Yes, Node.js project → ExcelJS

Need to preserve VBA macros?
  ├─ Yes → openpyxl (keep_vba=True), POI
  └─ No → Any library

Need charts + conditional formatting + data validation?
  ├─ Yes → xlsxwriter (Python), POI (Java), ExcelJS (Node)
  └─ Basic formatting only → Any library
```
