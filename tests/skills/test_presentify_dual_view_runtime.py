"""Real browser lifecycle tests for the offline shared presentation runtime."""

from __future__ import annotations

import html
import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"
FIXTURE = ROOT / "tests/fixtures/interactive-handbooks"


def runtime_html(bundle=BUNDLE, total=6):
    """Build an explicit runtime harness; production assembly belongs to Phase 3."""
    data = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))
    slides = []
    for i in range(total):
        key = f"s{i}"
        theme = data["presentation"]["theme_sequence"][i % 6]
        heading = html.escape(data["sections"][i % 6]["heading"])
        slides.append(f'''<section data-dv-slide="{key}" data-theme="{theme}" hidden>
          <h2>{heading}</h2><p>Instrument A: 12. Instrument B: 18.</p>
          <div data-dv-animate="process" data-dv-step="0">Acquire</div>
          <div data-dv-animate="process" data-dv-step="2">Review</div>
          <svg viewBox="0 0 300 50" width="300" height="50" aria-label="Observations">
            <rect data-dv-animate="comparison" data-dv-mark x="0" y="0" width="120" height="20" fill="currentColor"/>
            <rect data-dv-animate="comparison" data-dv-mark x="0" y="28" width="180" height="20" fill="currentColor"/>
          </svg>
          <label>Chart input <input data-dv-native value="12"></label>
          <div data-dv-native tabindex="0" style="max-height:60px"><p style="height:150px">Scrollable directory</p></div>
          <button class="details" onclick="this.nextElementSibling.showModal()">Details</button>
          <dialog><p>Complete detail</p><button onclick="this.closest('dialog').close()">Close detail</button></dialog>
        </section>''')
    icon = (
        '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M8 4L16 12L8 20"/></svg>'
    )
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Runtime specimen</title>
      <style>{(bundle / "assets/dual-view.css").read_text(encoding="utf-8")}</style>
      <main data-dv-page><button data-dv-open id="global">Presentation Mode</button>
        <h1>Aster Observatory</h1><button data-dv-open id="hero">Presentation Mode</button>
        <p style="height:180vh">Detailed reading content remains available without JavaScript.</p>
        <button data-dv-chapter="s3" id="chapter">Present chapter</button>
      </main><p data-dv-status role="status"></p>
      <div data-dv-deck hidden><div class="dv-stage">{"".join(slides)}</div>
        <nav data-dv-controls aria-label="Presentation controls">
          <button data-dv-prev>{icon}Back</button><button data-dv-replay>{icon}Replay</button>
          <span data-dv-count aria-live="polite"></span>
          <select data-dv-picker aria-label="Go to slide"></select>
          <button data-dv-next>{icon}Next</button><button data-dv-fullscreen>{icon}Fullscreen</button>
          <button data-dv-exit>{icon}Exit</button>
        </nav>
      </div><script>{(bundle / "assets/dual-view-runtime.js").read_text(encoding="utf-8")}</script></html>"""


@pytest.fixture
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser, tmp_path):
    path = tmp_path / "runtime.html"
    path.write_text(runtime_html(), encoding="utf-8")
    page = browser.new_page(viewport={"width": 1366, "height": 768})
    page.add_init_script(
        "Element.prototype.requestFullscreen = () => Promise.reject(new Error('denied'))"
    )
    page.goto(path.as_uri())
    yield page
    page.close()


def state(page):
    return page.evaluate("NexusDualView.snapshot()")


def test_entry_reset_chapter_and_exit_restore_reading(page):
    page.locator("#chapter").click()
    assert state(page)["index"] == 3
    page.keyboard.press("Escape")
    assert page.evaluate("document.activeElement.id") == "chapter"
    assert page.evaluate("scrollY") > 100
    page.locator("#global").click()
    assert state(page)["index"] == 0
    page.keyboard.press("End")
    assert state(page)["index"] == 5
    page.locator("[data-dv-exit]").click()
    page.locator("#hero").click()
    assert state(page)["index"] == 0
    assert (
        page.locator("[data-dv-status]")
        .inner_text()
        .startswith("Fullscreen unavailable")
    )


def test_keyboard_priority_focus_trap_and_nested_modal(page):
    page.locator("#hero").click()
    page.locator("[data-dv-slide]:visible input").focus()
    page.keyboard.press("ArrowRight")
    assert state(page)["index"] == 0
    page.locator("[data-dv-exit]").focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.closest('[data-dv-deck]') !== null")
    assert not page.evaluate(
        "document.activeElement.closest('[data-dv-page]') !== null"
    )
    page.locator("[data-dv-slide]:visible .details").click()
    page.keyboard.press("Escape")
    assert state(page)["active"]
    assert page.locator("dialog[open]").count() == 0
    page.keyboard.press("Escape")
    assert not state(page)["active"]


def test_history_deep_links_and_invalid_hash(page):
    page.evaluate("location.hash = 'slide-3'")
    page.wait_for_function("NexusDualView.snapshot().index === 2")
    assert not state(page)["fullscreen"]
    page.keyboard.press("ArrowRight")
    assert state(page)["index"] == 3
    page.go_back()
    page.wait_for_function("NexusDualView.snapshot().index === 2")
    page.evaluate("location.hash = 'slide-999'")
    page.wait_for_function("!NexusDualView.snapshot().active")
    assert page.locator("[data-dv-status]").inner_text().startswith("Unknown slide")


def test_replay_motion_intermediate_and_reduced_motion(page):
    page.locator("#hero").click()
    timing = page.evaluate("""() => [...document.querySelectorAll('[data-dv-slide]:not([hidden]) [data-dv-animate]')].map(e => {
      const a=e.getAnimations()[0]; a.pause(); a.currentTime=100;
      return {delay:a.effect.getTiming().delay, opacity:getComputedStyle(e).opacity, clip:getComputedStyle(e).clipPath};
    })""")
    assert [t["delay"] for t in timing] == [0, 260, 0, 0]
    assert float(timing[1]["opacity"]) == 0
    assert timing[2]["clip"] != "inset(0px)"
    page.locator("[data-dv-replay]").click()
    assert state(page)["animations"] == 4
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_function("NexusDualView.snapshot().animations === 0")
    assert (
        page.locator("[data-dv-slide]:visible [data-dv-step='2']").evaluate(
            "e=>getComputedStyle(e).opacity"
        )
        == "1"
    )
    page.locator("[data-dv-exit]").click()
    assert page.evaluate("document.getAnimations().length") == 0


def test_rapid_actions_theme_stability_and_destroy(page):
    page.evaluate(
        "NexusDualView.open(3); NexusDualView.next(); NexusDualView.close(); NexusDualView.open(3)"
    )
    assert state(page)["index"] == 3
    assert page.locator("[data-dv-deck]").get_attribute("data-theme") == "dark"
    assert page.locator("[data-dv-slide]:visible").count() == 1
    page.evaluate("NexusDualView.destroy()")
    assert not state(page)["active"]
    assert not page.locator("[data-dv-page]").evaluate("e=>e.inert")
    assert page.evaluate("document.getAnimations().length") == 0


@pytest.mark.parametrize("exit_action", ["escape", "button"])
def test_fullscreen_close_restores_entry_focus(browser, tmp_path, exit_action):
    path = tmp_path / "fullscreen-focus.html"
    path.write_text(runtime_html(), encoding="utf-8")
    page = browser.new_page()
    page.goto(path.as_uri())
    page.locator("#chapter").click()
    page.wait_for_function("document.fullscreenElement !== null")
    if exit_action == "escape":
        page.keyboard.press("Escape")
    else:
        page.locator("[data-dv-exit]").click()
    page.wait_for_function("document.fullscreenElement === null")
    page.wait_for_function("document.activeElement.id === 'chapter'", timeout=1500)
    assert not state(page)["active"]
    assert page.evaluate("scrollY") > 100
    page.close()


def test_reopening_during_fullscreen_exit_keeps_new_deck_focus(browser, tmp_path):
    path = tmp_path / "fullscreen-reopen.html"
    path.write_text(runtime_html(), encoding="utf-8")
    page = browser.new_page()
    page.goto(path.as_uri())
    page.locator("#hero").click()
    page.wait_for_function("document.fullscreenElement !== null")
    page.evaluate("NexusDualView.close(); NexusDualView.open(3)")
    page.wait_for_function("document.fullscreenElement === null")
    assert state(page)["active"] and state(page)["index"] == 3
    assert page.evaluate("!!document.activeElement.closest('[data-dv-deck]')")
    page.close()


def test_real_fullscreen_exit_and_explicit_toggle(browser, tmp_path):
    path = tmp_path / "native.html"
    path.write_text(runtime_html(), encoding="utf-8")
    page = browser.new_page()
    page.goto(path.as_uri())
    page.locator("#hero").click()
    page.wait_for_function("document.fullscreenElement !== null")
    page.locator("[data-dv-slide]:visible .details").click()
    assert page.locator("dialog[open]").is_visible()
    page.locator("dialog[open] button").click()
    page.locator("[data-dv-fullscreen]").click()
    page.wait_for_function("document.fullscreenElement === null")
    assert state(page)["active"]
    page.locator("[data-dv-fullscreen]").click()
    page.wait_for_function("document.fullscreenElement !== null")
    page.evaluate("document.exitFullscreen()")
    page.wait_for_function("!NexusDualView.snapshot().active")
    assert page.evaluate("document.activeElement.id") == "hero"
    page.close()


@pytest.mark.parametrize(
    "size",
    [(1366, 768), (1280, 720), (1536, 784), (1920, 850), (1920, 851), (390, 844)],
)
def test_all_slides_fit_declared_viewport(page, size):
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.locator("#hero").click()
    for i in range(6):
        page.evaluate("i=>NexusDualView.open(i)", i)
        bounds = page.locator("[data-dv-slide]:visible").evaluate(
            "e=>({width:e.clientWidth,scrollWidth:e.scrollWidth,height:e.clientHeight,scrollHeight:e.scrollHeight})"
        )
        assert bounds["scrollWidth"] <= bounds["width"] + 1
        if size[0] > 760:
            assert bounds["scrollHeight"] <= bounds["height"] + 1


def test_no_js_print_and_offline(browser, tmp_path):
    path = tmp_path / "detached-renamed.html"
    path.write_text(runtime_html(), encoding="utf-8")
    page = browser.new_page(java_script_enabled=False)
    outbound = []
    page.on(
        "request",
        lambda r: (
            outbound.append(r.url) if r.url.startswith(("http:", "https:")) else None
        ),
    )
    page.goto(path.as_uri())
    assert page.locator("h1").is_visible()
    assert not page.locator("[data-dv-deck]").is_visible()
    assert not page.locator("#hero").is_visible()
    page.emulate_media(media="print")
    assert page.locator("h1").is_visible()
    assert not outbound
    page.close()


def test_long_deck_and_empty_storyboard(browser, tmp_path):
    path = tmp_path / "long.html"
    path.write_text(runtime_html(total=48), encoding="utf-8")
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(path.as_uri())
    page.locator("#hero").click()
    page.keyboard.press("End")
    assert page.locator("[data-dv-count]").inner_text() == "48 / 48"
    assert page.locator("[data-dv-picker] option").count() == 48
    assert page.locator("[data-dv-controls]").evaluate(
        "e=>e.scrollWidth <= e.clientWidth"
    )
    empty = tmp_path / "empty.html"
    empty.write_text(runtime_html(total=0), encoding="utf-8")
    page.goto(empty.as_uri())
    assert not page.locator("#hero").is_visible()
    assert "empty or incomplete" in page.locator("[data-dv-status]").inner_text()
    page.close()


def test_print_from_active_presentation_keeps_reading_content(page):
    page.locator("#hero").click()
    assert state(page)["active"]
    assert not page.locator("[data-dv-page]").is_visible()
    page.emulate_media(media="print")
    assert page.locator("[data-dv-page]").is_visible()
    assert not page.locator("[data-dv-deck]").is_visible()
    page.emulate_media(media="screen")
    assert not page.locator("[data-dv-page]").is_visible()
    assert page.locator("[data-dv-deck]").is_visible()
    page.keyboard.press("Escape")
    assert page.locator("[data-dv-page]").is_visible()


def test_touch_native_region_and_hidden_document_stop_work(page):
    page.locator("#hero").click()
    slide = page.locator("[data-dv-slide]:visible h2")
    slide.dispatch_event(
        "pointerdown",
        {"pointerType": "touch", "pointerId": 1, "clientX": 250, "clientY": 100},
    )
    slide.dispatch_event(
        "pointerup",
        {"pointerType": "touch", "pointerId": 1, "clientX": 50, "clientY": 110},
    )
    assert state(page)["index"] == 1
    native = page.locator("[data-dv-slide]:visible input")
    native.dispatch_event(
        "pointerdown",
        {"pointerType": "touch", "pointerId": 2, "clientX": 250, "clientY": 100},
    )
    native.dispatch_event(
        "pointerup",
        {"pointerType": "touch", "pointerId": 2, "clientX": 50, "clientY": 110},
    )
    assert state(page)["index"] == 1
    page.evaluate(
        "Object.defineProperty(document,'hidden',{value:true,configurable:true}); document.dispatchEvent(new Event('visibilitychange'))"
    )
    assert state(page)["animations"] == 0
    page.evaluate(
        "Object.defineProperty(document,'hidden',{value:false,configurable:true}); document.dispatchEvent(new Event('visibilitychange'))"
    )
    assert state(page)["animations"] == 4


def test_invalid_api_and_reading_animation_are_safe(page):
    page.evaluate("NexusDualView.open(NaN)")
    assert not state(page)["active"]
    page.evaluate(
        "window.readingAnimation=document.querySelector('h1').animate([{opacity:.9},{opacity:1}],{duration:2000,iterations:Infinity})"
    )
    page.locator("#hero").click()
    assert page.evaluate("readingAnimation.playState") == "paused"
    page.locator("[data-dv-exit]").click()
    assert page.evaluate("readingAnimation.playState") == "running"
    page.evaluate("readingAnimation.cancel()")


def test_interrupted_fullscreen_promise_does_not_reopen(page):
    page.evaluate(
        "() => { Element.prototype.requestFullscreen=()=>new Promise(resolve=>window.finishFullscreen=resolve); }"
    )
    page.locator("#hero").click()
    page.locator("[data-dv-exit]").click()
    page.evaluate("finishFullscreen()")
    assert not state(page)["active"]
    assert page.evaluate("document.documentElement.style.overflow") == ""
