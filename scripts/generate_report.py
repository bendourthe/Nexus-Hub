# Version: 0.7.0

import json
import sys
import os
import subprocess
import re
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.enum.section import WD_SECTION
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from docx.enum.table import WD_TABLE_ALIGNMENT
except ImportError:
    print("Error: python-docx not installed. Please run: pip install python-docx")
    sys.exit(1)

# python-pptx is optional; only required for --type generic-pptx
PPTX_AVAILABLE = False
try:
    from pptx import Presentation
    from pptx.util import Inches as PptxInches, Pt as PptxPt, Emu
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.dml.color import RGBColor as PptxRGBColor
    PPTX_AVAILABLE = True
except ImportError:
    pass

# Manual constant definitions
WD_ALIGN_VERTICAL_TOP = 0
WD_ALIGN_VERTICAL_CENTER = 1
WD_ALIGN_VERTICAL_BOTTOM = 3

def get_git_user_name():
    try:
        result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
        name = result.stdout.strip()
        if name:
            return name
    except Exception:
        pass
    return None

def resolve_author(data_author):
    git_user = get_git_user_name()
    if git_user:
        return git_user
    if data_author and data_author != "DevAI-Hub Agent":
        return data_author
    return "DevAI-Hub Agent"

# --- DOCX Helpers ---

def create_element(name):
    return OxmlElement(name)

def create_attribute(element, name, value):
    element.set(qn(name), value)

def add_page_number(paragraph):
    """Adds 'Page X of Y' to a paragraph."""
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.add_run("Page ")
    
    run1 = paragraph.add_run()
    fldChar1 = create_element('w:fldChar')
    create_attribute(fldChar1, 'w:fldCharType', 'begin')
    run1._r.append(fldChar1)

    run2 = paragraph.add_run()
    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = "PAGE"
    run2._r.append(instrText)

    run3 = paragraph.add_run()
    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'end')
    run3._r.append(fldChar2)

    paragraph.add_run(" of ")

    run4 = paragraph.add_run()
    fldChar3 = create_element('w:fldChar')
    create_attribute(fldChar3, 'w:fldCharType', 'begin')
    run4._r.append(fldChar3)

    run5 = paragraph.add_run()
    instrText2 = create_element('w:instrText')
    create_attribute(instrText2, 'xml:space', 'preserve')
    instrText2.text = "NUMPAGES"
    run5._r.append(instrText2)

    run6 = paragraph.add_run()
    fldChar4 = create_element('w:fldChar')
    create_attribute(fldChar4, 'w:fldCharType', 'end')
    run6._r.append(fldChar4)

def add_toc(doc):
    """Inserts a Native Word Table of Contents field."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    run = paragraph.add_run()
    fldChar = create_element('w:fldChar')
    create_attribute(fldChar, 'w:fldCharType', 'begin')
    # No dirty flag - we rely on PowerShell post-processing
    run._r.append(fldChar)
    
    run2 = paragraph.add_run()
    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    run2._r.append(instrText)
    
    run3 = paragraph.add_run()
    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'separate')
    run3._r.append(fldChar2)
    
    # Placeholder text so it's not empty if PS fails
    run_placeholder = paragraph.add_run("Right-click to update Table of Contents")
    run_placeholder.italic = True
    
    run4 = paragraph.add_run()
    fldChar3 = create_element('w:fldChar')
    create_attribute(fldChar3, 'w:fldCharType', 'end')
    run4._r.append(fldChar3)

def update_toc_via_word(docx_path):
    """Uses PowerShell/Word Interop to update TOC fields."""
    abs_path = os.path.abspath(docx_path)
    print(f"Attempting to update TOC via Word Interop for: {abs_path}")
    
    # PowerShell command to open Word, update TOC, save, and quit.
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    try {{
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        if (!$word) {{ exit 1 }}
        $doc = $word.Documents.Open('{abs_path}')
        $doc.TablesOfContents | ForEach-Object {{ $_.Update() }}
        $doc.Save()
        $doc.Close()
        $word.Quit()
        exit 0
    }} catch {{
        Write-Host "Error updating TOC: $_"
        if ($word) {{ $word.Quit() }}
        exit 1
    }}
    """
    
    try:
        result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully updated TOC via Word.")
        else:
            print(f"Word TOC update failed (skipping): {result.stdout}")
    except Exception as e:
        print(f"Could not run PowerShell TOC update: {e}")

def add_formatted_text(paragraph, text):
    """
    Parses markdown formatting (bold, code) and adds it to the paragraph.
    Supports **bold** and `code` styles.
    """
    if not text:
        return

    # Split by bold markers first
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            # This segment is bold
            content_text = part[2:-2]
            # Check for code inside bold (rare, but possible: **`code`**)
            code_parts = re.split(r'(`.*?`)', content_text)
            for cp in code_parts:
                if cp.startswith('`') and cp.endswith('`'):
                    run = paragraph.add_run(cp[1:-1])
                    run.bold = True
                    run.font.name = 'Courier New'
                else:
                    if cp:
                        run = paragraph.add_run(cp)
                        run.bold = True
        else:
            # This segment is not bold, check for code
            if not part:
                continue
            code_parts = re.split(r'(`.*?`)', part)
            for cp in code_parts:
                if cp.startswith('`') and cp.endswith('`'):
                    run = paragraph.add_run(cp[1:-1])
                    run.font.name = 'Courier New'
                else:
                    if cp:
                        paragraph.add_run(cp)

def add_list_item(doc, text, style='List Bullet'):
    """Safe list item addition with formatting."""
    try:
        p = doc.add_paragraph(style=style)
    except (KeyError, ValueError):
        # Fallback if style doesn't exist
        p = doc.add_paragraph()
        if style == 'List Bullet':
            p.add_run("• ")
        elif style == 'List Number':
            pass 
            
    add_formatted_text(p, text)

