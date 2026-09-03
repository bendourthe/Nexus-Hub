"""v4.4.2 Phase 4 gates: connector geometry, Video and waveform Audio, the layered harness.

Browser tests, because every claim is about live geometry or runtime behaviour: connectors
drawn from measured card rectangles must not cross a card at any width; the waveform must
paint while the clip plays and freeze when it pauses; the harness choreography must reach a
fully lit end state; and SVG text must stay inside its viewBox at every width.
"""

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
    page.wait_for_function("window.NexusSeq && window.NexusFlow")
    page.wait_for_timeout(200)
    return context, page, requests


# ------------------------------------------------------------------ connectors


@pytest.mark.parametrize("width", WIDTHS)
def test_flow_connectors_never_cross_a_card(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, width=width)
        try:
            data = page.evaluate(
                """() => {
                    const out = { roots: 0, paths: 0, crossings: [] };
                    for (const root of document.querySelectorAll('[data-flow-root]')) {
                        out.roots += 1;
                        const nodes = [...root.querySelectorAll(':scope > [data-flow-node]')];
                        const boxes = nodes.map(n => n.getBoundingClientRect());
                        for (const p of root.querySelectorAll(':scope > svg.fx-flow-overlay path.fxp')) {
                            out.paths += 1;
                            const r = p.getBoundingClientRect();
                            // Shrink the connector box by 2px at each end: it is ALLOWED to touch the
                            // card edges it joins, never to run over a card body.
                            const top = r.top + 2, bottom = r.bottom - 2;
                            for (const b of boxes) {
                                const ov = Math.min(bottom, b.bottom) - Math.max(top, b.top);
                                const oh = Math.min(r.right, b.right) - Math.max(r.left, b.left);
                                if (ov > 1 && oh > 1) out.crossings.push(root.closest('section').id + '@' + Math.round(ov));
                            }
                        }
                    }
                    out.inline = document.querySelectorAll('.fx-model-flow .fx-flow-link').length;
                    return out;
                }"""
            )
        finally:
            browser.close()
    # Three roots by design: the Models flow, the request region nested inside it, and the Agentic flow.
    assert data["roots"] == 3 and data["inline"] == 0, data
    assert data["paths"] == 7, f"1 + 2 + 4 connectors expected, drew {data['paths']}"
    assert not data["crossings"], f"connectors overlap cards at {width}px: {data['crossings']}"


def test_models_and_agentic_still_share_the_entry_and_inside_bytes(playwright_mod) -> None:
    """v4.4.3 replaced the ring with the one-pass block; the sharing rule is unchanged."""
    html = GUIDE.read_text(encoding="utf-8")
    import re
    entries = re.findall(r'<div class="fx-entry" data-grammar="entry">[\s\S]*?<div class="fx-ctx-plus"', html)
    assert len(entries) == 2 and entries[0] == entries[1]
    assert html.count('data-grammar="one-pass"') == 2
    assert html.count('data-grammar="work-cycle"') == 0, "the ring grammar is retired"


# ------------------------------------------------------------------ media


def test_output_labels_and_waveform_states(playwright_mod) -> None:
    hash_js = """() => { const c = document.querySelector('canvas.fx-wave'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
                  let h = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) h = (h * 31 + (i >> 2)) >>> 0; return h; }"""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, requests = _open(browser)
        try:
            labels = page.evaluate(
                "() => [...document.querySelectorAll('#fx-model-lifecycle .fx-out-tag')].map(e => e.textContent.trim())"
            )
            page.locator("#fx-model-lifecycle .fx-outs").scroll_into_view_if_needed()
            static_state = page.evaluate("() => document.querySelector('canvas.fx-wave').dataset.waveState")
            static_px = page.evaluate(
                """() => { const c = document.querySelector('canvas.fx-wave'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
                          let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n; }"""
            )
            static_hash = page.evaluate(hash_js)
            page.evaluate("() => { const a = document.querySelector('audio.fx-out-audio'); a.volume = 0.05; return a.play(); }")
            page.wait_for_function("() => document.querySelector('canvas.fx-wave').dataset.waveState === 'live'", timeout=3000)
            # Headless Chromium advances a media element slowly with no output device, so the live
            # trace is near-flat here; what is provable is that frames keep being drawn from the
            # analyser and that the live trace is not the static one.
            page.wait_for_function("() => (+document.querySelector('canvas.fx-wave').dataset.waveFrames || 0) >= 3", timeout=3000)
            f1 = page.evaluate("() => +document.querySelector('canvas.fx-wave').dataset.waveFrames")
            live_hash = page.evaluate(hash_js)
            page.wait_for_timeout(300)
            f2 = page.evaluate("() => +document.querySelector('canvas.fx-wave').dataset.waveFrames")
            page.evaluate("() => document.querySelector('audio.fx-out-audio').pause()")
            page.wait_for_function("() => document.querySelector('canvas.fx-wave').dataset.waveState === 'static'")
            f3 = page.evaluate("() => +document.querySelector('canvas.fx-wave').dataset.waveFrames")
            after_hash = page.evaluate(hash_js)
            page.wait_for_timeout(300)
            f4 = page.evaluate("() => +document.querySelector('canvas.fx-wave').dataset.waveFrames")
        finally:
            browser.close()
    assert labels == ["Text", "Image", "Video", "Audio"], labels
    assert static_state == "static" and static_px > 100, "a static waveform paints without any gesture"
    assert f2 > f1 >= 3, f"live frames must keep drawing while playing: {f1} -> {f2}"
    assert live_hash != static_hash, "the live trace must differ from the static waveform"
    assert f4 == f3, "drawing must stop once the clip pauses"
    assert after_hash == static_hash, "pause restores the static waveform"
    assert not requests, f"media must never fetch: {requests}"


