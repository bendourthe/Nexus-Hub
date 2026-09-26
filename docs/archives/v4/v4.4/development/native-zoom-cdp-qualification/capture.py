"""Capture bounded guide evidence through Chromium's native zoom and CDP."""

import base64
import io
import json
import tempfile
from pathlib import Path

from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
EXTENSION = ROOT / "docs/archives/v4/v4.4/development/native-zoom-qualification/extension"
GUIDE = ROOT / "guides/website/nexus-hub-guide.html"
TARGETS = (
    ("home", "home", "#page-home"),
    ("tokens", "foundations", "#fx-tokens"),
    ("models", "foundations", "#fx-model-lifecycle"),
    ("prompt-engineering", "foundations", "#fx-prompts"),
    ("context-engineering", "foundations", "#fx-context"),
    ("agentic-platforms", "foundations", "#fx-agent-platform"),
    ("harnesses", "foundations", "#fx-harness"),
    ("training", "training", "#page-training"),
)


def capture(page, cdp, target, where, output):
    page.evaluate(
        """({selector, where}) => {
            const rect = document.querySelector(selector).getBoundingClientRect();
            const top = rect.top + scrollY;
            const position = where === 'top' ? top - 60 : top + rect.height - innerHeight + 60;
            scrollTo(0, Math.max(0, position));
        }""",
        {"selector": target, "where": where},
    )
    page.wait_for_timeout(200)
    raw = base64.b64decode(
        cdp.send(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": False, "fromSurface": True},
        )["data"]
    )
    output.write_bytes(raw)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    return {
        "file": output.name,
        "scroll_y": page.evaluate("scrollY"),
        "image_size": list(image.size),
        "channel_stddev": [round(value, 2) for value in ImageStat.Stat(image).stddev],
    }


def dark_pixels(raw):
    image = Image.open(io.BytesIO(raw)).convert("L")
    return sum(count for value, count in enumerate(image.histogram()) if value < 100)


def main():
    output = HERE / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory() as profile, sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            profile,
            channel="chromium",
            headless=True,
            viewport={"width": 1280, "height": 800},
            reduced_motion="reduce",
            args=[
                f"--disable-extensions-except={EXTENSION}",
                f"--load-extension={EXTENSION}",
            ],
        )
        page = context.new_page()
        worker = context.service_workers[0] if context.service_workers else context.wait_for_event("serviceworker")
        cdp = context.new_cdp_session(page)
        page.goto(
            'data:text/html,<body style="margin:0;height:2500px;background:white">'
            '<h1 id="target" style="position:absolute;top:1000px;color:black">Scroll control</h1></body>'
        )
        control_zoom = worker.evaluate(
            """async () => {
                const tab = (await chrome.tabs.query({active: true})).at(-1);
                await chrome.tabs.setZoom(tab.id, 2);
                return chrome.tabs.getZoom(tab.id);
            }"""
        )
        page.locator("#target").scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        ordinary = page.screenshot()
        protocol = base64.b64decode(
            cdp.send(
                "Page.captureScreenshot",
                {"format": "png", "captureBeyondViewport": False, "fromSurface": True},
            )["data"]
        )
        (output / "control-playwright.png").write_bytes(ordinary)
        (output / "control-cdp.png").write_bytes(protocol)
        control = {
            "zoom": control_zoom,
            "dpr": page.evaluate("devicePixelRatio"),
            "scroll_y": page.evaluate("scrollY"),
            "playwright_dark_pixels": dark_pixels(ordinary),
            "cdp_dark_pixels": dark_pixels(protocol),
        }
        (HERE / "method-control.json").write_text(json.dumps(control, indent=2) + "\n", encoding="utf-8")
        for theme in ("dark", "light"):
            for name, route, selector in TARGETS:
                page.goto(f"{GUIDE.resolve().as_uri()}#{route}", wait_until="domcontentloaded")
                page.wait_for_function(
                    "route => document.querySelector('#page-' + route).classList.contains('active')",
                    arg=route,
                )
                if page.evaluate("document.documentElement.dataset.theme") != theme:
                    page.locator("#themeToggle").evaluate("element => element.click()")
                zoom = worker.evaluate(
                    """async () => {
                        const tab = (await chrome.tabs.query({active: true})).at(-1);
                        await chrome.tabs.setZoom(tab.id, 2);
                        return chrome.tabs.getZoom(tab.id);
                    }"""
                )
                metrics = page.evaluate(
                    """selector => {
                        const element = document.querySelector(selector);
                        return {
                            theme: document.documentElement.dataset.theme,
                            dpr: devicePixelRatio,
                            inner_width: innerWidth,
                            document_overflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
                            target_overflow: Math.max(0, element.scrollWidth - element.clientWidth),
                            visible: getComputedStyle(element).display !== 'none',
                        };
                    }""",
                    selector,
                )
                if zoom != 2 or metrics["dpr"] != 2 or metrics["theme"] != theme or not metrics["visible"]:
                    raise RuntimeError(f"Invalid capture state for {theme}/{name}: {zoom}, {metrics}")
                shots = [
                    capture(page, cdp, selector, where, output / f"{theme}-{name}-{where}.png")
                    for where in ("top", "end")
                ]
                rows.append({"route": route, "scene": name, "zoom": zoom, **metrics, "captures": shots})
        context.close()
    (HERE / "metrics.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Control: {control}; captured {len(rows)} route/theme combinations and {sum(len(row['captures']) for row in rows)} views")


if __name__ == "__main__":
    main()