def add_markdown_paragraph(doc, text, style=None):
    """Parses markdown (headers, lists, bold, code) and adds it to the document."""
    if not text:
        return

    lines = text.split('\n')
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Code Blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            p = doc.add_paragraph(line if line else " ")
            try:
                p.style = doc.styles['Normal']
            except: pass
            if p.runs:
                font = p.runs[0].font
                font.name = 'Courier New'
                font.size = Pt(9)
            continue

        # Headers (### Title)
        if stripped.startswith('#'):
            level = len(stripped.split(' ', 1)[0])
            content = stripped.split(' ', 1)[1] if ' ' in stripped else stripped
            if level > 9: level = 9
            doc.add_heading(content, level=level)
            continue

        # List Items (Bullets)
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:]
            add_list_item(doc, content, style='List Bullet')
            continue
        
        # List Items (Numbered)
        if stripped and len(stripped) > 2 and stripped[0].isdigit() and stripped[1:3] in ['. ', ') ']:
             content = stripped.split(' ', 1)[1] if ' ' in stripped else stripped
             add_list_item(doc, content, style='List Number')
             continue

        # Normal Paragraph
        p = doc.add_paragraph(style=style)
        add_formatted_text(p, line)

def generate_tree_structure(startpath, prefix=""):
    tree_str = ""
    try:
        items = os.listdir(startpath)
    except OSError:
        return ""
    items = [i for i in items if not i.startswith('.')] 
    items.sort()
    for index, item in enumerate(items):
        path = os.path.join(startpath, item)
        is_last = (index == len(items) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{item}\n"
        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            tree_str += generate_tree_structure(path, prefix + extension)
    return tree_str

# --- Generators ---

def generate_markdown_report(data, author, tree_structure, output_file="Codebase_Report.md"):
    title = data.get("title", "Codebase Report")
    subtitle = data.get("subtitle", "")
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    md_content = f"""# {title}
**Subtitle**: {subtitle}
**Author**: {author}
**Date**: {date_str}

## Document's Purpose
{data.get('purpose', 'N/A')}

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Component Analysis](#2-component-analysis)
3. [Dependencies & Prerequisites](#3-dependencies--prerequisites)
4. [User Manual & Usage Guide](#4-user-manual--usage-guide)
5. [Improvements & Optimizations](#5-improvements--optimizations)
6. [Appendix A: Project Architecture](#appendix-a-project-architecture)

## 1. Executive Summary
{data.get('executive_summary', 'N/A')}

## 2. Component Analysis
"""
    for comp in data.get("components", []):
        md_content += f"\n### {comp.get('name', 'Component')}\n"
        md_content += f"**Description**: {comp.get('description', '')}\n\n"
        md_content += f"{comp.get('details', '')}\n"

    md_content += "\n## 3. Dependencies & Prerequisites\n"
    deps = data.get("dependencies", [])
    if isinstance(deps, dict):
        for category, items in deps.items():
            md_content += f"\n### {category}\n"
            for item in items:
                md_content += f"- {item}\n"
    elif isinstance(deps, list):
        for d in deps:
            md_content += f"- {d}\n"
    else:
        md_content += f"{deps}\n"

    md_content += f"\n## 4. User Manual & Usage Guide\n{data.get('user_manual', 'N/A')}\n"

    md_content += "\n## 5. Improvements & Optimizations\n"
    issues = data.get("issues", [])
    if isinstance(issues, dict):
        for category, items in issues.items():
            md_content += f"\n### {category}\n"
            for item in items:
                md_content += f"- {item}\n"
    elif isinstance(issues, list):
        for issue in issues:
            md_content += f"- {issue}\n"
    else:
        md_content += f"{issues}\n"

    md_content += f"\n## Appendix A: Project Architecture\n```text\n{tree_structure}\n```\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Generated Markdown: {output_file}")


