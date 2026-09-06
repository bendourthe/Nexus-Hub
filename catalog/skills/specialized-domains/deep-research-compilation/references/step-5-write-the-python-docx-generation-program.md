## Step 5: Write the Python-Docx Generation Program

This is the heart of the skill. You author `<cache_dir>/generate.py` per invocation, adapted to the style profile from Step 1 and the merged markdown from Step 3. Save it, then run it via Bash. The generator writes its output to `<final_dir>/<ReportTitle>.docx`.

### Proven OOXML patterns (copy-adapt these; do not reinvent)

#### A. Open the template and clear the body while preserving sectPr

```python
import docx
from docx.oxml.ns import qn

def clear_body(doc):
    body = doc.element.body
    sectpr_found = False
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            sectpr_found = True
        else:
            body.remove(child)
    assert sectpr_found, "Template missing sectPr -- invalid template"

doc = docx.Document(template_path)
clear_body(doc)
doc.core_properties.title = title
doc.core_properties.author = author
doc.core_properties.last_modified_by = author
doc.core_properties.subject = subtitle
```

#### B. Apply a paragraph style by writing `<w:pStyle>` directly (critical)

**Do not** use `paragraph.style = doc.styles["Heading 1"]`. On a freshly-loaded template with an empty body, python-docx's style collection often does not expose template-defined styles, and the assignment silently falls back to Normal. Write the XML directly:

```python
from docx.oxml import OxmlElement

_STYLE_ID = {
    "Title": "Title", "Subtitle": "Subtitle",
    "Heading 1": "Heading1", "Heading 2": "Heading2",
    "Heading 3": "Heading3", "Heading 4": "Heading4",
    "Normal": "Normal", "Hyperlink": "Hyperlink",
    "Table Grid": "TableGrid", "List Paragraph": "ListParagraph",
    "TOC Heading": "TOCHeading",
}

def apply_style(paragraph, style_name):
    style_id = _STYLE_ID.get(style_name, style_name.replace(" ", ""))
    p = paragraph._p
    pPr = p.find(qn("w:pPr")) or OxmlElement("w:pPr")
    if pPr.getparent() is None:
        p.insert(0, pPr)
    for existing in pPr.findall(qn("w:pStyle")):
        pPr.remove(existing)
    el = OxmlElement("w:pStyle")
    el.set(qn("w:val"), style_id)
    pPr.insert(0, el)

def apply_table_style(table, style_name):
    style_id = _STYLE_ID.get(style_name, style_name.replace(" ", ""))
    tblPr = table._tbl.tblPr
    for existing in tblPr.findall(qn("w:tblStyle")):
        tblPr.remove(existing)
    el = OxmlElement("w:tblStyle")
    el.set(qn("w:val"), style_id)
    tblPr.insert(0, el)
```

#### C. Run builder with direct XML properties

```python
def add_run(paragraph, text, *, bold=False, italic=False, font=None,
            size_half_pt=None, color_hex=None, superscript=False,
            underline=False, rstyle=None):
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    if rstyle:
        el = OxmlElement("w:rStyle"); el.set(qn("w:val"), rstyle); rPr.append(el)
    if bold:   rPr.append(OxmlElement("w:b"))
    if italic: rPr.append(OxmlElement("w:i"))
    if font:
        el = OxmlElement("w:rFonts")
        for a in ("w:ascii","w:hAnsi","w:cs"):
            el.set(qn(a), font)
        rPr.append(el)
    if size_half_pt is not None:
        for tag in ("w:sz","w:szCs"):
            el = OxmlElement(tag); el.set(qn("w:val"), str(size_half_pt)); rPr.append(el)
    if color_hex:
        el = OxmlElement("w:color"); el.set(qn("w:val"), color_hex); rPr.append(el)
    if underline:
        el = OxmlElement("w:u"); el.set(qn("w:val"), "single"); rPr.append(el)
    if superscript:
        el = OxmlElement("w:vertAlign"); el.set(qn("w:val"), "superscript"); rPr.append(el)
    if len(rPr):
        r.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    paragraph._p.append(r)
    return r
```

#### D. Internal hyperlink (for citations: target = bookmark `_RefN`)

