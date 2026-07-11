#!/usr/bin/env python3
"""Build the Phase 5 worked example: TWO same-preset (technical) presentify
runs over the deck.pdf fixture model, driven by two committed design-entropy
briefs (brief-a.json / brief-b.json, rolled against design-history.json).

Each output implements: the reconstructed Revenue chart (medium confidence -
worksheet comment adjacent, provenance badge, original shown alongside and in
the view-original lightbox), the map/photo as lightboxed originals, the
decorative-logo skip, the five-point interaction budget, a design record with
the roll's seed, and the coverage-reconciliation comment (0 unaccounted).

Run A: light teal / duotone-graphic / grotesk-editorial / bento-mosaic /
       minimal-fade / sticky-figure-scrollytelling
Run B: dark cyan-slate / high-contrast-editorial / mono-technical /
       offset-column-rhythm / crisp-instant / filterable-grid

`?static=1` pre-reveals all content (a documented QA hook used only for
headless screenshots). Outputs are committed evidence (v3.9 precedent).
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = HERE.parent / "fixtures" / "models" / "deck_pdf_enriched.json"

CATEGORIES = ["Q1", "Q2", "Q3", "Q4"]
VALUES = [120.0, 135.0, 150.0, 170.0]

WORKSHEET = """FIGURE WORKSHEET - deck.pdf page 2, "Figure 1: Revenue by quarter (USD millions)"
Chart family:        bar (single series)
Title (as printed):  not printed inside the figure (page heading: Revenue by Quarter)
X axis:              categorical: Q1, Q2, Q3, Q4
Y axis:              unlabeled in figure; unit from caption = USD millions; ticks 0, 50, 100, 150; scale: linear
Gridlines / ticks:   0, 50, 100, 150
Legend:              none (single blue series)
Series readings:     Q1 -> 120; Q2 -> 135; Q3 -> 150 (on the 150 tick); Q4 -> 170 (0.4 tick-spacings above 150)
Estimated precision: read to the nearest 5 against gridlines
Footnotes/source:    caption "Figure 1: Revenue by quarter (USD millions)"
Anomalies:           topmost value sits above the last labeled tick (axis line continues); otherwise none"""

RECONCILIATION = """COVERAGE RECONCILIATION - deck.pdf
manifest: images found 8 / kept 4 / skipped 4; native charts 0;
          vector regions rasterized 2 / skipped 0; scanned pages 0
- [skipped]       image page 1 "logo" - decorative (repeated-asset: on 5 pages, kept once; no content value)
- [reconstructed] chart from image page 2 "Figure 1: Revenue by quarter (USD millions)"
                  (confidence medium, worksheet comment adjacent, view-original toggle + original alongside)
- [rendered]      image page 3 "Figure 2: Site enrollment map" (map - enhanced original, lightbox)
- [rendered]      image page 4 "Photo: Team offsite, June 2026" (photo, lightbox)
verdict: ACCOUNTED - 0 unaccounted"""

# Shared interaction core: lightbox (pan/zoom/trap), reveals, nav tracking,
# progress, and the interactive bar-chart controller (wheel y-zoom, y-range
# inputs, legend toggle, hover/focus readout, reset). Same functional core in
# both runs; the DESIGN diverges per brief.
SHARED_JS = """
document.documentElement.classList.add('js');
var motionOK = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (location.search.indexOf('static') > -1) {
  document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('revealed'); });
  motionOK = false;
} else {
  var ro = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('revealed'); ro.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(function (el) { ro.observe(el); });
}
var navLinks = {};
document.querySelectorAll('nav.site a[href^="#"]').forEach(function (a) {
  navLinks[a.getAttribute('href').slice(1)] = a;
});
var no = new IntersectionObserver(function (es) {
  es.forEach(function (e) {
    if (e.isIntersecting) {
      Object.keys(navLinks).forEach(function (k) { navLinks[k].removeAttribute('aria-current'); });
      if (navLinks[e.target.id]) { navLinks[e.target.id].setAttribute('aria-current', 'true'); }
    }
  });
}, { rootMargin: '-35% 0px -55% 0px' });
document.querySelectorAll('section[id]').forEach(function (s) { no.observe(s); });
var bar = document.getElementById('progress');
if (bar) {
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
}

