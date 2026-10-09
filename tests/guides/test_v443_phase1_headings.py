"""v4.4.3 Phase 1 gates: one heading rule, comparison-grade table headers, and no second person.

The operator's review of the shipped v4.4.2 build asked for three things that are all measurable:
the segment label three times larger, the segment title half its size, and no title left wrapping.
A stylesheet cannot promise the third on its own, because a fixed size does not know its container,
so NexusFit measures and shrinks. These tests hold the rule where it matters (720px and wider, one
line always) and hold the floor where a single line is impossible, rather than pretending a 320px
viewport can carry a 33px heading on one line.

The second-person sweep is asserted over the static document, which is what the reader loads. Text
the Training simulation injects at runtime is out of this version's scope and is not claimed here.

v4.4.4 removed the Foundations scene subtitle from this measurement. It is no longer a heading: the
review inverted the pair so the scene NAME is the title and the descriptive phrase is a sentence
beneath it, which should wrap like prose rather than shrink to one line. Titles and Home labels are
still measured here; the new pair order is asserted in `test_v442_phase3_foundations.py`.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

PAGES = ("home", "foundations", "commands", "cheatsheets")
ALL_WIDTHS = (320, 420, 720, 900, 1440)
ONE_LINE_WIDTHS = (720, 900, 1440)
FIT_FLOOR = 15
SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself|yourselves|you're|you'll|you've|you'd)\b", re.I)


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


def _page(browser, width: int, route: str):
    ctx = browser.new_context(viewport={"width": width, "height": 900})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + f"#{route}")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.wait_for_timeout(180)
    return ctx, page


MEASURE = """() => {
  const rows = [];
  document.querySelectorAll('.page.active .section-title, .page.active .eyebrow')
    .forEach(el => {
      const cs = getComputedStyle(el);
      const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2;
      const r = el.getBoundingClientRect();
      /* Count lines inside the padding and the rule above an H2, not across them. */
      const inner = r.height - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - parseFloat(cs.borderTopWidth) - parseFloat(cs.borderBottomWidth);
      const host = el.parentElement, hcs = getComputedStyle(host);
      const avail = host.clientWidth - parseFloat(hcs.paddingLeft) - parseFloat(hcs.paddingRight);
      /* the glyph run, not the box: a capped box hides its own overflow */
      const range = document.createRange(); range.selectNodeContents(el);
      const ink = range.getBoundingClientRect().width; range.detach();
      rows.push({
        kind: el.classList.contains('section-title') ? 'title' : 'label',
        text: el.textContent.replace(/\\s+/g, ' ').trim().slice(0, 46),
        px: +parseFloat(cs.fontSize).toFixed(2),
        base: +parseFloat(el.getAttribute('data-fit-base')).toFixed(2),
        wrap: el.getAttribute('data-fit-wrap'),
        lines: Math.max(1, Math.round(inner / lh)),
        spill: +(ink - avail).toFixed(1),
      });
    });
  return rows;
}"""


def test_section_titles_stand_alone_without_eyebrow_labels(playwright_mod) -> None:
    """v4.13.10 R21: the eyebrow labels above section titles are gone; the title carries the keyword."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _page(browser, 1440, "home")
            data = page.evaluate(
                """() => {
                    const ti = document.querySelector('#nhg-install .section-title');
                    return { eyebrows: document.querySelectorAll('#page-home .eyebrow').length,
                             title: parseFloat(getComputedStyle(ti).fontSize), text: ti.textContent.trim() };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["eyebrows"] == 0, data
    assert data["text"] == "Installation", data
    assert data["title"] >= 26, data


@pytest.mark.parametrize("width", ONE_LINE_WIDTHS)
def test_no_heading_wraps_from_720_upward(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        wrapped = {}
        try:
            for route in PAGES:
                ctx, page = _page(browser, width, route)
                wrapped[route] = [r for r in page.evaluate(MEASURE) if r["lines"] > 1 or r["wrap"] != "nowrap"]
                ctx.close()
        finally:
            browser.close()
    assert not any(wrapped.values()), f"headings wrapped at {width}px: {wrapped}"


@pytest.mark.parametrize("width", ALL_WIDTHS)
def test_no_heading_spills_past_its_container(playwright_mod, width: int) -> None:
    """The absolute rule at every width: the glyph run stays inside the container that holds it."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        spills = {}
        try:
            for route in PAGES:
                ctx, page = _page(browser, width, route)
                rows = page.evaluate(MEASURE)
                spills[route] = [r for r in rows if r["spill"] > 1.5]
                for r in rows:
                    assert r["px"] >= FIT_FLOOR - 0.01, (width, route, r)
                    assert r["px"] <= r["base"] + 0.5, (width, route, r)
                ctx.close()
        finally:
            browser.close()
    assert not any(spills.values()), f"headings spill past their container at {width}px: {spills}"


def test_migration_table_headers_carry_the_comparison_grade(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _page(browser, 1440, "home")
            data = page.evaluate(
                """() => {
                    const read = el => { const cs = getComputedStyle(el);
                      return {t: el.textContent.trim(), px: +parseFloat(cs.fontSize).toFixed(1),
                              weight: cs.fontWeight, upper: cs.textTransform, color: cs.color}; };
                    return {
                      th: [...document.querySelectorAll('.tbl-migrate th')].map(read),
                      without: read(document.querySelector('.cmp-side--without')),
                      with_: read(document.querySelector('.cmp-side--with')),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    th, without, with_ = data["th"], data["without"], data["with_"]
    assert len(th) == 3, th
    for cell in th:
        assert cell["px"] == without["px"], (cell, without)
        assert cell["weight"] == without["weight"], (cell, without)
        assert cell["upper"] == without["upper"] == "uppercase", (cell, without)
    assert th[0]["color"] == without["color"], (th[0], without)
    assert th[1]["color"] == with_["color"], (th[1], with_)
    assert th[2]["color"] not in (without["color"], with_["color"]), th[2]


def test_static_document_never_addresses_the_reader(guide_text: str) -> None:
    body = guide_text[guide_text.index("<body") :]
    for tag in ("script", "style"):
        body = re.sub(rf"<{tag}\b.*?</{tag}>", " ", body, flags=re.S)
    # Speaker labels and usage notices belong to the requested illustrative session dialogue.
    body = re.sub(r'<div class="ph-run">[\s\S]*?(?=<p class="ph-note">)', " ", body)
    prose = re.sub(r"<[^>]+>", " ", body)
    assert not SECOND_PERSON.findall(prose), sorted(set(SECOND_PERSON.findall(prose)))
    facing = re.findall(r'(?:aria-label|alt|title|data-th|placeholder)="([^"]*)"', body)
    offenders = [v for v in facing if SECOND_PERSON.search(v)]
    assert not offenders, offenders


# --- One heading system (v4.13.10 R21) ----------------------------------------------------

TRAINING = GUIDE.with_name("training.html")
SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "with"}
HEADINGS_JS = """() => [...document.querySelectorAll('main h1, main h2, main h3')]
  .filter(h => h.getClientRects().length && !h.closest('figure, .pg-fig, .ide, .ss-host, .cx-preview, .tr-reward'))
  .map(h => { const c = getComputedStyle(h);
    return { tag: h.tagName, text: h.textContent.trim(), size: c.fontSize, weight: c.fontWeight, color: c.color,
             gradient: c.webkitTextFillColor === 'rgba(0, 0, 0, 0)' || /gradient/.test(c.backgroundImage) }; })"""


def _routes():
    return [(GUIDE.as_uri() + "#home", "home"), (GUIDE.as_uri() + "#foundations", "foundations"),
            (GUIDE.as_uri() + "#cheatsheets", "cheatsheets"), (TRAINING.as_uri(), "training")]


def _headings(playwright_mod) -> dict:
    out = {}
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for url, name in _routes():
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(url)
                page.wait_for_timeout(500)
                out[name] = page.evaluate(HEADINGS_JS)
                page.close()
        finally:
            browser.close()
    return out


def test_every_page_shares_one_heading_style(playwright_mod) -> None:
    """Maintainer review 7: Home, Foundations, Cheatsheets, and Training styled headings differently."""
    pages = _headings(playwright_mod)
    for tag in ("H2", "H3"):
        styles = {name: {(h["size"], h["weight"], h["color"]) for h in hs if h["tag"] == tag} for name, hs in pages.items()}
        seen = set().union(*styles.values())
        assert len(seen) == 1, f"{tag} differs across pages: {styles}"
    page_h1 = {name: {(h["size"], h["weight"]) for h in hs if h["tag"] == "H1"} for name, hs in pages.items() if name != "home"}
    assert len(set().union(*page_h1.values())) == 1, f"page titles differ: {page_h1}"
    h1 = float(next(iter(set().union(*page_h1.values())))[0][:-2])
    h2 = float(next(h["size"] for h in pages["foundations"] if h["tag"] == "H2")[:-2])
    assert h1 >= h2 * 1.4, "H1 must be clearly more prominent than H2"
    assert not [h["text"] for hs in pages.values() for h in hs if h["gradient"]], "no gradient words in headings"


def test_headings_are_keyword_labels_never_sentences(playwright_mod) -> None:
    """Maintainer review 7: headings are keywords in Title Case, never sentences."""
    bad = []
    for name, hs in _headings(playwright_mod).items():
        for h in hs:
            text = h["text"]
            if not text:
                continue
            words = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", text)
            lowered = [w for w in words if w[0].islower() and w.lower() not in SMALL_WORDS]
            if text[-1] in ".?!" or len(words) > 6 or lowered:
                bad.append((name, h["tag"], text))
    assert not bad, bad


def test_no_eyebrow_lines_or_dash_prefixes_render(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for url, name in _routes():
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(url)
                page.wait_for_timeout(400)
                shown = page.evaluate("[...document.querySelectorAll('main .eyebrow, main .tr-kicker')].filter(e => e.getClientRects().length).length")
                # R27: the H2 marker is the round accent dot; a dash (a wide, flat bar) must never return.
                dash = page.evaluate("[...document.querySelectorAll('main h2')].filter(h => { const b = getComputedStyle(h, '::before');"
                                     " return b.content !== 'none' && Math.abs(parseFloat(b.width) - parseFloat(b.height)) > .5; }).length")
                assert shown == 0 and dash == 0, (name, shown, dash)
                page.close()
        finally:
            browser.close()


# --- Text roles and the H2 dot (v4.13.10 R27, T100) ---------------------------------------
TYPE_CSS = GUIDE.parent / "shared" / "type.css"
# Illustration internals and controls, exactly as type.css documents them.
ROLE_EXEMPT = ['figure', '.pg-fig', '.ide', '.ss-host', '.tro', '.fxo', '.cx-preview', 'svg', '.fx-diagram', '.ml-flow',
               '.ml-tier-list', '.ml-scale', '.ph', '.term', '.loop-strip', '.tr-flow', '.ide-wrap', '.hero-lockup', '.hb', '.tm']
ROLE_AUDIT_JS = """(exempt) => {
  exempt = exempt + ', .tr-reward, [aria-hidden="true"]';
  const CONTROL = 'nav, button, summary, .pagenav';
  const PHRASING = new Set(['STRONG','B','EM','I','A','ABBR','SUP','SUB','MARK','KBD','S','U','Q','CITE','DFN','TIME','BR','WBR','SMALL']);
  const ALL = ['fontSize','fontWeight','lineHeight','letterSpacing','color','fontFamily'], METRIC = ['fontSize','letterSpacing','fontFamily'];
  const main = document.querySelector('main'), host = document.querySelector('.page.active .container') || main, refs = {};
  const ref = (role, tone) => { const k = role + '|' + (tone || '');
    if (!refs[k]) { const d = document.createElement('div'); d.dataset.ty = role; if (tone) d.dataset.tone = tone; d.textContent = 'x';
      host.appendChild(d); const c = getComputedStyle(d); refs[k] = Object.fromEntries(ALL.map(p => [p, c[p]])); d.remove(); }
    return refs[k]; };
  const out = [];
  let checked = 0;
  for (const el of main.querySelectorAll('*')) {
    if (PHRASING.has(el.tagName) || ['SCRIPT','STYLE','TEMPLATE','NOSCRIPT'].includes(el.tagName)) continue;
    if (!el.getClientRects().length || el.closest(exempt)) continue;
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (cs.visibility === 'hidden' || r.width < 1 || r.height < 1) continue;
    checked++;
    const text = el.textContent.trim().replace(/\\s+/g, ' ').slice(0, 40), name = el.tagName + '.' + [...el.classList].join('.');
    const owner = el.closest('[data-ty]');
    if (!owner) { out.push([name, text, 'no role']); continue; }
    const want = ref(owner.dataset.ty, owner.dataset.tone);
    for (const p of (el.closest(CONTROL) ? METRIC : ALL)) if (cs[p] !== want[p]) out.push([name, text, owner.dataset.ty, p, cs[p], want[p]]);
  }
  return { checked, out };
}"""
DOT_JS = """() => { const probe = document.createElement('i'); probe.style.color = 'var(--accent)'; document.body.appendChild(probe);
  const accent = getComputedStyle(probe).color; probe.remove();
  const vis = h => h.getClientRects().length && !h.closest('figure, .pg-fig, .ide, .ss-host, .cx-preview, .tr-reward');
  const h2 = [...document.querySelectorAll('main h2')].filter(vis).map(h => { const c = getComputedStyle(h), b = getComputedStyle(h, '::before');
    const w = parseFloat(b.width), top = parseFloat(b.top);
    return { text: h.textContent.trim(), content: b.content, round: b.borderTopLeftRadius === '50%' || parseFloat(b.borderTopLeftRadius) >= w / 2,
             square: Math.abs(w - parseFloat(b.height)) < .5 && w > 0, bg: b.backgroundColor, accent,
             centre: top + parseFloat(b.height) / 2, line: parseFloat(c.paddingTop) + parseFloat(c.lineHeight) / 2,
             after: getComputedStyle(h, '::after').content }; });
  const h3 = [...document.querySelectorAll('main h3')].filter(vis).map(h => [h.textContent.trim(), getComputedStyle(h, '::before').content]);
  return { h2, h3 }; }"""


def _each_page(playwright_mod, script: str, arg=None) -> dict:
    out = {}
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for url, name in _routes():
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(url)
                page.wait_for_timeout(500)
                out[name] = page.evaluate(script, arg) if arg is not None else page.evaluate(script)
                page.close()
        finally:
            browser.close()
    return out


def test_the_exemptions_are_the_ones_type_css_documents() -> None:
    comment = TYPE_CSS.read_text(encoding="utf-8").split("*/", 1)[0]
    missing = [sel for sel in ROLE_EXEMPT if sel not in comment]
    assert not missing, f"type.css must document every exemption the audit uses: {missing}"


def test_every_text_element_renders_with_its_role(playwright_mod) -> None:
    """Maintainer review (revision 7): every text element has a named role whose style lives in type.css."""
    pages = _each_page(playwright_mod, ROLE_AUDIT_JS, ", ".join(ROLE_EXEMPT))
    for name, res in pages.items():
        assert res["checked"] > 20, (name, res["checked"])
    bad = {name: res["out"][:10] for name, res in pages.items() if res["out"]}
    assert not bad, bad


def test_every_h2_carries_the_accent_dot_and_no_h3_does(playwright_mod) -> None:
    """Maintainer review (revision 7): one coloured dot left of every H2, centred on its first line; never on an H3."""
    pages = _each_page(playwright_mod, DOT_JS)
    for name, res in pages.items():
        assert res["h2"], name
        for h in res["h2"]:
            assert h["content"] in ('""', "''") and h["round"] and h["square"], (name, h)
            assert h["bg"] == h["accent"], (name, h)
            assert abs(h["centre"] - h["line"]) <= 1, (name, h)
            assert h["after"] in ("none", "normal"), (name, h)
        dotted = [t for t, content in res["h3"] if content not in ("none", "normal")]
        assert not dotted, (name, dotted)
