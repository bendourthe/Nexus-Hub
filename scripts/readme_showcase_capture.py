"""Capture simultaneous monitor views and editor-specific platform illustrations."""
from __future__ import annotations

import json

from readme_guide_capture import save_frames, shot


def capture_showcase(page, root, output, kind, source):
    page.add_init_script("window.README_GENERATED=" + json.dumps(source).replace("<", "\\u003c"))
    page.goto((root / "guides/website/readme-showcase.html").as_uri() + "?tour=" + kind)
    page.wait_for_function("!!window.demoReady")
    frames, durations = [], []
    count = page.evaluate("window.showcaseDemo.scenes.length")
    for index in range(count):
        before = max(0, index - 1) if kind == "usage" and index == 2 else index
        origin = page.evaluate("i=>window.showcaseDemo.render(i,{progress:0,click:false})", before)
        if kind == "usage" and index == 1:
            origin = [{"x": 140, "y": 350}] * 3
        for progress in (.2, .4, .6, .8, 1):
            page.evaluate("([i,p,origin,showHover])=>window.showcaseDemo.render(i,{progress:p,from:origin,click:false,showHover})", [before, progress, origin, index != 1 or progress == 1])
            frames.append(shot(page.locator("#showcase-stage")))
            durations.append(120)
        if kind == "usage" and index == 2:
            page.evaluate("()=>window.showcaseDemo.render(1,{click:true})")
            frames.append(shot(page.locator("#showcase-stage")))
            durations.append(250)
            # Exercise each status button, then retain the synchronized result.
            for button in page.locator(".status button").all():
                button.click()
        page.evaluate("i=>window.showcaseDemo.render(i,{click:false})", index)
        if kind == "usage":
            assert page.locator(".desktop").count() == 3
            assert page.locator(".hover:not([hidden])").count() == (3 if index == 1 else 0)
            assert page.locator(".dashboard:not([hidden])").count() == (3 if index >= 2 else 0)
        frames.append(shot(page.locator("#showcase-stage")))
        durations.append(6000 if index else 3000)
        frames[-1].save(output / f"{kind}-scene-{index+1:02}.png", optimize=True)
    return save_frames(output, kind, frames, durations, "readme-showcase.* + shipped monitor and settings renderers", count, poster=11)
