"""Inspect model-to-slide chart layout in the pinned LVEDP handbook."""

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

MEASURE = r"""() => {
  const box = el => {
    const r = el.getBoundingClientRect();
    return {width: r.width, height: r.height, aspect: r.width / r.height};
  };
  const chartData = (host, chart) => {
    const svg = host.querySelector('.chart svg');
    if (!svg || !chart) return null;
    const vb = svg.viewBox.baseVal;
    const plots = [...svg.querySelectorAll('rect.c-plot')].map(el =>
      ['x', 'y', 'width', 'height'].map(a => Number(el.getAttribute(a))));
    const target = box(host);
    const svgBox = box(svg);
    return {
      box: target,
      svgAspect: vb.width / vb.height,
      svgWidth: vb.width,
      svgHeight: vb.height,
      svgScreenWidth: svgBox.width,
      plots,
      xTicks: [...svg.querySelectorAll('text.c-tick')].length,
      legendMode: chart.legendMode || 'none',
      textPx: chart.textPx,
      notePx: chart.notePx,
      cols: chart.colsEff,
      rows: chart.geometry().rows,
    };
  };
  const slide = document.querySelector('.dkslide.on');
  const k = Number.parseFloat(getComputedStyle(document.querySelector('#deck'))
    .getPropertyValue('--k')) || 1;
  const deck = [...slide.querySelectorAll('.dkfig[data-fig]')].map(host => ({
    id: host.dataset.fig, ...chartData(host, host.chart),
    modelRects: ((window.SupiraFigModel && window.SupiraFigModel(host.dataset.fig)) ||
      {panels: []}).panels.map(panel => panel.rect || null),
  }));
  return {slide: Number(slide.dataset.slide), k,
    activeSlides: document.querySelectorAll('.dkslide.on').length,
    deckScrollLeft: document.querySelector('#deck').scrollLeft,
    pageChartHosts: document.querySelectorAll('figure.fig[id]').length, deck};
}"""


def describe(deck: dict, k: float, slide: int) -> dict:
    plot_aspects = [
        round(width / height, 3)
        for _, _, width, height in deck["plots"]
        if height
    ]
    return {
        "slide": slide,
        "id": deck["id"],
        "modelPanelCount": len(deck["modelRects"]),
        "slidePlotAspects": plot_aspects,
        "holderAspect": round(deck["box"]["aspect"], 3),
        "slideSvg": [deck["svgWidth"], deck["svgHeight"]],
        "slideTicks": deck["xTicks"],
        "slideLegend": deck["legendMode"],
        "slideTextPx": deck["textPx"],
        "slideNotePx": deck["notePx"],
        "slideCols": deck["cols"],
        "slideRows": deck["rows"],
        "slideSvgScaleBeyondStage": round(
            deck["svgScreenWidth"] / deck["svgWidth"] / k, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path)
    args = parser.parse_args()
    blob = subprocess.check_output(["git", "show", BLOB], cwd=args.source_repo)
    digest = hashlib.sha256(blob).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"Unexpected source SHA-256: {digest}")
    output = {"blob": BLOB, "sha256": digest, "viewports": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                requests: list[str] = []
                page.route("**/*", lambda route: (requests.append(route.request.url), route.abort()))
                page.set_content(blob.decode("utf-8-sig"), wait_until="domcontentloaded")
                page.locator("[data-deck-open]").first.click()
                records: list[dict] = []
                missing: list[str] = []
                page_chart_hosts = None
                count = page.locator(".dkslide").count()
                for index in range(count):
                    page.locator(".dkdots button").nth(index).evaluate("el => el.click()")
                    snapshot = page.evaluate(MEASURE)
                    if (snapshot["slide"] != index + 1 or snapshot["activeSlides"] != 1
                            or snapshot["deckScrollLeft"] != 0):
                        raise RuntimeError(f"Unexpected deck navigation at {width}x{height}, slide {index + 1}")
                    page_chart_hosts = snapshot["pageChartHosts"]
                    for deck_figure in snapshot["deck"]:
                        if deck_figure.get("box") and deck_figure["modelRects"]:
                            records.append(describe(deck_figure, snapshot["k"], index + 1))
                        else:
                            missing.append(deck_figure["id"])
                page.locator(".dkdots button").nth(1).evaluate("el => el.click()")
                baseline = page.evaluate(MEASURE)["deck"][0]
                page.locator(".dkslide.on .dkfig svg").first.evaluate(
                    "el => el.style.transform = 'scale(0.5)'")
                altered = page.evaluate(MEASURE)["deck"][0]
                baseline_scale = baseline["svgScreenWidth"] / baseline["svgWidth"]
                altered_scale = altered["svgScreenWidth"] / altered["svgWidth"]
                half_scale_rejected = altered_scale < baseline_scale * 0.75
                if (len(records) != 14 or missing or requests or page_chart_hosts != 0
                        or not half_scale_rejected
                        or any(not record["slidePlotAspects"]
                               or abs(record["slideSvgScaleBeyondStage"] - 1) > 0.02
                               or record["slideTextPx"] != 21 for record in records)):
                    raise RuntimeError(f"Unexpected chart state at {width}x{height}")
                output["viewports"].append({
                    "size": [width, height], "slides": count, "charts": records,
                    "pageChartHosts": page_chart_hosts,
                    "missingModelOrSlide": missing, "externalRequests": len(requests),
                    "negativeControl": {
                        "halfScaleRejected": half_scale_rejected,
                        "observedScaleRatio": round(altered_scale / baseline_scale, 3),
                    },
                })
                page.close()
        finally:
            browser.close()
    print(json.dumps(output, separators=(",", ":")))


if __name__ == "__main__":
    main()