def generate_docx_report(data, author, tree_structure, output_file="Codebase_Report.docx"):
    doc = Document()
    
    # Title Logic
    raw_title = data.get("title", "Codebase Report")
    project_name = os.path.basename(os.getcwd())
    if "Codebase Deep Dive Report" in raw_title or raw_title.strip() == "Codebase Report":
        # Force project name
        title = f"{project_name} Codebase Report"
    else:
        title = raw_title
        
    subtitle = data.get("subtitle", "Detailed Codebase Analysis")
    header_subtitle = data.get("header_subtitle", subtitle) # Fallback to full subtitle if short one is missing

    # --- Section 0: Title Page (Centered) ---
    section0 = doc.sections[0]
    # Set Margins to 1 inch
    section0.left_margin = Inches(1)
    section0.right_margin = Inches(1)
    section0.top_margin = Inches(1)
    section0.bottom_margin = Inches(1)
    
    # User reported vertical alignment property wasn't working reliably. 
    # Using manual buffer lines to force visual centering.
    section0.vertical_alignment = WD_ALIGN_VERTICAL_TOP 
    
    # Add buffer lines for vertical centering
    for _ in range(8):
        doc.add_paragraph()
    
    # Title Content
    title_p = doc.add_heading(title, 0)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle_p = doc.add_paragraph(subtitle)
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_p.runs[0].italic = True
    
    doc.add_paragraph() 
    
    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_p.add_run(f"Author: {author}\n")
    meta_p.add_run(f"Date: {datetime.now().strftime('%B %d, %Y')}")

    # --- Section 1: Main Content (Top Aligned) ---
    section_break = doc.add_section(WD_SECTION.NEW_PAGE)
    
    # Access the new section
    section1 = doc.sections[-1]
    section1.vertical_alignment = WD_ALIGN_VERTICAL_TOP
    # Set Margins to 1 inch
    section1.left_margin = Inches(1)
    section1.right_margin = Inches(1)
    section1.top_margin = Inches(1)
    section1.bottom_margin = Inches(1)
    
    # -- Setup Header (Section 1) --
    header = section1.header
    header.is_linked_to_previous = False
    
    for p in header.paragraphs:
         element = p._element
         if element.getparent():
             element.getparent().remove(element)

    # Header Table: 7.5 inches wide (extends 0.5 inch into margins on each side)
    htable = header.add_table(rows=1, cols=2, width=Inches(7.5))
    htable.alignment = WD_TABLE_ALIGNMENT.CENTER
    htable.autofit = False
    htable.columns[0].width = Inches(3.75)
    htable.columns[1].width = Inches(3.75)
    
    cell_h_left = htable.cell(0, 0)
    p_h_left = cell_h_left.paragraphs[0]
    p_h_left.text = title
    p_h_left.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    cell_h_right = htable.cell(0, 1)
    p_h_right = cell_h_right.paragraphs[0]
    p_h_right.text = header_subtitle
    p_h_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # -- Setup Footer (Section 1) --
    footer = section1.footer
    footer.is_linked_to_previous = False
    
    for p in footer.paragraphs:
         element = p._element
         if element.getparent():
             element.getparent().remove(element)

    # Footer Table: 7.5 inches wide
    ftable = footer.add_table(rows=1, cols=2, width=Inches(7.5))
    ftable.alignment = WD_TABLE_ALIGNMENT.CENTER
    ftable.autofit = False
    ftable.columns[0].width = Inches(3.75)
    ftable.columns[1].width = Inches(3.75)

    cell_f_left = ftable.cell(0, 0)
    p_f_left = cell_f_left.paragraphs[0]
    p_f_left.text = author
    p_f_left.alignment = WD_ALIGN_PARAGRAPH.LEFT

    cell_f_right = ftable.cell(0, 1)
    p_f_right = cell_f_right.paragraphs[0]
    p_f_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_page_number(p_f_right)

    # --- Content ---
    doc.add_heading("Document's Purpose", level=1)
    doc.add_paragraph(data.get("purpose", ""))

    doc.add_heading("Table of Contents", level=1)
    add_toc(doc)
    doc.add_page_break()

    doc.add_heading("1. Executive Summary", level=1)
    # Ensure this is not empty
    exec_sum = data.get("executive_summary", "N/A")
    add_markdown_paragraph(doc, exec_sum)

    doc.add_heading("2. Component Analysis", level=1)
    for comp in data.get("components", []):
        doc.add_heading(comp.get("name", "Component"), level=2)
        desc = comp.get("description", "")
        if desc:
            p = doc.add_paragraph()
            p.add_run("Description: ").bold = True
            p.add_run(desc)
        
        details = comp.get("details", "")
        if details:
            add_markdown_paragraph(doc, details)

    doc.add_heading("3. Dependencies & Prerequisites", level=1)
    deps = data.get("dependencies", [])
    if deps:
        if isinstance(deps, dict):
            for category, items in deps.items():
                doc.add_heading(category, level=2)
                for item in items:
                    add_list_item(doc, item)
        elif isinstance(deps, list):
            for d in deps:
                add_list_item(doc, d)
        else:
            add_markdown_paragraph(doc, deps)
    else:
        doc.add_paragraph("No dependencies specified.")

    doc.add_heading("4. User Manual & Usage Guide", level=1)
    manual = data.get("user_manual", "")
    if manual:
        add_markdown_paragraph(doc, manual)
    else:
        doc.add_paragraph("No user manual provided.")

    doc.add_heading("5. Improvements & Optimizations", level=1)
    issues = data.get("issues", [])
    if issues:
        if isinstance(issues, dict):
            for category, items in issues.items():
                doc.add_heading(category, level=2)
                for item in items:
                    add_list_item(doc, item)
        elif isinstance(issues, list):
            for issue in issues:
                add_list_item(doc, issue)
        else:
            add_markdown_paragraph(doc, issues)
    else:
        doc.add_paragraph("No issues identified.")

    # --- Appendix ---
    doc.add_page_break()
    doc.add_heading("Appendix A: Project Architecture", level=1)
    
    p = doc.add_paragraph(tree_structure)
    try:
        p.style = doc.styles['Normal']
    except: pass
    p.runs[0].font.name = 'Courier New'
    p.runs[0].font.size = Pt(9)

    doc.save(output_file)
    print(f"Generated DOCX: {output_file}")
    
    # Run TOC Updater
    update_toc_via_word(output_file)


# --- Code Review Report Generators ---

def _build_redundancy_section(redundancy_data):
    """Build the Redundancy & Trimming markdown from either a string or structured object."""
    if not redundancy_data:
        return "No redundancy identified."
    if isinstance(redundancy_data, str):
        return redundancy_data

    # Structured format: { safe_removals, simplifications, trade_off_removals }
    sections = []

    safe = redundancy_data.get("safe_removals", "")
    if safe:
        sections.append(f"### Safe Removals (zero behavior impact)\n\n{safe}")

    simplifications = redundancy_data.get("simplifications", "")
    if simplifications:
        sections.append(f"### Simplifications (same outcome, less complexity)\n\n{simplifications}")

    trade_offs = redundancy_data.get("trade_off_removals", "")
    if trade_offs:
        sections.append(f"### Trade-off Removals (pros/cons analysis)\n\n{trade_offs}")

    return "\n\n".join(sections) if sections else "No redundancy identified."


