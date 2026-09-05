"""Behavioral gates for the Models learning lab, replacing the retired eight-stage scene."""

from pathlib import Path
import re

import pytest
from playwright.sync_api import expect, sync_playwright

GUIDE = Path(__file__).resolve().parents[2] / "guides/website/nexus-hub-guide.html"
MODES = ("language", "diffusion", "world", "multimodal")


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
    assert min(heights) >= 280  # Outputs can grow naturally; no clipping to force equal heights.
    assert not errors and not requests
    page.close()


def test_keyboard_tabs_follow_focus_and_aria_contract(browser):
    page = open_scene(browser)
    tab = page.locator("#ml-tab-language")
    tab.focus()
    for key, mode in (("ArrowRight", "diffusion"), ("End", "multimodal"), ("ArrowRight", "language"), ("ArrowLeft", "multimodal"), ("Home", "language")):
        page.keyboard.press(key)
        selected = page.locator(f"#ml-tab-{mode}")
        expect(selected).to_be_focused()
        expect(selected).to_have_attribute("aria-selected", "true")
        expect(page.locator(".ml-tabs [tabindex='0']")).to_have_count(1)
        expect(page.locator(f"#ml-{mode}")).to_be_visible()
        assert selected.get_attribute("aria-controls") == f"ml-{mode}"
    page.close()


@pytest.mark.parametrize("mode", MODES)
def test_manual_steps_and_pause_keep_every_demo_inspectable(browser, mode):
    page = open_scene(browser)
    page.locator(f"[data-mode={mode}]").click()
    panel = page.locator(f"#ml-{mode}")
    if mode == "world":
        before = panel.locator(".ml-room > .ml-room-camera").get_attribute("transform")
        source = panel.locator(".ml-room use").get_attribute("href")
    for n in range(6):
        page.get_by_role("button", name="Next step", exact=True).click()
        expect(panel).to_have_attribute("data-frame", str(n))
        expect(panel).not_to_have_class(re.compile("ml-playing"))
        if mode == "language":
            scores = panel.locator(".ml-prob>div>span").all_text_contents()
            assert sum(int(value.rstrip("%")) for value in scores) == 100
        if mode == "diffusion" and n == 0:
            assert panel.locator(".ml-noise").evaluate("e=>+getComputedStyle(e).opacity") == 1
        if mode == "world" and n == 2:
            assert before != panel.locator(".ml-room > .ml-room-camera").get_attribute("transform")
            assert panel.locator(".ml-room use").get_attribute("href") == source
    expect(page.locator("#ml-motion")).to_be_disabled()
    page.close()


def test_language_predictions_repeat_and_pause_without_reset(browser):
    page = open_scene(browser, motion="no-preference")
    page.clock.install()
    page.locator('[data-mode="language"]').click()
    panel = page.locator("#ml-language")
    page.clock.run_for(2500)
    expect(panel).to_have_attribute("data-frame", "1")
    expect(page.locator("#ml-prefix")).to_have_text("Yeast ")
    expect(panel.locator(".ml-prompt")).not_to_contain_text("Yeast")
    expect(page.locator("#ml-prediction")).to_have_text("produces")
    expect(page.locator("#ml-tokens")).to_have_text("Yeast produces")
    page.clock.run_for(12100)
    expect(panel).to_have_attribute("data-frame", "0")
    expect(panel).to_have_class(re.compile("ml-playing"))
    page.get_by_role("button", name="Pause animations").click()
    value = panel.get_attribute("data-frame")
    page.clock.run_for(5000)
    expect(panel).to_have_attribute("data-frame", value)
    expect(panel).not_to_have_class(re.compile("ml-playing"))
    page.get_by_role("button", name="Play animations").click()
    page.clock.run_for(2500)
    assert panel.get_attribute("data-frame") != value
    page.close()


