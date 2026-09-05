"""Behavioral gates for the Models learning lab, replacing the retired eight-stage scene."""

from pathlib import Path
import re

import pytest
from playwright.sync_api import expect, sync_playwright

GUIDE = Path(__file__).resolve().parents[2] / "guides/website/nexus-hub-guide.html"
MODES = ("language", "diffusion", "world", "omni")


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        instance = pw.chromium.launch()
        yield instance
        instance.close()


def open_scene(browser, width=1440, motion="reduce", theme="dark", **options):
    page = browser.new_page(viewport={"width": width, "height": 1000}, reduced_motion=motion, **options)
    page.goto(GUIDE.as_uri() + "#foundations")
    page.evaluate("t => document.documentElement.dataset.theme=t", theme)
    page.locator(".ml-lab").scroll_into_view_if_needed()
    return page


@pytest.mark.parametrize("theme", ("dark", "light"))
@pytest.mark.parametrize("width", (320, 420, 768, 1024, 1440))
def test_all_modes_fit_and_keep_their_text_readable(browser, width, theme):
    page = open_scene(browser, width=width, theme=theme)
    errors, requests = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: requests.append(request.url) if request.url.startswith("http") else None)
    heights = []
    for mode in MODES:
        page.locator(f"[data-mode={mode}]").click()
        panel = page.locator(f"#ml-{mode}")
        expect(panel).to_be_visible()
        expect(page.locator(".ml-panel:visible")).to_have_count(1)
        geometry = panel.evaluate("""panel => ({
            pageOverflow: document.documentElement.scrollWidth > innerWidth + 1,
            clipped: [...panel.querySelectorAll('*')].filter(e => !(e instanceof SVGElement)
                && e.clientWidth && (e.scrollWidth > e.clientWidth + 2 ||
                (getComputedStyle(e).overflow === 'hidden' && e.scrollHeight > e.clientHeight + 2)))
                .map(e => e.className),
            height: panel.querySelector('.ml-board').getBoundingClientRect().height
        })""")
        assert not geometry["pageOverflow"] and not geometry["clipped"], geometry
        heights.append(geometry["height"])
        expect(panel).to_have_attribute("data-frame", "5")
        assert panel.locator(".ml-status").inner_text().strip()
    assert max(heights) - min(heights) <= 1
    assert not errors and not requests
    page.close()


def test_keyboard_tabs_follow_focus_and_aria_contract(browser):
    page = open_scene(browser)
    tab = page.locator("#ml-tab-language")
    tab.focus()
    for key, mode in (("ArrowRight", "diffusion"), ("End", "omni"), ("ArrowRight", "language"), ("ArrowLeft", "omni"), ("Home", "language")):
        page.keyboard.press(key)
        selected = page.locator(f"#ml-tab-{mode}")
        expect(selected).to_be_focused()
        expect(selected).to_have_attribute("aria-selected", "true")
        expect(page.locator(".ml-tabs [tabindex='0']")).to_have_count(1)
        expect(page.locator(f"#ml-{mode}")).to_be_visible()
        assert selected.get_attribute("aria-controls") == f"ml-{mode}"
    page.close()


@pytest.mark.parametrize("mode", MODES)
def test_finite_animation_replays_and_cancels_when_leaving(browser, mode):
    page = open_scene(browser, motion="no-preference")
    page.locator(f"[data-mode={mode}]").click()
    panel = page.locator(f"#ml-{mode}")
    panel.locator("[data-run]").click()
    expect(panel).to_have_attribute("data-frame", "0")
    if mode == "diffusion":
        assert panel.locator(".ml-noise").evaluate("e => +getComputedStyle(e).opacity") == 1
    expect(panel).to_have_attribute("data-frame", "2", timeout=2500)
    if mode == "language":
        expect(page.locator("#ml-tokens")).to_have_text("The sky")
        scores = panel.locator(".ml-prob>div>span").all_text_contents()
        assert sum(int(value.rstrip("%")) for value in scores) == 100
    if mode == "diffusion":
        assert 0 < panel.locator(".ml-noise").evaluate("e=>+getComputedStyle(e).opacity") < 1
    if mode == "world":
        assert panel.locator(".ml-next-world").evaluate("e=>getComputedStyle(e).transform") != "none"
    expect(panel).to_have_attribute("data-frame", "5", timeout=4500)
    expect(panel).not_to_have_class(re.compile("ml-playing"))
    panel.locator("[data-run]").click()
    expect(panel).to_have_attribute("data-frame", "0")
    page.locator("a[href='#home']").first.click()
    expect(panel).not_to_have_class(re.compile("ml-playing"))
    expect(panel).to_have_attribute("data-frame", "5")
    page.wait_for_timeout(850)
    expect(panel).to_have_attribute("data-frame", "5")
    page.close()


