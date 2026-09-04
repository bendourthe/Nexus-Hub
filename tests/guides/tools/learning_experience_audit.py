"""Repeatable local guide measurements; screenshots preserve the real rendered state."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
GUIDE = ROOT / 'guides/website/nexus-hub-guide.html'

WORDS = """el => {
 const copy = el.cloneNode(true);
 copy.querySelectorAll('nav,.pagenav,.progress-dots,pre,code,script,style').forEach(n=>n.remove());
 const total = copy.textContent.trim().split(/\\s+/).filter(Boolean).length;
 copy.querySelectorAll('details:not([open])').forEach(n=>n.remove());
 return {main:copy.textContent.trim().split(/\\s+/).filter(Boolean).length,total};
}"""

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--guide', type=Path, default=GUIDE)
    parser.add_argument('--pages', nargs='+', default=['home','foundations','training','cheatsheets'])
    parser.add_argument('--performance', action='store_true')
    parser.add_argument('--screenshots', action='store_true')
    args = parser.parse_args()
    guide = args.guide.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    report = dict(sha256=hashlib.sha256(guide.read_bytes()).hexdigest(),bytes=guide.stat().st_size,
                  machine=platform.platform(), cases=[], performance=[])
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        report['browser'] = browser.version
        for theme in ['light','dark']:
            for width in [320,420,719,720,721,768,1024,1440,1920]:
                ctx=browser.new_context(viewport=dict(width=width,height=900))
                ctx.add_init_script('localStorage.setItem("portfolio-theme",'+json.dumps(theme)+');')
                page=ctx.new_page()
                errors=[]
                requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:requests.append(r.url) if r.url.startswith('http') else None)
                for route in args.pages:
                    page.goto(guide.as_uri()+'#'+route)
                    page.wait_for_timeout(100)
                    root=page.locator('#page-'+route)
                    case=dict(theme=theme,width=width,page=route,words=root.evaluate(WORDS))
                    case.update(page.evaluate('''()=>({height:document.documentElement.scrollHeight,
                      overflow:document.documentElement.scrollWidth>innerWidth,
                      hiddenEssentials:[...document.querySelectorAll('.page.active [data-seq],.page.active [data-lesson-step]')].filter(n=>getComputedStyle(n).opacity==='0').length})'''))
                    if args.screenshots and width in [420,1440]:
                        # Walk the page as a reader would, never force classes or opacity.
                        for y in range(0,case['height'],700):
                            page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})',y)
                            page.wait_for_timeout(100)
                        page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
                        page.wait_for_timeout(150)
                        page.screenshot(path=str(args.out/f'{route}-{theme}-{width}-top.png'))
                        page.screenshot(path=str(args.out/f'{route}-{theme}-{width}-full.png'),full_page=True)
                        scenes=page.locator('.page.active .lesson')
                        for i in range(scenes.count()):
                            scene=scenes.nth(i)
                            scene.evaluate('(el)=>el.scrollIntoView({block:"start",behavior:"instant"})')
                            page.wait_for_timeout(150)
                            page.screenshot(path=str(args.out/f'{route}-{theme}-{width}-{scene.get_attribute("id")}.png'))
                            if scene.bounding_box()['height']>780:
                                scene.evaluate('(el)=>el.scrollIntoView({block:"end",behavior:"instant"})')
                                page.screenshot(path=str(args.out/f'{route}-{theme}-{width}-{scene.get_attribute("id")}-bottom.png'))
                    case.update(errors=list(errors),externalRequests=list(requests))
                    report['cases'].append(case)
                ctx.close()
        if args.performance:
            for theme,width in [('light',1440),('dark',1440),('light',420)]:
                ctx=browser.new_context(viewport=dict(width=width,height=900))
                ctx.add_init_script('localStorage.setItem("portfolio-theme",'+json.dumps(theme)+');')
                page=ctx.new_page()
                cdp=ctx.new_cdp_session(page)
                cdp.send('Performance.enable')
                for run in range(4): # warmup followed by three comparable samples
                    page.goto(guide.as_uri()+'#foundations')
                    page.wait_for_timeout(300)
                    before={m['name']:m['value'] for m in cdp.send('Performance.getMetrics')['metrics']}
                    sample=page.evaluate('''async()=>{
                      const frames=[],longTasks=[];let last=performance.now(),raf;
                      const observer=new PerformanceObserver(list=>list.getEntries().forEach(e=>longTasks.push(e.duration)));
                      observer.observe({type:'longtask',buffered:false});
                      function tick(t){frames.push(t-last);last=t;raf=requestAnimationFrame(tick)}
                      raf=requestAnimationFrame(tick);
                      const start=performance.now(),height=document.documentElement.scrollHeight-innerHeight;
                      while(performance.now()-start<10000){scrollTo(0,height*(performance.now()-start)/10000);await new Promise(r=>setTimeout(r,50))}
                      cancelAnimationFrame(raf);observer.disconnect();frames.sort((a,b)=>a-b);
                      const nav=[];
                      for(let i=0;i<20;i++){const t=performance.now();document.querySelector('[data-go="'+(i%2?'foundations':'home')+'"]').click();await new Promise(requestAnimationFrame);nav.push(performance.now()-t)}
                      return {p95FrameMs:frames[Math.floor(frames.length*.95)],maxLongTaskMs:Math.max(0,...longTasks),longTaskCount:longTasks.length,maxNavigationMs:Math.max(...nav)};
                    }''')
                    after={m['name']:m['value'] for m in cdp.send('Performance.getMetrics')['metrics']}
                    sample.update(theme=theme,width=width,run=run,warmup=run==0,
                                  metrics={k:round(after[k]-before[k],6) for k in ['LayoutCount','LayoutDuration','RecalcStyleCount','RecalcStyleDuration','ScriptDuration','TaskDuration']})
                    report['performance'].append(sample)
                ctx.close()
        browser.close()
    (args.out/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(bytes=report['bytes'],cases=len(report['cases']),overflow=sum(c['overflow'] for c in report['cases']),errors=sum(bool(c['errors']) for c in report['cases']),performance=len(report['performance']))))

if __name__=='__main__':
    main()
