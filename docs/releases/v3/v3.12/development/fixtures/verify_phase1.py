#!/usr/bin/env python3
"""Verify Phase 1 (extraction fidelity) against the generated fixtures.

Runs scripts/extract_content.py over ./inputs/ into ./models/ and asserts the
plan's acceptance criteria. Prints one PASS/FAIL line per check and exits
non-zero when any check fails. Degradation checks re-run the extractor in a
subprocess with selected imports blocked (sys.modules[name] = None), so no
package needs to be uninstalled.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
MODELS = HERE / "models"
def _repo_root(start: Path) -> Path:
    """Walk up to the repository root instead of hand-counting parent depth.

    A fixed ``parents[N]`` silently breaks whenever the file moves a level, and
    the v4.0.0 docs migration moved this tree one level deeper. Anchoring on a
    marker that only the root carries makes the location irrelevant.
    """
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "catalog").is_dir():
            return candidate
    raise RuntimeError(f"repository root not found above {start}")

REPO = _repo_root(HERE)
EXTRACTOR = (
    REPO
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "scripts"
    / "extract_content.py"
)
BUILDER = EXTRACTOR.parent / "build_presentation.py"

FAILURES: list = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    suffix = f"  [{detail}]" if detail and not condition else ""
    print(f"{status}  {name}{suffix}")
    if not condition:
        FAILURES.append(name)


def run_extractor(
    inputs: list, out: Path, blocked: tuple = ()
) -> subprocess.CompletedProcess:
    """Run the extractor in a subprocess, optionally blocking imports."""
    argv = [str(path) for path in inputs] + ["-o", str(out)]
    code = (
        "import sys, runpy\n"
        f"for name in {list(blocked)!r}:\n"
        "    sys.modules[name] = None\n"
        f"sys.argv = ['extract_content.py'] + {argv!r}\n"
        f"runpy.run_path({str(EXTRACTOR)!r}, run_name='__main__')\n"
    )
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def blocks(model: dict, block_type: str) -> list:
    found: list = []
    for section in model["sections"]:
        for block in section["blocks"]:
            if block["type"] == block_type:
                found.append(block)
    return found


def all_text(model: dict) -> str:
    parts: list = []
    for section in model["sections"]:
        parts.append(section.get("heading") or "")
        for block in section["blocks"]:
            if block["type"] == "paragraph":
                parts.append(block["text"])
            elif block["type"] == "bullets":
                parts.extend(item["text"] for item in block["items"])
            elif block["type"] == "table":
                parts.extend(cell for row in block["rows"] for cell in row)
                parts.extend(block.get("header") or [])
    return " ".join(parts)


def main() -> int:
    MODELS.mkdir(exist_ok=True)

    # --- deck.pdf: the PDF-from-PowerPoint failure case -----------------
    result = run_extractor([INPUTS / "deck.pdf"], MODELS / "deck_pdf.json")
    check("deck.pdf extraction exits 0", result.returncode == 0, result.stderr[-400:])
    model = load(MODELS / "deck_pdf.json")
    cov = model["coverage"]["per_source"][0]
    check("schema_version is 2", model.get("schema_version") == 2)
    check("deck.pdf tagged deck_like", model["sources"][0].get("deck_like") is True)
    headings = [section["heading"] for section in model["sections"]]
    check(
        "typographic slide titles promoted",
        "Revenue by Quarter" in headings and "Enrollment Map" in headings,
        f"headings={headings}",
    )
    images = blocks(model, "image")
    regions = [b for b in images if b.get("origin") == "rasterized-region"]
    rasters = [b for b in images if b.get("origin") == "embedded-raster"]
    check("vector figure regions rasterized (chart + map)", len(regions) >= 2)
    check(
        "embedded photo extracted",
        any(b.get("page") == 4 for b in rasters),
        f"raster pages={[b.get('page') for b in rasters]}",
    )
    check(
        "chart region caption attached",
        any((b.get("caption") or "").startswith("Figure 1:") for b in regions),
        f"captions={[b.get('caption') for b in regions]}",
    )
    check(
        "repeated logo deduplicated",
        any("repeated-asset" in reason for reason in cov["skip_reasons"])
        and cov["images_skipped"] >= 3,
        f"cov={cov}",
    )
    check(
        "coverage counts vector regions",
        cov["vector_regions_rasterized"] == len(regions),
    )

    # --- deck.pptx: groups + native chart --------------------------------
    result = run_extractor([INPUTS / "deck.pptx"], MODELS / "deck_pptx.json")
    check("deck.pptx extraction exits 0", result.returncode == 0, result.stderr[-400:])
    model = load(MODELS / "deck_pptx.json")
    check(
        "grouped-shape text extracted",
        "Grouped insight" in all_text(model),
    )
    charts = blocks(model, "chart")
    native = [c for c in charts if c.get("provenance") == "native-chart"]
    check("native PPTX chart extracted", len(native) == 1, f"charts={len(charts)}")
    if native:
        chart = native[0]
        check(
            "PPTX chart values are the source's real numbers",
            chart["categories"] == ["Q1", "Q2", "Q3", "Q4"]
            and chart["series"][0]["values"] == [120.0, 135.0, 150.0, 170.0],
            f"chart={chart['categories']} {chart['series'][0]['values']}",
        )
        check(
            "PPTX chart title captured as caption",
            "Revenue by quarter" in chart.get("caption", ""),
        )
    check(
        "PPTX picture has origin/page metadata",
        any(
            b.get("origin") == "shape-picture" and isinstance(b.get("page"), int)
            for b in blocks(model, "image")
        ),
    )
    check("PPTX notes preserved", len(blocks(model, "notes")) == 1)
    check("PPTX table preserved", len(blocks(model, "table")) == 1)

    # --- report.docx: injected native chart part -------------------------
    result = run_extractor([INPUTS / "report.docx"], MODELS / "report_docx.json")
    check(
        "report.docx extraction exits 0", result.returncode == 0, result.stderr[-400:]
    )
    model = load(MODELS / "report_docx.json")
    native = [
        c for c in blocks(model, "chart") if c.get("provenance") == "native-chart"
    ]
    check("native DOCX chart extracted", len(native) == 1)
    if native:
        chart = native[0]
        check(
            "DOCX chart values are the source's real numbers",
            chart["categories"] == ["North", "South", "East"]
            and chart["series"][0]["values"] == [10.0, 20.0, 30.0]
            and chart["series"][0]["name"] == "Units",
            f"chart={chart['categories']} {chart['series'][0]}",
        )
    check(
        "DOCX inline image tagged",
        any(b.get("origin") == "inline-image" for b in blocks(model, "image")),
    )

    # --- data.xlsx: source-data provenance --------------------------------
    result = run_extractor([INPUTS / "data.xlsx"], MODELS / "data_xlsx.json")
    check("data.xlsx extraction exits 0", result.returncode == 0)
    model = load(MODELS / "data_xlsx.json")
    charts = blocks(model, "chart")
    check(
        "xlsx chart carries source-data provenance",
        len(charts) == 1 and charts[0].get("provenance") == "source-data",
    )

    # --- scanned.pdf: two-tier OCR path -----------------------------------
    result = run_extractor([INPUTS / "scanned.pdf"], MODELS / "scanned.json")
    check(
        "scanned.pdf extraction exits 0", result.returncode == 0, result.stderr[-400:]
    )
    model = load(MODELS / "scanned.json")
    cov = model["coverage"]["per_source"][0]
    check("both scanned pages detected", cov["scanned_pages_detected"] == 2)
    check("OCR ran on both pages (tier A)", cov["ocr_pages"] == 2, f"cov={cov}")
    ocr_paragraphs = [
        b
        for b in blocks(model, "paragraph") + blocks(model, "table")
        if b.get("provenance") == "ocr"
    ]
    check("OCR blocks carry provenance + confidence", len(ocr_paragraphs) > 0)
    check(
        "OCR confidence values populated",
        all(isinstance(b.get("ocr_confidence"), float) for b in ocr_paragraphs),
    )
    text = all_text(model).upper()
    check(
        "OCR recovered the known heading",
        "QUARTERLY" in text,
        text[:200],
    )
    check(
        "OCR recovered known table values",
        "42" in text and "37" in text,
    )
    pages_imaged = [
        b.get("page")
        for b in blocks(model, "image")
        if b.get("origin") == "scanned-page"
    ]
    check(
        "full-page scanned images emitted (tier B)",
        sorted(pages_imaged) == [1, 2],
        f"pages={pages_imaged}",
    )

    # --- degradation: no OCR engine ---------------------------------------
    result = run_extractor(
        [INPUTS / "scanned.pdf"],
        MODELS / "scanned_no_ocr.json",
        blocked=("rapidocr_onnxruntime", "pytesseract"),
    )
    check("no-OCR run exits 0", result.returncode == 0, result.stderr[-400:])
    model = load(MODELS / "scanned_no_ocr.json")
    cov = model["coverage"]["per_source"][0]
    check(
        "no-OCR run falls back to agent-vision pages",
        cov["ocr_pages"] == 0 and cov["agent_read_pages"] == 2,
        f"cov={cov}",
    )
    check(
        "no-OCR run still ships page images (no content loss)",
        len([b for b in blocks(model, "image") if b.get("origin") == "scanned-page"])
        == 2,
    )

    # --- degradation: no pypdfium2 renderer -------------------------------
    result = run_extractor(
        [INPUTS / "deck.pdf"],
        MODELS / "deck_no_renderer.json",
        blocked=("pypdfium2",),
    )
    check("no-renderer run exits 0", result.returncode == 0, result.stderr[-400:])
    check(
        "no-renderer run warns once with the pip hint",
        "pip install pypdfium2" in result.stderr,
        result.stderr[-300:],
    )
    model = load(MODELS / "deck_no_renderer.json")
    cov = model["coverage"]["per_source"][0]
    check(
        "no-renderer run keeps text + raster images",
        cov["vector_regions_skipped"] >= 2
        and any(b.get("origin") == "embedded-raster" for b in blocks(model, "image")),
        f"cov={cov}",
    )

    # --- degradation: no PDF parser at all --------------------------------
    result = run_extractor(
        [INPUTS / "deck.pdf"],
        MODELS / "deck_no_parser.json",
        blocked=("pdfplumber", "pypdf"),
    )
    check(
        "missing parser exits non-zero with the pip message",
        result.returncode != 0
        and "pip install pdfplumber" in result.stderr
        and "Traceback" not in result.stderr,
        result.stderr[-300:],
    )

    # --- multi-file merge + attribution ------------------------------------
    result = run_extractor(
        [
            INPUTS / "deck.pptx",
            INPUTS / "report.docx",
            INPUTS / "data.xlsx",
            INPUTS / "deck.pdf",
        ],
        MODELS / "combined.json",
    )
    check("multi-file extraction exits 0", result.returncode == 0)
    model = load(MODELS / "combined.json")
    check(
        "multi-file: 4 sources + 4 coverage entries in order",
        len(model["sources"]) == 4
        and len(model["coverage"]["per_source"]) == 4
        and [c["path"] for c in model["coverage"]["per_source"]]
        == [s["path"] for s in model["sources"]],
    )
    breaks = [
        s["heading"]
        for s in model["sections"]
        if s["kind"] == "section-break" and not s["blocks"]
    ]
    check("multi-file: per-source section breaks", len(breaks) >= 4)

    # --- determinism --------------------------------------------------------
    run_extractor([INPUTS / "deck.pdf"], MODELS / "deck_a.json")
    run_extractor([INPUTS / "deck.pdf"], MODELS / "deck_b.json")
    check(
        "byte-identical re-extraction (deck.pdf)",
        (MODELS / "deck_a.json").read_bytes() == (MODELS / "deck_b.json").read_bytes(),
    )
    run_extractor([INPUTS / "scanned.pdf"], MODELS / "scanned_b.json")
    check(
        "byte-identical re-extraction (scanned.pdf, OCR)",
        (MODELS / "scanned.json").read_bytes()
        == (MODELS / "scanned_b.json").read_bytes(),
    )

    # --- builder compatibility (v1 and v2) ----------------------------------
    v1_model = {
        "schema_version": 1,
        "title": "V1 Compat",
        "sources": [{"path": "x.docx", "format": "docx", "title": "V1 Compat"}],
        "sections": [
            {
                "heading": "V1 Compat",
                "subheading": None,
                "kind": "title",
                "source_index": 0,
                "blocks": [],
            },
            {
                "heading": "Body",
                "subheading": None,
                "kind": "content",
                "source_index": 0,
                "blocks": [{"type": "paragraph", "text": "Still builds."}],
            },
        ],
    }
    (MODELS / "v1_model.json").write_text(json.dumps(v1_model), encoding="utf-8")
    for label, model_file in (
        ("v1", MODELS / "v1_model.json"),
        ("v2", MODELS / "deck_pptx.json"),
    ):
        result = subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(model_file),
                "-o",
                str(MODELS / f"builder_{label}.html"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(
            f"builder accepts {label} model",
            result.returncode == 0 and (MODELS / f"builder_{label}.html").is_file(),
            result.stderr[-300:],
        )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED: {', '.join(FAILURES)}")
        return 1
    print("All Phase 1 checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
