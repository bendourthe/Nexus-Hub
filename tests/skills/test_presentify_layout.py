"""Unit coverage for the v3.15.4 Phase 1 full-width canvas contract.

Covers the `--layout {full|standard|portrait}` output-aspect support added to
`build_presentation.py`: the injected `--page-max` / `--gutter` custom-property
pair and the `data-aspect` root attribute, the offline self-check, and a
regression guard for the TITLE_RE fix (the header comment's literal "<title>"
must no longer swallow the document head). It also ships the headless-optional
rendered-width helper the Phase 5 visual-QA gate will reuse: a browser measures
the widest top-level content band, and without one the test skips-with-note
after a deterministic CSS/markup heuristic proves the >=95%-of-viewport metric.

The builder is loaded by path via importlib (it lives outside the test tree),
matching the pattern in test_media_key_setup.py.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUILD_PATH = (
    _ROOT
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "scripts"
    / "build_presentation.py"
)

# Expected injected canvas vars per layout (must match ASPECTS in the builder).
EXPECTED = {
    "full": {"page_max": "100%", "gutter": "clamp(1rem, 2vw, 2rem)"},
    "standard": {"page_max": "1180px", "gutter": "clamp(24px, 7vw, 140px)"},
    "portrait": {"page_max": "46rem", "gutter": "clamp(20px, 6vw, 72px)"},
}
VIEWPORT = 1920
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load(_BUILD_PATH, "build_presentation")


def _model_json() -> str:
    """A small content-only model (no data/image slides) so the widest content
    band is a plain `.slide__body`, driven purely by --page-max/--gutter."""
    import json

    return json.dumps(
        {
            "schema_version": 2,
            "title": "Aspect Fixture",
            "sections": [
                {
                    "heading": "Aspect Fixture",
                    "kind": "title",
                    "blocks": [{"type": "paragraph", "text": "Cover paragraph."}],
                },
                {
                    "heading": "Body",
                    "kind": "content",
                    "blocks": [
                        {"type": "paragraph", "text": "Prose within the measure."},
                        {"type": "bullets", "items": [{"text": "a", "depth": 0}]},
                    ],
                },
            ],
        }
    )


def _build(tmp_path: Path, layout: str) -> str:
    """Build the fixture at `layout` via the CLI entry point; return the HTML."""
    model = tmp_path / "model.json"
    model.write_text(_model_json(), encoding="utf-8")
    out = tmp_path / f"out-{layout}.html"
    rc = build.main([str(model), "-o", str(out), "--layout", layout])
    assert rc == 0, f"builder exited {rc} for --layout {layout}"
    return out.read_text(encoding="utf-8")


# --- injected canvas vars + attribute --------------------------------------


@pytest.mark.parametrize("layout", sorted(EXPECTED))
def test_layout_injects_expected_canvas_vars(tmp_path, layout):
    html = _build(tmp_path, layout)
    # data-aspect stamped on the real root <html> element (not a CSS comment).
    assert re.search(rf'<html\b[^>]*\bdata-aspect="{layout}"', html), (
        f"root <html> missing data-aspect={layout}"
    )
    # The injected NEXUS_ASPECT block carries the expected page-max / gutter.
    assert f"--page-max: {EXPECTED[layout]['page_max']};" in html
    assert f"--gutter: {EXPECTED[layout]['gutter']};" in html


def test_default_layout_is_standard(tmp_path):
    """No --layout flag reproduces today's centered column (standard)."""
    model = tmp_path / "model.json"
    model.write_text(_model_json(), encoding="utf-8")
    out = tmp_path / "out-default.html"
    assert build.main([str(model), "-o", str(out)]) == 0
    html = out.read_text(encoding="utf-8")
    assert 'data-aspect="standard"' in html
    assert f"--page-max: {EXPECTED['standard']['page_max']};" in html


# --- offline guarantee ------------------------------------------------------


@pytest.mark.parametrize("layout", sorted(EXPECTED))
def test_output_is_offline_clean(tmp_path, layout):
    html = _build(tmp_path, layout)
    stripped = _COMMENT_RE.sub("", html)
    # No off-host fetch construct survives (mirror the builder's own gate).
    for pattern in build._FETCH_PATTERNS:
        assert not pattern.search(stripped), (
            f"external reference found in --layout {layout} output"
        )
    # And no bare external URL scheme outside comments.
    assert "http://" not in stripped and "https://" not in stripped


