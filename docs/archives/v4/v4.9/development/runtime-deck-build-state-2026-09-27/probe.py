"""Inspect the preserved LVEDP deck's authored build states without changing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright


BLOB = "bab8523:docs/handbooks/algorithms/lvedp-algorithm.html"
SHA256 = "c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c"
VIEWPORTS = [(1366, 768), (390, 844)]


def inspect_slide(page, index: int) -> dict:
    page.locator(".dkdots button").nth(index).click()
    page.wait_for_timeout(30)
    start = page.evaluate(
        """() => {
          const slide = document.querySelector('.dkslide.on');
          const fragments = [...slide.querySelectorAll('[data-fragment]')];
          const indices = [...new Set(fragments.map(el => Number(el.dataset.fragment)))].sort((a,b) => a-b);
          const ends = new Map(indices.map(i => [i, 0]));
          for (const animation of slide.getAnimations({subtree:true})) {
            const target = animation.effect && animation.effect.target;
            const fragment = target && target.closest('[data-fragment]');
            if (!fragment || !slide.contains(fragment)) continue;
            const end = animation.effect.getComputedTiming().endTime;
            if (Number.isFinite(end)) ends.set(Number(fragment.dataset.fragment), Math.max(ends.get(Number(fragment.dataset.fragment)) || 0, end));
          }
          const figures = [...slide.querySelectorAll('.dkfig svg, .dkfill svg, .dkflow svg')].map(svg => {
            const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
            return {width:Math.round(r.width),height:Math.round(r.height),
                    viewBox:vb && vb.width && vb.height ? [vb.width,vb.height] : null,
                    preserveAspectRatio:svg.getAttribute('preserveAspectRatio') || 'xMidYMid meet'};
          });
          return {slide:Number(slide.dataset.slide), fragmentElements:fragments.length,
                  indices, ends:Object.fromEntries(ends), figures};
        }"""
    )
    states = []
    elapsed = 30
    for fragment in start["indices"]:
        target = min(8000, max(elapsed, int(start["ends"][str(fragment)]) + 50))
        if target > elapsed:
            page.wait_for_timeout(target - elapsed)
            elapsed = target
        states.append(
            page.evaluate(
                """() => {
                  const slide = document.querySelector('.dkslide.on');
                  const visible = [...slide.querySelectorAll('[data-fragment]')].filter(el => {
                    const r = el.getBoundingClientRect();
                    let node = el;
                    while (node && node !== slide) {
                      const style = getComputedStyle(node);
                      if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) < .5) return false;
                      node = node.parentElement;
                    }
                    return r.width > 0 && r.height > 0;
                  });
                  return {visibleFragments:visible.length, activeSlides:document.querySelectorAll('.dkslide.on').length,
                          visibleIndices:[...new Set(visible.map(el => Number(el.dataset.fragment)))].sort((a,b) => a-b)};
                }"""
            )
        )
        states[-1]["afterFragment"] = fragment
        states[-1]["elapsedMs"] = elapsed
    start["states"] = states
    start["fragmentBudgetPass"] = start["indices"] == list(range(1, len(start["indices"]) + 1)) and len(start["indices"]) <= 8
    return start


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path, help="Read-only local rd-data-dev repository")
    args = parser.parse_args()
    blob = subprocess.check_output(["git", "show", BLOB], cwd=args.source_repo)
    digest = hashlib.sha256(blob).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"Unexpected source SHA-256: {digest}")
    html = blob.decode("utf-8-sig")
    report = {"blob": BLOB, "sha256": digest, "viewports": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                requests = []
                page.route("**/*", lambda route: (requests.append(route.request.url), route.abort()))
                page.set_content(html, wait_until="domcontentloaded")
                page.locator("[data-deck-open]").first.click()
                slides = page.locator(".dkslide").count()
                measurements = [inspect_slide(page, index) for index in range(slides)]
                page.locator(".dkslide").nth(7).locator("[data-fragment]").first.evaluate(
                    "el => el.setAttribute('data-fragment', '0')"
                )
                mutant = inspect_slide(page, 7)
                report["viewports"].append({
                    "size": [width, height], "slides": measurements, "externalRequests": requests,
                    "zeroIndexControlRejected": measurements[7]["fragmentBudgetPass"] and not mutant["fragmentBudgetPass"],
                })
                page.close()
        finally:
            browser.close()
    print(json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    main()
