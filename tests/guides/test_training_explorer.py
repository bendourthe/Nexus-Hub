"""Phase 5 browser contracts for the cumulative Training project explorer."""

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
        render_gate(  # type: ignore[operator]
            f"Playwright Chromium cannot launch: {error}"
        )


def test_training_runtime_reduces_files_and_game_state_deterministically(
    render_gate: object,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    data = json.loads(
        (
            GUIDE.parent / "example" / "training-scenes.json"
        ).read_text(encoding="utf-8")
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 1000, "height": 940})
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            page = context.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.goto(f"{GUIDE.resolve().as_uri()}#training/describe", wait_until="load")
            page.wait_for_function("window.NexusTraining && window.NexusShooter")

            initial = page.evaluate("window.NexusTraining.snapshot()")
            assert initial["sceneId"] == "describe"
            assert initial["sceneIndex"] == 0
            assert initial["appliedThrough"] == -1
            assert initial["ran"] is False
            assert initial["game"] == {
                "damageMode": "buggy",
                "verticalMovementEnabled": False,
                "fixture": "enemy-hit",
            }
            assert set(initial["filePaths"]) == {"src/damage.js", "src/game.js"}
            assert page.locator('[data-nht="file-body"] img').count() == 0

            invalid_numeric_snapshots = page.evaluate(
                """
                () => [
                  window.NexusTraining.go(NaN),
                  window.NexusTraining.go(1.5)
                ]
                """
            )
            assert invalid_numeric_snapshots == [initial, initial]

            page.evaluate("window.NexusTraining.selectFile('not-created-yet.md')")
            assert page.locator('[data-nht="file-path"]').inner_text() == "not-created-yet.md"
            assert "Not created yet" in page.locator('[data-nht="file-body"]').inner_text()
            assert "not created" in page.locator('[data-nht="file-state"]').inner_text().lower()

            expected_paths = {item["path"] for item in data["initial"]["files"]}
            run_button = page.locator('[data-nht="run"]')
            terminal = page.locator('[data-nht="terminal"]')

            for index, scene in enumerate(data["scenes"]):
                page.evaluate("sceneId => window.NexusTraining.go(sceneId)", scene["id"])
                before = page.evaluate("window.NexusTraining.snapshot()")
                assert before["sceneId"] == scene["id"]
                assert before["sceneIndex"] == index
                assert before["appliedThrough"] == index - 1
                assert before["ran"] is False
                assert set(before["filePaths"]) == expected_paths

                if scene["id"] == "describe":
                    # Proof of the seeded bug: in buggy mode the very FIRST enemy shot
                    # is terminal while lives still read 3.
                    dead = page.evaluate(
                        """
                        () => {
                          const api = window.NexusShooter;
                          api.reset("enemy-hit");
                          api.start();
                          let s = api.snapshot(), n = 0;
                          while (s.lifecycle !== "destroyed" && n++ < 500) s = api.step();
                          return s;
                        }
                        """
                    )
                    assert dead["damageMode"] == "buggy"
                    assert dead["lifecycle"] == "destroyed"
                    assert dead["lives"] == 3, "the bug destroys the ship without spending a life"

                run_button.click()
                assert run_button.is_enabled(), "Show now must remain clickable"
                if run_button.inner_text() == "Show now":
                    run_button.click()
                page.wait_for_function(
                    "document.querySelector('[data-nht=\"run\"]').textContent === 'Run again'"
                )

                terminal_text = terminal.inner_text()
                for line in scene["output"]:
                    assert line in terminal_text
                for file_change in scene["files"]:
                    expected_paths.add(file_change["path"])

                after = page.evaluate("window.NexusTraining.snapshot()")
                assert after["appliedThrough"] == index
                assert after["ran"] is True
                assert after["game"] == scene["game"]
                assert set(after["filePaths"]) == expected_paths
                tree_paths = set(
                    page.locator('[data-nht="file"]').evaluate_all(
                        "items => items.map(item => item.dataset.filePath)"
                    )
                )
                assert tree_paths == expected_paths

                if scene["id"] == "describe":
                    assert "<img onerror>" in terminal_text
                    assert terminal.locator("img").count() == 0
                    source_item = page.locator(
                        '[data-nht="file"][data-file-path="src/damage.js"]'
                    )
                    source_item.focus()
                    source_item.press("Enter")
                    active_path = page.evaluate(
                        "document.activeElement && document.activeElement.dataset.filePath"
                    )
                    assert active_path == "src/damage.js"
                    page.locator('[data-file-path="src/damage.js"]').press(
                        "ArrowDown"
                    )
                    assert page.evaluate(
                        "document.activeElement && document.activeElement.dataset.filePath"
                    ) == "src/game.js"

                if scene["id"] in {"implement", "compare"}:
                    result = page.evaluate(
                        """
                        () => {
                          const api = window.NexusShooter;
                          api.reset();
                          api.start();
                          let s = api.snapshot(), n = 0;
                          while (s.lives === 3 && s.lifecycle !== "destroyed" && n++ < 800) {
                            s = api.step();
                          }
                          return s;
                        }
                        """
                    )
                    assert result["damageMode"] == "fixed"
                    if scene["id"] == "implement":
                        # Fixed damage: the first hit costs ONE life and play continues.
                        assert result["lives"] == 2
                        assert result["lifecycle"] != "destroyed"
                        assert result["verticalMovementEnabled"] is False
                        assert page.locator(".diff-add").count() > 0
                        assert page.locator(".diff-remove").count() > 0
                        stable = page.evaluate("window.NexusTraining.snapshot()")
                        assert page.evaluate("window.NexusTraining.run()") == stable
                    else:
                        assert result["verticalMovementEnabled"] is True
                        assert result["fixture"] == "play"

            assert "shooter-briefing.html" in expected_paths
            body = page.locator('[data-nht="file-body"]')
            assert body.locator("img").count() == 0
            assert not console_errors, f"console errors: {console_errors}"
            assert not page_errors, f"page errors: {page_errors}"
        finally:
            browser.close()