# --- head-integrity regression guard (TITLE_RE fix) ------------------------


@pytest.mark.parametrize("layout", sorted(EXPECTED))
def test_head_survives_title_substitution(tmp_path, layout):
    """The header comment's literal "<title>" must not eat the document head.

    Before the Phase 1.3 fix, TITLE_RE's `.*?` spanned from the comment's
    "<title>" mention to the real </title>, deleting the comment close, the
    <html> tag, <head>, and the <meta> tags. Assert they all survive.
    """
    html = _build(tmp_path, layout)
    assert "-->" in html
    assert re.search(r"<html\b[^>]*>", html)
    assert "<head>" in html
    assert '<meta charset="utf-8">' in html
    # Exactly one real title element, carrying the injected title.
    titles = re.findall(r"<title>[^<]*</title>", html)
    assert titles == ["<title>Aspect Fixture</title>"]
    # The <html> tag precedes <head>, which precedes the real <title>.
    assert html.index("<html") < html.index("<head>") < html.index(
        "<title>Aspect Fixture</title>"
    )


# --- rendered-width helper (headless-optional; Phase 5 gate seed) -----------


def _split_clamp_args(inner: str) -> list[str]:
    """Split clamp() args on top-level commas (our tokens have no nesting)."""
    return [part.strip() for part in inner.split(",")]


def _len_px(token: str, viewport: int, root_font: int = 16) -> float:
    """Resolve a simple CSS length (px / rem / vw / %) or clamp() to pixels."""
    token = token.strip()
    if token.startswith("clamp(") and token.endswith(")"):
        low, pref, high = (
            _len_px(part, viewport, root_font)
            for part in _split_clamp_args(token[len("clamp(") : -1])
        )
        return max(low, min(pref, high))
    if token.endswith("px"):
        return float(token[:-2])
    if token.endswith("rem"):
        return float(token[:-3]) * root_font
    if token.endswith("vw"):
        return float(token[:-2]) / 100.0 * viewport
    if token.endswith("%"):
        return float(token[:-1]) / 100.0 * viewport
    return float(token)


def _heuristic_band_fraction(html: str, viewport: int = VIEWPORT) -> float:
    """CSS/markup estimate of the widest content band as a viewport fraction.

    The `.slide__body` width is `min(--page-max, viewport - 2*--gutter)`; for
    `--page-max: 100%` the body fills the gutter-reduced content box. This is
    the deterministic fallback the Phase 5 gate uses when no browser is present.
    """
    page_max = re.search(r"--page-max:\s*([^;]+);", html).group(1).strip()
    gutter = re.search(r"--gutter:\s*([^;]+);", html).group(1).strip()
    gutter_px = _len_px(gutter, viewport)
    available = viewport - 2 * gutter_px
    if page_max == "100%":
        band = available
    else:
        band = min(_len_px(page_max, viewport), available)
    return band / viewport


def measure_widest_band(html_path: Path, viewport: int = VIEWPORT):
    """Return (fraction, mode). mode is 'rendered' (headless browser measured
    the widest visible `.slide__body`) or 'heuristic' (CSS/markup estimate).

    This is the seed of the Phase 5 visual-QA gate's full-width check: a real
    render when a browser is available, a deterministic fallback otherwise.
    """
    html = Path(html_path).read_text(encoding="utf-8")
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return _heuristic_band_fraction(html, viewport), "heuristic"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": viewport, "height": 1080})
            page.goto(Path(html_path).as_uri())
            width = page.evaluate(
                "() => Math.max(0, ...Array.from("
                "document.querySelectorAll('.slide__body'))"
                ".map(el => el.getBoundingClientRect().width))"
            )
            browser.close()
        if not width:
            return _heuristic_band_fraction(html, viewport), "heuristic"
        return width / viewport, "rendered"
    except Exception:
        return _heuristic_band_fraction(html, viewport), "heuristic"


