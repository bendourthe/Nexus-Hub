"""Baseline builder: opt-in brand font embedding and gallery grouping (v4.13 AR-18).

A brand font is inlined as a base64 @font-face read from the brand's
`assets_dir`, so the deck never fetches a font. A run of comparable,
low-`page_fraction` images renders as one `.gallery`; a hero or an image with
no page geometry stays a stacked figure. Both are deterministic and both leave
a model or theme that does not use them byte-identical.
"""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_BUILDER = (
    Path(__file__).resolve().parents[2]
    / "catalog/skills/specialized-domains/document-to-interactive-html/scripts/build_presentation.py"
)
_PIXEL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
_FONT_BYTES = b"wOF2-fixture-font-bytes"


def _build(tmp_path: Path, model: dict, theme: dict | None = None) -> tuple[int, str, str]:
    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps(model), encoding="utf-8")
    out = tmp_path / "deck.html"
    argv = [sys.executable, str(_BUILDER), str(model_path), "-o", str(out)]
    if theme is not None:
        brand = tmp_path / "brand" / "brand.json"
        brand.parent.mkdir(exist_ok=True)
        brand.write_text(json.dumps(theme), encoding="utf-8")
        argv += ["--theme", str(brand)]
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
    html = out.read_text(encoding="utf-8") if out.exists() else ""
    return proc.returncode, html, proc.stderr


def _image(alt: str, fraction: float | None) -> dict:
    block = {"type": "image", "data_uri": _PIXEL, "alt": alt}
    if fraction is not None:
        block["page_fraction"] = fraction
    return block


_TEXT_MODEL = {
    "schema_version": 2,
    "title": "Fonts",
    "sections": [{"heading": "One", "kind": "content", "blocks": [{"type": "paragraph", "text": "x"}]}],
}


def _brand_with_font(tmp_path: Path, file_name: str = "BrandSans.woff2") -> dict:
    fonts = tmp_path / "brand" / "fonts"
    fonts.mkdir(parents=True)
    (fonts / "BrandSans.woff2").write_bytes(_FONT_BYTES)
    return {
        "assets_dir": "fonts/",
        "fonts": {
            "heading": '"Brand Sans", system-ui, sans-serif',
            "embed": [{"family": "Brand Sans", "file": file_name, "weight": 700}],
        },
    }


def test_brand_font_is_inlined_without_a_network_reference(tmp_path: Path) -> None:
    code, html, stderr = _build(tmp_path, _TEXT_MODEL, _brand_with_font(tmp_path))

    assert code == 0, stderr
    encoded = base64.b64encode(_FONT_BYTES).decode("ascii")
    assert re.search(
        r'@font-face \{ font-family: "Brand Sans"; src: url\(data:font/woff2;base64,'
        + re.escape(encoded)
        + r'\) format\("woff2"\); font-weight: 700;',
        html,
    )
    head = html.split("</head>", 1)[0]
    assert 'id="nexus-brand-fonts"' in head
    assert not re.search(r"@import|url\(\s*[\"']?(https?:)?//|fonts\.googleapis", html)


def test_theme_without_embed_entries_adds_no_font_block(tmp_path: Path) -> None:
    code, html, stderr = _build(tmp_path, _TEXT_MODEL, {"fonts": {"heading": "Georgia, serif"}})

    assert code == 0, stderr
    assert "@font-face" not in html
    assert "nexus-brand-fonts" not in html


@pytest.mark.parametrize("file_name", ["../outside.woff2", "missing.woff2"])
def test_font_outside_assets_dir_or_missing_fails_closed(tmp_path: Path, file_name: str) -> None:
    (tmp_path / "brand").mkdir()
    (tmp_path / "brand" / "outside.woff2").write_bytes(_FONT_BYTES)
    code, html, stderr = _build(tmp_path, _TEXT_MODEL, _brand_with_font(tmp_path, file_name))

    assert code == 2
    assert "fonts.embed[0].file" in stderr
    assert html == ""


def _gallery_alts(html: str) -> list[list[str]]:
    return [
        re.findall(r'alt="([^"]+)"', match)
        for match in re.findall(r'<div class="gallery">(.*?)</div>', html, flags=re.DOTALL)
    ]


def test_comparable_secondary_images_render_inside_one_gallery(tmp_path: Path) -> None:
    model = {
        "schema_version": 2,
        "title": "Gallery",
        "sections": [{
            "heading": "Screens",
            "kind": "content",
            "blocks": [
                _image("hero", 0.72),
                _image("a", 0.12),
                _image("b", 0.15),
                _image("c", 0.2),
                _image("far", 0.45),
                {"type": "paragraph", "text": "between"},
                _image("lone", 0.1),
                _image("unmeasured-1", None),
                _image("unmeasured-2", None),
            ],
        }],
    }
    code, html, stderr = _build(tmp_path, model)

    assert code == 0, stderr
    # One gallery: the 0.12-0.2 run. The hero, the 0.45 image (more than 2x the
    # run's smallest), the lone image and images without geometry stay stacked.
    assert _gallery_alts(html) == [["a", "b", "c"]]
    for alt in ("hero", "far", "lone", "unmeasured-1", "unmeasured-2"):
        assert f'<figure><img src="{_PIXEL}" alt="{alt}">' in html


def test_gallery_grouping_is_deterministic(tmp_path: Path) -> None:
    model = {
        "schema_version": 2,
        "title": "Gallery",
        "sections": [{"heading": "S", "kind": "content", "blocks": [_image("a", 0.2), _image("b", 0.3)]}],
    }
    first = _build(tmp_path, model)[1]
    second = _build(tmp_path, model)[1]

    assert first == second
    assert _gallery_alts(first) == [["a", "b"]]
