"""v4.13.10 R52: the installed-version check in the guide and both READMEs.

The guide's Home install verification list gains a third step that shows
``nexus-hub version`` (prints the installed version) and ``nexus-hub upgrade``
(installs the latest release) as inline commands with copy chips, and both
READMEs tell a reader how to check the installed version.

The browser test skips when Playwright or Chromium is missing and fails closed
under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guides" / "website" / "nexus-hub-guide.html"
READMES = [ROOT / "README.md", ROOT / "README_zh.md"]
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
COMMANDS = ["nexus-hub version", "nexus-hub upgrade"]


def _verify_list() -> str:
    text = GUIDE.read_text(encoding="utf-8")
    home = text.split('id="page-home"', 1)[-1].split('id="page-foundations"', 1)[0]
    match = re.search(r'<ol class="verify-steps verify-steps--secondary">(.*?)</ol>', home, re.S)
    assert match, "the Home install verification list is missing"
    return match.group(1)


def test_verify_list_shows_version_and_upgrade_as_copyable_cells() -> None:
    steps = _verify_list()
    for command in COMMANDS:
        arg = command.split()[1]
        cell = re.search(
            rf'<span class="cmd-cell"><code data-ty="code" class="inv" data-copy="{re.escape(command)}">'
            rf'<span data-ty="code" data-tone="accent" class="inv-cmd">nexus-hub</span> '
            rf'<span data-ty="code" class="inv-arg">{arg}</span></code></span>',
            steps,
        )
        assert cell, f"{command}: expected an inline cmd-cell with a copy payload"
    notes = re.findall(r'<p data-ty="caption" class="vs-note">(.*?)</p>', steps)
    plain = [re.sub(r"<[^>]+>", "", n) for n in notes]
    assert "nexus-hub version prints the installed version." in plain
    assert "nexus-hub upgrade checks for the latest release and installs it." in plain
    assert steps.count('class="vs-n"') == 3


def test_both_readmes_show_the_version_check() -> None:
    for readme in READMES:
        text = readme.read_text(encoding="utf-8")
        assert "nexus-hub version" in text, readme.name
        assert "nexus-hub upgrade" in text, readme.name


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


@pytest.mark.parametrize("width", [1440, 390])
def test_version_cells_render_with_copy_chips(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(GUIDE.as_uri() + "#home/install")
            page.wait_for_selector(".verify-steps--secondary .copy-btn")
            data = page.evaluate(
                """(cmds) => cmds.map((c) => {
                    const code = document.querySelector(`.verify-steps--secondary code[data-copy="${c}"]`);
                    const cell = code && code.closest('.cmd-cell');
                    const btn = cell && cell.querySelector('.copy-btn');
                    const r = cell ? cell.getBoundingClientRect() : null;
                    return { cmd: c, visible: !!(r && r.width > 0 && r.height > 0),
                             chip: !!btn, label: btn ? btn.getAttribute('aria-label') : null,
                             inView: !!(r && r.right <= document.documentElement.clientWidth + 0.5),
                             text: code ? code.textContent.replace(/\\s+/g, ' ').trim() : null };
                })""",
                COMMANDS,
            )
            for item in data:
                assert item["visible"], item
                assert item["chip"] and item["label"] == "Copy to clipboard", item
                assert item["inView"], f"{item['cmd']} overflows at {width}px"
                assert item["text"] == item["cmd"], item
        finally:
            browser.close()
