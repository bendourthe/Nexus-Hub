"""Retained harness structure, choreography, reduced-motion and responsive-label gates."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (320, 420, 720, 721, 900, 1440)


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


def _open(browser, width: int = 1440, **ctx):
    context = browser.new_context(viewport={"width": width, "height": 900}, **ctx)
    page = context.new_page()
    requests: list[str] = []
    page.on("request", lambda r: requests.append(r.url) if r.url.startswith("http") else None)
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusSeq")
    page.wait_for_timeout(200)
    return context, page, requests


def test_harness_diagram_is_layered_and_choreographed(playwright_mod) -> None:
    """v4.4.3 merged the two harness scenes and rebuilt the figure in HTML.

    The two-instance rule went with the merge: there is one figure now, so there is no static
    second copy to compare it against. Everything else is unchanged and still asserted here --
    three nested layers, all nine ports, a timeline that advances monotonically to its end, and an
    end state where every stop including the output is lit.
    """
    root = "document.querySelector('#fx-harness .hx')"
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser)
        try:
            structure = page.evaluate(
                f"""() => {{
                    const r = {root};
                    const layers = [...r.querySelectorAll('[data-phase3-harness-layer]')].map(g => g.dataset.phase3HarnessLayer);
                    const ports = [...r.querySelectorAll('.hx-ports li')].map(t => t.textContent.trim());
                    // v4.4.4: the journey became the flow, so the steps are the flow's own.
                    return {{ layers, ports, total: window.NexusSeq.state(r).total }};
                }}"""
            )
            page.locator("#fx-harness").scroll_into_view_if_needed()
            page.wait_for_function(f"() => window.NexusSeq.state({root}).running === true")
            seen = []
            for _ in range(120):
                st = page.evaluate(f"() => window.NexusSeq.state({root})")
                seen.append(st["step"])
                if st["step"] >= st["total"]:
                    break
                page.wait_for_timeout(150)
            end = page.evaluate(
                f"""() => {{ const r = {root}; return {{
                    stops: r.querySelectorAll('.hxf-step.is-on').length,
                    out: r.querySelector('.hxf-step--out').classList.contains('is-on') }}; }}"""
            )
        finally:
            browser.close()
    assert set(structure["layers"]) == {"model", "platform", "nexus-hub"}
    for port in ("context", "tools", "permissions", "execution", "observations", "skills", "hooks", "gates", "artifacts"):
        assert port in structure["ports"], port
    assert len(structure["ports"]) == 9, structure["ports"]
    assert structure["total"] == 5, "five flow steps, from the prompt to the verified work"
    assert seen == sorted(seen) and seen[-1] == 5, seen
    assert end["stops"] == 5 and end["out"], end


def test_harness_choreography_end_state_under_reduced_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, reduced_motion="reduce")
        try:
            page.locator("#fx-harness").scroll_into_view_if_needed()
            page.wait_for_function(
                "() => { const s = window.NexusSeq.state(document.querySelector('#fx-harness .hx')); return s.step === s.total; }"
            )
            lit = page.evaluate("() => document.querySelectorAll('#fx-harness .hx .seq-rise.is-on').length")
        finally:
            browser.close()
    assert lit == 5, lit


@pytest.mark.parametrize("width", WIDTHS)
def test_harness_text_stays_inside_its_own_box(playwright_mod, width: int) -> None:
    """The figure is HTML now, so the property is stronger and simpler: no label may spill out of
    the element that owns it. The old form inspected SVG text, which this figure no longer has, so
    it would have passed vacuously rather than failing honestly."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, width=width)
        try:
            page.locator("#fx-harness").scroll_into_view_if_needed()
            page.wait_for_timeout(220)
            bad = page.evaluate(
                """() => {
                    const out = [];
                    const fig = document.querySelector('#fx-harness .hx');
                    if (!fig) return ['the merged harness figure is missing'];
                    fig.querySelectorAll('*').forEach(el => {
                        if (el.children.length) return;
                        const box = el.getBoundingClientRect();
                        const range = document.createRange();
                        range.selectNodeContents(el);
                        const ink = range.getBoundingClientRect();
                        range.detach();
                        if (ink.width && (ink.right > box.right + 1.5 || ink.left < box.left - 1.5))
                            out.push((el.className.toString().split(' ')[0] || el.tagName) + ': ' + el.textContent.trim().slice(0, 40));
                    });
                    return out;
                }"""
            )
        finally:
            browser.close()
    assert not bad, f"harness text escapes its own box at {width}px: {bad}"
