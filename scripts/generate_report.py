
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

def add_list_item(doc, text):
    """Safe list item addition."""
    try:
        p = doc.add_paragraph(text, style='List Bullet')
    except (KeyError, ValueError):
        p = doc.add_paragraph(f"• {text}")

def add_markdown_paragraph(doc, text, style=None):
    """Parses simple markdown (bold, code, lists) and adds it to the document."""
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
            p = doc.add_paragraph(line)
            try:
                p.style = doc.styles['Normal']
            except: pass
            font = p.runs[0].font
            font.name = 'Courier New'
            font.size = Pt(9)
            continue

        # List Items
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:]
            add_list_item(doc, content)
            continue
        
        if stripped and len(stripped) > 2 and stripped[0].isdigit() and stripped[1:3] in ['. ', ') ']:
             try:
                p = doc.add_paragraph(style='List Number')
             except:
                p = doc.add_paragraph()
             content = stripped.split(' ', 1)[1] if ' ' in stripped else stripped
        else:
            p = doc.add_paragraph(style=style)
            content = line

        # Bold Parsing (**text**)
        parts = re.split(r'(\*\*.*?\*\*)', content)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                code_parts = re.split(r'(`.*?`)', part)
                for cp in code_parts:
                    if cp.startswith('`') and cp.endswith('`'):
                        run = p.add_run(cp[1:-1])
                        run.font.name = 'Courier New'
                    else:
                        p.add_run(cp)

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
4. [Platform Support](#4-platform-support)
5. [User Manual & Usage Guide](#5-user-manual--usage-guide)
6. [Issues & Optimization](#6-issues--optimization)
7. [Appendix A: Project Architecture](#appendix-a-project-architecture)

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
    if isinstance(deps, list):
        for d in deps:
            md_content += f"- {d}\n"
    else:
        md_content += f"{deps}\n"

    md_content += "\n## 4. Platform Support\n"
    platforms = data.get("platforms", [])
    if isinstance(platforms, list):
        for p in platforms:
            md_content += f"- {p}\n"
    else:
        md_content += f"{platforms}\n"

    md_content += f"\n## 5. User Manual & Usage Guide\n{data.get('user_manual', 'N/A')}\n"

    md_content += "\n## 6. Issues & Optimization\n"
    for issue in data.get("issues", []):
        md_content += f"- {issue}\n"

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
        if isinstance(deps, list):
            for d in deps:
                add_list_item(doc, d)
        else:
             add_markdown_paragraph(doc, deps)
    else:
        doc.add_paragraph("No dependencies specified.")

    doc.add_heading("4. Platform Support", level=1)
    platforms = data.get("platforms", [])
    if platforms:
         if isinstance(platforms, list):
            doc.add_paragraph(", ".join(platforms))
         else:
            add_markdown_paragraph(doc, platforms)
    else:
        doc.add_paragraph("No platform info specified.")

    doc.add_heading("5. User Manual & Usage Guide", level=1)
    manual = data.get("user_manual", "")
    if manual:
        add_markdown_paragraph(doc, manual)
    else:
        doc.add_paragraph("No user manual provided.")

    doc.add_heading("6. Issues & Optimization", level=1)
    issues = data.get("issues", [])
    if issues:
        for issue in issues:
            add_list_item(doc, issue)
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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        author = resolve_author(data.get("author"))
        
        root_dir = os.getcwd()
        tree_str = f"{os.path.basename(root_dir)}/\n{generate_tree_structure(root_dir)}"
        
        generate_markdown_report(data, author, tree_str)
        generate_docx_report(data, author, tree_str)
        
    else:
        print("Usage: python generate_report.py <json_file>")
