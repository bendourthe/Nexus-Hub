"""v4.4.3 Phase 4 gates: Context Engineering -- legend rows, illustrated material, honest budget.

Three things the review asked for are asserted here. The legend row puts its swatch and label on one
line and the description under it, which is what stopped a three-word description from wrapping to
three lines beside a one-word label. The kinds of attachable material are a two-by-two grid of
drawings rather than four dashed boxes each containing the noun it was already labelled with. And
the budget comparison carries no legend and no percentages, because mapping three numbers onto three
unlabelled stripes is exactly what the reader could not do.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


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


def _scene(browser, width: int = 1440):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.locator("#fx-context").scroll_into_view_if_needed()
    page.wait_for_timeout(240)
    return ctx, page


def test_every_legend_row_is_swatch_and_label_over_description(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            rows = page.evaluate(
                """() => [...document.querySelectorAll('#page-foundations .ann-legend-row')].map(r => {
                    const dt = r.querySelector('dt'), dd = r.querySelector('dd');
                    const dtr = dt.getBoundingClientRect(), ddr = dd.getBoundingClientRect();
                    const swatch = getComputedStyle(dt, '::before');
                    const ddLh = parseFloat(getComputedStyle(dd).lineHeight);
                    return { label: dt.textContent.trim(), desc: dd.textContent.trim(),
                             above: dtr.bottom <= ddr.top + 1,
                             sameLeft: Math.abs(dtr.left - ddr.left) < 2,
                             swatch: parseFloat(swatch.width) > 0 && parseFloat(swatch.height) > 0,
                             descLines: Math.round(ddr.height / ddLh) };
                })"""
            )
            ctx.close()
        finally:
            browser.close()
    assert rows, "no legend rows found"
    for row in rows:
        assert row["above"], row
        assert row["sameLeft"], row
        assert row["swatch"], f"the label lost its colour swatch: {row}"
        assert row["descLines"] <= 2, row


def test_attachments_and_context_folder_are_above_the_prompt_that_names_them(playwright_mod) -> None:
    """The composed prompt names every visible attachment and selected folder."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const grid = document.querySelector('#fx-context .cx-materials');
                    const cells = [...grid.querySelectorAll('.cx-file')].map(c => ({
                      name: c.querySelector('.cx-kind').textContent.trim(),
                      example: c.querySelector('.cx-ex').textContent.trim(),
                      mono: getComputedStyle(c.querySelector('.cx-ex')).fontFamily.toLowerCase(),
                    }));
                    return { columns: getComputedStyle(grid).gridTemplateColumns.trim().split(/\s+/).length,
                             cells, drawings: grid.querySelectorAll('svg').length,
                             abovePrompt: grid.getBoundingClientRect().bottom <= document.querySelector('#fx-ann-context .ann-text').getBoundingClientRect().top,
                             named: cells.every(c => document.querySelector('#fx-ann-context .ann-text').textContent.includes(c.example)),
                             sameBox: grid.parentElement.id === 'fx-ann-context',
                             dashed: document.querySelectorAll('#fx-context .fx-ctx-kind').length };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["columns"] == 3, data
    assert len(data["cells"]) == 3, data["cells"]
    assert data["abovePrompt"] and data["named"] and data["sameBox"], data
    assert data["dashed"] == 0, "the dashed noun boxes must not return"
    names = [c["name"] for c in data["cells"]]
    assert names == ["Attached image", "Attached PDF", "Selected folder"], names
    for cell in data["cells"]:
        assert cell["example"], f"{cell['name']} has no example"
        assert cell["example"] != cell["name"], "an example must not restate the kind"
        assert "mono" in cell["mono"] or "courier" in cell["mono"] or "consol" in cell["mono"], cell


