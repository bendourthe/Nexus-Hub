"""Check semantic flow build order in the pinned historical LVEDP deck."""

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
MANIFEST = {
    12: ["The reference", "Data platform", "Console", "Enhanced", "Compare"],
    14: ["1 · Enhance the platform", "2 · Enhance the console", "3 · Run the validation",
         "4 · Ship both", "5 · Document it"],
    15: ["R&D", "Software", "Quality", "Approval and change control"],
}

INSPECT = r"""slideNumber => {
  const slide = document.querySelector(`.dkslide[data-slide="${slideNumber}"]`);
  const svg = slide.querySelector('.dkflow svg:has(.dknode)');
  const nodes = [...svg.querySelectorAll('.dknode[data-fragment]')].map(el => {
    const rect = el.querySelector('rect');
    const css = getComputedStyle(el);
    return {label: el.querySelector('.nt').textContent.trim(),
            fragment: Number(el.dataset.fragment),
            box: [Number(rect.getAttribute('x')), Number(rect.getAttribute('y')),
                  Number(rect.getAttribute('width')), Number(rect.getAttribute('height'))],
            delay: parseFloat(css.animationDelay), animation: css.animationName,
            opacity: Number(css.opacity)};
  });
  const distance = (x, y, box) => Math.hypot(
    Math.max(box[0] - x, 0, x - box[0] - box[2]),
    Math.max(box[1] - y, 0, y - box[1] - box[3]));
  const lines = [...svg.querySelectorAll('line.dkarrow[data-fragment]')].map((el, index) => {
    const x1 = Number(el.getAttribute('x1'));
    const y1 = Number(el.getAttribute('y1'));
    const x2 = Number(el.getAttribute('x2'));
    const y2 = Number(el.getAttribute('y2'));
    const closest = (x, y) => nodes.map((node, nodeIndex) =>
      ({nodeIndex, distance: distance(x, y, node.box)})).sort((a, b) => a.distance - b.distance)[0];
    const css = getComputedStyle(el);
    return {index, fragment: Number(el.dataset.fragment), source: closest(x1, y1),
            target: closest(x2, y2), delay: parseFloat(css.animationDelay),
            animation: css.animationName, opacity: Number(css.opacity)};
  });
  return {slideNumber, nodes, lines};
}"""


def failures(result: dict) -> list[str]:
    slide = result["slideNumber"]
    nodes = result["nodes"]
    labels = [node["label"] for node in sorted(nodes, key=lambda item: item["fragment"])]
    errors = []
    if labels != MANIFEST[slide]:
        errors.append(f"slide {slide}: node order differs from the authored manifest")
    if [node["fragment"] for node in sorted(nodes, key=lambda item: item["fragment"])] != list(
        range(1, len(nodes) + 1)
    ):
        errors.append(f"slide {slide}: node fragments are not contiguous")
    for node in nodes:
        if node["animation"] != "dkfrag" or not 0 <= node["delay"] <= 2.6:
            errors.append(f"slide {slide}: {node['label']} has no bounded fragment animation")
    for line in result["lines"]:
        source_match = line["source"]
        target_match = line["target"]
        if source_match["distance"] > 12 or target_match["distance"] > 12:
            errors.append(f"slide {slide}: line {line['index']} has an unmatched endpoint")
            continue
        source = nodes[source_match["nodeIndex"]]
        target = nodes[target_match["nodeIndex"]]
        if source is target or source["fragment"] >= line["fragment"]:
            errors.append(f"slide {slide}: line {line['index']} precedes its source")
        if target["fragment"] != line["fragment"]:
            errors.append(f"slide {slide}: line {line['index']} is separate from its target")
        if line["animation"] != "dkfrag" or abs(line["delay"] - target["delay"]) > 0.001:
            errors.append(f"slide {slide}: line {line['index']} animation misses its target")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path, help="Read-only local algorithms Git repository")
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
                                        reduced_motion="no-preference")
                requests = []
                page.route("**/*", lambda route: (requests.append(route.request.url), route.abort()))
                page.set_content(blob.decode("utf-8-sig"), wait_until="domcontentloaded")
                page.locator("[data-deck-open]").first.click()
                counts = {"slides": 0, "nodes": 0, "connectors": 0, "failures": []}
                for slide in MANIFEST:
                    page.locator(".dkdots button").nth(slide - 1).evaluate("el => el.click()")
                    page.wait_for_timeout(30)
                    state = page.evaluate(INSPECT, slide)
                    counts["slides"] += 1
                    counts["nodes"] += len(state["nodes"])
                    counts["connectors"] += len(state["lines"])
                    counts["failures"].extend(failures(state))
                    page.wait_for_timeout(2150)
                    settled = page.evaluate(INSPECT, slide)
                    if any(item["opacity"] < 0.95 for item in settled["nodes"] + settled["lines"]):
                        counts["failures"].append(f"slide {slide}: a node or connector did not reveal")
                page.locator(".dkdots button").nth(13).evaluate("el => el.click()")
                page.wait_for_timeout(30)
                baseline = page.evaluate(INSPECT, 14)
                if failures(baseline):
                    counts["failures"].append("slide 14: negative-control baseline was not clean")
                page.locator('.dkslide[data-slide="14"] line.dkarrow').first.evaluate(
                    "el => el.dataset.fragment = '1'")
                early = page.evaluate(INSPECT, 14)
                counts["earlyArrowRejected"] = bool(failures(early))
                page.locator('.dkslide[data-slide="14"] line.dkarrow').first.evaluate(
                    "el => el.setAttribute('x1', '10000')")
                detached = page.evaluate(INSPECT, 14)
                counts["detachedArrowRejected"] = any(
                    "unmatched endpoint" in error for error in failures(detached))
                counts["externalRequests"] = len(requests)
                if not counts["earlyArrowRejected"] or not counts["detachedArrowRejected"]:
                    counts["failures"].append("negative control was not rejected")
                if requests:
                    counts["failures"].append("external network request occurred")
                report["viewports"].append({"size": [width, height], **counts})
                page.close()
        finally:
            browser.close()
    print(json.dumps(report, separators=(",", ":"), ensure_ascii=True))
    if any(viewport["failures"] for viewport in report["viewports"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
