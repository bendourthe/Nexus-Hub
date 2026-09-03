"""v4.4.3 Phase 5 gates: Models -- no ring, motion that plays itself, named models, live connectors.

The review named four things in this scene. The spinning ring depicted nothing and its own caption
had to admit it, so it is gone and the test asserts the absence rather than a tuned version of it.
The video needed no press. The connectors were too faint to read. And the worked example was a
document summary, which is not where agentic AI earns its keep.

Model names are asserted against a declared list read from each vendor's own documentation on
2026-09-03. The point of the assertion is that the guide names real released models from more than
one provider, not that these particular names are eternal; a future refresh updates both together.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

# Read from the vendors' own model documentation on 2026-09-03.
DECLARED_MODELS = {
    "Anthropic": ("Claude Opus 5", "Claude Haiku 4.5"),
    "OpenAI": ("GPT-5.6 Sol",),
    "Google": ("Gemini 3.8 Flash",),
}


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
    assert guide_text.count('data-grammar="one-pass"') == 2, "both scenes share the replacement motif"
    # The CSS that spun it, and the reduced-motion state it needed, go with it.
    assert ".js .fx-scene.live .fx-cycle svg" not in guide_text
    assert "nhg-cycle-spin 6s" not in guide_text


def test_inside_the_model_states_three_true_things_with_the_caveat(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const p = document.querySelector('#fx-model-lifecycle .fx-pass');
                    return { steps: [...p.querySelectorAll('.fx-pass-step')].map(s => s.textContent.trim()),
                             effort: [...p.querySelectorAll('.fx-effort-row')].map(r => ({
                               name: r.querySelector('.fx-effort-name').textContent.trim(),
                               w: r.querySelector('.fx-effort-bar').style.getPropertyValue('--w').trim() })),
                             note: p.querySelector('.fx-pass-note').textContent.trim(),
                             seq: window.NexusSeq.state(p).total };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert len(data["steps"]) == 3 and all(data["steps"]), data["steps"]
    assert data["seq"] == 3, data
    assert len(data["effort"]) == 2, data["effort"]
    lo, hi = (int(row["w"].rstrip("%")) for row in data["effort"])
    assert hi > lo, f"higher effort must read as more room: {data['effort']}"
    assert "not a transcript of hidden reasoning" in data["note"], data["note"]
    assert "promises no number of steps" in data["note"], data["note"]


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
                             label: img.closest('.fx-out').querySelector('.fx-out-tag').textContent.trim() };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["src"].startswith("data:image/gif"), data
    assert data["state"] == "playing", data
    assert data["controls"] == 0, "a control is back on the motion output"
    assert data["hasPoster"], "the still frame must stay available for reduced motion"
    assert data["label"] == "Video", data


def test_released_models_are_named_from_three_providers(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            chips = page.evaluate(
                "() => [...document.querySelectorAll('#fx-model-lifecycle .fx-models li')].map(li => ({"
                "  provider: li.querySelector('b').textContent.trim(),"
                "  model: li.textContent.replace(li.querySelector('b').textContent, '').trim() }))"
            )
            ctx.close()
        finally:
            browser.close()
    assert chips, "no released models are named"
    providers = {c["provider"] for c in chips}
    assert len(providers) >= 3, f"at least three providers expected, got {sorted(providers)}"
    for chip in chips:
        declared = DECLARED_MODELS.get(chip["provider"])
        assert declared, f"undeclared provider: {chip['provider']}"
        assert chip["model"] in declared, f"{chip['model']!r} is not in the declared list for {chip['provider']}"


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
