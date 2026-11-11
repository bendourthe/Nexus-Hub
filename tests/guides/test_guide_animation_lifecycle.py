"""The inactive Training canvas must not consume a reading tab's frame budget."""

from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides/website/nexus-hub-guide.html"
TRAINING = GUIDE.parent / "training.html"


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
    """v4.13.10: the Sky Sentinel loop on training.html asks for frames only while a game runs."""
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.add_init_script("""window.gameFrames = 0;
      const raf = window.requestAnimationFrame;
      window.requestAnimationFrame = cb => raf.call(window, t => {
        if (cb.name === 'loop') window.gameFrames++;
        cb(t);
      });""")
    game = "SkySentinel.get('buggy')"
    page.goto(TRAINING.as_uri() + "#review")
    page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.stage() === 'review' && window.SkySentinel")
    page.wait_for_timeout(300)
    before = page.evaluate("gameFrames")
    page.wait_for_timeout(200)
    assert page.evaluate("gameFrames") == before, "a session stage with no running game requests frames"

    page.evaluate("NexusTrainingPage.go('play-buggy')")
    page.wait_for_function("NexusTrainingPage.stage() === 'play-buggy'")
    page.locator('[data-ss-id="buggy"]').scroll_into_view_if_needed()
    page.locator('[data-ss-id="buggy"] .ss-start').click()
    page.wait_for_function(f"{game}.state().tick > 2")
    page.evaluate(f"{game}.pause('manual')")
    before = page.evaluate("gameFrames")
    tick = page.evaluate(f"{game}.state().tick")
    page.wait_for_timeout(200)
    assert page.evaluate("gameFrames") <= before + 1, "a paused game keeps requesting frames"
    assert page.evaluate(f"{game}.state().tick") == tick

    page.evaluate(f"{game}.resume(); {game}.resume()")
    page.wait_for_function("tick => SkySentinel.get('buggy').state().tick > tick", arg=tick)
    start = page.evaluate("[gameFrames, performance.now()]")
    page.wait_for_timeout(500)
    end = page.evaluate("[gameFrames, performance.now()]")
    rate = (end[0] - start[0]) / ((end[1] - start[1]) / 1000)
    assert rate < 75, f"resuming twice started a second loop: {rate:.0f} frames per second"

    page.evaluate("NexusTrainingPage.go('review')")
    # v4.13.10 R3: on one scrolling page, scrolling a game out of view pauses it.
    page.wait_for_function(f"{game}.state().pausedBy === 'offscreen'")
    page.wait_for_timeout(50)
    before = page.evaluate("gameFrames")
    page.wait_for_timeout(200)
    assert page.evaluate("gameFrames") == before, "a game on a hidden stage keeps requesting frames"
    page.evaluate(f"{game}.reset()")
    assert page.evaluate(f"{game}.state().state") == "idle"
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
    # The guardrail ring figure left Home on 2026-11-10; Why Nexus Hub is a benefits summary now.
    page.locator(".ph").scroll_into_view_if_needed()
    page.wait_for_function("document.querySelector('.ph').classList.contains('live')")
    # The mid-task handoff strip (.ph-cut) left Home on 2026-11-10; its animation checks retired with it.