def generate_code_review_markdown(data, author, tree_structure, output_file="Code_Review_Report.md"):
    """Generates a Markdown code review report following the 4-section structure."""
    title = data.get("title", "Code Review Report")
    subtitle = data.get("subtitle", "")
    review_date = data.get("review_date", datetime.now().strftime("%Y-%m-%d"))
    mode = data.get("mode", "Full Codebase")
    verdict = data.get("verdict", "COMMENT")
    exec_summary = data.get("executive_summary", {})
    stats = exec_summary.get("statistics", {})
    total = stats.get("total", stats.get("p0", 0) + stats.get("p1", 0) + stats.get("p2", 0) + stats.get("p3", 0))

    md = f"""# {title}

**Subtitle**: {subtitle}
**Author**: {author}
**Review Date**: {review_date}
**Mode**: {mode}
**Overall Verdict**: {verdict}

---

## Table of Contents

1. [Section 1: Codebase Overview](#section-1-codebase-overview)
2. [Section 2: Executive Summary](#section-2-executive-summary)
3. [Section 3: Detailed Report](#section-3-detailed-report)
   - [Phase 1: By Feature/Functionality](#phase-1-grouped-by-featurefunctionality)
   - [Phase 2: By Priority](#phase-2-grouped-by-priority)
4. [Appendix: Project Architecture](#appendix-project-architecture)

---

# Section 1: Codebase Overview

{data.get("codebase_overview", "N/A")}

---

# Section 2: Executive Summary

## Verdict: {verdict}

| Metric | Count |
|--------|-------|
| P0 (Critical) | {stats.get("p0", 0)} |
| P1 (High) | {stats.get("p1", 0)} |
| P2 (Medium) | {stats.get("p2", 0)} |
| P3 (Low) | {stats.get("p3", 0)} |
| **Total** | **{total}** |

**Risk Level**: {exec_summary.get("risk_level", "N/A")} - {exec_summary.get("risk_justification", "")}

## Critical Fixes

{exec_summary.get("critical_fixes", "No critical fixes identified.")}

## Functional Groupings

{exec_summary.get("functional_groupings", "N/A")}

## Redundancy & Trimming

{_build_redundancy_section(exec_summary.get("redundancy_trimming"))}

## Roadmap Perspective

### Short-term (minimal effort, high value)

{exec_summary.get("roadmap", {}).get("short_term", "N/A")}

### Long-term (significant development required)

{exec_summary.get("roadmap", {}).get("long_term", "N/A")}

---

# Section 3: Detailed Report

## Phase 1: Grouped by Feature/Functionality

"""

    # Feature groups
    for group in data.get("feature_groups", []):
        group_name = group.get("name", "Unknown")
        finding_count = group.get("finding_count", len(group.get("findings", [])))
        md += f"### {group_name} ({finding_count} findings)\n\n"
        md += f"{group.get('summary', '')}\n\n"

        for finding in group.get("findings", []):
            md += f"#### {finding.get('id', '')}. {finding.get('title', '')}\n"
            md += f"**Severity**: {finding.get('severity', '')}\n"
            md += f"**File**: {finding.get('file', '')}:{finding.get('line', '')}\n"
            md += f"**Category**: {finding.get('category', '')}\n\n"
            md += f"**Issue**: {finding.get('description', '')}\n\n"
            md += f"**Impact**: {finding.get('impact', '')}\n\n"
            md += f"**Fix**: {finding.get('fix', '')}\n\n"
            md += f"**Effort**: {finding.get('effort', '')}\n\n"
            md += "---\n\n"

    # Priority view
    md += "## Phase 2: Grouped by Priority\n\n"

    priority_labels = [
        ("p0", "P0 - Critical (must fix)"),
        ("p1", "P1 - High (should fix)"),
        ("p2", "P2 - Medium (recommended)"),
        ("p3", "P3 - Low (optional)")
    ]

    for pkey, plabel in priority_labels:
        findings = data.get("priority_findings", {}).get(pkey, [])
        if not findings:
            # Build from feature_groups if priority_findings not provided
            findings = []
            for group in data.get("feature_groups", []):
                for f in group.get("findings", []):
                    if f.get("severity", "").upper() == pkey.upper():
                        f_copy = dict(f)
                        f_copy["feature_group"] = group.get("name", "")
                        findings.append(f_copy)

        md += f"### {plabel}\n\n"
        if findings:
            md += "| # | Title | Feature Group | File | Impact | Fix |\n"
            md += "|---|-------|---------------|------|--------|-----|\n"
            for i, f in enumerate(findings, 1):
                fg = f.get("feature_group", "")
                md += f"| {i} | {f.get('title', '')} | {fg} | {f.get('file', '')}:{f.get('line', '')} | {f.get('impact', '')} | {f.get('fix', '')} |\n"
            md += "\n"
        else:
            md += "No findings at this severity level.\n\n"

    # Removal plan
    removal = data.get("removal_plan", "")
    if removal:
        md += f"---\n\n## Removal/Iteration Plan\n\n{removal}\n\n"

    # Methodology
    md += f"---\n\n## Methodology\n\n{data.get('methodology', '6-phase code review')}\n\n"

    # Appendix
    md += f"## Appendix: Project Architecture\n\n```text\n{tree_structure}\n```\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"Generated Code Review Markdown: {output_file}")


