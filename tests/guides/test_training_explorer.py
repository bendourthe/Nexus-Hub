"""Browser contracts for the seven-section Training explorer."""

from __future__ import annotations

import json
import re
from pathlib import Path

GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"


def _require_browser(render_gate: object) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        render_gate("Playwright is not installed")  # type: ignore[operator]
        return
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception as error:  # noqa: BLE001 - render_gate classifies launch failures
        render_gate(f"Playwright Chromium cannot launch: {error}")  # type: ignore[operator]


def test_test_local_hostile_output_stays_inert_in_browser(render_gate: object, tmp_path: Path) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    data = json.loads((GUIDE.parent / "example" / "training-scenes.json").read_text(encoding="utf-8"))
    hostile = '<img src=x onerror="window.__hostileFixtureRan=1"> </script><script>window.__hostileFixtureRan=1</script>'
    data["scenes"][1]["actions"][0]["output"].append(hostile)
    encoded = json.dumps(data, ensure_ascii=True).replace("<", r"\u003c").replace(">", r"\u003e")
    html, replacements = re.subn(
        r'(<script type="application/json" id="nh-training-scenes">\s*)(.*?)(\s*</script>)',
        lambda match: match.group(1) + encoded + match.group(3),
        GUIDE.read_text(encoding="utf-8"),
        count=1,
        flags=re.DOTALL,
    )
    assert replacements == 1
    fixture = tmp_path / "hostile-training.html"
    fixture.write_text(html, encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(reduced_motion="reduce")
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            page = context.new_page()
            page.goto(f"{fixture.resolve().as_uri()}#training/describe-review", wait_until="load")
            page.wait_for_function("window.NexusTraining && window.NexusShooter")
            section = page.locator('[data-nht-section="describe-review"]')
            section.locator('[data-nht="run"]').click()
            terminal = section.locator('[data-nht="terminal"]')
            assert hostile in terminal.inner_text()
            assert terminal.locator("img, script").count() == 0
            assert page.evaluate("window.__hostileFixtureRan === undefined")
        finally:
            browser.close()


def test_training_actions_are_isolated_and_files_accumulate(render_gate: object) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 1440, "height": 940}, reduced_motion="reduce")
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{GUIDE.resolve().as_uri()}#training/describe-review", wait_until="load")
            page.wait_for_function("window.NexusTraining && window.NexusShooter")
            describe = page.locator('[data-nht-section="describe-review"]')
            plan = page.locator('[data-nht-section="plan"]')
            assert describe.locator('[data-nht="command"]').inner_text() == "/describe full"
            assert plan.locator('[data-nht="output"]').inner_text() == ""
            describe.locator('[data-nht="run"]').click()
            assert "applyEnemyHit" in describe.locator('[data-nht="output"]').inner_text()
            assert plan.locator('[data-nht="output"]').inner_text() == ""
            assert page.evaluate("window.NexusTraining.snapshot().completed") == ["1:0"]
            assert "docs/analysis.md" in page.evaluate("window.NexusTraining.snapshot().filePaths")

            describe.locator('[data-nht-action-index="1"]').click()
            assert describe.locator('[data-nht="command"]').inner_text() == "/review"
            describe.locator('[data-nht="run"]').click()
            assert "P1 correctness" in describe.locator('[data-nht="output"]').inner_text()
            assert page.evaluate("window.NexusTraining.snapshot().completed") == ["1:0", "1:1"]
            page.evaluate("window.NexusTraining.go('plan')")
            paths = page.evaluate("window.NexusTraining.snapshot().filePaths")
            assert {"docs/analysis.md", "docs/review.md"} <= set(paths)
            assert "docs/comparison.md" not in paths
            assert plan.locator('[data-nht="output"]').inner_text() == ""
            assert not errors, errors
        finally:
            browser.close()


def test_stacked_training_sections_are_keyboard_reachable_and_narrow_safe(render_gate: object) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width in (1440, 420):
                context = browser.new_context(viewport={"width": width, "height": 940}, reduced_motion="reduce")
                context.route(re.compile(r"^https?://"), lambda route: route.abort())
                page = context.new_page()
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{GUIDE.resolve().as_uri()}#training", wait_until="load")
                page.wait_for_function("window.NexusTraining && window.NexusShooter")
                jump = page.get_by_role("navigation", name="Training sections").get_by_role("link", name="Plan")
                jump.focus()
                page.keyboard.press("Enter")
                page.wait_for_function("location.hash === '#training/plan' && window.NexusTraining.snapshot().sectionId === 'plan'")
                assert page.evaluate("window.NexusTraining.snapshot().sectionId") == "plan"
                assert page.locator('#page-training section[data-nht-section] h2').count() == 7
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
                assert not errors, errors
                context.close()
        finally:
            browser.close()
