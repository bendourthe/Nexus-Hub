"""Behavioral gates for the compact Models demonstrations and comparisons."""
from pathlib import Path
import hashlib
import os
import re
import pytest

# Playwright is loaded in the fixture, never at module scope. The repo-tests group runs
# without it installed, and a module-level import turns a skippable module into a
# COLLECTION error, which aborts the whole tests/guides run instead of skipping this one
# file. Every test here takes the browser fixture, so the fixture is the only gate needed.
REQUIRE_RENDER = os.environ.get('NEXUS_REQUIRE_RENDER') == '1'
expect = None  # bound by the browser fixture; bare-name lookups need a real global


def _load_playwright():
    """Return (sync_playwright, expect), or None when the package is absent."""
    try:
        from playwright.sync_api import expect as _expect, sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        return None
    return sync_playwright, _expect

GUIDE = Path(__file__).resolve().parents[2] / 'guides/website/nexus-hub-guide.html'
MODES = ('language', 'diffusion', 'world', 'multimodal')

@pytest.fixture(scope='module')
def browser():
    global expect
    loaded = _load_playwright()
    if loaded is None:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail('NEXUS_REQUIRE_RENDER=1 but playwright is not installed')
        pytest.skip('playwright is not installed')
    sync_playwright, expect = loaded
    # The driver is entered with `with` so it tears down on every exit path, including a launch
    # failure; the hand-rolled __enter__/__exit__ pair leaked it when the driver started but the
    # browser did not. `else` keeps the yield off the failure path, so `b` is read only where it
    # is definitely bound.
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # pragma: no cover - environment dependent
            if REQUIRE_RENDER:
                pytest.fail(f'NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}')
            pytest.skip(f'chromium is unavailable: {exc}')
        else:
            try:
                yield b
            finally:
                b.close()

def open_scene(browser, width=1440, motion='reduce', theme='dark', **options):
    p = browser.new_page(viewport={'width': width, 'height': 1000}, reduced_motion=motion, **options)
    if motion == 'no-preference':
        p.clock.install(time=1000)
        p.clock.pause_at(1000)
    p.goto(GUIDE.as_uri() + '#foundations')
    p.evaluate('t=>document.documentElement.dataset.theme=t', theme)
    p.locator('.ml-lab').scroll_into_view_if_needed()
    p.mouse.move(0, 0)
    return p

@pytest.mark.parametrize('theme', ('dark', 'light'))
@pytest.mark.parametrize('width', (320, 420, 768, 1024, 1440))
def test_modes_and_comparisons_fit_without_clipping(browser, width, theme):
    p = open_scene(browser, width=width, theme=theme)
    for mode in MODES:
        p.locator(f'[data-mode={mode}]').click()
        expect(p.locator(f'#ml-{mode}')).to_be_visible()
        expect(p.locator('.ml-panel:visible')).to_have_count(1)
        geo = p.locator('#fx-model-lifecycle').evaluate('''root=>({
          overflow:document.documentElement.scrollWidth>innerWidth+1,
          clipped:[...root.querySelectorAll('*')].filter(e=>!(e instanceof SVGElement)&&e.clientWidth&&
          (e.scrollWidth>e.clientWidth+2||(getComputedStyle(e).overflow==='hidden'&&e.scrollHeight>e.clientHeight+2))).map(e=>e.className)
        })''')
        assert not geo['overflow'] and not geo['clipped'], geo
    expect(p.locator('.ml-heading .ml-tabs [role=tab]')).to_have_count(4)
    expect(p.locator('#ml-step, #ml-motion')).to_have_count(0)
    p.close()

