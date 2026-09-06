from pathlib import Path
from playwright.sync_api import sync_playwright
import json
out=Path(__file__).resolve().parent
root=out.parents[6]
import os, re, subprocess, hashlib
os.chdir(root)
with sync_playwright() as pw:
 b=pw.chromium.launch();results=[]
 for width in [320,420,768,1024,1440]:
  for theme in ['dark','light']:
   p=b.new_page(viewport={'width':width,'height':1100},reduced_motion='reduce');p.goto(Path('guides/website/nexus-hub-guide.html').resolve().as_uri()+'#foundations');p.evaluate('t=>document.documentElement.dataset.theme=t',theme)
   for mode in ['language','diffusion','world','multimodal']:
    p.locator('[data-mode='+mode+']').click();panel=p.locator('#ml-'+mode)
    geo=panel.evaluate('''e=>({overflow:document.documentElement.scrollWidth>innerWidth+1,clipped:[...e.querySelectorAll('*')].filter(x=>!(x instanceof SVGElement)&&x.clientWidth&&x.scrollWidth>x.clientWidth+2).map(x=>x.className)})''');results.append(dict(width=width,theme=theme,mode=mode,**geo))
    if width in [320,1440]:p.locator('.ml-lab').evaluate("e=>window.scrollTo({top:e.getBoundingClientRect().top+scrollY-90,behavior:'instant'})");p.locator('.ml-lab').screenshot(path=str(out/f'{theme}-{width}-{mode}.png'))
   if width in [320,1440]:
    p.locator('.ml-capability').screenshot(path=str(out/f'{theme}-{width}-classes.png'));p.locator('.ml-reasoning').screenshot(path=str(out/f'{theme}-{width}-effort.png'));p.locator('.ml-intro').screenshot(path=str(out/f'{theme}-{width}-training.png'))
   if width==1440:
    p.locator('[data-mode=language]').click();p.locator('#fx-model-lifecycle').screenshot(path=str(out/f'{theme}-section.png'))
   p.close()
 p=b.new_page(viewport={'width':1440,'height':1100},reduced_motion='no-preference');errors=[];requests=[]
 p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:requests.append(r.url) if r.url.startswith('http') else None)
 p.goto(Path('guides/website/nexus-hub-guide.html').resolve().as_uri()+'#foundations')
 p.locator('.ml-lab').scroll_into_view_if_needed();p.locator('#ml-motion').click()
 frames=[]
 for mode in ['language','diffusion','world','multimodal']:
  p.locator('[data-mode='+mode+']').click()
  for n in range(6):
   p.locator('#ml-step').click();panel=p.locator('#ml-'+mode);frames.append({'mode':mode,'frame':panel.get_attribute('data-frame')})
   if mode=='world' or n in [0,2,5]:p.locator('.ml-lab').screenshot(path=str(out/f'frame-{mode}-{n}.png'))
 p.locator('[data-mode=language]').click();p.locator('#ml-motion').click();p.wait_for_timeout(1250)
 travel=p.locator('#ml-language .ml-signal circle').evaluate('e=>getComputedStyle(e).offsetDistance')
 p.locator('.ml-lab').screenshot(path=str(out/'network-in-flight.png'))
 p.locator('a[href="#home"]').first.click();p.wait_for_timeout(200)
 idle=p.locator('#fx-model-lifecycle .ml-playing').count()
 (out/'runtime.json').write_text(json.dumps({'errors':errors,'requests':requests,'frames':frames,'signal_offset':travel,'playing_after_exit':idle},indent=2))
 b.close();(out/'layout.json').write_text(json.dumps(results,indent=2));print([r for r in results if r['overflow'] or r['clipped']]);print('Cases',len(results))

html=Path('guides/website/nexus-hub-guide.html').read_text(encoding='utf-8')
base=subprocess.check_output(['git','show','80197e3a:guides/website/nexus-hub-guide.html']).decode('utf-8')
def strip_models(s):
 s=re.sub(r'<section[^>]+id="fx-model-lifecycle"[\s\S]*?</section>','MODELS',s)
 s=re.sub(r'#fx-model-lifecycle h3[\s\S]*?(?=</style>)','MODELS_CSS',s)
 point=s.rindex("var root=document")
 a=s.rindex('(function(){',0,point);b=s.index('})();',point)+5
 return s[:a]+'MODELS_JS'+s[b:]
checks=[]
for i,(attrs,code) in enumerate(re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S)):
 if 'application/json' in attrs:continue
 temp=Path(os.environ['TEMP'])/f'models-flow-check-{i}.js';temp.write_text(code,encoding='utf-8')
 result=subprocess.run(['node','--check',str(temp)],capture_output=True,text=True)
 checks.append(result.returncode==0)
 if result.returncode:raise AssertionError(result.stderr)
assert strip_models(base)==strip_models(html),'Unrelated guide content changed'
(out/'scope.json').write_text(json.dumps({'baseline':'80197e3a','outside_models_unchanged':True,'bytes':len(html.encode()),'sha256':hashlib.sha256(html.encode()).hexdigest(),'syntax_checks':checks},indent=2))
