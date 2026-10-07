"""v4.13.10 R44 and R45: the Home benefits figure and the illustrated install walkthrough.

R44 removes the hero button row and replaces the "Raw Prompting Limits" cards with a figure in
which the hero's five platforms flow into the Nexus Hub mark, which then lights four illustrated
benefits in turn. R45 gives each install tab numbered steps beside the system's icon and an
animated mockup of that system's terminal running the installer, whose output must come from the
real installer scripts. The copy chip, detection, and stored choice are covered by
test_v41310_r38_install.py.

Browser tests skip when Playwright or Chromium is missing and fail closed under
NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

PLATFORMS = ["Claude", "ChatGPT", "Gemini", "Cursor", "GitHub Copilot"]
BENEFITS = [("consistency", "Consistency"), ("depth", "Depth"), ("safety", "Safety"), ("governance", "Governance")]
INSTALL_SH = "curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash"
INSTALL_PS = "irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex"
COMMANDS = {"win": INSTALL_PS, "mac": INSTALL_SH, "linux": INSTALL_SH}
STEPS = {
    "win": ["Press the Windows key, or click Start.", "Type PowerShell and press Enter.", "Paste the command and press Enter."],
    "mac": ["Press Cmd + Space to open Spotlight.", "Type Terminal and press Enter.", "Paste the command and press Enter."],
    "linux": ["Press Ctrl + Alt + T, or open Terminal from the applications menu.", "Paste the command and press Enter."],
}
# Each system's own terminal look: skin class, body background, and where the window controls sit.
CHROME = {
    "win": ("tm--win", "rgb(1, 36, 86)", "right"),
    "mac": ("tm--mac", "rgb(30, 30, 30)", "left"),
    "linux": ("tm--gnome", "rgb(48, 10, 36)", "right"),
}
# Values the real installer computes at run time (repository, paths, version, the verified
# platform and its surfaces). The mockup marks each one with <var>; everything else must be
# literal text from the installer source named on the line.
DYNAMIC = {
    "bendourthe/Nexus-Hub@main", "C:\\Users\\dev\\.nexus-hub\\src", "/Users/dev/.nexus-hub/src",
    "/home/dev/.nexus-hub/src", "4.13.10", "Claude", "commands:ok, skills:ok",
}


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


def _open(browser, width: int = 1440, height: int = 900, reduced: bool = False, hash_: str = "#home"):
    context = browser.new_context(viewport={"width": width, "height": height}, user_agent=WIN_UA,
                                  reduced_motion="reduce" if reduced else "no-preference")
    page = context.new_page()
    page.goto(GUIDE.as_uri() + hash_)
    page.wait_for_selector("#nhg-benefits .hb")
    return context, page


def _home_source() -> str:
    text = GUIDE.read_text(encoding="utf-8")
    start = text.index('id="page-home"')
    return text[start: text.index('<section class="page', start + 10)]


# --------------------------------------------------------------------------------- R44 source


def test_the_hero_has_no_button_row() -> None:
    home = _home_source()
    hero = home[: home.index('id="nhg-benefits"')]
    assert 'class="btn-row"' not in hero and 'class="btn' not in hero, "the hero keeps no buttons"
    for label in ("Get trained", "Open Cheatsheets", 'href="#home/install"'):
        assert label not in hero, label
    assert "Raw Prompting Limits" not in home and 'id="nhg-why"' not in home


# --------------------------------------------------------------------------------- R44 rendered


def test_benefits_sit_between_the_hero_and_installation(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            data = page.evaluate(
                """() => { const box = document.querySelector('#page-home > .container');
                  return { buttons: document.querySelectorAll('#page-home .hero .btn, #page-home .hero .btn-row').length,
                           order: [...box.children].map(e => e.id || e.className).slice(0, 4),
                           title: document.querySelector('#nhg-benefits .section-title').textContent.trim() }; }"""
            )
        finally:
            browser.close()
    assert data["buttons"] == 0, data
    assert data["order"][:3] == ["hero", "nhg-benefits", "nhg-install"], data
    assert data["title"] == "Harness Benefits"


def test_four_illustrated_panels_name_the_benefits(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            panels = page.evaluate(
                """() => [...document.querySelectorAll('#nhg-benefits .hb-panel')].map(p => ({
                    key: p.dataset.benefit, title: p.querySelector('h3').textContent.trim(),
                    line: p.querySelector('p').textContent.trim(), ill: p.querySelectorAll('svg.hb-ill > *').length,
                    count: (p.querySelector('[data-count="skills"]') || {}).textContent || null }))"""
            )
        finally:
            browser.close()
    assert [(p["key"], p["title"]) for p in panels] == BENEFITS
    for panel in panels:
        assert panel["ill"] >= 4, f"{panel['key']}: the panel carries an illustration"
        assert 3 <= len(panel["line"].split()) <= 9, panel["line"]
        assert not re.search(r"\byou\b", panel["line"], re.I)
    depth = panels[1]
    assert depth["count"] and depth["count"].isdigit(), "the skill count stays dynamic"


def test_each_platform_flows_into_the_hub(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            data = page.evaluate(
                """() => { const fig = document.querySelector('#nhg-benefits .hb');
                  const rail = [...document.querySelectorAll('#page-home .platform-rail [data-platform]')].map(e => e.dataset.platform);
                  const plats = [...fig.querySelectorAll('.hb-plat')];
                  const svg = fig.querySelector('.hb-wires--in'), r = svg.getBoundingClientRect();
                  const hub = fig.querySelector('.hb-hub svg').getBoundingClientRect();
                  const px = p => [r.left + p.x / 100 * r.width, r.top + p.y / 40 * r.height];
                  const wires = [...svg.querySelectorAll('path')].map(w => [px(w.getPointAtLength(0)), px(w.getPointAtLength(w.getTotalLength()))]);
                  return { rail, plats: plats.map(p => p.dataset.platform),
                           marks: plats.map(p => { const m = p.querySelector('.hb-mark').getBoundingClientRect();
                             return { svg: p.querySelectorAll('.hb-mark svg').length, ids: p.querySelectorAll('[id]').length,
                                      cx: m.left + m.width / 2, bottom: m.bottom }; }),
                           wires, hub: { cx: hub.left + hub.width / 2, top: hub.top },
                           use: fig.querySelector('.hb-hub use').getAttribute('href') }; }"""
            )
        finally:
            browser.close()
    assert data["rail"] == PLATFORMS and data["plats"] == PLATFORMS, "the same five platforms as the hero row"
    assert data["use"] == "#nexus-mark"
    assert len(data["wires"]) == len(PLATFORMS)
    for mark, (start, end) in zip(data["marks"], data["wires"]):
        assert mark["svg"] == 1 and mark["ids"] == 0, "the hero icon is reused without duplicate ids"
        assert abs(start[0] - mark["cx"]) < 14 and abs(start[1] - mark["bottom"]) < 14, (mark, start)
        assert abs(end[0] - data["hub"]["cx"]) < 4 and abs(end[1] - data["hub"]["top"]) < 6, (data["hub"], end)


def test_the_loop_lights_each_panel_in_turn(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            page.locator("#nhg-benefits .hb").scroll_into_view_if_needed()
            states = []
            for step in ("1", "2", "3", "4"):
                page.wait_for_selector(f'#nhg-benefits .hb.live[data-step="{step}"]', timeout=25000)
                page.wait_for_timeout(700)
                states.append(page.evaluate(
                    """() => [...document.querySelectorAll('#nhg-benefits .hb-panel')].map(p => [
                        p.classList.contains('is-on'), p.classList.contains('is-done'), +getComputedStyle(p).opacity])"""
                ))
        finally:
            browser.close()
    for n, state in enumerate(states, 1):
        assert [s[0] for s in state] == [i == n for i in range(1, 5)], (n, state)
        assert [s[1] for s in state] == [i < n for i in range(1, 5)], (n, state)
        lit = state[n - 1][2]
        assert lit == 1, (n, state)
        for i, (_on, _done, opacity) in enumerate(state, 1):
            if i > n:
                assert opacity < lit, "a panel waiting its turn rests dimmer"


def test_the_loop_stops_offscreen_and_in_a_hidden_tab(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            page.locator("#nhg-benefits .hb").scroll_into_view_if_needed()
            page.wait_for_selector('#nhg-benefits .hb.live[data-step="1"]', timeout=10000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_function("!document.querySelector('#nhg-benefits .hb').classList.contains('live')")
            step = page.get_attribute("#nhg-benefits .hb", "data-step")
            page.wait_for_timeout(4000)
            assert page.get_attribute("#nhg-benefits .hb", "data-step") == step, "offscreen, the loop holds still"
            page.locator("#nhg-benefits .hb").scroll_into_view_if_needed()
            page.wait_for_selector("#nhg-benefits .hb.live")
            page.evaluate("""() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
                                     document.dispatchEvent(new Event('visibilitychange')); }""")
            assert not page.evaluate("document.querySelector('#nhg-benefits .hb').classList.contains('live')")
        finally:
            browser.close()


def test_reduced_motion_shows_the_final_frame(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, reduced=True)
            page.wait_for_timeout(500)
            data = page.evaluate(
                """() => { const fig = document.querySelector('#nhg-benefits .hb'), op = s => +getComputedStyle(document.querySelector(s)).opacity;
                  return { anim: fig.classList.contains('hb--anim'), step: fig.dataset.step,
                           panels: [...fig.querySelectorAll('.hb-panel')].map(p => +getComputedStyle(p).opacity),
                           go: op('.hb-go'), nogo: op('.hb-nogo'), x: op('.hb-x'),
                           marks: fig.querySelectorAll('.hb-mark svg').length,
                           mocks: [...document.querySelectorAll('[data-tm]')].map(m => ({ step: m.dataset.tmStep, anim: m.classList.contains('tm--anim'),
                             hidden: [...m.querySelectorAll('.tm-l, .tm-cmd, .tm-end')].filter(e => getComputedStyle(e).visibility !== 'visible').length })) }; }"""
            )
        finally:
            browser.close()
    assert not data["anim"] and data["step"] == "all", data
    assert data["panels"] == [1, 1, 1, 1], data
    assert data["go"] == 1 and data["nogo"] == 0 and data["x"] == 1, data
    assert data["marks"] == len(PLATFORMS), "the icons still appear without motion"
    for mock in data["mocks"]:
        assert mock == {"step": "done", "anim": False, "hidden": 0}, mock


# --------------------------------------------------------------------------------- R45


def _real_sources() -> dict:
    names = ("install.ps1", "install.sh", "scripts/installer.ps1", "scripts/installer.sh", "scripts/lib/integrations/runner.py")
    return {n: (ROOT / n).read_text(encoding="utf-8") for n in names}


@pytest.mark.parametrize("os_key", list(COMMANDS))
def test_each_tab_shows_its_icon_steps_and_terminal(playwright_mod, os_key: str) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, hash_="#home/install")
            page.click(f"#install-tab-{os_key}")
            data = page.evaluate(
                """os => { const panel = document.getElementById('install-panel-' + os), tm = panel.querySelector('[data-tm]');
                  const bar = tm.querySelector('.tm-bar').getBoundingClientRect();
                  const ctl = tm.querySelector('.tm-ctl, .tm-lights').getBoundingClientRect();
                  const wrap = panel.querySelector('.tm-wrap');
                  return { icon: !!panel.querySelector('.inst-os[data-os="' + os + '"] svg'),
                           steps: [...panel.querySelectorAll('.inst-list li')].map(li => li.textContent.replace(/^\\d+/, '').trim()),
                           kbd: panel.querySelectorAll('kbd').length,
                           cls: [...tm.classList], bg: getComputedStyle(tm.querySelector('.tm-body')).backgroundColor,
                           ctlSide: ctl.left - bar.left < bar.right - ctl.right ? 'left' : 'right',
                           lights: tm.querySelectorAll('.tm-lights i').length,
                           hidden: tm.getAttribute('aria-hidden'), role: wrap.getAttribute('role'), label: wrap.getAttribute('aria-label'),
                           cmd: tm.querySelector('.tm-cmd').textContent.trim(),
                           order: [...panel.querySelector('.inst').children].map(e => e.className.split(' ')[0]) }; }""",
                os_key,
            )
        finally:
            browser.close()
    skin, bg, side = CHROME[os_key]
    assert data["icon"], "the system's icon"
    assert data["steps"] == STEPS[os_key] and data["kbd"] == 0
    assert data["order"] == ["inst-steps", "term", "tm-wrap"], "steps, the command box, then the mockup"
    assert skin in data["cls"] and data["bg"] == bg, data
    assert data["ctlSide"] == side, data
    assert data["lights"] == (3 if os_key == "mac" else 0)
    assert data["hidden"] == "true" and data["role"] == "img" and data["label"], data
    assert not re.search(r"\byou\b", data["label"], re.I)
    assert data["cmd"] == COMMANDS[os_key], "the mockup pastes the exact command"


@pytest.mark.parametrize("os_key", list(COMMANDS))
def test_the_mocked_output_comes_from_the_real_installer(playwright_mod, os_key: str) -> None:
    sources = _real_sources()
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            lines = page.evaluate(
                """os => [...document.querySelectorAll('#install-panel-' + os + ' .tm-l')].map(l => {
                    const lit = [], vars = [];
                    const walk = n => { for (const c of n.childNodes) {
                      if (c.nodeType === 3) lit.push(c.textContent); else if (c.tagName === 'VAR') vars.push(c.textContent); else walk(c); } };
                    walk(l); return { src: l.dataset.src, text: l.textContent, lit, vars }; })""",
                os_key,
            )
        finally:
            browser.close()
    assert 8 <= len(lines) <= 12, len(lines)
    assert lines[-1]["text"].endswith("installed (Global scope)."), "the mockup ends on the done message"
    family = "install.ps1" if os_key == "win" else "install.sh"
    core = "scripts/installer.ps1" if os_key == "win" else "scripts/installer.sh"
    assert {line["src"] for line in lines} == {family, core, "scripts/lib/integrations/runner.py"}
    for line in lines:
        source = sources[line["src"]]
        for chunk in line["lit"]:
            assert chunk.strip() in source, f"{line['src']} never prints {chunk.strip()!r} ({line['text']!r})"
        for value in line["vars"]:
            assert value in source or value in DYNAMIC, f"{value!r} is neither in {line['src']} nor a run-time value"
    texts = [line["text"] for line in lines]
    assert any(t.startswith("Welcome to the Nexus-Hub Universal Installer") for t in texts)
    assert any("installed (Global scope)." in t for t in texts), "the mockup ends on the real done message"


def test_the_mockup_plays_paste_enter_output_and_restarts_on_a_tab_switch(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, hash_="#home/install")
            page.click("#install-tab-linux")
            tm = "#install-panel-linux [data-tm]"
            # Record every step as it happens; polling can miss a short step on a busy machine.
            page.evaluate(
                """sel => { const m = document.querySelector(sel), vis = e => getComputedStyle(e).visibility === 'visible';
                  window.tmSeen = {};
                  new MutationObserver(() => { const step = m.dataset.tmStep;
                    if (!(step in window.tmSeen)) window.tmSeen[step] = { cmd: vis(m.querySelector('.tm-cmd')),
                      lines: [...m.querySelectorAll('.tm-l')].filter(vis).length, total: m.querySelectorAll('.tm-l').length,
                      end: vis(m.querySelector('.tm-end')) }; }).observe(m, { attributes: true, attributeFilter: ['data-tm-step'] }); }""",
                tm,
            )
            page.locator(tm).scroll_into_view_if_needed()
            page.wait_for_function("['prompt', 'paste', 'run', 'done'].every(s => window.tmSeen && s in window.tmSeen)", timeout=25000)
            seen = page.evaluate("window.tmSeen")
            # The click scrolls the tab row into view; the mockup plays once it is on screen too.
            page.click("#install-tab-mac")
            page.locator("#install-panel-mac [data-tm]").scroll_into_view_if_needed()
            page.wait_for_selector('#install-panel-mac [data-tm][data-tm-step="prompt"]', timeout=5000)
            mac_lines = page.evaluate("[...document.querySelectorAll('#install-panel-mac .tm-l')].filter(e => getComputedStyle(e).visibility === 'visible').length")
        finally:
            browser.close()
    assert seen["prompt"]["cmd"] is False and seen["prompt"]["lines"] == 0
    assert seen["paste"]["cmd"] is True and seen["paste"]["lines"] == 0, "pasted at once, before Enter"
    assert seen["done"]["lines"] == seen["done"]["total"] and seen["done"]["end"], seen
    assert mac_lines == 0, "switching tabs starts that system's mockup from the prompt"


@pytest.mark.parametrize("os_key", list(COMMANDS))
def test_no_overflow_or_scroll_bars_at_390(playwright_mod, os_key: str) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, width=390, height=844, hash_="#home/install")
            page.click(f"#install-tab-{os_key}")
            result = page.evaluate(
                """() => { const out = [];
                  for (const id of ['nhg-benefits', 'nhg-install']) { const s = document.getElementById(id), sr = s.getBoundingClientRect();
                    for (const e of s.querySelectorAll('*')) { if (!e.getClientRects().length) continue; const r = e.getBoundingClientRect();
                      if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible') out.push('scroll ' + e.className);
                      if (r.width > 0 && (r.left < sr.left - 1 || r.right > sr.right + 1)) out.push('outside ' + (e.className.baseVal ?? e.className)); } }
                  return { doc: document.documentElement.scrollWidth - document.documentElement.clientWidth, out }; }"""
            )
        finally:
            browser.close()
    assert result == {"doc": 0, "out": []}, result


def test_each_system_reads_with_the_same_logo_and_label_everywhere(playwright_mod) -> None:
    """R45 follow-up: the tab, the step label, and the Detected note pair one logo with one label."""
    names = {"win": "Windows", "mac": "macOS", "linux": "Linux"}
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, hash_="#home/install")
            data = page.evaluate(
                """() => { const pair = el => { const svg = el.querySelector('svg.os-logo'), r = svg.getBoundingClientRect();
                    return { use: svg.querySelector('use').getAttribute('href'), hidden: svg.getAttribute('aria-hidden'),
                             text: el.textContent.trim(), h: Math.round(r.height), font: Math.round(parseFloat(getComputedStyle(el).fontSize)),
                             fill: getComputedStyle(svg).fill, color: getComputedStyle(el).color }; };
                  const tabs = [...document.querySelectorAll('#nhg-install [role=tab]')].map(t => [t.dataset.tab, pair(t), Math.round(t.getBoundingClientRect().height)]);
                  const steps = [...document.querySelectorAll('#nhg-install .inst-os')].map(p => { p.closest('.tab-panel').hidden = false; return [p.dataset.os, pair(p)]; });
                  return { tabs, steps, note: pair(document.getElementById('install-detected')) }; }"""
            )
        finally:
            browser.close()
    heights = {h for _key, _pair, h in data["tabs"]}
    assert len(heights) == 1, "no layout jump between tabs"
    for key, pair, _h in data["tabs"]:
        assert pair["use"] == f"#os-{key}" and pair["hidden"] == "true" and pair["text"] == names[key], pair
        assert abs(pair["h"] - pair["font"]) <= 1 and pair["fill"] == pair["color"], "text height, current colour"
    for key, pair in data["steps"]:
        assert pair["use"] == f"#os-{key}" and pair["text"] == names[key], pair
    assert data["note"]["use"] == "#os-win" and data["note"]["text"] == "Detected: Windows"
