"""Measure visible text and SVG viewport containment at every authored deck build state."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright


BLOB = "bab8523:docs/handbooks/algorithms/lvedp-algorithm.html"
SHA256 = "c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c"
VIEWPORTS = [(1366, 768), (1024, 768), (768, 1024), (390, 844)]

SNAPSHOT = r"""() => {
  const slide = document.querySelector('.dkslide.on');
  const canvas = document.querySelector('#deck .dkcanvas');
  const stage = canvas.getBoundingClientRect();
  const floor = stage.height * 0.02;
  const visible = el => {
    let opacity = 1;
    for (let node = el; node; node = node.parentElement) {
      const css = getComputedStyle(node);
      if (css.display === 'none' || css.visibility === 'hidden') return false;
      opacity *= Number(css.opacity);
      if (opacity < 0.5) return false;
    }
    return true;
  };
  const failures = [];
  let textNodes = 0;
  const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const label = node.textContent.trim();
    if (!label || !visible(node.parentElement)) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const rect = range.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) continue;
    const el = node.parentElement;
    const css = getComputedStyle(el);
    let scale = 1;
    if (el instanceof SVGElement) {
      const m = el.getScreenCTM();
      if (m) scale = Math.min(Math.hypot(m.a, m.b), Math.hypot(m.c, m.d));
    } else {
      for (let parent = el; parent; parent = parent.parentElement) {
        const style = getComputedStyle(parent);
        const m = new DOMMatrix(style.transform === 'none' ? undefined : style.transform);
        scale *= Math.min(Math.hypot(m.a, m.b), Math.hypot(m.c, m.d)) *
          (parseFloat(style.zoom) || 1);
      }
    }
    const px = parseFloat(css.fontSize) * scale;
    textNodes++;
    if (px + 0.1 < floor) failures.push({text: label.slice(0, 50), px: +px.toFixed(2)});
  }
  const clipped = [];
  const svgs = [...slide.querySelectorAll('.dkfig svg, .dkfill svg, .dkflow svg')];
  let visibleFigures = 0;
  for (const [index, svg] of svgs.entries()) {
    if (!visible(svg)) continue;
    const r = svg.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    visibleFigures++;
    if (r.left < -0.5 || r.top < -0.5 || r.right > innerWidth + 0.5 ||
        r.bottom > innerHeight + 0.5) {
      clipped.push({index, box: [r.left, r.top, r.right, r.bottom].map(x => +x.toFixed(1))});
    }
  }
  return {slideNumber: Number(slide.dataset.slide),
          active: document.querySelectorAll('.dkslide.on').length,
          deckScrollLeft: document.querySelector('#deck').scrollLeft,
          floor: +floor.toFixed(2), textNodes, failures, visibleFigures, clipped};
}"""

TIMING = """() => {
  const slide = document.querySelector('.dkslide.on');
  const indices = [...new Set([...slide.querySelectorAll('[data-fragment]')]
    .map(el => Number(el.dataset.fragment)))].sort((a, b) => a - b);
  const ends = new Map(indices.map(i => [i, 0]));
  for (const animation of slide.getAnimations({subtree: true})) {
    const target = animation.effect && animation.effect.target;
    const fragment = target && target.closest('[data-fragment]');
    if (!fragment || !slide.contains(fragment)) continue;
    const end = animation.effect.getComputedTiming().endTime;
    const index = Number(fragment.dataset.fragment);
    if (Number.isFinite(end)) ends.set(index, Math.max(ends.get(index) || 0, end));
  }
  return {indices, ends: Object.fromEntries(ends)};
}"""


def inspect_slide(page, index: int) -> list[dict]:
    if index:
        page.keyboard.press("ArrowRight")
    page.wait_for_timeout(30)
    timing = page.evaluate(TIMING)
    if any(end > 7950 for end in timing["ends"].values()):
        raise RuntimeError(f"Slide {index + 1} has a fragment timer outside the 8s probe window")
    states = [{"after": 0, **page.evaluate(SNAPSHOT)}]
    elapsed = 30
    for fragment in timing["indices"]:
        target = min(8000, max(elapsed, int(timing["ends"][str(fragment)]) + 50))
        if target > elapsed:
            page.wait_for_timeout(target - elapsed)
            elapsed = target
        states.append({"after": fragment, **page.evaluate(SNAPSHOT)})
    return states


def summarize(states: list[tuple[int, dict]]) -> dict:
    floor_states = [(slide, state["after"]) for slide, state in states if state["failures"]]
    clipped_states = [(slide, state["after"]) for slide, state in states if state["clipped"]]
    return {
        "states": len(states),
        "textNodeChecks": sum(state["textNodes"] for _, state in states),
        "visibleSvgBoxChecks": sum(state["visibleFigures"] for _, state in states),
        "floorFailureStates": len(floor_states),
        "floorFailureSlides": sorted({slide for slide, _ in floor_states}),
        "clippedFigureStates": len(clipped_states),
        "clippedFigureSlides": sorted({slide for slide, _ in clipped_states}),
        "activeSlideFailures": sum(state["active"] != 1 for _, state in states),
        "wrongSlideStates": sum(state["slideNumber"] != slide for slide, state in states),
        "internalScrollStates": sum(state["deckScrollLeft"] != 0 for _, state in states),
        "firstFloorFailure": next(
            ({"slide": slide, "after": state["after"], **state["failures"][0]}
             for slide, state in states if state["failures"]), None),
        "firstClippedFigure": next(
            ({"slide": slide, "after": state["after"], **state["clipped"][0]}
             for slide, state in states if state["clipped"]), None),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path, help="Read-only local algorithms Git repository")
    args = parser.parse_args()
    blob = subprocess.check_output(["git", "show", BLOB], cwd=args.source_repo)
    digest = hashlib.sha256(blob).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"Unexpected source SHA-256: {digest}")
    result = {"blob": BLOB, "sha256": digest, "viewports": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                requests = []
                page.route("**/*", lambda route: (requests.append(route.request.url), route.abort()))
                page.set_content(blob.decode("utf-8-sig"), wait_until="domcontentloaded")
                page.locator("[data-deck-open]").first.click()
                slides = page.locator(".dkslide").count()
                states = [(index + 1, state)
                          for index in range(slides)
                          for state in inspect_slide(page, index)]
                summary = summarize(states)
                summary.update({"size": [width, height], "slides": slides,
                                "externalRequests": len(requests)})
                if (width, height) == VIEWPORTS[0]:
                    page.locator(".dkdots button").nth(7).evaluate("el => el.click()")
                    page.wait_for_timeout(3000)
                    baseline = page.evaluate(SNAPSHOT)
                    page.locator(".dkslide.on svg text").first.evaluate(
                        "el => el.style.setProperty('font-size', '1px', 'important')")
                    small = page.evaluate(SNAPSHOT)
                    page.locator(".dkslide.on .dkfig svg, .dkslide.on .dkfill svg, "
                                 ".dkslide.on .dkflow svg").first.evaluate(
                        "el => el.style.transform = 'translateX(-10000px)'")
                    shifted = page.evaluate(SNAPSHOT)
                    summary["negativeControls"] = {
                        "fontRejected": len(small["failures"]) > len(baseline["failures"]),
                        "figureRejected": len(shifted["clipped"]) > len(small["clipped"]),
                    }
                result["viewports"].append(summary)
                page.close()
        finally:
            browser.close()
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
