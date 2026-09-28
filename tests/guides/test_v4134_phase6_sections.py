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
