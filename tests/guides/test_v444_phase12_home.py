"""v4.4.4 Phases 1 and 2 gates: the guardrails wording and the portability benefit.

The review asked for exact words in two places and for a second benefit the segment never showed.
Wording is asserted literally, because "roughly this" is how a rename drifts back. The portability
figure is asserted structurally: one install and four named platforms. The 2026-11-10 restructure
renamed the guardrails segment Why Nexus Hub, replaced the mid-task switch mockup with the handoff
animation, and moved the generic-command table to the Cheatsheets page, where it is asserted now. A second
2026-11-10 pass replaced the guardrail rings with a benefits summary, asserted in test_v415_home_animations.py.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
PLATFORMS = ("Claude Code", "Codex", "Cursor", "Antigravity")


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


def _home(browser, width: int = 1440):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#home")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.wait_for_timeout(220)
    return ctx, page


def test_the_command_segment_and_its_moved_table_keep_their_names(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _home(browser)
            data = page.evaluate(
                """() => {
                    const sec = document.querySelector('#nhg-commands'), table = document.querySelector('#cs-catalog .tbl-migrate');
                    return {
                      label: sec.querySelectorAll('.eyebrow').length,
                      title: sec.querySelector('.section-title').textContent.trim(),
                      headers: [...table.querySelectorAll('th')].map(t => t.textContent.trim()),
                      stacked: [...new Set([...table.querySelectorAll('td[data-th]')]
                                 .map(t => t.getAttribute('data-th')))].sort(),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["label"] == 0, data["label"]
    assert data["title"] == "Platform Coverage", data["title"]
    assert data["headers"] == ["Generic Platforms", "Nexus Hub", "What it adds"], data["headers"]
    # the stacked-layout labels must follow the header rename, or a phone reads the old names
    assert data["stacked"] == ["Generic Platforms", "Nexus Hub", "What it adds"], data["stacked"]


def test_the_segment_carries_both_benefits(playwright_mod) -> None:
    """One install across four platforms on Home, AND commands built on the generic ones on Cheatsheets."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _home(browser)
            page.locator("#nhg-commands").scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            data = page.evaluate(
                """() => {
                    const fig = document.querySelector('#nhg-commands .ph');
                    const rows = [...document.querySelectorAll('#cs-catalog .tbl-migrate tbody tr')];
                    return {
                      source: fig.querySelector('.ph-src').textContent.trim(),
                      targets: [...fig.querySelectorAll('.ph-target b')].map(b => b.textContent.trim()),
                      fans: fig.querySelectorAll('.ph-lane').length,
                      sequenced: fig.hasAttribute('data-seq-root'),
                      generics: rows.map(r => r.children[0].textContent.trim()),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    # benefit one: one install, four platforms
    assert "One install" in data["source"], data["source"]
    assert data["targets"] == list(PLATFORMS), data["targets"]
    assert data["fans"] == 4, "one connector per platform"
    assert not data["sequenced"], "the figure must not reveal itself in steps"
    # benefit two: the mapping still starts from the generic built-ins
    joined = " ".join(data["generics"]).lower()
    for generic in ("/goal", "/grill", "/loop", "/batch"):
        assert generic in joined, f"the generic command {generic} is no longer mapped"