def test_offscreen_and_live_reduced_motion_stop_work(browser):
    page = open_scene(browser, motion="no-preference")
    panel = page.locator("#ml-language")
    panel.locator("[data-run]").click()
    expect(panel).to_have_attribute("data-frame", "0")
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    expect(panel).not_to_have_class(re.compile("ml-playing"))
    expect(panel).to_have_attribute("data-frame", "5")
    panel.locator("[data-run]").click()
    page.emulate_media(reduced_motion="reduce")
    expect(panel).to_have_attribute("data-frame", "5")
    expect(panel).not_to_have_class(re.compile("ml-playing"))
    page.close()


def test_capability_and_effort_are_independent_and_reach_a_response(browser):
    page = open_scene(browser)
    for tier in range(4):
        page.locator(f"[data-tier='{tier}']").click()
        for effort in range(4):
            page.locator(f"[data-effort='{effort}']").click()
            expect(page.locator(f"[data-tier='{tier}']")).to_have_attribute("aria-pressed", "true")
            expect(page.locator(f"[data-effort='{effort}']")).to_have_attribute("aria-pressed", "true")
            expect(page.locator(".ml-tier-list [aria-pressed=true]")).to_have_count(1)
            expect(page.locator(".ml-efforts [aria-pressed=true]")).to_have_count(1)
            family = page.locator(f"[data-tier='{tier}'] span").inner_text().split()[0]
            level = page.locator(f"[data-effort='{effort}']").inner_text()
            assert family in page.locator("#ml-selection").inner_text()
            assert level in page.locator("#ml-effort-note").inner_text()
    page.locator("#ml-send").click()
    expect(page.locator("#ml-send-result")).to_contain_text("Response:")
    page.close()


def test_default_is_compact_and_heading_matches_foundations(browser):
    page = open_scene(browser)
    scene = page.locator("#fx-model-lifecycle")
    assert len(scene.inner_text().split()) < 420
    assert scene.bounding_box()["height"] < 1800
    style = page.evaluate("""() => ['#fx-model-lifecycle .fx-subtitle','#fx-agent-platform .fx-subtitle'].map(s => {
        const c=getComputedStyle(document.querySelector(s));return [c.fontSize,c.fontWeight,c.color,c.lineHeight];})""")
    assert style[0] == style[1]
    page.close()


def test_without_javascript_every_explanation_is_available(browser):
    page = browser.new_page(java_script_enabled=False, viewport={"width": 420, "height": 900})
    page.goto(GUIDE.as_uri() + "#foundations")
    for mode in MODES:
        expect(page.locator(f"#ml-{mode}")).to_be_visible()
    expect(page.locator(".ml-run:visible")).to_have_count(0)
    assert page.locator(".ml-panel").count() == 4
    page.close()


def test_teaching_distinguishes_training_prediction_and_effort():
    html = GUIDE.read_text(encoding="utf-8")
    scene = re.search(r'<section[^>]+id="fx-model-lifecycle"[\s\S]*?</section>', html).group()
    text = re.sub(r"<[^>]+>", " ", scene).lower()
    for concept in ("neural network", "does not retrain", "token", "noise", "scene and an action", "multimodal", "internal tokens", "not a fixed number of loops", "not live ai or private thoughts"):
        assert concept in text, concept
    assert 'class="fx-cycle"' not in html
    assert 'data-grammar="work-cycle"' not in html
    assert '<audio' not in scene  # The voice diagram is explicitly illustrated, not a broken player.
