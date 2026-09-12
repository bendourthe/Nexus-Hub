"""Phase 1 retained-input scaffolding; runtime and production assembly are pending."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def build(source: Path, output: Path) -> None:
    """Validate a neutral specimen before writing its incomplete reading page."""
    model = json.loads(source.read_text(encoding="utf-8"))
    ids = [section.get("id") for section in model["sections"]]
    if any(not isinstance(key, str) or not key for key in ids) or len(set(ids)) != len(
        ids
    ):
        raise ValueError("sections.id: missing or duplicate source key")
    for slide in model["presentation"]["slides"]:
        for key in slide["source_ids"]:
            if key not in ids:
                raise ValueError(
                    f"presentation.slides.source_ids: unknown source key {key}"
                )
    if output.resolve() == source.resolve() or output.exists():
        raise ValueError(f"output: refusing conflicting path {output.name}")
    page = [
        "<!doctype html><html lang='en'><meta charset='utf-8'>",
        f"<title>{html.escape(model['title'])}</title><main>",
        f"<h1>{html.escape(model['title'])}</h1>",
        "<p>Draft fixture: presentation runtime and production assembler pending.</p>",
    ]
    for section in model["sections"]:
        page.append(
            f'<section id="{html.escape(section["id"], quote=True)}">'
            f"<h2>{html.escape(section['heading'])}</h2>"
        )
        for block in section["blocks"]:
            if block["type"] == "paragraph":
                page.append(f"<p>{html.escape(block['text'])}</p>")
        page.append("</section>")
    storyboard = json.dumps(model["presentation"], sort_keys=True).replace(
        "<", "\\u003c"
    )
    page.append(
        f'</main><script type="application/json" id="storyboard">{storyboard}</script></html>'
    )
    output.write_text("\n".join(page), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
