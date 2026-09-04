"""Exercise real Training controls and retain state/geometry evidence without a live assistant."""
from pathlib import Path
import argparse,json,hashlib
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[3]
GUIDE=ROOT/'guides/website/nexus-hub-guide.html'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    data=json.loads((GUIDE.parent/'example/training-scenes.json').read_text(encoding='utf-8'))
    report={'sha256':hashlib.sha256(GUIDE.read_bytes()).hexdigest(),'scenes':[],'fullscreen':[],'errors':[]}
    with sync_playwright() as p:
        b=p.chromium.launch()
        for theme,width in [('light',1440),('dark',1440),('light',420),('dark',420)]:
            page=b.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
            page.add_init_script('localStorage.setItem("portfolio-theme",'+json.dumps(theme)+')')
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.goto(GUIDE.as_uri()+'#training')
            for scene in data['scenes']:
                page.locator('[data-nht="progress"] button').nth(data['scenes'].index(scene)).click()
                before=page.evaluate('NexusTraining.snapshot()')
                assert before['runState']=='not-run'
                term=page.locator('[data-nht="terminal"]')
                term.evaluate('el=>el.scrollIntoView({block:"start",behavior:"instant"})')
                page.screenshot(path=str(args.out/f'{theme}-{width}-{scene["id"]}-before.png'))
                page.locator('[data-nht="run"]').click()
                after=page.evaluate('NexusTraining.snapshot()')
                assert after['runState']=='complete'
                assert scene['artifact']['path'] in after['filePaths']
                assert 'Gate: pass'==page.locator('[data-nht="gate-status"]').inner_text()
                term.evaluate('el=>el.scrollIntoView({block:"start",behavior:"instant"})')
                page.screenshot(path=str(args.out/f'{theme}-{width}-{scene["id"]}-after.png'))
                report['scenes'].append({'theme':theme,'width':width,'scene':scene['id'],'before':before,'after':after,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')})
            page.close()
        for width,height in [(1280,720),(1366,768),(1440,900),(1920,1080),(420,900)]:
            for fallback in [False,True]:
                page=b.new_page(viewport={'width':width,'height':height})
                page.goto(GUIDE.as_uri()+'#training')
                if fallback:page.evaluate('()=>{document.getElementById("nhTraining").requestFullscreen=()=>Promise.reject(new Error("Unavailable"));}')
                page.locator('#nhtPresent').click();page.wait_for_timeout(100)
                assert page.locator('#nhTraining').evaluate('n=>n.classList.contains("is-present")')
                page.screenshot(path=str(args.out/f'fullscreen-{width}-{height}-fallback-{fallback}.png'))
                report['fullscreen'].append({'width':width,'height':height,'fallback':fallback,'active':True,'native':page.evaluate('!!document.fullscreenElement')})
                page.locator('#nhTraining').focus();page.keyboard.press('Escape');page.wait_for_timeout(100)
                assert not page.locator('#nhTraining').evaluate('n=>n.classList.contains("is-present")')
                page.close()
        b.close()
    (args.out/'states.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'scenes':len(report['scenes']),'fullscreen':len(report['fullscreen']),'errors':len(report['errors'])}))

if __name__=='__main__':main()
