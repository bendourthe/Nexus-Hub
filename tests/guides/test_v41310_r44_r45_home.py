"""v4.13.10 R44, R45, and R47: the Home hero benefits figure and the illustrated install walkthrough.

R44 removed the hero button row and the "Raw Prompting Limits" cards. R47 (revision 17) folds the
benefits figure into the hero: no "Harness Benefits" heading, one platform row whose five circles
each hold a logo and a name, lines from those circles into the Nexus Hub mark, and four panels
(Depth, Safety, Cross-Platform, Transparency) whose illustrations show their lines. R45 gives each
install tab numbered steps beside the system's icon and an animated mockup of that system's
terminal running the installer, whose output must come from the real installer scripts. R49 makes
every terminal dark and neutral, adds the mouse that right-clicks to paste (PowerShell pastes on the
click; macOS and GNOME open a menu), and replays the installer's own output, its wordmark included,
with every line tracing to the installer line(s) it names in data-src. The copy
chip, detection, and stored choice are covered by test_v41310_r38_install.py.

Browser tests skip when Playwright or Chromium is missing and fail closed under
NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

PLATFORMS = ["Claude", "ChatGPT", "Gemini", "Cursor", "GitHub Copilot"]
BENEFITS = [("depth", "Depth"), ("safety", "Safety"), ("cross-platform", "Cross-Platform"), ("transparency", "Transparency")]
DOMAINS = ["Security", "Testing", "Docs", "Architecture", "DevOps"]
FIG = "#nhg-benefits.hb"
INSTALL_SH = "curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash"
INSTALL_PS = "irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex"
COMMANDS = {"win": INSTALL_PS, "mac": INSTALL_SH, "linux": INSTALL_SH}
STEPS = {
    "win": ["Press the Windows key, or click Start.", "Type PowerShell and press Enter.", "Paste the command and press Enter."],
    "mac": ["Press Cmd + Space to open Spotlight.", "Type Terminal and press Enter.", "Paste the command and press Enter."],
    "linux": ["Press Ctrl + Alt + T, or open Terminal from the applications menu.", "Paste the command and press Enter."],
}
# Each system's own terminal look: skin class, a dark neutral window (R49: no blue PowerShell,
# no aubergine GNOME), and where the window controls sit.
CHROME = {
    "win": ("tm--win", "rgb(12, 12, 12)", "right"),
    "mac": ("tm--mac", "rgb(30, 30, 30)", "left"),
    "linux": ("tm--gnome", "rgb(30, 30, 30)", "right"),
}
# Values the real installer computes at run time (repository and branch, home and catalog paths,
# version, scope, the verified platform and its surfaces, and the PowerShell check mark, which the
# source writes as [char]0x2713). The mockup marks each one with <var>; everything else must be
# literal text on an installer line the mocked line cites.
DYNAMIC = {
    "bendourthe/Nexus-Hub@main", "main", "C:\\Users\\dev", "/Users/dev", "/home/dev", "4.13.10", "Global",
    "Claude", "commands:ok, skills:ok, CLAUDE.md SKILL_INDEX:ok", "\u2713",
}
DYNAMIC_PATHS = ("C:\\Users\\dev\\", "/Users/dev/", "/home/dev/")
# R49 playback: PowerShell pastes on right-click; macOS Terminal and GNOME Terminal open a menu.
SEQUENCE = {
    "win": ["prompt", "move", "click", "paste", "enter", "run", "done"],
    "mac": ["prompt", "move", "click", "menu", "pick", "paste", "enter", "run", "done"],
    "linux": ["prompt", "move", "click", "menu", "pick", "paste", "enter", "run", "done"],
}
# The flow every mockup shows, in order: the bootstrap, the wordmark, the welcome, the sections, done.
MILESTONES = ["Downloading Nexus-Hub catalog", "Extracting catalog to", "Running installer from", "\u2588\u2588\u2588\u2557",
              "Multi-platform AI skill harness", "Welcome to the Nexus-Hub Universal Installer", "SKILLS & COMMANDS",
              "AUTO-APPROVE PERMISSIONS", "INSTALL VERIFICATION", "installed (Global scope)."]


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
    page.wait_for_selector(FIG)
    return context, page


def _home_source() -> str:
    text = GUIDE.read_text(encoding="utf-8")
    start = text.index('id="page-home"')
    return text[start: text.index('<section class="page', start + 10)]


def _panel_text(benefit: str) -> str:
    home = _home_source()
    start = home.index(f'data-benefit="{benefit}"')
    return re.sub(r"<[^>]+>", " ", home[start: home.index("</li>", home.index("<h3", start))])


# --------------------------------------------------------------------------------- source


def test_the_hero_has_no_button_row() -> None:
    home = _home_source()
    hero = home[: home.index('id="nhg-install"')]
    assert 'class="btn-row"' not in hero and 'class="btn' not in hero, "the hero keeps no buttons"
    for label in ("Get trained", "Open Cheatsheets", 'href="#home/install"'):
        assert label not in hero, label
    assert "Raw Prompting Limits" not in home and 'id="nhg-why"' not in home


def test_no_harness_benefits_heading_and_one_platform_row() -> None:
    home = _home_source()
    assert "Harness Benefits" not in home, "R47: the figure is part of the hero, without a heading"
    assert home.count('class="platform-rail"') == 1 and "hb-plats" not in home and "hb-mark" not in home


def test_safety_names_no_specific_command() -> None:
    text = _panel_text("safety")
    assert "Potentially dangerous request" in text
    assert not re.search(r"\b(git|rm|sudo|push|chmod|del|drop)\b|--|-rf", text, re.I), text


# --------------------------------------------------------------------------------- rendered


def test_the_figure_sits_in_the_hero_and_installation_follows(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            data = page.evaluate(
                """() => { const box = document.querySelector('#page-home > .container'), hero = box.querySelector('.hero');
                  return { buttons: document.querySelectorAll('#page-home .hero .btn, #page-home .hero .btn-row').length,
                           order: [...box.children].map(e => e.id || e.className).slice(0, 2),
                           hero: [...hero.children].map(e => e.id || e.classList[0]),
                           headings: [...hero.querySelectorAll('h2')].length }; }"""
            )
        finally:
            browser.close()
    assert data["buttons"] == 0, data
    assert data["order"] == ["hero", "nhg-install"], data
    assert data["hero"] == ["hero-lockup", "hero-subtitle", "hero-lead", "nhg-benefits"], "the figure follows the lead"
    assert data["headings"] == 0, "no section heading inside the hero"


def test_four_illustrated_panels_name_the_benefits(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            panels = page.evaluate(
                """() => [...document.querySelectorAll('#nhg-benefits .hb-panel')].map(p => ({
                    key: p.dataset.benefit, title: p.querySelector('h3').textContent.trim(),
                    line: p.querySelector('p').textContent.trim(), ill: p.querySelectorAll('.hb-ill *').length,
                    hidden: p.querySelector('.hb-ill').getAttribute('aria-hidden') }))"""
            )
        finally:
            browser.close()
    assert [(p["key"], p["title"]) for p in panels] == BENEFITS
    for panel in panels:
        assert panel["ill"] >= 6 and panel["hidden"] == "true", f"{panel['key']}: the panel carries an illustration"
        assert 3 <= len(panel["line"].split()) <= 14, panel["line"]
        assert not re.search(r"\byou\b", panel["line"], re.I)


def test_five_circles_each_hold_a_logo_and_a_name(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in (1440, 390):
                _context, page = _open(browser, width=width, height=900 if width > 600 else 844)
                data = page.evaluate(
                    """() => { const rows = document.querySelectorAll('#page-home .platform-rail');
                      const inside = (r, c) => r.left >= c.left - 1 && r.right <= c.right + 1 && r.top >= c.top - 1 && r.bottom <= c.bottom + 1;
                      return { rows: rows.length, inFigure: !!rows[0].closest('#nhg-benefits'),
                        items: [...rows[0].querySelectorAll('.platform-item')].map(li => { const c = li.getBoundingClientRect(), s = getComputedStyle(li);
                          const logo = li.querySelector('.platform-mark svg').getBoundingClientRect(), name = li.querySelector('.platform-name');
                          return { name: name.textContent.trim(), w: c.width, h: c.height, round: s.borderTopLeftRadius,
                                   border: s.borderTopStyle, logo: inside(logo, c) && logo.width >= 24,
                                   label: inside(name.getBoundingClientRect(), c), size: parseFloat(getComputedStyle(name).fontSize) }; }) }; }"""
                )
                assert data["rows"] == 1 and data["inFigure"], data
                assert [i["name"] for i in data["items"]] == PLATFORMS
                for item in data["items"]:
                    assert abs(item["w"] - item["h"]) < 1 and item["w"] >= 80, (width, item)
                    assert item["round"] == "50%" and item["border"] == "solid", (width, item)
                    assert item["logo"] and item["label"] and item["size"] >= 15, (width, item)
        finally:
            browser.close()


def test_each_circle_flows_into_the_hub(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in (1440, 390):
                _context, page = _open(browser, width=width, height=900 if width > 600 else 844)
                data = page.evaluate(
                    """() => { const fig = document.getElementById('nhg-benefits'), f = fig.getBoundingClientRect();
                      const hub = fig.querySelector('.hb-hub svg').getBoundingClientRect();
                      const at = (w, l) => { const p = w.getPointAtLength(l); return [f.left + p.x, f.top + p.y]; };
                      return { circles: [...fig.querySelectorAll('.platform-item')].map(e => { const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.bottom]; }),
                               wires: [...fig.querySelectorAll('.hb-wires .hb-in')].map(w => [at(w, 0), at(w, w.getTotalLength())]),
                               outs: fig.querySelectorAll('.hb-wires .hb-out').length,
                               hub: [hub.left + hub.width / 2, hub.top], use: fig.querySelector('.hb-hub use').getAttribute('href') }; }"""
                )
                assert data["use"] == "#nexus-mark"
                assert len(data["wires"]) == len(PLATFORMS), data
                for (cx, bottom), (start, end) in zip(data["circles"], data["wires"]):
                    assert abs(start[0] - cx) < 2 and abs(start[1] - bottom) < 2, (width, start, cx, bottom)
                    assert abs(end[0] - data["hub"][0]) < 2 and abs(end[1] - data["hub"][1]) < 2, (width, end, data["hub"])
                assert data["outs"] == (4 if width > 860 else 0), "the mark feeds the panels while they share a row"
        finally:
            browser.close()


def test_each_illustration_shows_its_line(playwright_mod) -> None:
    """The final frame: every label reads at the caption size and matches its panel's line."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in (1440, 390):
                _context, page = _open(browser, width=width, height=900 if width > 600 else 844, reduced=True)
                data = page.evaluate(
                    """() => { const P = k => document.querySelector(`.hb-panel[data-benefit="${k}"]`);
                      const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility === 'visible' && +getComputedStyle(e).opacity > 0;
                      const shown = (p, s) => [...p.querySelectorAll(s)].filter(vis).map(e => e.textContent.trim());
                      const within = (a, b) => { a = a.getBoundingClientRect(); b = b.getBoundingClientRect();
                        return a.left >= b.left - 1 && a.right <= b.right + 1 && a.top >= b.top - 1 && a.bottom <= b.bottom + 1; };
                      const caption = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ty-caption')) * 16;
                      const labels = [...document.querySelectorAll('#nhg-benefits .hb-ill [data-ty]')].filter(vis);
                      const d = P('depth'), s = P('safety'), x = P('cross-platform'), t = P('transparency');
                      return { caption, small: labels.filter(e => parseFloat(getComputedStyle(e).fontSize) < caption).map(e => e.textContent),
                        depth: { count: d.querySelector('p [data-count="skills"]').textContent, badges: shown(d, '.hb-badges li'),
                                 model: shown(d, '.hb-node'), state: shown(d, '.hb-state > *') },
                        safety: { req: shown(s, '.hb-req .hb-k'), state: shown(s, '.hb-state > *'), guard: vis(s.querySelector('.hb-guard')),
                                  mark: s.querySelector('.hb-guard use').getAttribute('href'), run: getComputedStyle(s.querySelector('.hb-run')).textDecorationLine,
                                  agent: shown(s, '.hb-track .hb-k') },
                        xp: { names: shown(x, '.hb-pf > .hb-k'), limit: shown(x, '.hb-lim'), resumed: shown(x, '.hb-res'),
                              meter: x.querySelector('.hb-meter i').getBoundingClientRect().width / x.querySelector('.hb-meter').getBoundingClientRect().width,
                              taskInB: within(x.querySelector('.hb-task'), x.querySelector('.hb-pf--b')), dots: x.querySelectorAll('.hb-task .hb-dots i').length },
                        tr: { report: shown(t, '.hb-report > .hb-k'), lines: t.querySelectorAll('.hb-ln i').length, gauge: vis(t.querySelector('.hb-g1')),
                              usage: shown(t, '.hb-gauge .hb-k'), note: shown(t, '.hb-note'), noteInRecord: within(t.querySelector('.hb-note'), t.querySelector('.hb-report')) } }; }"""
                )
                assert data["caption"] >= 15 and data["small"] == [], (width, data["small"])
                depth = data["depth"]
                assert depth["count"].isdigit() and int(depth["count"]) > 100, "the skill count stays dynamic"
                assert depth["badges"] == DOMAINS and depth["model"] == ["Model"] and depth["state"] == ["Skilled"], depth
                safety = data["safety"]
                assert safety["req"] == ["Potentially dangerous request"] and safety["state"] == ["Blocked"], safety
                assert safety["guard"] and safety["mark"] == "#nexus-mark" and safety["run"] == "line-through", safety
                assert safety["agent"] == ["Agent"]
                xp = data["xp"]
                assert xp["names"] == ["Platform A", "Platform B"] and xp["limit"] == ["Limit"] and xp["resumed"] == ["Resumed"], xp
                assert xp["meter"] > 0.98 and xp["taskInB"] and xp["dots"] == 3, xp
                tr = data["tr"]
                assert tr["report"] == ["Report"] and tr["lines"] == 3 and tr["gauge"] and tr["usage"] == ["Usage"], tr
                assert tr["note"] == ["Lessons"] and tr["noteInRecord"], tr
        finally:
            browser.close()


