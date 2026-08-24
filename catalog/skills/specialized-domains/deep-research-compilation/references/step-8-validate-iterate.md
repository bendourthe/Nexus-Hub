## Step 8: Validate + Iterate

After generating the `.docx`, open it via zipfile and run these checks:

```python
def validate_docx(path):
    import zipfile, re
    with zipfile.ZipFile(path) as z:
        doc = z.read("word/document.xml").decode("utf-8")
    anchors = set(re.findall(r'w:hyperlink w:anchor="(_Ref\d+)"', doc))
    bookmarks = set(re.findall(r'w:bookmarkStart[^/]*w:name="(_Ref\d+)"', doc))
    broken = sorted(anchors - bookmarks)
    orphan = sorted(bookmarks - anchors)

    pstyles = set(re.findall(r'w:pStyle w:val="([^"]+)"', doc))
    heading_styles = {s for s in pstyles if s.startswith("Heading") or s == "Title"}
    toc_present = "TOC " in doc and "w:fldChar" in doc

    issues = []
    if broken: issues.append(f"broken citation anchors: {broken}")
    if not heading_styles: issues.append("no heading styles applied -- TOC will be empty")
    if not toc_present: issues.append("TOC field missing")
    if orphan: issues.append(f"orphan bookmarks: {orphan}")  # warning only, not fatal
    return issues
```

For `.md`:

```python
def validate_md(path):
    text = Path(path).read_text(encoding="utf-8")
    anchors_used = set(re.findall(r"\(#(ref\d+)\)", text))
    anchor_defs = set(re.findall(r'<a id="(ref\d+)"', text))
    broken = sorted(anchors_used - anchor_defs)
    return [f"broken anchors: {broken}"] if broken else []
```

If any **fatal** issue is reported (broken citation anchors, missing heading styles, missing TOC field), diagnose:

- Broken anchors: a citation references a number outside the canonical list. Re-check the renumbering map.
- Missing heading styles: you forgot `apply_style()` on a heading -- check `render_block` for the heading branch.
- Missing TOC: `insert_toc()` wasn't called or its XML is malformed.

Edit `<cache_dir>/generate.py` and re-run. Maximum 3 iterations; if still failing, stop and report the failure to the user with the raw issue list.

---
