"""v4.4.3 Phase 5 gates: Models -- no ring, motion that plays itself, live connectors.

v4.4.4 rebuilt this scene around how a model works, so two tests here were superseded rather than
repointed: the three-step block became a token strip plus base-and-reasoning lanes, and the provider
list became one family per provider without version numbers. Both are asserted in
`test_v444_phase6_models.py`; keeping thin duplicates here would have meant two places to update and
one of them going stale.

The tests that remain still hold their own rules: the ring cannot return, the video plays unaided,
the worked example runs the length of the scene, and the connectors are thick enough to read.

The review named four things in this scene. The spinning ring depicted nothing and its own caption
had to admit it, so it is gone and the test asserts the absence rather than a tuned version of it.
The video needed no press. The connectors were too faint to read. And the worked example was a
document summary, which is not where agentic AI earns its keep.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

# v4.4.4 moved the provider list to one family per provider with no version numbers, and its
# declared table now lives in `test_v444_phase6_models.py`. Nothing in this module reads it.


def _load_sync_playwright():
    """Return playwright's sync entry point, or None when the package is absent."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        return None
    return sync_playwright


@pytest.fixture(scope="module")
def playwright_mod():
    sync_playwright = _load_sync_playwright()
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


@pytest.fixture(scope="module")
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def _scene(browser, width: int = 1440):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusFit && window.NexusSeq && window.NexusFlow")
    page.locator("#fx-model-lifecycle").scroll_into_view_if_needed()
    page.wait_for_timeout(260)
    return ctx, page


def test_no_work_cycle_ring_survives_anywhere_in_a_scene(guide_text: str) -> None:
    fx = guide_text[guide_text.index('id="page-foundations"') : guide_text.index('id="page-training"')]
    assert 'class="fx-cycle"' not in fx, "the ring came back into a Foundations scene"
    assert 'data-grammar="work-cycle"' not in guide_text, "the ring grammar is retired"
    # v4.4.4 retired the platform scene's flow, so the motif belongs to the Models scene alone.
    assert guide_text.count('data-grammar="one-pass"') == 1, "the motif belongs to the Models scene"
    # The CSS that spun it, and the reduced-motion state it needed, go with it.
    assert ".js .fx-scene.live .fx-cycle svg" not in guide_text
    assert "nhg-cycle-spin 6s" not in guide_text


def test_the_video_output_plays_without_being_asked(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const img = document.querySelector('.fx-out-motion');
                    return { src: img.src.slice(0, 20), state: img.getAttribute('data-motion-state'),
                             hasPoster: !!img.getAttribute('data-poster-src'),
                             controls: document.querySelectorAll('[data-media-toggle]').length,
                             /* v4.4.4: the video sits in the omni modality tier now. */
                             label: img.closest('.mx-tier').querySelector('.mx-tier-tag').textContent.trim() };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["src"].startswith("data:image/gif"), data
    assert data["state"] == "playing", data
    assert data["controls"] == 0, "a control is back on the motion output"
    assert data["hasPoster"], "the still frame must stay available for reduced motion"
    assert data["label"] == "Omni", data


def test_the_worked_example_runs_the_length_of_the_scene(playwright_mod) -> None:
    """One example, from the prompt to the text output, and it is a build task."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => ({
                    prompt: document.querySelector('#fx-model-lifecycle .fx-ctx-query p').textContent.trim(),
                    text: document.querySelector('#fx-model-lifecycle .fx-out-text p').textContent.trim(),
                })"""
            )
            ctx.close()
        finally:
            browser.close()
    assert "rate limiting" in data["prompt"].lower(), data["prompt"]
    assert "tests" in data["prompt"].lower(), data["prompt"]
    assert "limiter" in data["text"].lower(), data["text"]
    for stale in ("contract", "deadline"):
        assert stale not in (data["prompt"] + data["text"]).lower(), data


def test_connectors_are_thick_enough_to_read(playwright_mod, guide_text: str) -> None:
    stroke = re.search(r"\.fxp \{[^}]*stroke-width:\s*([0-9.]+)", guide_text)
    assert stroke and float(stroke.group(1)) >= 2.0, "the base connector is still hairline"
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            heads = page.evaluate(
                """() => [...document.querySelectorAll('#fx-model-lifecycle svg.fx-flow-overlay path.fx-head')]
                     .map(h => { const b = h.getBBox(); return {w: +b.width.toFixed(1), h: +b.height.toFixed(1)}; })"""
            )
            ctx.close()
        finally:
            browser.close()
    assert heads, "no flow arrowheads were drawn"
    for head in heads:
        assert head["w"] >= 14, f"arrowhead too small to read: {head}"
        assert head["h"] >= 8, f"arrowhead too small to read: {head}"
