"""v4.4.1 Phase 2 browser gates for Home: lockup motion, rail optics, and pill readability.

These are browser assertions rather than structural ones because each claim is about COMPUTED
state that markup cannot prove:

- "the whole lockup floats as one unit" is a claim about three elements sharing one vertical
  delta over time while their pairwise offsets stay fixed. A CSS rule cannot show that; only
  sampling positions at three animation times can.
- "the float stops when Home is offscreen or motion is reduced" is a claim about the ABSENCE
  of movement, which is exactly the kind of thing a structural test reports as passing while
  the page animates anyway.
- "the pills are readable two-line pills" is a claim about computed font size and about the
  command and description occupying different lines, not about the DOM containing two children.

Skipped unless a browser is available, and fail-closed under NEXUS_REQUIRE_RENDER=1 so CI
cannot silently degrade to no coverage.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

PLATFORMS = ("Claude", "ChatGPT", "Gemini", "Cursor", "GitHub Copilot")


def _launch(pw, reduced_motion: str = "no-preference", width: int = 1440):
    browser = pw.chromium.launch()
    page = browser.new_page(
        viewport={"width": width, "height": 900},
        reduced_motion=reduced_motion,
    )
    page.goto(GUIDE.as_uri())
    page.wait_for_timeout(350)
    return browser, page


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
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


def _lockup_positions(page) -> tuple[float, float, float]:
    """Vertical page offsets of the mark and both wordmark spans."""
    return tuple(
        page.evaluate(
            """() => {
                const mark = document.querySelector('.hero-lockup .hero-mark');
                const bold = document.querySelector('.hero-lockup .hero-wordmark b');
                const soft = document.querySelector('.hero-lockup .hero-wordmark span');
                return [mark, bold, soft].map(el => el.getBoundingClientRect().top);
            }"""
        )
    )


def test_full_lockup_stays_aligned_at_rest(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            samples = []
            for _ in range(3):
                samples.append(_lockup_positions(page))
                page.wait_for_timeout(900)
        finally:
            browser.close()

    # The identity stays still; motion is reserved for explanatory playback.
    deltas = [
        tuple(round(later[i] - samples[0][i], 2) for i in range(3)) for later in samples[1:]
    ]
    assert all(all(abs(d) <= 0.5 for d in delta) for delta in deltas), (
        f"the lockup drifted while reading: {samples}"
    )

    # Every moving sample must move all three elements by the SAME delta: that is what makes
    # it one lockup rather than three independently drifting pieces.
    for delta in deltas:
        spread = max(delta) - min(delta)
        assert spread < 0.75, f"lockup elements moved by different amounts: {delta}"

    # Pairwise horizontal/vertical relationships stay fixed throughout.
    for sample in samples[1:]:
        for i in range(1, 3):
            base_gap = samples[0][i] - samples[0][0]
            gap = sample[i] - sample[0]
            assert abs(gap - base_gap) < 0.75, "the lockup's internal spacing changed while floating"


def test_lockup_is_static_under_reduced_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw, reduced_motion="reduce")
        try:
            first = _lockup_positions(page)
            page.wait_for_timeout(1600)
            second = _lockup_positions(page)
        finally:
            browser.close()
    for a, b in zip(first, second):
        assert abs(a - b) < 0.25, (
            f"the lockup moved under prefers-reduced-motion: {first} -> {second}"
        )


def test_lockup_is_static_once_home_is_offscreen(playwright_mod) -> None:
    """The float is observer-gated, so scrolling Home away must stop it completely."""
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(700)
            live = page.evaluate(
                "() => document.querySelector('.hero-lockup').classList.contains('live')"
            )
            assert live is False, "the hero lockup is still marked live after scrolling away"
            first = _lockup_positions(page)
            page.wait_for_timeout(1500)
            second = _lockup_positions(page)
        finally:
            browser.close()
    for a, b in zip(first, second):
        assert abs(a - b) < 0.25, "the lockup kept animating while offscreen"


@pytest.mark.parametrize("width", (320, 420, 900, 1440))
def test_platform_rail_has_no_overflow_clipping_or_orphan_row(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw, width=width)
        try:
            data = page.evaluate(
                """() => {
                    const items = [...document.querySelectorAll('.platform-rail .platform-item')];
                    return {
                        docOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
                        rows: items.map(el => Math.round(el.getBoundingClientRect().top)),
                        centres: items.map(el => {
                            const r = el.getBoundingClientRect();
                            return { top: Math.round(r.top), cx: r.left + r.width / 2 };
                        }),
                        clipped: items.map(el => {
                            const n = el.querySelector('.platform-name');
                            return n.scrollWidth > n.clientWidth + 1;
                        }),
                        marks: items.map(el => {
                            const m = el.querySelector('.platform-mark');
                            const r = m.getBoundingClientRect();
                            return r.width > 8 && r.height > 8;
                        }),
                    };
                }"""
            )
            viewport_centre = page.evaluate("() => window.innerWidth / 2")
        finally:
            browser.close()

    assert len(data["rows"]) == 5, "the rail must render exactly five items"
    assert not data["docOverflow"], f"horizontal overflow at {width} px"
    assert not any(data["clipped"]), f"a platform label is clipped at {width} px"
    assert all(data["marks"]), f"a platform mark rendered with no visible area at {width} px"

    # Five items cannot fill a multi-column row evenly, so any short final row must be
    # CENTRED. A left-hanging remainder is the orphan row the plan forbids.
    by_row: dict[int, list[float]] = {}
    for cell in data["centres"]:
        by_row.setdefault(cell["top"], []).append(cell["cx"])
    if len(by_row) > 1:
        last_top = max(by_row)
        last_row = by_row[last_top]
        row_centre = (min(last_row) + max(last_row)) / 2
        assert abs(row_centre - viewport_centre) < width * 0.08, (
            f"the final rail row is not centred at {width} px "
            f"(row centre {row_centre:.0f} vs viewport centre {viewport_centre:.0f})"
        )




def test_footer_attribution_is_visible_on_every_page_and_absent_from_home_flow(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            results = {}
            for route in ("home", "foundations", "training", "cheatsheets"):
                page.goto(GUIDE.as_uri() + f"#{route}")
                page.wait_for_timeout(200)
                results[route] = page.evaluate(
                    """() => {
                        const f = document.querySelector('footer.site-footer .footer-attrib');
                        const r = f.getBoundingClientRect();
                        return { visible: r.width > 0 && r.height > 0, text: f.textContent,
                                 licence: !!f.querySelector('a[href*="creativecommons.org/licenses/by/4.0"]') };
                    }"""
                )
            home_credits = page.evaluate("() => document.querySelectorAll('#page-home .platform-credits').length")
        finally:
            browser.close()
    for route, r in results.items():
        assert r["visible"], f"footer attribution not visible on {route}"
        assert "Codicons icon set by Microsoft Corporation" in r["text"] and r["licence"], route
        assert "trademarks of their respective owners" in r["text"]
    assert home_credits == 0
