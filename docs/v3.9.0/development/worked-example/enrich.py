#!/usr/bin/env python3
"""Apply the /presentify enrichment pass to a baseline content model.

The deterministic baseline builder renders a table of numbers as a table. The
enrichment pass (the LLM-native step in the skill) decides, per data shape, when
that table communicates better as a chart and which chart type fits. This script
encodes one such decision so the worked example is reproducible: it promotes a
named section's first numeric table (a label column plus one or more same-unit
numeric columns) into a chart block of a chosen type, and marks the section
data-forward. The chart-type choice per section is the agent's judgment, recorded
here as data rather than hand-edited HTML so the result can be regenerated.

Local-only; standard library only. No network calls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _to_number(cell: str) -> float:
    """Parse a numeric cell, tolerating thousands separators and surrounding text."""
    cleaned = cell.replace(",", "").strip()
    return float(cleaned)


def table_to_chart(table: dict[str, Any], chart_type_hint: str) -> dict[str, Any]:
    """Turn a {header, rows} table into a {categories, series} chart block.

    Column 0 supplies the category labels; every remaining column becomes a
    series named by its header. Raises ValueError if a numeric column is not
    cleanly numeric, so a bad promotion fails loudly instead of charting garbage.
    """
    header = table.get("header") or []
    rows = table.get("rows") or []
    if len(header) < 2 or not rows:
        raise ValueError("table needs a label column and at least one value column")
    categories = [row[0] for row in rows]
    series = []
    for col in range(1, len(header)):
        values = [_to_number(row[col]) for row in rows]
        series.append({"name": header[col], "values": values})
    return {
        "type": "chart",
        "chart_type_hint": chart_type_hint,
        "categories": categories,
        "series": series,
    }


def promote_first_table(section: dict[str, Any], chart_type_hint: str) -> bool:
    """Replace the first table block in a section with a chart; mark it data-forward."""
    for i, block in enumerate(section["blocks"]):
        if block.get("type") == "table":
            section["blocks"][i] = table_to_chart(block, chart_type_hint)
            section["kind"] = "data"
            return True
    return False


def enrich(model: dict[str, Any], rules: dict[str, str], subtitle: str | None) -> None:
    """Apply {section_heading: chart_type_hint} promotions and an optional subtitle."""
    if subtitle:
        for section in model["sections"]:
            if section.get("kind") == "title":
                section["subheading"] = subtitle
                break
    for section in model["sections"]:
        hint = rules.get(section.get("heading", ""))
        if hint and promote_first_table(section, hint):
            print(f"  promoted table in '{section['heading']}' -> {hint} chart")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the enrichment pass to a model.")
    parser.add_argument("model", help="Baseline content-model JSON path.")
    parser.add_argument("-o", "--out", required=True, help="Enriched output JSON path.")
    parser.add_argument(
        "--chart",
        action="append",
        default=[],
        metavar="HEADING=TYPE",
        help="Promote the first table in HEADING to a TYPE chart (repeatable).",
    )
    parser.add_argument("--subtitle", help="Set the title-section subheading.")
    args = parser.parse_args()

    rules: dict[str, str] = {}
    for spec in args.chart:
        heading, _, chart_type = spec.partition("=")
        rules[heading] = chart_type

    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    print(f"Enriching {args.model}")
    enrich(model, rules, args.subtitle)
    Path(args.out).write_text(
        json.dumps(model, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
