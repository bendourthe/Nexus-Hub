"""Exercise retained brand, navigation, scaling and native scrolling boundaries."""

import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"
sys.path.insert(0, str(BUNDLE / "scripts"))
dual = importlib.import_module("dual_view")


@pytest.fixture
def handbook(tmp_path):
    shutil.copytree(
        ROOT / "tests/fixtures/interactive-handbooks", tmp_path, dirs_exist_ok=True
    )
    model = json.loads((tmp_path / "model.json").read_text(encoding="utf-8"))
    model["sections"][1]["fragment"] = "agenda.html"
    links = "".join(
        f'<a href="#{key}">{key.title()}</a><a role="button" href="#slide-{index + 3}" data-dv-chapter="{key}">Present {key}</a>'
        for index, key in enumerate(model["design"]["agenda"])
    )
    (tmp_path / "agenda.html").write_text(
        '{{unit:agenda-text}}<div role="navigation" aria-label="Source agenda">'
        + links
        + "</div>",
        encoding="utf-8",
    )
    (tmp_path / "model.json").write_text(json.dumps(model), encoding="utf-8")
    dual.assemble(tmp_path / "model.json", tmp_path / "handbook.html")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.add_init_script(
            "document.documentElement.requestFullscreen=()=>Promise.reject(new Error('fitted test'))"
        )
        page.goto((tmp_path / "handbook.html").as_uri())
        yield page, model
        browser.close()


def test_authored_agenda_alias_and_global_entry_keep_distinct_targets(handbook):
    page, model = handbook
    agenda = page.locator(
        '[data-dv-page] [role="navigation"][aria-label="Source agenda"]'
    )
    assert (
        agenda.locator("a:not([role])").evaluate_all("xs=>xs.map(x=>x.hash.slice(1))")
        == model["design"]["agenda"]
    )
    assert (
        page.locator("#calibration").evaluate("x=>x.closest('section').id")
        == "acquisition"
    )
    themes = page.locator("[data-dv-section]").evaluate_all(
        "xs=>xs.map(x=>x.dataset.theme)"
    )
    assert themes == ["dark", "light"] * 3
    agenda.get_by_role("button", name="Present review", exact=True).click()
    assert page.evaluate("NexusDualView.snapshot().index") == 4
    page.keyboard.press("Escape")
    page.locator("[data-dv-open]").last.click()
    assert page.evaluate("NexusDualView.snapshot().index") == 0


def test_original_brand_geometry_and_controls_survive_every_theme(handbook):
    page, model = handbook
    for index, theme in enumerate(model["presentation"]["theme_sequence"]):
        page.evaluate("i=>NexusDualView.open(i)", index)
        slide = page.locator("[data-dv-slide]:visible")
        mark = slide.locator(".dv-brand svg")
        assert mark.get_attribute("viewBox") == "0 0 240 60"
        assert mark.locator("path").get_attribute("d") == "M30 2L58 52H2Z"
        assert mark.locator("text").text_content() == "ASTER"
        assert mark.locator("text").get_attribute("font-family") == "sans-serif"
        assert mark.locator("path").get_attribute("fill") == (
            "#ffd27d" if theme == "dark" else "#15283c"
        )
        bounds = mark.bounding_box()
        assert bounds["width"] / bounds["height"] == pytest.approx(4)
        heading = slide.locator("h2").evaluate(
            "x=>{const r=document.createRange();r.selectNodeContents(x);const b=r.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height}}"
        )
        assert (
            heading["x"] + heading["width"] <= bounds["x"]
            or heading["y"] + heading["height"] <= bounds["y"]
            or heading["y"] >= bounds["y"] + bounds["height"]
        )
        for icon in page.locator("[data-dv-controls] button:not(:disabled) svg").all():
            assert icon.bounding_box()["width"] >= 18
            assert icon.evaluate("x=>getComputedStyle(x).stroke") != "none"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_native_directory_scroll_and_forced_colors_remain_usable(handbook, theme):
    page, _ = handbook
    page.evaluate("NexusDualView.open(5)")
    page.evaluate(
        "theme=>{document.querySelector('[data-dv-deck]').dataset.theme=theme;document.querySelector('[data-dv-slide]:not([hidden])').dataset.theme=theme}",
        theme,
    )
    region = page.locator("[data-dv-slide]:visible [data-dv-native]").first
    assert region.count() == 1
    region.evaluate("x=>{x.style.height='60px';x.tabIndex=0}")
    region.focus()
    page.keyboard.press("End")
    expect(region).to_be_focused()
    assert page.evaluate("NexusDualView.snapshot().index") == 5
    page.wait_for_function(
        "document.querySelector('[data-dv-slide]:not([hidden]) [data-dv-native]').scrollTop > 0"
    )
    assert region.evaluate("x=>getComputedStyle(x).scrollbarWidth") != "none"
    assert region.evaluate("x=>getComputedStyle(x).scrollbarColor").endswith(
        "rgba(0, 0, 0, 0)"
    )
    page.emulate_media(forced_colors="active")
    assert region.evaluate("x=>getComputedStyle(x).scrollbarColor") == "auto"
    region.evaluate("x=>x.scrollTop=0")
    region.hover()
    page.mouse.wheel(0, 300)
    page.wait_for_function(
        "document.querySelector('[data-dv-slide]:not([hidden]) [data-dv-native]').scrollTop > 0"
    )


def test_live_resize_and_supported_visual_scale_preserve_active_slide(handbook):
    page, _ = handbook
    page.evaluate("NexusDualView.open(0)")
    session = page.context.new_cdp_session(page)
    for width, height in [
        (1920, 1080),
        (761, 900),
        (760, 900),
        (390, 844),
        (1366, 768),
    ]:
        page.set_viewport_size({"width": width, "height": height})
        assert page.evaluate("innerWidth") == width
        assert page.evaluate("NexusDualView.snapshot().index") == 0
        stage = page.locator(".dv-stage")
        assert stage.evaluate("x=>x.scrollWidth<=x.clientWidth+1")
        if width > 760:
            assert stage.evaluate("x=>x.scrollHeight<=x.clientHeight+1")
    session.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 1.25})
    assert page.evaluate("visualViewport.scale") == pytest.approx(1.25)
    session.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 1})
    page.get_by_role("button", name="Next", exact=True).click()
    assert page.evaluate("NexusDualView.snapshot().index") == 1
    session.detach()


@pytest.mark.parametrize("broken", [False, True])
def test_retained_wave_covers_canvas_at_both_motion_extremes(tmp_path, broken):
    wave = (ROOT / "tests/fixtures/interactive-handbooks/wave.svg").read_text(
        encoding="utf-8"
    )
    if broken:
        wave = wave.replace('viewBox="0 0 1600 100"', 'viewBox="0 0 2000 100"')
    path = tmp_path / "wave.html"
    path.write_text(
        '<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<style>body{margin:0}svg{display:block;width:100%;height:100px;overflow:hidden}</style>"
        + wave,
        encoding="utf-8",
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        for width in [390, 1366, 2560]:
            page.set_viewport_size({"width": width, "height": 768})
            page.goto(path.as_uri())
            page.evaluate(
                "window.waveMotion=document.querySelector('path').animate("
                "[{transform:'translateX(-20px)'},{transform:'translateX(20px)'}],"
                "{duration:1000,fill:'both'});waveMotion.pause()"
            )
            for time in [0, 500, 1000]:
                page.evaluate("t=>waveMotion.currentTime=t", time)
                bounds = page.locator("path").bounding_box()
                covers = bounds["x"] <= 0 and bounds["x"] + bounds["width"] >= width
                assert covers is not broken
        browser.close()