```python
def add_internal_link(paragraph, anchor, text, *, color_hex, superscript=True, size_half_pt=18):
    hyp = OxmlElement("w:hyperlink")
    hyp.set(qn("w:anchor"), anchor)
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    for tag, attr in [("w:rStyle","Hyperlink")]:
        el = OxmlElement(tag); el.set(qn("w:val"), attr); rPr.append(el)
    el = OxmlElement("w:color"); el.set(qn("w:val"), color_hex); rPr.append(el)
    el = OxmlElement("w:u"); el.set(qn("w:val"), "single"); rPr.append(el)
    for tag in ("w:sz","w:szCs"):
        el = OxmlElement(tag); el.set(qn("w:val"), str(size_half_pt)); rPr.append(el)
    if superscript:
        el = OxmlElement("w:vertAlign"); el.set(qn("w:val"), "superscript"); rPr.append(el)
    r.append(rPr)
    t = OxmlElement("w:t"); t.text = text; r.append(t)
    hyp.append(r)
    paragraph._p.append(hyp)
```

#### E. External hyperlink (for reference URLs)

```python
from docx.opc.constants import RELATIONSHIP_TYPE as RT

def add_external_link(paragraph, url, text, *, color_hex, size_half_pt=None, underline=True):
    rId = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyp = OxmlElement("w:hyperlink"); hyp.set(qn("r:id"), rId)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    el = OxmlElement("w:rStyle"); el.set(qn("w:val"), "Hyperlink"); rPr.append(el)
    el = OxmlElement("w:color"); el.set(qn("w:val"), color_hex); rPr.append(el)
    if underline:
        el = OxmlElement("w:u"); el.set(qn("w:val"), "single"); rPr.append(el)
    if size_half_pt is not None:
        for tag in ("w:sz","w:szCs"):
            el = OxmlElement(tag); el.set(qn("w:val"), str(size_half_pt)); rPr.append(el)
    r.append(rPr)
    t = OxmlElement("w:t"); t.text = text; r.append(t)
    hyp.append(r); paragraph._p.append(hyp)
```

#### F. Bookmark wrapping a paragraph

```python
def add_bookmark(paragraph, name, bookmark_id):
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bookmark_id))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd"); end.set(qn("w:id"), str(bookmark_id))
    paragraph._p.insert(0, start)
    paragraph._p.append(end)
```

Use a single monotonic counter for bookmark IDs across the whole document.

#### G. Settings: make TOC refresh on open

```python
def set_update_fields(doc):
    settings = doc.settings.element
    existing = settings.find(qn("w:updateFields"))
    if existing is None:
        el = OxmlElement("w:updateFields"); el.set(qn("w:val"), "true")
        settings.append(el)
    else:
        existing.set(qn("w:val"), "true")
```

#### H. TOC as an SDT + field code

```python
def insert_toc(doc):
    p_h = doc.add_paragraph()
    apply_style(p_h, "TOC Heading")
    add_run(p_h, "Table of Contents")

    p = doc.add_paragraph()
    # field begin
    r = OxmlElement("w:r"); el = OxmlElement("w:fldChar")
    el.set(qn("w:fldCharType"), "begin"); el.set(qn("w:dirty"), "true")
    r.append(el); p._p.append(r)
    # instruction
    r = OxmlElement("w:r"); el = OxmlElement("w:instrText")
    el.set(qn("xml:space"), "preserve"); el.text = 'TOC \\o "1-3" \\h \\z \\u'
    r.append(el); p._p.append(r)
    # separator
    r = OxmlElement("w:r"); el = OxmlElement("w:fldChar")
    el.set(qn("w:fldCharType"), "separate"); r.append(el); p._p.append(r)
    # placeholder text shown before F9/auto-refresh
    r = OxmlElement("w:r"); t = OxmlElement("w:t")
    t.text = "Right-click and select Update Field to refresh the Table of Contents."
    r.append(t); p._p.append(r)
    # field end
    r = OxmlElement("w:r"); el = OxmlElement("w:fldChar")
    el.set(qn("w:fldCharType"), "end"); r.append(el); p._p.append(r)
```

#### I. Title page (driven by the style profile, not hardcoded values)

