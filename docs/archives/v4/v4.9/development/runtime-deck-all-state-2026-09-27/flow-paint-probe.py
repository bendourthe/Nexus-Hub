"""Check painted connector bodies on the pinned LVEDP runtime flow slides."""

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
SLIDES = {12: 6, 14: 4, 15: 3}
LINE_SELECTOR = ".dkslide.on .dkflow svg:has(.dknode) line.dkarrow[data-fragment]"

MIDPOINT = r"""el => {
  const x = (Number(el.getAttribute('x1')) + Number(el.getAttribute('x2'))) / 2;
  const y = (Number(el.getAttribute('y1')) + Number(el.getAttribute('y2'))) / 2;
  const point = el.ownerSVGElement.createSVGPoint();
  point.x = x;
  point.y = y;
  const screen = point.matrixTransform(el.getScreenCTM());
  const css = getComputedStyle(el);
  return {x: screen.x, y: screen.y, opacity: Number(css.opacity),
          stroke: css.stroke, width: css.strokeWidth};
}"""


def shot(page) -> Image.Image:
    return Image.open(io.BytesIO(page.screenshot())).convert("RGB")


def pixel_change(before: Image.Image, after: Image.Image, x: float, y: float) -> dict:
    left = max(0, int(x) - 9)
    top = max(0, int(y) - 9)
    right = min(before.width, int(x) + 10)
    bottom = min(before.height, int(y) + 10)
    if left >= right or top >= bottom:
        return {"changed": 0, "maxDelta": 0, "offscreen": True}
    difference = ImageChops.difference(
        before.crop((left, top, right, bottom)),
        after.crop((left, top, right, bottom)),
    )
    data = difference.tobytes()
    deltas = [max(data[index:index + 3]) for index in range(0, len(data), 3)]
    return {"changed": sum(delta >= 16 for delta in deltas),
            "maxDelta": max(deltas, default=0), "offscreen": False}


def exercise_slide(page, slide: int, expected_lines: int) -> dict:
    page.locator(".dkdots button").nth(slide - 1).evaluate("el => el.click()")
    page.wait_for_timeout(2400)
    pause_rule = page.add_style_tag(
        content="*,*::before,*::after{animation-play-state:paused!important;transition:none!important}")
    state = page.evaluate("""slide => ({active: document.querySelectorAll('.dkslide.on').length,
      number: Number(document.querySelector('.dkslide.on').dataset.slide),
      scroll: document.querySelector('#deck').scrollLeft})""", slide)
    if state != {"active": 1, "number": slide, "scroll": 0}:
        raise RuntimeError(f"Unexpected deck state on slide {slide}: {state}")
    lines = page.locator(LINE_SELECTOR)
    if lines.count() != expected_lines:
        raise RuntimeError(f"Slide {slide} has {lines.count()} connectors, expected {expected_lines}")
    baseline = shot(page)
    records = []
    for index in range(expected_lines):
        line = lines.nth(index)
        point = line.evaluate(MIDPOINT)
        line.evaluate("el => el.style.visibility = 'hidden'")
        hidden = shot(page)
        line.evaluate("el => el.style.removeProperty('visibility')")
        change = pixel_change(baseline, hidden, point["x"], point["y"])
        if point["opacity"] < 0.95 or point["stroke"] == "none":
            raise RuntimeError(f"Slide {slide} connector {index} is not visibly styled: {point}")
        if change["offscreen"] or change["changed"] < 2 or change["maxDelta"] < 16:
            raise RuntimeError(f"Slide {slide} connector {index} has no painted midpoint: {change}")
        records.append({"index": index, "point": [round(point["x"], 1), round(point["y"], 1)],
                        "opacity": point["opacity"], "stroke": point["stroke"],
                        "width": point["width"], **change})
    control = lines.first
    center = control.evaluate(MIDPOINT)
    control.evaluate("el => el.style.setProperty('opacity', '0', 'important')")
    if control.evaluate("el => Number(getComputedStyle(el).opacity)") != 0:
        raise RuntimeError(f"Invisible-stroke control did not become invisible on slide {slide}")
    invisible = shot(page)
    control.evaluate("el => el.style.visibility = 'hidden'")
    invisible_hidden = shot(page)
    noise = pixel_change(invisible, invisible_hidden, center["x"], center["y"])
    control.evaluate("el => {el.style.removeProperty('opacity'); el.style.removeProperty('visibility')}")
    pause_rule.evaluate("el => el.remove()")
    if noise["offscreen"] or noise["changed"] or noise["maxDelta"]:
        raise RuntimeError(f"Invisible connector control changed pixels on slide {slide}: {noise}")
    return {"slide": slide, "lines": records, "invisibleStrokeControl": noise}


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
                slides = [exercise_slide(page, number, count) for number, count in SLIDES.items()]
                if requests or errors:
                    raise RuntimeError(f"Unexpected network or page errors at {width}x{height}: {requests}, {errors}")
                report["viewports"].append({"size": [width, height], "slides": slides,
                                            "externalRequests": requests, "pageErrors": errors})
                page.close()
        finally:
            browser.close()
    print(json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    main()