def test_the_moments_play_in_order(playwright_mod) -> None:
    """Safety: pending, then the shield, then blocked. Cross-Platform: the limit, then the move, then resumed."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            page.locator("#nhg-benefits .hb-panels").scroll_into_view_if_needed()
            frames = {}
            for key, step, times in (("safety", "2", (300, 1560, 2400)), ("cross-platform", "3", (300, 1660, 2100, 3000))):
                page.wait_for_selector(f'{FIG}.live[data-step="{step}"]', timeout=30000)
                frames[key] = [page.evaluate(
                    """([k, t]) => { const p = document.querySelector(`.hb-panel[data-benefit="${k}"]`);
                      for (const a of p.getAnimations({ subtree: true })) { a.pause(); a.currentTime = t; }
                      const vis = s => { const e = p.querySelector(s); return getComputedStyle(e).visibility === 'visible' && +getComputedStyle(e).opacity > 0.5; };
                      const r = s => p.querySelector(s).getBoundingClientRect();
                      return k === 'safety' ? { pending: vis('.hb-was'), blocked: vis('.hb-now'), guard: vis('.hb-guard') }
                        : { limit: vis('.hb-lim'), resumed: vis('.hb-res'), x: r('.hb-task').left - r('.hb-pf--a').left }; }""",
                    [key, t]) for t in times]
                page.evaluate("k => { for (const a of document.querySelector(`.hb-panel[data-benefit=\"${k}\"]`).getAnimations({ subtree: true })) a.play(); }", key)
        finally:
            browser.close()
    s = frames["safety"]
    assert s[0] == {"pending": True, "blocked": False, "guard": False}, s
    assert s[1]["pending"] and s[1]["guard"] and not s[1]["blocked"], "the shield intercepts before the request is marked"
    assert s[2] == {"pending": False, "blocked": True, "guard": True}, s
    x = frames["cross-platform"]
    assert not x[0]["limit"] and x[1]["limit"] and not x[1]["resumed"], x
    assert x[0]["x"] <= x[1]["x"] < x[2]["x"] < x[3]["x"], "the task card moves from A toward B"
    assert x[3]["resumed"], x


def test_the_loop_lights_each_panel_in_turn(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            page.locator(FIG).scroll_into_view_if_needed()
            states = []
            for step in ("1", "2", "3", "4"):
                page.wait_for_selector(f'{FIG}.live[data-step="{step}"]', timeout=25000)
                page.wait_for_timeout(700)
                states.append(page.evaluate(
                    """() => [...document.querySelectorAll('#nhg-benefits .hb-panel')].map(p => [
                        p.classList.contains('is-on'), p.classList.contains('is-done'), +getComputedStyle(p).opacity,
                        getComputedStyle(p).boxShadow !== 'none',
                        [...p.children].findIndex(e => e.tagName === 'H3') < [...p.children].findIndex(e => e.classList.contains('hb-ill'))])"""
                ))
        finally:
            browser.close()
    for n, state in enumerate(states, 1):
        assert [s[0] for s in state] == [i == n for i in range(1, 5)], (n, state)
        assert [s[1] for s in state] == [i < n for i in range(1, 5)], (n, state)
        # Review 20: no panel fades; only the active one carries the accent outline, and every panel
        # reads title and text before its illustration.
        assert all(s[2] == 1 for s in state), ("no panel fades", n, state)
        assert [s[3] for s in state] == [i == n for i in range(1, 5)], ("outline on the active panel only", n, state)
        assert all(s[4] for s in state), ("title and text sit above the illustration", n, state)


def test_the_loop_stops_offscreen_and_in_a_hidden_tab(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser)
            page.locator(FIG).scroll_into_view_if_needed()
            page.wait_for_selector(f'{FIG}.live[data-step="1"]', timeout=10000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_function("!document.getElementById('nhg-benefits').classList.contains('live')")
            step = page.get_attribute(FIG, "data-step")
            page.wait_for_timeout(4000)
            assert page.get_attribute(FIG, "data-step") == step, "offscreen, the loop holds still"
            page.locator(FIG).scroll_into_view_if_needed()
            page.wait_for_selector(f"{FIG}.live")
            page.evaluate("""() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
                                     document.dispatchEvent(new Event('visibilitychange')); }""")
            assert not page.evaluate("document.getElementById('nhg-benefits').classList.contains('live')")
        finally:
            browser.close()


def test_reduced_motion_shows_the_final_frame(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, reduced=True)
            page.wait_for_timeout(500)
            data = page.evaluate(
                """() => { const fig = document.getElementById('nhg-benefits'), op = s => +getComputedStyle(fig.querySelector(s)).opacity;
                  const vis = s => getComputedStyle(fig.querySelector(s)).visibility;
                  return { anim: fig.classList.contains('hb--anim'), step: fig.dataset.step,
                           running: fig.getAnimations({ subtree: true }).length,
                           panels: [...fig.querySelectorAll('.hb-panel')].map(p => +getComputedStyle(p).opacity),
                           guard: op('.hb-guard'), note: op('.hb-note'), res: op('.hb-res'), lim: op('.hb-lim'),
                           was: [...fig.querySelectorAll('.hb-was')].map(e => getComputedStyle(e).visibility),
                           now: [...fig.querySelectorAll('.hb-now')].map(e => getComputedStyle(e).visibility + ':' + getComputedStyle(e).opacity),
                           wires: fig.querySelectorAll('.hb-wires .hb-in').length,
                           marks: fig.querySelectorAll('.platform-mark svg').length,
                           mocks: [...document.querySelectorAll('[data-tm]')].map(m => ({ step: m.dataset.tmStep, anim: m.classList.contains('tm--anim'),
                             hidden: [...m.querySelectorAll('.tm-l, .tm-cmd, .tm-end')].filter(e => getComputedStyle(e).visibility !== 'visible').length,
                             mouse: getComputedStyle(m.querySelector('.tm-ms')).opacity,
                             extras: [...m.querySelectorAll('.tm-menu, .tm-key')].map(e => getComputedStyle(e).visibility),
                             wordmark: m.querySelector('.tm-wm').textContent.split('\\n').length })) }; }"""
            )
        finally:
            browser.close()
    assert not data["anim"] and data["step"] == "all" and data["running"] == 0, data
    assert data["panels"] == [1, 1, 1, 1], data
    assert data["guard"] == 1 and data["note"] == 1 and data["res"] == 1 and data["lim"] == 1, data
    assert data["was"] == ["hidden", "hidden"] and data["now"] == ["visible:1", "visible:1"], data
    assert data["wires"] == len(PLATFORMS), "the lines are drawn without motion too"
    assert data["marks"] == len(PLATFORMS), "the icons still appear without motion"
    for mock in data["mocks"]:
        assert {k: mock[k] for k in ("step", "anim", "hidden")} == {"step": "done", "anim": False, "hidden": 0}, mock
        assert mock["mouse"] == "0" and set(mock["extras"]) == {"hidden"}, "the finished output shows no mouse, menu, or Enter cue"
        assert mock["wordmark"] == 6, "the installer's wordmark is part of the finished output"


# --------------------------------------------------------------------------------- R45


def _real_sources() -> dict:
    names = ("install.ps1", "install.sh", "scripts/installer.ps1", "scripts/installer.sh", "scripts/lib/integrations/runner.py")
    return {n: (ROOT / n).read_text(encoding="utf-8").split("\n") for n in names}


def _assert_dark_neutral(css: str) -> None:
    """R49: a regular dark terminal. Near black (low relative luminance) and grey (no hue cast)."""
    r, g, b = (int(v) for v in re.findall(r"\d+", css)[:3])
    lin = [((c / 255) / 12.92 if c / 255 <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4) for c in (r, g, b)]
    luminance = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    assert luminance < 0.03, f"{css} is not dark (luminance {luminance:.3f})"
    assert max(r, g, b) - min(r, g, b) <= 6, f"{css} has a colour cast (blue PowerShell or aubergine GNOME)"


def _banner(lines: list, start: str, close: str) -> str:
    """The wordmark as the installer prints it: the six lines inside the here-string or heredoc."""
    fn = next(i for i, t in enumerate(lines) if start in t)
    a = next(i for i in range(fn, len(lines)) if lines[i].rstrip().endswith(("@'", "<<'NEXUS_BANNER_EOF'"))) + 1
    b = next(i for i in range(a, len(lines)) if lines[i].startswith(close))
    return "\n".join(lines[a:b])


def _cited(sources: dict, src: str) -> tuple:
    """'file:12,40' or 'file:3591-3596' -> (file, [line numbers])."""
    name, refs = src.rsplit(":", 1)
    nums = []
    for ref in refs.split(","):
        lo, _, hi = ref.partition("-")
        nums.extend(range(int(lo), int(hi or lo) + 1))
    assert name in sources and all(1 <= n <= len(sources[name]) for n in nums), src
    return name, nums


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
                           cls: [...tm.classList], bg: getComputedStyle(tm).backgroundColor,
                           bodyBg: getComputedStyle(tm.querySelector('.tm-body')).backgroundColor,
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
    assert data["bodyBg"] == "rgba(0, 0, 0, 0)", "the window colour shows through; no tinted body"
    _assert_dark_neutral(data["bg"])
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
                    walk(l); return { src: l.dataset.src || null, cls: l.className, text: l.textContent, lit, vars,
                                      color: getComputedStyle(l).color }; })""",
                os_key,
            )
            end = page.evaluate("os => { const e = document.querySelector('#install-panel-' + os + ' .tm-end'); return { src: e.dataset.src || null, builtin: e.dataset.builtin || null, text: e.textContent.trim() }; }", os_key)
        finally:
            browser.close()
    family = "install.ps1" if os_key == "win" else "install.sh"
    core = "scripts/installer.ps1" if os_key == "win" else "scripts/installer.sh"
    allowed = {family, core, "scripts/lib/integrations/runner.py"}
    traced = 0
    for line in lines:
        text = line["text"]
        if not line["src"]:
            # Untraced lines are only the installer's blank lines and a dimmed elision.
            assert text.strip() in ("", "..."), f"untraced line {text!r}"
            assert (text.strip() == "...") == ("tm-skip" in line["cls"]), line
            continue
        name, nums = _cited(sources, line["src"])
        assert name in allowed, line["src"]
        cited = "\n".join(sources[name][n - 1] for n in nums)
        for chunk in line["lit"]:
            assert chunk.strip() in cited, f"{line['src']} does not print {chunk.strip()!r} ({text!r})"
        for value in line["vars"]:
            assert value in cited or value in DYNAMIC or value.startswith(DYNAMIC_PATHS), f"{value!r} is neither on {line['src']} nor a run-time value"
        traced += 1
    assert traced >= 20, f"{traced} traced lines"
    texts = [line["text"] for line in lines]
    at = [next(i for i, t in enumerate(texts) if m in t) for m in MILESTONES]
    assert at == sorted(at), "the installer's flow, in order: bootstrap, wordmark, welcome, sections, done"
    shown = [t for t in texts if t.strip() not in ("", "...")]
    if os_key == "win":
        # Show-FarewellBanner follows the done line; an interactive console then pauses.
        assert shown[-2].endswith("installed (Global scope).") and shown[-1].endswith("installed."), shown[-2:]
        name, nums = _cited(sources, end["src"])
        assert end["builtin"] == "Pause" and "Pause" in sources[name][nums[0] - 1] and end["text"].startswith("Press Enter to continue")
    else:
        assert shown[-1].endswith("installed (Global scope)."), shown[-1]
        assert end["src"] is None and end["text"].endswith(("~ %", "~$")), "the prompt returns"
    for line in lines:
        if "Welcome to the Nexus-Hub" in line["text"] or "tm-wm" in line["cls"]:
            assert "tm-c" in line["cls"] and line["color"] != "rgb(204, 204, 204)", "the installer prints these in cyan"


