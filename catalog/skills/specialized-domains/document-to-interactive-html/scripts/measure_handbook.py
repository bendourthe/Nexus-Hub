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

# responsive-typography.md section 4.1 owns this one, and it is deliberately NOT
# expressed in px. The floors above are reading-page floors set for a document at
# desk distance; a stage is read across a room, so its floor is a share of the
# stage height and therefore holds at any canvas size. It is measured here rather
# than in visual_qa_score.py because the value that matters is the RENDERED size
# after the stage's transform, which markup alone cannot decide - the reason that
# script's slide-type checks stop at declared sizes and name this a render probe.
SLIDE_STAGE_FLOOR_FRACTION = 0.02

# Ceilings on RENDERED size, per named role. The floor gate above is one-sided,
# so text rendering far ABOVE the document scale passed silently - which is
# exactly how the SVG scaling trap escapes: an SVG multiplies its authored
# font-size by (css width / viewBox width), so `font-size:14px` in a 120-unit
# viewBox laid out at 600px renders at 70px while the source looks ordinary.
#
# These are calibrated against real output rather than guessed. The repository's
# own handbooks render at most: title 68.3, heading-1 41.0, body 20.0,
# interactive 18.0, caption 14.0. Each ceiling sits well above its observed
# maximum so legitimate design has room, and far below what the scaling trap
# produces.
TYPE_CEILINGS = {
    "title": 96,
    "subtitle": 56,
    "heading-1": 56,
    "heading-2": 44,
    "heading-3": 36,
    "lead": 32,
    "body": 28,
    "caption": 22,
    "plot-title": 32,
    "axis-title": 26,
    "axis-tick": 22,
    "legend": 22,
    "annotation": 26,
    "annotation-strong": 30,
    "table-header": 24,
    "table-cell": 24,
    "mono": 24,
    "interactive": 28,
}

