"""v4.4.1 Phase 6 gates: fullscreen control placement, Outline semantics, Escape precedence,
and the bounded presentation geometry.

These are browser tests because every claim is about COMPUTED placement or live focus
behavior. In particular, "Outline is a nonmodal disclosure" and "Escape closes Outline
before it exits presentation" cannot be read off markup: both are statements about what
happens to focus and state when a key is pressed, in a specific order.

The geometry assertions measure real pairwise intersection AREA rather than checking CSS
declarations, because the v4.4.1 layout work repeatedly produced rules that looked correct
and still overlapped at one viewport size out of four.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

# The desktop fullscreen sizes the plan names, plus the narrow reflow sizes.
DESKTOP = ((1920, 1080), (1440, 900), (1366, 768), (1280, 720))
NARROW = ((900, 900), (420, 900), (320, 900))

REGIONS = {
    "toolbar": ".nht-bar",
    "game": ".nht-game",
    "terminal": ".term--nht",
    "explorer": ".nht-explorer",
    "takeaway": ".nht-takeaway",
    "controls": ".nht-controls",
}
PAIRS = [
    ("toolbar", "game"), ("toolbar", "terminal"),
    ("game", "terminal"), ("game", "explorer"),
    ("terminal", "explorer"), ("explorer", "takeaway"), ("takeaway", "controls"),
]


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


def _present(page, route: str = "describe"):
    page.goto(GUIDE.as_uri() + f"#training/{route}")
    page.wait_for_function("window.NexusTraining && window.NexusShooter")
    page.locator("#nhtPresent").click()
    page.wait_for_function(
        "document.getElementById('nhTraining').classList.contains('is-present')"
    )


def _intersections(page):
    return page.evaluate(
        """([regions, pairs]) => {
            // A region inside a scrolling or clipping ancestor is only VISIBLE where the
            // ancestor lets it show. Comparing raw rects reports overlaps that no reader
            // can see, so each rect is clipped to its clipping ancestors first.
            const visibleRect = (el) => {
                let r = el.getBoundingClientRect();
                let box = {l: r.left, t: r.top, rt: r.right, b: r.bottom};
                for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
                    const cs = getComputedStyle(p);
                    if (cs.overflow === 'visible' && cs.overflowY === 'visible'
                        && cs.overflowX === 'visible') continue;
                    const pr = p.getBoundingClientRect();
                    box.l = Math.max(box.l, pr.left);
                    box.t = Math.max(box.t, pr.top);
                    box.rt = Math.min(box.rt, pr.right);
                    box.b = Math.min(box.b, pr.bottom);
                }
                return {x: box.l, y: box.t,
                        w: Math.max(0, box.rt - box.l), h: Math.max(0, box.b - box.t)};
            };
            const box = {};
            for (const k in regions) {
                const el = document.querySelector(regions[k]);
                if (!el) return {missing: k};
                box[k] = visibleRect(el);
            }
            const bad = [];
            for (const [a, b] of pairs) {
                const A = box[a], B = box[b];
                const ow = Math.max(0, Math.min(A.x + A.w, B.x + B.w) - Math.max(A.x, B.x));
                const oh = Math.max(0, Math.min(A.y + A.h, B.y + B.h) - Math.max(A.y, B.y));
                if (ow * oh >= 1) bad.push(`${a}/${b}=${Math.round(ow * oh)}px2`);
            }
            return {bad, overflow: document.documentElement.scrollWidth > window.innerWidth + 1};
        }""",
        [REGIONS, PAIRS],
    )


# --------------------------------------------------------------- control placement


def test_fullscreen_control_sits_in_the_bar_immediately_before_outline(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            page.goto(GUIDE.as_uri() + "#training/describe")
            page.wait_for_function("window.NexusTraining")
            placement = page.evaluate(
                """() => {
                    const bar = document.querySelector('#nhTraining .nht-bar');
                    const fs = document.getElementById('nhtPresent');
                    const outline = document.querySelector('[data-nht="outline"]');
                    const order = [...bar.querySelectorAll('button')];
                    return {
                        inBar: bar.contains(fs),
                        inRoot: document.getElementById('nhTraining').contains(fs),
                        fsBeforeOutline: order.indexOf(fs) < order.indexOf(outline),
                        adjacent: order.indexOf(outline) - order.indexOf(fs) === 1,
                        label: fs.textContent.trim(),
                        pressed: fs.getAttribute('aria-pressed'),
                        icon: !!fs.querySelector('svg path'),
                        heroButtons: document.querySelectorAll('#page-training .hero .btn-row').length,
                    };
                }"""
            )
        finally:
            browser.close()
    assert placement["inBar"] and placement["inRoot"], (
        "the control must live inside the fullscreen root so it survives presentation"
    )
    assert placement["fsBeforeOutline"] and placement["adjacent"], (
        "Full screen must sit immediately before Outline"
    )
    assert placement["label"] == "Full screen"
    assert placement["pressed"] == "false"
    assert placement["icon"], "a conventional four-corner icon is required"
    assert placement["heroButtons"] == 0, "the old hero Present button must be gone"


def test_control_label_and_state_track_presentation(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _present(page)
            during = page.evaluate(
                """() => {
                    const fs = document.getElementById('nhtPresent');
                    return {label: fs.textContent.trim(), pressed: fs.getAttribute('aria-pressed'),
                            visible: fs.getClientRects().length > 0};
                }"""
            )
            page.locator("#nhtPresent").click()
            page.wait_for_function(
                "!document.getElementById('nhTraining').classList.contains('is-present')"
            )
            after = page.evaluate(
                "() => { const f = document.getElementById('nhtPresent');"
                " return {label: f.textContent.trim(), pressed: f.getAttribute('aria-pressed')}; }"
            )
        finally:
            browser.close()
    assert during["label"] == "Exit full screen" and during["pressed"] == "true"
    assert during["visible"], "the control must stay reachable inside presentation"
    assert after["label"] == "Full screen" and after["pressed"] == "false"


# ------------------------------------------------------------------ Outline semantics


def test_outline_is_a_nonmodal_disclosure_without_a_focus_trap(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            page.goto(GUIDE.as_uri() + "#training/describe")
            page.wait_for_function("window.NexusTraining")
            trigger = page.locator('[data-nht="outline"]')
            trigger.click()
            state = page.evaluate(
                """() => {
                    const panel = document.getElementById('nhtOutline');
                    const trig = document.querySelector('[data-nht="outline"]');
                    return {
                        open: !panel.hidden,
                        expanded: trig.getAttribute('aria-expanded'),
                        role: panel.getAttribute('role'),
                        labelled: panel.getAttribute('aria-label'),
                        // A disclosure must NOT claim dialog semantics or trap focus.
                        notDialog: panel.getAttribute('role') !== 'dialog'
                            && !panel.hasAttribute('aria-modal'),
                    };
                }"""
            )
            assert state["open"] and state["expanded"] == "true"
            assert state["role"] == "region" and state["labelled"]
            assert state["notDialog"], "Outline must not use dialog semantics"

            # Outside click dismisses without stealing focus back.
            page.locator(".nht-loop").click(position={"x": 5, "y": 5})
            page.wait_for_function("document.getElementById('nhtOutline').hidden")
            assert trigger.get_attribute("aria-expanded") == "false"

            # Escape dismisses AND returns focus to the trigger.
            trigger.click()
            page.wait_for_function("!document.getElementById('nhtOutline').hidden")
            page.keyboard.press("Escape")
            page.wait_for_function("document.getElementById('nhtOutline').hidden")
            assert page.evaluate(
                "document.activeElement.getAttribute('data-nht')"
            ) == "outline", "Escape must return focus to the Outline trigger"
        finally:
            browser.close()


def test_escape_precedence_is_outline_then_game_then_overlay(playwright_mod) -> None:
    """The three Escape owners must not fight: Outline wins, then a focused game keeps its
    own Escape, and only then does Escape leave the presentation overlay."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _present(page)

            # 1. Outline open: Escape closes it and presentation SURVIVES.
            page.locator('[data-nht="outline"]').click()
            page.wait_for_function("!document.getElementById('nhtOutline').hidden")
            page.keyboard.press("Escape")
            page.wait_for_function("document.getElementById('nhtOutline').hidden")
            assert page.evaluate(
                "document.getElementById('nhTraining').classList.contains('is-present')"
            ), "closing Outline must not also exit presentation"

            # 2. Focused active game: Escape pauses the game, presentation SURVIVES.
            start = page.locator("[data-arcade-start]")
            start.wait_for(state="visible")
            start.click()
            page.wait_for_function("window.NexusShooter.snapshot().lifecycle !== 'idle'")
            # The game must own focus before its Escape handler can be the one that runs.
            page.wait_for_function(
                "document.activeElement.hasAttribute('data-arcade-game')"
            )
            page.keyboard.press("Escape")
            # Wait for the contract, not for a duration: under suite load a fixed sleep
            # samples the state before the handler has run.
            page.wait_for_function(
                "window.NexusShooter.snapshot().pauseReasons.includes('manual')"
            )
            assert page.evaluate(
                "document.getElementById('nhTraining').classList.contains('is-present')"
            ), "the game's Escape must not also exit presentation"
            assert page.evaluate(
                "document.activeElement.getAttribute('data-arcade-action')"
            ) == "toggle", "the game's Escape must focus its Resume control"

            # 3. Neither open nor game-focused: Escape exits the overlay.
            page.locator("#nhtPresent").focus()
            page.wait_for_function("document.activeElement.id === 'nhtPresent'")
            page.keyboard.press("Escape")
            page.wait_for_function(
                "!document.getElementById('nhTraining').classList.contains('is-present')"
            )
            assert page.evaluate("document.activeElement.id") == "nhtPresent", (
                "leaving presentation must restore focus to its trigger"
            )
        finally:
            browser.close()