def generate_code_review_docx(data, author, tree_structure, output_file="Code_Review_Report.docx"):
    """Generates a DOCX code review report following the 4-section structure."""
    doc = Document()

    title = data.get("title", "Code Review Report")
    subtitle = data.get("subtitle", "Comprehensive Code Review")
    header_subtitle = data.get("header_subtitle", "Code Review Report")
    review_date = data.get("review_date", datetime.now().strftime("%Y-%m-%d"))
    mode = data.get("mode", "Full Codebase")
    verdict = data.get("verdict", "COMMENT")
    exec_summary = data.get("executive_summary", {})
    stats = exec_summary.get("statistics", {})
    total = stats.get("total", stats.get("p0", 0) + stats.get("p1", 0) + stats.get("p2", 0) + stats.get("p3", 0))

    # --- Section 0: Title Page ---
    section0 = doc.sections[0]
    section0.left_margin = Inches(1)
    section0.right_margin = Inches(1)
    section0.top_margin = Inches(1)
    section0.bottom_margin = Inches(1)
    section0.vertical_alignment = WD_ALIGN_VERTICAL_TOP

    for _ in range(8):
        doc.add_paragraph()

    title_p = doc.add_heading(title, 0)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle_p = doc.add_paragraph(subtitle)
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_p.runs[0].italic = True

    doc.add_paragraph()

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_p.add_run(f"Author: {author}\n")
    meta_p.add_run(f"Date: {review_date}\n")
    meta_p.add_run(f"Mode: {mode}\n")
    meta_p.add_run(f"Verdict: {verdict}")

    # --- Section 1: Main Content ---
    doc.add_section(WD_SECTION.NEW_PAGE)
    section1 = doc.sections[-1]
    section1.vertical_alignment = WD_ALIGN_VERTICAL_TOP
    section1.left_margin = Inches(1)
    section1.right_margin = Inches(1)
    section1.top_margin = Inches(1)
    section1.bottom_margin = Inches(1)

    # Header
    header = section1.header
    header.is_linked_to_previous = False
    for p in header.paragraphs:
        element = p._element
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    htable = header.add_table(rows=1, cols=2, width=Inches(7.5))
    htable.alignment = WD_TABLE_ALIGNMENT.CENTER
    htable.autofit = False
    htable.columns[0].width = Inches(3.75)
    htable.columns[1].width = Inches(3.75)

    cell_h_left = htable.cell(0, 0)
    p_h_left = cell_h_left.paragraphs[0]
    p_h_left.text = title
    p_h_left.alignment = WD_ALIGN_PARAGRAPH.LEFT

    cell_h_right = htable.cell(0, 1)
    p_h_right = cell_h_right.paragraphs[0]
    p_h_right.text = header_subtitle
    p_h_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Footer
    footer = section1.footer
    footer.is_linked_to_previous = False
    for p in footer.paragraphs:
        element = p._element
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    ftable = footer.add_table(rows=1, cols=2, width=Inches(7.5))
    ftable.alignment = WD_TABLE_ALIGNMENT.CENTER
    ftable.autofit = False
    ftable.columns[0].width = Inches(3.75)
    ftable.columns[1].width = Inches(3.75)

    cell_f_left = ftable.cell(0, 0)
    p_f_left = cell_f_left.paragraphs[0]
    p_f_left.text = author
    p_f_left.alignment = WD_ALIGN_PARAGRAPH.LEFT

    cell_f_right = ftable.cell(0, 1)
    p_f_right = cell_f_right.paragraphs[0]
    p_f_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_page_number(p_f_right)

    # TOC
    doc.add_heading("Table of Contents", level=1)
    add_toc(doc)
    doc.add_page_break()

    # --- Section 1: Codebase Overview ---
    doc.add_heading("Section 1: Codebase Overview", level=1)
    add_markdown_paragraph(doc, data.get("codebase_overview", "N/A"))

    # --- Section 2: Executive Summary ---
    doc.add_heading("Section 2: Executive Summary", level=1)

    doc.add_heading(f"Verdict: {verdict}", level=2)

    # Statistics table
    stats_table = doc.add_table(rows=6, cols=2)
    stats_table.style = "Light Grid Accent 1"
    stats_table.cell(0, 0).text = "Metric"
    stats_table.cell(0, 1).text = "Count"
    stats_table.cell(1, 0).text = "P0 (Critical)"
    stats_table.cell(1, 1).text = str(stats.get("p0", 0))
    stats_table.cell(2, 0).text = "P1 (High)"
    stats_table.cell(2, 1).text = str(stats.get("p1", 0))
    stats_table.cell(3, 0).text = "P2 (Medium)"
    stats_table.cell(3, 1).text = str(stats.get("p2", 0))
    stats_table.cell(4, 0).text = "P3 (Low)"
    stats_table.cell(4, 1).text = str(stats.get("p3", 0))
    stats_table.cell(5, 0).text = "Total"
    stats_table.cell(5, 1).text = str(total)
    # Bold the total row
    for cell in stats_table.rows[5].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True

    doc.add_paragraph()
    risk_p = doc.add_paragraph()
    risk_p.add_run("Risk Level: ").bold = True
    risk_p.add_run(f"{exec_summary.get('risk_level', 'N/A')} - {exec_summary.get('risk_justification', '')}")

    doc.add_heading("Critical Fixes", level=2)
    add_markdown_paragraph(doc, exec_summary.get("critical_fixes", "No critical fixes identified."))

    doc.add_heading("Functional Groupings", level=2)
    add_markdown_paragraph(doc, exec_summary.get("functional_groupings", "N/A"))

    doc.add_heading("Redundancy & Trimming", level=2)
    add_markdown_paragraph(doc, _build_redundancy_section(exec_summary.get("redundancy_trimming")))

    doc.add_heading("Roadmap Perspective", level=2)
    doc.add_heading("Short-term (minimal effort, high value)", level=3)
    add_markdown_paragraph(doc, exec_summary.get("roadmap", {}).get("short_term", "N/A"))
    doc.add_heading("Long-term (significant development required)", level=3)
    add_markdown_paragraph(doc, exec_summary.get("roadmap", {}).get("long_term", "N/A"))

    # --- Section 3: Detailed Report ---
    doc.add_page_break()
    doc.add_heading("Section 3: Detailed Report", level=1)

    # Phase 1: By Feature
    doc.add_heading("Phase 1: Grouped by Feature/Functionality", level=2)

    for group in data.get("feature_groups", []):
        group_name = group.get("name", "Unknown")
        finding_count = group.get("finding_count", len(group.get("findings", [])))
        doc.add_heading(f"{group_name} ({finding_count} findings)", level=3)
        add_markdown_paragraph(doc, group.get("summary", ""))

        for finding in group.get("findings", []):
            doc.add_heading(f"{finding.get('id', '')}. {finding.get('title', '')}", level=4)

            meta = doc.add_paragraph()
            meta.add_run("Severity: ").bold = True
            meta.add_run(f"{finding.get('severity', '')}\n")
            meta.add_run("File: ").bold = True
            meta.add_run(f"{finding.get('file', '')}:{finding.get('line', '')}\n")
            meta.add_run("Category: ").bold = True
            meta.add_run(f"{finding.get('category', '')}\n")
            meta.add_run("Effort: ").bold = True
            meta.add_run(finding.get("effort", ""))

            issue_p = doc.add_paragraph()
            issue_p.add_run("Issue: ").bold = True
            issue_p.add_run(finding.get("description", ""))

            impact_p = doc.add_paragraph()
            impact_p.add_run("Impact: ").bold = True
            impact_p.add_run(finding.get("impact", ""))

            fix_p = doc.add_paragraph()
            fix_p.add_run("Fix: ").bold = True
            fix_p.add_run(finding.get("fix", ""))

    # Phase 2: By Priority
    doc.add_page_break()
    doc.add_heading("Phase 2: Grouped by Priority", level=2)

    priority_labels = [
        ("p0", "P0 - Critical (must fix)"),
        ("p1", "P1 - High (should fix)"),
        ("p2", "P2 - Medium (recommended)"),
        ("p3", "P3 - Low (optional)")
    ]

    for pkey, plabel in priority_labels:
        doc.add_heading(plabel, level=3)

        findings = data.get("priority_findings", {}).get(pkey, [])
        if not findings:
            findings = []
            for group in data.get("feature_groups", []):
                for f in group.get("findings", []):
                    if f.get("severity", "").upper() == pkey.upper():
                        f_copy = dict(f)
                        f_copy["feature_group"] = group.get("name", "")
                        findings.append(f_copy)

        if findings:
            cols = 6
            tbl = doc.add_table(rows=1 + len(findings), cols=cols)
            tbl.style = "Light Grid Accent 1"
            headers = ["#", "Title", "Feature Group", "File", "Impact", "Fix"]
            for i, h in enumerate(headers):
                tbl.cell(0, i).text = h
                for paragraph in tbl.cell(0, i).paragraphs:
                    for run in paragraph.runs:
                        run.bold = True

            for row_idx, f in enumerate(findings, 1):
                tbl.cell(row_idx, 0).text = str(row_idx)
                tbl.cell(row_idx, 1).text = f.get("title", "")
                tbl.cell(row_idx, 2).text = f.get("feature_group", "")
                tbl.cell(row_idx, 3).text = f"{f.get('file', '')}:{f.get('line', '')}"
                tbl.cell(row_idx, 4).text = f.get("impact", "")
                tbl.cell(row_idx, 5).text = f.get("fix", "")
        else:
            doc.add_paragraph("No findings at this severity level.")

    # Removal plan
    removal = data.get("removal_plan", "")
    if removal:
        doc.add_page_break()
        doc.add_heading("Removal/Iteration Plan", level=1)
        add_markdown_paragraph(doc, removal)

    # Methodology
    doc.add_heading("Methodology", level=1)
    doc.add_paragraph(data.get("methodology", "6-phase code review"))

    # Appendix
    doc.add_page_break()
    doc.add_heading("Appendix: Project Architecture", level=1)
    p = doc.add_paragraph(tree_structure)
    try:
        p.style = doc.styles['Normal']
    except:
        pass
    if p.runs:
        p.runs[0].font.name = 'Courier New'
        p.runs[0].font.size = Pt(9)

    doc.save(output_file)
    print(f"Generated Code Review DOCX: {output_file}")

    update_toc_via_word(output_file)


