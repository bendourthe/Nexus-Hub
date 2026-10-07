"""v4.13.10 R34: the reward presents Nexus AI Studio as a live app.

After the Nexus boss falls, the reward panel plays an animated mockup of the Nexus AI Studio
window (its title bar, its Chatbot / Agents / Images / Videos sidebar, and its composer with a
model picker). The loop shows chat, agentic work credited to the Nexus Hub harness, image
generation, and video generation, each on a named local model. These checks guard the order of
the scenes, the local and harness labels, the layout at desktop and phone widths, the reduced
motion still frame, and that the loop only runs while the panel is on screen.

Browser tests skip when Playwright or Chromium is missing, and fail closed under
NEXUS_REQUIRE_RENDER=1 so CI cannot silently lose coverage.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

SCENES = ["chat", "agents", "images", "videos"]
PAGES = ["Chatbot", "Agents", "Images", "Videos"]
# Model names as the Nexus AI catalog lists them; every one runs on the device.
LOCAL_MODELS = {"Gemma 4 12B", "Qwen3-Coder 30B-A3B", "SANA 1.5 1.6B 1024px", "Wan 2.2 TI2V 5B"}

DEFEAT_BOSS = """() => { const g = SkySentinel.get('fixed'); SkySentinel.manual(true);
  g.configure({ level: 3, bossNow: true }); g.start(); g.step(600);
  g.defeatBoss(); SkySentinel.manual(false); }"""

# What a reader sees at one moment: the active pane, its labels, and any layout fault.
VIEW = """() => {
  const w = document.querySelector('.nxs'), log = w.querySelector('.nxs-log');
  const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  const scene = w.querySelector('.nxs-scene.is-on');
  const lb = log.getBoundingClientRect(), wb = w.getBoundingClientRect();
  const scrollers = [...w.querySelectorAll('*')].filter(e => /auto|scroll/.test(getComputedStyle(e).overflowX + getComputedStyle(e).overflowY));
  const clipped = [...scene.children].filter(e => vis(e) && e.getBoundingClientRect().bottom > lb.bottom + 1);
  const small = [...w.querySelectorAll('*')].filter(e => vis(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())
    && parseFloat(getComputedStyle(e).fontSize) < 11);
  const meta = [...scene.querySelectorAll('.nxs-meta')].filter(vis).map(e => e.innerText);
  return {
    scene: scene.getAttribute('data-s'), nav: w.querySelector('.nxs-nav .is-on').textContent.trim(),
    page: w.querySelector('.nxs-page-name').innerText, model: w.querySelector('.nxs-model-name').innerText,
    modelVisible: vis(w.querySelector('.nxs-model-name')), local: w.querySelector('.nxs-local').innerText,
    localVisible: vis(w.querySelector('.nxs-local')), meta,
    harness: vis(scene.querySelector('.nxs-hub-badge')) ? scene.querySelector('.nxs-hub-badge').innerText : '',
    scrollers: scrollers.length, clipped: clipped.map(e => e.className), small: small.map(e => e.className),
    overflowX: document.documentElement.scrollWidth - innerWidth, right: wb.right - innerWidth,
    headings: document.querySelectorAll('.nxs h1, .nxs h2, .nxs h3, .nxs h4, [role=heading]').length };
}"""


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        sync_playwright = None
    if sync_playwright is None:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
    except Exception as exc:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
        pytest.skip(f"chromium is unavailable: {exc}")
    return sync_playwright


def _reward(pw, width: int, height: int, motion: str = "no-preference"):
    """Open the fixed game, defeat the boss the way the page tests do, and wait for the reward."""
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion=motion)
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(TRAINING.as_uri() + "#play-fixed")
    page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.stage() !== null && window.NexusTrainingReward")
    page.evaluate(DEFEAT_BOSS)
    page.wait_for_function("NexusTrainingPage.reward()")
    page.wait_for_timeout(700)
    return browser, page, errors


def _seek(page, scene: int, ms: int):
    page.evaluate(f"NexusTrainingReward.seek({scene} * NexusTrainingReward.scene + {ms})")
    page.wait_for_timeout(350)
    return page.evaluate(VIEW)


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_the_four_pillars_play_in_order_on_local_models(playwright_mod, width: int, height: int) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _reward(pw, width, height)
        try:
            assert page.evaluate("NexusTrainingReward.scenes") == SCENES
            seen = []
            for k in range(4):
                start = _seek(page, k, page.evaluate("NexusTrainingReward.marks.focus"))
                end = _seek(page, k, page.evaluate("NexusTrainingReward.scene") - 150)
                for view in (start, end):
                    assert view["scene"] == SCENES[k] and view["nav"] == PAGES[k] and view["page"] == PAGES[k], view
                    assert view["model"] in LOCAL_MODELS and view["modelVisible"], view
                    assert view["localVisible"] and view["local"].startswith("Local"), view
                # The finished answer, plan, picture, or clip is signed by its model and stays on the device.
                assert end["meta"] and all(m.rstrip().endswith("On this device") for m in end["meta"]), end
                assert any(view["model"] in m for m in end["meta"]), end
                seen.append(end["scene"])
            assert seen == SCENES
            models = {page.evaluate(f"NexusTrainingReward.seek({k} * NexusTrainingReward.scene + 5000).model") for k in range(4)}
            assert models == LOCAL_MODELS, "each pillar names its own local model"
            assert not errors, errors
        finally:
            browser.close()


def test_the_agentic_scene_credits_the_nexus_hub_harness(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _reward(pw, 1440, 900)
        try:
            view = _seek(page, 1, 7200)
            assert view["scene"] == "agents" and view["harness"] == "Nexus Hub harness", view
            st = page.evaluate("NexusTrainingReward.state()")
            assert st["harness"] == 3 and st["tools"] == 4 and st["done"], st
            tools = page.locator(".nxs-scene.is-on .nxs-tools code").all_inner_texts()
            assert tools == ["list_directory", "read_file", "edit_file", "write_file"]
            typing = page.evaluate("NexusTrainingReward.seek(NexusTrainingReward.scene + 2000)")
            assert typing["typed"].startswith("/implement") and not typing["sent"], typing
            assert _seek(page, 0, 5000)["harness"] == "", "the harness badge belongs to the agentic scene"
            assert not errors, errors
        finally:
            browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_the_mockup_fits_without_scroll_bars_or_overflow(playwright_mod, width: int, height: int) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _reward(pw, width, height)
        try:
            for k in range(4):
                for ms in (2400, 5200, 7400):
                    view = _seek(page, k, ms)
                    assert view["scrollers"] == 0, ("no scroll bar inside the mockup", view)
                    assert view["clipped"] == [], ("every message fits its pane", k, ms, view)
                    assert view["small"] == [], ("text stays readable", view)
                    assert view["overflowX"] <= 0 and view["right"] <= 0, ("no horizontal overflow", view)
                    assert view["headings"] == 0, "the panel keeps one heading; the mockup adds none"
            assert page.locator(".tr-reward h2").count() == 1
            assert not errors, errors
        finally:
            browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_reduced_motion_holds_one_still_frame(playwright_mod, width: int, height: int) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _reward(pw, width, height, motion="reduce")
        try:
            first = page.evaluate("NexusTrainingReward.state()")
            page.wait_for_timeout(1200)
            assert page.evaluate("NexusTrainingReward.state()") == first, "the frame does not move"
            assert first["scene"] == "agents" and first["done"] and first["sent"], first
            assert page.evaluate("NexusTrainingReward.running()") is False
            assert not page.locator(".nxs-cur").is_visible()
            view = page.evaluate(VIEW)
            assert view["harness"] == "Nexus Hub harness" and view["model"] in LOCAL_MODELS, view
            assert view["clipped"] == [] and view["overflowX"] <= 0, view
            assert not errors, errors
        finally:
            browser.close()


def test_the_loop_runs_only_while_the_panel_is_on_screen(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(TRAINING.as_uri() + "#play-fixed")
            page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.stage() !== null && window.NexusTrainingReward")
            page.wait_for_timeout(400)
            assert page.evaluate("NexusTrainingReward.running()") is False, "a hidden reward does not animate"
            assert page.evaluate("NexusTrainingReward.state().t") == 0
            page.evaluate(DEFEAT_BOSS)
            page.wait_for_function("NexusTrainingPage.reward()")
            page.evaluate("document.querySelector('.nxs').scrollIntoView({ block: 'center' })")
            page.wait_for_function("NexusTrainingReward.state().t > 500", timeout=5000)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
            assert page.evaluate("NexusTrainingReward.running()") is False
            held = page.evaluate("NexusTrainingReward.state().t")
            page.wait_for_timeout(600)
            assert page.evaluate("NexusTrainingReward.state().t") == held, "off screen, the clock stops"
            assert page.evaluate("document.querySelector('.nxs').classList.contains('is-idle')")
        finally:
            browser.close()
