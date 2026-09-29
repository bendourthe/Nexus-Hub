"""Measure the reveal and sequence intersection boundaries without changing guide state."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=next(p for p in Path(__file__).resolve().parents if (p/'guides/website/nexus-hub-guide.html').is_file())
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    page=browser.new_page(viewport={'width':420,'height':900})
    page.goto((root/'guides/website/nexus-hub-guide.html').as_uri()+'#foundations')
    page.evaluate('''() => { window.observed=[]; let r=document.querySelector('#hx-harness'); window.probeObserver=new IntersectionObserver(es=>observed.push(...es.map(e=>({ratio:e.intersectionRatio,intersects:e.isIntersecting}))),{threshold:.4}); probeObserver.observe(r); }''')
    page.locator('#hx-harness').evaluate('(el)=>el.scrollIntoView({block:"center",behavior:"instant"})')
    page.wait_for_timeout(8500)
    result=page.evaluate('''() => ({events:observed,state:NexusSeq.state(document.querySelector('#hx-harness')), nodes:['#fx-harness','#hx-harness'].map(s=>{let el=document.querySelector(s),r=el.getBoundingClientRect(),cs=getComputedStyle(el);return {selector:s,classes:el.className,top:r.top,bottom:r.bottom,height:r.height,opacity:cs.opacity}})})''')
    (Path(__file__).parent/'visibility-probe.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
    browser.close()