# --- Generic Word Report Generators ---

def _read_markdown_files(md_files):
    """Reads and concatenates multiple Markdown files, separated by page-break markers."""
    sections = []
    for md_path in md_files:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if content:
            sections.append(content)
    return sections


def _parse_markdown_title(content):
    """Extracts the first H1 heading from Markdown content as the document title."""
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            return stripped[2:].strip()
    return None


def generate_generic_markdown_report(md_files, title, subtitle, output_file):
    """Combines multiple Markdown files into a single structured Markdown report."""
    author = resolve_author(None)
    date_str = datetime.now().strftime("%Y-%m-%d")
    sections = _read_markdown_files(md_files)

    md_content = f"""# {title}

**Subtitle**: {subtitle}
**Author**: {author}
**Date**: {date_str}

---

"""
    for i, section in enumerate(sections):
        md_content += section
        if i < len(sections) - 1:
            md_content += "\n\n---\n\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Generated Markdown: {output_file}")


def generate_generic_docx_report(md_files, title, subtitle, output_file, template_path=None):
    """
    Generates a Word document from one or more Markdown files.

    If template_path is provided and points to a valid .docx, opens it as the
    document base (inheriting styles, fonts, color schemes). Otherwise creates
    a blank document with the standard DevAI-Hub formatting.
    """
    author = resolve_author(None)
    header_subtitle = subtitle if subtitle else title
    sections = _read_markdown_files(md_files)
    combined_content = "\n\n".join(sections)

    # Auto-detect title from content if not provided
    if not title or title == "Report":
        detected = _parse_markdown_title(combined_content)
        if detected:
            title = detected

    # Open template or create blank document
    if template_path and os.path.exists(template_path):
        doc = Document(template_path)
        # Clear placeholder content from template body (preserve styles)
        for para in list(doc.paragraphs):
            element = para._element
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
        # Clear any tables that may exist in template body
        for table in list(doc.tables):
            element = table._element
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
    else:
        doc = Document()

    # --- Section 0: Title Page ---
    section0 = doc.sections[0]
    section0.left_margin = Inches(1)
    section0.right_margin = Inches(1)
    section0.top_margin = Inches(1)
    section0.bottom_margin = Inches(1)
    section0.vertical_alignment = WD_ALIGN_VERTICAL_TOP

    # Buffer lines for visual centering
    for _ in range(8):
        doc.add_paragraph()

    title_p = doc.add_heading(title, 0)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if subtitle:
        subtitle_p = doc.add_paragraph(subtitle)
        subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_p.runs[0].italic = True

    doc.add_paragraph()

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_p.add_run(f"Author: {author}\n")
    meta_p.add_run(f"Date: {datetime.now().strftime('%B %d, %Y')}")

    # --- Section 1: Main Content ---
    doc.add_section(WD_SECTION.NEW_PAGE)
    section1 = doc.sections[-1]
    section1.vertical_alignment = WD_ALIGN_VERTICAL_TOP
    section1.left_margin = Inches(1)
    section1.right_margin = Inches(1)
    section1.top_margin = Inches(1)
    section1.bottom_margin = Inches(1)

    # Header
    header = section1.header
    header.is_linked_to_previous = False
    for p in header.paragraphs:
        element = p._element
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    htable = header.add_table(rows=1, cols=2, width=Inches(7.5))
    htable.alignment = WD_TABLE_ALIGNMENT.CENTER
    htable.autofit = False
    htable.columns[0].width = Inches(3.75)
    htable.columns[1].width = Inches(3.75)

    cell_h_left = htable.cell(0, 0)
    p_h_left = cell_h_left.paragraphs[0]
    p_h_left.text = title
    p_h_left.alignment = WD_ALIGN_PARAGRAPH.LEFT

    cell_h_right = htable.cell(0, 1)
    p_h_right = cell_h_right.paragraphs[0]
    p_h_right.text = header_subtitle
    p_h_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Footer
    footer = section1.footer
    footer.is_linked_to_previous = False
    for p in footer.paragraphs:
        element = p._element
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    ftable = footer.add_table(rows=1, cols=2, width=Inches(7.5))
    ftable.alignment = WD_TABLE_ALIGNMENT.CENTER
    ftable.autofit = False
    ftable.columns[0].width = Inches(3.75)
    ftable.columns[1].width = Inches(3.75)

    cell_f_left = ftable.cell(0, 0)
    p_f_left = cell_f_left.paragraphs[0]
    p_f_left.text = author
    p_f_left.alignment = WD_ALIGN_PARAGRAPH.LEFT

    cell_f_right = ftable.cell(0, 1)
    p_f_right = cell_f_right.paragraphs[0]
    p_f_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_page_number(p_f_right)

    # Table of Contents
    doc.add_heading("Table of Contents", level=1)
    add_toc(doc)
    doc.add_page_break()

    # --- Render Markdown Content ---
    add_markdown_paragraph(doc, combined_content)

    doc.save(output_file)
    print(f"Generated DOCX: {output_file}")

    update_toc_via_word(output_file)