def test_the_wordmark_is_the_installers_own(playwright_mod) -> None:
    """The styled title, character for character, written as numeric references so the page stays ASCII."""
    sources = _real_sources()
    ps = _banner(sources["scripts/installer.ps1"], "function Write-NexusBanner", "'@")
    sh = _banner(sources["scripts/installer.sh"], "print_nexus_banner() {", "NEXUS_BANNER_EOF")
    assert ps == sh and len(ps.split("\n")) == 6 and "\u2588" in ps
    raw = GUIDE.read_bytes()
    install = raw[raw.index(b'id="nhg-install"'): raw.index(b'id="nhg-copy-status"')]
    assert all(byte < 128 for byte in install), "the install section is ASCII; box characters are character references"
    pre = re.search(rb'<pre class="tm-l tm-c tm-wm" data-src="([^"]+)">(.*?)</pre>', install, re.S)
    assert pre and b"&#9608;" in pre.group(2)
    assert html.unescape(pre.group(2).decode("ascii")) == ps, "the source holds the installer's wordmark exactly"
    name, nums = _cited(sources, pre.group(1).decode())
    assert "\n".join(sources[name][n - 1] for n in nums) == ps, "the cited lines are the banner"
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, hash_="#home/install")
            shown = page.evaluate("() => [...document.querySelectorAll('[data-tm] .tm-wm')].map(p => [p.closest('[data-tm]').dataset.tm, p.textContent, p.dataset.src])")
        finally:
            browser.close()
    assert [k for k, _t, _s in shown] == ["win", "mac", "linux"]
    for key, text, src in shown:
        assert text == (ps if key == "win" else sh), f"{key}: the wordmark differs from the installer"
        assert src.startswith("scripts/installer.ps1:" if key == "win" else "scripts/installer.sh:"), src


