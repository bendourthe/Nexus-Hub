#!/usr/bin/env python3
"""Capture a landing page for the fly-over film (references/landing-flyover.md, step 1).

  probe   <url> --out RUN/capture        page height, background, section outline, candidate
                                         lift pieces, and full-page strips to look at
  capture <url> --spec spec.json --out RUN/capture [--logo FILE] [--fonts]
          [--brand NAME] [--line1 TEXT] [--tail TEXT]
                                         locked full-page texture with the lifted pieces hidden,
                                         each piece alone on transparency with 28px padding,
                                         and layers.json with every position and anchor

The page is loaded with prefers-reduced-motion: reduce, so diagrams and terminals render their
designed final frame, then scrolled once to the bottom and locked (animations paused, timers
cleared, animation frames stopped) before anything is measured. This is the only networked step:
it reaches the given URL and, with --fonts, the two title fonts' host.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

PAD = 28
VIEWPORT = {"width": 1440, "height": 900}
ROLES = ("heroChip", "button", "card", "chip", "photo", "flyChip", "testimonial")
FONT_CSS = "https://fonts.googleapis.com/css2?family=Geist:wght@500&family=Instrument+Serif:ital@1&display=block"
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
FONT_FILES = {"Geist": "geist-500.woff2", "Instrument Serif": "instrument-serif-italic.woff2"}

LOCK_JS = """() => {
  document.getAnimations().forEach(a => { try { a.pause(); } catch (e) {} });
  const hi = setTimeout(() => {}, 0);
  for (let i = 0; i <= hi; i++) { clearTimeout(i); clearInterval(i); }
  window.requestAnimationFrame = () => 0;
}"""
SCROLL_JS = """async () => {
  const H = document.documentElement.scrollHeight;
  for (let y = 0; y <= H; y += 300) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 70)); }
  await new Promise(r => setTimeout(r, 800));
  window.scrollTo(0, 0);
}"""
CSS = """
html.cap-base [data-layer] { visibility: hidden !important; }
html.cap-iso, html.cap-iso body { background: transparent !important; }
html.cap-iso body { visibility: hidden !important; }
html.cap-iso [data-layer-on] { visibility: visible !important; }
"""

PROBE_JS = """() => {
  const H = document.documentElement.scrollHeight;
  const label = (el) => {
    const cls = typeof el.className === 'string' ? el.className.trim().replace(/\\s+/g, '.') : '';
    return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (cls ? '.' + cls : '');
  };
  const box = (el) => { const r = el.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; };
  const sections = [...document.querySelectorAll('header, nav, section, footer, main > div')]
    .filter(el => el.getBoundingClientRect().height > 40)
    .map(el => { const h = el.querySelector('h1,h2,h3'); return { el: label(el), box: box(el), title: h ? h.textContent.trim().replace(/\\s+/g, ' ').slice(0, 70) : '' }; });
  const boxy = [...document.querySelectorAll('body *')].filter(el => {
    const r = el.getBoundingClientRect();
    if (r.width < 40 || r.height < 24 || r.width > 1200) return false;
    const cs = getComputedStyle(el);
    return cs.borderTopWidth !== '0px' || cs.backgroundColor !== 'rgba(0, 0, 0, 0)' || cs.boxShadow !== 'none' || el.tagName === 'IMG';
  }).map(el => ({ el: label(el), box: box(el), text: (el.textContent || el.alt || '').trim().replace(/\\s+/g, ' ').slice(0, 40) }));
  return { height: H, width: document.documentElement.scrollWidth, bg: getComputedStyle(document.body).backgroundColor, sections, candidates: boxy.slice(0, 400) };
}"""

MARK_JS = """({ specs, anchors, pad }) => {
  const parse = (s) => {
    let m = s.match(/rgba?\\(([^)]+)\\)/);
    if (m) { const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return [p[0] / 255, p[1] / 255, p[2] / 255, p[3] ?? 1]; }
    m = s.match(/color\\(srgb ([^)]+)\\)/);
    if (m) { const p = m[1].split(/[ /]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p[3] ?? 1]; }
    return [0, 0, 0, 0];
  };
  const over = (top, under) => {
    const a = top[3] + under[3] * (1 - top[3]);
    if (a === 0) return [0, 0, 0, 0];
    return [0, 1, 2].map(i => (top[i] * top[3] + under[i] * under[3] * (1 - top[3])) / a).concat(a);
  };
  // Translucent pieces get the opaque colour they show over the page, so they read the same lifted.
  const opaqueBg = (el) => {
    const own = parse(getComputedStyle(el).backgroundColor);
    if (own[3] === 0 || own[3] >= 0.999) return null;
    const chain = [];
    for (let p = el.parentElement; p; p = p.parentElement) chain.push(parse(getComputedStyle(p).backgroundColor));
    let base = [1, 1, 1, 1];
    for (let i = chain.length - 1; i >= 0; i--) base = over(chain[i], base);
    const c = over(own, base).map((v, i) => i < 3 ? Math.round(v * 255) : 1);
    return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
  };
  const find = (q) => {
    const spec = typeof q === 'string' ? { sel: q } : q;
    let els = [...document.querySelectorAll(spec.sel)];
    if (spec.text) { const ts = [].concat(spec.text); els = els.filter(e => ts.some(t => e.textContent.replace(/\\s+/g, ' ').includes(t))); }
    return els;
  };
  const layers = [];
  for (const spec of specs) {
    for (const el of find(spec)) {
      if (el.closest('[data-layer]')) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      const id = 'L' + String(layers.length).padStart(2, '0');
      el.setAttribute('data-layer', id);
      layers.push({
        id, role: spec.role, sel: spec.sel, pad,
        text: el.textContent.trim().replace(/\\s+/g, ' ').slice(0, 48),
        x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height,
        radius: parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0,
        bg: opaqueBg(el),
      });
    }
  }
  const rect = (q) => { const el = find(q)[0]; if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height }; };
  const centre = (q) => { const b = rect(q); return b ? b.y + b.h / 2 : null; };
  const hero = rect(anchors.hero);
  return {
    layers,
    page: { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight, bg: getComputedStyle(document.body).backgroundColor },
    anchors: {
      heroBottom: hero ? hero.y + hero.h : null,
      secondTitle: centre(anchors.secondTitle),
      footerTitle: centre(anchors.footerTitle),
      mockup: anchors.mockup ? centre(anchors.mockup) : null,
      button: anchors.button ? rect(anchors.button) : null,
    },
  };
}"""


def _check_url(url: str) -> str:
    if urlparse(url).scheme not in ("http", "https"):
        raise SystemExit(f"only http(s) pages can be captured: {url}")
    return url


def _open(playwright, url: str, scale: int):
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport=VIEWPORT, device_scale_factor=scale, reduced_motion="reduce")
    page.goto(url, wait_until="networkidle", timeout=90_000)
    page.evaluate(SCROLL_JS)
    page.wait_for_timeout(2500)
    page.evaluate(LOCK_JS)
    return browser, page


def _playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415 - lazy
    except ImportError as exc:
        raise SystemExit("Playwright is not importable; run scripts/ensure_render_env.py for the one-time setup") from exc
    return sync_playwright()


def probe(url: str, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    with _playwright() as p:
        browser, page = _open(p, _check_url(url), 1)
        info = page.evaluate(PROBE_JS)
        strip = 2600
        for i, y in enumerate(range(0, info["height"], strip)):
            page.screenshot(path=str(out / f"probe-strip-{i}.png"), full_page=True, scale="css",
                            clip={"x": 0, "y": y, "width": VIEWPORT["width"], "height": min(strip, info["height"] - y)})
        browser.close()
    (out / "probe.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(f"page {info['width']}x{info['height']}, background {info['bg']}, {len(info['sections'])} sections, "
          f"{len(info['candidates'])} candidate pieces; details in {out / 'probe.json'}, strips probe-strip-*.png")
    return 0


def _fetch_fonts(out: Path) -> list[str]:
    """Download the two title fonts (latin subset) from the font host; render then stays offline."""
    fonts = out / "fonts"
    fonts.mkdir(exist_ok=True)
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
    css = urllib.request.urlopen(urllib.request.Request(FONT_CSS, headers=ua), timeout=20).read().decode()
    saved = []
    for block in re.findall(r"/\* latin \*/\s*@font-face\s*{[^}]+}", css):
        family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        src = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
        if urlparse(src).hostname not in FONT_HOSTS or family not in FONT_FILES:
            continue
        (fonts / FONT_FILES[family]).write_bytes(urllib.request.urlopen(src, timeout=20).read())
        saved.append(FONT_FILES[family])
    return saved


def capture(args: argparse.Namespace) -> int:
    out: Path = args.out
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    bad = [s for s in spec.get("layers", []) if s.get("role") not in ROLES]
    if bad:
        raise SystemExit(f"unknown roles {sorted({s.get('role') for s in bad})}; use {ROLES}")
    for key in ("hero", "secondTitle", "footerTitle"):
        if not spec.get("anchors", {}).get(key):
            raise SystemExit(f"spec.anchors.{key} is required")
    (out / "pieces").mkdir(parents=True, exist_ok=True)
    with _playwright() as p:
        browser, page = _open(p, _check_url(args.url), 2)
        page.add_style_tag(content=CSS)
        meta = page.evaluate(MARK_JS, {"specs": spec["layers"], "anchors": spec["anchors"], "pad": PAD})
        missing = [k for k in ("heroBottom", "secondTitle", "footerTitle") if meta["anchors"][k] is None]
        if missing:
            raise SystemExit(f"anchors not found on the page: {missing}")
        page.evaluate("() => document.documentElement.classList.add('cap-base')")
        page.screenshot(path=str(out / "page.png"), full_page=True)
        page.evaluate("() => document.documentElement.classList.remove('cap-base')")
        for layer in meta["layers"]:
            page.evaluate(
                """({ id, bg }) => {
                  document.documentElement.classList.add('cap-iso');
                  const el = document.querySelector(`[data-layer="${id}"]`);
                  el.setAttribute('data-layer-on', '');
                  if (bg) el.style.setProperty('background-color', bg, 'important');
                  for (const e of document.body.querySelectorAll('*')) {
                    if (el.contains(e) || e.contains(el)) continue;
                    if (getComputedStyle(e).visibility === 'visible') { e.setAttribute('data-cap-hid', ''); e.style.setProperty('visibility', 'hidden', 'important'); }
                  }
                }""", {"id": layer["id"], "bg": layer["bg"]})
            layer["file"] = f"pieces/{layer['id']}.png"
            page.screenshot(path=str(out / layer["file"]), full_page=True, omit_background=True,
                            clip={"x": layer["x"] - PAD, "y": layer["y"] - PAD, "width": layer["w"] + 2 * PAD, "height": layer["h"] + 2 * PAD})
            page.evaluate(
                """({ id, bg }) => {
                  document.documentElement.classList.remove('cap-iso');
                  const el = document.querySelector(`[data-layer="${id}"]`);
                  el.removeAttribute('data-layer-on');
                  if (bg) el.style.removeProperty('background-color');
                  for (const e of document.querySelectorAll('[data-cap-hid]')) { e.style.removeProperty('visibility'); e.removeAttribute('data-cap-hid'); }
                }""", {"id": layer["id"], "bg": layer["bg"]})
        browser.close()
    meta["page"].update(file="page.png", dpr=2)
    meta["url"] = args.url
    meta["title"] = {"badge": args.brand or "", "line1": args.line1 or "", "tail": args.tail or ""}
    if args.logo:
        logo = Path(args.logo)
        shutil.copyfile(logo, out / ("logo" + logo.suffix.lower()))
        meta["logo"] = "logo" + logo.suffix.lower()
    if args.fonts:
        try:
            meta["fonts"] = _fetch_fonts(out)
        except OSError as exc:
            print(f"fonts not fetched ({exc}); the title falls back to system fonts", file=sys.stderr)
    (out / "layers.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"page {meta['page']['width']}x{meta['page']['height']}, {len(meta['layers'])} lifted pieces, anchors {meta['anchors']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe")
    pr.add_argument("url")
    pr.add_argument("--out", type=Path, required=True)
    ca = sub.add_parser("capture")
    ca.add_argument("url")
    ca.add_argument("--spec", required=True)
    ca.add_argument("--out", type=Path, required=True)
    ca.add_argument("--logo")
    ca.add_argument("--fonts", action="store_true")
    ca.add_argument("--brand")
    ca.add_argument("--line1")
    ca.add_argument("--tail")
    args = ap.parse_args(argv)
    return probe(args.url, args.out) if args.cmd == "probe" else capture(args)


if __name__ == "__main__":
    sys.exit(main())
