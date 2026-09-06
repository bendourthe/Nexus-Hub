"""v4.4.2 Phase 3 gates: Foundations title system, scene balance, and the annotated prompt.

Browser tests, because every claim is about computed layout or live behaviour: a centred
page title in the hero-subtitle style, no scene with an empty column, children contained by
their scene box at six widths, and an annotated prompt whose highlights light in document
order and all at once under reduced motion.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (320, 420, 720, 721, 900, 1440)
BALANCE_BOUND = 1.35


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
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusSeq && window.NexusTraining")
    page.wait_for_timeout(150)
    return context, page


# ------------------------------------------------------------------ title system


def test_page_opens_with_a_centred_title_in_the_hero_subtitle_style(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser)
        try:
            data = page.evaluate(
                """() => {
                    const hero = document.querySelector('#page-foundations .hero');
                    const title = hero.querySelector('h1.page-title');
                    const lead = hero.querySelector('.page-lead');
                    const home = document.querySelector('#page-home .hero-subtitle');
                    const c = el => { const r = el.getBoundingClientRect(); return r.left + r.width / 2; };
                    return {
                        kicker: !!hero.querySelector('.eyebrow'),
                        text: title.textContent.replace(/\\s+/g, ' ').trim(),
                        align: getComputedStyle(title).textAlign,
                        leadAlign: getComputedStyle(lead).textAlign,
                        sameSize: getComputedStyle(title).fontSize === getComputedStyle(home).fontSize,
                        sameWeight: getComputedStyle(title).fontWeight === getComputedStyle(home).fontWeight,
                        centred: Math.abs(c(title) - window.innerWidth / 2) < 3,
                        grad: !!title.querySelector('.gtext'),
                    };
                }"""
            )
        finally:
            browser.close()
    assert data["kicker"] is False, "the page-level Foundations kicker is gone"
    assert data["text"] == "The concepts behind every AI-assisted project"
    assert data["align"] == "center" and data["leadAlign"] == "center" and data["centred"]
    assert data["sameSize"] and data["sameWeight"], "the page title shares the Home hero-subtitle style"
    assert data["grad"]


def test_scene_titles_come_before_their_subtitles(playwright_mod) -> None:
    """Scene names keep their order and share the Home label/subtitle styling."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser)
        try:
            rows = page.evaluate(
                """() => [...document.querySelectorAll('#page-foundations .fx-title')].map(t => {
                    const sub = t.querySelector('.fx-subtitle'), h2 = t.querySelector('h2.section-title');
                    const cs = getComputedStyle(sub), hs = getComputedStyle(h2);
                    return {
                      title: h2.textContent.trim(),
                      subtitle: sub.textContent.trim(),
                      titleFirstOnScreen: h2.getBoundingClientRect().bottom <= sub.getBoundingClientRect().top + 1,
                      titleFirstInDom: (h2.compareDocumentPosition(sub) & Node.DOCUMENT_POSITION_FOLLOWING) ? true : false,
                      labelStyle: ['color','fontWeight','letterSpacing','textTransform','lineHeight'].every(k => hs[k] === getComputedStyle(document.querySelector('#page-home .eyebrow'))[k]),
                      subtitleStyle: ['color','fontWeight','letterSpacing','textTransform'].every(k => cs[k] === getComputedStyle(document.querySelector('#page-home .section-title'))[k]),
                      marker: getComputedStyle(h2,'::before').content !== 'none',
                      notALabel: cs.textTransform === 'none',
                      sameLeft: Math.abs(h2.getBoundingClientRect().left - sub.getBoundingClientRect().left) < 2,
                    };
                })"""
            )
        finally:
            browser.close()
    assert len(rows) == 6, "v4.4.4 also merged the chatbot comparison into Agentic Platforms"
    for row in rows:
        assert row["title"] and row["subtitle"], row
        assert row["titleFirstOnScreen"] and row["titleFirstInDom"], row
        assert row["labelStyle"] and row["subtitleStyle"] and row["marker"], row
        assert row["notALabel"], f"the subtitle must not render as an uppercase label: {row}"
        assert row["sameLeft"], row


# ------------------------------------------------------------------ balance and containment


