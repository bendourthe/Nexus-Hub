"""v4.4.5 Phases 6 and 7 -- what the two operator mockups added, and what they did not.

Both mockups teach through controls. The agentic one hides its best lesson behind a button: a
reader only learns that a boundary REPORTS a refusal instead of routing around it if they press
the read-only setting and watch step 03 stop. The harness one hides its five-step work sequence
behind a run button and its per-layer detail behind three more.

This guide has no controls, so every one of those states is on the page at once. That is the
property under test here, and it is asserted as multiplicity rather than presence: the agentic
boundary must show all THREE settings, the harness must state a limit or a guarantee on all
THREE layers, and the work sequence must show all FIVE steps without anything being run.

The negative assertions matter as much. Neither mockup's absolutely-positioned SVG map came
across, and both would have brought one: a 720x520 system map and a 760x470 adapter map, each
placing every label by offset inside a fixed viewBox. Phase 5 already recorded what that
construction does at a width nobody tested.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (1440, 1024, 720, 480, 320)


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


def _scene_text(guide_text: str, scene_id: str) -> str:
    start = guide_text.index(f'id="{scene_id}"')
    return guide_text[start : guide_text.index("</section>", start)]


def _page(browser, width: int = 1440):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.wait_for_timeout(400)
    return ctx, page


# --------------------------------------------------------------- Phase 6, Agentic Platforms


def test_the_equation_names_what_agentic_means(guide_text: str) -> None:
    """The mockup's single most useful sentence, which this scene did not have."""
    scene = _scene_text(guide_text, "fx-agent-platform")
    assert 'data-ap-block="equation"' in scene, "the model-plus-harness equation is missing"
    lowered = scene.lower()
    assert "describes what a system does, not a special kind of model" in lowered, (
        "the equation must say that agentic is a behaviour, not a model class"
    )
    assert scene.index('data-ap-block="equation"') < scene.index('id="cv-compare"'), (
        "the equation has to be read before the two lanes it explains"
    )


def test_all_three_boundary_settings_are_visible_with_their_outcomes(playwright_mod) -> None:
    """In the mockup these are buttons, and the refusal lesson only fires if one is pressed."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _page(browser)
            data = page.evaluate(
                """() => {
                    const items = [...document.querySelectorAll('#fx-agent-platform .ap-bset li')];
                    return items.map(li => ({
                      name: li.querySelector('b').textContent.trim(),
                      outcome: li.querySelector('em').textContent.trim(),
                      painted: li.getBoundingClientRect().height > 10,
                      stop: li.classList.contains('ap-bset--stop'),
                    }));
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert len(data) == 3, data
    assert all(item["painted"] and item["outcome"] for item in data), data
    assert [item["name"] for item in data] == ["Read only", "Ask before edits", "Scoped edits"]
    refused = next(item for item in data if item["stop"])
    assert "reports" in refused["outcome"].lower(), (
        "the read-only setting must teach that the platform REPORTS the boundary rather than "
        f"routing around it: {refused['outcome']}"
    )


def test_the_anatomy_names_six_parts_without_importing_the_map(guide_text: str) -> None:
    scene = _scene_text(guide_text, "fx-agent-platform")
    assert 'data-ap-block="anatomy"' in scene
    for part in ("Planner", "Specialists", "Tools", "Boundary", "Observations", "Verifier"):
        assert f"<dt>{part}</dt>" in scene, f"the anatomy is missing {part}"
    assert "<svg" not in scene.split('data-ap-block="anatomy"')[1], (
        "the mockup's absolutely-positioned system map must not come with the list"
    )


# --------------------------------------------------------------- Phase 7, Harnesses


def test_every_harness_layer_states_a_limit_or_a_guarantee(guide_text: str) -> None:
    """The scene used to state only the platform layer's limits.

    That made the platform look like the only layer with a weakness, when the model cannot
    reach a tool at all and the outer layer's hooks fire only where a host exposes the event.
    """
    scene = _scene_text(guide_text, "fx-harness")
    assert scene.count("hxf-limit") == 3, (
        f"expected a stated limit or guarantee on all three layers, found {scene.count('hxf-limit')}"
    )
    lowered = scene.lower()
    assert "why it needs the next layer" in lowered, "the model layer states nothing"
    assert "its limits" in lowered, "the platform layer states nothing"
    assert "what it preserves" in lowered, "the outer layer states nothing"


def test_the_work_sequence_shows_five_steps_with_nothing_to_run(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _page(browser)
            data = page.evaluate(
                """() => {
                    const steps = [...document.querySelectorAll('#fx-harness .hxw-steps li')];
                    return {
                      names: steps.map(s => s.querySelector('b').textContent.trim()),
                      painted: steps.every(s => s.getBoundingClientRect().height > 10),
                      buttons: document.querySelectorAll('#fx-harness button').length,
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert len(data["names"]) == 5, data["names"]
    assert data["painted"], "every step must be on the page, not waiting for a run"
    assert data["buttons"] == 0, "the mockup's run button came along"
    assert data["names"][0].lower().startswith("load"), data["names"]
    assert "chain" in data["names"][-1].lower(), data["names"]


def test_the_artifact_chain_is_shown_rather_than_claimed(playwright_mod) -> None:
    """The scene asserted that artifacts chain. The mockup shows the chain, so now it does."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _page(browser)
            data = page.evaluate(
                """() => {
                    const chips = [...document.querySelectorAll('#fx-harness .hx-chip')];
                    const rows = [...document.querySelectorAll('#fx-harness .hx-row b')];
                    return { chips: chips.map(c => c.textContent.trim()),
                             lefts: chips.map(c => Math.round(c.getBoundingClientRect().left)),
                             tops: chips.map(c => Math.round(c.getBoundingClientRect().top)),
                             rows: rows.map(r => r.textContent.trim()) };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["chips"] == ["skill", "plan", "gate", "evidence"], data["chips"]
    # Sorted left offsets are NOT enough: four identical offsets sort fine, and that is
    # exactly what a stacked chain produces. The first run of this phase shipped one chip per
    # line at full width and this assertion passed. One row with strictly increasing offsets
    # is the property that failed, so it is the property measured.
    assert len(set(data["tops"])) == 1, (
        f"the chain must read across one row, not stack: tops {data['tops']}"
    )
    assert data["lefts"] == sorted(data["lefts"]) and len(set(data["lefts"])) == 4, (
        f"a chain has to read in one direction, one chip at a time: {data['lefts']}"
    )
    assert len(data["rows"]) == 4, f"two rows per lane, both lanes: {data['rows']}"


def test_neither_rebuilt_scene_overflows_at_any_width(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                ctx, page = _page(browser, width)
                page.evaluate(
                    "() => document.querySelectorAll('#foundations .fx-scene')"
                    ".forEach(s => s.scrollIntoView())"
                )
                page.wait_for_timeout(300)
                over = page.evaluate(
                    """() => ['fx-agent-platform', 'fx-harness'].map(id => {
                        const s = document.getElementById(id);
                        return [id, Math.round(s.scrollWidth - s.clientWidth)];
                    }).filter(([, o]) => o > 0)"""
                )
                ctx.close()
                assert not over, f"{width}: {over}"
        finally:
            browser.close()
