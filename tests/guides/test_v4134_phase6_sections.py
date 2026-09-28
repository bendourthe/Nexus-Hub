"""v4.13.4 Phase 6: Training is seven scoped reading sections."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
SOURCE = GUIDE.parent / "example" / "training-scenes.json"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
EXPECTED = ["game", "describe-review", "plan", "implement", "fixed-game", "compare", "presentify"]


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
        pg.goto(GUIDE.as_uri() + "#training")
        pg.wait_for_function("window.NexusShooter && window.NexusTraining")
        yield pg, errors
        browser.close()


def test_seven_sections_in_order(page):
    pg, errors = page
    ids = pg.evaluate(
        """() => [...document.querySelectorAll('#page-training section[data-nht-section]')]
            .map(section => section.getAttribute('data-nht-section'))"""
    )
    assert ids == EXPECTED, ids
    assert not errors, errors


def test_every_section_has_an_h2(page):
    pg, errors = page
    sections = pg.evaluate(
        """() => {const sections = [...document.querySelectorAll('#page-training section[data-nht-section]')];
            return {count:sections.length,missing:sections.filter(section => !section.querySelector('h2'))
                .map(section => section.getAttribute('data-nht-section'))};}"""
    )
    assert sections["count"] == 7, sections
    assert not sections["missing"], sections
    assert not errors, errors


def test_three_arcade_instances(page):
    pg, errors = page
    ids = pg.evaluate("() => window.NexusShooter.instances()")
    assert sorted(ids) == ["buggy", "featured", "fixed"], ids
    assert not errors, errors


def test_section_source_and_embedded_data_have_the_same_seven_records():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    html = GUIDE.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="nh-training-scenes">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    assert match, "embedded Training JSON is missing"
    assert json.loads(match.group(1)) == source
    assert [record["id"] for record in source["scenes"]] == EXPECTED
    assert all("stage" not in record for record in source["scenes"])
    assert [len(record["actions"]) for record in source["scenes"]] == [0, 2, 1, 1, 0, 1, 1]
    headings = re.findall(
        r'<section class="nht-section" data-nht-section="([^"]+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>',
        html,
        re.DOTALL,
    )
    assert headings == [(record["id"], record["heading"]) for record in source["scenes"]]


def test_presentation_and_deck_identifiers_are_gone():
    html = GUIDE.read_text(encoding="utf-8")
    assert ".nht.is-present" not in html
    assert 'id="nhtPresent"' not in html
    assert 'data-nht="prev"' not in html
    assert 'data-nht="next"' not in html
    assert 'data-nht="step-num"' not in html
    assert "function inPresent(" not in html
    assert "function finishPresent(" not in html


def test_narrow_sections_do_not_overflow_horizontally(page):
    pg, errors = page
    pg.set_viewport_size({"width": 420, "height": 940})
    overflow = pg.evaluate("() => document.documentElement.scrollWidth > innerWidth + 1")
    assert not overflow
    assert not errors, errors


def test_implement_finishes_the_damage_plan_before_the_comparison_feature():
    scenes = {scene["id"]: scene for scene in json.loads(SOURCE.read_text(encoding="utf-8"))["scenes"]}
    implement = scenes["implement"]
    assert implement["actions"][0]["command"] == "/implement fix-damage-handling full"
    assert [beat["name"] for beat in implement["finalPhase"]["beats"]] == [
        "Automatic review", "Known-gaps reconciliation", "Tests to green", "Update release"
    ]
    final_text = json.dumps(implement["finalPhase"]).lower()
    assert "movement" not in final_text
    assert "3 passed" in final_text
    assert "movement" in json.dumps(scenes["compare"]).lower()
    release = implement["finalPhase"]["beats"][-1]["summary"]
    assert all(term in release for term in ("integration PR", "changelog", "manifest", "tags"))


def test_buggy_game_introduces_objective_and_controls():
    html = GUIDE.read_text(encoding="utf-8")
    instructions = re.search(r'<p[^>]*id="nagInstructions"[^>]*>(.*?)</p>', html)
    assert instructions
    assert "<strong>Objective:</strong>" in instructions.group(1)
    assert all(term in instructions.group(1) for term in ("shooting enemies", "Space", "Seeded defect"))


def test_learner_can_observe_the_damage_finding_and_surviving_first_hit(page):
    pg, errors = page
    review = pg.locator('[data-nht-section="describe-review"]')
    review.locator('[data-nht-action-index="1"]').click()
    review.locator('[data-nht="run"]').click()
    assert "P1 correctness" in review.locator('[data-nht="output"]').inner_text()
    plan = pg.locator('[data-nht-section="plan"]')
    plan.locator('[data-nht="run"]').click()
    assert "first hit leaves the ship alive" in plan.locator('[data-nht="output"]').inner_text()
    result = pg.evaluate("""() => {
        const sample = id => {
            const game = window.NexusShooter.get(id);
            game.reset('enemy-hit'); game.start();
            let state = game.snapshot(), steps = 0;
            while (state.lives === 3 && state.lifecycle !== 'destroyed' && steps++ < 500) state = game.step();
            return {lives: state.lives, lifecycle: state.lifecycle};
        };
        return {buggy: sample('buggy'), fixed: sample('fixed')};
    }""")
    assert result["buggy"] == {"lives": 3, "lifecycle": "destroyed"}
    assert result["fixed"]["lives"] == 2
    assert result["fixed"]["lifecycle"] != "destroyed"
    assert not errors, errors


def test_later_commands_complete_the_evidence_chain(page):
    pg, errors = page
    describe = pg.locator('[data-nht-section="describe-review"]')
    describe.locator('[data-nht="run"]').click()
    describe.locator('[data-nht-action-index="1"]').click()
    describe.locator('[data-nht="run"]').click()
    expected = [
        ("plan", "docs/releases/v0.1/plans/fix-damage-handling.md"),
        ("implement", "tests/damage.test.js"),
        ("compare", "src/movement.js"),
        ("presentify", "shooter-briefing.html"),
    ]
    for section_id, output_file in expected:
        pg.evaluate("id => window.NexusTraining.go(id)", section_id)
        section = pg.locator(f'[data-nht-section="{section_id}"]')
        section.locator('[data-nht="run"]').click()
        assert output_file in pg.evaluate("window.NexusTraining.snapshot().filePaths")
        assert section.locator('[data-nht="output"]').inner_text().strip()
    paths = pg.evaluate("window.NexusTraining.snapshot().filePaths")
    assert all(path in paths for path in ("docs/analysis.md", "docs/review.md", "CHANGELOG.md", "tests/damage.test.js", "src/movement.js", "shooter-briefing.html"))
    assert not errors, errors


def test_training_api_selects_review_action_by_command(page):
    pg, errors = page
    result = pg.evaluate("""() => {
        window.NexusTraining.go('describe-review');
        const selected = window.NexusTraining.selectAction('describe-review', '/review');
        const completed = window.NexusTraining.run();
        return {selected, completed};
    }""")
    assert result["selected"]["sectionId"] == "describe-review"
    assert result["selected"]["actionIndex"] == 1
    assert "docs/review.md" in result["completed"]["filePaths"]
    assert pg.locator('[data-nht-section="describe-review"] [data-nht="command"]').inner_text() == "/review"
    assert not errors, errors


def test_current_section_jump_returns_to_section(page):
    pg, errors = page
    jump = pg.locator('a[data-go="training/plan"]')
    jump.click()
    pg.wait_for_function("location.hash === '#training/plan'")
    jump.click()
    assert pg.evaluate("window.scrollY") > 100
    assert pg.evaluate("document.querySelector('#training-plan').getBoundingClientRect().top") < 250
    assert not errors, errors


def test_canvas_fallback_reports_each_game_mode():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            pg = browser.new_page(reduced_motion="reduce")
            pg.add_init_script("HTMLCanvasElement.prototype.getContext = () => null")
            pg.goto(GUIDE.as_uri() + "#training")
            pg.wait_for_function("window.NexusTraining && window.NexusShooter")
            fallback = {name: pg.locator(f'[data-arcade-id="{name}"] [data-arcade-fallback]').inner_text() for name in ("buggy", "fixed", "featured")}
            assert "seeded damage bug active" in fallback["buggy"]
            assert "damage repaired" in fallback["fixed"]
            assert "vertical movement enabled" in fallback["featured"]
            assert "same state" not in " ".join(fallback.values())
        finally:
            browser.close()


def test_fixed_and_featured_games_accept_visible_controls_independently(page):
    pg, errors = page
    before = pg.evaluate("""() => Object.fromEntries(['buggy', 'fixed', 'featured'].map(id => {
        const state = window.NexusShooter.get(id).snapshot();
        return [id, {x: state.player.x, y: state.player.y, lifecycle: state.lifecycle}];
    }))""")
    fixed = pg.locator('[data-arcade-id="fixed"]')
    fixed.locator('[data-arcade-start]').click()
    fixed.locator('[data-arcade-control="left"]').dispatch_event("pointerdown")
    pg.evaluate("window.NexusShooter.get('fixed').step()")
    fixed.locator('[data-arcade-control="left"]').dispatch_event("pointerup")
    featured = pg.locator('[data-arcade-id="featured"]')
    featured.locator('[data-arcade-start]').click()
    featured.locator('[data-arcade-control="up"]').dispatch_event("pointerdown")
    pg.evaluate("window.NexusShooter.get('featured').step()")
    featured.locator('[data-arcade-control="up"]').dispatch_event("pointerup")
    after = pg.evaluate("""() => Object.fromEntries(['buggy', 'fixed', 'featured'].map(id => {
        const state = window.NexusShooter.get(id).snapshot();
        return [id, {x: state.player.x, y: state.player.y, lifecycle: state.lifecycle}];
    }))""")
    assert after["buggy"] == before["buggy"]
    assert after["fixed"]["x"] < before["fixed"]["x"]
    assert after["featured"]["y"] < before["featured"]["y"]
    assert not errors, errors


def test_animated_command_can_finish_or_switch_actions():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            pg = browser.new_page(reduced_motion="no-preference")
            pg.goto(GUIDE.as_uri() + "#training/describe-review")
            pg.wait_for_function("window.NexusTraining && window.NexusShooter")
            section = pg.locator('[data-nht-section="describe-review"]')
            run = section.locator('[data-nht="run"]')
            run.click()
            assert run.inner_text() == "Show now"
            run.click()
            assert "docs/analysis.md" in pg.evaluate("window.NexusTraining.snapshot().filePaths")
            run.click()
            section.locator('[data-nht-action-index="1"]').click()
            assert "working..." not in section.locator('[data-nht="output"]').inner_text()
            section.locator('[data-nht="run"]').click()
            section.locator('[data-nht="run"]').click()
            assert "docs/review.md" in pg.evaluate("window.NexusTraining.snapshot().filePaths")
        finally:
            browser.close()


def test_long_presentation_command_wraps_in_its_terminal(page):
    pg, errors = page
    command = pg.locator('[data-nht-section="presentify"] [data-nht="command"]')
    dimensions = command.evaluate("node => ({scroll: node.scrollWidth, client: node.clientWidth})")
    assert dimensions["scroll"] <= dimensions["client"] + 1, dimensions
    assert not errors, errors


def test_hidden_training_page_pauses_game_without_intersection_observer():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            pg = browser.new_page(reduced_motion="no-preference")
            pg.add_init_script("delete window.IntersectionObserver")
            pg.goto(GUIDE.as_uri() + "#training/game")
            pg.wait_for_function("window.NexusTraining && window.NexusShooter")
            pg.evaluate("() => {const game = window.NexusShooter.get('buggy'); game.reset('play'); game.start();}")
            pg.wait_for_timeout(300)
            assert pg.evaluate("window.NexusShooter.get('buggy').snapshot().tick") > 0
            pg.evaluate("location.hash = '#foundations'")
            pg.wait_for_function("document.body.getAttribute('data-page') === 'foundations'")
            paused = pg.evaluate("window.NexusShooter.get('buggy').snapshot()")
            pg.wait_for_timeout(250)
            after = pg.evaluate("window.NexusShooter.get('buggy').snapshot()")
            assert after["tick"] == paused["tick"]
            assert "page-hidden" in after["pauseReasons"]
            pg.evaluate("location.hash = '#training/game'")
            pg.wait_for_function("document.body.getAttribute('data-page') === 'training'")
            pg.wait_for_timeout(250)
            assert pg.evaluate("window.NexusShooter.get('buggy').snapshot().tick") > after["tick"]
        finally:
            browser.close()
