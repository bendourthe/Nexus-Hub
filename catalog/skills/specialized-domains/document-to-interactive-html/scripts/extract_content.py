#!/usr/bin/env python3
"""
extract_content.py - Local multi-format document extractor for the
document-to-interactive-html skill.

This script ships as a Tier-3 bundled resource: the agent invokes it via the
shell and consumes its JSON output without reading the source into context. It
maps one OR many source documents - in any mix of PowerPoint (.pptx), Word
(.docx), Excel (.xlsx), and PDF (.pdf) - into the single normalized "content
model" defined in references/content-model.md. The Phase 2 builder
(build_presentation.py) consumes that model and never reads a source format
directly.

LOCAL-FIRST and ZERO-NETWORK by construction: every parser is a local library,
imported LAZILY inside the function that needs it so a missing library degrades
to a clear `pip install` message (and a non-zero exit) instead of a crash, and
so a missing parser for one format never blocks another. This script imports no
socket / urllib / http / requests module and opens no connection; no document
ever leaves the machine.

Parsers (lazy-imported, install only what your inputs need):
    .pptx  ->  python-pptx        (pip install python-pptx)
    .docx  ->  python-docx        (pip install python-docx)
    .xlsx  ->  openpyxl           (pip install openpyxl)
    .pdf   ->  pdfplumber         (pip install pdfplumber); pypdf is a fallback
    images ->  Pillow (optional)  (pip install Pillow) - only used to downscale
                                   an over-budget image; absence => the image is
                                   skipped with a warning, never an error.

Usage:
    python extract_content.py deck.pptx -o model.json
    python extract_content.py report.docx data.xlsx -o combined.json
    python extract_content.py ./inputs_folder -o model.json --max-image-bytes 1500000

Output is written to the --out JSON path; all diagnostics go to stderr so stdout
stays clean. Output ordering is deterministic: sources in input order, sections
in source order, blocks in document order.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import NoReturn

EXTENSION_FORMATS = {
    ".pptx": "pptx",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".pdf": "pdf",
}

DEFAULT_MAX_IMAGE_BYTES = 2_000_000


def _missing(pip_name: str) -> NoReturn:
    """Print the standard missing-dependency message and exit non-zero.

    Raises SystemExit (a BaseException, not an Exception) so it is never
    swallowed by the per-file `except Exception` guard in build_model.
    """
    print(
        f"Error: {pip_name} not installed. Please run: pip install {pip_name}",
        file=sys.stderr,
    )
    raise SystemExit(1)


# --- small shared helpers --------------------------------------------------


def _cell_str(value: object) -> str:
    """Stringify a cell value deterministically (None -> '', 3.0 -> '3')."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _is_number(value: object) -> bool:
    """True for a real numeric cell (bool is excluded; it subclasses int)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _try_downscale(blob: bytes, max_bytes: int) -> bytes | None:
    """Best-effort downscale of an over-budget image via Pillow (optional).

    Returns JPEG bytes within budget, or None if Pillow is absent or the image
    cannot be brought under budget. Never raises on a missing library.
    """
    try:
        from PIL import Image
    except ImportError:
        return None
    import io

    try:
        image = Image.open(io.BytesIO(blob)).convert("RGB")
    except (OSError, ValueError):
        return None
    scale = 1.0
    for _ in range(6):
        width, height = image.size
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        buffer = io.BytesIO()
        image.resize(new_size).save(buffer, format="JPEG", quality=82)
        data = buffer.getvalue()
        if len(data) <= max_bytes:
            return data
        scale *= 0.7
    return None


def _encode_image(
    blob: bytes, content_type: str, alt: str, max_bytes: int
) -> dict | None:
    """Build a base64 image block, downscaling or skipping if over budget."""
    if len(blob) > max_bytes:
        downscaled = _try_downscale(blob, max_bytes)
        if downscaled is None or len(downscaled) > max_bytes:
            print(
                f"Warning: skipping image ({len(blob)} bytes) over the "
                f"{max_bytes}-byte budget (install Pillow to downscale).",
                file=sys.stderr,
            )
            return None
        blob, content_type = downscaled, "image/jpeg"
    encoded = base64.b64encode(blob).decode("ascii")
    return {
        "type": "image",
        "data_uri": f"data:{content_type or 'image/png'};base64,{encoded}",
        "alt": alt or "Image",
    }


def _table_from_grid(grid: list) -> dict | None:
    """Turn a list-of-rows grid into a table block (first row = header)."""
    rows = [[_cell_str(cell) for cell in (row or [])] for row in grid]
    rows = [row for row in rows if any(cell for cell in row)]
    if not rows:
        return None
    return {"type": "table", "header": rows[0], "rows": rows[1:]}


# --- PowerPoint ------------------------------------------------------------


def _pptx_text_block(text_frame: object) -> dict | None:
    paragraphs = [p for p in text_frame.paragraphs if p.text.strip()]
    if not paragraphs:
        return None
    if len(paragraphs) == 1 and int(getattr(paragraphs[0], "level", 0) or 0) == 0:
        return {"type": "paragraph", "text": paragraphs[0].text.strip()}
    items = [
        {"text": p.text.strip(), "depth": int(getattr(p, "level", 0) or 0)}
        for p in paragraphs
    ]
    return {"type": "bullets", "items": items}


def _pptx_table_block(table: object) -> dict | None:
    rows = [[_cell_str(cell.text) for cell in row.cells] for row in table.rows]
    if not rows:
        return None
    header: list = []
    body = rows
    try:
        if table.first_row:
            header, body = rows[0], rows[1:]
    except (AttributeError, ValueError):
        pass
    return {"type": "table", "header": header, "rows": body}


def _pptx_image_block(shape: object, max_bytes: int) -> dict | None:
    try:
        image = shape.image
    except (AttributeError, ValueError):
        return None
    alt = (getattr(shape, "name", "") or "Image").strip() or "Image"
    return _encode_image(image.blob, image.content_type, alt, max_bytes)


def _pptx_kind(index: int, heading: str, blocks: list) -> str:
    if index == 0:
        return "title"
    has_content = any(block["type"] != "notes" for block in blocks)
    if heading and not has_content:
        return "section-break"
    return "content"


def _extract_pptx(path: str, max_bytes: int) -> tuple[str, list]:
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER
    except ImportError:
        _missing("python-pptx")

    presentation = Presentation(path)
    doc_title: str | None = None
    sections: list = []
    for index, slide in enumerate(presentation.slides):
        title_shape = slide.shapes.title
        heading = title_shape.text.strip() if title_shape is not None else ""
        if doc_title is None and heading:
            doc_title = heading
        skip_ids = {title_shape.shape_id} if title_shape is not None else set()
        subheading: str | None = None
        for placeholder in slide.placeholders:
            try:
                if placeholder.placeholder_format.type == PP_PLACEHOLDER.SUBTITLE:
                    subheading = placeholder.text.strip()
                    skip_ids.add(placeholder.shape_id)
                    break
            except (AttributeError, ValueError):
                continue
        blocks: list = []
        for shape in slide.shapes:
            if shape.shape_id in skip_ids:
                continue
            block = None
            if getattr(shape, "has_table", False):
                block = _pptx_table_block(shape.table)
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                block = _pptx_image_block(shape, max_bytes)
            elif getattr(shape, "has_text_frame", False):
                block = _pptx_text_block(shape.text_frame)
            if block is not None:
                blocks.append(block)
        if slide.has_notes_slide:
            note = slide.notes_slide.notes_text_frame.text.strip()
            if note:
                blocks.append({"type": "notes", "text": note})
        sections.append(
            {
                "heading": heading,
                "subheading": subheading,
                "kind": _pptx_kind(index, heading, blocks),
                "source_index": 0,
                "blocks": blocks,
            }
        )
    return doc_title or Path(path).stem, sections


# --- Word ------------------------------------------------------------------


def _iter_docx_blocks(document: object):
    """Yield Paragraph and Table objects in document order."""
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _docx_list_level(paragraph: object) -> int | None:
    """Return a list nesting level (0-based) or None when not a list item."""
    from docx.oxml.ns import qn

    properties = paragraph._p.pPr
    if properties is None:
        name = (paragraph.style.name if paragraph.style else "") or ""
        return 0 if name.startswith("List") else None
    num_pr = properties.find(qn("w:numPr"))
    if num_pr is None:
        name = (paragraph.style.name if paragraph.style else "") or ""
        return 0 if name.startswith("List") else None
    level = num_pr.find(qn("w:ilvl"))
    if level is not None:
        return int(level.get(qn("w:val")) or 0)
    return 0


def _docx_paragraph_images(paragraph: object, document: object, max_bytes: int) -> list:
    from docx.oxml.ns import qn

    blocks: list = []
    for blip in paragraph._p.findall(".//" + qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        if not rid:
            continue
        try:
            part = document.part.related_parts[rid]
        except KeyError:
            continue
        block = _encode_image(
            part.blob, getattr(part, "content_type", "image/png"), "Image", max_bytes
        )
        if block is not None:
            blocks.append(block)
    return blocks


def _docx_table_block(table: object) -> dict | None:
    rows = [[_cell_str(cell.text) for cell in row.cells] for row in table.rows]
    return _table_from_grid(rows)


def _extract_docx(path: str, max_bytes: int) -> tuple[str, list]:
    try:
        from docx import Document
    except ImportError:
        _missing("python-docx")

    document = Document(path)
    doc_title: str | None = None
    sections: list = []
    current: dict | None = None
    pending: list = []

    def flush_bullets() -> None:
        if pending and current is not None:
            current["blocks"].append({"type": "bullets", "items": list(pending)})
        pending.clear()

    def ensure_section() -> dict:
        nonlocal current
        if current is None:
            current = {
                "heading": "Overview",
                "subheading": None,
                "kind": "content",
                "source_index": 0,
                "blocks": [],
            }
            sections.append(current)
        return current

    for item in _iter_docx_blocks(document):
        if hasattr(item, "rows"):  # Table
            flush_bullets()
            block = _docx_table_block(item)
            if block is not None:
                ensure_section()["blocks"].append(block)
            continue
        style = (item.style.name if item.style else "") or ""
        text = item.text.strip()
        if style == "Title":
            if not doc_title:
                doc_title = text
            continue
        if style.startswith("Heading"):
            flush_bullets()
            current = {
                "heading": text,
                "subheading": None,
                "kind": "content",
                "source_index": 0,
                "blocks": [],
            }
            sections.append(current)
            continue
        images = _docx_paragraph_images(item, document, max_bytes)
        if images:
            flush_bullets()
            ensure_section()["blocks"].extend(images)
        if not text:
            continue
        level = _docx_list_level(item)
        if level is not None:
            ensure_section()
            pending.append({"text": text, "depth": level})
        else:
            flush_bullets()
            ensure_section()["blocks"].append({"type": "paragraph", "text": text})
    flush_bullets()
    return doc_title or Path(path).stem, sections


# --- Excel -----------------------------------------------------------------


def _trim_grid(rows: list) -> list:
    rows = [
        list(row)
        for row in rows
        if any(cell is not None and str(cell).strip() != "" for cell in row)
    ]
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [None] * (width - len(row)) for row in rows]
    keep = [
        col
        for col in range(width)
        if any(row[col] is not None and str(row[col]).strip() != "" for row in rows)
    ]
    if not keep:
        return []
    return [[row[col] for col in keep] for row in rows]


def _chart_hint(category_count: int, series_count: int) -> str:
    if series_count == 1 and category_count <= 6:
        return "pie"
    if category_count > 12:
        return "line"
    return "bar"


def _grid_to_block(grid: list) -> dict | None:
    if len(grid) >= 2 and len(grid[0]) >= 2:
        header = [_cell_str(cell) for cell in grid[0]]
        body = grid[1:]
        categories = [_cell_str(row[0]) for row in body]
        series: list = []
        for col in range(1, len(header)):
            column = [row[col] for row in body]
            if column and all(_is_number(value) for value in column):
                series.append(
                    {
                        "name": header[col] or f"Series {col}",
                        "values": [float(value) for value in column],
                    }
                )
        if series and any(categories):
            return {
                "type": "chart",
                "chart_type_hint": _chart_hint(len(categories), len(series)),
                "categories": categories,
                "series": series,
            }
    return _table_from_grid(grid)


def _extract_xlsx(path: str) -> tuple[str, list]:
    try:
        from openpyxl import load_workbook
    except ImportError:
        _missing("openpyxl")

    workbook = load_workbook(path, data_only=True, read_only=True)
    sections: list = []
    for worksheet in workbook.worksheets:
        grid = _trim_grid([list(row) for row in worksheet.iter_rows(values_only=True)])
        if not grid:
            continue
        block = _grid_to_block(grid)
        sections.append(
            {
                "heading": worksheet.title,
                "subheading": None,
                "kind": "data",
                "source_index": 0,
                "blocks": [block] if block is not None else [],
            }
        )
    workbook.close()
    return Path(path).stem, sections


# --- PDF -------------------------------------------------------------------


def _pdf_page_section(text: str, page_number: int) -> dict:
    lines = text.splitlines()
    heading = f"Page {page_number}"
    start = 0
    for index, line in enumerate(lines):
        if line.strip():
            if len(line.strip()) <= 80:
                heading, start = line.strip(), index + 1
            else:
                start = index
            break
    paragraphs: list = []
    current: list = []
    for line in lines[start:]:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    blocks = [{"type": "paragraph", "text": para} for para in paragraphs if para]
    return {
        "heading": heading,
        "subheading": None,
        "kind": "content",
        "source_index": 0,
        "blocks": blocks,
    }


def _extract_pdf_pypdf(path: str) -> tuple[str, list]:
    try:
        from pypdf import PdfReader
    except ImportError:
        _missing("pdfplumber")

    reader = PdfReader(path)
    doc_title: str | None = None
    sections: list = []
    for index, page in enumerate(reader.pages):
        section = _pdf_page_section(page.extract_text() or "", index + 1)
        if doc_title is None and not section["heading"].startswith("Page "):
            doc_title = section["heading"]
        sections.append(section)
    return doc_title or Path(path).stem, sections


def _extract_pdf(path: str, max_bytes: int) -> tuple[str, list]:
    try:
        import pdfplumber
    except ImportError:
        return _extract_pdf_pypdf(path)

    doc_title: str | None = None
    sections: list = []
    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages):
            section = _pdf_page_section(page.extract_text() or "", index + 1)
            for table in page.extract_tables() or []:
                block = _table_from_grid(table)
                if block is not None:
                    section["blocks"].append(block)
            if doc_title is None and not section["heading"].startswith("Page "):
                doc_title = section["heading"]
            sections.append(section)
    return doc_title or Path(path).stem, sections


# --- dispatch and merge ----------------------------------------------------


def _detect_format(path: str) -> str | None:
    return EXTENSION_FORMATS.get(Path(path).suffix.lower())


def _expand_inputs(paths: list) -> list:
    """Expand folders to their supported files (sorted), keep files as-is."""
    expanded: list = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for child in sorted(path.iterdir()):
                if child.is_file() and _detect_format(str(child)):
                    expanded.append(str(child))
        else:
            expanded.append(str(path))
    return expanded


def _extract_one(path: str, fmt: str, max_bytes: int) -> tuple[str, list]:
    if fmt == "pptx":
        return _extract_pptx(path, max_bytes)
    if fmt == "docx":
        return _extract_docx(path, max_bytes)
    if fmt == "xlsx":
        return _extract_xlsx(path)
    if fmt == "pdf":
        return _extract_pdf(path, max_bytes)
    raise ValueError(f"unsupported format: {fmt}")


def _agenda_section(headings: list) -> dict:
    return {
        "heading": "Agenda",
        "subheading": None,
        "kind": "section-break",
        "source_index": 0,
        "blocks": [
            {
                "type": "bullets",
                "items": [{"text": head, "depth": 0} for head in headings],
            }
        ],
    }


def build_model(
    paths: list, max_bytes: int = DEFAULT_MAX_IMAGE_BYTES, title_override: str | None = None
) -> dict:
    """Extract every input into one merged, deterministic content model."""
    sources: list = []
    per_source: list = []  # (index, fmt, title, sections)
    for path in _expand_inputs(paths):
        fmt = _detect_format(path)
        if fmt is None:
            print(f"Warning: skipping unsupported file: {path}", file=sys.stderr)
            continue
        if not Path(path).is_file():
            print(f"Warning: input not found: {path}", file=sys.stderr)
            continue
        try:
            detected_title, sections = _extract_one(path, fmt, max_bytes)
        except SystemExit:
            raise  # missing-dependency exit must propagate
        except Exception as exc:  # noqa: BLE001 - logged, then this file is skipped
            print(f"Warning: failed to extract {path}: {exc}", file=sys.stderr)
            continue
        index = len(sources)
        title = detected_title or Path(path).stem
        sources.append({"path": Path(path).name, "format": fmt, "title": title})
        per_source.append((index, fmt, title, sections))

    if not sources:
        print(
            "Error: no supported input documents found (.pptx/.docx/.xlsx/.pdf).",
            file=sys.stderr,
        )
        raise SystemExit(2)

    out_sections: list = []
    if len(sources) > 1:
        umbrella = title_override or sources[0]["title"]
        out_sections.append(
            {
                "heading": umbrella,
                "subheading": "Combined sources",
                "kind": "title",
                "source_index": 0,
                "blocks": [
                    {
                        "type": "bullets",
                        "items": [
                            {"text": src["title"], "depth": 0} for src in sources
                        ],
                    }
                ],
            }
        )
        for index, _fmt, title, sections in per_source:
            out_sections.append(
                {
                    "heading": title,
                    "subheading": None,
                    "kind": "section-break",
                    "source_index": index,
                    "blocks": [],
                }
            )
            for section in sections:
                section["source_index"] = index
                out_sections.append(section)
        model_title = umbrella
    else:
        index, fmt, title, sections = per_source[0]
        model_title = title_override or title
        if fmt in ("docx", "pdf", "xlsx"):
            out_sections.append(
                {
                    "heading": model_title,
                    "subheading": None,
                    "kind": "title",
                    "source_index": 0,
                    "blocks": [],
                }
            )
            headings = [
                section["heading"]
                for section in sections
                if section["kind"] in ("content", "data") and section["heading"]
            ]
            if fmt in ("docx", "pdf") and len(headings) >= 2:
                out_sections.append(_agenda_section(headings))
        for section in sections:
            section["source_index"] = 0
            out_sections.append(section)

    return {
        "schema_version": 1,
        "title": model_title,
        "sources": sources,
        "sections": out_sections,
    }


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract one or more documents (.pptx/.docx/.xlsx/.pdf, or a folder "
            "of them) into the normalized content-model JSON consumed by "
            "build_presentation.py. Local-only parsing; no network calls."
        )
    )
    parser.add_argument(
        "inputs", nargs="+", help="Input file(s) or folder(s) to extract."
    )
    parser.add_argument(
        "-o", "--out", required=True, help="Output content-model JSON path."
    )
    parser.add_argument(
        "--max-image-bytes",
        type=int,
        default=DEFAULT_MAX_IMAGE_BYTES,
        help="Per-image byte budget before downscale/skip (default 2000000).",
    )
    parser.add_argument(
        "--title", default=None, help="Override the synthesized presentation title."
    )
    args = parser.parse_args(argv)

    model = build_model(args.inputs, args.max_image_bytes, args.title)
    out_path = Path(args.out)
    if out_path.parent and not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(model, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(
        f"Wrote {out_path} ({len(model['sources'])} source(s), "
        f"{len(model['sections'])} section(s)).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