# --------------------------------------------------------------- bounded geometry


@pytest.mark.parametrize("size", DESKTOP)
def test_desktop_presentation_regions_never_intersect(playwright_mod, size) -> None:
    width, height = size
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        try:
            _present(page, "presentify")
            result = _intersections(page)
            portrait = page.evaluate(
                """() => { const r = document.querySelector('.nag-stage').getBoundingClientRect();
                           return r.height >= r.width - 1; }"""
            )
        finally:
            browser.close()
    assert "missing" not in result, f"missing region {result.get('missing')} at {width}x{height}"
    assert not result["bad"], f"overlapping regions at {width}x{height}: {result['bad']}"
    assert not result["overflow"], f"horizontal overflow at {width}x{height}"
    assert portrait, f"the game must stay portrait or square at {width}x{height}"


@pytest.mark.parametrize("size", NARROW)
def test_narrow_presentation_reflows_into_one_scroll_surface(playwright_mod, size) -> None:
    width, height = size
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        try:
            _present(page, "presentify")
            result = _intersections(page)
            scrollers = page.evaluate(
                """() => {
                    const root = document.getElementById('nhTraining');
                    return [...root.querySelectorAll('*')].filter(el => {
                        const cs = getComputedStyle(el);
                        return (cs.overflowY === 'auto' || cs.overflowY === 'scroll')
                            && el.scrollHeight > el.clientHeight + 1;
                    }).map(el => el.className.split(' ')[0]);
                }"""
            )
        finally:
            browser.close()
    assert not result["bad"], f"overlapping regions at {width}x{height}: {result['bad']}"
    assert not result["overflow"], f"horizontal overflow at {width}x{height}"
    assert len(scrollers) <= 1, (
        f"narrow presentation must reflow into ONE scroll surface; found {scrollers}"
    )