def test_dumping_everything_names_its_cost(playwright_mod) -> None:
    """The review asked for the cost to be named: tokens, speed, money, and the miss risk."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const spend = document.querySelector('#fx-context .fx-spend');
                    const read = sel => [...spend.querySelectorAll(sel + ' li')].map(l => l.textContent.trim());
                    const lanes = [...spend.querySelectorAll('.fx-spend-row')].map(r => Math.round(r.getBoundingClientRect().left));
                    return { costs: read('.cx-outcomes--cost'), gains: read('.cx-outcomes--gain'),
                             columns: getComputedStyle(spend).gridTemplateColumns.trim().split(/\s+/).length,
                             lanes };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["columns"] == 2, "the bad and good approaches must read side by side"
    assert len(data["lanes"]) == 2 and data["lanes"][0] < data["lanes"][1], data["lanes"]
    assert len(data["costs"]) == 4 and len(data["gains"]) == 4, data
    joined = " ".join(data["costs"]).lower()
    for named in ("tokens", "slower", "costs more", "needle in a haystack"):
        assert named in joined, f"the cost of dumping everything does not name {named!r}"
    gained = " ".join(data["gains"]).lower()
    for named in ("fewer tokens", "faster", "costs less"):
        assert named in gained, f"the gain does not name {named!r}"


def test_the_budget_comparison_reads_without_a_legend(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const spend = document.querySelector('#fx-context .fx-spend');
                    const meters = [...spend.querySelectorAll('.fx-meter')].map(m => ({
                        w: +m.getBoundingClientRect().width.toFixed(1),
                        labelled: [...m.children].filter(s => s.textContent.trim()).length,
                        segs: m.children.length,
                    }));
                    return { meters, text: spend.innerText,
                             legends: spend.querySelectorAll('.fx-legend, .fx-key, .fx-bar').length,
                             notes: [...spend.querySelectorAll('.fx-spend-note')].map(p => p.textContent.trim()) };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["legends"] == 0, "the bar-and-legend construction is still present"
    assert "%" not in data["text"], f"percentages are back in the copy: {data['text']}"
    assert len(data["meters"]) == 2, data["meters"]
    assert data["meters"][0]["w"] == data["meters"][1]["w"], "the two budgets must be the same width"
    for meter in data["meters"]:
        assert meter["labelled"] >= 1, f"no segment names what fills it: {meter}"
    assert len(data["notes"]) == 2 and all(data["notes"]), data["notes"]


def test_the_worked_example_is_an_agentic_project_task(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            text = page.evaluate("() => document.querySelector('#fx-ann-context .ann-text').innerText.toLowerCase()")
            ctx.close()
        finally:
            browser.close()
    assert "checkout" in text and "align back and place order" in text and "change delivery" in text, text
    assert "checkout-guidelines.pdf" in text and "assets/checkout/" in text, text


def test_context_previews_support_keyboard_close_and_folder_expansion(playwright_mod):
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        ctx, page = _scene(browser)
        try:
            dialog = page.locator("#cx-preview")
            for kind in ("image", "pdf", "folder"):
                button = page.locator('[data-cx-preview="' + kind + '"]')
                button.focus()
                page.keyboard.press("Enter")
                assert dialog.evaluate("e => e.open")
                assert dialog.locator("[data-cx-close]").evaluate("e => e === document.activeElement")
                if kind == "image":
                    image = dialog.get_by_role("img")
                    assert image.count() == 1
                    assert image.evaluate("e => e.src.startsWith('data:image/png') && e.naturalWidth === 720")
                    assert "checkout-layout.png" in dialog.inner_text()
                    assert "missing delivery control" in dialog.inner_text()
                elif kind == "pdf":
                    assert "Checkout interface" in dialog.inner_text()
                    assert "Change delivery" in dialog.inner_text()
                else:
                    assert "cart.svg" in dialog.inner_text()
                    dialog.locator("summary").filter(has_text="illustrations/").click()
                    assert dialog.get_by_text("order-confirmed.svg").is_visible()
                page.keyboard.press("Escape")
                assert not dialog.evaluate("e => e.open")
                assert button.evaluate("e => e === document.activeElement")
            page.locator('[data-cx-preview="image"]').click()
            dialog.locator("[data-cx-close]").click()
            assert not dialog.evaluate("e => e.open")
        finally:
            ctx.close()
            browser.close()