// Lightbox (shared with the view-original toggle).
var lb = document.getElementById('lightbox');
var lbImg = lb.querySelector('img');
var opener = null, scale = 1, tx = 0, ty = 0, dragging = false, dx = 0, dy = 0;
function lbApply() { lbImg.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')'; }
function lbOpen(btn, src, alt) {
  opener = btn; lbImg.src = src; lbImg.alt = alt || '';
  scale = 1; tx = ty = 0; lbApply();
  lb.classList.add('open'); lb.querySelector('button.close').focus();
}
function lbClose() { lb.classList.remove('open'); if (opener) { opener.focus(); opener = null; } }
document.querySelectorAll('button.imgbtn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var img = btn.querySelector('img');
    lbOpen(btn, btn.getAttribute('data-full') || img.src, img.alt);
  });
});
lb.querySelector('button.close').addEventListener('click', lbClose);
lb.querySelector('button.reset').addEventListener('click', function () { scale = 1; tx = ty = 0; lbApply(); });
lb.addEventListener('click', function (e) { if (e.target === lb) { lbClose(); } });
lb.addEventListener('wheel', function (e) {
  e.preventDefault();
  scale = Math.min(8, Math.max(0.4, scale * (e.deltaY < 0 ? 1.15 : 0.87)));
  lbApply();
}, { passive: false });
lbImg.addEventListener('pointerdown', function (e) {
  dragging = true; dx = e.clientX - tx; dy = e.clientY - ty; lbImg.setPointerCapture(e.pointerId);
});
lbImg.addEventListener('pointermove', function (e) {
  if (dragging) { tx = e.clientX - dx; ty = e.clientY - dy; lbApply(); }
});
lbImg.addEventListener('pointerup', function () { dragging = false; });
document.addEventListener('keydown', function (e) {
  if (!lb.classList.contains('open')) { return; }
  if (e.key === 'Escape') { lbClose(); }
  if (e.key === 'Tab') {
    var f = lb.querySelectorAll('button');
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  }
});