```python
def emit_title_page(doc, profile, title, subtitle, date):
    # leading blank Title paragraphs for the style's border-rule rhythm
    for _ in range(2):
        p = doc.add_paragraph(); apply_style(p, "Title")
        p.alignment = 1  # center

    p = doc.add_paragraph(); apply_style(p, "Title"); p.alignment = 1
    tp = profile["title"]
    add_run(p, title,
            font=tp["font"],
            size_half_pt=int(tp["size_pt"]*2),
            color_hex=tp["color"].lstrip("#"))

    if subtitle:
        for _ in range(2):
            p = doc.add_paragraph(); apply_style(p, "Subtitle"); p.alignment = 1
        p = doc.add_paragraph(); apply_style(p, "Subtitle"); p.alignment = 1
        sp = profile["subtitle"]
        add_run(p, subtitle,
                font=sp["font"],
                size_half_pt=int(sp["size_pt"]*2),
                color_hex=sp["color"].lstrip("#"))

    for _ in range(3):
        p = doc.add_paragraph(); apply_style(p, "Subtitle"); p.alignment = 1

    if date:
        p = doc.add_paragraph(); apply_style(p, "Subtitle"); p.alignment = 1
        # date is typically smaller + gray; if profile doesn't carry explicit
        # date styling, derive: 18 pt, #808080
        add_run(p, date,
                font=profile["subtitle"]["font"],
                size_half_pt=36, color_hex="808080", italic=True)

    # Hard page break to start the body on page 2
    p = doc.add_paragraph()
    r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page")
    r.append(br); p._p.append(r)
```

Note: every value (font, size, color) comes from `profile`. A different template with a red/black corporate look produces `profile["title"] = {"font": "Arial Black", "size_pt": 44, "color": "#CC0000", ...}` and the generated `.docx` matches that.

#### J. Metadata table with borderless outer + light-gray row rules

```python
from docx.shared import Inches

def emit_metadata_table(doc, profile, author, last_updated):
    table = doc.add_table(rows=2, cols=2)
    apply_table_style(table, "Table Grid")
    mt = profile["metadata_table"]
    table.columns[0].width = Inches(mt["col1_in"])
    table.columns[1].width = Inches(mt["col2_in"])

    tblPr = table._tbl.tblPr
    for existing in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(existing)
    borders = OxmlElement("w:tblBorders")
    specs = [
        ("w:top",    "single", "4", "808080"),
        ("w:left",   "nil",    None, None),
        ("w:bottom", "single", "4", "808080"),
        ("w:right",  "nil",    None, None),
        ("w:insideH","single", "4", mt["border_top_bottom_color"].lstrip("#")),
        ("w:insideV","nil",    None, None),
    ]
    for tag, val, sz, clr in specs:
        el = OxmlElement(tag); el.set(qn("w:val"), val)
        if sz:  el.set(qn("w:sz"), sz)
        if clr: el.set(qn("w:color"), clr)
        borders.append(el)
    tblPr.append(borders)

    rows = [("Authors", author or ""), ("Last Updated", last_updated or "")]
    for i, (label, value) in enumerate(rows):
        lp = table.rows[i].cells[0].paragraphs[0]
        add_run(lp, label, bold=True)
        vp = table.rows[i].cells[1].paragraphs[0]
        add_run(vp, value)
```

#### K. Citation run pattern (the 3-run superscript + internal-hyperlink block)

```python
CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

def render_inline(paragraph, text, profile):
    # Minimal tokenizer: extract citations first, then bold/italic/code/link.
    cit_color = profile["citation"]["color_override"].lstrip("#")
    cit_sz = int(profile["citation"]["size_pt"] * 2)

    pos = 0
    for m in CITATION_RE.finditer(text):
        if m.start() > pos:
            _render_runs(paragraph, text[pos:m.start()], profile)  # bold/italic/code/link
        nums = [int(n.strip()) for n in m.group(1).split(",")]
        add_run(paragraph, " [", superscript=True, size_half_pt=cit_sz)
        for i, n in enumerate(nums):
            if i > 0:
                add_run(paragraph, ",", superscript=True, size_half_pt=cit_sz)
            add_internal_link(paragraph, f"_Ref{n}", str(n),
                              color_hex=cit_color, size_half_pt=cit_sz, superscript=True)
        add_run(paragraph, "]", superscript=True, size_half_pt=cit_sz)
        pos = m.end()
    if pos < len(text):
        _render_runs(paragraph, text[pos:], profile)
```

