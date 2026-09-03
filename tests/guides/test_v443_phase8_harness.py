"""v4.4.3 Phase 8 gates: one harness scene, and a guard for the defect this phase uncovered.

The review asked for a single harness segment: define a harness, then show what Nexus Hub adds. The
two scenes it replaces drew their labels as SVG text inside a 540-unit viewBox, so at a narrow
column the port names overlapped each other and the rings. Nested elements cannot overlap their own
labels, so the figure is HTML and the containment property is asserted directly.

The third test here is a general guard, added because Phase 4 of this same plan removed CSS rules it
judged dead from a usage COUNT rather than from the locations of those usages. Two of the four
`fx-budget` usages were in the harness trail, so that block silently lost its border, background,
and two-column layout, and no test noticed because no test tied markup to style. This one does.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
PLATFORM_PORTS = ("context", "tools", "permissions", "execution", "observations")
NEXUS_PORTS = ("skills", "hooks", "gates", "artifacts")


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


def _scene(browser, width: int = 1440):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.locator("#fx-harness").scroll_into_view_if_needed()
    page.wait_for_timeout(260)
    return ctx, page


def test_there_is_exactly_one_harness_scene(guide_text: str) -> None:
    fx = guide_text[guide_text.index('id="page-foundations"') : guide_text.index('id="page-training"')]
    assert fx.count('id="fx-harness"') == 1
    assert "fx-practice" not in guide_text, "the second harness scene must be gone, markup and styles"
    assert "fx-hstack" not in guide_text, "the retired SVG figure must not survive anywhere"
    assert fx.count('class="fx-scene') == 7, "Foundations carries seven scenes after the merge"
    # Both halves of the story must live in the one scene.
    scene = fx[fx.index('id="fx-harness"') : fx.index("</section>", fx.index('id="fx-harness"'))]
    text = re.sub(r"<[^>]+>", " ", scene).lower()
    assert "does not replace the model" in text, "the honest scope qualifier is required"
    assert "only where the host exposes the registered event" in text
    assert scene.count("data-phase3-claim") == 5, "the five repository-anchored claims must survive"


def test_the_three_layers_are_geometrically_nested(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const fig = document.querySelector('#fx-harness .hx');
                    const box = sel => { const e = fig.querySelector(sel); return e && e.getBoundingClientRect(); };
                    const outer = box('.hx-ring--nexus'), inner = box('.hx-ring--platform'), core = box('.hx-core');
                    const inside = (a, b) => a.left >= b.left - 1 && a.right <= b.right + 1
                                          && a.top >= b.top - 1 && a.bottom <= b.bottom + 1;
                    return {
                      nested: inside(inner, outer) && inside(core, inner),
                      outerPorts: [...fig.querySelectorAll('.hx-ring--nexus > .hx-ports li')].map(l => l.textContent.trim()),
                      innerPorts: [...fig.querySelectorAll('.hx-ring--platform > .hx-ports li')].map(l => l.textContent.trim()),
                      layers: [...fig.querySelectorAll('[data-phase3-harness-layer]')].map(e => e.dataset.phase3HarnessLayer),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["nested"], "the platform ring must sit inside the Nexus Hub ring, with the model innermost"
    assert set(data["layers"]) == {"nexus-hub", "platform", "model"}, data["layers"]
    assert data["innerPorts"] == list(PLATFORM_PORTS), data["innerPorts"]
    assert data["outerPorts"] == list(NEXUS_PORTS), data["outerPorts"]


def test_the_journey_reads_as_movement_and_ends_in_verified_work(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            page.wait_for_function(
                "() => { const s = window.NexusSeq.state(document.querySelector('#fx-harness .hx'));"
                " return s && s.step === s.total; }"
            )
            data = page.evaluate(
                """() => {
                    const stops = [...document.querySelectorAll('#fx-harness .hx-stop')];
                    return {
                      total: window.NexusSeq.state(document.querySelector('#fx-harness .hx')).total,
                      seq: stops.map(s => +s.dataset.seq),
                      lit: stops.filter(s => s.classList.contains('is-on')).length,
                      lastIsOut: stops[stops.length - 1].classList.contains('hx-stop--out'),
                      outCount: stops.filter(s => s.classList.contains('hx-stop--out')).length,
                      texts: stops.map(s => s.textContent.trim().toLowerCase()),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["total"] == 6 and data["seq"] == [1, 2, 3, 4, 5, 6], data
    assert data["lit"] == 6, "every stop must be lit at the end state"
    assert data["lastIsOut"] and data["outCount"] == 1, data
    # the journey the review asked for: in from the operator, through both loops, out verified
    assert "prompt" in data["texts"][0] and "material" in data["texts"][0], data["texts"][0]
    assert "reasons" in data["texts"][3], data["texts"][3]
    assert "verified" in data["texts"][5], data["texts"][5]


def test_every_class_used_in_foundations_has_a_style_rule(guide_text: str) -> None:
    """The guard for the Phase 4 defect: markup that references a rule nobody defines.

    Phase 4 removed the budget rules after counting four usages of `fx-budget` and assuming all
    four were the two boxes being replaced. Two were in the harness trail, which then rendered with
    no border, no background, and no columns. A count cannot tell you where a class is used; this
    test ties every class in the Foundations markup to a declaration in the stylesheet.
    """
    css = guide_text.split("<style>", 1)[1].split("</style>", 1)[0]
    declared = set(re.findall(r"\.([A-Za-z][\w-]*)", css))
    fx = guide_text[guide_text.index('id="page-foundations"') : guide_text.index('id="page-training"')]
    used: set[str] = set()
    for match in re.finditer(r'class="([^"]+)"', fx):
        used.update(match.group(1).split())
    undeclared = sorted(name for name in used if name not in declared)
    assert not undeclared, f"Foundations markup uses classes with no style rule: {undeclared}"
