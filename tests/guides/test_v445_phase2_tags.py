"""v4.4.5 Phase 2 -- the Foundations block tags share one doubled size.

The review asked to double "'Vague', 'Engineered' and other similar text items on the
Foundations page". Two kinds of small uppercase label live there, and the distinction is the
whole content of this gate.

A BLOCK tag names a whole box or figure: Vague, Engineered, the budget tags, the boundary tag,
the legend terms the review pointed at in its own screenshot. Those are doubled, and they all
resolve to ONE token rather than to eight near-identical numbers, because 11.5px and 12px
doubled are 23px and 24px and nobody can see that difference -- but a ninth hand-authored size
is exactly how a design system stops being one.

An IN-CELL descriptor sits inside a quarter-width matrix cell. Those keep their size on
purpose. Doubling a 10.5px label inside a 250px cell does not make it easier to read; it makes
the cell three lines tall, which works against the legibility this review round is about. The
test pins that decision so it reads as a choice rather than as an omission.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (1440, 1024, 720, 480, 320)

# Selector -> whether it is a block tag (doubled) or an in-cell descriptor (left alone).
BLOCK_TAGS = (
    ".pe-tag",
    ".fx-ctx-tag",
    ".fx-spend-tag",
    ".fx-boundary-tag",
    ".ann-legend-row dt",
)
IN_CELL = (".cx-kind", ".fx-mat-name")


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


def test_one_token_carries_every_block_tag_size(guide_text: str) -> None:
    """A hand-written px on a block tag is the drift this token exists to prevent."""
    assert "--fx-tag:" in guide_text, "the tag-size token is missing"
    for selector in BLOCK_TAGS:
        rule = re.search(r"^%s \{[^}]*\}$" % re.escape(selector), guide_text, re.M)
        assert rule, f"no rule for {selector}"
        assert "var(--fx-tag)" in rule.group(0), (
            f"{selector} does not use the shared tag token: {rule.group(0)}"
        )


def test_the_block_tags_render_at_the_doubled_size(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = ctx.new_page()
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_function("window.NexusFit && window.NexusSeq")
            page.wait_for_timeout(400)
            sizes = page.evaluate(
                """(sel) => Object.fromEntries(sel.map(s => {
                    const el = document.querySelector(s);
                    return [s, el ? parseFloat(getComputedStyle(el).fontSize) : null];
                }))""",
                list(BLOCK_TAGS),
            )
            ctx.close()
        finally:
            browser.close()
    for selector, size in sizes.items():
        assert size is not None, f"{selector} is not on the page"
        assert size >= 22, f"{selector} renders at {size}px, which is not the doubled size"


def test_the_in_cell_descriptors_were_deliberately_left_alone(playwright_mod) -> None:
    """Recorded as a decision, not an oversight: a doubled label in a narrow cell is worse."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = ctx.new_page()
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_function("window.NexusFit")
            page.wait_for_timeout(400)
            sizes = page.evaluate(
                """(sel) => Object.fromEntries(sel.map(s => {
                    const el = document.querySelector(s);
                    return [s, el ? parseFloat(getComputedStyle(el).fontSize) : null];
                }))""",
                list(IN_CELL),
            )
            ctx.close()
        finally:
            browser.close()
    for selector, size in sizes.items():
        if size is None:
            continue
        assert size < 16, (
            f"{selector} is {size}px: an in-cell descriptor was doubled, which the Phase 2 "
            "decision explicitly declined. Change the decision in the plan first."
        )


def test_no_foundations_scene_overflows_at_any_width(playwright_mod) -> None:
    """A 23px uppercase tag with letter spacing is wide. Five widths, measured not assumed."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                ctx = browser.new_context(viewport={"width": width, "height": 1000})
                page = ctx.new_page()
                page.goto(GUIDE.as_uri() + "#foundations")
                page.wait_for_function("window.NexusFit")
                page.wait_for_timeout(500)
                page.evaluate(
                    "() => document.querySelectorAll('#foundations .fx-scene')"
                    ".forEach(s => s.scrollIntoView())"
                )
                page.wait_for_timeout(350)
                over = page.evaluate(
                    """() => [...document.querySelectorAll('#foundations .fx-scene')]
                        .map(s => [s.id, Math.round(s.scrollWidth - s.clientWidth)])
                        .filter(([, o]) => o > 0)"""
                )
                ctx.close()
                assert not over, f"{width}: scenes overflow {over}"
        finally:
            browser.close()
