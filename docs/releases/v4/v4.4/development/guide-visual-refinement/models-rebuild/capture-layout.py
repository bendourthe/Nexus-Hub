from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path.cwd(); out=root/'docs/releases/v4/v4.4/development/guide-visual-refinement/models-rebuild'
rows=[]
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for theme in ['dark','light']:
  for width in [320,420,768,1024,1440]:
   p=b.new_page(viewport={'width':width,'height':1000},reduced_motion='reduce'); errors=[]; p.on('pageerror',lambda e:errors.append(str(e)))
   p.goto((root/'guides/website/nexus-hub-guide.html').as_uri()+'#foundations');p.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
   for mode in ['language','diffusion','world','omni']:
    p.locator('[data-mode='+mode+']').click(); p.wait_for_timeout(100)
    row=p.evaluate('''() => {let s=document.querySelector('#fx-model-lifecycle'),r=document.querySelector('.ml-panel:not([hidden])');return {height:s.getBoundingClientRect().height,words:s.innerText.split(/\\s+/).length,pageOverflow:document.documentElement.scrollWidth>innerWidth+1,clipped:[...r.querySelectorAll('*')].filter(e=>e.clientWidth&&e.scrollWidth>e.clientWidth+2&&!(e instanceof SVGElement)).map(e=>e.className)}}''')
    rows.append(dict(theme=theme,width=width,mode=mode,errors=errors,**row))
    if width in [320,1440]:
     p.locator('.ml-lab').screenshot(path=str(out/f'demo-{theme}-{width}-{mode}.png'))
   if width==1440:
    p.locator('[data-mode=language]').click();p.set_viewport_size({'width':width,'height':1900});p.evaluate("window.scrollTo({top:document.querySelector('#fx-model-lifecycle').getBoundingClientRect().top+scrollY-85,behavior:'instant'})");p.wait_for_timeout(100);p.screenshot(path=str(out/f'section-{theme}-1440.png'))
   p.close()
 b.close()
(out/'layout-matrix.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('Cases',len(rows),'issues',[r for r in rows if r['pageOverflow'] or r['clipped'] or r['errors']]);print('Desktop',rows[16])
