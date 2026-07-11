#!/usr/bin/env python3
"""Author the Phase 3 minimum-interaction-budget demo page.

Takes the chart-free scanned fixture model (models/scanned_enriched.json:
corrected text, a verified table, two scanned-page images - ZERO chart blocks)
and authors a single self-contained page implementing all five budget points
from references/interactive-features.md:

    1. Section nav with active-state tracking (aria-current)
    2. Scroll-triggered reveals (IntersectionObserver, .js-gated)
    3. Hover + focus-visible affordances (cards, images, table rows)
    4. Pan/zoom lightbox on every non-decorative image (dialog, focus trap)
    5. Signature interaction: animated KPI counters from the table values

All vanilla inline JS/CSS, reduced-motion-guarded, zero external requests.
Output: models/budget-demo.html (gitignored evidence; verified by
verify_budget_demo.py). Run gen_fixtures.py + verify_phase1.py + the Phase 2
enrichment first if models/scanned_enriched.json is missing.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = HERE / "models" / "scanned_enriched.json"
OUT = HERE / "models" / "budget-demo.html"

CSS = """
:root { --paper:#f7f4ee; --ink:#2b2b28; --accent:#8a3324; --line:#d8d2c4; }
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink);
  font: 17px/1.6 Georgia, 'Times New Roman', serif; }
header.hero { padding: 4rem 8vw 2rem; border-bottom: 3px double var(--line); }
h1 { font-size: 2.6rem; margin: 0 0 .3rem; letter-spacing: -.01em; }
nav.toc { position: sticky; top: 0; background: var(--paper);
  border-bottom: 1px solid var(--line); padding: .6rem 8vw; z-index: 5; }
nav.toc a { color: var(--ink); text-decoration: none; margin-right: 1.4rem;
  padding: .2rem 0; border-bottom: 2px solid transparent;
  font-family: Verdana, Geneva, sans-serif; font-size: .8rem; }
nav.toc a[aria-current="true"] { border-bottom-color: var(--accent);
  color: var(--accent); }
nav.toc a:hover, nav.toc a:focus-visible { border-bottom-color: var(--ink); }
#progress { position: fixed; top: 0; left: 0; height: 3px;
  background: var(--accent); width: 0; z-index: 9; }
main { padding: 0 8vw 4rem; }
section { padding: 2.5rem 0; border-bottom: 1px solid var(--line); }
.js .reveal { opacity: 0; transform: translateY(14px);
  transition: opacity .45s ease, transform .45s ease; }
.js .reveal.revealed { opacity: 1; transform: none; }
.kpis { display: flex; gap: 1.2rem; flex-wrap: wrap; margin: 1.2rem 0; }
.card { background: #fffdf8; border: 1px solid var(--line); padding: 1rem 1.4rem;
  min-width: 10rem; transition: transform .18s ease, box-shadow .18s ease; }
.card:hover, .card:focus-visible { transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(43,43,40,.12); outline: 2px solid var(--accent);
  outline-offset: 2px; }
.card .num { font-size: 2.2rem; color: var(--accent);
  font-family: Verdana, Geneva, sans-serif; }
table { border-collapse: collapse; margin: 1rem 0; width: 100%; max-width: 28rem; }
th, td { border: 1px solid var(--line); padding: .5rem .9rem; text-align: left; }
tbody tr { transition: background .15s ease; }
tbody tr:hover, tbody tr:focus-within { background: #efe9db; }
button.imgbtn { border: 1px solid var(--line); padding: 0; background: none;
  cursor: zoom-in; display: inline-block; max-width: 46%; margin: .6rem 1rem .6rem 0;
  transition: transform .18s ease; }
button.imgbtn:hover, button.imgbtn:focus-visible { transform: scale(1.015);
  outline: 3px solid var(--accent); outline-offset: 3px; }
button.imgbtn img { display: block; width: 100%; height: auto; }
#lightbox { position: fixed; inset: 0; background: rgba(20,18,14,.9);
  display: none; align-items: center; justify-content: center; z-index: 20; }
#lightbox.open { display: flex; }
#lightbox img { max-width: 92vw; max-height: 88vh; cursor: grab;
  transform-origin: 0 0; }
#lightbox .bar { position: absolute; top: .8rem; right: 1rem; display: flex;
  gap: .6rem; }
#lightbox button { font: .85rem Verdana, sans-serif; background: var(--paper);
  border: 0; padding: .45rem .8rem; cursor: pointer; }