def test_presentation_survives_a_route_change_without_stranding_the_page(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _present(page)
            page.evaluate("location.hash = '#home'")
            page.wait_for_function("document.body.dataset.page === 'home'")
            # The router and the presentation-exit handler both listen on hashchange, so
            # the exit lands in the same task queue rather than synchronously with the
            # page swap. Wait for the contract instead of sampling mid-transition.
            page.wait_for_function(
                "!document.getElementById('nhTraining').classList.contains('is-present')"
            )
            state = page.evaluate(
                """() => ({
                    present: document.getElementById('nhTraining').classList.contains('is-present'),
                    headerInert: !!document.querySelector('.site-header').inert,
                    outlineOpen: !document.getElementById('nhtOutline').hidden,
                })"""
            )
        finally:
            browser.close()
    assert not state["present"], "leaving Training must exit presentation"
    assert not state["headerInert"], "the header must not stay inert after leaving"
    assert not state["outlineOpen"], "Outline must not survive the route change"


# ============================================================================ v4.4.2 Phase 6
# Full-window three-pane presentation: coverage and stage-height floors from
# presentation-geometry.md, Outline as an overlay that moves nothing, and a short-window
# fallback that reflows into one scroll surface exactly like a narrow one.

COVERAGE_FLOOR = 0.88
STAGE_FLOOR = 0.45   # of viewport height; the arithmetic behind this number is in presentation-geometry.md
PRESENT_REGIONS = {
    **REGIONS,
    "toolbar": ".nht-bar", "progress": ".nht-loop", "head": ".nht-head",
    "tools": ".nht-tools", "after": ".nht-after",
}


def _coverage(page):
    return page.evaluate(
        """(regs) => {
            const vw = innerWidth, vh = innerHeight, cell = 8, cols = Math.ceil(vw / cell);
            const grid = new Uint8Array(cols * Math.ceil(vh / cell));
            const rects = {};
            for (const k in regs) {
                const el = document.querySelector(regs[k]);
                if (!el) return { missing: k };
                const r = el.getBoundingClientRect();
                rects[k] = [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
                for (let y = Math.max(0, r.top); y < Math.min(vh, r.bottom); y += cell)
                    for (let x = Math.max(0, r.left); x < Math.min(vw, r.right); x += cell)
                        grid[Math.floor(y / cell) * cols + Math.floor(x / cell)] = 1;
            }
            const stage = document.querySelector('.nag-stage').getBoundingClientRect();
            let n = 0; for (const v of grid) n += v;
            return { coverage: n / grid.length, stageH: stage.height / vh, rects,
                     belowFold: Object.entries(rects).filter(([k, r]) => r[1] + r[3] > vh + 1).map(([k]) => k) };
        }""",
        PRESENT_REGIONS,
    )


@pytest.mark.parametrize("size", DESKTOP)
def test_desktop_presentation_fills_the_window(playwright_mod, size) -> None:
    width, height = size
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        try:
            _present(page, "presentify")
            data = _coverage(page)
            columns = page.evaluate(
                "() => getComputedStyle(document.querySelector('.nht.is-present .nht-slide')).gridTemplateColumns.trim().split(/\\s+/).length"
            )
        finally:
            browser.close()
    assert "missing" not in data, data
    assert data["coverage"] >= COVERAGE_FLOOR, f"{width}x{height}: regions cover {data['coverage']:.2f} of the viewport, floor {COVERAGE_FLOOR}"
    assert data["stageH"] >= STAGE_FLOOR, f"{width}x{height}: stage is {data['stageH']:.2f} of the viewport height, floor {STAGE_FLOOR}"
    assert not data["belowFold"], f"{width}x{height}: regions extend below the viewport: {data['belowFold']}"
    assert columns == 3, f"three panes expected, got {columns} columns"


@pytest.mark.parametrize("size", DESKTOP)
def test_opening_outline_moves_no_region(playwright_mod, size) -> None:
    width, height = size
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        try:
            _present(page, "describe")
            before = _coverage(page)["rects"]
            page.locator('[data-nht="outline"]').click()
            page.wait_for_function("() => !document.getElementById('nhtOutline').hidden")
            page.wait_for_timeout(120)
            during = _coverage(page)["rects"]
            overlay = page.evaluate(
                "() => { const o = document.getElementById('nhtOutline'); const cs = getComputedStyle(o);"
                " const r = o.getBoundingClientRect(); return { pos: cs.position, top: r.top, visible: r.height > 0 }; }"
            )
            page.keyboard.press("Escape")
            page.wait_for_function("() => document.getElementById('nhtOutline').hidden")
            after = _coverage(page)["rects"]
        finally:
            browser.close()
    assert overlay["pos"] == "absolute" and overlay["visible"] and overlay["top"] >= 40, overlay
    assert during == before, f"opening Outline moved regions at {width}x{height}: {[k for k in before if before[k] != during[k]]}"
    assert after == before


def test_short_window_reflows_like_a_narrow_one(playwright_mod) -> None:
    """A 1280x600 window is wide but too short for three panes; it takes the single-scroll reflow."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 600})
        try:
            _present(page, "presentify")
            result = _intersections(page)
            layout = page.evaluate(
                """() => {
                    const slide = document.querySelector('.nht.is-present .nht-slide');
                    const root = document.getElementById('nhTraining');
                    const scrollers = [...root.querySelectorAll('*')].filter(el => {
                        const cs = getComputedStyle(el);
                        return (cs.overflowY === 'auto' || cs.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 1;
                    }).map(el => el.className.split(' ')[0]);
                    return { display: getComputedStyle(slide).display, scrollers,
                             outlinePos: getComputedStyle(document.getElementById('nhtOutline')).position };
                }"""
            )
        finally:
            browser.close()
    assert layout["display"] == "flex", layout
    assert not result["bad"] and not result["overflow"], result
    assert len(layout["scrollers"]) <= 1, layout
    assert layout["outlinePos"] == "static", "the overlay Outline reverts to in-flow in the single-scroll reflow"
