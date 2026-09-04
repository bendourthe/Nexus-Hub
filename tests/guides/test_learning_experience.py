"""Observable learning-guide contracts, independent of dated illustration markup."""
from pathlib import Path
import os
import pytest

GUIDE = Path(__file__).resolve().parents[2] / 'guides/website/nexus-hub-guide.html'

@pytest.fixture(scope='module')
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if os.environ.get('NEXUS_REQUIRE_RENDER') == '1':
            pytest.fail('Guide validation requires Playwright')
        pytest.skip('Playwright is optional outside guide validation')
    with sync_playwright() as p:
        b=p.chromium.launch()
        yield b
        b.close()

@pytest.mark.parametrize('width',[320,420,1440])
def test_teaching_content_never_waits_for_animation(browser,width):
    page=browser.new_page(viewport={'width':width,'height':900})
    page.goto(GUIDE.as_uri()+'#foundations')
    roots=page.locator('#page-foundations [data-seq-root]')
    for i in range(roots.count()):
        root=roots.nth(i)
        root.evaluate('(el)=>el.scrollIntoView({block:"center"})')
        assert root.evaluate('el=>[...el.querySelectorAll("[data-seq]")].every(n=>getComputedStyle(n).opacity!=="0")')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.close()

def test_headings_keep_css_sizes_and_reading_page_is_idle(browser):
    page=browser.new_page()
    page.goto(GUIDE.as_uri()+'#foundations')
    assert page.locator('.page.active .section-title[style*="font-size"]').count()==0
    page.wait_for_timeout(100)
    assert page.evaluate('[...document.querySelectorAll("[data-seq-root]")].every(n=>!NexusSeq.state(n).running)')
    page.close()

def test_sequence_replay_pause_and_motion_preference(browser):
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.goto(GUIDE.as_uri()+'#foundations')
    root=page.locator('.page.active [data-seq-root]').first
    root.evaluate('(el)=>el.scrollIntoView({block:"center"})')
    root.evaluate('(el)=>{NexusSeq.reset(el);NexusSeq.play(el)}')
    assert root.evaluate('el=>NexusSeq.state(el).running')
    root.evaluate('el=>NexusSeq.pause(el)')
    state=root.evaluate('el=>NexusSeq.state(el)')
    page.wait_for_timeout(800)
    assert root.evaluate('el=>NexusSeq.state(el)')==state
    root.evaluate('(el)=>NexusSeq.play(el)')
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_timeout(100)
    assert not root.evaluate('el=>NexusSeq.state(el).running')
    assert root.evaluate('el=>NexusSeq.state(el).reduced')
    assert root.evaluate('el=>[...el.querySelectorAll("[data-seq]")].every(n=>getComputedStyle(n).opacity!=="0")')
    page.close()

def test_no_javascript_keeps_teaching_text(browser):
    page=browser.new_page(java_script_enabled=False,viewport={'width':420,'height':900})
    page.goto(GUIDE.as_uri()+'#foundations')
    assert page.locator('#page-foundations').is_visible()
    assert page.locator('#page-foundations').inner_text().strip()
    page.close()

@pytest.mark.parametrize('route',['home','foundations','training','cheatsheets'])
def test_idle_reading_has_no_animation_frame_loop(browser,route):
    page=browser.new_page()
    page.add_init_script('''const nativeFrame=window.requestAnimationFrame.bind(window);
      window.guideFrames=0;window.requestAnimationFrame=(fn)=>nativeFrame(t=>{window.guideFrames++;fn(t)});''')
    page.goto(GUIDE.as_uri()+'#'+route)
    page.wait_for_timeout(1000)
    before=page.evaluate('window.guideFrames')
    page.wait_for_timeout(1000)
    assert page.evaluate('window.guideFrames')-before<=1
    page.close()

def test_game_sleeps_between_routes_and_resumes(browser):
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.add_init_script('''const nativeFrame=window.requestAnimationFrame.bind(window);
      window.guideFrames=0;window.requestAnimationFrame=(fn)=>nativeFrame(t=>{window.guideFrames++;fn(t)});''')
    page.goto(GUIDE.as_uri()+'#training')
    page.locator('[data-arcade-start]').scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    page.evaluate('NexusShooter.reset("play");NexusShooter.start()')
    before=page.evaluate('guideFrames')
    page.wait_for_timeout(150)
    assert page.evaluate('guideFrames')>before+2
    page.evaluate('location.hash="foundations"')
    page.wait_for_timeout(200)
    before=page.evaluate('guideFrames')
    page.wait_for_timeout(200)
    assert page.evaluate('guideFrames')-before<=1
    page.evaluate('location.hash="training"')
    page.locator('[data-arcade-start]').scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    page.evaluate('NexusShooter.start()')
    before=page.evaluate('guideFrames')
    page.wait_for_timeout(150)
    assert page.evaluate('guideFrames')>before+2
    page.close()

@pytest.mark.parametrize('width',[420,1440])
def test_home_explains_layers_and_offers_a_visible_learning_action(browser,width):
    page=browser.new_page(viewport={'width':width,'height':900})
    page.goto(GUIDE.as_uri())
    assert page.locator('.home-layers dt').all_text_contents()==['Model','Platform','Nexus Hub']
    action=page.locator('#page-home .hero [data-go="foundations"]')
    assert action.is_visible()
    assert action.bounding_box()['y']+action.bounding_box()['height']<=900
    if width==1440:
        box=page.locator('.home-layers').bounding_box()
        assert box['y']+box['height']<=900
    text=page.locator('#page-home').inner_text()
    assert 'cannot bypass' not in text and 'world experts' not in text
    assert 'depend on the host platform' in text
    page.close()

