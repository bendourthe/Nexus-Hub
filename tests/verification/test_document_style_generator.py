"""Generator defaults for the document style rules (catalog/rules/documents/document-style.md).

Rules 1, 2 and 4 are code defaults in scripts/generate_report.py, not only prose. Each
test builds a real .docx, saves it, reopens it, and reads the cell fills and run
formatting back from the file, so the assertions describe what a reader of the
document actually gets.

Run from the repo root:

    python -m pytest tests/verification/test_document_style_generator.py -v
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

docx = pytest.importorskip("docx")
from docx.oxml.ns import qn  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("generate_report", REPO_ROOT / "scripts" / "generate_report.py")
assert _SPEC and _SPEC.loader
gr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gr)

GREEN, ORANGE = "C6E0B4", "F8CBAD"


def _fill(cell) -> str | None:
    shd = cell._tc.tcPr.find(qn("w:shd")) if cell._tc.tcPr is not None else None
    return None if shd is None else shd.get(qn("w:fill"))


def _reopen(doc, tmp_path: Path):
    path = tmp_path / "out.docx"
    doc.save(path)
    return docx.Document(path)


def _table(tints, header_fill=None, tmp_path=None):
    doc = docx.Document()
    table = doc.add_table(rows=1 + len(tints), cols=2)
    for row_idx, row in enumerate(table.rows):
        for col_idx, cell in enumerate(row.cells):
            cell.text = "Header" if row_idx == 0 else f"r{row_idx}c{col_idx}"
    gr.apply_table_style(table, row_tints=tints, header_fill=header_fill)
    return _reopen(doc, tmp_path).tables[0]


def test_color_coded_table_gets_neutral_header_and_alternating_tints(tmp_path: Path) -> None:
    table = _table([GREEN, GREEN, GREEN, ORANGE, ORANGE], tmp_path=tmp_path)
    header = table.rows[0].cells[0]
    assert _fill(header) == "262626"
    run = header.paragraphs[0].runs[0]
    assert run.bold and str(run.font.color.rgb) == "FFFFFF"
    fills = [_fill(row.cells[0]) for row in table.rows[1:]]
    light_green, light_orange = gr._lighten(GREEN), gr._lighten(ORANGE)
    assert fills == [GREEN, light_green, GREEN, ORANGE, light_orange]
    # every cell of a row carries the same fill
    assert all(len({_fill(c) for c in row.cells}) == 1 for row in table.rows)


def test_lightened_tint_is_55_percent_toward_white() -> None:
    assert gr._lighten("000000") == "8C8C8C"
    assert gr._lighten("FFFFFF") == "FFFFFF"


def test_plain_table_alternates_white_and_light_gray(tmp_path: Path) -> None:
    doc = docx.Document()
    gr.add_markdown_paragraph(doc, "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n| 5 | 6 |")
    table = _reopen(doc, tmp_path).tables[0]
    assert _fill(table.rows[0].cells[0]) == "262626"
    assert [_fill(r.cells[0]) for r in table.rows[1:]] == ["FFFFFF", "F2F2F2", "FFFFFF"]


def test_header_never_reuses_a_row_color_across_groups(tmp_path: Path) -> None:
    table = _table([GREEN, ORANGE], header_fill=GREEN, tmp_path=tmp_path)
    assert _fill(table.rows[0].cells[0]) == "262626"


def test_header_may_take_the_row_color_when_every_row_shares_it(tmp_path: Path) -> None:
    table = _table([GREEN, GREEN, GREEN], header_fill=GREEN, tmp_path=tmp_path)
    assert _fill(table.rows[0].cells[0]) == GREEN


def test_header_moves_off_a_dark_row_tint_close_to_the_default(tmp_path: Path) -> None:
    table = _table(["303030", "303030", ORANGE], tmp_path=tmp_path)
    header = _fill(table.rows[0].cells[0])
    assert header not in ("262626", "303030")
    assert gr._color_distance(header, "303030") >= gr._HEADER_MIN_DISTANCE


def test_lead_in_formatting_ends_at_the_colon(tmp_path: Path) -> None:
    doc = docx.Document()
    p = doc.add_paragraph()
    gr.add_lead_in(p, "Label: ")
    p.add_run("value")
    runs = _reopen(doc, tmp_path).paragraphs[0].runs
    assert [(r.text, bool(r.bold)) for r in runs] == [("Label:", True), (" ", False), ("value", False)]


@pytest.mark.parametrize(
    "markdown",
    ["**Released device (PMA)**: approved", "**Released device (PMA): **approved", "**Released device (PMA):** approved"],
)
def test_markdown_lead_in_bold_covers_label_and_colon_only(markdown: str, tmp_path: Path) -> None:
    doc = docx.Document()
    gr.add_formatted_text(doc.add_paragraph(), markdown)
    runs = _reopen(doc, tmp_path).paragraphs[0].runs
    assert (runs[0].text, bool(runs[0].bold)) == ("Released device (PMA):", True)
    assert not runs[1].bold and runs[1].text.startswith(" ")
    assert "".join(r.text for r in runs) == "Released device (PMA): approved"