def test_no_scene_has_an_empty_column_at_1440(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser)
        try:
            scenes = page.evaluate(
                """() => [...document.querySelectorAll('#page-foundations .fx-scene')].map(s => {
                    const c = s.querySelector('.fx-copy'), d = s.querySelector('.fx-diagram');
                    const h = e => e ? e.getBoundingClientRect().height : 0;
                    return { id: s.id, cols: getComputedStyle(s).gridTemplateColumns.trim().split(/\\s+/).length,
                             copy: h(c), diagram: h(d) };
                })"""
            )
        finally:
            browser.close()
    assert len(scenes) == 6, "v4.4.4 also merged the chatbot comparison into Agentic Platforms"
    for sc in scenes:
        if sc["cols"] == 1:
            continue
        lo, hi = sorted((sc["copy"], sc["diagram"]))
        assert lo > 0 and hi / lo <= BALANCE_BOUND, f"{sc['id']}: columns {sc['copy']:.0f} vs {sc['diagram']:.0f} exceed {BALANCE_BOUND}x"


@pytest.mark.parametrize("width", WIDTHS)
def test_every_scene_child_stays_inside_its_scene_box(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser, width=width)
        try:
            bad = page.evaluate(
                """() => {
                    const out = [];
                    for (const s of document.querySelectorAll('#page-foundations .fx-scene')) {
                        const sb = s.getBoundingClientRect();
                        for (const el of s.querySelectorAll('*')) {
                            const r = el.getBoundingClientRect();
                            if (r.width === 0 || r.height === 0) continue;
                            if (r.left < sb.left - 1 || r.right > sb.right + 1) out.push(s.id + ':' + (el.className || el.tagName));
                        }
                    }
                    return { out: [...new Set(out)].slice(0, 6), overflow: document.documentElement.scrollWidth - window.innerWidth };
                }"""
            )
        finally:
            browser.close()
    assert not bad["out"], f"children escape their scene horizontally at {width}px: {bad['out']}"
    assert bad["overflow"] <= 1


def test_tokens_figure_and_image_top_align_side_by_side(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser)
        try:
            data = page.evaluate(
                """() => {
                    const duo = document.querySelector('#fx-tokens .fx-duo');
                    const [a, b] = [...duo.children].map(e => e.getBoundingClientRect());
                    return { tops: Math.abs(a.top - b.top), sideBySide: a.right <= b.left + 1 || b.right <= a.left + 1,
                             inDiagram: !!document.querySelector('#fx-tokens .fx-diagram .fx-tokfig') };
                }"""
            )
        finally:
            browser.close()
    assert data["inDiagram"], "the token figure moved into the diagram column"
    assert data["tops"] < 2 and data["sideBySide"], data


# ------------------------------------------------------------------ annotated prompt


def test_annotated_prompt_is_one_text_with_four_labelled_parts(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser)
        try:
            data = page.evaluate(
                """() => {
                    const root = document.getElementById('fx-ann-prompt');
                    const text = root.querySelector('.ann-text');
                    const marks = [...text.querySelectorAll('.ann')];
                    const legend = [...root.querySelectorAll('.ann-legend dt')].map(d => d.textContent.trim());
                    return {
                        oneParagraph: root.querySelectorAll('.ann-text').length === 1,
                        parts: marks.map(m => m.dataset.part),
                        nested: root.querySelectorAll('.ann .ann').length,
                        joined: text.textContent.replace(/\\s+/g, ' ').trim(),
                        legend,
                        colours: new Set(marks.map(m => getComputedStyle(m).textDecorationColor)).size,
                        weakFirst: document.querySelector('#fx-prompts').innerHTML.indexOf('fx-state--weak')
                                 < document.querySelector('#fx-prompts').innerHTML.indexOf('fx-ann-prompt'),
                    };
                }"""
            )
            ctx_parts = page.evaluate(
                "() => [...document.querySelectorAll('#fx-ann-context .ann')].map(m => m.dataset.part)"
            )
        finally:
            browser.close()
    assert data["oneParagraph"] and data["nested"] == 0
    # v4.4.5 renamed the parts on instruction; "goal" now names the finish line the
    # figure used to call "done". The order is unchanged, the vocabulary is not.
    assert data["parts"] == ["request", "context", "goal", "format"]
    assert data["joined"].startswith("Summarise this contract and list every deadline. Use the signed PDF")
    assert data["legend"] == ["Request", "Context", "Goal", "Format"]
    assert data["colours"] == 4, "each part carries its own colour"
    assert data["weakFirst"], "the vague prompt still reads before the precise one"
    assert ctx_parts == ["request", "attachments", "goal", "context"]


