from pathlib import Path
from playwright.sync_api import sync_playwright
import json,re,subprocess,tempfile
root=Path.cwd();out=root/'docs/releases/v4/v4.4/development/guide-visual-refinement/models-rebuild';s=(root/'guides/website/nexus-hub-guide.html').read_text(encoding='utf-8');scripts=[]
for attrs,body in re.findall(r'<script([^>]*)>([\s\S]*?)</script>',s):
 if 'application/json' not in attrs:scripts.append(body)
p=Path(tempfile.gettempdir())/'nexus-models-final-js.js';p.write_text('\n'.join(scripts),encoding='utf-8');result=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert result.returncode==0,result.stderr
records=[];errors=[];requests=[]
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(viewport={'width':1440,'height':1100},reduced_motion='no-preference');p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:requests.append(r.url) if r.url.startswith('http') else None);p.goto((root/'guides/website/nexus-hub-guide.html').as_uri()+'#foundations')
 for mode in ['language','diffusion','world','omni']:
  p.locator('[data-mode='+mode+']').click();panel=p.locator('#ml-'+mode);panel.locator('[data-run]').click()
  for frame in [0,2,5]:
   p.wait_for_function('(v)=>document.querySelector(v[0]).dataset.frame===v[1]',arg=['#ml-'+mode,str(frame)],timeout=6000)
   records.append({'mode':mode,'frame':frame,'status':panel.locator('.ml-status').inner_text()});panel.locator('.ml-board').screenshot(path=str(out/f'animation-{mode}-{frame}.png'),animations='allow')
  assert panel.evaluate('e=>!e.classList.contains("ml-playing")')
 p.wait_for_timeout(1000);assert p.locator('.ml-playing').count()==0;b.close()
(out/'runtime.json').write_text(json.dumps({'javascript_syntax':'pass','frames':records,'errors':errors,'external_requests':requests,'idle_after_completion':True},indent=2)+'\n',encoding='utf-8');print('Syntax passed; captured',len(records),'frames; errors',errors,'external requests',requests)