`_render_runs` walks markdown-style inline tokens (`**bold**`, `*italic*`, `` `code` ``, `[link](url)`) and emits a run for each. Citations are stripped first so the markdown-link regex cannot eat a `[N]` by mistake.

#### L. References section (one entry per paragraph with hanging indent, bookmark-wrapped)

```python
def emit_references(doc, canonical, profile):
    h = doc.add_paragraph(); apply_style(h, "Heading 1")
    add_run(h, "References")

    re_style = profile["reference_entry"]
    url_color = re_style["url_color"].lstrip("#")

    for idx, ref in enumerate(canonical, start=1):
        p = doc.add_paragraph(); apply_style(p, "Normal")

        # spacing before/after + hanging indent
        pPr = p._p.find(qn("w:pPr"))
        sp = OxmlElement("w:spacing")
        sp.set(qn("w:before"), str(int(re_style["spacing_before_pt"]*20)))
        sp.set(qn("w:after"),  str(int(re_style["spacing_after_pt"]*20)))
        pPr.append(sp)
        ind = OxmlElement("w:ind")
        twips = int(re_style["hanging_in"] * 1440)
        ind.set(qn("w:left"), str(twips))
        ind.set(qn("w:hanging"), str(twips))
        pPr.append(ind)

        add_bookmark(p, f"_Ref{ref['num']}", bookmark_id=1000 + idx)

        add_run(p, f"[{ref['num']}] ", bold=True,
                size_half_pt=int(re_style["size_pt"]*2))

        text = (ref.get("text") or "").strip()
        url = ref.get("url")
        if url and url in text:
            text = text.replace(url, "").rstrip(" .,;")
        if text:
            add_run(p, text + (" " if url else ""),
                    size_half_pt=int(re_style["size_pt"]*2))
        if url:
            add_external_link(p, url, url,
                              color_hex=url_color,
                              size_half_pt=int(re_style["url_size_pt"]*2))
```

#### M. Saving

```python
doc.save(output_path)
```

No `.close()`. python-docx handles the file lifecycle via the context of save.

### Assembly

The overall generator program body:

```python
def main():
    with open(style_profile_path) as f:
        profile = json.load(f)
    merged = Path(merged_md_path).read_text(encoding="utf-8")
    refs = json.load(open(refs_json_path)) if refs_json_path else {"canonical": []}

    doc = docx.Document(template_path)
    clear_body(doc)
    set_update_fields(doc)
    doc.core_properties.title = title
    doc.core_properties.author = author
    doc.core_properties.last_modified_by = author
    doc.core_properties.subject = subtitle

    emit_title_page(doc, profile, title, subtitle, date)

    # Parse merged markdown into (pre_toc_blocks, main_blocks) on PRE-TOC markers
    pre_toc, main = parse_merged_md(merged)

    # Pre-TOC: Document's Purpose + prose, then metadata table
    for blk in pre_toc: render_block(doc, blk, profile)
    emit_metadata_table(doc, profile, author, last_updated=date)

    # TOC then page break
    insert_toc(doc)
    page_break_paragraph(doc)

    # Body: render every block except any `# References` (we emit from refs.json)
    for blk in strip_references_section(main):
        render_block(doc, blk, profile)

    # Hard page break + References
    if refs.get("canonical"):
        page_break_paragraph(doc)
        emit_references(doc, refs["canonical"], profile)

    doc.save(output_path)
    print(f"Wrote {output_path}")

if __name__ == "__main__":
    main()
```

Save this program to `<cache_dir>/generate.py`, embedding the canonical refs + style profile either as `open(...)` reads against the sibling JSON artifacts (`refs.json`, `style_profile.json`), or inlined as literals for full single-file reproducibility. Either is acceptable. Hard-code the `<final_dir>/<ReportTitle>.docx` output path inside the script so the user can re-run it without re-deriving paths.

### Run the program

```bash
python "<cache_dir>/generate.py"
```

If any import fails, the program prints a clear `pip install <pkg>` hint and exits. Dependencies beyond `python-docx` are lazy-imported inside the per-format parsers so the generator runs with just `python-docx` in the typical case.

---