# --- Generic PowerPoint Report Generators ---

def _split_markdown_into_slides(content):
    """
    Parses Markdown content into a slide-oriented structure.

    Returns a list of slide dicts:
    [
        {"type": "title", "title": "...", "subtitle": "..."},
        {"type": "section", "title": "..."},
        {"type": "content", "title": "...", "body": "..."},
    ]
    """
    slides = []
    current_slide = None
    body_lines = []

    def flush_current():
        nonlocal current_slide, body_lines
        if current_slide:
            if current_slide["type"] == "content":
                current_slide["body"] = "\n".join(body_lines).strip()
            slides.append(current_slide)
            current_slide = None
            body_lines = []

    lines = content.split('\n')
    title_found = False

    for line in lines:
        stripped = line.strip()

        # Skip YAML frontmatter
        if stripped == '---' and not title_found and not slides:
            continue

        # H1: Title slide (first) or Section divider (subsequent)
        if stripped.startswith('# ') and not stripped.startswith('## '):
            flush_current()
            heading = stripped[2:].strip()
            if not title_found:
                title_found = True
                current_slide = {"type": "title", "title": heading, "subtitle": ""}
            else:
                current_slide = {"type": "section", "title": heading}
            continue

        # H2: Content slide
        if stripped.startswith('## ') and not stripped.startswith('### '):
            flush_current()
            heading = stripped[3:].strip()
            current_slide = {"type": "content", "title": heading, "body": ""}
            body_lines = []
            continue

        # H3+: Sub-heading within a content slide
        if stripped.startswith('### '):
            heading = stripped.lstrip('#').strip()
            body_lines.append(f"\n{heading}")
            continue

        # Everything else: body content for current slide
        if current_slide and current_slide["type"] in ("content",):
            body_lines.append(line)
        elif current_slide and current_slide["type"] == "title" and stripped:
            # Capture subtitle-like content after the title
            if stripped.startswith('**') and 'Subtitle' in stripped:
                current_slide["subtitle"] = stripped.replace('**Subtitle**:', '').replace('**', '').strip()

    flush_current()
    return slides


def _add_pptx_bullet_text(text_frame, text, level=0, bold=False, font_size=PptxPt(14) if PPTX_AVAILABLE else None):
    """Adds a bullet-point paragraph to a PowerPoint text frame."""
    if not PPTX_AVAILABLE:
        return
    p = text_frame.add_paragraph()
    p.level = level
    p.space_after = PptxPt(4)

    # Handle basic Markdown formatting in the text
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run()
            run.text = part[2:-2]
            run.font.bold = True
            if font_size:
                run.font.size = font_size
        elif part.strip():
            run = p.add_run()
            run.text = part
            run.font.bold = bold
            if font_size:
                run.font.size = font_size


def _add_pptx_code_block(slide, code_text, left=None, top=None, width=None, height=None):
    """Adds a monospace code block as a text box to a PowerPoint slide."""
    if not PPTX_AVAILABLE:
        return

    left = left or PptxInches(0.5)
    top = top or PptxInches(2.0)
    width = width or PptxInches(9.0)
    height = height or PptxInches(4.5)

    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True

    # Style the text box with a light gray background
    fill = txBox.shape.fill
    fill.solid()
    fill.fore_color.rgb = PptxRGBColor(0xF5, 0xF5, 0xF5)

    p = tf.paragraphs[0]
    p.text = code_text
    p.font.name = 'Courier New'
    p.font.size = PptxPt(10)
    p.font.color.rgb = PptxRGBColor(0x33, 0x33, 0x33)


