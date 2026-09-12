#!/usr/bin/env python3
"""Measure every independently inventoried handbook section and slide offline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from typing import Any

VIEWPORTS = [
    (2560, 1300),
    (1920, 1080),
    (1366, 768),
    (390, 844),
    (1600, 900),
    (1024, 850),
    (1024, 851),
    (2560, 720),
    (760, 900),
    (761, 900),
]

# responsive-typography.md section 4 and svg-diagram-quality.md own these floors.
# A larger heading floor may be declared by the visual brief; it is not universal.
FONT_FLOORS = {"heading": 16, "body": 16, "label": 13, "interactive": 12}

MEASURE = r"""(root) => {
 const visible = e => e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
 const fonts=[], figures=[], clipped=[], contrast=[], overlaps=[], brand=[], deformed=[], faded=[];
 // Contrast is measured on RENDERED computed colors, never by pairing token
 // names. A block that redefines a custom property inside the same rule that
 // consumes it resolves at computed-value time, so a name-pairing check reads
 // the outer value and scores a dark-on-dark pair clean.
 const rgb = v => { const m=(v||'').match(/[\d.]+/g); return m ? [+m[0],+m[1],+m[2], m.length>3?+m[3]:1] : null; };
 const lum = c => { const f=x=>{x/=255;return x<=0.03928?x/12.92:Math.pow((x+0.055)/1.055,2.4)};
   return 0.2126*f(c[0])+0.7152*f(c[1])+0.0722*f(c[2]); };
 const ratio = (a,b) => { const l1=lum(a),l2=lum(b); return (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05); };
 // Walk ancestors for the first opaque painted background, as the compositor does.
 const backdrop = e => {
   for(let p=e;p;p=p.parentElement) {
     const c=rgb(getComputedStyle(p).backgroundColor);
     if(c && c[3]===1) return c;
   }
   const c=rgb(getComputedStyle(document.body).backgroundColor);
   return (c && c[3]===1) ? c : [255,255,255];
 };
 for(const e of root.querySelectorAll('h1,h2,h3,p,li,td,th,figcaption,svg text,label,button,a,input,select,textarea')) {
   if(!visible(e)) continue;
   const css=getComputedStyle(e); let scale=1;
   if(e instanceof SVGElement) {
     const m=e.getScreenCTM(); if(m) scale=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));
   } else {
     for(let p=e;p;p=p.parentElement) {
       const style=getComputedStyle(p),m=new DOMMatrix(style.transform==='none'?undefined:style.transform);
       scale*=Math.min(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d))*(parseFloat(style.zoom)||1);
     }
   }
   const role=e.matches('h1,h2,h3')?'heading':e.matches('button,a,input,select,textarea')?'interactive':e.matches('svg text,figcaption,label')?'label':'body';
   const px=parseFloat(css.fontSize)*scale;
   fonts.push({role,px,text:e.textContent.trim().slice(0,60)});
   const label=e.textContent.trim();
   if(label) {
     const ink=rgb(e instanceof SVGElement ? (css.fill!=='none'?css.fill:css.color) : css.color);
     if(ink && ink[3]>0.05) {
       // WCAG 1.4.3: 3.0 for large text (>=24px, or >=18.66px bold), else 4.5.
       const bold=(parseInt(css.fontWeight,10)||400)>=700;
       const floor=(px>=24||(bold&&px>=18.66))?3:4.5;
       const bg=backdrop(e);
       const value=ratio(ink,bg);
       if(value<floor) contrast.push({role,px:Math.round(px*10)/10,
         ink:ink.slice(0,3),background:bg.slice(0,3),
         ratio:Math.round(value*100)/100,floor,text:label.slice(0,60)});
     }
   }
   const r=e.getBoundingClientRect();
   for(let p=e.parentElement;p && root.contains(p);p=p.parentElement) {
     const s=getComputedStyle(p),b=p.getBoundingClientRect();
     if((/hidden|clip/.test(s.overflowX)&&(r.left<b.left-1||r.right>b.right+1)) ||
        (/hidden|clip/.test(s.overflowY)&&(r.top<b.top-1||r.bottom>b.bottom+1))) {
       clipped.push(e.textContent.trim().slice(0,60));break;
     }
   }
 }
 for(const e of root.querySelectorAll('figure,canvas,img')) if(visible(e)) {
   const b=e.getBoundingClientRect();figures.push({tag:e.tagName,width:b.width,height:b.height,area:b.width*b.height});
 }
 // A label sitting wholly inside a node box is correct labelling; a label
 // STRADDLING a filled shape's edge is a collision. Partial overlap is the
 // signal, so proper in-box labels never register. Arrowhead, viewport-fit and
 // marker-integrity checks never compare a label against a shape at all.
 for(const svg of root.querySelectorAll('svg')) {
   if(!visible(svg)) continue;
   const shapes=[...svg.querySelectorAll('rect,circle,ellipse,polygon')].filter(s=>{
     const f=getComputedStyle(s).fill;
     return f && f!=='none' && !/rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0\s*\)/.test(f);
   });
   for(const t of svg.querySelectorAll('text')) {
     if(!t.textContent.trim() || !visible(t)) continue;
     const a=t.getBoundingClientRect();
     if(!a.width || !a.height) continue;
     for(const s of shapes) {
       if(s.contains(t)) continue;
       const b=s.getBoundingClientRect();
       const ox=Math.min(a.right,b.right)-Math.max(a.left,b.left);
       const oy=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
       if(ox<=0.5||oy<=0.5) continue;                       // no meaningful overlap
       const inside=a.left>=b.left-0.5&&a.right<=b.right+0.5&&
                    a.top>=b.top-0.5&&a.bottom<=b.bottom+0.5;
       if(inside) continue;                                  // a proper in-box label
       const covered=(ox*oy)/(a.width*a.height);
       if(covered<0.08) continue;                            // a grazing touch
       overlaps.push({text:t.textContent.trim().slice(0,40),shape:s.tagName,
         covered:Math.round(covered*100)});
       break;
     }
   }
 }
 // A brand lockup carries meaning in its shapes, not in text, so the contrast
 // pass above cannot see it. brand_variants is keyed by the SURFACE theme, and
 // an author who reads the key as the artwork's own colour inverts every slide
 // and ships a wordmark that vanishes into the background.
 for(const mark of root.querySelectorAll('.dv-brand svg, header > svg')) {
   if(!visible(mark)) continue;
   const bg=backdrop(mark);
   for(const shape of mark.querySelectorAll('path,rect,polygon,circle,ellipse')) {
     const box=shape.getBoundingClientRect();
     if(box.width*box.height<16) continue;            // hairlines and registration marks
     const fill=rgb(getComputedStyle(shape).fill);
     if(!fill || fill[3]<0.5) continue;               // unfilled or near-transparent by intent
     const value=ratio(fill,bg);
     if(value<1.5) {                                  // effectively the background colour
       brand.push({ratio:Math.round(value*100)/100,fill:fill.slice(0,3),
         background:bg.slice(0,3),width:Math.round(box.width),height:Math.round(box.height)});
     }
   }
 }
 // Non-uniform scaling deforms a chart's marks, so a circle stops reading as a
 // point and a bar stops being comparable. Decorative artwork may stretch.
 for(const chart of root.querySelectorAll('.dv-chart svg,[data-dv-chart] svg,svg:has([data-dv-mark])')) {
   if(!visible(chart)) continue;
   if((chart.getAttribute('preserveAspectRatio')||'').trim().toLowerCase().startsWith('none'))
     deformed.push({marks:chart.querySelectorAll('[data-dv-mark]').length});
 }
 // Content already on screen must be readable at first paint. A scroll-driven
 // reveal that starts below full opacity ships its opening screen half-faded,
 // and the reader has nothing to scroll to trigger it.
 for(const e of root.querySelectorAll('h1,h2,h3,p,li,td,th,figcaption')) {
   if(!e.textContent.trim() || !visible(e)) continue;
   const box=e.getBoundingClientRect();
   if(box.bottom<=0 || box.top>=innerHeight) continue;   // not on the opening screen
   let alpha=1;
   for(let p=e;p;p=p.parentElement) alpha*=parseFloat(getComputedStyle(p).opacity)||1;
   if(alpha<0.95) faded.push({alpha:Math.round(alpha*100)/100,
     text:e.textContent.trim().slice(0,50)});
 }
 const b=root.getBoundingClientRect();
 return {fonts,figures,clipped,contrast,overlaps,brand,deformed,faded,width:root.clientWidth,scrollWidth:root.scrollWidth,
   height:root.clientHeight,scrollHeight:root.scrollHeight,visible:visible(root),
   theme:root.getAttribute('data-theme'),bounds:{x:b.x,y:b.y,width:b.width,height:b.height}};
}"""


# Chromium drops background painting for print unless print-color-adjust is
# exact, so a dark band prints WHITE while its light ink survives. The computed
# style still reports the declared dark background, which is why the rendered
# contrast pass above cannot see this: print emulation changes what is painted,
# not what is computed. This models the paint decision instead of reading the
# declaration, and runs under print emulation so an @media print palette remap
# has already been applied and legitimately passes.
PRINT_CONTRAST = r"""() => {
 const rgb = v => { const m=(v||'').match(/[\d.]+/g); return m ? [+m[0],+m[1],+m[2], m.length>3?+m[3]:1] : null; };
 const lum = c => { const f=x=>{x/=255;return x<=0.03928?x/12.92:Math.pow((x+0.055)/1.055,2.4)};
   return 0.2126*f(c[0])+0.7152*f(c[1])+0.0722*f(c[2]); };
 const ratio = (a,b) => { const l1=lum(a),l2=lum(b); return (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05); };
 const paints = e => {
   for(let p=e;p;p=p.parentElement) {
     const s=getComputedStyle(p);
     const adjust=s.printColorAdjust||s.webkitPrintColorAdjust||'';
     if(adjust.trim()==='exact') return true;
   }
   return false;
 };
 const PAPER=[255,255,255];
 const out=[];
 for(const e of document.querySelectorAll('h1,h2,h3,p,li,td,th,figcaption')) {
   const text=e.textContent.trim();
   if(!text || !e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})) continue;
   const css=getComputedStyle(e);
   const ink=rgb(css.color);
   if(!ink || ink[3]<0.05) continue;
   let declared=null, owner=null;
   for(let p=e;p;p=p.parentElement) {
     const c=rgb(getComputedStyle(p).backgroundColor);
     if(c && c[3]===1) { declared=c; owner=p; break; }
   }
   // A surface only reaches paper if the printer is told to paint it.
   const effective=(declared && paints(owner)) ? declared : PAPER;
   const px=parseFloat(css.fontSize)||16;
   const bold=(parseInt(css.fontWeight,10)||400)>=700;
   const floor=(px>=24||(bold&&px>=18.66))?3:4.5;
   const value=ratio(ink,effective);
   if(value<floor) out.push({ratio:Math.round(value*100)/100,floor,
     ink:ink.slice(0,3),declared:declared?declared.slice(0,3):null,
     printed:effective,text:text.slice(0,50)});
 }
 return out;
}"""

# A declaration is a request, not a fact. A rule that sets position sticky or
# fixed can lose the cascade to a later rule at equal specificity, and the
# element then computes static with nothing reporting it: the navigation simply
# stops following the reader. Only rules whose media condition currently matches
# are considered, so a breakpoint that deliberately does not stick is not a
# finding. If an override IS deliberate, remove the losing declaration rather
# than leaving a live rule that never applies.
DECLARED_POSITION = r"""() => {
 const wanted=new Set(['sticky','fixed']);
 const out=[];
 const seen=new Set();
 const walk = (rules, active) => {
   for(const rule of rules||[]) {
     if(rule.media) { walk(rule.cssRules, active && matchMedia(rule.media.mediaText).matches); continue; }
     if(rule.cssRules && !rule.selectorText) { walk(rule.cssRules, active); continue; }
     if(!active || !rule.selectorText || !rule.style) continue;
     const want=(rule.style.position||'').trim().toLowerCase();
     if(!wanted.has(want)) continue;
     let nodes=[];
     try { nodes=[...document.querySelectorAll(rule.selectorText)]; } catch(e) { continue; }
     for(const node of nodes) {
       if(!node.checkVisibility || !node.checkVisibility({checkVisibilityCSS:true})) continue;
       const got=getComputedStyle(node).position;
       if(got===want) continue;
       const key=rule.selectorText+'|'+want+'|'+got;
       if(seen.has(key)) continue;
       seen.add(key);
       out.push({selector:rule.selectorText.slice(0,70),declared:want,computed:got,
         tag:node.tagName.toLowerCase()});
     }
   }
 };
 for(const sheet of document.styleSheets) {
   try { walk(sheet.cssRules, true); } catch(e) { /* cross-origin sheet */ }
 }
 return out;
}"""

def measure(
    html: Path,
    inventory: dict[str, Any],
    detector_path: Path,
    viewports: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "status": "unverified",
        "output_sha256": hashlib.sha256(html.read_bytes()).hexdigest(),
        "rows": [],
        "errors": [],
        "qualitative_review": "required separately",
        "verification_scope": "rendered geometry, inventory and declared browser behaviors",
    }
    sections, slides = inventory.get("section_ids"), inventory.get("slide_ids")
    if (
        not isinstance(sections, list)
        or not sections
        or not all(isinstance(value, str) and value for value in sections)
        or len(set(sections)) != len(sections)
    ):
        report["errors"].append("independent unique section_ids required")
        return report
    if (
        not isinstance(slides, list)
        or not all(isinstance(value, str) and value for value in slides)
        or len(set(slides)) != len(slides)
    ):
        report["errors"].append(
            "independent unique slide_ids required; [] means explicit opt-out"
        )
        return report
    try:
        from playwright.sync_api import sync_playwright

        spec = importlib.util.spec_from_file_location(
            "handbook_visual_detector", detector_path
        )
        if spec is None or spec.loader is None:
            raise ValueError("visual detector unavailable")
        detector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(detector)
        allowlist = inventory.get("detector_allowlist", [])
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            report["browser"] = "Chromium " + browser.version
            for width, height in viewports or VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("pageerror", lambda error: report["errors"].append(str(error)))

                def block(route):
                    report["errors"].append("outbound request: " + route.request.url)
                    route.abort()

                page.route("http**/*", block)
                page.goto(html.resolve().as_uri())
                page.evaluate("document.fonts.ready")
                page.wait_for_function(
                    "Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)"
                )
                actual = page.locator("[data-dv-section]").evaluate_all(
                    "es=>es.map(e=>e.dataset.dvSection)"
                )
                actual_slides = page.locator("[data-dv-slide]").evaluate_all(
                    "es=>es.map(e=>e.dataset.dvSlide)"
                )
                if actual != sections or actual_slides != slides:
                    raise ValueError(
                        f"inventory mismatch: sections {actual}; slides {actual_slides}"
                    )
                if not slides and page.locator("[data-dv-deck],[data-dv-open]").count():
                    raise ValueError("opt-out contains presentation elements")
                for label in inventory.get("expected_labels", []):
                    if label not in page.locator("[data-dv-page]").inner_text():
                        report["errors"].append("missing source label: " + label)
                for view, ids, selector in (
                    ("reading", sections, "[data-dv-section]"),
                    ("presentation", slides, "[data-dv-slide]"),
                ):
                    if view == "presentation" and slides:
                        page.evaluate("window.NexusDualView.open()")
                    for index, identity in enumerate(ids):
                        item = page.locator(selector).nth(index)
                        if view == "reading":
                            item.scroll_into_view_if_needed()
                        states = (
                            ("initial", "mid", "final")
                            if view == "presentation"
                            else ("final",)
                        )
                        for state in states:
                            if state == "mid":
                                page.wait_for_timeout(260)
                            if state == "final" and view == "presentation":
                                page.wait_for_timeout(900)
                                page.wait_for_function(
                                    "document.querySelector('[data-dv-deck]').getAnimations({subtree:true}).filter(a=>a.effect&&Number.isFinite(a.effect.getComputedTiming().endTime)).every(a=>a.playState==='finished'||a.playState==='idle')",
                                    timeout=5000,
                                )
                            values = item.evaluate(MEASURE)
                            row = {
                                "view": view,
                                "id": identity,
                                "viewport": [width, height],
                                "state": state,
                                **values,
                            }
                            report["rows"].append(row)
                            if state != "final":
                                continue
                            if (
                                not values["visible"]
                                or values["clipped"]
                                or values["scrollWidth"] > values["width"] + 1
                            ):
                                report["errors"].append(
                                    f"{view}/{identity}/{width}x{height}: clipped, hidden or horizontal overflow"
                                )
                            if (
                                view == "presentation"
                                and width > 760
                                and values["scrollHeight"] > values["height"] + 1
                            ):
                                report["errors"].append(
                                    f"{identity}/{width}x{height}: desktop stage scroll"
                                )
                            for item in values["faded"]:
                                report["errors"].append(
                                    f"{view}/{identity}/{width}x{height}: opening-screen "
                                    f"content at opacity {item['alpha']} -- {item['text']!r}"
                                )
                            for mark in values["brand"]:
                                report["errors"].append(
                                    f"{view}/{identity}/{width}x{height}: brand mark "
                                    f"{mark['width']}x{mark['height']} is invisible at "
                                    f"{mark['ratio']}:1, rgb{tuple(mark['fill'])} on "
                                    f"rgb{tuple(mark['background'])}; brand_variants is "
                                    f"keyed by the SURFACE theme"
                                )
                            for chart in values["deformed"]:
                                report["errors"].append(
                                    f"{view}/{identity}/{width}x{height}: chart uses "
                                    f"preserveAspectRatio=none, deforming "
                                    f"{chart['marks']} data mark(s)"
                                )
                            for hit in values["overlaps"]:
                                report["errors"].append(
                                    f"{view}/{identity}/{width}x{height}: svg label "
                                    f"{hit['text']!r} straddles a <{hit['shape']}> "
                                    f"({hit['covered']}% of the label covered)"
                                )
                            for pair in values["contrast"]:
                                report["errors"].append(
                                    f"{view}/{identity}/{width}x{height}: contrast "
                                    f"{pair['ratio']}:1 below {pair['floor']}:1 for "
                                    f"{pair['role']} rgb{tuple(pair['ink'])} on "
                                    f"rgb{tuple(pair['background'])} -- {pair['text']!r}"
                                )
                            for font in values["fonts"]:
                                if font["px"] + 0.1 < max(
                                    FONT_FLOORS[font["role"]],
                                    inventory.get("font_floors", {}).get(
                                        font["role"], FONT_FLOORS[font["role"]]
                                    ),
                                ):
                                    report["errors"].append(
                                        f"{identity}: undersized {font['role']}: {font['px']:.2f}px"
                                    )
                            found = page.evaluate(
                                detector._DETECTOR_JS,
                                {
                                    "tolerance": 1,
                                    "minimumTextWidth": 16,
                                    "minimumTextHeight": 12,
                                    "fontFloor": 12,
                                    "viewportWidth": width,
                                    "viewportHeight": height,
                                    "allowlist": allowlist,
                                    "linkedStylesheets": [],
                                },
                            )
                            row["detector_findings"] = found["findings"]
                            report["errors"].extend(
                                f"{identity}: {f['rule']}"
                                for f in found["findings"]
                                if f["rule"] in detector.GATE_RULES
                            )
                        if view == "presentation" and index + 1 < len(ids):
                            page.keyboard.press("ArrowRight")
                page.close()
            page = browser.new_page(
                java_script_enabled=False, viewport={"width": 1366, "height": 768}
            )
            page.goto(html.resolve().as_uri())
            if (
                page.locator("[data-dv-section]").count() != len(sections)
                or not page.locator("[data-dv-page]").is_visible()
            ):
                raise ValueError("no-JS reading view missing")
            for hit in page.evaluate(DECLARED_POSITION):
                report["errors"].append(
                    f"layout: {hit['selector']!r} declares position "
                    f"{hit['declared']} but <{hit['tag']}> computes "
                    f"{hit['computed']}; the declaration never applies"
                )
            page.emulate_media(media="print")
            if not page.locator("[data-dv-page]").is_visible():
                raise ValueError("print reading view missing")
            for pair in page.evaluate(PRINT_CONTRAST):
                report["errors"].append(
                    f"print: contrast {pair['ratio']}:1 below {pair['floor']}:1 -- "
                    f"ink rgb{tuple(pair['ink'])} prints on rgb{tuple(pair['printed'])}"
                    + (
                        f" because the declared rgb{tuple(pair['declared'])} surface "
                        f"is not painted without print-color-adjust: exact"
                        if pair["declared"]
                        else ""
                    )
                    + f" -- {pair['text']!r}"
                )
            report["no_js_and_print"] = "pass"
            page.close()
            if slides:
                page = browser.new_page(reduced_motion="reduce")
                page.goto(html.resolve().as_uri())
                page.evaluate(
                    "()=>{Element.prototype.requestFullscreen=()=>Promise.reject(new Error('controlled denial'));}"
                )
                page.locator("[data-dv-open]").first.click()
                if not page.evaluate(
                    "window.NexusDualView.snapshot().active && !document.fullscreenElement"
                ):
                    raise ValueError(
                        "fullscreen denial did not retain usable presentation"
                    )
                page.keyboard.press("Escape")
                if page.evaluate("window.NexusDualView.snapshot().active"):
                    raise ValueError("Escape did not restore reading")
                # R25 names focus restoration beside scroll restoration. A
                # keyboard or screen-reader user returned to <body> has lost
                # their place entirely, and deck deactivation alone cannot
                # detect that.
                landed = page.evaluate(
                    "() => {const a=document.activeElement;"
                    " return {tag:a?a.tagName.toLowerCase():'none',"
                    " opener:!!(a&&a.closest&&a.closest('[data-dv-open],[data-dv-chapter]'))};}"
                )
                if not landed["opener"]:
                    report["errors"].append(
                        "focus: closing the presentation left focus on "
                        f"<{landed['tag']}> rather than the control that opened it"
                    )
                report["reduced_motion_fullscreen_fallback_escape"] = "pass"
                page.close()
            browser.close()
        report["status"] = "fail" if report["errors"] else "pass"
    except Exception as exc:  # noqa: BLE001 - unavailable renderer is an explicit non-pass
        report["errors"].append(str(exc))
    sizes = [f["px"] for row in report["rows"] for f in row["fonts"]]
    report["font_px"] = (
        {"min": min(sizes), "mean": statistics.mean(sizes), "max": max(sizes)}
        if sizes
        else None
    )
    report["coverage"] = {
        "sections": len(sections),
        "slides": len(slides),
        "measured_states": len(report["rows"]),
    }
    if hashlib.sha256(html.read_bytes()).hexdigest() != report["output_sha256"]:
        report["status"] = "unverified"
        report["errors"].append("output changed during measurement")
    report["fail_count"] = len(report["errors"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument(
        "--detector",
        required=True,
        type=Path,
        help="installed functional-verification/scripts/detect_visual_defects.py",
    )
    args = parser.parse_args()
    result = measure(
        args.html, json.loads(args.inventory.read_text(encoding="utf-8")), args.detector
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
