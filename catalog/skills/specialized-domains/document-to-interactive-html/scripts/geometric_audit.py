#!/usr/bin/env python3
"""Audit rendered figure geometry for the six mechanically-detectable defects.

Everything here measures SCREEN space. The first version of this audit in the
source project used `getBBox`, which ignores transforms, and it reported every
rotated y-axis title as clipped - roughly 220 findings for one real defect. A
measurement that disagrees with the screen is not a measurement.

Two false-positive defences are load-bearing and both came from real noise:

- A rotated axis title sits outside its own untransformed box but inside the
  viewport once the transform is applied, so clipping is judged from
  `getBoundingClientRect` and the SVG's own on-screen rect.
- A label beside a wiggly trace is inside that trace's bounding box almost
  always, because the bounding box of a wiggly line is the whole panel. Ink is
  what matters, so the trace is sampled with `getPointAtLength` and the label
  is reported only when it covers a sampled point.

Geometry clipped away by an ancestor is never visible, so `clip-path` and
scroll clipping are intersected before anything is judged.

An unavailable renderer reports `unverified` with the exact error. It never
reports a pass it could not establish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXIT_PASS = 0
EXIT_FINDINGS = 1
EXIT_UNVERIFIED = 2

CHECKS = (
    "clipped-text",
    "label-overlap",
    "label-on-trace",
    "legend-colour-collision",
    "oversized-type",
    "stroke-drift",
)

# Sampling density along a trace. 240 points resolves a label-sized gap on a
# full-width panel; the cost is a few milliseconds per path.
TRACE_SAMPLES = 240

AUDIT = r"""(options) => {
  const SAMPLES = options.samples;
  // A check named here is skipped. This exists for the negative control: a
  // check that cannot be switched off cannot be shown to be the thing that
  // produced a finding, and an assertion nobody has watched fail is not
  // evidence. The test suite drives it; normal runs pass an empty list.
  const disabled = new Set(options.disabled || []);
  const findings = [];
  const add = (check, element, measurement, message) => {
    if (disabled.has(check)) return;
    findings.push({check, selector: selectorFor(element), measurement, message});
  };

  // A stable-enough selector for a report a human has to act on.
  const selectorFor = (el) => {
    if (!el) return "(detached)";
    if (el.id) return `#${CSS.escape(el.id)}`;
    const parts = [];
    let cur = el;
    while (cur && cur.nodeType === 1 && parts.length < 4) {
      let part = cur.tagName.toLowerCase();
      const parent = cur.parentElement;
      if (parent) {
        const sibs = [...parent.children].filter((c) => c.tagName === cur.tagName);
        if (sibs.length > 1) part += `:nth-of-type(${sibs.indexOf(cur) + 1})`;
      }
      parts.unshift(part);
      cur = cur.parentElement;
    }
    return parts.join(" > ");
  };

  const round = (n) => Math.round(n * 100) / 100;
  const rectOf = (el) => el.getBoundingClientRect();
  const area = (r) => Math.max(0, r.width) * Math.max(0, r.height);

  const intersect = (a, b) => ({
    left: Math.max(a.left, b.left),
    top: Math.max(a.top, b.top),
    right: Math.min(a.right, b.right),
    bottom: Math.min(a.bottom, b.bottom),
    get width() { return this.right - this.left; },
    get height() { return this.bottom - this.top; },
  });

  // Geometry an ancestor clipped away is not on screen, whatever the element's
  // own rect says. Phantom overlaps in the source project came from ignoring this.
  const visibleRect = (el) => {
    let box = rectOf(el);
    let cur = el.parentElement;
    while (cur && cur !== document.documentElement) {
      const style = getComputedStyle(cur);
      const clips =
        style.clipPath !== "none" ||
        style.overflow === "hidden" ||
        style.overflow === "clip" ||
        style.overflowX === "hidden" ||
        style.overflowY === "hidden";
      if (clips) {
        const c = intersect(box, rectOf(cur));
        if (c.width <= 0 || c.height <= 0) return null;
        box = {left: c.left, top: c.top, right: c.right, bottom: c.bottom,
               width: c.width, height: c.height};
      }
      cur = cur.parentElement;
    }
    return box;
  };

  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === "none" || s.visibility === "hidden") return false;
    return parseFloat(s.opacity || "1") > 0.05;
  };

  const svgs = [...document.querySelectorAll("svg")].filter(visible);

  // ---- 1. text outside its SVG viewport -----------------------------------
  // Screen space only. A rotated title is inside the viewport once its
  // transform applies, and must not be reported.
  for (const svg of svgs) {
    const frame = rectOf(svg);
    for (const text of svg.querySelectorAll("text")) {
      if (!visible(text) || !text.textContent.trim()) continue;
      // The RAW rect, deliberately. An SVG defaults to overflow:hidden, so
      // intersecting the text against the very viewport that clipped it is
      // circular and can never report anything. Clipping by an ancestor
      // OUTSIDE the svg is handled where it matters, in the overlap checks.
      const box = rectOf(text);
      if (!box || (!box.width && !box.height)) continue;
      const outLeft = frame.left - box.left;
      const outRight = box.right - frame.right;
      const outTop = frame.top - box.top;
      const outBottom = box.bottom - frame.bottom;
      const worst = Math.max(outLeft, outRight, outTop, outBottom);
      if (worst > 1) {
        add("clipped-text", text,
            {overflow_px: round(worst), text: text.textContent.trim().slice(0, 40)},
            `Text extends ${round(worst)}px outside its SVG viewport`);
      }
    }
  }

  // ---- 2. label overlapping label -----------------------------------------
  for (const svg of svgs) {
    const labels = [...svg.querySelectorAll("text")]
      .filter((t) => visible(t) && t.textContent.trim())
      .map((t) => ({el: t, box: visibleRect(t)}))
      .filter((l) => l.box);
    for (let i = 0; i < labels.length; i += 1) {
      for (let j = i + 1; j < labels.length; j += 1) {
        const a = labels[i], b = labels[j];
        const c = intersect(a.box, b.box);
        if (c.width > 1 && c.height > 1) {
          // Ratio against the smaller label: a graze at a corner is not a collision.
          const share = area(c) / Math.max(1, Math.min(area(a.box), area(b.box)));
          if (share > 0.08) {
            add("label-overlap", b.el,
                {overlap_px: round(area(c)), share: round(share),
                 other: selectorFor(a.el)},
                `Label overlaps ${selectorFor(a.el)} over ${Math.round(share * 100)}% of its area`);
          }
        }
      }
    }
  }

  // ---- 3. label sitting on a plotted trace --------------------------------
  // Sampled ink, never the bounding box: the box of a wiggly trace is the panel.
  for (const svg of svgs) {
    const ctm = svg.getScreenCTM();
    if (!ctm) continue;
    const traces = [...svg.querySelectorAll("path")].filter((p) => {
      if (!visible(p)) return false;
      const s = getComputedStyle(p);
      // A filled region is not a trace; a stroked open path is.
      return s.stroke && s.stroke !== "none" && typeof p.getPointAtLength === "function";
    });
    const labels = [...svg.querySelectorAll("text")]
      .filter((t) => visible(t) && t.textContent.trim())
      .map((t) => ({el: t, box: visibleRect(t)}))
      .filter((l) => l.box);
    if (!traces.length || !labels.length) continue;

    for (const trace of traces) {
      let total = 0;
      try { total = trace.getTotalLength(); } catch (e) { continue; }
      if (!total || !isFinite(total)) continue;
      const pts = [];
      for (let k = 0; k <= SAMPLES; k += 1) {
        let p;
        try { p = trace.getPointAtLength((total * k) / SAMPLES); } catch (e) { break; }
        const sp = p.matrixTransform(ctm);
        pts.push(sp);
      }
      if (!pts.length) continue;
      for (const label of labels) {
        const hits = pts.filter((p) =>
          p.x >= label.box.left && p.x <= label.box.right &&
          p.y >= label.box.top && p.y <= label.box.bottom).length;
        if (hits > 0) {
          add("label-on-trace", label.el,
              {sampled_points_covered: hits, samples: pts.length,
               trace: selectorFor(trace),
               text: label.el.textContent.trim().slice(0, 40)},
              `Label covers ${hits} sampled points of ${selectorFor(trace)}`);
        }
      }
    }
  }

  // ---- 4. two legend entries sharing one colour ---------------------------
  // Only meaningful where the legend keys by colour, which is the common case.
  const legendGroups = [...document.querySelectorAll(
    ".dv-legend, [data-dv-legend], .legend, [data-legend]")].filter(visible);
  for (const legend of legendGroups) {
    const seen = new Map();
    const entries = [...legend.querySelectorAll(
      "[data-legend-entry], button, li, .legend-entry")].filter(visible);
    for (const entry of entries) {
      // The swatch is whichever descendant actually paints a colour.
      const swatchEl = entry.querySelector("[data-swatch], svg *, .swatch") || entry;
      const s = getComputedStyle(swatchEl);
      const paint = [s.fill, s.backgroundColor, s.stroke, s.color].find(
        (v) => v && v !== "none" && !/rgba\(0, 0, 0, 0\)/.test(v));
      if (!paint) continue;
      const label = entry.textContent.trim().slice(0, 40);
      if (seen.has(paint)) {
        add("legend-colour-collision", entry,
            {colour: paint, other: seen.get(paint), label},
            `Legend entry "${label}" reuses ${paint}, already used by "${seen.get(paint)}"`);
      } else {
        seen.set(paint, label);
      }
    }
  }

  // ---- 5. type rendering far above the document scale ---------------------
  // Rendered size, not authored: an SVG scales its own font-size by the ratio
  // of its css width to its viewBox width.
  const bodySize = parseFloat(getComputedStyle(document.body).fontSize) || 16;
  const ceiling = bodySize * options.oversize_multiple;
  for (const svg of svgs) {
    const vb = svg.viewBox && svg.viewBox.baseVal;
    const frame = rectOf(svg);
    const ratio = vb && vb.width ? frame.width / vb.width : 1;
    for (const text of svg.querySelectorAll("text")) {
      if (!visible(text) || !text.textContent.trim()) continue;
      const authored = parseFloat(getComputedStyle(text).fontSize) || 0;
      const rendered = authored * ratio;
      if (rendered > ceiling) {
        add("oversized-type", text,
            {rendered_px: round(rendered), ceiling_px: round(ceiling),
             authored_px: round(authored), svg_ratio: round(ratio),
             text: text.textContent.trim().slice(0, 40)},
            `Type renders at ${round(rendered)}px against a ${round(ceiling)}px ceiling`);
      }
    }
  }

  // ---- 6. inconsistent stroke width across comparable traces --------------
  // Comparable means: stroked paths inside the same SVG carrying a data mark.
  for (const svg of svgs) {
    const marks = [...svg.querySelectorAll("path[data-dv-mark], path[data-mark], .dv-chart path")]
      .filter((p) => {
        if (!visible(p)) return false;
        const s = getComputedStyle(p);
        return s.stroke && s.stroke !== "none";
      });
    if (marks.length < 2) continue;
    const widths = new Map();
    for (const mark of marks) {
      const w = round(parseFloat(getComputedStyle(mark).strokeWidth) || 0);
      if (!w) continue;
      if (!widths.has(w)) widths.set(w, []);
      widths.get(w).push(mark);
    }
    if (widths.size > 1) {
      const sorted = [...widths.entries()].sort((a, b) => b[1].length - a[1].length);
      const [dominant] = sorted[0];
      for (const [w, els] of sorted.slice(1)) {
        for (const el of els) {
          add("stroke-drift", el,
              {stroke_width: w, dominant_width: dominant, distinct_widths: widths.size},
              `Stroke width ${w} differs from the dominant ${dominant} across comparable traces`);
        }
      }
    }
  }

  return {findings, svg_count: svgs.length};
}"""


def audit(
    html: Path,
    samples: int,
    oversize_multiple: float,
    disabled: list[str] | None = None,
) -> dict[str, Any]:
    """Render the page and run every check. Never claims a pass it cannot prove."""
    report: dict[str, Any] = {
        "status": "unverified",
        "source": str(html),
        "source_sha256": hashlib.sha256(html.read_bytes()).hexdigest(),
        "checks": list(CHECKS),
        "findings": [],
        "errors": [],
        "verification_scope": "rendered figure geometry in screen space",
    }
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        report["errors"].append(f"playwright is not installed: {exc}")
        return report

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            report["browser"] = "Chromium " + browser.version
            page = browser.new_page(viewport={"width": 1366, "height": 900})
            page.on("pageerror", lambda error: report["errors"].append(str(error)))

            def block(route):
                report["errors"].append("outbound request: " + route.request.url)
                route.abort()

            page.route("http**/*", block)
            page.goto(html.resolve().as_uri())
            page.evaluate("document.fonts.ready")
            result = page.evaluate(
                AUDIT,
                {
                    "samples": samples,
                    "oversize_multiple": oversize_multiple,
                    "disabled": disabled or [],
                },
            )
            browser.close()
    except Exception as exc:  # pragma: no cover - environment dependent
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        return report

    report["findings"] = result["findings"]
    report["svg_count"] = result["svg_count"]
    report["status"] = "fail" if result["findings"] else "pass"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="the rendered HTML file to audit")
    parser.add_argument("--samples", type=int, default=TRACE_SAMPLES,
                        help="points sampled along each trace")
    parser.add_argument("--oversize-multiple", type=float, default=3.0,
                        help="rendered type above this multiple of body size fails")
    parser.add_argument("--disable", action="append", default=[], choices=list(CHECKS),
                        help="skip a check; repeatable, for the negative control")
    parser.add_argument("--out", type=Path, help="write the JSON report here")
    args = parser.parse_args(argv)

    if not args.html.is_file():
        print(json.dumps({"status": "unverified",
                          "errors": [f"no such file: {args.html}"]}, indent=2))
        return EXIT_UNVERIFIED

    report = audit(args.html, args.samples, args.oversize_multiple, args.disable)
    text = json.dumps(report, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)

    if report["status"] == "unverified":
        return EXIT_UNVERIFIED
    return EXIT_FINDINGS if report["findings"] else EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
