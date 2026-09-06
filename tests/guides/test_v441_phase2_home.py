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


def test_full_lockup_floats_as_one_unit(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            samples = []
            for _ in range(3):
                samples.append(_lockup_positions(page))
                page.wait_for_timeout(900)
        finally:
            browser.close()

    # Some sample must differ from the first, or nothing is animating at all.
    deltas = [
        tuple(round(later[i] - samples[0][i], 2) for i in range(3)) for later in samples[1:]
    ]
    assert any(any(abs(d) > 0.5 for d in delta) for delta in deltas), (
        f"the lockup never moved across three samples: {samples}"
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


@pytest.mark.parametrize("width", (320, 420, 900, 1440))
def test_workflow_pills_are_readable_two_line_pills(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw, width=width)
        try:
            steps = page.evaluate(
                """() => [...document.querySelectorAll('.loop-step')].map(el => {
                    const code = el.querySelector('code');
                    const desc = el.querySelector('span');
                    const cr = code.getBoundingClientRect();
                    const dr = desc.getBoundingClientRect();
                    const cs = getComputedStyle(code);
                    const ds = getComputedStyle(desc);
                    return {
                        text: code.textContent.trim(),
                        codeSize: parseFloat(cs.fontSize),
                        descSize: parseFloat(ds.fontSize),
                        codeWraps: code.scrollWidth > code.clientWidth + 1,
                        separated: dr.top >= cr.bottom - 1,
                    };
                })"""
            )
        finally:
            browser.close()

    assert steps, "expected the Home workflow loop steps"
    for step in steps:
        assert step["codeSize"] >= 14.0, (
            f"{step['text']} command is {step['codeSize']}px at {width}px; floor is 14px"
        )
        assert step["descSize"] >= 13.5, (
            f"{step['text']} description is {step['descSize']}px at {width}px"
        )
        assert not step["codeWraps"], f"{step['text']} command wraps at {width}px"
        assert step["separated"], (
            f"{step['text']} description is not on its own line at {width}px"
        )
        assert step["codeSize"] > step["descSize"], (
            f"{step['text']} command must stay visually dominant"
        )


# ============================================================================ v4.4.2 Phase 2
# The hero statement, the restored sections, the merged comparison, the guardrails illustration,
# the footer attribution, and the catalog-derived counts. Structural facts are checked in the
# browser too, because the claims are about order, computed size, visibility, and word budgets.

import json as _json
import re as _re

_FIXTURE = _ROOT / "tests" / "guides" / "fixtures" / "v412-home-copy.json"
_HOOKS_DIR = _ROOT / "catalog" / "hooks"

EXPECTED_HOME_ORDER = [
    "Upgrade any agentic AI platform with an autonomous team of world experts",
    "What raw prompting cannot deliver",
    "One command, then an assistant restart",
    "Three things make this more than a prompt library",
    "Adds an extra layer of security",
    "Raw prompting vs Nexus Hub",
    "Install once, work anywhere",
    "One governed loop, from first look to shipped",
]


def _section_words(page, section_id: str) -> int:
    """Word count of a section's RESTORED prose.

    v4.4.4 adds content to a restored section that v4.1.2 never had, the portability figure the
    operator asked for, so measuring it against a v4.1.2 baseline measures the wrong thing. Blocks
    marked `data-v444-new` are excluded here and capped separately in the test below, which keeps
    both halves honest: restored prose still cannot creep back toward its old length, and the new
    block cannot grow without a number on it.
    """
    return page.evaluate(
        """id => { const sec = document.getElementById(id).cloneNode(true);
             sec.querySelectorAll('[data-v444-new]').forEach(e => e.remove());
             document.body.appendChild(sec);
             const n = sec.innerText.replace(/\s+/g, ' ').trim().split(' ').length;
             sec.remove(); return n; }""",
        section_id,
    )


def _new_block_words(page, selector: str) -> int:
    return page.evaluate(
        """sel => { const e = document.querySelector(sel);
             return e ? e.innerText.replace(/\s+/g, ' ').trim().split(' ').length : 0; }""",
        selector,
    )


def test_home_hero_statement_is_centred_and_exact(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            data = page.evaluate(
                """() => {
                    const sub = document.querySelector('.hero-subtitle');
                    const lead = document.querySelector('.hero-lead');
                    const rail = document.querySelector('.platform-rail');
                    const c = el => { const r = el.getBoundingClientRect(); return r.left + r.width / 2; };
                    return {
                        subText: sub.textContent.replace(/\\s+/g, ' ').trim(),
                        leadStart: lead.textContent.trim().slice(0, 58),
                        subCentre: c(sub), leadCentre: c(lead), railCentre: c(rail),
                        subAlign: getComputedStyle(sub).textAlign,
                        gradFill: getComputedStyle(document.querySelector('.gtext')).webkitTextFillColor,
                        gradColor: getComputedStyle(document.querySelector('.gtext')).color,
                        subSize: parseFloat(getComputedStyle(sub).fontSize),
                        tagline: !!document.querySelector('.hero-tagline'),
                        credits: !!document.querySelector('#page-home .platform-credits'),
                    };
                }"""
            )
        finally:
            browser.close()
    assert data["subText"] == EXPECTED_HOME_ORDER[0]
    assert data["leadStart"] == "Nexus Hub is an advanced harness for agentic AI platforms."
    assert data["subAlign"] == "center"
    assert abs(data["subCentre"] - data["railCentre"]) < 2 and abs(data["leadCentre"] - data["railCentre"]) < 2
    # The gradient paints through text-fill-color while `color` stays a real, measurable colour.
    assert data["gradFill"] in ("rgba(0, 0, 0, 0)", "transparent")
    assert data["gradColor"] not in ("rgba(0, 0, 0, 0)", "transparent")
    assert 38 <= data["subSize"] <= 46, data["subSize"]
    assert not data["tagline"] and not data["credits"]


def test_home_sections_render_in_the_agreed_order(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            titles = page.evaluate(
                "() => [...document.querySelectorAll('#page-home .hero-subtitle, #page-home .section-title')]"
                ".map(e => e.textContent.replace(/\\s+/g, ' ').trim())"
            )
        finally:
            browser.close()
    assert titles == EXPECTED_HOME_ORDER, titles


def test_restored_sections_are_at_most_two_thirds_of_their_v412_word_count(playwright_mod) -> None:
    fixture = _json.loads(_FIXTURE.read_text(encoding="utf-8"))["sections"]
    ids = {"why-it-matters": "nhg-why", "how-it-works": "nhg-how", "favorite-commands": "nhg-commands"}
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            counts = {key: _section_words(page, sid) for key, sid in ids.items()}
            portability = _new_block_words(page, "#nhg-commands [data-v444-new]")
            merged = page.evaluate(
                "() => { const h = [...document.querySelectorAll('#page-home .section-title')]"
                ".find(e => e.textContent.trim() === 'Raw prompting vs Nexus Hub');"
                " return h.closest('section').innerText.replace(/\\s+/g, ' ').trim().split(' ').length; }"
            )
        finally:
            browser.close()
    for key, words in counts.items():
        ceiling = fixture[key]["v412_words"] * 2 // 3
        assert words <= ceiling, f"{key}: {words} words exceeds the two-thirds ceiling of {ceiling}"
    # The merged comparison replaces v4.1.2's "The difference" and must not exceed ITS ceiling.
    assert merged <= fixture["the-difference"]["v412_words"] * 2 // 3, merged
    # The requested phase table and saved/resumed/completed checklists expand the session example.
    # Keep their combined illustration bounded while retaining the original section ceilings.
    assert 20 <= portability <= 320, f"the portability figure is {portability} words"


def test_merged_comparison_labels_render_at_twice_the_v441_size(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            sizes = page.evaluate(
                "() => [...document.querySelectorAll('.cmp-side')].map(e => parseFloat(getComputedStyle(e).fontSize))"
            )
            rows = page.evaluate("() => document.querySelectorAll('#page-home .cmp-row').length")
        finally:
            browser.close()
    assert sizes and all(abs(s - 26) < 0.5 for s in sizes), sizes   # v4.4.1 rendered 13px
    assert rows == 5


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


def test_migration_table_stacks_into_labelled_cards_below_720px(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw, width=420)
        try:
            data = page.evaluate(
                """() => {
                    const rows = [...document.querySelectorAll('.tbl-migrate tbody tr')];
                    const thead = getComputedStyle(document.querySelector('.tbl-migrate thead')).display;
                    const cells = [...rows[0].querySelectorAll('td')];
                    const tops = cells.map(td => Math.round(td.getBoundingClientRect().top));
                    const labels = cells.map(td => getComputedStyle(td, '::before').content);
                    return { rows: rows.length, thead, stacked: new Set(tops).size === cells.length, labels,
                             overflow: document.documentElement.scrollWidth - window.innerWidth };
                }"""
            )
        finally:
            browser.close()
    assert data["rows"] == 7 and data["thead"] == "none"
    assert data["stacked"], "cells must stack vertically at 420px"
    assert all('"' in l and l != "none" for l in data["labels"]), data["labels"]
    assert data["overflow"] <= 1


def test_guardrails_section_names_only_shipped_registered_hooks(playwright_mod) -> None:
    settings = _json.loads((_HOOKS_DIR / "settings.json").read_text(encoding="utf-8"))
    registered = set()
    for entries in settings["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                m = _re.search(r"([a-z0-9_-]+)\.(sh|py)\b", hook.get("command", ""))
                if m:
                    registered.add(m.group(1))
    pretooluse = set()
    for entry in settings["hooks"]["PreToolUse"]:
        for hook in entry["hooks"]:
            m = _re.search(r"([a-z0-9_-]+)\.(sh|py)\b", hook["command"])
            if m:
                pretooluse.add(m.group(1))
    with playwright_mod() as pw:
        browser, page = _launch(pw)
        try:
            data = page.evaluate(
                """() => ({
                    ports: [...document.querySelectorAll('#nhg-guard-fig .gf-hooks li')].map(e => e.dataset.hook),
                    blocked: [...document.querySelectorAll('#nhg-guard-fig .gf-cell--stop b')].map(e => e.dataset.hook),
                    pretooluse: +document.querySelector('#nhg-guardrails [data-count="pretooluse"]').textContent,
                    hooks: +document.querySelector('#nhg-guardrails [data-count="hooks"]').textContent,
                    text: document.getElementById('nhg-guardrails').innerText.toLowerCase(),
                })"""
            )
        finally:
            browser.close()
    assert len(data["ports"]) == 6
    for name in data["ports"]:
        assert (_HOOKS_DIR / f"{name}.sh").is_file(), f"{name}.sh does not ship"
        assert (_HOOKS_DIR / f"{name}.ps1").is_file(), f"{name}.ps1 sibling missing"
        assert name in registered, f"{name} is not registered in settings.json"
    assert data["blocked"], "no attempt names the hook that blocked it"
    for hook in data["blocked"]:
        assert hook in data["ports"], hook
    assert data["pretooluse"] == len(pretooluse) and data["hooks"] == len(registered)
    assert "makes ai safe" not in data["text"], "claims must be enforcement statements, not a safety guarantee"


def test_guardrails_choreography_reaches_a_fully_blocked_end_state(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _launch(pw, reduced_motion="reduce")
        try:
            page.locator("#nhg-guard-fig").scroll_into_view_if_needed()
            page.wait_for_function(
                "() => { const s = window.NexusSeq.state(document.getElementById('nhg-guard-fig')); return s && s.step === s.total; }"
            )
            data = page.evaluate(
                """() => ({
                    total: window.NexusSeq.state(document.getElementById('nhg-guard-fig')).total,
                    lit: document.querySelectorAll('#nhg-guard-fig .is-on').length,
                    blocks: document.querySelectorAll('#nhg-guard-fig .gf-out--stop').length,
                })"""
            )
        finally:
            browser.close()
    assert data["total"] == 3 and data["lit"] == 3 and data["blocks"] == 2
