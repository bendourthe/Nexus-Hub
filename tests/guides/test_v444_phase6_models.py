"""v4.4.4 Phase 6 gates: how a model works, rather than a catalogue of its outputs.

The review asked this scene to teach three things: that a model predicts the next token, that a base
model answers in one pass while a reasoning model prompts itself first, and that models differ in
what they can read and produce. It also asked for one model family per provider with no version
numbers, and for audio to leave the teaching.

The provider list is asserted against a declared table read from each vendor's own documentation on
2026-09-03. It carries no digits on purpose: a family name ages slowly, a version number ages in
weeks, and a static offline file cannot refresh itself.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
STAGED = (
    _ROOT / "docs" / "releases" / "v4" / "v4.4" / "development" / "guide-visual-and-arcade-rebuild" / "assets"
)
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

# provider -> family, read from each vendor's own model documentation on 2026-09-03
DECLARED = {
    "Anthropic": "Claude Fable",
    "OpenAI": "GPT Sol",
    "Google": "Gemini Flash",
    "xAI": "Grok",
}
TIERS = ("Text", "Multimodal", "Omni")


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
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.locator("#fx-model-lifecycle").scroll_into_view_if_needed()
    page.wait_for_timeout(260)
    return ctx, page


def test_one_model_family_per_provider_and_no_version_numbers(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            chips = page.evaluate(
                "() => [...document.querySelectorAll('#fx-model-lifecycle .fx-models li')].map(li => ({"
                "  provider: li.querySelector('b').textContent.trim(),"
                "  family: li.textContent.replace(li.querySelector('b').textContent, '').trim() }))"
            )
            ctx.close()
        finally:
            browser.close()
    assert len(chips) == len(DECLARED), chips
    providers = [c["provider"] for c in chips]
    assert len(set(providers)) == len(providers), f"one family per provider: {providers}"
    for chip in chips:
        assert chip["provider"] in DECLARED, f"undeclared provider: {chip['provider']}"
        assert chip["family"] == DECLARED[chip["provider"]], chip
        assert not re.search(r"\d", chip["family"]), f"a version number came back: {chip}"


def test_the_answer_is_shown_one_token_at_a_time(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const pass = document.querySelector('#fx-model-lifecycle .fx-pass');
                    const chips = [...pass.querySelectorAll('.mx-tok-chip')];
                    return {
                      count: chips.length,
                      seq: chips.map(c => +c.dataset.seq),
                      highlighted: chips.filter(c => c.classList.contains('mx-tok-chip--next')).length,
                      total: window.NexusSeq.state(pass).total,
                      note: pass.querySelector('.fx-pass-note').textContent.toLowerCase(),
                      notes: pass.querySelectorAll('.fx-pass-note').length,
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["count"] >= 6, data
    assert data["seq"] == sorted(data["seq"]) and data["seq"][0] == 1, data["seq"]
    assert data["total"] == data["count"], "every token should be one step"
    assert data["highlighted"] == 1, "exactly one chip marks the token being chosen"
    assert data["notes"] == 1, "the scene carried a leftover note"
    assert "every token already produced" in data["note"], data["note"]
    assert "not a transcript of hidden reasoning" in data["note"], data["note"]


def test_base_and_reasoning_differ_by_the_self_prompt_loop(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            lanes = page.evaluate(
                """() => [...document.querySelectorAll('#fx-model-lifecycle .mx-lane')].map(l => ({
                    tag: l.querySelector('.mx-lane-tag').textContent.trim(),
                    nodes: [...l.querySelectorAll('.mx-node')].map(n => n.textContent.trim()),
                    selfPrompts: l.querySelectorAll('.mx-node--self').length,
                    loops: l.querySelectorAll('.mx-loop').length,
                    why: l.querySelector('.mx-lane-why').textContent.toLowerCase(),
                }))"""
            )
            ctx.close()
        finally:
            browser.close()
    assert len(lanes) == 2, lanes
    base, reason = lanes
    assert base["tag"] == "Base model" and reason["tag"] == "Reasoning model", lanes
    assert base["selfPrompts"] == 0 and base["loops"] == 0, "a base model does not prompt itself"
    assert reason["selfPrompts"] == 1 and reason["loops"] == 1, "the reasoning lane must show the loop"
    assert len(reason["nodes"]) > len(base["nodes"]), "the reasoning path must be longer"
    assert "one pass" in " ".join(base["nodes"]).lower(), base["nodes"]
    assert "prompts itself" in " ".join(reason["nodes"]).lower(), reason["nodes"]
    # the trade-off is stated, not implied
    assert "slower" in reason["why"] and "expensive" in reason["why"], reason["why"]


def test_three_modality_tiers_and_no_audio(playwright_mod, guide_text: str) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const grid = document.querySelector('#fx-model-lifecycle .mx-tiers');
                    const tiers = [...grid.querySelectorAll('.mx-tier')].map(t => ({
                      tag: t.querySelector('.mx-tier-tag').textContent.trim(),
                      io: [...t.querySelectorAll('.mx-tier-io span')].map(s => s.textContent.trim()),
                      media: t.querySelectorAll('.mx-tier-media svg, .mx-tier-media img').length,
                      top: Math.round(t.getBoundingClientRect().top),
                    }));
                    return { columns: getComputedStyle(grid).gridTemplateColumns.trim().split(/\\s+/).length,
                             tiers, audio: document.querySelectorAll('audio, canvas.fx-wave').length };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["columns"] == 3, data
    assert [t["tag"] for t in data["tiers"]] == list(TIERS), data["tiers"]
    assert len({t["top"] for t in data["tiers"]}) == 1, "the three tiers should read as one row at 1440"
    assert data["audio"] == 0, "audio left the teaching, so it must leave the page"
    # the two richer tiers carry the approved media; the text tier carries text
    assert data["tiers"][0]["media"] == 0, data["tiers"][0]
    assert data["tiers"][1]["media"] == 1 and data["tiers"][2]["media"] == 1, data["tiers"]
    for tier in data["tiers"]:
        assert any("in" in item for item in tier["io"]), tier
        assert any("out" in item for item in tier["io"]), tier

    # the audio asset and its engine leave with it, rather than sitting unused
    assert "fx-out-audio" not in guide_text and "canvas.fx-wave" not in guide_text
    assert "data:audio/wav" not in guide_text, "the approved WAV is still embedded"
    assert "initWaveform" not in guide_text, "the waveform engine is still shipped"
    # the two surviving assets must still match the ledger
    image = re.search(r'<span class="mx-tier-media fx-out-media" data-media="image">(<svg[\s\S]*?</svg>)</span>', guide_text)
    assert image, "the multimodal tier lost its approved image"
    staged = (STAGED / "model-output-image.svg").read_text(encoding="utf-8").strip()
    assert hashlib.sha256(image.group(1).encode("utf-8")).hexdigest() == hashlib.sha256(
        staged.encode("utf-8")
    ).hexdigest(), "the inline image no longer matches the approved ledger bytes"
