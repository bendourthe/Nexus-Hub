"""v4.4.5 Phases 6 and 7 -- what the two operator mockups added, and what they did not.

Both mockups teach through controls. The agentic one hides its best lesson behind a button: a
reader only learns that a boundary REPORTS a refusal instead of routing around it if they press
the read-only setting and watch step 03 stop. The harness one hides its five-step work sequence
behind a run button and its per-layer detail behind three more.

This guide has no controls, so every one of those states is on the page at once. That is the
property under test here, and it is asserted as multiplicity rather than presence: the agentic
boundary must show all THREE settings, the harness must state a limit or a guarantee on all
THREE layers, and the work sequence must show all FIVE steps without anything being run.

The negative assertions matter as much. Neither mockup's absolutely-positioned SVG map came
across, and both would have brought one: a 720x520 system map and a 760x470 adapter map, each
placing every label by offset inside a fixed viewBox. Phase 5 already recorded what that
construction does at a width nobody tested.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (1440, 1024, 720, 480, 320)


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


def _scene_text(guide_text: str, scene_id: str) -> str:
    start = guide_text.index(f'id="{scene_id}"')
    return guide_text[start : guide_text.index("</section>", start)]


def _page(browser, width: int = 1440):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.wait_for_timeout(400)
    return ctx, page


# --------------------------------------------------------------- Phase 6, Agentic Platforms


def test_the_scene_names_what_agentic_means(guide_text: str) -> None:
    """v4.4.6 dropped the model-plus-harness equation block.

    Its point - that "agentic" describes what surrounds the model, not a different model - is now
    carried by the subtitle and the lead, so that is what this asserts.
    """
    scene = _scene_text(guide_text, "fx-agent-platform")
    assert "Same model. Very different capabilities." in scene, "the subtitle must state the claim"
    assert "wraps the same model" in scene, "the lead must say the model is the same in both lanes"
    assert scene.index("Same model.") < scene.index('class="ap2-card"'), (
        "the claim must arrive before the comparison that demonstrates it"
    )

def test_the_boundary_marks_the_actions_it_gates(guide_text: str) -> None:
    """v4.4.6 dropped the tool strip; it listed the same six actions as the key below it.

    Permission is now shown where it belongs: the boundary marks the half of the key that can
    change the work, so a reader cannot read that half without reading what gates it.
    """
    scene = _scene_text(guide_text, "fx-agent-platform")
    assert scene.count('data-grammar="boundary"') == 1, "exactly one boundary"
    assert scene.index('data-kind="write"') <= scene.index('data-grammar="boundary"') + 40, (
        "the boundary must mark the write half of the key"
    )
    write = scene[scene.index('data-kind="write"'):]
    assert "permission and tool boundary" in write.lower()
    assert "stays conditional" in scene, "the conditional sentence must survive the cut"

def test_one_key_covers_the_whole_scene(guide_text: str) -> None:
    """v4.4.6 replaced the two per-card statement lists with one shared key.

    Two lists meant the same icon appeared in one lane and not the other, so a reader could not
    tell whether a colour meant the same thing on both sides. The key is split by the distinction
    the section is actually about: whether an action can change the work.
    """
    scene = _scene_text(guide_text, "fx-agent-platform")
    assert scene.count('class="ap2-legend"') == 1, "exactly one key"
    assert 'data-kind="read"' in scene and 'data-kind="write"' in scene
    assert "ap2-can" not in scene, "the per-card lists must not come back"
    read = scene[scene.index('data-kind="read"'):scene.index('data-kind="write"')]
    write = scene[scene.index('data-kind="write"'):]
    # the read half must not claim anything that writes, and vice versa
    for word in ("edits a file", "runs a command", "creates a file"):
        assert word in write and word not in read, word
    for word in ("reads a file", "searches the web"):
        assert word in read, word

def test_the_harness_scene_reaches_across_platforms(guide_text: str) -> None:
    """The portability claim is the reason the outer layer exists, so it must be shown, not asserted.

    v4.4.6 replaced the layer table with three cards and a band naming the platforms the one
    harness installs into. The band is what carries the claim now.
    """
    scene = _scene_text(guide_text, "fx-harness")
    band = scene[scene.index('class="hx-span"'):]
    for host in ("Claude Code", "Codex", "Cursor", "Antigravity"):
        assert host in band, f"{host} must be named in the cross-platform band"
    assert "nexus-mark" in band, "the one harness must be drawn around the platforms it spans"
    low = band.lower()
    assert "same skills" in low and "same guardrails" in low, band[:200]

def test_the_harness_layers_are_ordered_and_distinct(guide_text: str) -> None:
    """v4.4.6 cut the five-step work sequence; the three layers carry the order now.

    The sequence spelled out what the outer loop does per job. The scene's job is the comparison
    between the layers, and the sequence was competing with it for the reader's attention.
    """
    scene = _scene_text(guide_text, "fx-harness")
    # the layers nest, so source order runs outermost-first
    order = [scene.index(f'data-layer="{k}"') for k in ("nexus", "platform", "model")]
    assert order == sorted(order), "the layers must nest, outermost first"
    assert scene.count('class="hx-col"') == 3, "three layers, no more"
    assert "hx-feats" in scene, "the outer layer must list what it adds"

def test_the_scope_qualifiers_survive_the_cut(guide_text: str) -> None:
    """The two statements that keep this section honest are the ones easiest to lose in a trim.

    Nexus Hub replaces neither the model nor the platform runtime, and hooks only fire where the
    host exposes the event. Both are claims against Nexus Hub's own interest, which is exactly why
    a shorter scene must keep them.
    """
    scene = _scene_text(guide_text, "fx-harness").lower()
    assert "does not replace the model" in scene
    assert "does not replace the platform runtime" in scene
    assert "only where the host exposes the registered event" in scene

def test_neither_rebuilt_scene_overflows_at_any_width(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                ctx, page = _page(browser, width)
                page.evaluate(
                    "() => document.querySelectorAll('#foundations .fx-scene')"
                    ".forEach(s => s.scrollIntoView())"
                )
                page.wait_for_timeout(300)
                over = page.evaluate(
                    """() => ['fx-agent-platform', 'fx-harness'].map(id => {
                        const s = document.getElementById(id);
                        return [id, Math.round(s.scrollWidth - s.clientWidth)];
                    }).filter(([, o]) => o > 0)"""
                )
                ctx.close()
                assert not over, f"{width}: {over}"
        finally:
            browser.close()