def test_waveform_is_static_under_reduced_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, reduced_motion="reduce")
        try:
            page.evaluate("() => { const a = document.querySelector('audio.fx-out-audio'); a.volume = 0.05; return a.play(); }")
            page.wait_for_timeout(400)
            state = page.evaluate("() => document.querySelector('canvas.fx-wave').dataset.waveState")
        finally:
            browser.close()
    assert state == "static"


# ------------------------------------------------------------------ layered harness


def test_harness_diagram_is_layered_and_choreographed(playwright_mod) -> None:
    root = "document.getElementById('fx-hstack-nexus')"
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser)
        try:
            structure = page.evaluate(
                f"""() => {{
                    const r = {root};
                    const layers = [...r.querySelectorAll('[data-phase3-harness-layer]')].map(g => g.dataset.phase3HarnessLayer);
                    const ports = [...r.querySelectorAll('.h-port')].map(t => t.textContent.trim());
                    const stat = document.getElementById('fx-hstack-platform');
                    return {{ layers, ports, staticLit: stat.querySelectorAll('.is-on').length,
                              staticHasTimeline: stat.hasAttribute('data-seq-root'),
                              total: window.NexusSeq.state(r).total }};
                }}"""
            )
            page.locator("#fx-hstack-nexus").scroll_into_view_if_needed()
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
                    ports: r.querySelectorAll('.h-portg.is-on').length,
                    out: !!r.querySelector('.h-out').closest('.is-on'),
                    ghost: !!r.querySelector('.h-ghost.is-on') }}; }}"""
            )
        finally:
            browser.close()
    assert set(structure["layers"]) == {"model", "platform", "nexus-hub"}
    for port in ("context", "tools", "permissions", "execution", "observations", "skills", "hooks", "gates", "artifacts"):
        assert port in structure["ports"], port
    assert structure["staticLit"] > 0 and not structure["staticHasTimeline"], "the scene-7 instance is static and fully lit"
    assert structure["total"] == 7
    assert seen == sorted(seen) and seen[-1] == 7, seen
    assert end["ports"] == 9 and end["out"] and end["ghost"], end


def test_harness_choreography_end_state_under_reduced_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, reduced_motion="reduce")
        try:
            page.locator("#fx-hstack-nexus").scroll_into_view_if_needed()
            page.wait_for_function(
                "() => { const s = window.NexusSeq.state(document.getElementById('fx-hstack-nexus')); return s.step === s.total; }"
            )
            lit = page.evaluate("() => document.querySelectorAll('#fx-hstack-nexus .h-portg.is-on, #fx-hstack-nexus .seq-rise.is-on').length")
        finally:
            browser.close()
    assert lit >= 15, lit


@pytest.mark.parametrize("width", WIDTHS)
def test_harness_svg_text_stays_inside_its_viewbox(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, width=width)
        try:
            bad = page.evaluate(
                """() => {
                    const out = [];
                    for (const svg of document.querySelectorAll('.fx-hstack svg')) {
                        const sb = svg.getBoundingClientRect();
                        for (const t of svg.querySelectorAll('text')) {
                            const r = t.getBoundingClientRect();
                            if (r.left < sb.left - 1 || r.right > sb.right + 1 || r.top < sb.top - 1 || r.bottom > sb.bottom + 1) out.push(t.textContent.trim());
                        }
                    }
                    return out;
                }"""
            )
        finally:
            browser.close()
    assert not bad, f"SVG text escapes the viewBox at {width}px: {bad}"