// Interactive reconstructed chart: canvas bars + zoom/pan-range/toggle/readout.
function barChart(canvasId, opts) {
  var canvas = document.getElementById(canvasId);
  var readout = document.getElementById(canvasId + '-readout');
  var state = { yMin: 0, yMax: opts.yMax, hidden: false, highlight: -1 };
  var dpr = window.devicePixelRatio || 1;
  function draw() {
    var w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    var g = canvas.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    var padL = 46, padB = 26, padT = 12;
    var plotW = w - padL - 10, plotH = h - padT - padB;
    g.strokeStyle = opts.grid; g.fillStyle = opts.text;
    g.font = '11px ' + opts.font; g.textAlign = 'right'; g.lineWidth = 1;
    var span = state.yMax - state.yMin;
    var step = span > 250 ? 100 : 50;
    for (var v = Math.ceil(state.yMin / step) * step; v <= state.yMax; v += step) {
      var y = padT + plotH - ((v - state.yMin) / span) * plotH;
      g.globalAlpha = 0.5; g.beginPath(); g.moveTo(padL, y); g.lineTo(w - 10, y); g.stroke();
      g.globalAlpha = 1; g.fillText(String(v), padL - 6, y + 4);
    }
    g.textAlign = 'center';
    var n = opts.categories.length, slot = plotW / n, bw = Math.min(64, slot * 0.55);
    for (var i = 0; i < n; i++) {
      var x = padL + slot * i + slot / 2;
      g.fillStyle = opts.text;
      g.fillText(opts.categories[i], x, h - 8);
      if (state.hidden) { continue; }
      var clamped = Math.max(state.yMin, Math.min(opts.values[i], state.yMax));
      var bh = ((clamped - state.yMin) / span) * plotH;
      g.fillStyle = state.highlight === i ? opts.accent2 : opts.accent;
      g.fillRect(x - bw / 2, padT + plotH - bh, bw, bh);
    }
  }
  function bandFor(evX) {
    var rect = canvas.getBoundingClientRect();
    var slot = (canvas.clientWidth - 56) / opts.categories.length;
    var index = Math.floor((evX - rect.left - 46) / slot);
    return index >= 0 && index < opts.categories.length ? index : -1;
  }
  canvas.addEventListener('mousemove', function (e) {
    var index = bandFor(e.clientX);
    state.highlight = index;
    readout.textContent = index < 0 || state.hidden
      ? opts.idle
      : opts.categories[index] + ': ' + opts.values[index] + ' ' + opts.unit;
    draw();
  });
  canvas.addEventListener('mouseleave', function () {
    state.highlight = -1; readout.textContent = opts.idle; draw();
  });
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    state.yMax = Math.round(Math.min(400, Math.max(80, state.yMax * (e.deltaY < 0 ? 0.9 : 1.1))));
    document.getElementById(canvasId + '-ymax').value = state.yMax;
    draw();
  }, { passive: false });
  document.getElementById(canvasId + '-ymax').addEventListener('change', function () {
    state.yMax = Math.min(400, Math.max(state.yMin + 10, parseInt(this.value, 10) || opts.yMax));
    this.value = state.yMax; draw();
  });
  document.getElementById(canvasId + '-ymin').addEventListener('change', function () {
    state.yMin = Math.max(0, Math.min(state.yMax - 10, parseInt(this.value, 10) || 0));
    this.value = state.yMin; draw();
  });
  var legend = document.getElementById(canvasId + '-legend');
  legend.addEventListener('click', function () {
    state.hidden = !state.hidden;
    legend.setAttribute('aria-pressed', state.hidden ? 'false' : 'true');
    legend.classList.toggle('off', state.hidden);
    draw();
  });
  document.getElementById(canvasId + '-reset').addEventListener('click', function () {
    state.yMin = 0; state.yMax = opts.yMax; state.hidden = false; state.highlight = -1;
    document.getElementById(canvasId + '-ymin').value = 0;
    document.getElementById(canvasId + '-ymax').value = opts.yMax;
    legend.setAttribute('aria-pressed', 'true'); legend.classList.remove('off');
    readout.textContent = opts.idle; draw();
  });
  window.addEventListener('resize', draw);
  window.__charts = window.__charts || {};
  window.__charts[canvasId] = { state: state, draw: draw };
  draw();
}
"""

SCROLLY_JS = """
// Signature move (run A): sticky-figure scrollytelling - steps highlight bars.
(function () {
  var steps = document.querySelectorAll('.scrolly-step');
  if (!steps.length) { return; }
  var chart = window.__charts['revchart'];
  var so = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) { return; }
      steps.forEach(function (s) { s.classList.remove('active'); });
      e.target.classList.add('active');
      chart.state.highlight = parseInt(e.target.getAttribute('data-bar'), 10);
      chart.draw();
    });
  }, { rootMargin: '-45% 0px -45% 0px' });
  steps.forEach(function (s) { so.observe(s); });
})();
"""

FILTER_JS = """
// Signature move (run B): chip-filterable exhibit grid.
(function () {
  var chips = document.querySelectorAll('.chip');
  var items = document.querySelectorAll('.exhibit');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.setAttribute('aria-pressed', 'false'); });
      chip.setAttribute('aria-pressed', 'true');
      var kind = chip.getAttribute('data-filter');
      items.forEach(function (item) {
        item.hidden = kind !== 'all' && item.getAttribute('data-kind') !== kind;
      });
    });
  });
})();
"""


def chart_panel(font: str, idle: str) -> str:
    """The reconstructed-chart panel markup shared by both runs."""
    return f"""
<div class="chartwrap">
  <div class="chartmeta">
    <span class="badge">reconstructed from source figure - confidence: medium</span>
    <span class="precision">Values read from the source figure to the nearest 5 (USD millions).</span>
  </div>
  <canvas id="revchart" role="img" aria-label="Revenue by quarter, reconstructed bar chart: Q1 120, Q2 135, Q3 150, Q4 170 USD millions" height="300"></canvas>
  <div class="chartctl">
    <button id="revchart-legend" type="button" aria-pressed="true" class="legendbtn"><span class="swatch"></span>Revenue</button>
    <label>y-min <input id="revchart-ymin" type="number" value="0" min="0" step="10"></label>
    <label>y-max <input id="revchart-ymax" type="number" value="200" min="80" step="10"></label>
    <button id="revchart-reset" type="button">Reset</button>
    <span id="revchart-readout" class="readout" aria-live="polite">{idle}</span>
  </div>
