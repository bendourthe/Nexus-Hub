"""Regression tests for deterministic Presentify fixture enrichment."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_ENRICH_PATH = (
    _ROOT / "docs" / "releases" / "v3" / "v3.12" / "development" / "fixtures" / "enrich_models.py"
)


def _load_enricher():
    spec = importlib.util.spec_from_file_location("presentify_enrich_models", _ENRICH_PATH)
    assert spec and spec.loader, f"cannot load {_ENRICH_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("heading", "revenue", "figure"),
    [
        ("QUARTERLYUPDATE", "Revenue grewtwelvepercent over the prior quarter.", "REVENUEFIGURE"),
        ("QUARTERLY UPDATE", "Revenue grew twelve percent over the prior quarter.", "REVENUE FIGURE"),
    ],
)
def test_scanned_enrichment_accepts_ocr_spacing_variants(
    tmp_path: Path, heading: str, revenue: str, figure: str
) -> None:
    model = {
        "sections": [
            {
                "blocks": [
                    {"type": "paragraph", "text": heading, "provenance": "ocr"},
                    {"type": "paragraph", "text": revenue, "provenance": "ocr"},
                    {"type": "paragraph", "text": figure, "provenance": "ocr"},
                    {
                        "type": "table",
                        "rows": [["North", "42"], ["South", "37"]],
                        "provenance": "ocr",
                    },
                ]
            }
        ],
        "coverage": {"per_source": [{"skip_reasons": []}]},
    }
    (tmp_path / "scanned.json").write_text(json.dumps(model), encoding="utf-8")
    enricher = _load_enricher()
    enricher.MODELS = tmp_path

    enricher.enrich_scanned()

    enriched = json.loads((tmp_path / "scanned_enriched.json").read_text(encoding="utf-8"))
    blocks = enriched["sections"][0]["blocks"]
    paragraphs = [block["text"] for block in blocks if block["type"] == "paragraph"]
    assert paragraphs == [
        "QUARTERLY UPDATE",
        "Revenue grew twelve percent over the prior quarter.",
        "Enrollment reached both regional targets.",
        "REVENUE FIGURE",
    ]
    assert all(
        block["provenance"] == "agent-read"
        for block in blocks
        if block["type"] == "paragraph"
    )
    assert next(block for block in blocks if block["type"] == "table")["verified"] is True