def test_keyboard_tabs_follow_focus_and_aria_contract(browser):
    p = open_scene(browser)
    p.locator('#ml-tab-language').focus()
    for key, mode in [('ArrowRight','diffusion'),('End','multimodal'),('ArrowRight','language'),('ArrowLeft','multimodal'),('Home','language')]:
        p.keyboard.press(key)
        selected = p.locator(f'#ml-tab-{mode}')
        expect(selected).to_be_focused()
        expect(selected).to_have_attribute('aria-selected','true')
        expect(p.locator('.ml-tabs [tabindex="0"]')).to_have_count(1)
        expect(p.locator(f'#ml-{mode}')).to_be_visible()
    p.close()

def test_training_subheadings_match_and_networks_are_distinct(browser):
    p = open_scene(browser)
    styles = p.evaluate('''()=>['.ml-training-title','.ml-rl>strong'].map(s=>{const c=getComputedStyle(document.querySelector(s));return [c.fontSize,c.fontWeight,c.color,c.lineHeight]})''')
    assert styles[0] == styles[1]
    graphs = p.locator('.ml-network .ml-graph').evaluate_all('''es=>es.map(e=>({kind:e.dataset.graph,nodes:e.querySelectorAll('.ml-node').length,paths:[...e.querySelectorAll('.ml-spark')].map(p=>p.style.offsetPath)}))''')
    assert len({g['kind'] for g in graphs}) == 4
    assert all(g['nodes'] >= 25 and len(g['paths']) >= 8 and len(set(g['paths'])) > 5 for g in graphs)
    p.close()

def test_language_is_quick_then_holds_complete_answer(browser):
    p = open_scene(browser, motion='no-preference')
    p.locator('[data-mode=language]').click()
    panel = p.locator('#ml-language')
    p.clock.run_for(750)
    expect(p.locator('#ml-tokens')).to_have_text('Yeast produces')
    p.clock.run_for(2500)
    expect(panel).to_have_attribute('data-frame','5')
    expect(p.locator('#ml-tokens')).to_have_text('Yeast produces gas, making dough expand.')
    p.clock.run_for(2600)
    expect(panel).to_have_attribute('data-frame','5')
    expect(panel).not_to_have_class(re.compile('ml-playing'))
    p.clock.run_for(950)
    expect(panel).to_have_attribute('data-frame','0')
    assert sum(int(x.rstrip('%')) for x in panel.locator('.ml-prob>div>span').all_text_contents()) == 100
    p.close()

def test_diffusion_holds_clear_image_before_restarting(browser):
    p = open_scene(browser, motion='no-preference')
    p.locator('[data-mode=diffusion]').click(); panel = p.locator('#ml-diffusion')
    p.clock.run_for(2700); expect(panel).to_have_attribute('data-frame','5')
    p.clock.run_for(2800); expect(panel).to_have_attribute('data-frame','5')
    assert panel.locator('.ml-noise').evaluate('e=>+getComputedStyle(e).opacity') == 0
    p.clock.run_for(650); expect(panel).to_have_attribute('data-frame','0')
    p.close()

@pytest.mark.parametrize('mode', MODES)
def test_output_focus_and_hover_pause_each_demo(browser, mode):
    p = open_scene(browser, motion='no-preference')
    p.locator(f'[data-mode={mode}]').click(); panel=p.locator(f'#ml-{mode}')
    p.clock.run_for(800); panel.locator('.ml-board').focus(); frame=panel.get_attribute('data-frame')
    p.clock.run_for(7500); expect(panel).to_have_attribute('data-frame',frame)
    expect(panel).not_to_have_class(re.compile('ml-playing'))
    p.locator(f'[data-mode={mode}]').focus(); panel.locator('.ml-board').hover()
    p.clock.run_for(7500); expect(panel).to_have_attribute('data-frame',frame)
    p.mouse.move(0,0); p.clock.run_for(800)
    assert panel.get_attribute('data-frame') != frame
    p.close()

