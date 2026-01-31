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
          "title": "[Project Name] Codebase Report",
          "subtitle": "A Comprehensive Evaluation of [Project]’s Capabilities, Architectural Patterns, and Deployment Systems",
          "header_subtitle": "Capabilities, Architecture, and Deployment Evaluation",
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

3.  **Generate Reports**
    *   Check if `python-docx` is installed. If not, ask the user to run `pip install python-docx`.
    *   The helper script `scripts/generate_report.py` handles both Markdown and DOCX generation.
    *   Run the script: `python scripts/generate_report.py report_data.json`
    *   **Features**:
        *   **Authorship**: Automatically detects `git config user.name` if available.
        *   **Silent TOC Update**: Pre-calculates TOC via background PowerShell process.
        *   **Professional Layout**: 1.0" Body Margins, 0.5" Header/Footer Margins, Centered Title Page.
        *   **Dynamic Titles**: Supports short headers via `header_subtitle`.
    *   If the script is missing, create it first using the content below:

<details>
<summary>scripts/generate_report.py content (if missing)</summary>

```python
import json
import sys
import os
import subprocess
import re
from datetime import datetime

try:
    from docx import Document
# ... (See full implementation in scripts/generate_report.py)
```
</details>

## Output
*   `Codebase_Report.md`: Markdown version of the report (with TOC and Appendix).
*   `Codebase_Report.docx`: Professional Word document (with Title Page, Headers/Footers, TOC).