def test_training_present_mode_keeps_major_regions_separate(
    render_gate: object,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    selectors = {
        "game": ".nht-game",
        "terminal": ".term--nht",
        "explorer": ".nht-explorer",
        "takeaway": ".nht-takeaway",
        "controls": ".nht-controls",
    }
    pairs = (
        ("game", "terminal"),
        ("game", "explorer"),
        ("terminal", "explorer"),
        ("explorer", "takeaway"),
        ("takeaway", "controls"),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width, height in (
                (1920, 1080),
                (1440, 900),
                (1024, 768),
                (900, 900),
            ):
                context = browser.new_context(viewport={"width": width, "height": height})
                context.route(re.compile(r"^https?://"), lambda route: route.abort())
                page = context.new_page()
                page.goto(f"{GUIDE.resolve().as_uri()}#training/describe", wait_until="load")
                page.wait_for_function("window.NexusTraining && window.NexusShooter")
                page.locator("#nhtPresent").click()
                page.wait_for_function(
                    "document.getElementById('nhTraining').classList.contains('is-present')"
                )
                assert page.locator("#nhTraining").get_attribute("role") == "dialog"
                assert page.locator("#nhTraining").get_attribute("aria-modal") == "true"
                assert page.locator(".site-header").evaluate("element => element.inert")
                assert page.locator('[data-nht="exit-present"]').is_visible()
                rectangles = {
                    name: page.locator(selector).bounding_box()
                    for name, selector in selectors.items()
                }
                assert all(rectangles.values()), (
                    f"missing presentation region at {width}x{height}: {rectangles}"
                )
                for first, second in pairs:
                    first_box = rectangles[first]
                    second_box = rectangles[second]
                    assert first_box is not None and second_box is not None
                    overlap_width = max(
                        0,
                        min(
                            first_box["x"] + first_box["width"],
                            second_box["x"] + second_box["width"],
                        )
                        - max(first_box["x"], second_box["x"]),
                    )
                    overlap_height = max(
                        0,
                        min(
                            first_box["y"] + first_box["height"],
                            second_box["y"] + second_box["height"],
                        )
                        - max(first_box["y"], second_box["y"]),
                    )
                    assert overlap_width * overlap_height < 1, (
                        f"{first} overlaps {second} at {width}x{height}: "
                        f"{first_box} vs {second_box}"
                    )
                page.keyboard.press("Shift+Tab")
                assert page.evaluate(
                    "document.getElementById('nhTraining').contains(document.activeElement)"
                )
                page.keyboard.press("Escape")
                page.wait_for_function(
                    "!document.getElementById('nhTraining').classList.contains('is-present')"
                )
                assert page.evaluate("document.activeElement.id") == "nhtPresent"
                assert not page.locator(".site-header").evaluate("element => element.inert")
                page.locator("#nhtPresent").click()
                page.wait_for_function(
                    "document.getElementById('nhTraining').classList.contains('is-present')"
                )
                page.locator('[data-nht="exit-present"]').click()
                page.wait_for_function(
                    "!document.getElementById('nhTraining').classList.contains('is-present')"
                )
                assert page.evaluate("document.activeElement.id") == "nhtPresent"
                context.close()
        finally:
            browser.close()


def test_training_present_fallback_cleans_up_when_route_changes(
    render_gate: object,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 1000, "height": 900})
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            page = context.new_page()
            page_errors: list[str] = []
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.goto(f"{GUIDE.resolve().as_uri()}#training/describe", wait_until="load")
            page.wait_for_function("window.NexusTraining && window.NexusShooter")
            page.evaluate(
                """
                () => Object.defineProperty(
                  document.getElementById("nhTraining"),
                  "requestFullscreen",
                  {
                    configurable: true,
                    value: () => Promise.reject(new Error("fullscreen blocked for test"))
                  }
                )
                """
            )

            page.locator("#nhtPresent").click()
            page.wait_for_function(
                "document.getElementById('nhTraining').classList.contains('is-present')"
            )
            page.evaluate("location.hash = '#home'")
            page.wait_for_function(
                """
                document.body.getAttribute('data-page') === 'home'
                && !document.getElementById('nhTraining').classList.contains('is-present')
                """
            )

            assert not page.locator(".site-header").evaluate("element => element.inert")
            assert not page.locator("#page-home").evaluate("element => element.inert")
            assert page.locator("#nhTraining").get_attribute("role") is None
            assert page.locator("#nhTraining").get_attribute("aria-modal") is None
            assert not page_errors, f"page errors: {page_errors}"
            context.close()
        finally:
            browser.close()
