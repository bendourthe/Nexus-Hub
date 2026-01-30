
import json
import sys
import os
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    print("Error: python-docx not installed. Please run: pip install python-docx")
    sys.exit(1)

def create_report(data, output_file="Codebase_Report.docx"):
    doc = Document()
    
    # Title Page
    title = data.get("title", "Codebase Deep Dive Report")
    subtitle = data.get("subtitle", "Comprehensive Analysis & Documentation")
    author = data.get("author", "DevAI-Hub Agent")
    date_str = datetime.now().strftime("%B %d, %Y")

    doc.add_heading(title, 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(subtitle).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"\n\n\n\nAuthor: {author}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Date: {date_str}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    # Purpose Section
    doc.add_heading("1. Document Purpose", level=1)
    purpose = data.get("purpose", "This document provides a detailed analysis of the codebase, outlining its architecture, components, and usage.")
    doc.add_paragraph(purpose)

    # Executive Summary
    doc.add_heading("2. Executive Summary", level=1)
    summary = data.get("executive_summary", "No summary provided.")
    doc.add_paragraph(summary)

    # Table of Contents (Placeholder - Word generates real TOCs best, but we can list sections)
    # doc.add_heading("Table of Contents", level=1)
    # doc.add_paragraph("1. Document Purpose\n2. Executive Summary\n3. Component Analysis\n4. User Manual")
    # doc.add_page_break()

    # Component Analysis
    doc.add_heading("3. Component Analysis", level=1)
    components = data.get("components", [])
    if not components:
        doc.add_paragraph("No component details provided.")
    
    for comp in components:
        name = comp.get("name", "Unnamed Component")
        desc = comp.get("description", "")
        details = comp.get("details", "")
        
        doc.add_heading(name, level=2)
        if desc:
            p = doc.add_paragraph()
            runner = p.add_run("Description: ")
            runner.bold = True
            p.add_run(desc)
        
        if details:
            doc.add_paragraph(details)

    # User Manual / Usage Guide
    doc.add_heading("4. User Manual & Usage Guide", level=1)
    manual = data.get("user_manual", "")
    if manual:
        doc.add_paragraph(manual)
    else:
        doc.add_paragraph("No specific usage instructions provided.")

    # Issues & Optimization
    doc.add_heading("5. Issues & Optimization", level=1)
    issues = data.get("issues", [])
    if issues:
        for issue in issues:
            doc.add_paragraph(f"- {issue}", style='List Bullet')
    else:
        doc.add_paragraph("No major issues identified.")

    # Save
    try:
        doc.save(output_file)
        print(f"Successfully generated report: {output_file}")
    except Exception as e:
        print(f"Error saving document: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Read from stdin if no file provided
        if not sys.stdin.isatty():
             try:
                data = json.load(sys.stdin)
             except json.JSONDecodeError:
                print("Error: Invalid JSON input from stdin.")
                sys.exit(1)
        else:
            print("Usage: python generate_report.py <input.json>")
            sys.exit(1)
            
    create_report(data)
