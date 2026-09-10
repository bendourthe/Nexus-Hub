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
 const fonts=[], figures=[], clipped=[], contrast=[];
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
 const b=root.getBoundingClientRect();
 return {fonts,figures,clipped,contrast,width:root.clientWidth,scrollWidth:root.scrollWidth,
   height:root.clientHeight,scrollHeight:root.scrollHeight,visible:visible(root),
   theme:root.getAttribute('data-theme'),bounds:{x:b.x,y:b.y,width:b.width,height:b.height}};
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
            page.emulate_media(media="print")
            if not page.locator("[data-dv-page]").is_visible():
                raise ValueError("print reading view missing")
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
