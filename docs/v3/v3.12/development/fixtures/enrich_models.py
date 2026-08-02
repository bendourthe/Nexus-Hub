#!/usr/bin/env python3
"""Apply the Phase 2 figure-reconstruction protocol results to the fixture
models (the model round-trip): agent classifications, the one accepted chart
reconstruction (worksheet readings = fixture ground truth), and the scanned
fixture's OCR corrections.

The classification/worksheet decisions encoded here were made by the agent
reading the fixture images (see the Phase 2 session history); this script
replays them deterministically so `models/deck_pdf_enriched.json` and
`models/scanned_enriched.json` - the inputs to the Phase 3 budget demo and
the Phase 5 worked example - are reproducible from the kit alone.

Run after: gen_fixtures.py + verify_phase1.py (which produce models/*.json).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

MODELS = Path(__file__).resolve().parent / "models"

GROUND_TRUTH = [120.0, 135.0, 150.0, 170.0]


def enrich_deck() -> None:
    model = json.loads((MODELS / "deck_pdf.json").read_text(encoding="utf-8"))
    inserted = False
    for section in model["sections"]:
        new_blocks: list = []
        for block in section["blocks"]:
            new_blocks.append(block)
            if block["type"] != "image":
                continue
            origin, page = block.get("origin"), block.get("page")
            if origin == "embedded-raster" and page == 1:
                block["classification"] = "decorative"  # repeated logo
            elif origin == "rasterized-region" and page == 2:
                block["classification"] = "chart"
                new_blocks.append(
                    {
                        "type": "chart",
                        "chart_type_hint": "bar",
                        "categories": ["Q1", "Q2", "Q3", "Q4"],
                        "series": [{"name": "Revenue", "values": GROUND_TRUTH}],
                        "provenance": "reconstructed-from-image",
                        "confidence": "medium",
                        "source_image": block["data_uri"],
                        "caption": block.get(
                            "caption",
                            "Figure 1: Revenue by quarter (USD millions)",
                        ),
                        "axis": {
                            "x_label": "Quarter",
                            "y_label": "Revenue",
                            "y_min": 0,
                            "y_max": 175,
                            "unit": "USD millions",
                        },
                    }
                )
                inserted = True
            elif origin == "rasterized-region" and page == 3:
                block["classification"] = "map"
            elif origin == "embedded-raster" and page == 4:
                block["classification"] = "photo"
        section["blocks"] = new_blocks
    model["coverage"]["per_source"][0]["skip_reasons"].append(
        "decorative-skip: repeated logo (page 1) - no content value"
    )
    (MODELS / "deck_pdf_enriched.json").write_text(
        json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    unclassified = [
        b
        for s in model["sections"]
        for b in s["blocks"]
        if b["type"] == "image"
        and b.get("origin") != "scanned-page"
        and not b.get("classification")
    ]
    assert inserted and not unclassified
    print("deck_pdf_enriched.json written (4 classifications, 1 reconstruction)")


def enrich_scanned() -> None:
    model = json.loads((MODELS / "scanned.json").read_text(encoding="utf-8"))
    corrections = 0
    for section in model["sections"]:
        new_blocks: list = []
        for block in section["blocks"]:
            if block.get("provenance") == "ocr" and block["type"] == "paragraph":
                text = block["text"]
                compact = re.sub(r"[^a-z0-9]+", "", text.casefold())
                if compact == "quarterlyupdate":
                    block["text"] = "QUARTERLY UPDATE"
                    block["provenance"] = "agent-read"
                    corrections += 1
                    new_blocks.append(block)
                    continue
                if compact.startswith("revenuegrewtwelvepercent"):
                    new_blocks.append(
                        {
                            "type": "paragraph",
                            "text": "Revenue grew twelve percent over the "
                            "prior quarter.",
                            "provenance": "agent-read",
                        }
                    )
                    new_blocks.append(
                        {
                            "type": "paragraph",
                            "text": "Enrollment reached both regional targets.",
                            "provenance": "agent-read",
                        }
                    )
                    corrections += 1
                    continue
                if compact == "revenuefigure":
                    block["text"] = "REVENUE FIGURE"
                    block["provenance"] = "agent-read"
                    corrections += 1
                    new_blocks.append(block)
                    continue
            if block.get("provenance") == "ocr" and block["type"] == "table":
                assert block["rows"] == [["North", "42"], ["South", "37"]]
                block["verified"] = True
            new_blocks.append(block)
        section["blocks"] = new_blocks
    model["coverage"]["per_source"][0]["skip_reasons"].append(
        "reconstruction-declined (page 2 figure): no axes/ticks/labels and "
        "caption says illustrative - low confidence, presented as enhanced "
        "original"
    )
    (MODELS / "scanned_enriched.json").write_text(
        json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    fabricated = [
        b for s in model["sections"] for b in s["blocks"] if b["type"] == "chart"
    ]
    assert corrections == 3 and not fabricated
    print("scanned_enriched.json written (3 OCR corrections, 0 fabricated charts)")


if __name__ == "__main__":
    enrich_deck()
    enrich_scanned()
    print("round-trip OK")
