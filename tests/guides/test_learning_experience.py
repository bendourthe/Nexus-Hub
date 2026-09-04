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