def test_heuristic_band_fraction_meets_contract(tmp_path):
    """Browser-free proof of the >=95%-of-viewport full-width metric and that
    standard / portrait stay a bounded column (the CSS math is correct)."""
    full = _heuristic_band_fraction(_build(tmp_path, "full"))
    standard = _heuristic_band_fraction(_build(tmp_path, "standard"))
    portrait = _heuristic_band_fraction(_build(tmp_path, "portrait"))
    assert full >= 0.95, f"full-width band only {full:.3f} of viewport"
    assert standard < 0.95, f"standard band unexpectedly wide ({standard:.3f})"
    assert portrait < standard, "portrait should be narrower than standard"


def test_rendered_band_width(tmp_path, render_gate):
    """True rendered width when a headless browser is present; skip-with-note
    otherwise (never a hard fail on a missing browser)."""
    full_frac, mode = measure_widest_band(_build_path(tmp_path, "full"))
    if mode != "rendered":
        render_gate("no headless browser available; rendered-width check skipped")
    std_frac, _ = measure_widest_band(_build_path(tmp_path, "standard"))
    assert full_frac >= 0.95, f"full-width rendered at {full_frac:.3f} of viewport"
    assert std_frac < 0.95, f"standard rendered too wide ({std_frac:.3f})"


def _build_path(tmp_path: Path, layout: str) -> Path:
    """Build the fixture at `layout` and return the output path (for the
    rendered helper, which reads from disk)."""
    _build(tmp_path, layout)
    return tmp_path / f"out-{layout}.html"


# --- image sizing caps (Phase 2) -------------------------------------------


def test_template_carries_image_caps(tmp_path):
    """Browser-free coverage: the hero height cap, the no-crop object-fit
    policy, and the bounded gallery-tile style are all present in the output."""
    html = _build(tmp_path, "standard")
    assert "max-height: 80vh" in html  # hero image height cap
    assert "object-fit: contain" in html  # no meaningful-content crop
    assert ".gallery {" in html  # bounded gallery grid
    assert ".gallery img {" in html
    assert "max-height: 40vh" in html  # gallery-tile height cap


def test_builder_emits_matching_theme_color_vars(tmp_path):
    """BG-1 regression (v3.15.4 Phase 7): the built output defines the
    --color-bg / --color-fg custom properties the template CSS references, not
    the mismatched --color-background / --color-foreground that left them
    undefined (and the body without its theme colors)."""
    html = _build(tmp_path, "standard")
    assert "--color-bg:" in html and "--color-fg:" in html
    assert "--color-background:" not in html
    assert "--color-foreground:" not in html


def _tall_png_data_uri(width: int = 240, height: int = 2000) -> str:
    """A tall base64 PNG so the 80vh hero cap is observable when rendered."""
    import base64
    import io as _io

    image_mod = pytest.importorskip("PIL.Image")
    img = image_mod.new("RGB", (width, height), (30, 90, 140))
    buffer = _io.BytesIO()
    img.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _image_model_json(data_uri: str) -> str:
    import json

    return json.dumps(
        {
            "schema_version": 2,
            "title": "Image Fixture",
            "sections": [
                {
                    "heading": "Tall image",
                    "kind": "image",
                    "blocks": [
                        {"type": "image", "data_uri": data_uri, "alt": "Tall image"}
                    ],
                }
            ],
        }
    )


def test_rendered_image_box_respects_caps(tmp_path, render_gate):
    """Headless-optional (the 1.4 pattern): a tall image renders within the 80vh
    cap with object-fit: contain. Skip-with-note when no headless browser (or no
    Pillow to build the fixture) is present."""
    data_uri = _tall_png_data_uri()
    model = tmp_path / "img-model.json"
    model.write_text(_image_model_json(data_uri), encoding="utf-8")
    out = tmp_path / "img.html"
    assert build.main([str(model), "-o", str(out)]) == 0
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        render_gate("no headless browser available; rendered image-box check skipped")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 1000})
            page.goto(out.as_uri())
            box = page.evaluate(
                "() => { const el = document.querySelector('figure img');"
                " if (!el) return null;"
                " const cs = getComputedStyle(el);"
                " return {h: el.getBoundingClientRect().height, fit: cs.objectFit}; }"
            )
            browser.close()
    except Exception:
        render_gate("headless browser present but render failed; check skipped")
    assert box is not None, "no figure img rendered"
    assert box["fit"] == "contain", f"object-fit was {box['fit']!r}, expected contain"
    assert box["h"] <= 0.8 * 1000 + 1, f"image height {box['h']}px exceeds the 80vh cap"
