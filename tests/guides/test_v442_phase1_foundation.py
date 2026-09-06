"""v4.4.2 Phase 1 gates: the NexusSeq sequencer, the section-title scale, and the rename.

Browser tests, because every claim is about live behaviour or computed style: a timeline
advancing in order, pausing offscreen and on a hidden tab, collapsing to its end state under
reduced motion, and a title scale that must never force horizontal overflow at 320 px.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
PAGES = ("home", "foundations", "training", "cheatsheets")

# Visible-text rename allowlist: these carriers hold repository or command identifiers,
# where the hyphenated form is the correct spelling.
RENAME_EXEMPT_SELECTOR = "code, pre, kbd, [data-copy], a[href*='github.com/bendourthe/Nexus-Hub']"


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


def _open(browser, route: str = "home", **ctx):
    context = browser.new_context(viewport={"width": 1440, "height": 900}, **ctx)
    page = context.new_page()
    page.goto(GUIDE.as_uri() + f"#{route}")
    page.wait_for_function("window.NexusSeq && window.NexusTraining")
    return context, page


STATE = "() => window.NexusSeq.state(document.getElementById('nhg-loop'))"


# ------------------------------------------------------------------ sequencer


def test_sequencer_advances_steps_in_document_order(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        context, page = _open(browser)
        try:
            page.locator("#nhg-loop").scroll_into_view_if_needed()
            page.wait_for_function(f"({STATE})().running === true")
            seen = []
            for _ in range(40):
                st = page.evaluate(STATE)
                seen.append(st["step"])
                if st["step"] >= st["total"]:
                    break
                page.wait_for_timeout(120)
            on_order = page.evaluate(
                "() => [...document.querySelectorAll('#nhg-loop .is-on')].map(e => +e.dataset.seq)"
            )
        finally:
            browser.close()
    assert seen == sorted(seen), f"steps must only ever increase: {seen}"
    assert seen[-1] == 6, f"all six loop steps must light: {seen}"
    assert on_order == [1, 2, 3, 4, 5, 6]


def test_sequencer_pauses_offscreen_and_resumes_from_the_same_step(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        context, page = _open(browser)
        try:
            page.locator("#nhg-loop").scroll_into_view_if_needed()
            page.wait_for_function(f"({STATE})().step >= 2")
            page.evaluate("window.scrollTo(0, 0)")            # loop leaves the viewport
            page.wait_for_function(f"({STATE})().running === false")
            frozen = page.evaluate(STATE)["step"]
            page.wait_for_timeout(1500)
            still = page.evaluate(STATE)["step"]
            page.locator("#nhg-loop").scroll_into_view_if_needed()
            page.wait_for_function(f"({STATE})().running === true")
            resumed = page.evaluate(STATE)["step"]
        finally:
            browser.close()
    assert still == frozen, "a paused timeline must not advance"
    assert resumed >= frozen, "resume continues from the paused step, never restarts"


def test_sequencer_pauses_on_a_hidden_tab(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        context, page = _open(browser)
        try:
            page.locator("#nhg-loop").scroll_into_view_if_needed()
            page.wait_for_function(f"({STATE})().running === true")
            page.evaluate(
                "() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => true});"
                " document.dispatchEvent(new Event('visibilitychange')); }"
            )
            page.wait_for_function(f"({STATE})().running === false")
            page.evaluate(
                "() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => false});"
                " document.dispatchEvent(new Event('visibilitychange')); }"
            )
            page.wait_for_function(f"({STATE})().running === true")
        finally:
            browser.close()


def test_reduced_motion_reaches_the_end_state_without_scheduling(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        context, page = _open(browser, reduced_motion="reduce")
        try:
            page.locator("#nhg-loop").scroll_into_view_if_needed()
            page.wait_for_function(f"({STATE})().step === ({STATE})().total")
            st = page.evaluate(STATE)
            lit = page.evaluate("() => document.querySelectorAll('#nhg-loop .is-on').length")
            done = page.evaluate("() => document.getElementById('nhg-loop').classList.contains('seq-done')")
            # Under reduced motion play() is synchronous: nothing is left running to tick.
            page.wait_for_timeout(700)
            again = page.evaluate(STATE)
        finally:
            browser.close()
    assert st["reduced"] is True and st["running"] is False
    assert lit == st["total"] == 6 and done
    assert again["step"] == st["step"] and again["running"] is False


def test_malformed_step_is_skipped_with_a_warning_and_the_rest_run(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        context, page = _open(browser)
        warnings: list[str] = []
        page.on("console", lambda m: warnings.append(m.text) if m.type == "warning" else None)
        try:
            result = page.evaluate(
                """() => {
                    const root = document.createElement('div');
                    root.id = 'seq-probe';
                    root.innerHTML = '<i id="ok1" data-seq="1" data-seq-dur="20"></i>'
                                   + '<i id="bad" data-seq="abc"></i>'
                                   + '<i id="ok2" data-seq="2" data-seq-dur="20"></i>';
                    document.body.appendChild(root);
                    window.NexusSeq.register(root);
                    window.NexusSeq.play(root);
                    return new Promise(res => setTimeout(() => res({
                        state: window.NexusSeq.state(root),
                        on: [...root.querySelectorAll('.is-on')].map(e => e.id),
                    }), 200));
                }"""
            )
        finally:
            browser.close()
    assert result["state"]["total"] == 2, result
    assert result["on"] == ["ok1", "ok2"], result
    assert any("malformed step" in w and "#bad" in w for w in warnings), warnings


# ------------------------------------------------------------------ title scale


def test_section_titles_share_one_scale_and_never_overflow(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            context, page = _open(browser)
            sizes = page.evaluate(
                "() => [...document.querySelectorAll('.section-title')]"
                ".map(e => Math.round(parseFloat(e.getAttribute('data-fit-base'))))"
            )
            fitted = page.evaluate(
                "() => [...document.querySelectorAll('.page.active .section-title')].map(e => ({"
                "  base: parseFloat(e.getAttribute('data-fit-base')),"
                "  now: parseFloat(getComputedStyle(e).fontSize),"
                "  wrap: e.getAttribute('data-fit-wrap') }))"
            )
            training_title = page.evaluate(
                "() => Math.round(parseFloat(getComputedStyle(document.querySelector('[data-nht=\"title\"]')).fontSize))"
            )
            context.close()
            overflow = {}
            for width in (320, 420, 900, 1440):
                for route in PAGES:
                    ctx = browser.new_context(viewport={"width": width, "height": 900})
                    pg = ctx.new_page()
                    pg.goto(GUIDE.as_uri() + f"#{route}")
                    pg.wait_for_function("window.NexusSeq")
                    pg.wait_for_timeout(150)
                    overflow[(width, route)] = pg.evaluate(
                        "() => document.documentElement.scrollWidth - window.innerWidth"
                    )
                    ctx.close()
        finally:
            browser.close()
    # v4.4.3 merged the two harness scenes and v4.4.4 merged the chatbot comparison into Agentic
    # Platforms, so Foundations contributes two titles fewer than it did at v4.4.2.
    # The requested Home and Foundations closing Next sections were removed.
    assert len(sizes) == 20, f"expected 20 section titles across the four pages, found {len(sizes)}"
    assert len(set(sizes)) == 1, f"one shared stylesheet size expected, got {sorted(set(sizes))}"
    # v4.4.1 rendered h2 at 1.7rem (27.2px); v4.4.2 tuned the token to 2.4 (65.3px); the v4.4.3
    # review halved it to 1.2 (32.6px) and tripled the label instead. The RENDERED size is now
    # per-container, because NexusFit shrinks anything that would wrap, so only the base is shared.
    assert 32 <= sizes[0] <= 34, sizes[0]
    assert fitted, "no active-page titles measured"
    for row in fitted:
        assert row["now"] <= row["base"] + 0.5, row
        assert row["now"] >= 15, row
        assert row["wrap"] in ("nowrap", "normal"), row
    assert training_title < 40, "the Training slide title is not a section title and must not scale"
    bad = {k: v for k, v in overflow.items() if v > 1}
    assert not bad, f"horizontal overflow at (width, page): {bad}"


# ------------------------------------------------------------------ rename


def test_visible_text_says_nexus_hub_without_the_hyphen(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        context, page = _open(browser)
        try:
            leaks = page.evaluate(
                f"""() => {{
                    const clone = document.body.cloneNode(true);
                    clone.querySelectorAll("{RENAME_EXEMPT_SELECTOR}").forEach(e => e.remove());
                    clone.querySelectorAll('script, style').forEach(e => e.remove());
                    const text = clone.textContent;
                    const labels = [...document.querySelectorAll('[aria-label*="Nexus-Hub" i]')].length;
                    const pseudo = [...document.querySelectorAll('.cmp-a, .cmp-b')]
                        .map(e => getComputedStyle(e, '::before').content).filter(c => /nexus-hub/i.test(c)).length;
                    return {{ text: (text.match(/Nexus-Hub/gi) || []).length, labels, pseudo,
                              title: document.title }};
                }}"""
            )
        finally:
            browser.close()
    assert leaks["text"] == 0, f"{leaks['text']} visible 'Nexus-Hub' strings remain"
    assert leaks["labels"] == 0 and leaks["pseudo"] == 0, leaks
    assert "Nexus Hub" in leaks["title"]