@pytest.mark.parametrize("root_id", ["fx-ann-prompt", "fx-ann-context"])
def test_prompt_highlights_wait_for_the_matching_box(playwright_mod, root_id) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser)
        try:
            root = page.locator("#" + root_id)
            root.scroll_into_view_if_needed()
            page.wait_for_timeout(250)
            root.evaluate("e => window.NexusSeq.reset(e)")
            page.wait_for_timeout(400)

            def snapshot():
                return root.evaluate("""e => [...e.querySelectorAll('.ann')].map(m => ({
                    active: m.classList.contains('is-on'),
                    box: e.querySelector('.ann-legend-row[data-part="' + m.dataset.part + '"]').classList.contains('is-on'),
                    background: getComputedStyle(m).backgroundColor,
                    decoration: getComputedStyle(m).textDecorationLine,
                    codePlain: [...m.querySelectorAll('code')].every(c => getComputedStyle(c).backgroundColor === 'rgba(0, 0, 0, 0)'),
                }))""")

            plain = snapshot()
            assert all(not m["active"] and not m["box"] for m in plain)
            assert all(m["background"] == "rgba(0, 0, 0, 0)" and m["decoration"] == "none" and m["codePlain"] for m in plain)
            root.evaluate("e => window.NexusSeq.play(e)")
            page.wait_for_timeout(1000)
            first = snapshot()
            assert [m["active"] for m in first] == [True, False, False, False], "the first step must last longer than one second"
            page.wait_for_timeout(1100)
            second = snapshot()
            assert [m["active"] for m in second] == [True, True, False, False]
            for marks in (first, second):
                for mark in marks:
                    assert mark["active"] == mark["box"]
                    assert mark["decoration"] == ("underline" if mark["active"] else "none")
                    assert (mark["background"] != "rgba(0, 0, 0, 0)") == mark["active"]
        finally:
            browser.close()


def test_annotated_prompt_reveals_in_document_order_and_all_at_once_under_reduced_motion(playwright_mod) -> None:
    state = "() => window.NexusSeq.state(document.getElementById('fx-ann-prompt'))"
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page = _open(browser)
        try:
            page.locator("#fx-ann-prompt").scroll_into_view_if_needed()
            page.wait_for_function(f"({state})().running === true")
            order = []
            for _ in range(60):
                lit = page.evaluate("() => [...document.querySelectorAll('#fx-ann-prompt .ann.is-on')].map(m => m.dataset.part)")
                if lit and (not order or lit != order[-1]):
                    order.append(lit)
                if len(lit) == 4:
                    break
                page.wait_for_timeout(120)
            legend_lit = page.evaluate("() => document.querySelectorAll('#fx-ann-prompt .ann-legend-row.is-on').length")
        finally:
            browser.close()
        browser = pw.chromium.launch()
        _ctx, page = _open(browser, reduced_motion="reduce")
        try:
            page.locator("#fx-ann-prompt").scroll_into_view_if_needed()
            page.wait_for_function(f"({state})().step === ({state})().total")
            reduced = page.evaluate(
                "() => ({ marks: document.querySelectorAll('#fx-ann-prompt .ann.is-on').length,"
                " rows: document.querySelectorAll('#fx-ann-prompt .ann-legend-row.is-on').length,"
                " running: window.NexusSeq.state(document.getElementById('fx-ann-prompt')).running })"
            )
        finally:
            browser.close()
    assert order[-1] == ["request", "context", "goal", "format"], order
    for earlier, later in zip(order, order[1:]):
        assert later[: len(earlier)] == earlier, f"reveal must be cumulative and in order: {order}"
    assert legend_lit == 4
    assert reduced == {"marks": 4, "rows": 4, "running": False}