def test_offscreen_routes_and_live_reduced_motion_stop_work(browser):
    page = open_scene(browser, motion="no-preference")
    panel = page.locator("#ml-language")
    page.locator('[data-mode="language"]').click()
    expect(panel).to_have_class(re.compile("ml-playing"))
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    expect(panel).not_to_have_class(re.compile("ml-playing"))
    frame = panel.get_attribute("data-frame")
    page.wait_for_timeout(2600)
    expect(panel).to_have_attribute("data-frame", frame)
    page.locator('.ml-lab').scroll_into_view_if_needed()
    expect(panel).to_have_class(re.compile("ml-playing"))
    page.emulate_media(reduced_motion="reduce")
    expect(panel).to_have_attribute("data-frame", "5")
    expect(panel).not_to_have_class(re.compile("ml-playing"))
    page.emulate_media(reduced_motion="no-preference")
    page.get_by_role("button", name="Play animations").click()
    page.locator("a[href='#home']").first.click()
    expect(page.locator("#fx-model-lifecycle .ml-playing")).to_have_count(0)
    page.close()


def test_capability_and_effort_are_independent_and_explain_the_selection(browser):
    page = open_scene(browser)
    widths = page.locator(".ml-tier-art svg").evaluate_all("es=>es.map(e=>e.getBoundingClientRect().width)")
    assert widths == sorted(widths) and len(set(widths)) == 4
    for tier in range(4):
        button = page.locator(f"[data-tier='{tier}']")
        button.click()
        expect(button).to_contain_text("Anthropic")
        expect(button).to_contain_text("OpenAI")
        for effort in range(4):
            page.locator(f"[data-effort='{effort}']").click()
            expect(button).to_have_attribute("aria-pressed", "true")
            expect(page.locator(f"[data-effort='{effort}']")).to_have_attribute("aria-pressed", "true")
            expect(page.locator(".ml-tier-list [aria-pressed=true]")).to_have_count(1)
            expect(page.locator(".ml-efforts [aria-pressed=true]")).to_have_count(1)
            assert page.locator(f"[data-effort='{effort}']").inner_text() in page.locator("#ml-effort-note").inner_text()
            expect(page.locator(".ml-reason-progress [data-on]")).to_have_count(effort + 1)
    expect(page.locator("#ml-tier-note")).to_contain_text("Frontier")
    expect(page.locator(".ml-send, .ml-think")).to_have_count(0)
    page.close()


def test_higher_effort_allows_more_internal_processing_before_reply(browser):
    page = open_scene(browser, motion="no-preference")
    page.clock.install()
    page.locator('[data-effort="0"]').click()
    page.clock.run_for(2700)
    expect(page.locator("#ml-reason-state")).to_have_text("Ready to reply")
    page.locator('[data-effort="3"]').click()
    page.clock.run_for(2700)
    expect(page.locator("#ml-reason-state")).to_have_text("Compare approaches")
    page.clock.run_for(7200)
    expect(page.locator("#ml-reason-state")).to_have_text("Ready to reply")
    page.close()


def test_default_is_compact_and_heading_matches_foundations(browser):
    page = open_scene(browser)
    scene = page.locator("#fx-model-lifecycle")
    assert len(scene.inner_text().split()) < 420
    assert scene.bounding_box()["height"] < 2100
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
    for concept in ("neural network", "pre-training", "post-training", "reinforcement learning", "weights", "token", "noise", "scene and an action", "multimodal", "internal tokens", "not a fixed number of loops", "not exact model internals or live ai"):
        assert concept in text, concept
    assert 'class="fx-cycle"' not in html
    assert 'data-grammar="work-cycle"' not in html
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(scene, "html.parser")
    architectures = []
    for mode in MODES:
        panel = soup.select_one(f"#ml-{mode}")
        assert "User request" in panel.get_text() and panel.select_one(".ml-board")
        architectures.append(panel.select_one(".ml-network svg use")["href"])
    assert len(set(architectures)) == 4
    multi = soup.select_one("#ml-multimodal")
    assert "voice recording" in multi.select_one(".ml-prompt").get_text()
    assert "Shared learned weights" in multi.get_text()
    assert multi.select_one('.ml-ui-attachment [role="img"]')
    assert 'omni' not in text and 'picnic' not in text
    assert '<audio' not in scene  # The voice diagram is explicitly illustrated, not a broken player.


def test_diffusion_reveals_the_photograph_in_under_four_seconds(browser):
    page = open_scene(browser, motion="no-preference")
    page.clock.install()
    page.locator('[data-mode="diffusion"]').click()
    page.clock.run_for(3300)
    panel = page.locator("#ml-diffusion")
    expect(panel).to_have_attribute("data-frame", "5")
    page.clock.run_for(700)
    expect(panel).to_have_attribute("data-frame", "0")
    page.close()