#lightbox button:focus-visible { outline: 3px solid var(--accent); }
details { border: 1px solid var(--line); background: #fffdf8; padding: .6rem 1rem;
  margin: 1rem 0; max-width: 40rem; }
summary { cursor: pointer; font-family: Verdana, Geneva, sans-serif;
  font-size: .85rem; }
summary:hover, summary:focus-visible { color: var(--accent); }
@media (prefers-reduced-motion: reduce) {
  .js .reveal { opacity: 1; transform: none; transition: none; }
  .card, button.imgbtn, tbody tr { transition: none; }
  html { scroll-behavior: auto !important; }
}
html { scroll-behavior: smooth; }
"""

JS = """
document.documentElement.classList.add('js');
var motionOK = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// 2. Scroll reveals (once, staggered per section child)
var ro = new IntersectionObserver(function (es) {
  es.forEach(function (e) {
    if (e.isIntersecting) { e.target.classList.add('revealed'); ro.unobserve(e.target); }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach(function (el) { ro.observe(el); });

// 1. Active-state nav tracking + reading progress
var links = {};
document.querySelectorAll('nav.toc a').forEach(function (a) {
  links[a.getAttribute('href').slice(1)] = a;
});
var no = new IntersectionObserver(function (es) {
  es.forEach(function (e) {
    if (e.isIntersecting) {
      Object.keys(links).forEach(function (k) { links[k].removeAttribute('aria-current'); });
      var link = links[e.target.id];
      if (link) { link.setAttribute('aria-current', 'true'); }
    }
  });
}, { rootMargin: '-40% 0px -50% 0px' });
document.querySelectorAll('main section[id]').forEach(function (s) { no.observe(s); });
var bar = document.getElementById('progress');
var ticking = false;
window.addEventListener('scroll', function () {
  if (ticking) { return; }
  ticking = true;
  requestAnimationFrame(function () {
    var h = document.documentElement;
    bar.style.width = (100 * h.scrollTop / (h.scrollHeight - h.clientHeight)) + '%';
    ticking = false;
  });
});

// 5. Animated KPI counters (exact final value; instant under reduced motion)
var co = new IntersectionObserver(function (es) {
  es.forEach(function (e) {
    if (!e.isIntersecting) { return; }
    co.unobserve(e.target);
    var el = e.target, target = parseInt(el.getAttribute('data-count'), 10);
    if (!motionOK) { el.textContent = target; return; }
    var t0 = null;
    function step(t) {
      if (!t0) { t0 = t; }
      var p = Math.min((t - t0) / 800, 1);
      el.textContent = Math.round(target * p);
      if (p < 1) { requestAnimationFrame(step); } else { el.textContent = target; }
    }
    requestAnimationFrame(step);
  });
}, { threshold: 0.6 });
document.querySelectorAll('[data-count]').forEach(function (el) { co.observe(el); });

// 4. Lightbox: wheel zoom, drag pan, reset, Escape, focus trap + restore
var lb = document.getElementById('lightbox');
var lbImg = lb.querySelector('img');
var opener = null, scale = 1, tx = 0, ty = 0, dragging = false, dx = 0, dy = 0;
function apply() { lbImg.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')'; }
function openLB(btn) {
  opener = btn;
  lbImg.src = btn.querySelector('img').src;
  lbImg.alt = btn.querySelector('img').alt;
  scale = 1; tx = ty = 0; apply();
  lb.classList.add('open');
  lb.querySelector('button.close').focus();
}
function closeLB() {
  lb.classList.remove('open');
  if (opener) { opener.focus(); opener = null; }
}
document.querySelectorAll('button.imgbtn').forEach(function (btn) {
  btn.addEventListener('click', function () { openLB(btn); });
});
lb.querySelector('button.close').addEventListener('click', closeLB);
lb.querySelector('button.reset').addEventListener('click', function () {
  scale = 1; tx = ty = 0; apply();
});
lb.addEventListener('click', function (e) { if (e.target === lb) { closeLB(); } });
lb.addEventListener('wheel', function (e) {
  e.preventDefault();
  scale = Math.min(8, Math.max(0.4, scale * (e.deltaY < 0 ? 1.15 : 0.87)));
  apply();
}, { passive: false });
lbImg.addEventListener('pointerdown', function (e) {
  dragging = true; dx = e.clientX - tx; dy = e.clientY - ty;
  lbImg.setPointerCapture(e.pointerId);
});
lbImg.addEventListener('pointermove', function (e) {
  if (dragging) { tx = e.clientX - dx; ty = e.clientY - dy; apply(); }
});
lbImg.addEventListener('pointerup', function () { dragging = false; });
document.addEventListener('keydown', function (e) {
  if (!lb.classList.contains('open')) { return; }
  if (e.key === 'Escape') { closeLB(); }
  if (e.key === 'Tab') {  // focus trap across the two dialog buttons
    var f = lb.querySelectorAll('button');
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
  }
});
"""


def main() -> int:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    paragraphs: list = []
    table = None
    pages: list = []
    for section in model["sections"]:
        for block in section["blocks"]:
            if block["type"] == "paragraph" and not block["text"].startswith("Page"):
                paragraphs.append(block["text"])
            elif block["type"] == "table":
                table = block
            elif block["type"] == "image" and block.get("origin") == "scanned-page":
                pages.append(block)
    assert table is not None and len(pages) == 2, "unexpected fixture shape"

    rows = "".join(
        f'<tr tabindex="0"><td>{r[0]}</td><td>{r[1]}</td></tr>' for r in table["rows"]
    )
    kpis = "".join(
        f'<div class="card reveal" tabindex="0"><div class="num" '
        f'data-count="{r[1]}" aria-label="{r[1]} units">0</div>'
        f"<div>{r[0]} region units</div></div>"
        for r in table["rows"]
    )
    figures = "".join(
        f'<button class="imgbtn reveal" type="button" '
        f'aria-label="Open scanned page {b["page"]} in the zoom viewer">'
        f'<img src="{b["data_uri"]}" alt="{b["alt"]}"></button>'
        for b in pages
    )
    paras = "".join(f'<p class="reveal">{t}</p>' for t in paragraphs[:4])

    html = f"""<!DOCTYPE html>
<!-- Phase 3 minimum-interaction-budget demo: authored from the chart-free
     scanned fixture model. Design record: warm paper / Georgia serif /
     madder accent #8a3324 / sticky small-caps nav - deliberately NOT the
     dark+amber attractor. All five budget points implemented inline. -->
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quarterly Update - interactive demo</title>
<style>{CSS}</style></head>
<body>
<div id="progress" aria-hidden="true"></div>
<header class="hero"><h1>Quarterly Update</h1>
<p>An interactive presentation of a scanned two-page report - no chartable
data, full interaction budget.</p></header>
<nav class="toc" aria-label="Sections">
<a href="#summary">Summary</a><a href="#figures">Source pages</a>
<a href="#detail">Detail</a></nav>
<main>
<section id="summary"><h2 class="reveal">Summary</h2>{paras}
<div class="kpis">{kpis}</div>
<table class="reveal"><thead><tr><th>{table["header"][0]}</th>
<th>{table["header"][1]}</th></tr></thead><tbody>{rows}</tbody></table>
</section>
<section id="figures"><h2 class="reveal">Source pages</h2>
<p class="reveal">Every scanned page opens in the pan/zoom viewer (click,
or focus and press Enter).</p>{figures}</section>
<section id="detail"><h2 class="reveal">Detail</h2>
<details class="reveal"><summary>Verification notes</summary>
<p>OCR text on these pages was verified against the page images; numeric
values were confirmed by direct reading. The page-2 figure is illustrative
(no axes) and is therefore presented as an original, not reconstructed.</p>
</details></section>
</main>
<div id="lightbox" role="dialog" aria-modal="true" aria-label="Image viewer">
<div class="bar"><button type="button" class="reset">Reset view</button>
<button type="button" class="close">Close</button></div>
<img src="" alt=""></div>
<script>{JS}</script>
<!-- COVERAGE RECONCILIATION - scanned.pdf
manifest: scanned pages 2 (OCR'd 2, low-confidence flagged for verification);
          images found 2 / kept 2 / skipped 0; tables 1
- [rendered]      scanned page 1 image (lightbox)
- [rendered]      scanned page 2 image (lightbox)
- [verified-ocr]  table page 1 (Region/Units: North 42, South 37 confirmed against the page image)
- [agent-read]    heading + two body paragraphs (OCR spacing/merge corrections applied)
- [skipped]       page 2 bar figure reconstruction DECLINED - no axes/ticks/labels, caption says
                  illustrative (low confidence); presented via the page image instead
verdict: ACCOUNTED - 0 unaccounted -->
</body></html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
