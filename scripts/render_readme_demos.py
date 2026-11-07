"""Render README media from the original guide, shipped settings panel and desktop handoff.

Requires local Node, settings development dependencies, Playwright Chromium and Pillow. No network calls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_process import install_no_window_default
from playwright.sync_api import sync_playwright
from readme_guide_capture import (
    capture_commands,
    capture_installation,
    capture_workflow,
    save_frames,
    shot,
)
from readme_provider_capture import capture_provider, component_script, components

ROOT = Path(__file__).resolve().parents[1]
install_no_window_default()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing files are never overwritten")
    parser.add_argument("--only", choices=["installation", "workflow", "settings", "commands", "continuity", "usage"])
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    artifacts, errors = [], []
    source = components(ROOT)
    (output / "usage-components.js").write_text(component_script(source), encoding="utf-8")
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1, reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        for kind, capture in (("installation", capture_installation), ("workflow", capture_workflow), ("commands", capture_commands)):
            if not args.only or args.only == kind:
                artifacts.append(capture(page, ROOT, output))
                print(kind + " captured", flush=True)
        for kind in ("settings", "usage"):
            if not args.only or args.only == kind:
                artifacts.append(capture_provider(page, ROOT, output, kind, source))
                print(kind + " captured", flush=True)
        if not args.only or args.only == "continuity":
            page.goto((ROOT / "guides/website/readme-demos.html").as_uri())
            page.wait_for_function("!!window.readmeDemos")
            frames = []
            count = page.evaluate("window.readmeDemos.scenes.continuity.length")
            for index in range(count):
                scene = page.evaluate("i=>window.readmeDemos.scenes.continuity[i]",index)
                motion = page.evaluate("i=>window.readmeDemos.render('continuity',i,{progress:0,generateProgress:.05})",index)
                for progress in (.2,.4,.6,.8,1):
                    page.evaluate("([i,progress,from])=>window.readmeDemos.render('continuity',i,{progress,from,click:false,generateProgress:.05})",[index,progress,motion["from"]])
                    frames.append(shot(page.locator("#continuity-stage")))
                if scene.get("generate"):
                    for progress in (.12,.3,.52,.75,1):
                        page.evaluate("([i,progress])=>window.readmeDemos.render('continuity',i,{generateProgress:progress})",[index,progress])
                        frames.append(shot(page.locator("#continuity-stage")))
                page.evaluate("i=>window.readmeDemos.render('continuity',i)",index)
                page.wait_for_function("Array.from(document.images).every(i=>i.complete)")
                assert page.locator(".native-window").count() == 2
                assert page.locator(".process-strip [aria-current=step]").count() == 1
                frames.append(shot(page.locator("#continuity-stage")))
                frames[-1].save(output / f"continuity-scene-{index+1:02}.png", optimize=True)
                if scene["phase"] in (9,10):
                    assert page.locator("textarea[aria-label='ChatGPT prompt']").input_value() == page.evaluate("window.readmeDemos.handoffText")
                if scene["phase"] >= 11:
                    assert page.locator(".sent-handoff pre").inner_text() == page.evaluate("window.readmeDemos.handoffText")
            durations = []
            for scene in page.evaluate("window.readmeDemos.scenes.continuity"):
                durations.extend([100]*5)
                if scene.get("generate"): durations.extend([600]*5)
                durations.append(3400 if scene["phase"] in (2,5,9,11,12) else 1900)
            artifacts.append(save_frames(output,"continuity",frames,durations,"guides/website/readme-platforms.* + readme-tour.*",count,poster=17))
        assert not errors, errors
        browser.close()
    report = {"artifacts": artifacts, "browser_errors": errors, "execution": "Illustrations only; no installer, agent or user settings executed"}
    (output / "render-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
