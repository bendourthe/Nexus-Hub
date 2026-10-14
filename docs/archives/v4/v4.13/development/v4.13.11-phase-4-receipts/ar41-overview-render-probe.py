"""Render the overview handbook offline and record reading + Presentation Mode evidence."""
import json, sys, pathlib, hashlib
from playwright.sync_api import sync_playwright

html = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
rec = {"file": str(html), "sha256": hashlib.sha256(html.read_bytes()).hexdigest()}
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 860}, device_scale_factor=1)
    errors, requests = [], []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("request", lambda r: requests.append(r.url) if not r.url.startswith(("file:", "data:", "blob:")) else None)
    page.goto(html.as_uri())
    page.wait_for_function("document.documentElement.dataset.dvReady === 'true' || document.body.dataset.dvReady === 'true'", timeout=15000)
    rec["reading"] = page.evaluate("""() => {
      const pages = [...document.querySelectorAll('[data-dv-page]')];
      const visible = pages.filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
      const headings = [...document.querySelectorAll('main h1, main h2')].map(h => h.textContent.trim()).slice(0, 12);
      return { title: document.title, pages: pages.length, visible_pages: visible.length,
               headings, scroll_width: document.documentElement.scrollWidth, viewport: innerWidth };
    }""")
    page.screenshot(path=str(out / "reading.png"), clip={"x": 0, "y": 0, "width": 1280, "height": 860})
    opener = page.locator("[data-dv-open]").first
    rec["open_label"] = opener.inner_text().strip()[:80]
    opener.click()
    page.wait_for_timeout(600)
    def deck_state():
        return page.evaluate("""() => {
          const decks = [...document.querySelectorAll('[data-dv-deck]')];
          const shown = decks.filter(d => { const s = getComputedStyle(d); const r = d.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; });
          const count = [...document.querySelectorAll('[data-dv-count]')].map(e => e.textContent.trim()).filter(Boolean);
          const r = shown[0] ? shown[0].getBoundingClientRect() : null;
          return { decks: decks.length, shown: shown.length, count, rect: r && {w: Math.round(r.width), h: Math.round(r.height)} };
        }""")
    rec["presentation_open"] = deck_state()
    page.screenshot(path=str(out / "presentation.png"), clip={"x": 0, "y": 0, "width": 1280, "height": 860})
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(400)
    rec["presentation_next"] = deck_state()
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    rec["after_escape"] = deck_state()
    rec["page_errors"] = errors
    rec["network_requests"] = requests
    b.close()
(out / "receipt.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
print(json.dumps(rec, indent=2))