def test_home_example_connects_request_to_checked_artifact(browser):
    page=browser.new_page()
    page.goto(GUIDE.as_uri())
    example=page.locator('#home-example')
    assert example.locator('.document-sheet').count()==2
    text=example.inner_text()
    assert 'Maya' in text and 'Friday' in text and 'Confirm the follow-up date' in text
    assert example.locator('[data-seq-play]').get_attribute('type')=='button'
    assert page.locator('.platform-rail .platform-item').count()==5
    assert page.locator('#nhg-install [data-copy]').count()>=5
    page.close()

def test_home_copy_is_shorter_without_hiding_it(browser):
    page=browser.new_page()
    page.goto(GUIDE.as_uri())
    counts=page.locator('#page-home').evaluate('''el=>{
      const clone=el.cloneNode(true);
      clone.querySelectorAll('nav,.pagenav,.progress-dots,pre,code,script,style').forEach(n=>n.remove());
      const total=clone.textContent.trim().split(/\\s+/).length;
      clone.querySelectorAll('details:not([open])').forEach(n=>n.remove());
      return {total,main:clone.textContent.trim().split(/\\s+/).length};
    }''')
    assert counts['main']<=777
    assert counts['total']<1150
    page.close()

@pytest.mark.parametrize('width',[320,420,720,1024,1440,1920])
@pytest.mark.parametrize('theme',['light','dark'])
def test_home_instruction_labels_stay_readable_and_bounded(browser,width,theme):
    page=browser.new_page(viewport={'width':width,'height':900})
    page.add_init_script(f'localStorage.setItem("portfolio-theme","{theme}")')
    page.goto(GUIDE.as_uri())
    issues=page.locator('#page-home').evaluate('''el=>[...el.querySelectorAll('.home-layers dt,.home-layers dd,.home-demo p,.home-demo dt,.home-demo dd,.home-process strong,.home-process span')].flatMap(n=>{
      const box=n.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(n);
      const text=range.getBoundingClientRect(),font=parseFloat(getComputedStyle(n).fontSize);
      return font<14 || text.right>box.right+2 || text.left<box.left-2 ? [n.textContent] : [];
    })''')
    assert issues==[]
    page.close()

def test_token_selection_preserves_exact_text_and_keyboard_access(browser):
    import json
    fixture=json.loads((GUIDE.parents[2]/'tests/guides/fixtures/meeting-note-tokens.json').read_text())
    page=browser.new_page()
    page.goto(GUIDE.as_uri()+'#foundations/tokens')
    buttons=page.locator('[data-token-index]')
    assert buttons.count()==len(fixture['pieces'])
    for i,piece in enumerate(fixture['pieces']):
        buttons.nth(i).focus()
        page.keyboard.press('Enter')
        assert page.locator('.token-source').text_content()==fixture['text']
        assert page.locator('.token-source mark').text_content()==piece
        assert page.locator('[data-token-index][aria-pressed="true"]').count()==1
        assert page.evaluate('document.activeElement.getAttribute("data-token-index")')==str(i)
    assert ''.join(fixture['pieces'])==fixture['text']
    page.close()

@pytest.mark.parametrize('width',[320,420,720,721,1024,1440,1920])
def test_foundation_lesson_text_stays_inside_its_container(browser,width):
    page=browser.new_page(viewport={'width':width,'height':900})
    page.goto(GUIDE.as_uri()+'#foundations')
    assert page.locator('[data-concept]').evaluate_all('els=>els.map(n=>n.dataset.concept)').__getitem__(slice(0,4))==['model','tokens','prompt','context']
    issues=page.locator('#page-foundations .lesson').evaluate_all('''els=>els.flatMap(el=>[...el.querySelectorAll('h2,h3,p,dt,dd,.diagram-label,.lesson-token,.budget-key span')].flatMap(n=>{
      if(!n.checkVisibility())return [];
      const box=n.getBoundingClientRect(),r=document.createRange();r.selectNodeContents(n);
      const text=r.getBoundingClientRect(),font=parseFloat(getComputedStyle(n).fontSize);
      return font<14 || text.right>box.right+2 || text.left<box.left-2 || box.right>innerWidth+1 ? [n.textContent] : [];
    }))''')
    assert issues==[]
    page.close()

def test_lessons_keep_evidence_and_model_boundaries_explicit(browser):
    page=browser.new_page()
    page.goto(GUIDE.as_uri()+'#foundations')
    model=page.locator('#fx-model-lifecycle')
    assert model.locator('.model-training').is_visible()
    assert model.locator('meter').count()==3
    assert sum(model.locator('meter').evaluate_all('els=>els.map(n=>Number(n.value))'))==100
    assert 'invented for teaching' in model.inner_text()
    assert 'does not, by itself, retrain' in model.inner_text()
    assert 'Mark missing owners or dates as unknown' in page.locator('#fx-prompts').inner_text()
    assert page.locator('#fx-context .context-tray .document-sheet').count()==2
    assert 'Meeting notes' in page.locator('.evidence-line').inner_text()
    assert 'Outside this request' in page.locator('.context-outside').inner_text()
    assert page.locator('#page-foundations img[src^="data:image/gif"]').count()==0
    page.close()

@pytest.mark.parametrize('concept,section',[('model','fx-model-lifecycle'),('tokens','fx-tokens'),('prompt','fx-prompts'),('context','fx-context')])
def test_lesson_links_reach_the_named_reading_position(browser,concept,section):
    page=browser.new_page()
    page.goto(GUIDE.as_uri()+'#foundations')
    page.locator('.lesson-nav a[href="#foundations/'+concept+'"]').click()
    page.wait_for_timeout(100)
    box=page.locator('#'+section).bounding_box()
    assert 50<=box['y']<=100
    assert page.locator('#page-foundations').is_visible()
    page.close()
