"""The inactive Training canvas must not consume a reading tab's frame budget."""

from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides/website/nexus-hub-guide.html"


@pytest.fixture
def browser(render_gate):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        render_gate("Playwright is not installed")
        return
    with sync_playwright() as pw:
        try:
            instance = pw.chromium.launch()
        except Exception as error:
            render_gate(f"Chromium is unavailable: {error}")
            return
        yield instance
        instance.close()


def test_game_sleeps_and_resumes_without_duplicate_frame_loops(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.add_init_script("""window.gameFrames = 0;
      const raf = window.requestAnimationFrame;
      window.requestAnimationFrame = cb => raf.call(window, t => {
        if (cb.name === 'frame') window.gameFrames++;
        cb(t);
      });""")
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_timeout(300)
    before = page.evaluate("gameFrames")
    page.wait_for_timeout(150)
    assert page.evaluate("gameFrames") == before
    page.evaluate("location.hash = 'training/describe'")
    page.locator("[data-arcade-game]").scroll_into_view_if_needed()
    page.locator("[data-arcade-start]").click()
    page.wait_for_function("NexusShooter.snapshot().tick > 2")
    page.evaluate("NexusShooter.pause('manual')")
    before = page.evaluate("gameFrames")
    tick = page.evaluate("NexusShooter.snapshot().tick")
    page.wait_for_timeout(150)
    assert page.evaluate("gameFrames") == before
    assert page.evaluate("NexusShooter.snapshot().tick") == tick
    page.evaluate("NexusShooter.resume('manual'); NexusShooter.resume('manual')")
    page.wait_for_function("tick => NexusShooter.snapshot().tick > tick", arg=tick)
    page.evaluate("location.hash = 'foundations'")
    page.wait_for_function("NexusShooter.snapshot().pauseReasons.includes('offscreen')")
    before = page.evaluate("gameFrames")
    page.wait_for_timeout(150)
    assert page.evaluate("gameFrames") == before
    page.evaluate("NexusShooter.reset()")
    assert page.evaluate("NexusShooter.snapshot().lifecycle") == "idle"
    page.wait_for_timeout(150)
    assert page.evaluate("gameFrames") == before


def test_harness_text_stays_visible_when_sequence_resets_and_motion_is_reduced(browser):
    page = browser.new_page(viewport={"width": 420, "height": 900})
    page.goto(GUIDE.as_uri() + "#foundations")
    page.evaluate("NexusSeq.reset(document.querySelector('#hx-harness'))")
    assert page.locator(".hxf-step").evaluate_all(
        "els => els.every(el => getComputedStyle(el).opacity === '1')"
    )
    page.emulate_media(reduced_motion="reduce")
    page.locator("#fx-tokens").scroll_into_view_if_needed()
    assert page.locator('[data-image-stage="tokens"] .fx-tokcell-edge').evaluate_all(
        "els => els.every(el => getComputedStyle(el).animationName === 'none')"
    )


def test_home_diagrams_keep_examples_visible_and_pause_decorative_motion(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(GUIDE.as_uri() + "#home")
    assert page.locator(".ph-dot").count() == 0
    logo = page.locator('.gf-logo')
    assert logo.evaluate("e => getComputedStyle(e).animationPlayState") == "paused"
    logo.scroll_into_view_if_needed()
    page.wait_for_function("document.querySelector('.guard-fig').classList.contains('live')")
    assert logo.evaluate("e => getComputedStyle(e).animationPlayState") == "running"
    assert logo.evaluate("e => getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)"
    page.emulate_media(reduced_motion="reduce")
    assert logo.evaluate("e => getComputedStyle(e).animationName") == "none"
    page.emulate_media(reduced_motion="no-preference")

    handoff = page.locator(".ph-cut")
    assert handoff.evaluate("e => getComputedStyle(e, '::before').animationName") == "none"
    page.evaluate("NexusSeq.reset(document.querySelector('#nhg-guard-fig'))")
    assert page.locator(".gf-lane").evaluate_all(
        "els => els.length === 3 && els.every(e => getComputedStyle(e).opacity === '1')"
    )
    page.locator(".ph").scroll_into_view_if_needed()
    page.wait_for_function("document.querySelector('.ph').classList.contains('live')")
    assert handoff.evaluate("e => getComputedStyle(e, '::before').animationName") == "none"
    assert handoff.evaluate("e => getComputedStyle(e, '::before').transform") == "none"
    # Exercise the visibility-event branch without relying on headless tab occlusion.
    page.evaluate("""Object.defineProperty(document, 'hidden', {value: true, configurable: true});
      document.dispatchEvent(new Event('visibilitychange'));""")
    assert handoff.evaluate("e => getComputedStyle(e, '::before').animationName") == "none"
    page.evaluate("""delete document.hidden;
      document.dispatchEvent(new Event('visibilitychange'));""")
    assert handoff.evaluate("e => getComputedStyle(e, '::before').animationName") == "none"
    page.emulate_media(reduced_motion="reduce")
    assert handoff.evaluate("e => getComputedStyle(e, '::before').animationName") == "none"
    assert page.locator(".gf-cell--ask").first.evaluate(
        "e => getComputedStyle(e, '::after').animationName"
    ) == "none"