def test_world_camera_rotates_and_moves_through_depth_mesh(browser):
    p = open_scene(browser, motion='no-preference'); p.locator('[data-mode=world]').click()
    canvas=p.locator('.ml-room'); expect(canvas).to_have_attribute('data-ready','true')
    p.locator('[data-mode=world]').click(); p.clock.run_for(6000)
    left=[float(v) for v in canvas.get_attribute('data-camera').split(',')]
    image_left=hashlib.sha256(canvas.screenshot()).hexdigest()
    p.mouse.move(0,0)
    p.clock.run_for(6000)
    right=[float(v) for v in canvas.get_attribute('data-camera').split(',')]
    assert left[0] < -.3 and right[0] > .3
    assert left[1] < 0 < right[1] and left[2] > 0 and right[2] > 0
    assert image_left != hashlib.sha256(canvas.screenshot()).hexdigest()
    p.close()

def test_tiers_sweep_with_growing_complexity_and_provider_marks(browser):
    p=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='no-preference')
    p.clock.install(time=1000); p.clock.pause_at(1000)
    p.goto(GUIDE.as_uri()+'#foundations')
    p.locator('.ml-capability').scroll_into_view_if_needed(); p.mouse.move(0,0)
    nodes=p.locator('.ml-tier-art .ml-graph').evaluate_all('es=>es.map(e=>+e.dataset.nodes)')
    assert nodes == sorted(nodes) and len(set(nodes)) == 4
    expect(p.locator('.ml-provider .brand-copy svg')).to_have_count(8)
    for n in (1,2,3,0):
        p.clock.run_for(4250)
        expect(p.locator(f'[data-tier="{n}"]')).to_have_attribute('aria-pressed','true')
    p.close()

def test_four_effort_allowances_finish_at_different_times(browser):
    p = open_scene(browser, motion='no-preference'); p.locator('.ml-reasoning').scroll_into_view_if_needed(); p.mouse.move(0,0)
    for elapsed,completed in [(850,1),(1400,2),(2100,3),(2100,4)]:
        p.clock.run_for(elapsed)
        expect(p.locator('td[data-effort][data-done]')).to_have_count(completed)
    counts=p.locator('td[data-effort] .ml-graph').evaluate_all('es=>es.map(e=>e.dataset.nodes)')
    assert len(set(counts)) == 1
    p.close()

def test_routes_and_reduced_motion_stop_all_animations(browser):
    p = open_scene(browser, motion='no-preference'); p.locator('[data-mode=language]').click()
    expect(p.locator('#ml-language')).to_have_class(re.compile('ml-playing'))
    p.emulate_media(reduced_motion='reduce')
    expect(p.locator('#ml-language')).to_have_attribute('data-frame','5')
    expect(p.locator('#fx-model-lifecycle .ml-playing')).to_have_count(0)
    expect(p.locator('td[data-effort][data-done]')).to_have_count(4)
    p.emulate_media(reduced_motion='no-preference'); p.locator('a[href="#home"]').first.click()
    expect(p.locator('#fx-model-lifecycle .ml-playing')).to_have_count(0)
    p.close()

def test_compact_language_layout_and_offline_runtime(browser):
    p=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce'); errors=[]; requests=[]
    p.on('pageerror',lambda e:errors.append(str(e)))
    p.on('request',lambda r:requests.append(r.url) if r.url.startswith('http') else None)
    p.goto(GUIDE.as_uri()+'#foundations')
    assert p.locator('.ml-lab').bounding_box()['height'] < 480
    expect(p.locator('#ml-language .ml-prompt')).to_contain_text('Each predicted token')
    expect(p.locator('#ml-language .ml-prompt')).not_to_contain_text('Yeast')
    assert not errors and not requests
    p.close()

def test_without_javascript_explanations_remain_available(browser):
    p=browser.new_page(java_script_enabled=False,viewport={'width':420,'height':900})
    p.goto(GUIDE.as_uri()+'#foundations')
    for mode in MODES: expect(p.locator(f'#ml-{mode}')).to_be_visible()
    expect(p.locator('.ml-room-fallback')).to_be_visible()
    expect(p.locator('.ml-tabs:visible')).to_have_count(0)
    p.close()
