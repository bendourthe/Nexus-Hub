---
description: Run a deep review of the codebase and generate a well-structured report (Markdown & DOCX) with executive summary, component analysis, and user manual.
---

# Generate Codebase Report Command

Analyze the codebase and generate a comprehensive report in both Markdown and DOCX formats.

## Process

1.  **Deep Codebase Analysis**
    *   Scan the project structure.
    *   Identify key components, their purpose, and interactions.
    *   Analyze the `README.md` and other documentation for context.
    *   Identify potential issues or optimization areas.

2.  **Generate Report Content (JSON)**
    *   Construct a JSON object with the following structure:
        ```json
        {
          "title": "Codebase Deep Dive Report",
          "subtitle": "Analysis of [Project Name]",
          "author": "DevAI-Hub Agent",
          "purpose": "Detailed paragraph explaining the report's purpose.",
          "executive_summary": "One or two paragraphs summarizing the purpose of the codebase, how it works, and how it can be used.",
          "components": [
            {
              "name": "Component Name",
              "description": "Brief description.",
              "details": "Detailed explanation of functionality, file location, and usage."
            }
          ],
          "user_manual": "Detailed user manual with steps on how to use the app.",
          "issues": ["List of potential issues", "Optimization suggestions"]
        }
        ```
    *   Save this JSON to `report_data.json`.

3.  **Generate Markdown Report**
    *   Create a file `Codebase_Report.md` using the data from the analysis.
    *   Include all sections: Title, Purpose, Executive Summary, Component Analysis, User Manual.

4.  **Generate DOCX Report**
    *   Check if `python-docx` is installed. If not, ask the user to run `pip install python-docx`.
    *   The helper script `scripts/generate_report.py` handles the DOCX generation.
    *   Run the script: `python scripts/generate_report.py report_data.json`
    *   If the script is missing, create it first using the content below:

<details>
<summary>scripts/generate_report.py content (if missing)</summary>

```python
import json
import sys
import os
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    print("Error: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)

def create_report(data_file):
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    doc = Document()
    
    # Title Page
    doc.add_heading(data.get("title", "Report"), 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(data.get("subtitle", "")).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"\nAuthor: {data.get('author', 'Agent')}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    # Sections
    sections = [
        ("1. Document Purpose", "purpose"),
        ("2. Executive Summary", "executive_summary"),
        ("3. User Manual", "user_manual")
    ]
    
    for title, key in sections:
        doc.add_heading(title, level=1)
        doc.add_paragraph(data.get(key, "N/A"))

    # Components
    doc.add_heading("4. Component Analysis", level=1)
    for comp in data.get("components", []):
        doc.add_heading(comp.get("name", "Component"), level=2)
        doc.add_paragraph(f"Description: {comp.get('description', '')}")
        doc.add_paragraph(comp.get("details", ""))

    output_file = "Codebase_Report.docx"
    doc.save(output_file)
    print(f"Generated: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_report(sys.argv[1])
    else:
        print("Usage: python generate_report.py <json_file>")
```
</details>

## Output
*   `Codebase_Report.md`: Markdown version of the report.
*   `Codebase_Report.docx`: Professional Word document (if python-docx is available).
