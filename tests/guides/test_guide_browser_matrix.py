"""Keep the retained visual matrix aligned with the two-page guide (v4.13.10)."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

MATRIX = Path(__file__).resolve().parent / "tools" / "browser_matrix.py"
STORY = Path(__file__).resolve().parents[2] / "guides" / "website" / "src" / "training-story.json"
SPEC = importlib.util.spec_from_file_location("browser_matrix", MATRIX)
assert SPEC and SPEC.loader
matrix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(matrix)


def test_matrix_stages_exist_in_the_story():
    stage_ids = {s["id"] for s in json.loads(STORY.read_text(encoding="utf-8"))["stages"]}
    assert set(matrix.ROUTES) <= stage_ids
    for cases in matrix.declare_groups().values():
        for case in cases:
            if "stage" in case:
                assert case["stage"] in stage_ids, case["label"]
                assert case["url"].startswith(matrix.TRAINING.as_uri()), case["label"]


def test_matrix_geometry_uses_stage_owned_regions():
    groups = matrix.declare_groups()
    for name in ("fullscreen", "narrow", "short", "zoom"):
        assert groups[name] and all(case["geometry"] for case in groups[name])
    assert "game" in matrix.geometry_regions("play-buggy")
    assert "session" not in matrix.geometry_regions("play-buggy")
    assert {"session", "files", "activity"} <= set(matrix.geometry_regions("review"))
    assert set(matrix.geometry_regions("intro")) == {"banner"}


def test_matrix_no_longer_targets_the_retired_in_guide_training():
    text = MATRIX.read_text(encoding="utf-8")
    for retired in ("#training/", "NexusShooter", "NexusTraining ", "data-nht-section", "data-arcade-"):
        assert retired not in text, retired
    assert "training" not in matrix.PAGES


# --- v4.13.11 WN-1-v4134: the zoom group emulates native browser zoom -----------------------

REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

# A header that is 1000 px wide above 700 px and wraps below it: overflow under a 200%
# CSS zoom that media queries ignore, no overflow under real 200% zoom at 1280 px.
_RESPONSIVE = (
    "<!doctype html><style>body{margin:0}.bar{display:flex;width:1000px}"
    "@media (max-width:700px){.bar{width:auto;flex-wrap:wrap}}</style>"
    "<div class=bar><a>Home</a><a>Training</a><a>Theme</a></div>"
)
# A box no viewport query can shrink: overflow under any 200% zoom at 1280 px.
_RIGID = "<!doctype html><style>body{margin:0}</style><div style='width:900px;height:20px'></div>"


def test_zoom_cases_emulate_native_zoom_through_the_context():
    for case in matrix.declare_groups()["zoom"]:
        opts = matrix.context_options(case)
        assert opts["device_scale_factor"] == case["zoom"] == 2, case["label"]
        assert opts["viewport"] == {"width": case["width"] // 2, "height": case["height"] // 2}, case["label"]
    plain = matrix.context_options({"width": 1440, "height": 900, "theme": "dark"})
    assert plain["viewport"] == {"width": 1440, "height": 900} and plain["device_scale_factor"] == 1
    assert "style.zoom =" not in MATRIX.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def chromium():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - pragma: no cover, environment dependent
            if REQUIRE_RENDER:
                pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
            pytest.skip(f"chromium is unavailable: {exc}")
        yield browser
        browser.close()


def _overflow(browser, html: str) -> bool:
    case = {"width": 1280, "height": 720, "theme": "dark", "zoom": 2}
    ctx = browser.new_context(**matrix.context_options(case))
    page = ctx.new_page()
    page.set_content(html)
    geo = page.evaluate(matrix.GEOMETRY_JS, [{}, []])
    ctx.close()
    return geo["horizontalOverflow"]


def test_native_zoom_lets_media_queries_collapse_the_header(chromium):
    assert _overflow(chromium, _RESPONSIVE) is False


def test_native_zoom_still_catches_real_overflow(chromium):
    assert _overflow(chromium, _RIGID) is True
