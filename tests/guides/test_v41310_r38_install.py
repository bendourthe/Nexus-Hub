"""v4.13.10 R38: the Home install section opens on the visitor's system.

A web page cannot open a terminal, so the section detects Windows, macOS, or Linux, selects
that tab, and gives two steps: open the terminal, then copy the exact command with one large
button. These tests load the page as each system, check the fallback and a stored manual
choice, read the clipboard after the copy button, and measure the narrow layout.

Browser tests skip when Playwright or Chromium is missing and fail closed under
NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
STORE_KEY = "nexus-hub-guide:install-os"

INSTALL_SH = "curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash"
INSTALL_PS = "irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex"
COMMANDS = {"win": INSTALL_PS, "mac": INSTALL_SH, "linux": INSTALL_SH}
NAMES = {"win": "Windows", "mac": "macOS", "linux": "Linux"}

# (user agent, client-hints platform or None when the API is absent, navigator.platform)
AGENTS = {
    "win": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Windows", "Win32"),
    "mac": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15", None, "MacIntel"),
    "linux": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Linux", "Linux x86_64"),
    "iphone": ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", None, "iPhone"),
    "android": ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36", "Android", "Linux armv81"),
    "chromeos": ("Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Chrome OS", "Linux x86_64"),
    "unknown": ("Mozilla/5.0 (compatible; ExampleBot/1.0)", "", ""),
}
EXPECTED = {"win": "win", "mac": "mac", "linux": "linux", "iphone": "mac", "android": "linux", "chromeos": "linux"}

# Playwright overrides the user-agent string only; the platform APIs report the host, so
# the init script pins them to the simulated system.
PLATFORM_INIT = """(() => { const hint = %s, plat = %s;
  Object.defineProperty(Navigator.prototype, 'userAgentData', { configurable: true,
    get: () => (hint === null ? undefined : { platform: hint, brands: [], mobile: false }) });
  Object.defineProperty(Navigator.prototype, 'platform', { configurable: true, get: () => plat }); })();"""


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


def _open(browser, agent: str, width: int = 1440, height: int = 900, stored: str | None = None):
    ua, hint, plat = AGENTS[agent]
    context = browser.new_context(viewport={"width": width, "height": height}, user_agent=ua)
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = context.new_page()
    page.add_init_script(PLATFORM_INIT % (json.dumps(hint), json.dumps(plat)))
    if stored is not None:
        # Seed once, so a reload shows what the page itself stored.
        page.add_init_script(
            "try { if (!sessionStorage.getItem('r38-seeded')) { "
            f"localStorage.setItem('{STORE_KEY}', '{stored}'); sessionStorage.setItem('r38-seeded', '1'); }} }} catch (e) {{}}"
        )
    page.goto(GUIDE.as_uri() + "#home/install")
    page.wait_for_selector("#nhg-install [role=tab][aria-selected=true]")
    return context, page


def _state(page) -> dict:
    return page.evaluate(
        """() => { const sel = document.querySelector('#nhg-install [role=tab][aria-selected=true]');
          const note = document.getElementById('install-detected');
          const shown = [...document.querySelectorAll('#nhg-install .tab-panel')].filter(p => !p.hidden && getComputedStyle(p).display !== 'none');
          return { tab: sel.dataset.tab, note: note.hidden ? null : note.textContent,
                   panels: shown.map(p => p.dataset.panel) }; }"""
    )


@pytest.mark.parametrize("agent", list(EXPECTED))
def test_the_section_opens_on_the_detected_system(playwright_mod, agent: str) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, agent)
            want = EXPECTED[agent]
            assert _state(page) == {"tab": want, "note": f"Detected: {NAMES[want]}", "panels": [want]}
        finally:
            browser.close()


def test_an_unknown_system_falls_back_to_windows_without_a_note(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, "unknown")
            assert _state(page) == {"tab": "win", "note": None, "panels": ["win"]}
        finally:
            browser.close()


def test_a_stored_manual_choice_beats_detection(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, "win", stored="linux")
            state = _state(page)
            assert state["tab"] == "linux" and state["panels"] == ["linux"]
            assert state["note"] == "Detected: Windows", "the note still reports the detected system"
            # A click stores the new choice, and a reload keeps it over detection.
            page.click("#install-tab-mac")
            assert page.evaluate(f"localStorage.getItem('{STORE_KEY}')") == "mac"
            page.reload()
            page.wait_for_selector("#nhg-install [role=tab][aria-selected=true]")
            assert _state(page)["tab"] == "mac"
            # A stored value that names no tab is ignored.
            page.evaluate(f"localStorage.setItem('{STORE_KEY}', 'beos')")
            page.reload()
            page.wait_for_selector("#nhg-install [role=tab][aria-selected=true]")
            assert _state(page)["tab"] == "win"
        finally:
            browser.close()


def test_detection_alone_never_stores_a_choice(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, "mac")
            assert page.evaluate(f"localStorage.getItem('{STORE_KEY}')") is None
        finally:
            browser.close()


def test_the_copy_button_copies_the_exact_command_for_each_tab(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, "unknown")
            for tab, command in COMMANDS.items():
                page.click(f"#install-tab-{tab}")
                page.evaluate("navigator.clipboard.writeText('')")
                page.evaluate("document.getElementById('nhg-copy-status').textContent = ''")
                button = page.locator(f"#install-panel-{tab} .install-copy")
                assert button.is_visible()
                assert button.inner_text().strip() == "Copy install command"
                button.click()
                page.wait_for_function(
                    "(b) => document.querySelector(b).textContent.trim() === 'Copied'",
                    arg=f"#install-panel-{tab} .install-copy",
                )
                assert page.evaluate("navigator.clipboard.readText()") == command, tab
                assert "Copied" in page.locator("#nhg-copy-status").inner_text()
                # The terminal under the button shows the same command, with no second chip.
                shown = page.locator(f"#install-panel-{tab} .term--install code[data-copy]")
                assert shown.inner_text().strip() == command
                assert page.locator(f"#install-panel-{tab} .term--install .copy-btn").count() == 0
            page.wait_for_function(
                "() => document.querySelector('#install-panel-linux .install-copy').textContent.trim() === 'Copy install command'",
                timeout=5000,
            )
        finally:
            browser.close()


def test_the_tabs_switch_with_the_keyboard(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, "win")
            page.focus("#install-tab-win")
            for key, want in (("ArrowRight", "mac"), ("ArrowRight", "linux"), ("ArrowRight", "win"),
                              ("ArrowLeft", "linux"), ("Home", "win"), ("End", "linux")):
                page.keyboard.press(key)
                state = _state(page)
                assert state["tab"] == want and state["panels"] == [want], (key, state)
                assert page.evaluate("document.activeElement.id") == f"install-tab-{want}"
            tabs = page.evaluate(
                """() => [...document.querySelectorAll('#nhg-install [role=tab]')].map(t => [t.id, t.getAttribute('aria-controls'),
                     t.getAttribute('aria-selected'), t.tabIndex, document.getElementById(t.getAttribute('aria-controls')).getAttribute('aria-labelledby')])"""
            )
            assert tabs == [
                ["install-tab-win", "install-panel-win", "false", -1, "install-tab-win"],
                ["install-tab-mac", "install-panel-mac", "false", -1, "install-tab-mac"],
                ["install-tab-linux", "install-panel-linux", "true", 0, "install-tab-linux"],
            ]
            assert page.evaluate(f"localStorage.getItem('{STORE_KEY}')") == "linux"
        finally:
            browser.close()


@pytest.mark.parametrize("agent", ["win", "mac", "linux"])
def test_the_install_section_has_no_horizontal_overflow_at_390(playwright_mod, agent: str) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            _context, page = _open(browser, agent, width=390, height=844)
            page.evaluate("document.querySelector('#nhg-install details').open = true")
            result = page.evaluate(
                """() => { const s = document.getElementById('nhg-install'), sr = s.getBoundingClientRect();
                  const scrolls = [...s.querySelectorAll('*')].filter(e => e.getClientRects().length
                      && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible')
                    .map(e => e.tagName + '.' + e.className);
                  const outside = [...s.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect();
                      return r.width > 0 && (r.left < sr.left - 1 || r.right > sr.right + 1); }).map(e => e.tagName + '.' + e.className);
                  const btn = document.querySelector('.tab-panel.active .install-copy').getBoundingClientRect();
                  return { doc: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                           scrolls, outside, button: [btn.width, btn.height] }; }"""
            )
            assert result["doc"] == 0, result
            assert result["scrolls"] == [], result
            assert result["outside"] == [], result
            assert result["button"][1] >= 44, "the copy button keeps a large target"
        finally:
            browser.close()