def generate_generic_pptx_report(md_files, title, subtitle, output_file, template_path=None):
    """
    Generates a PowerPoint presentation from one or more Markdown files.

    H1 headings become section divider slides, H2 headings become content slides.
    If template_path is provided, the template's slide layouts are reused.
    """
    if not PPTX_AVAILABLE:
        print("Error: python-pptx not installed. Please run: pip install python-pptx")
        sys.exit(1)

    author = resolve_author(None)
    sections = _read_markdown_files(md_files)
    combined_content = "\n\n".join(sections)

    # Auto-detect title from content if not provided
    if not title or title == "Report":
        detected = _parse_markdown_title(combined_content)
        if detected:
            title = detected

    # Open template or create blank presentation
    if template_path and os.path.exists(template_path):
        prs = Presentation(template_path)
    else:
        prs = Presentation()

    # Set slide dimensions to widescreen 16:9
    prs.slide_width = PptxInches(13.333)
    prs.slide_height = PptxInches(7.5)

    # Discover available layouts
    slide_layouts = prs.slide_layouts
    layout_title = slide_layouts[0]        # Title Slide
    layout_section = slide_layouts[2] if len(slide_layouts) > 2 else slide_layouts[0]  # Section Header
    layout_content = slide_layouts[1] if len(slide_layouts) > 1 else slide_layouts[0]  # Title and Content
    layout_blank = slide_layouts[6] if len(slide_layouts) > 6 else slide_layouts[-1]   # Blank

    # Parse content into slide structure
    slide_data = _split_markdown_into_slides(combined_content)

    # If no slides were parsed, create a simple title + content structure
    if not slide_data:
        slide_data = [
            {"type": "title", "title": title, "subtitle": subtitle or ""},
            {"type": "content", "title": "Content", "body": combined_content}
        ]

    for sd in slide_data:
        if sd["type"] == "title":
            slide = prs.slides.add_slide(layout_title)
            # Set title
            if slide.shapes.title:
                slide.shapes.title.text = sd["title"]
            # Set subtitle
            for shape in slide.placeholders:
                if shape.placeholder_format.idx == 1:  # Subtitle placeholder
                    shape.text = sd.get("subtitle", subtitle or "")
                    if shape.text_frame.paragraphs:
                        p = shape.text_frame.paragraphs[0]
                        run = p.add_run()
                        run.text = f"\n{author} | {datetime.now().strftime('%B %d, %Y')}"
                        run.font.size = PptxPt(14)
                        run.font.color.rgb = PptxRGBColor(0x88, 0x88, 0x88)
                    break

        elif sd["type"] == "section":
            slide = prs.slides.add_slide(layout_section)
            if slide.shapes.title:
                slide.shapes.title.text = sd["title"]

        elif sd["type"] == "content":
            body_text = sd.get("body", "")

            # Check if the body is primarily a code block
            stripped_body = body_text.strip()
            if stripped_body.startswith("```") and stripped_body.endswith("```"):
                # Render as a code slide
                slide = prs.slides.add_slide(layout_blank)
                # Add title as a text box
                txBox = slide.shapes.add_textbox(PptxInches(0.5), PptxInches(0.3), PptxInches(9.0), PptxInches(0.8))
                tf = txBox.text_frame
                p = tf.paragraphs[0]
                p.text = sd["title"]
                p.font.size = PptxPt(24)
                p.font.bold = True
                # Add code block
                code_lines = stripped_body.split('\n')
                # Remove opening and closing ``` lines
                code_lines = [l for l in code_lines if not l.strip().startswith('```')]
                _add_pptx_code_block(slide, "\n".join(code_lines))
                continue

            # Regular content slide
            slide = prs.slides.add_slide(layout_content)
            if slide.shapes.title:
                slide.shapes.title.text = sd["title"]

            # Find the body placeholder
            body_shape = None
            for shape in slide.placeholders:
                if shape.placeholder_format.idx == 1:  # Body placeholder
                    body_shape = shape
                    break

            if body_shape and body_shape.has_text_frame:
                tf = body_shape.text_frame
                tf.clear()

                # Parse body content into the text frame
                in_code_block = False
                code_lines = []
                first_para = True

                for line in body_text.split('\n'):
                    stripped = line.strip()

                    # Toggle code blocks
                    if stripped.startswith("```"):
                        if in_code_block:
                            # End code block: add collected lines
                            for cl in code_lines:
                                _add_pptx_bullet_text(tf, cl, level=1,
                                                       font_size=PptxPt(10))
                            code_lines = []
                        in_code_block = not in_code_block
                        continue

                    if in_code_block:
                        code_lines.append(line)
                        continue

                    # Skip empty lines
                    if not stripped:
                        continue

                    # Bullet points
                    if stripped.startswith("- ") or stripped.startswith("* "):
                        content_text = stripped[2:]
                        _add_pptx_bullet_text(tf, content_text, level=0,
                                               font_size=PptxPt(14))
                    elif stripped.startswith("  - ") or stripped.startswith("  * "):
                        content_text = stripped.strip()[2:]
                        _add_pptx_bullet_text(tf, content_text, level=1,
                                               font_size=PptxPt(12))
                    elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1:3] in ['. ', ') ']:
                        content_text = stripped.split(' ', 1)[1] if ' ' in stripped else stripped
                        _add_pptx_bullet_text(tf, content_text, level=0,
                                               font_size=PptxPt(14))
                    elif stripped.startswith('### ') or stripped.startswith('#### '):
                        heading_text = stripped.lstrip('#').strip()
                        _add_pptx_bullet_text(tf, heading_text, level=0, bold=True,
                                               font_size=PptxPt(16))
                    else:
                        # Regular text paragraph
                        _add_pptx_bullet_text(tf, stripped, level=0,
                                               font_size=PptxPt(14))
            else:
                # No body placeholder found; use a text box
                txBox = slide.shapes.add_textbox(
                    PptxInches(0.5), PptxInches(1.5),
                    PptxInches(9.0), PptxInches(5.5)
                )
                tf = txBox.text_frame
                tf.word_wrap = True
                for line in body_text.split('\n'):
                    stripped = line.strip()
                    if stripped:
                        _add_pptx_bullet_text(tf, stripped, level=0,
                                               font_size=PptxPt(14))

    prs.save(output_file)
    print(f"Generated PPTX: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate reports from JSON data or Markdown files.")
    parser.add_argument("json_file", nargs='?', default=None,
                        help="Path to JSON data file (required for codebase/code-review types)")
    parser.add_argument("--type", dest="report_type", default="codebase",
                        choices=["codebase", "code-review", "generic-word", "generic-pptx"],
                        help="Report type: 'codebase' (default), 'code-review', 'generic-word', or 'generic-pptx'")
    parser.add_argument("--md-files", nargs='+', default=None,
                        help="Markdown file(s) to include (for generic-word/generic-pptx types)")
    parser.add_argument("--title", default="Report",
                        help="Document title (for generic types)")
    parser.add_argument("--subtitle", default="",
                        help="Document subtitle (for generic types)")
    parser.add_argument("--template", default=None,
                        help="Path to .docx or .pptx template file")
    parser.add_argument("--output", default=None,
                        help="Output file path")

    args = parser.parse_args()

    if args.report_type in ("generic-word", "generic-pptx"):
        # Generic report mode: requires --md-files
        if not args.md_files:
            parser.error("--md-files is required for generic-word and generic-pptx report types")

        # Validate all markdown files exist
        for md_file in args.md_files:
            if not os.path.exists(md_file):
                parser.error(f"Markdown file not found: {md_file}")

        if args.report_type == "generic-word":
            output_docx = args.output or "Report.docx"
            output_md = os.path.splitext(output_docx)[0] + ".md"

            generate_generic_markdown_report(args.md_files, args.title, args.subtitle, output_md)
            generate_generic_docx_report(args.md_files, args.title, args.subtitle,
                                         output_docx, template_path=args.template)

        elif args.report_type == "generic-pptx":
            output_pptx = args.output or "Report.pptx"
            generate_generic_pptx_report(args.md_files, args.title, args.subtitle,
                                          output_pptx, template_path=args.template)
    else:
        # JSON-based report mode (original behavior)
        if not args.json_file:
            parser.error("json_file is required for codebase and code-review report types")

        with open(args.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        author = resolve_author(data.get("author"))

        root_dir = os.getcwd()
        tree_str = f"{os.path.basename(root_dir)}/\n{generate_tree_structure(root_dir)}"

        if args.report_type == "code-review":
            generate_code_review_markdown(data, author, tree_str)
            generate_code_review_docx(data, author, tree_str)
        else:
            generate_markdown_report(data, author, tree_str)
            generate_docx_report(data, author, tree_str)
