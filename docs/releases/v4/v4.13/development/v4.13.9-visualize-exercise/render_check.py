"""Evidence copy of the T416 render check: open each HTML output headless, network blocked, read computed values."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

FIXTURES = Path(__file__).resolve().parents[6] / "tests" / "fixtures" / "inline-visualization"
SHOTS = Path(sys.argv[1])
PROBE = """() => {
  const doc = document.documentElement;
  const all = [...document.querySelectorAll('*')];
  const handlers = all.filter(el => [...el.attributes].some(a => /^on/i.test(a.name))).length;
  const svg = document.querySelector('svg').getBoundingClientRect();
  const fig = document.querySelector('figure').getBoundingClientRect();
  const labels = [...document.querySelectorAll('svg text')].map(t => {
    const r = t.getBoundingClientRect();
    return {text: t.textContent, w: Math.round(r.width), h: Math.round(r.height),
            inside: r.left >= svg.left - 1 && r.right <= svg.right + 1 && r.top >= svg.top - 1 && r.bottom <= svg.bottom + 1};
  });
  const boxes = [...document.querySelectorAll('svg text')].map(t => ({t: t.textContent, r: t.getBoundingClientRect()}));
  const overlaps = [];
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const a = boxes[i].r, b = boxes[j].r;
    if (a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1) overlaps.push([boxes[i].t, boxes[j].t]);
  }
  return {
    overlaps,
    scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth,
    scripts: document.querySelectorAll('script').length, handlers,
    foreignObject: document.querySelectorAll('foreignObject').length,
    hrefs: document.querySelectorAll('[href], [*|href]').length,
    csp: !!document.querySelector('meta[http-equiv="Content-Security-Policy"]'),
    svg: {w: Math.round(svg.width), h: Math.round(svg.height)},
    figure: {x: fig.x, y: fig.y, w: fig.width, h: fig.height},
    labelsOutside: labels.filter(l => !l.inside).map(l => l.text),
    labelsZero: labels.filter(l => l.w === 0 || l.h === 0).map(l => l.text),
    title: document.title,
    alerted: window.__alerted === true,
  };
}"""


def check(page_name: str, width: int, theme: str, browser) -> dict:
    attempted: list[str] = []
    context = browser.new_context(viewport={"width": width, "height": 900}, device_scale_factor=1, color_scheme=theme)
    page = context.new_page()
    page.add_init_script("window.alert = () => { window.__alerted = true; };")
    def route(r):
        if not r.request.url.startswith("file:"):
            attempted.append(r.request.url)
        r.abort() if not r.request.url.startswith("file:") else r.continue_()
    page.route("**/*", route)
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    page.goto((FIXTURES / page_name).as_uri())
    page.wait_for_timeout(300)
    data = page.evaluate(PROBE)
    fig = data["figure"]
    shot = SHOTS / f"{Path(page_name).stem}-{width}-{theme}.png"
    page.screenshot(path=str(shot), clip={"x": fig["x"], "y": fig["y"], "width": min(fig["w"], 1500), "height": min(fig["h"], 1500)})
    context.close()
    data.update({"page": page_name, "width": width, "theme": theme, "attempted_requests": attempted,
                 "dialogs": dialogs, "capture": str(shot)})
    return data


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name in ("sample.html", "hostile.html"):
            for width in (420, 1440):
                for theme in ("light", "dark"):
                    results.append(check(name, width, theme, browser))
        browser.close()
    for r in results:
        ok = (r["scrollWidth"] <= r["clientWidth"] and r["scripts"] == 0 and r["handlers"] == 0
              and r["foreignObject"] == 0 and r["hrefs"] == 0 and r["csp"] and not r["attempted_requests"]
              and not r["dialogs"] and not r["alerted"] and not r["labelsOutside"] and not r["labelsZero"]
              and not r["overlaps"])
        print(json.dumps({k: r[k] for k in ("page", "width", "theme", "scrollWidth", "clientWidth", "scripts", "handlers",
                                            "foreignObject", "hrefs", "csp", "svg", "attempted_requests", "dialogs",
                                            "labelsOutside", "labelsZero", "overlaps")}), "PASS" if ok else "FAIL")
    print("captures:", [r["capture"] for r in results if r["width"] == 1440 and r["theme"] == "light"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
