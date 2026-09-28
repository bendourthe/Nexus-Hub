"""v4.13.4 Phase 5: Training actions bind to their own section roots."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


@pytest.fixture()
def page():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page(viewport={"width": 1440, "height": 940}, reduced_motion="reduce")
        errors: list[str] = []
        pg.on("pageerror", lambda error: errors.append(str(error)))
        pg.goto(GUIDE.as_uri() + "#training/describe")
        pg.wait_for_function("window.NexusTraining && window.NexusShooter.instances().length")
        yield pg, errors
        browser.close()


def test_live_section_has_one_bound_controller_and_runs_once(page):
    pg, errors = page
    assert pg.evaluate(
        """() => {
          try { window.NexusTraining.mountSection(document.querySelector('[data-nht-section="describe-review"]'), {}); }
          catch (error) { return /already mounted/.test(String(error)); }
          return false;
        }"""
    )
    pg.locator('[data-nht-section="describe-review"] [data-nht="run"]').click()
    output = pg.locator('[data-nht-section="describe-review"] [data-nht="output"]')
    assert output.locator("div").count() == 5
    assert "1:0" in pg.evaluate("window.NexusTraining.snapshot().completed")
    assert not errors, errors


def test_two_section_roots_keep_actions_and_explorer_isolated(page):
    pg, errors = page
    result = pg.evaluate(
        """() => {
          const markup = `<div data-nht="terminal"><code data-nht="command"></code><button data-nht="run">Run</button><div data-nht="output"></div><p data-nht="hint"></p></div>
            <div data-nht="tools"></div><div data-nht="artifact"><code data-nht="artifact-path"></code><p data-nht="artifact-summary"></p></div>
            <div data-nht="gate"><span data-nht="gate-status"></span><b data-nht="gate-name"></b><span data-nht="gate-prompt"></span></div>
            <div data-nht="explorer"><span data-nht="file-count"></span><div data-nht="file-tree"></div><span data-nht="file-path"></span><span data-nht="file-state"></span><div data-nht="file-body"></div></div>`;
          const records = ['first','second'].map((id) => ({id, command:'/'+id, output:[id+' reply'],
            tools:[{name:id+' tool',purpose:'local'}], artifact:{path:id+'.md',summary:id+' artifact'},
            gate:{status:'pass',name:id+' gate',prompt:id+' prompt'},
            files:[{path:id+'.md',content:id+' file',language:'text'}], focus_file:id+'.md'}));
          const roots = records.map((record) => {
            const root = document.createElement('section'); root.dataset.testSection=record.id;
            root.innerHTML=markup; document.body.appendChild(root); return root;
          });
          const controllers = roots.map((root,i) => window.NexusTraining.mountSection(root,records[i]));
          const read = root => ['terminal','tools','artifact','gate','explorer'].map(name =>
            root.querySelector('[data-nht="'+name+'"]').textContent);
          const before = read(roots[0]);
          roots[1].querySelector('[data-nht="file"]').click();
          const pendingInert = roots[1].querySelector('[data-nht="file-body"]').textContent.includes('Not created yet');
          roots[1].querySelector('[data-nht="run"]').click();
          const after = read(roots[0]), second = read(roots[1]);
          let duplicateRejected = false;
          try { window.NexusTraining.mountSection(roots[1],records[1]); }
          catch(error) { duplicateRejected = /already mounted/.test(String(error)); }
          controllers[1].dispose();
          const afterDispose = read(roots[1]);
          roots[1].querySelector('[data-nht="run"]').click();
          const disposedInert = JSON.stringify(read(roots[1])) === JSON.stringify(afterDispose);
          const remounted = window.NexusTraining.mountSection(roots[1],records[1]);
          remounted.dispose(); controllers[0].dispose(); roots.forEach(root => root.remove());
          return {firstStable:JSON.stringify(before)===JSON.stringify(after),pendingInert,
                  secondOutput:second[0].includes('second reply'),
                  secondTools:second[1].includes('second tool'),
                  secondArtifact:second[2].includes('second artifact'),
                  secondGate:second[3].includes('second gate'),
                  secondExplorer:second[4].includes('second file'),
                  duplicateRejected,disposedInert};
        }"""
    )
    assert result == {
        "firstStable": True,
        "pendingInert": True,
        "secondOutput": True,
        "secondTools": True,
        "secondArtifact": True,
        "secondGate": True,
        "secondExplorer": True,
        "duplicateRejected": True,
        "disposedInert": True,
    }
    assert not errors, errors
