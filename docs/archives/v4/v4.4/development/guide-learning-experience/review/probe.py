"""One-off read-only browser audit of the current guide."""
import json
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'guides/website/nexus-hub-guide.html').is_file())
OUT = Path(__file__).resolve().parent
GUIDE = ROOT / 'guides/website/nexus-hub-guide.html'
report = {'sha256': hashlib.sha256(GUIDE.read_bytes()).hexdigest(), 'bytes': GUIDE.stat().st_size, 'cases': []}
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for width, theme in [(1440, 'light'), (1440, 'dark'), (420, 'light')]:
        context = browser.new_context(viewport={'width': width, 'height': 900})
        context.add_init_script("localStorage.setItem('portfolio-theme', " + json.dumps(theme) + ");")
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(GUIDE.as_uri() + '#foundations')
        page.wait_for_timeout(500)
        cdp = context.new_cdp_session(page)
        cdp.send('Performance.enable')
        before = {x['name']: x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
        for scene in ['tokens', 'prompts', 'context', 'model', 'platform', 'harness']:
            title = page.locator('#fx-' + scene + '-title')
            title.scroll_into_view_if_needed()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / f'{scene}-{theme}-{width}.png'))
        page.locator('#hx-harness').evaluate('(el)=>el.scrollIntoView({block:"center"})')
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / f'harness-in-view-{theme}-{width}.png'))
        after = {x['name']: x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
        data = page.evaluate('''() => ({height: document.documentElement.scrollHeight,
          viewport: {width: innerWidth, height: innerHeight},
          overflow: document.documentElement.scrollWidth > innerWidth,
          sections: [...document.querySelectorAll('.page.active .fx-scene')].map(x=>({id:x.id,height:x.offsetHeight})),
          sequences:[...document.querySelectorAll('.page.active [data-seq-root]')].map(x=>({id:x.id,cls:x.className,height:x.offsetHeight,steps:x.querySelectorAll('[data-seq]').length,hidden:[...x.querySelectorAll('[data-seq]')].filter(n=>getComputedStyle(n).opacity==='0').length,state:window.NexusSeq.state(x)}))})''')
        data.update({'theme': theme, 'width': width, 'errors': errors, 'metrics': {k: round(after[k]-before[k], 6) for k in ['LayoutCount','LayoutDuration','RecalcStyleCount','RecalcStyleDuration','ScriptDuration','TaskDuration']}})
        report['cases'].append(data)
        context.close()
    browser.close()
(OUT / 'probe.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
