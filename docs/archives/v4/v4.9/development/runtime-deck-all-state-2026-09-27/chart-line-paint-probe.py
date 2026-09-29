"""Check settled chart-line paint on the pinned LVEDP runtime deck."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright


BLOB = "bab8523:docs/handbooks/algorithms/lvedp-algorithm.html"
SHA256 = "c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c"
VIEWPORTS = [(1366, 768), (1024, 768), (768, 1024), (390, 844)]


def shot(page) -> Image.Image:
    return Image.open(io.BytesIO(page.screenshot())).convert("RGB")


def changed_pixels(before: Image.Image, after: Image.Image, box: dict) -> int:
    left = max(0, int(box["left"]) - 3)
    top = max(0, int(box["top"]) - 3)
    right = min(before.width, int(box["right"]) + 4)
    bottom = min(before.height, int(box["bottom"]) + 4)
    if left >= right or top >= bottom:
        return 0
    difference = ImageChops.difference(
        before.crop((left, top, right, bottom)),
        after.crop((left, top, right, bottom)),
    )
    data = difference.tobytes()
    return sum(max(data[index:index + 3]) >= 16 for index in range(0, len(data), 3))


def inspect_chart(page, host) -> dict | None:
    paths = host.locator(".chart svg path.c-line")
    if not paths.count():
        return None
    changes = []
    for index in range(paths.count()):
        path = paths.nth(index)
        state = path.evaluate("""el => {
          const style = getComputedStyle(el);
          const box = el.getBoundingClientRect();
          return {opacity: Number(style.opacity), stroke: style.stroke,
            length: el.getTotalLength(), box: {left: box.left, top: box.top,
            right: box.right, bottom: box.bottom}};
        }""")
        if state["opacity"] < 0.95 or state["stroke"] == "none" or state["length"] <= 0:
            raise RuntimeError(f"Chart line {index} is not visibly styled: {state}")
        baseline = shot(page)
        path.evaluate("el => el.style.visibility = 'hidden'")
        hidden = shot(page)
        path.evaluate("el => el.style.removeProperty('visibility')")
        painted = changed_pixels(baseline, hidden, state["box"])
        if not painted:
            raise RuntimeError(f"Chart line {index} did not paint inside its viewport box: {state}")
        path.evaluate("el => el.style.setProperty('opacity', '0', 'important')")
        invisible = shot(page)
        path.evaluate("el => el.style.visibility = 'hidden'")
        invisible_hidden = shot(page)
        control = changed_pixels(invisible, invisible_hidden, state["box"])
        path.evaluate("el => {el.style.removeProperty('opacity'); el.style.removeProperty('visibility')}")
        if control:
            raise RuntimeError(f"Invisible chart-line control {index} changed {control} pixels")
        changes.append(painted)
    return {"figure": host.get_attribute("data-fig"), "linePaths": paths.count(),
            "paintedPixelMin": min(changes), "paintedPixelMax": max(changes),
            "invisibleControls": len(changes)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path)
    args = parser.parse_args()
    blob = subprocess.check_output(["git", "show", BLOB], cwd=args.source_repo)
    digest = hashlib.sha256(blob).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"Unexpected source SHA-256: {digest}")
    report = {"blob": BLOB, "sha256": digest, "viewports": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height},
                                        device_scale_factor=1, reduced_motion="no-preference")
                requests: list[str] = []
                errors: list[str] = []
                page.route("**/*", lambda route: (requests.append(route.request.url), route.abort()))
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.set_content(blob.decode("utf-8-sig"), wait_until="domcontentloaded")
                page.locator("[data-deck-open]").first.click()
                records = []
                null_stroke_rejected = False
                for index in range(page.locator(".dkslide").count()):
                    page.locator(".dkdots button").nth(index).evaluate("el => el.click()")
                    page.wait_for_timeout(2400)
                    pause_rule = page.add_style_tag(content=
                        "*,*::before,*::after{animation-play-state:paused!important;transition:none!important}")
                    state = page.evaluate("""() => ({active: document.querySelectorAll('.dkslide.on').length,
                      number: Number(document.querySelector('.dkslide.on').dataset.slide),
                      scroll: document.querySelector('#deck').scrollLeft})""")
                    if state != {"active": 1, "number": index + 1, "scroll": 0}:
                        raise RuntimeError(f"Unexpected deck state: {state}")
                    for host in page.locator(".dkslide.on .dkfig[data-fig]").all():
                        result = inspect_chart(page, host)
                        if result:
                            records.append({"slide": index + 1, **result})
                    if index == 1:
                        control_host = page.locator(".dkslide.on .dkfig[data-fig]").first
                        control_path = control_host.locator(".chart svg path.c-line").first
                        control_path.evaluate("el => el.style.setProperty('stroke', 'none', 'important')")
                        try:
                            inspect_chart(page, control_host)
                        except RuntimeError as error:
                            null_stroke_rejected = "not visibly styled" in str(error)
                        finally:
                            control_path.evaluate("el => el.style.removeProperty('stroke')")
                    pause_rule.evaluate("el => el.remove()")
                if len(records) != 14 or not null_stroke_rejected or requests or errors:
                    raise RuntimeError(f"Incomplete chart coverage or browser errors: "
                                       f"{len(records)} samples, {null_stroke_rejected}, {requests}, {errors}")
                report["viewports"].append({"size": [width, height], "samples": records,
                                            "nullStrokeControlRejected": null_stroke_rejected,
                                            "externalRequests": requests, "pageErrors": errors})
                page.close()
        finally:
            browser.close()
    print(json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    main()
