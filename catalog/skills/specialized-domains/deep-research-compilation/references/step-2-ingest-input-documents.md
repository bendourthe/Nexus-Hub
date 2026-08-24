## Step 2: Ingest Input Documents

For each user-provided input, extract a normalized record:

```python
@dataclass
class ExtractedSource:
    source: str
    title: str
    sections: list[dict]    # [{"level": 1-4, "heading": str, "content_md": str}]
    references: list[dict]  # [{"local_num": int, "text": str, "url": str|None, "doi": str|None}]
    citations: list[dict]   # [{"section_idx": int, "char_offset": int, "local_num": int}]
```

### Per-format recipes

**.docx** -- use `python-docx` + raw zipfile XML for fidelity:

```python
import docx
from docx.oxml.ns import qn

d = docx.Document(path)
title = d.core_properties.title or Path(path).stem

sections = []
in_refs = False
ref_buf = []
for p in d.paragraphs:
    style_name = (p.style.name or "").strip()
    text = p.text.strip()
    if not text:
        continue
    if style_name.startswith("Heading"):
        if text.lower() == "references":
            in_refs = True; continue
        if in_refs: in_refs = False
        level = int(re.search(r"(\d)", style_name).group(1)) if re.search(r"\d", style_name) else 1
        sections.append({"level": level, "heading": text, "content_md": ""})
        continue
    if in_refs:
        # Look for external URL hyperlinks on this paragraph
        url = None
        for h in p._element.findall(qn("w:hyperlink")):
            rId = h.get(qn("r:id"))
            if rId and rId in d.part.rels and d.part.rels[rId].is_external:
                url = d.part.rels[rId].target_ref
                break
        ref_buf.append((text, url))
        continue
    if sections:
        sections[-1]["content_md"] += text + "\n\n"

# Citation discovery: superscript runs with bookmark-hyperlinks are true citations.
# Less-formatted docs just use [N] inline, which the regex below picks up.
```

For citation extraction, regex-scan each section's `content_md` for `\[(\d+(?:\s*,\s*\d+)*)\]` patterns. Also, Word's Gemini-style docs often render citations as small superscript text without bookmarks -- when you see a superscript run containing only digits, treat each digit as a citation local_num.

**.md** -- stdlib regex:

```python
CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
REF_LINK_RE = re.compile(r"^\[(\d+)\]:\s*(https?://\S+)\s*$", re.MULTILINE)
REF_HDG_RE  = re.compile(r"^#+\s*references\s*$", re.IGNORECASE | re.MULTILINE)

body, refs_text = split_on(REF_HDG_RE, raw)
sections = parse_headings(body)       # split on ^#{1,4}\s+...$
inline_cites = CITATION_RE.findall(body)
refs = parse_refs_block(refs_text)    # see Step 4 "Reference block parser"
```

**.pdf** -- `pypdf`:

```python
import pypdf
reader = pypdf.PdfReader(path)
full = "\n\n".join(p.extract_text() or "" for p in reader.pages)
if not full.strip():
    raise RuntimeError(f"{path}: no text layer -- OCR is out of scope")
```

Then apply the same heading heuristic as `.txt` (ALL-CAPS or underlined short lines).

**.pptx** -- `python-pptx`, one slide per section:

```python
from pptx import Presentation
prs = Presentation(path)
for idx, slide in enumerate(prs.slides, start=1):
    heading = (slide.shapes.title.text_frame.text.strip()
               if slide.shapes.title and slide.shapes.title.has_text_frame
               else f"Slide {idx}")
    body = "\n\n".join(s.text_frame.text for s in slide.shapes
                       if s != slide.shapes.title and s.has_text_frame)
```

**.html + URL** -- `beautifulsoup4` + `httpx`:

```python
import httpx
from bs4 import BeautifulSoup
html = (httpx.get(url, timeout=30, follow_redirects=True,
                  headers={"User-Agent": "compile-deep-research/1.0"}).text
        if url.startswith("http") else Path(url).read_text())
soup = BeautifulSoup(html, "html.parser")
for tag in soup(["script", "style", "noscript"]): tag.decompose()
# headings from <h1-h3>, paragraphs from <p>, refs from <a href> inside a section
# whose heading text contains "reference"
```

**.txt** -- regex heuristics:

- Heading pattern 1: ALL-CAPS short line (len 4-80, no terminal period).
- Heading pattern 2: any short line followed immediately by a line of `=` or `-` (underline style).
- References: everything after an isolated line `References` (case-insensitive).

### Parsing the References block (applies to every format)

References come in many forms. Use this layered approach:

1. **Line-anchored numbered**: each line starts with `[N]`, `N.`, or `N)`. Group continuation lines (no such prefix) into the prior entry.
2. **Markdown reference-link syntax**: `^\[N\]:\s*(https?://\S+)$` -- extract directly.
3. **Fallback**: split on blank lines; treat each paragraph as one entry.

For each entry text, run `URL_RE` and `DOI_RE` over it to pull structured values:

```python
URL_RE = re.compile(r"https?://[^\s\)\]\">]+", re.IGNORECASE)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"',<>]+", re.IGNORECASE)
```

---
