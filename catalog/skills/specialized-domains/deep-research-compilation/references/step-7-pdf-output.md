## Step 7: PDF Output

Always via `.docx` -> converter. Do not try to author PDF directly. The PDF output lands at `<final_dir>/<ReportTitle>.pdf`.

```python
def build_pdf(docx_path, pdf_path):
    # Primary: docx2pdf (wraps MS Word on Windows, Word/LibreOffice on macOS)
    try:
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
        if pdf_path.exists():
            return
    except Exception as e:
        print(f"[warn] docx2pdf failed: {e}")

    # Fallback: libreoffice --headless
    import shutil, subprocess
    libre = shutil.which("libreoffice") or shutil.which("soffice")
    if libre:
        try:
            result = subprocess.run(
                [libre, "--headless", "--convert-to", "pdf",
                 "--outdir", str(pdf_path.parent), str(docx_path)],
                timeout=120, capture_output=True, text=True,
            )
            produced = pdf_path.parent / (docx_path.stem + ".pdf")
            if produced.exists():
                if produced != pdf_path:
                    produced.replace(pdf_path)
                return
            print(f"[warn] libreoffice produced no output: {result.stderr}")
        except Exception as e:
            print(f"[warn] libreoffice failed: {e}")

    raise RuntimeError(
        "PDF conversion requires docx2pdf (pip install docx2pdf) or "
        "libreoffice on PATH. Install one and re-run; the .docx is kept for manual export."
    )
```

If only `.pdf` was requested (not `.docx`), delete the intermediate `.docx` after successful conversion. Otherwise keep both.

---
