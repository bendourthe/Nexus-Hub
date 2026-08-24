## Step 1: Inspect the .docx Template

Before synthesizing or generating anything, build a **style profile** of the selected template. Write it to `<cache_dir>/style_profile.json` so the user can review what you extracted.

### Procedure

```python
import json, re, zipfile
from pathlib import Path

TEMPLATE = Path(template_path)
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
from lxml import etree

with zipfile.ZipFile(TEMPLATE) as z:
    styles_xml  = z.read("word/styles.xml")
    theme_xml   = z.read("word/theme/theme1.xml")
    settings_xml = z.read("word/settings.xml")
    numbering_xml = z.read("word/numbering.xml") if "word/numbering.xml" in z.namelist() else None
    header_parts = [n for n in z.namelist() if n.startswith("word/header") and n.endswith(".xml")]
    footer_parts = [n for n in z.namelist() if n.startswith("word/footer") and n.endswith(".xml")]

styles_root = etree.fromstring(styles_xml)
```

### Styles to extract

For each of these `w:styleId`s in `styles.xml`, pull the resolved run + paragraph properties (font family, size in half-points, color hex, bold/italic, smallCaps, alignment, spacing before/after, line spacing, left/right indent, borders):

- `Title`, `Subtitle`
- `Heading1`, `Heading2`, `Heading3`, `Heading4`
- `Normal`, `ListParagraph`, `ListBullet`, `ListNumber`
- `Hyperlink`, `FollowedHyperlink`
- `TableGrid`
- `TOCHeading`, `TOC1`, `TOC2`, `TOC3`
- `Header`, `Footer`

Helper:

```python
def style_rpr(styles_root, style_id):
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    for s in styles_root.iter(f"{w}style"):
        if s.get(f"{w}styleId") == style_id:
            rpr = s.find(f"{w}rPr")
            ppr = s.find(f"{w}pPr")
            return rpr, ppr
    return None, None
```

Extract `rFonts@w:ascii`, `sz@w:val` (half-points), `color@w:val`, `b`, `i`, `smallCaps`, `u@w:val`; for paragraph: `jc@w:val`, `spacing@w:before/after/line`, `ind@w:left/right/hanging`, `pBdr>bottom/top@w:val/sz/color`. Treat missing values as inherited from the base style (follow `basedOn`).

### Header/footer detection

For each `word/header*.xml` and `word/footer*.xml`, capture: is it empty? does it have a `<w:pBdr>`? what are the three tab stops (left / center / right)? Does it reference `dc:title` or `dc:creator` via an `<w:sdt>` data-binding? This determines whether you need to populate header/footer text or rely on core-properties auto-population.

### Theme colors

Read `a:clrScheme` from `theme1.xml` to resolve any `w:themeColor="accentN"` references you see in styles.xml.

### Example style profile (what good output looks like)

```json
{
  "template": "branded-report-template.docx",
  "title": {"font": "Consolas", "size_pt": 32, "color": "#215868", "smallCaps": true, "align": "center", "border_bottom": {"sz_pt": 2.25, "color": "#244061"}},
  "subtitle": {"font": "Consolas", "size_pt": 26, "color": "#31849B", "smallCaps": true, "align": "center"},
  "heading1": {"font": "Calibri Light", "size_pt": 22, "color": "#215868", "bold": true, "smallCaps": true, "spacing_before_pt": 18, "spacing_after_pt": 12, "border_bottom": {"sz_pt": 1, "color": "#215868"}},
  "heading2": {"font": "Calibri Light", "size_pt": 16, "color": "#215868", "bold": true, "smallCaps": true, "spacing_before_pt": 12, "spacing_after_pt": 6},
  "heading3": {"font": "Calibri Light", "size_pt": 14, "color": "#215868", "bold": true, "smallCaps": true},
  "heading4": {"font": "Calibri Light", "size_pt": 12, "color": "#215868", "bold": true, "italic": true, "smallCaps": true},
  "normal":   {"font": "Calibri", "size_pt": 11, "color": "auto", "line_spacing": 1.15, "space_after_pt": 10},
  "hyperlink": {"color": "#2E74B5", "underline": "single"},
  "followed_hyperlink": {"color": "#800080", "underline": "single"},
  "table_grid": {"borders": "default"},
  "toc_heading": {"based_on": "Heading1"},
  "toc": {"levels": "1-3", "tab_leader": "dots"},
  "header": {"first_page_empty": true, "default": {"has_bottom_border": true, "tab_left": "{{dc:title}}", "tab_center": "", "tab_right": "{{user_supplied}}"}},
  "footer": {"first_page_empty": true, "default": {"has_top_border": true, "tab_left": "{{dc:creator}}", "tab_center": "Confidential - Do Not Distribute", "tab_right": "Page {PAGE} of {NUMPAGES}"}},
  "metadata_table": {"col1_in": 1.31, "col2_in": 5.38, "border_top_bottom_color": "#BFBFBF", "border_sides": "none"},
  "citation": {"size_pt": 9, "color_override": "#2E74B5", "vertAlign": "superscript"},
  "reference_entry": {"size_pt": 10, "hanging_in": 0.5, "spacing_before_pt": 3, "spacing_after_pt": 3, "url_size_pt": 9, "url_color": "#2E74B5"},
  "sectPr_preserved": true,
  "title_pg": true
}
```

Every number here must come from the template. A different template (e.g. a plain corporate white/blue) will produce a profile with different values, and your generated `.docx` must follow those values -- not the example values above.

### Summarize to the user

Before generation, describe the profile in plain language so the user can confirm it reads the template correctly:

> Template analyzed: `<name>`. Title style = Consolas 32 pt teal (`#215868`) smallCaps centered with a navy bottom rule. Body = Calibri 11 pt. H1-4 all Calibri Light smallCaps in the same teal; H1 adds a 1 pt teal underline. Hyperlinks render in medium blue (`#2E74B5`). Metadata table has light-gray row rules with no side borders. TOC uses levels 1-3, dots leader, headings are clickable.

If anything looks wrong, loop back and re-inspect before proceeding.

---