MEASURE = r"""(root) => {
 const visible = e => e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
 const fonts=[], figures=[], clipped=[], contrast=[], overlaps=[], brand=[], deformed=[], faded=[], unroled=[];
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
 const resolveTypeRole=(e)=>{
     const declared=e.closest('[data-type-role]');
     if(declared) return declared.getAttribute('data-type-role');
     if(e.matches('code,pre,kbd,samp,.mono')||e.closest('code,pre')) return 'mono';
     if(e.matches('th')) return 'table-header';
     if(e.matches('td')) return 'table-cell';
     if(e.matches('figcaption')) return 'caption';
     if(e.matches('h1')) return 'title';
     if(e.matches('h2')) return 'heading-1';
     if(e.matches('h3')) return 'heading-2';
     if(e.matches('h4,h5,h6')) return 'heading-3';
     if(e.matches('[data-subtitle],.subtitle')) return 'subtitle';
     if(e.matches('[data-lead],.lead')) return 'lead';
     if(e instanceof SVGElement) {
       if(e.closest('.dv-legend,[data-dv-legend],.legend')) return 'legend';
       if(e.matches('[data-plot-title],.plot-title')) return 'plot-title';
       if(e.matches('[data-axis-title],.axis-title')) return 'axis-title';
       if(e.matches('[data-axis-tick],.axis-tick,.tick text')) return 'axis-tick';
       if(e.matches('[data-annotation-strong],.annotation-strong')) return 'annotation-strong';
       return 'annotation';
     }
     if(e.matches('button,a,input,select,textarea,label')) return 'interactive';
     if(e.matches('p,li')) return 'body';
     return null;
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
   // The NAMED role, from responsive-typography.md section 12. This is separate
   // from the coarse `role` above, which the floor gate has always used: floors
   // and ceilings ask different questions, and merging them would change what
   // the floor gate measures. An explicit data-type-role always wins, so a
   // document can name a role the structural map cannot infer.
   const typeRole=resolveTypeRole(e);
   const px=parseFloat(css.fontSize)*scale;
   fonts.push({role,typeRole,px,text:e.textContent.trim().slice(0,60),
               selector:e.tagName.toLowerCase()+(e.id?('#'+e.id):'')});
   const label=e.textContent.trim();
   if(label) {
     const ink=rgb(e instanceof SVGElement ? (css.fill!=='none'?css.fill:css.color) : css.color);
     if(ink && ink[3]>0.05) {
       // Transparency is part of the colour the reader sees. Scoring the
       // DECLARED ink treats 40%-alpha grey as if it were solid grey and
       // reports a pass the screen does not support, so the ink is composited
       // over its backdrop at its effective alpha first: the element's own
       // rgba() alpha multiplied by every opacity inherited down the chain.
       // This is what makes contrast the single owner of legibility; the
       // opacity floor below keeps only the case contrast cannot see.
       let alpha=ink[3];
       for(let p=e;p;p=p.parentElement) alpha*=parseFloat(getComputedStyle(p).opacity)||1;
       // WCAG 1.4.3: 3.0 for large text (>=24px, or >=18.66px bold), else 4.5.
       const bold=(parseInt(css.fontWeight,10)||400)>=700;
       const floor=(px>=24||(bold&&px>=18.66))?3:4.5;
       const bg=backdrop(e);
       const seen=[0,1,2].map(i=>ink[i]*alpha+bg[i]*(1-alpha));
       const value=ratio(seen,bg);
       if(value<floor) contrast.push({role,px:Math.round(px*10)/10,
         ink:ink.slice(0,3),alpha:Math.round(alpha*100)/100,
         background:bg.slice(0,3),
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
 // Content already on screen must be present at first paint. A scroll-driven
 // reveal that starts below full opacity ships its opening screen half-faded,
 // and the reader has nothing to scroll to trigger it. The defect this was
 // built from measured 0.45.
 //
 // The floor is 0.5, not 0.95, and the difference is the whole point. Whether
 // dimmed text can be READ is a contrast question, and the contrast pass above
 // now composites accumulated opacity into the ink, so it answers that one
 // properly for every colour. A bare opacity number cannot: 0.85 on near-black
 // ink still measures 10.75:1 and is perfectly legible, while 0.96 on mid-grey
 // can sit under the floor. Keeping 0.95 here made this gate fail a deliberate
 // de-emphasis on secondary text while the readability hole stayed open.
 // What survives is the case contrast cannot see: content more absent than
 // present, which reads as a reveal that never ran whatever colour it is.
 for(const e of root.querySelectorAll('h1,h2,h3,p,li,td,th,figcaption')) {
   if(!e.textContent.trim() || !visible(e)) continue;
   const box=e.getBoundingClientRect();
   if(box.bottom<=0 || box.top>=innerHeight) continue;   // not on the opening screen
   let alpha=1;
   for(let p=e;p;p=p.parentElement) alpha*=parseFloat(getComputedStyle(p).opacity)||1;
   if(alpha<0.5) faded.push({alpha:Math.round(alpha*100)/100,
     text:e.textContent.trim().slice(0,50)});
 }
 const b=root.getBoundingClientRect();
 // Role COVERAGE walks every element that owns visible text of its own, which
 // is a wider set than the floor gate's fixed selector list. That list contains
 // only elements the role map already resolves, so a coverage check driven from
 // it could never report anything - a gate that cannot fail is not a gate. A
 // bare <span> carrying prose is exactly the case worth catching, because
 // silently treating it as body would apply the wrong ceiling to it.
 for(const e of root.querySelectorAll('*')) {
   if(!visible(e)) continue;
   if(e.closest('script,style,noscript,template')) continue;
   const own=[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
   if(!own) continue;
   // An inline element INHERITS the role of the block it sits in: a <strong>
   // inside a paragraph is body text, not an orphan. Reporting it would bury
   // the real case - 30 per handbook on the repository's own output, all of
   // them legitimate. Only a node with nothing role-bearing anywhere above it
   // is genuinely unassigned.
   let inherited=null;
   for(let a=e;a&&a!==root.parentElement;a=a.parentElement) {
     inherited=resolveTypeRole(a);
     if(inherited!==null) break;
   }
   if(inherited===null) {
     unroled.push({selector:e.tagName.toLowerCase()+(e.id?('#'+e.id):''),
                   text:e.textContent.trim().slice(0,60)});
   }
 }
 return {fonts,figures,clipped,contrast,overlaps,brand,deformed,faded,unroled,width:root.clientWidth,scrollWidth:root.scrollWidth,
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

# Deck integrity, evaluated against ONE slide while that slide is current.
#
# The "while current" part is the whole contract. A probe that walks every slide
# at the end reports all of them hidden, because only the current slide is
# displayed - that produced a false alarm in the source project and cost a round
# of investigation into a defect that did not exist. The caller runs this inside
# the existing per-slide loop, after the animation window has closed.
#
# Three defects, none of which is visible in markup review:
#
#  - A slide that overflows the fixed canvas. There is nowhere to scroll on a
#    slide, so overflow is content the reader can never reach.
#  - An element left permanently invisible by a fill-mode collision. Combining a
#    staggering utility that sets opacity:0 filling FORWARDS with a component
#    that animates itself filling BACKWARDS left four tiles invisible in the
#    source project. Undetectable by reading the CSS; trivial to measure once
#    the animations have finished.
#  - A dangling reference in a cloned figure. Slides clone the document's
#    figures, and a clone whose url(#x) still points at the original appears to
#    work only while the original is in the document to resolve against.
DECK_INTEGRITY = r"""(slide) => {
 const findings = [];
 const round = (n) => Math.round(n * 100) / 100;
 const name = (e) => e.tagName.toLowerCase() + (e.id ? ('#' + e.id) : '');

 // ---- canvas fit ---------------------------------------------------------
 const frame = slide.getBoundingClientRect();
 for (const child of slide.querySelectorAll('*')) {
   const cs = getComputedStyle(child);
   if (cs.display === 'none' || cs.visibility === 'hidden') continue;
   if (cs.position === 'fixed') continue;
   const r = child.getBoundingClientRect();
   if (!r.width && !r.height) continue;
   const overX = Math.max(frame.left - r.left, r.right - frame.right);
   const overY = Math.max(frame.top - r.top, r.bottom - frame.bottom);
   const worst = Math.max(overX, overY);
   if (worst > 2) {
     findings.push({rule: 'slide-overflow', selector: name(child),
       overflow_px: round(worst), axis: overX >= overY ? 'x' : 'y',
       text: (child.textContent || '').trim().slice(0, 40)});
     break;   // one report per slide; the first is enough to act on
   }
 }

 // The figure runtime delegates series clicks from document but resolves the
 // clicked button's nearest chart figure before changing its marks. A button
 // moved outside that figure remains visible and focusable yet cannot work.
 // Listener presence alone cannot catch it because document always listens.
 for (const control of slide.querySelectorAll('button[data-dv-series]')) {
   if (!control.closest('figure[data-dv-figure]')) {
     findings.push({rule: 'series-control-outside-figure', selector: name(control)});
   }
 }

 // ---- an element left invisible after the animation window ----------------
 for (const e of slide.querySelectorAll('*')) {
   const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
   const paints = own || e.tagName === 'IMG' || e.tagName === 'svg';
   if (!paints) continue;
   if (e.closest('[aria-hidden="true"],[hidden]')) continue;
   const cs = getComputedStyle(e);
   if (cs.display === 'none' || cs.visibility === 'hidden') continue;
   let effective = 1;
   for (let a = e; a && a !== document.documentElement; a = a.parentElement) {
     effective *= parseFloat(getComputedStyle(a).opacity || '1');
     if (a === slide) break;
   }
   if (effective < 0.05) {
     findings.push({rule: 'invisible-after-animation', selector: name(e),
       effective_opacity: round(effective),
       text: (e.textContent || '').trim().slice(0, 40)});
   }
 }

 // ---- a cloned figure whose references do not resolve ---------------------
 const scope = slide.querySelectorAll('[data-dv-clone], svg');
 for (const holder of scope) {
   if (holder.matches('[data-dv-clone]') && !holder.children.length) {
     findings.push({rule: 'empty-clone-holder', selector: name(holder)});
     continue;
   }
   for (const node of holder.querySelectorAll('*')) {
     const refs = [];
     for (const attr of node.getAttributeNames()) {
       const v = node.getAttribute(attr);
       if (!v) continue;
       const m = /^url\(["']?#([^"')]+)["']?\)$/.exec(v.trim());
       if (m) refs.push(m[1]);
       else if (attr === 'href' || attr === 'xlink:href') {
         if (v.startsWith('#')) refs.push(v.slice(1));
       }
     }
     for (const id of refs) {
       // Resolve WITHIN the slide first: a clone that resolves only against the
       // original is the exact defect, and it looks fine until the original goes.
       if (!slide.querySelector('[id="' + CSS.escape(id) + '"]')) {
         findings.push({rule: 'clone-reference-escapes-slide', selector: name(node),
           reference: id,
           resolves_in_document: !!document.getElementById(id)});
       }
     }
   }
 }
 return findings;
}"""

# Only independently mapped, DOM-rendered source values are in this envelope.
# MutationObserver sees brief text changes between the existing state samples;
# an unmapped value must remain unchecked rather than receive a false pass.
SOURCE_VALUE_WATCH = r"""(specs) => {
  window.__nexusSourceValueWatch = specs.map(spec => {
    const slide = [...document.querySelectorAll('[data-dv-slide]')]
      .find(node => node.dataset.dvSlide === spec.slide_id);
    const matches = slide ? slide.querySelectorAll(spec.selector) : [];
    if (matches.length !== 1) {
      return {spec, error: `source value ${spec.slide_id} ${spec.selector} matched ${matches.length} elements`};
    }
    const watch = {spec, count: 0, wrong: [], last: null};
    watch.capture = () => {
      const current = slide.querySelectorAll(spec.selector);
      if (current.length !== 1 || slide.hidden ||
          !current[0].checkVisibility({checkOpacity:true,checkVisibilityCSS:true})) return;
      const text = current[0].textContent.trim();
      if (text === watch.last) return;
      watch.last = text;
      watch.count++;
      if (text !== spec.text && watch.wrong.length < 3) watch.wrong.push(text);
    };
    watch.observer = new MutationObserver(watch.capture);
    watch.observer.observe(slide, {subtree:true,childList:true,characterData:true});
    return watch;
  });
  return window.__nexusSourceValueWatch.filter(watch => watch.error).map(watch => watch.error);
}"""

SOURCE_VALUE_RESULT = r"""(slideId) => window.__nexusSourceValueWatch
  .filter(watch => watch.spec.slide_id === slideId)
  .map(watch => {
    watch.capture();
    watch.observer.disconnect();
    return {selector:watch.spec.selector, expected:watch.spec.text,
      observed_changes:watch.count, wrong:watch.wrong};
  })"""


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
        "source_value_guard": {"status": "unchecked", "observations": [], "findings": []},
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
    source_values = inventory.get("source_values", [])
    if not isinstance(source_values, list) or any(
        not isinstance(spec, dict)
        or spec.get("slide_id") not in slides
        or not isinstance(spec.get("selector"), str)
        or not spec["selector"]
        or not isinstance(spec.get("text"), str)
        or not spec["text"]
        for spec in source_values
    ):
        report["errors"].append("source value inventory is malformed")
        return report
    if len({(spec["slide_id"], spec["selector"]) for spec in source_values}) != len(
        source_values
    ):
        report["errors"].append("source value inventory contains duplicate selectors")
        return report
    if source_values:
        report["source_value_guard"]["status"] = "unverified"
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
                if source_values:
                    errors = page.evaluate(SOURCE_VALUE_WATCH, source_values)
                    if errors:
                        raise ValueError("; ".join(errors))
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
                                # The stage floor is a SECOND, stricter floor that
                                # applies only while the slide is the measured root,
                                # because 2% of a stage means nothing on a scrolling
                                # page. Both can fire on one text node: the page floor
                                # says it is too small to read at a desk, this says it
                                # is too small to read across a room.
                                if view == "presentation":
                                    # The basis is the VIEWPORT height, not the
                                    # slide element's clientHeight. On a stage
                                    # that reflows and scrolls - compact mode at
                                    # 390x844 measured a 4070px element - the
                                    # element's height is the content's, and 2%
                                    # of it (81px) is a floor no type can meet.
                                    # The contract's own arithmetic settles it:
                                    # "on a 1080px stage, 21.6px" is 2% of the
                                    # viewport. A scrolling desktop stage is a
                                    # separate error already reported above.
                                    stage_floor = height * SLIDE_STAGE_FLOOR_FRACTION
                                    if stage_floor and font["px"] + 0.1 < stage_floor:
                                        report["errors"].append(
                                            f"{identity}/{width}x{height}: text below the "
                                            f"slide-stage floor: {font['px']:.2f}px under "
                                            f"{stage_floor:.2f}px "
                                            f"({SLIDE_STAGE_FLOOR_FRACTION:.0%} of the "
                                            f"{height}px stage) -- {font['text']!r}"
                                        )
                                # The other side of the same gate.
                                named = font.get("typeRole")
                                if named is not None:
                                    ceiling = inventory.get("type_ceilings", {}).get(
                                        named, TYPE_CEILINGS.get(named)
                                    )
                                    if view == "presentation" and ceiling:
                                        # A tall stage can require type larger than
                                        # the reading-page ceiling for the same role.
                                        ceiling = max(
                                            ceiling, height * SLIDE_STAGE_FLOOR_FRACTION
                                        )
                                    if ceiling and font["px"] > ceiling + 0.1:
                                        report["errors"].append(
                                            f"{identity}: oversized {named}: "
                                            f"{font['px']:.2f}px above the "
                                            f"{ceiling}px ceiling -- {font['text']!r}"
                                        )
                            for node in values.get("unroled", []):
                                report["errors"].append(
                                    f"{identity}: unassigned type role on "
                                    f"{node['selector']} -- {node['text']!r}"
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
                            if view == "presentation" and state == "final":
                                # While THIS slide is current, and only now:
                                # the animations have finished, so opacity is
                                # what the reader will actually see.
                                for hit in page.evaluate(
                                    DECK_INTEGRITY, item.element_handle()
                                ):
                                    report["errors"].append(
                                        f"{identity}: {hit['rule']} on "
                                        f"{hit['selector']}"
                                        + (f" -- {hit['text']!r}" if hit.get("text") else "")
                                    )
                                if source_values:
                                    for observed in page.evaluate(SOURCE_VALUE_RESULT, identity):
                                        report["source_value_guard"]["observations"].append(
                                            {"slide_id": identity, "viewport": [width, height], **observed}
                                        )
                                        if not observed["observed_changes"]:
                                            finding = (
                                                f"{identity}: source value {observed['selector']} was never visible"
                                            )
                                            report["errors"].append(finding)
                                            report["source_value_guard"]["findings"].append(finding)
                                        for wrong in observed["wrong"]:
                                            finding = (
                                                f"{identity}: source value {observed['selector']} displayed {wrong!r}; expected {observed['expected']!r}"
                                            )
                                            report["errors"].append(finding)
                                            report["source_value_guard"]["findings"].append(finding)
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
        if source_values:
            report["source_value_guard"]["status"] = (
                "fail" if report["source_value_guard"]["findings"] else "pass"
            )
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