</div>"""


def original_figure(img: dict, extra_class: str = "") -> str:
    caption = img.get("caption") or ""
    suffix = f" - {caption}" if caption else ""
    return (
        f'<figure class="original {extra_class}">'
        f'<button class="imgbtn" type="button" aria-label="Open the original source figure in the zoom viewer">'
        f'<img src="{img["data_uri"]}" alt="{img["alt"]}"></button>'
        f"<figcaption>Original source figure (view/zoom){suffix}"
        f"</figcaption></figure>"
    )


def lightbox_html() -> str:
    return (
        '<div id="lightbox" role="dialog" aria-modal="true" aria-label="Image viewer">'
        '<div class="bar"><button type="button" class="reset">Reset view</button>'
        '<button type="button" class="close">Close</button></div>'
        '<img src="" alt=""></div>'
    )


def load_images() -> dict:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    images: dict = {}
    for section in model["sections"]:
        for block in section["blocks"]:
            if block["type"] == "image":
                key = f"{block.get('origin')}-p{block.get('page')}"
                images[key] = block
    return images


def build_run_a(images: dict, brief: dict) -> str:
    chart_img = images["rasterized-region-p2"]
    map_img = images["rasterized-region-p3"]
    photo = images["embedded-raster-p4"]
    css = """
:root { --base:#f2f8f8; --surface:#dcebeb; --ink:#173033; --accent:#2a7f83; --accent2:#b6534e; }
* { box-sizing:border-box; } html { scroll-behavior:smooth; }
body { margin:0; background:var(--base); color:var(--ink); font:16px/1.55 Arial,'Helvetica Neue','Segoe UI',sans-serif; }
h1,h2,h3 { font-family:'Arial Black','Segoe UI','Helvetica Neue',sans-serif; letter-spacing:-.02em; }
#progress { position:fixed; top:0; left:0; height:4px; background:var(--accent2); width:0; z-index:9; }
nav.site { position:sticky; top:0; z-index:5; background:var(--surface); padding:.55rem 4vw; display:flex; gap:1.3rem; border-bottom:2px solid var(--accent); }
nav.site a { color:var(--ink); text-decoration:none; font-weight:700; font-size:.82rem; text-transform:uppercase; padding:.15rem 0; border-bottom:3px solid transparent; }
nav.site a[aria-current="true"] { border-bottom-color:var(--accent2); color:var(--accent2); }
nav.site a:hover, nav.site a:focus-visible { border-bottom-color:var(--accent); }
header.hero { padding:4.5rem 4vw 2.5rem; background:linear-gradient(120deg,var(--surface) 55%,var(--base) 55%); }
header.hero h1 { font-size:3.1rem; margin:0; color:var(--accent); }
header.hero p { max-width:38rem; }
.mosaic { display:grid; grid-template-columns:repeat(6,1fr); gap:14px; padding:2rem 4vw; }
.tile { background:#fff; border:2px solid var(--surface); padding:1.1rem 1.3rem; transition:transform .3s ease, border-color .3s ease; }
.tile:hover, .tile:focus-within { transform:translateY(-3px); border-color:var(--accent); }
.tile.big { grid-column:span 4; } .tile.mid { grid-column:span 3; } .tile.small { grid-column:span 2; }
.tile.stat .n { font-size:2.4rem; font-family:'Arial Black',sans-serif; color:var(--accent); }
section { padding:2.6rem 4vw; }
.js .reveal { opacity:0; transform:none; transition:opacity .6s ease; }
.js .reveal.revealed { opacity:1; }
.scrolly { display:grid; grid-template-columns:minmax(300px,3fr) 2fr; gap:2rem; align-items:start; }
.scrolly .sticky { position:sticky; top:70px; }
.scrolly-step { min-height:38vh; padding:1rem 1.2rem; border-left:5px solid var(--surface); margin:0 0 1rem; transition:border-color .3s ease, background .3s ease; }
.scrolly-step.active { border-left-color:var(--accent2); background:var(--surface); }
.chartwrap { background:#fff; border:2px solid var(--surface); padding:1rem; }
canvas#revchart { width:100%; height:300px; display:block; cursor:crosshair; }
.badge { display:inline-block; background:var(--accent); color:#fff; font-size:.7rem; font-weight:700; text-transform:uppercase; padding:.2rem .55rem; }
.precision { display:block; font-size:.8rem; opacity:.8; margin:.3rem 0 .6rem; }
.chartctl { display:flex; flex-wrap:wrap; gap:.7rem; align-items:center; margin-top:.6rem; font-size:.85rem; }
.chartctl input { width:4.5rem; padding:.15rem .3rem; border:1px solid var(--surface); }
.chartctl button { border:2px solid var(--accent); background:#fff; padding:.3rem .7rem; cursor:pointer; font-weight:700; }
.chartctl button:hover, .chartctl button:focus-visible { background:var(--accent); color:#fff; }
.legendbtn .swatch { display:inline-block; width:.75rem; height:.75rem; background:var(--accent); margin-right:.35rem; }
.legendbtn.off { opacity:.45; text-decoration:line-through; }
.readout { font-weight:700; color:var(--accent2); min-width:11rem; }
button.imgbtn { border:2px solid var(--surface); background:none; padding:0; cursor:zoom-in; display:block; max-width:100%; transition:border-color .3s ease; }
button.imgbtn:hover, button.imgbtn:focus-visible { border-color:var(--accent2); outline:none; }
button.imgbtn img { display:block; width:100%; height:auto; }
figure.original { margin:1rem 0 0; max-width:24rem; font-size:.8rem; }
#lightbox { position:fixed; inset:0; background:rgba(13,32,35,.92); display:none; align-items:center; justify-content:center; z-index:20; }
#lightbox.open { display:flex; }
#lightbox img { max-width:92vw; max-height:88vh; cursor:grab; transform-origin:0 0; }
#lightbox .bar { position:absolute; top:.8rem; right:1rem; display:flex; gap:.6rem; }
#lightbox button { background:var(--surface); border:0; padding:.5rem .9rem; font-weight:700; cursor:pointer; }
#lightbox button:focus-visible { outline:3px solid var(--accent2); }
tbody tr:hover, tbody tr:focus-within { background:var(--surface); }
@media (prefers-reduced-motion: reduce) {
  .js .reveal { opacity:1; transition:none; }
  .tile, .scrolly-step, button.imgbtn { transition:none; }
  html { scroll-behavior:auto !important; }
}
@media (max-width: 820px) { .mosaic { grid-template-columns:1fr 1fr; } .tile.big,.tile.mid,.tile.small { grid-column:span 2; } .scrolly { grid-template-columns:1fr; } .scrolly .sticky { position:static; } }
"""
    steps = "".join(
        f'<div class="scrolly-step" data-bar="{i}"><h3>{c}: {int(v)}M</h3>'
        f"<p>{text}</p></div>"
        for i, (c, v, text) in enumerate(
            zip(
                CATEGORIES,
                VALUES,
                [
                    "The year opened at 120 (all figures read from the source chart to the nearest 5).",
                    "Q2 added 15 on Q1 as the second site came online.",
                    "Q3 reached the 150 gridline exactly - the strongest single-quarter climb.",
                    "Q4 closed at 170, above the last labeled tick on the source axis.",
                ],
            )
        )
    )
    return f"""<!DOCTYPE html>
<!-- DESIGN RECORD (run A)
{brief["summary"]}
palette base {brief["palette"]["base"]} / surface {brief["palette"]["surface"]} / ink {brief["palette"]["ink"]} / accents {brief["palette"]["accent"]}, {brief["palette"]["accent_2"]}
type: grotesk-editorial (Arial Black / Arial); layout: bento-mosaic; motion: minimal-fade; move: sticky-figure-scrollytelling
-->
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nexus Board Review - run A</title><style>{css}</style></head>
<body>
<div id="progress" aria-hidden="true"></div>
<nav class="site" aria-label="Sections"><a href="#overview">Overview</a><a href="#revenue">Revenue</a><a href="#map">Enrollment</a><a href="#team">Team</a><a href="#summary">Summary</a></nav>
<header class="hero" id="overview"><h1>Nexus Board Review</h1>
<p>Fiscal year 2026 highlights, rebuilt from the source deck as an interactive site. Revenue figures are faithfully reconstructed from the source chart; the original is one click away everywhere.</p></header>
<div class="mosaic">
  <div class="tile big stat reveal" tabindex="0"><div class="n">170</div><div>Q4 revenue (USD millions, read from the source figure)</div></div>
  <div class="tile small stat reveal" tabindex="0"><div class="n">4</div><div>enrollment sites on the map</div></div>
  <div class="tile mid reveal" tabindex="0"><h3>+50 over the year</h3><p>From 120 in Q1 to 170 in Q4 - the growth story the deck leads with.</p></div>
  <div class="tile mid reveal" tabindex="0"><h3>January</h3><p>Next review scheduled; targets carried forward.</p></div>
</div>
<section id="revenue"><h2 class="reveal">Revenue by Quarter</h2>
<div class="scrolly">
  <div class="sticky reveal">{chart_panel("Arial", "hover or scroll the steps")}
  {original_figure(chart_img)}</div>
  <div>{steps}</div>
</div></section>
<section id="map"><h2 class="reveal">Enrollment Map</h2>
<p class="reveal">The source map is a vector graphic with unlabeled site markers; it is presented as the enhanced original (zoomable) rather than a lossy redraw.</p>
<div class="reveal" style="max-width:40rem">{original_figure(map_img)}</div></section>
<section id="team"><h2 class="reveal">Team</h2>
<div class="reveal" style="max-width:30rem">{original_figure(photo)}</div></section>
<section id="summary"><h2 class="reveal">Summary</h2>
<ul class="reveal"><li>Revenue reached 170 in Q4.</li><li>Enrollment expanded to four sites.</li><li>Next review scheduled for January.</li></ul>
<p class="reveal" style="font-size:.8rem;opacity:.75">The repeated page logo was classified decorative and omitted (see the coverage reconciliation in the page source).</p></section>
{lightbox_html()}
<script>{SHARED_JS}
barChart('revchart', {{ categories: {json.dumps(CATEGORIES)}, values: {json.dumps(VALUES)}, yMax: 200, unit: 'USD M', idle: 'hover or scroll the steps', accent: '#2a7f83', accent2: '#b6534e', grid: '#9dbcbc', text: '#173033', font: 'Arial' }});
{SCROLLY_JS}</script>
<!-- {WORKSHEET} -->
<!-- {RECONCILIATION} -->
</body></html>"""


def build_run_b(images: dict, brief: dict) -> str:
    chart_img = images["rasterized-region-p2"]
    map_img = images["rasterized-region-p3"]
    photo = images["embedded-raster-p4"]
    css = """
:root { --base:#14202a; --surface:#1d2e3a; --ink:#e4edf3; --accent:#3a7ca5; --accent2:#c47f3d; }
* { box-sizing:border-box; } html { scroll-behavior:smooth; }
body { margin:0; background:var(--base); color:var(--ink); font:16px/1.6 Arial,'Helvetica Neue','Segoe UI',sans-serif; }
h1,h2,h3,.mono { font-family:Consolas,'Cascadia Code','SF Mono',Menlo,monospace; }
#progress { position:fixed; top:0; left:0; height:3px; background:var(--accent2); width:0; z-index:9; }
nav.site { position:sticky; top:0; z-index:5; background:var(--base); border-bottom:1px solid var(--accent); padding:.6rem 5vw; display:flex; gap:1.6rem; }
nav.site a { color:var(--ink); text-decoration:none; font-family:Consolas,monospace; font-size:.85rem; padding:.1rem 0; border-bottom:2px solid transparent; }
nav.site a[aria-current="true"] { color:var(--accent2); border-bottom-color:var(--accent2); }
nav.site a:hover, nav.site a:focus-visible { border-bottom-color:var(--accent); }
header.hero { padding:5rem 5vw 3rem; border-bottom:1px solid var(--surface); }
header.hero h1 { font-size:2.7rem; margin:0 0 .4rem; }
header.hero h1::before { content:'// '; color:var(--accent2); }
.offset { display:grid; grid-template-columns:1fr 1fr; gap:3rem; padding:3rem 5vw; border-bottom:1px solid var(--surface); align-items:start; }
.offset:nth-of-type(even) .lead { order:2; }
section { border-bottom:1px solid var(--surface); }
.js .reveal { opacity:0; transform:translateX(-10px); transition:opacity .18s linear, transform .18s linear; }
.js .reveal.revealed { opacity:1; transform:none; }
.chartwrap { background:var(--surface); padding:1rem; border-top:3px solid var(--accent2); }
canvas#revchart { width:100%; height:300px; display:block; cursor:crosshair; }
.badge { display:inline-block; border:1px solid var(--accent2); color:var(--accent2); font-family:Consolas,monospace; font-size:.68rem; padding:.15rem .5rem; }
.precision { display:block; font-size:.8rem; opacity:.75; margin:.35rem 0 .6rem; }
.chartctl { display:flex; flex-wrap:wrap; gap:.7rem; align-items:center; margin-top:.6rem; font-size:.85rem; }
.chartctl input { width:4.5rem; background:var(--base); color:var(--ink); border:1px solid var(--accent); padding:.15rem .3rem; }
.chartctl button { border:1px solid var(--accent); background:transparent; color:var(--ink); padding:.3rem .7rem; cursor:pointer; font-family:Consolas,monospace; }
.chartctl button:hover, .chartctl button:focus-visible { background:var(--accent); color:#fff; }
.legendbtn .swatch { display:inline-block; width:.75rem; height:.75rem; background:var(--accent); margin-right:.35rem; }
.legendbtn.off { opacity:.45; text-decoration:line-through; }
.readout { font-family:Consolas,monospace; color:var(--accent2); min-width:11rem; }
.chips { display:flex; gap:.6rem; margin:1rem 0; }
.chip { border:1px solid var(--accent); background:transparent; color:var(--ink); font-family:Consolas,monospace; padding:.3rem .8rem; cursor:pointer; }
.chip[aria-pressed="true"] { background:var(--accent2); border-color:var(--accent2); color:#14202a; }
.chip:hover, .chip:focus-visible { border-color:var(--accent2); }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1rem; padding:0 5vw 3rem; }
.exhibit { background:var(--surface); padding:1rem; transition:outline-color .12s linear; outline:1px solid transparent; }
.exhibit:hover, .exhibit:focus-within { outline-color:var(--accent2); }
.exhibit .k { font-family:Consolas,monospace; font-size:.7rem; color:var(--accent2); text-transform:uppercase; }
.exhibit .n { font-size:2rem; font-family:Consolas,monospace; color:var(--accent); }
button.imgbtn { border:1px solid var(--accent); background:none; padding:0; cursor:zoom-in; display:block; max-width:100%; transition:outline-color .12s linear; outline:2px solid transparent; }
button.imgbtn:hover, button.imgbtn:focus-visible { outline-color:var(--accent2); }
button.imgbtn img { display:block; width:100%; height:auto; }
figure.original { margin:1rem 0 0; font-size:.8rem; }
#lightbox { position:fixed; inset:0; background:rgba(6,12,17,.94); display:none; align-items:center; justify-content:center; z-index:20; }
#lightbox.open { display:flex; }
#lightbox img { max-width:92vw; max-height:88vh; cursor:grab; transform-origin:0 0; }
#lightbox .bar { position:absolute; top:.8rem; right:1rem; display:flex; gap:.6rem; }
#lightbox button { background:var(--surface); color:var(--ink); border:1px solid var(--accent); padding:.5rem .9rem; cursor:pointer; font-family:Consolas,monospace; }
#lightbox button:focus-visible { outline:2px solid var(--accent2); }
@media (prefers-reduced-motion: reduce) {
  .js .reveal { opacity:1; transform:none; transition:none; }
  .exhibit, button.imgbtn, .chip { transition:none; }
  html { scroll-behavior:auto !important; }
}
@media (max-width: 820px) { .offset { grid-template-columns:1fr; } .offset:nth-of-type(even) .lead { order:0; } }
"""
    return f"""<!DOCTYPE html>
<!-- DESIGN RECORD (run B)
{brief["summary"]}
palette base {brief["palette"]["base"]} / surface {brief["palette"]["surface"]} / ink {brief["palette"]["ink"]} / accents {brief["palette"]["accent"]}, {brief["palette"]["accent_2"]}
type: mono-technical (Consolas headings / Arial body); layout: offset-column-rhythm; motion: crisp-instant; move: filterable-grid
-->
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nexus Board Review - run B</title><style>{css}</style></head>
<body>
<div id="progress" aria-hidden="true"></div>
<nav class="site" aria-label="Sections"><a href="#overview">overview</a><a href="#revenue">revenue</a><a href="#exhibits">exhibits</a><a href="#summary">summary</a></nav>
<header class="hero" id="overview"><h1>Nexus Board Review</h1>
<p class="mono" style="color:var(--accent2)">fiscal year 2026 / interactive rebuild / originals one click away</p>
<p style="max-width:44rem">The source deck's chart is reconstructed with audited values; the map and photo ship as zoomable originals; the repeated logo was classified decorative and omitted (reconciliation in the page source).</p></header>
<section class="offset" id="revenue">
  <div class="lead reveal"><h2>Revenue by Quarter</h2>
  <p>Read from the source figure against its 0/50/100/150 gridlines, to the nearest 5: 120, 135, 150, 170 (USD millions). Wheel-zoom the axis, drag the range inputs, toggle the series, hover for a readout.</p>
  {original_figure(chart_img)}</div>
  <div class="reveal">{chart_panel("Consolas", "hover a bar")}</div>
</section>
<section class="offset" id="exhibits-intro">
  <div class="lead reveal"><h2 id="exhibits">Exhibits</h2>
  <p>Filter the record: reconstructed data, source figures, and the numbers the deck closes on.</p>
  <div class="chips" role="group" aria-label="Filter exhibits">
    <button class="chip" type="button" data-filter="all" aria-pressed="true">all</button>
    <button class="chip" type="button" data-filter="figure" aria-pressed="false">figures</button>
    <button class="chip" type="button" data-filter="stat" aria-pressed="false">stats</button>
  </div></div>
  <div class="reveal"><p class="mono" style="opacity:.7">4 exhibits / 2 figures / 2 stats</p></div>
</section>
<div class="grid">
  <div class="exhibit reveal" data-kind="figure" tabindex="0"><span class="k">figure / map</span>{original_figure(map_img)}</div>
  <div class="exhibit reveal" data-kind="figure" tabindex="0"><span class="k">figure / photo</span>{original_figure(photo)}</div>
  <div class="exhibit reveal" data-kind="stat" tabindex="0"><span class="k">stat / revenue</span><div class="n">170</div><p>Q4 close (USD millions, reconstructed reading).</p></div>
  <div class="exhibit reveal" data-kind="stat" tabindex="0"><span class="k">stat / growth</span><div class="n">+50</div><p>Q1 to Q4 delta across the year.</p></div>
</div>
<section class="offset" id="summary">
  <div class="lead reveal"><h2>Summary</h2>
  <ul><li>Revenue reached 170 in Q4.</li><li>Enrollment expanded to four sites.</li><li>Next review scheduled for January.</li></ul></div>
  <div class="reveal"><p class="mono" style="opacity:.7">// end of record</p></div>
</section>
{lightbox_html()}
<script>{SHARED_JS}
barChart('revchart', {{ categories: {json.dumps(CATEGORIES)}, values: {json.dumps(VALUES)}, yMax: 200, unit: 'USD M', idle: 'hover a bar', accent: '#3a7ca5', accent2: '#c47f3d', grid: '#33506b', text: '#e4edf3', font: 'Consolas' }});
{FILTER_JS}</script>
<!-- {WORKSHEET} -->
<!-- {RECONCILIATION} -->
</body></html>"""


def main() -> int:
    images = load_images()
    brief_a = json.loads((HERE / "brief-a.json").read_text(encoding="utf-8"))
    brief_b = json.loads((HERE / "brief-b.json").read_text(encoding="utf-8"))
    (HERE / "run-a.html").write_text(build_run_a(images, brief_a), encoding="utf-8")
    (HERE / "run-b.html").write_text(build_run_b(images, brief_b), encoding="utf-8")
    for name in ("run-a.html", "run-b.html"):
        print(f"Wrote {name} ({(HERE / name).stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