@pytest.mark.parametrize("os_key", list(COMMANDS))
def test_the_mouse_right_clicks_pastes_and_the_output_streams(playwright_mod, os_key: str) -> None:
    """R49: the prompt idles, the mouse moves onto the window and right-clicks; PowerShell pastes on the
    click, macOS and GNOME open a menu and the mouse picks Paste; then Enter, the output, and done."""
    tm = f"#install-panel-{os_key} [data-tm]"
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, hash_="#home/install")
            page.click(f"#install-tab-{os_key}")
            # Record every step as it happens; polling can miss a short step on a busy machine.
            page.evaluate(
                """sel => { const m = document.querySelector(sel), vis = e => !!e && getComputedStyle(e).visibility === 'visible';
                  window.tmOrder = [];
                  new MutationObserver(() => { const step = m.dataset.tmStep, o = window.tmOrder;
                    if (o.length && o[o.length - 1].step === 'done') return;
                    o.push({ step, cmd: vis(m.querySelector('.tm-cmd')), menu: vis(m.querySelector('.tm-menu')), key: vis(m.querySelector('.tm-key')),
                             lines: [...m.querySelectorAll('.tm-l')].filter(vis).length, total: m.querySelectorAll('.tm-l').length,
                             end: vis(m.querySelector('.tm-end')) }); }).observe(m, { attributes: true, attributeFilter: ['data-tm-step'] }); }""",
                tm,
            )
            # Start from a clean loop: off screen it stops, back on screen it restarts at the prompt.
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_function("sel => !document.querySelector(sel).classList.contains('is-live')", arg=tm)
            page.evaluate("window.tmOrder = []")
            page.locator(tm).scroll_into_view_if_needed()
            page.wait_for_selector(f'{tm}[data-tm-step="click"]', timeout=15000)
            page.wait_for_timeout(250)
            click = page.evaluate(
                """sel => { const m = document.querySelector(sel), ms = m.querySelector('.tm-ms').getBoundingClientRect(), b = m.querySelector('.tm-body').getBoundingClientRect();
                  return { opacity: getComputedStyle(m.querySelector('.tm-ms')).opacity, inBody: ms.left > b.left && ms.left < b.right && ms.top > b.top && ms.top < b.bottom }; }""",
                tm,
            )
            pick = None
            if os_key != "win":
                # Sample inside the 750 ms pick step once the mouse has landed; a fixed wait after the
                # step starts can land in the paste step on a slow runner, where the highlight is gone.
                pick = page.wait_for_function(
                    """sel => { const m = document.querySelector(sel);
                      if (m.dataset.tmStep !== 'pick') return null;
                      const p = m.querySelector('.tm-paste'), r = p.getBoundingClientRect(), ms = m.querySelector('.tm-ms').getBoundingClientRect();
                      const onPaste = ms.left >= r.left && ms.left <= r.right && ms.top >= r.top && ms.top <= r.bottom;
                      if (!onPaste) return null;
                      return { items: [...m.querySelectorAll('.tm-menu span')].map(s => s.textContent), lit: getComputedStyle(p).backgroundColor, onPaste }; }""",
                    arg=tm, polling="raf", timeout=30000,
                ).json_value()
            page.wait_for_function("window.tmOrder.length && window.tmOrder[window.tmOrder.length - 1].step === 'done'", timeout=45000)
            order = page.evaluate("window.tmOrder")
            menus = page.evaluate("os => document.querySelectorAll('#install-panel-' + os + ' .tm-menu').length", os_key)
        finally:
            browser.close()
    assert [o["step"] for o in order] == SEQUENCE[os_key], order
    assert menus == (0 if os_key == "win" else 1), "PowerShell pastes on right-click; the others open a menu"
    seen = {o["step"]: o for o in order}
    for step in ("prompt", "move", "click", "menu", "pick"):
        if step in seen:
            assert not seen[step]["cmd"] and seen[step]["lines"] == 0, (step, seen[step])
    assert seen["paste"]["cmd"] and seen["paste"]["lines"] == 0 and not seen["paste"]["menu"], "pasted at once, before Enter"
    assert seen["enter"]["key"] and seen["enter"]["lines"] == 0, "a brief Enter cue before the output"
    assert seen["done"]["lines"] == seen["done"]["total"] and seen["done"]["end"] and not seen["done"]["key"], seen["done"]
    assert click == {"opacity": "1", "inBody": True}, click
    if pick is not None:
        assert seen["menu"]["menu"], "the right-click opens the menu"
        assert pick["items"] == ["Copy", "Paste", "Select All"] and pick["lit"] != "rgba(0, 0, 0, 0)" and pick["onPaste"], pick


def test_a_tab_switch_restarts_that_systems_mockup(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, hash_="#home/install")
            page.click("#install-tab-linux")
            page.locator("#install-panel-linux [data-tm]").scroll_into_view_if_needed()
            page.wait_for_selector('#install-panel-linux [data-tm][data-tm-step="run"]', timeout=20000)
            # The click scrolls the tab row into view; the mockup plays once it is on screen too.
            page.click("#install-tab-mac")
            page.locator("#install-panel-mac [data-tm]").scroll_into_view_if_needed()
            page.wait_for_selector('#install-panel-mac [data-tm][data-tm-step="prompt"]', timeout=5000)
            mac = page.evaluate("""() => { const m = document.querySelector('#install-panel-mac [data-tm]');
                return { lines: [...m.querySelectorAll('.tm-l')].filter(e => getComputedStyle(e).visibility === 'visible').length,
                         cmd: getComputedStyle(m.querySelector('.tm-cmd')).visibility }; }""")
        finally:
            browser.close()
    assert mac == {"lines": 0, "cmd": "hidden"}, "switching tabs starts that system's mockup from the idle prompt"


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
