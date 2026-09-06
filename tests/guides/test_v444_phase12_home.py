"""v4.4.4 Phases 1 and 2 gates: the guardrails wording and the portability benefit.

The review asked for exact words in two places and for a second benefit the segment never showed.
Wording is asserted literally, because "roughly this" is how a rename drifts back. The portability
figure is asserted structurally: one install, four named platforms, and a switch that names the
reason a task would move mid-flight.
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


def test_the_guardrails_segment_is_renamed_and_centred(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _home(browser)
            page.locator("#nhg-guardrails").scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            data = page.evaluate(
                """() => {
                    const sec = document.querySelector('#nhg-guardrails');
                    const centred = el => getComputedStyle(el).textAlign === 'center';
                    const tags = [...sec.querySelectorAll('.gf-ring-tag')];
                    const notes = [...sec.querySelectorAll('.gf-ring-note')];
                    const hooks = sec.querySelector('.gf-hooks');
                    return {
                      label: sec.querySelector('.eyebrow').textContent.trim(),
                      title: sec.querySelector('.section-title').textContent.trim(),
                      tags: tags.map(t => t.textContent.trim()),
                      notes: notes.map(n => n.textContent.trim()),
                      allCentred: tags.every(centred) && notes.every(centred),
                      hooksAlignment: getComputedStyle(hooks).textAlign,
                          platforms: [...sec.querySelectorAll(".gf-platforms>span")].map(e => e.textContent.trim()),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["label"] == "Guardrails & Safety", data["label"]
    assert data["title"] == "Adds an extra layer of security", data["title"]
    assert data["platforms"] == ["Claude", "ChatGPT", "Cursor", "Gemini"]
    assert data["allCentred"], "both ring headers and their subtexts must be centred"
    assert data["hooksAlignment"] == "center", "the guardrail descriptions must be centred"
    assert data["tags"] == ["Nexus Hub hooks", "Platform permissions"], data["tags"]
    outer, inner = data["notes"]
    for phrase in ("Block flagged unsafe actions", "even once approved", "explain the refusal"):
        assert phrase in outer, (phrase, outer)
    for phrase in ("Ask for permission first", "an unsafe action can still run"):
        assert phrase in inner, (phrase, inner)


def test_the_command_segment_is_renamed(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _home(browser)
            data = page.evaluate(
                """() => {
                    const sec = document.querySelector('#nhg-commands');
                    return {
                      label: sec.querySelector('.eyebrow').textContent.trim(),
                      title: sec.querySelector('.section-title').textContent.trim(),
                      headers: [...sec.querySelectorAll('.tbl-migrate th')].map(t => t.textContent.trim()),
                      stacked: [...new Set([...sec.querySelectorAll('.tbl-migrate td[data-th]')]
                                 .map(t => t.getAttribute('data-th')))].sort(),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["label"] == "One Harness, Multiple Platforms", data["label"]
    assert data["title"] == "Install once, work anywhere", data["title"]
    assert data["headers"] == ["Generic Platforms", "Nexus Hub", "What it adds"], data["headers"]
    # the stacked-layout labels must follow the header rename, or a phone reads the old names
    assert data["stacked"] == ["Generic Platforms", "Nexus Hub", "What it adds"], data["stacked"]


def test_the_segment_carries_both_benefits(playwright_mod) -> None:
    """One install across four platforms, AND commands built on the generic ones."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _home(browser)
            page.locator("#nhg-commands").scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            data = page.evaluate(
                """() => {
                    const fig = document.querySelector('#nhg-commands .ph');
                    const rows = [...document.querySelectorAll('#nhg-commands .tbl-migrate tbody tr')];
                    return {
                      source: fig.querySelector('.ph-src').textContent.trim(),
                      targets: [...fig.querySelectorAll('.ph-target b')].map(b => b.textContent.trim()),
                      fans: fig.querySelectorAll('.ph-lane').length,
                      sessions: [...fig.querySelectorAll('.ph-session')].map(s => ({
                        host: s.querySelector('.ph-head b').textContent.trim(),
                        logo: !!s.querySelector(".ph-head .brand-copy svg"),
                        commands: [...s.querySelectorAll('.ph-msg--user code')].map(e => e.textContent),
                        tasks: [...s.querySelectorAll(".ph-tasks")].map(list => [...list.querySelectorAll("label")].map(label => ({text: label.textContent, done: label.querySelector("input").checked}))),
                        phases: [...s.querySelectorAll(".ph-plan tbody tr")].map(row => row.cells.length),
                        text: s.textContent.toLowerCase() })),
                      cut: fig.querySelector('.ph-cut').textContent.trim().toLowerCase(),
                      note: fig.querySelector('.ph-note').textContent.trim().toLowerCase(),
                      sequenced: fig.hasAttribute('data-seq-root'),
                      generics: rows.map(r => r.children[0].textContent.trim()),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    # benefit one: one install, four platforms, and a mid-task switch
    assert "One install" in data["source"], data["source"]
    assert data["targets"] == list(PLATFORMS), data["targets"]
    assert data["fans"] == 4, "one connector per platform"
    assert not data["sequenced"], "the figure must not reveal itself in steps"
    hosts = [session["host"] for session in data["sessions"]]
    assert hosts[0] == "Claude Code" and hosts[-1] == "Codex", hosts
    assert len(set(hosts)) == 2, "the switch must cross exactly two platforms"
    claude, codex = data["sessions"]
    assert claude["logo"] and codex["logo"]
    assert "/plan" in claude["commands"] and "/implement" in claude["commands"]
    assert "usage limit reached" in claude["text"] and "3 hours" in claude["text"]
    assert "phase 1 in progress" in claude["text"]
    assert claude["phases"] == [3, 3, 3]
    saved, resumed, complete = claude["tasks"][0], *codex["tasks"]
    assert len(saved) == 4 and saved == resumed
    assert [task["done"] for task in saved] == [True, True, False, False]
    assert [task["text"] for task in saved] == [task["text"] for task in complete]
    assert all(task["done"] for task in complete)
    assert "/implement" in codex["commands"] and "booking-feature-plan.md" in codex["text"]
    assert "phase 1 verified and complete" in codex["text"]
    assert "next: run /implement phase 2" in codex["text"]

    assert "usage" in data["cut"], data["cut"]
    assert "files" in data["note"] and "resumes" in data["note"], data["note"]
    # benefit two: the mapping still starts from the generic built-ins
    joined = " ".join(data["generics"]).lower()
    for generic in ("/goal", "/grill", "/loop", "/batch"):
        assert generic in joined, f"the generic command {generic} is no longer mapped"
