"""v4.4.3 Phase 8 gates: one harness scene, and a guard for the defect this phase uncovered.

The review asked for a single harness segment: define a harness, then show what Nexus Hub adds. The
two scenes it replaced drew their labels as SVG text inside a 540-unit viewBox, so at a narrow
column the port names overlapped each other and the rings. Nested elements cannot overlap their own
labels, so the figure is HTML and the containment property is asserted directly.

v4.4.4 then replaced the nested rings with one flow, because the next review asked for a chart
following a prompt through the model and both harnesses rather than a picture of where they sit.
The containment and class-coverage guards are unchanged; the nesting assertion retired with the
rings.

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
    assert fx.count('class="fx-scene') == 6, "Foundations carries six scenes after both merges"
    # Both halves of the story must live in the one scene.
    scene = fx[fx.index('id="fx-harness"') : fx.index("</section>", fx.index('id="fx-harness"'))]
    text = re.sub(r"<[^>]+>", " ", scene).lower()
    assert "does not replace the model" in text, "the honest scope qualifier is required"
    assert "only where the host exposes the registered event" in text
    assert scene.count("data-phase3-claim") == 5, "the five repository-anchored claims must survive"


def test_the_flow_carries_the_analogy_and_the_platform_limits(playwright_mod) -> None:
    """v4.4.4 replaced the nested rings with one flow, on the review's instruction.

    The rings showed WHERE the layers sit; the review asked instead for a chart following a prompt
    through the model and both harnesses, with the platform layer's limits named and the analogy it
    supplied carried: a powerful brain, a graduate degree, decades of practical experience. The
    nesting assertion retires with the rings, and what replaces it is stronger about the teaching:
    the three layers appear in order, each with its own ports, and the middle one states its limits.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const flow = document.querySelector('#fx-harness .hxf');
                    const steps = [...flow.querySelectorAll('.hxf-step')].map(s => ({
                      tag: s.querySelector('.hxf-tag').textContent.trim(),
                      like: (s.querySelector('.hxf-like') || {textContent: ''}).textContent.trim(),
                      layer: s.dataset.phase3HarnessLayer || null,
                      ports: [...s.querySelectorAll('.hx-ports li')].map(l => l.textContent.trim()),
                      limit: (s.querySelector('.hxf-limit') || {textContent: ''}).textContent.trim(),
                      top: Math.round(s.getBoundingClientRect().top),
                    }));
                    return { steps, links: flow.querySelectorAll('.hxf-link').length,
                             pointsDown: [...flow.querySelectorAll('.hxf-link span')]
                               .every(t => parseFloat(getComputedStyle(t).borderTopWidth) >= 10) };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    steps = data["steps"]
    assert len(steps) == 5, [s["tag"] for s in steps]
    assert data["links"] == 4 and data["pointsDown"], data
    tops = [s["top"] for s in steps]
    assert tops == sorted(tops), f"the flow must read top to bottom: {tops}"
    layers = [s["layer"] for s in steps if s["layer"]]
    assert layers == ["model", "platform", "nexus-hub"], layers
    # the analogy the review supplied, on the three layers that have one
    model, platform, nexus = steps[1], steps[2], steps[3]
    assert "brain" in model["like"], model
    assert "degree" in platform["like"], platform
    assert "decades" in nexus["like"], nexus
    # each harness layer names what it contributes
    assert platform["ports"] == list(PLATFORM_PORTS), platform["ports"]
    assert nexus["ports"] == list(NEXUS_PORTS), nexus["ports"]
    # the platform layer's limits are named, which is what makes the outer layer necessary
    assert platform["limit"], "the platform layer must state its limits"
    lowered = platform["limit"].lower()
    assert "limits" in lowered and "session" in lowered, platform["limit"]
    assert not model["ports"] and not steps[0]["ports"], "only the harness layers carry ports"


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
