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
            page.wait_for_function("window.NexusTraining && window.NexusAsteroids")

            initial = page.evaluate("window.NexusTraining.snapshot()")
            assert initial["sceneId"] == "describe"
            assert initial["sceneIndex"] == 0
            assert initial["appliedThrough"] == -1
            assert initial["ran"] is False
            assert initial["game"] == {
                "collisionMode": "buggy",
                "splittingEnabled": False,
                "situation": "wrap-boundary",
            }
            assert set(initial["filePaths"]) == {"src/collision.js", "src/game.js"}
            assert page.locator('[data-nht="file-body"] img').count() == 0

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
                    missed = page.evaluate(
                        """
                        () => {
                          const api = window.NexusAsteroids;
                          api.pause("training-proof");
                          api.reset("wrap-boundary");
                          return api.step(1 / 60);
                        }
                        """
                    )
                    assert missed["collisionMode"] == "buggy"
                    assert missed["score"] == 0
                    assert missed["missedWrapHits"] == 1
                    assert [rock["id"] for rock in missed["asteroids"]] == [
                        "edge-rock"
                    ]

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
                        '[data-nht="file"][data-file-path="src/collision.js"]'
                    )
                    source_item.focus()
                    source_item.press("Enter")
                    active_path = page.evaluate(
                        "document.activeElement && document.activeElement.dataset.filePath"
                    )
                    assert active_path == "src/collision.js"
                    page.locator('[data-file-path="src/collision.js"]').press(
                        "ArrowDown"
                    )
                    assert page.evaluate(
                        "document.activeElement && document.activeElement.dataset.filePath"
                    ) == "src/game.js"

                if scene["id"] in {"implement", "compare"}:
                    result = page.evaluate(
                        """
                        () => {
                          const api = window.NexusAsteroids;
                          api.pause("training-proof");
                          return api.step(1 / 60);
                        }
                        """
                    )
                    assert result["collisionMode"] == "fixed"
                    assert result["score"] == 100
                    assert result["missedWrapHits"] == 0
                    if scene["id"] == "implement":
                        assert result["splittingEnabled"] is False
                        assert result["asteroids"] == []
                        assert page.locator(".diff-add").count() > 0
                        assert page.locator(".diff-remove").count() > 0
                        stable = page.evaluate("window.NexusTraining.snapshot()")
                        assert page.evaluate("window.NexusTraining.run()") == stable
                    else:
                        assert result["splittingEnabled"] is True
                        assert [rock["id"] for rock in result["asteroids"]] == [
                            "fragment-10",
                            "fragment-11",
                        ]

            assert "asteroids-briefing.html" in expected_paths
            body = page.locator('[data-nht="file-body"]')
            assert body.locator("img").count() == 0
            assert not console_errors, f"console errors: {console_errors}"
            assert not page_errors, f"page errors: {page_errors}"
        finally:
            browser.close()
