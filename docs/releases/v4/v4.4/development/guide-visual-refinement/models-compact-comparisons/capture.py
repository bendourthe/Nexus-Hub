"""Reproduce layout, motion, perspective and scope evidence for this refinement."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
from playwright.sync_api import sync_playwright

out=Path(__file__).resolve().parent
root=out.parents[6]
guide=root/'guides/website/nexus-hub-guide.html'
html=guide.read_text(encoding='utf-8')
base=subprocess.check_output(['git','show','416da259:guides/website/nexus-hub-guide.html'],cwd=root).decode('utf-8')
def without_models(s):
    s=re.sub(r'<section[^>]+id="fx-model-lifecycle"[\s\S]*?</section>','MODELS',s)
    s=re.sub(r'#fx-model-lifecycle h3[\s\S]*?(?=</style>)','MODELS_CSS',s)
    point=s.rindex('var root=document');a=s.rindex('(function(){',0,point);b=s.index('})();',point)+5
    return s[:a]+'MODELS_JS'+s[b:]
assert without_models(base)==without_models(html)
checks=[]
for i,(attrs,code) in enumerate(re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S)):
    if 'application/json' in attrs:continue
    temp=Path(os.environ['TEMP'])/f'models-compact-check-{i}.js';temp.write_text(code,encoding='utf-8')
    result=subprocess.run(['node','--check',str(temp)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    checks.append(True)
layout=[];runtime={'errors':[],'requests':[]};heights={}
with sync_playwright() as w:
    b=w.chromium.launch()
    for width in [320,420,768,1024,1440]:
        for theme in ['dark','light']:
            p=b.new_page(viewport={'width':width,'height':1100},reduced_motion='reduce')
            p.on('pageerror',lambda e:runtime['errors'].append(str(e)))
            p.on('request',lambda r:runtime['requests'].append(r.url) if r.url.startswith('http') else None)
            p.goto(guide.as_uri()+'#foundations');p.evaluate('t=>document.documentElement.dataset.theme=t',theme);p.mouse.move(0,0)
            for mode in ['language','diffusion','world','multimodal']:
                p.locator('[data-mode='+mode+']').click()
                geo=p.locator('#fx-model-lifecycle').evaluate("""e=>({overflow:document.documentElement.scrollWidth>innerWidth+1,clipped:[...e.querySelectorAll('*')].filter(x=>!(x instanceof SVGElement)&&x.clientWidth&&x.scrollWidth>x.clientWidth+2).map(x=>x.className)})""")
                layout.append(dict(width=width,theme=theme,mode=mode,**geo))
                if width in [320,1440]:p.locator('.ml-lab').screenshot(path=str(out/f'{theme}-{width}-{mode}.png'))
                if width==1440 and theme=='dark':heights[mode]=p.locator('.ml-lab').bounding_box()['height']
            if width in [320,1440]:
                for name,sel in [('training','.ml-intro'),('tiers','.ml-capability'),('effort','.ml-reasoning')]:p.locator(sel).screenshot(path=str(out/f'{theme}-{width}-{name}.png'))
            p.close()
    p=b.new_page(viewport={'width':1440,'height':1100},reduced_motion='no-preference')
    p.goto(guide.as_uri()+'#foundations');p.mouse.move(0,0);p.locator('[data-mode=world]').click();p.wait_for_function("document.querySelector('.ml-room').dataset.ready");p.clock.install(time=1000);p.clock.pause_at(1000);p.locator('[data-mode=world]').click()
    frames=[];elapsed=0
    for target in [0,2200,6000,12000]:
        p.mouse.move(0,0);p.clock.run_for(target-elapsed);elapsed=target
        frames.append({'time':target,'camera':p.locator('.ml-room').get_attribute('data-camera')})
        p.locator('.ml-lab').screenshot(path=str(out/f'world-{target}.png'))
    runtime['camera_frames']=frames
    p.locator('[data-mode=language]').click();p.mouse.move(0,0);p.clock.run_for(850)
    runtime['particles']=p.locator('#ml-language .ml-spark').evaluate_all('es=>es.map(e=>({offset:getComputedStyle(e).offsetDistance,state:getComputedStyle(e).animationPlayState}))')
    p.locator('.ml-lab').screenshot(path=str(out/'signals-in-flight.png'))
    p.close();p=b.new_page(viewport={'width':1440,'height':1100},reduced_motion='no-preference');p.goto(guide.as_uri()+'#foundations');p.mouse.move(0,0);p.clock.install(time=1000);p.clock.pause_at(1000);p.locator('.ml-reasoning').scroll_into_view_if_needed();p.clock.run_for(1700)
    p.locator('.ml-reasoning').screenshot(path=str(out/'effort-in-progress.png'))
    p.locator('a[href="#home"]').first.click();p.clock.run_for(200);runtime['playing_after_exit']=p.locator('#fx-model-lifecycle .ml-playing').count();p.close()
    old=Path(os.environ['TEMP'])/'models-compact-baseline.html';old.write_text(base,encoding='utf-8')
    p=b.new_page(viewport={'width':1440,'height':1100},reduced_motion='reduce');p.goto(old.as_uri()+'#foundations');baseline={}
    for mode in heights:p.locator('[data-mode='+mode+']').click();baseline[mode]=p.locator('.ml-lab').bounding_box()['height']
    b.close()
(out/'layout.json').write_text(json.dumps(layout,indent=2))
(out/'runtime.json').write_text(json.dumps(runtime,indent=2))
(out/'scope.json').write_text(json.dumps({'baseline':'416da259','outside_models_unchanged':True,'bytes':len(html.encode()),'sha256':hashlib.sha256(html.encode()).hexdigest(),'syntax_checks':checks,'lab_height_before':baseline,'lab_height_after':heights},indent=2))
assert not any(v['overflow'] or v['clipped'] for v in layout)
assert not runtime['errors'] and not runtime['requests'] and not runtime['playing_after_exit']
print('40 layout cases passed; runtime, syntax and scope checks passed')
