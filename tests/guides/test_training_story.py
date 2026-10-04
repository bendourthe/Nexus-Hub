"""v4.13.10 Phase 4: the Training story, its sessions, and the model badges.

The story lives in guides/website/src/training-story.json, is inlined into training.html by
scripts/stamp_guide_shared.py, and drives every stage. Static tests check the data; browser
tests check what a reader sees. Browser tests skip without Playwright or Chromium and fail
closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "guides" / "website"
TRAINING = WEB / "training.html"
STORY = WEB / "src" / "training-story.json"
SCHEMA = WEB / "src" / "training-story.schema.json"
RENDERER = WEB / "src" / "training-story.js"
MODEL_MAP = ROOT / "catalog" / "skills" / "ai-development" / "model-routing" / "references" / "last-known-model-map.json"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself|you're|you'll|you've|you'd)\b", re.IGNORECASE)


def _story() -> dict:
    return json.loads(STORY.read_text(encoding="utf-8"))


def _sessions() -> list[dict]:
    return [s for s in _story()["stages"] if s["kind"] == "session"]


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from _strings(item)
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)


# --- The story data ------------------------------------------------------------------


def test_story_matches_its_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(_story(), json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_story_stages_are_the_page_stages_in_order() -> None:
    page = TRAINING.read_bytes().decode("utf-8")
    assert [s["id"] for s in _story()["stages"]] == re.findall(r'<section class="page tr-stage" data-stage="([^"]+)"', page)


def test_both_loops_run_the_home_steps_and_loop_two_starts_at_review() -> None:
    steps = ["describe", "review", "plan", "implement", "test", "update"]
    loop1 = [s["step"] for s in _sessions() if s["loop"] == 1]
    loop2 = [s["step"] for s in _sessions() if s["loop"] == 2]
    assert loop1 == steps
    assert loop2 == steps[1:], "describe is already mapped in loop 2"
    assert all(s["id"] == f"loop{s['loop']}/{s['step']}" for s in _sessions())


def test_every_session_command_is_a_real_command_and_scope() -> None:
    for s in _sessions():
        name, _, scope = s["command"].partition(" ")
        path = ROOT / "catalog" / "commands" / f"{name.lstrip('/')}.md"
        assert path.is_file(), f"{s['id']}: {name} is not a catalog command"
        if scope and not re.match(r"v\d", scope):
            scopes = re.search(r"Recognized scopes: ([^.\n]*)", path.read_text(encoding="utf-8"))
            assert scopes and f"`{scope}`" in scopes.group(1), f"{s['id']}: {scope} is not a scope of {name}"


def test_badges_use_map_tiers_and_providers_are_map_columns() -> None:
    model_map = json.loads(MODEL_MAP.read_text(encoding="utf-8"))
    tiers = model_map["tiers"]
    columns = {p for row in tiers.values() for p in row}
    story = _story()
    assert set(story["providers"]) == columns
    assert story["defaultProvider"] == "Anthropic"
    for s in _sessions():
        assert s["badge"]["tier"] in tiers, s["id"]
        assert s["badge"]["effort"] in {"low", "medium", "high", "max"}, s["id"]


def test_the_two_bugs_are_told_the_way_the_game_plays_them() -> None:
    by_id = {s["id"]: s for s in _story()["stages"]}
    buggy = by_id["play-buggy"]["callout"]
    assert "first enemy hit destroys the ship" in buggy["items"][0]
    assert "One more defect hides" in buggy["hidden"]
    assert any("Not checked" == sec["heading"] for sec in by_id["loop1/review"]["session"]["sections"]), (
        "the first review states what it could not observe"
    )
    loop2 = by_id["loop2/review"]["session"]
    assert "self-test" in loop2["summary"]
    assert any(sec["heading"] == "Why loop 1 missed it" for sec in loop2["sections"])
    assert {by_id[i]["game"] for i in ("play-buggy", "play-partial", "play-fixed")} == {"buggy", "partial", "fixed"}


def test_story_text_never_addresses_the_reader_and_is_safe_in_a_script_block() -> None:
    texts = list(_strings(_story()))
    offenders = [t for t in texts if SECOND_PERSON.search(t)]
    assert not offenders, offenders[:3]
    assert not any("</" in t for t in texts), "the story sits inside a script block"


def test_renderer_only_sets_text() -> None:
    source = RENDERER.read_text(encoding="utf-8")
    assert "innerHTML" not in source and "outerHTML" not in source and "insertAdjacentHTML" not in source


# --- Browser -------------------------------------------------------------------------


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        sync_playwright = None
    if sync_playwright is None:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
    except Exception as exc:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
        pytest.skip(f"chromium is unavailable: {exc}")
    return sync_playwright


@pytest.fixture(scope="module")
def browser(playwright_mod):
    with playwright_mod() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


def _go(page, stage: str) -> None:
    page.evaluate(f"location.hash = '#{stage}'")
    page.wait_for_function(f"NexusTrainingPage.stage() === '{stage}'")


def _open(browser, width: int = 1280, url: str | None = None, **ctx):
    context = browser.new_context(viewport={"width": width, "height": 900}, **ctx)
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto((url or TRAINING.as_uri()) + "#intro")
    page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.stage() === 'intro'")
    return context, page, errors


def test_every_session_shows_its_banner_badge_and_report(browser) -> None:
    model_map = json.loads(MODEL_MAP.read_text(encoding="utf-8"))
    context, page, errors = _open(browser)
    try:
        for s in _sessions():
            _go(page, s["id"])
            sec = page.locator(f'section[data-stage="{s["id"]}"]')
            assert sec.locator(".tr-step").inner_text().lower() == s["banner"]["step"].lower()
            assert sec.locator("h1").inner_text() == s["banner"]["title"]
            assert s["banner"]["now"] in sec.locator(".tr-now").inner_text()
            badge = sec.locator(".tr-badge")
            assert badge.is_visible(), "the badge is always visible"
            values = badge.locator("dd").all_inner_texts()
            assert values == [s["badge"]["tier"], s["badge"]["effort"], model_map["tiers"][s["badge"]["tier"]]["Anthropic"]]
            assert sec.locator(".tr-cmd code").inner_text() == s["command"]
            assert sec.locator("h2.tr-section-title").count() == len(s["session"]["sections"])
            details = sec.locator("details.tr-details")
            assert details.get_attribute("open") is None, "technical details start closed"
            assert sec.locator(".tr-activity li").count() == len(s["activity"])
        assert not errors, errors
    finally:
        context.close()


def test_play_stages_show_the_callout_and_the_game(browser) -> None:
    context, page, _errors = _open(browser)
    try:
        for s in [x for x in _story()["stages"] if x["kind"] == "play"]:
            _go(page, s["id"])
            sec = page.locator(f'section[data-stage="{s["id"]}"]')
            callout = sec.locator(".tr-banner .tr-callout")
            assert callout.is_visible()
            assert s["callout"]["title"] in callout.inner_text()
            assert sec.locator(f'[data-ss-id="{s["game"]}"] .ss-canvas').is_visible()
            assert s["after"] in sec.locator(".tr-after").inner_text()
    finally:
        context.close()


def test_provider_switch_changes_every_badge_and_is_remembered(browser) -> None:
    model_map = json.loads(MODEL_MAP.read_text(encoding="utf-8"))
    context, page, _errors = _open(browser)
    try:
        _go(page, "loop1/plan")
        page.locator('section[data-stage="loop1/plan"] .tr-provider button[data-provider="OpenAI"]').click()
        shown = page.evaluate("[...document.querySelectorAll('.tr-badge-model')].map(e => [e.dataset.tierModel, e.textContent])")
        assert shown and all(text == model_map["tiers"][tier]["OpenAI"] for tier, text in shown)
        pressed = page.locator('section[data-stage="loop1/plan"] .tr-provider button[aria-pressed="true"]').inner_text()
        assert pressed == "OpenAI"
        page.reload()
        page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.story()")
        assert page.evaluate("NexusTrainingPage.story().provider()") == "OpenAI"
    finally:
        context.close()


def test_provider_switch_works_with_storage_blocked(browser) -> None:
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('blocked'); }});")
    page = context.new_page()
    try:
        page.goto(TRAINING.as_uri() + "#loop1/test")
        page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.story()")
        assert page.evaluate("NexusTrainingPage.story().provider()") == "Anthropic"
        page.locator('section[data-stage="loop1/test"] .tr-provider button[data-provider="Google"]').click()
        assert page.evaluate("NexusTrainingPage.story().provider()") == "Google"
    finally:
        context.close()


def test_no_panel_scrolls_and_the_file_panel_is_at_least_half_the_width(browser) -> None:
    context, page, _errors = _open(browser)
    try:
        for s in _sessions():
            _go(page, s["id"])
            m = page.evaluate(
                """(id) => { const sec = document.querySelector('section[data-stage="' + id + '"]');
                    const box = sec.querySelector('.container'), cs = getComputedStyle(box);
                    const content = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
                    const scrolls = [...sec.querySelectorAll('.tr-code, .tr-snippet pre, .tr-diff:not([data-long]) pre, .tr-session, .tr-files')]
                        .filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).map(e => e.className);
                    const main = sec.querySelector('.tr-main').getBoundingClientRect(), side = sec.querySelector('.tr-side').getBoundingClientRect();
                    return { content, files: sec.querySelector('.tr-files').getBoundingClientRect().width, scrolls,
                             flush: Math.abs(main.bottom - side.bottom) }; }""",
                s["id"],
            )
            assert not m["scrolls"], f"{s['id']}: {m['scrolls']}"
            assert m["files"] >= m["content"] / 2 - 1, f"{s['id']}: file panel {m['files']} of {m['content']}"
            assert m["flush"] <= 2, f"{s['id']}: the two columns end {m['flush']} px apart"
    finally:
        context.close()


def test_file_tabs_switch_by_click_and_arrow_keys(browser) -> None:
    context, page, _errors = _open(browser)
    try:
        _go(page, "loop1/describe")
        sec = page.locator('section[data-stage="loop1/describe"]')
        tabs = sec.locator('.tr-tab')
        assert tabs.count() == 2
        assert tabs.nth(1).get_attribute("aria-selected") == "true"
        assert "applyEnemyHit" in sec.locator(".tr-code").inner_text()
        tabs.nth(1).focus()
        page.keyboard.press("ArrowLeft")
        assert tabs.nth(0).get_attribute("aria-selected") == "true"
        assert "export function step" in sec.locator(".tr-code").inner_text()
        tabs.nth(1).click()
        assert tabs.nth(1).get_attribute("aria-selected") == "true"
    finally:
        context.close()


def _variant(tmp_path: Path, mutate) -> str:
    """A throwaway copy of training.html with a modified story block."""
    html = TRAINING.read_bytes().decode("utf-8")
    m = re.search(r'(<script type="application/json" id="nh-training-story">\r?\n)(.*?)(</script>)', html, re.S)
    story = json.loads(m.group(2))
    mutate(story)
    out = tmp_path / "training.html"
    out.write_text(html[: m.start(2)] + json.dumps(story) + "\n" + html[m.end(2):], encoding="utf-8")
    return out.as_uri()


def test_a_long_diff_scrolls_inside_its_own_block(browser, tmp_path: Path) -> None:
    def long_diff(story):
        stage = next(s for s in story["stages"] if s["id"] == "loop1/implement")
        stage["session"]["sections"][0]["diff"]["lines"] = [f"+line {i}" for i in range(60)]
    context, page, _errors = _open(browser, url=_variant(tmp_path, long_diff))
    try:
        _go(page, "loop1/implement")
        diff = page.locator('section[data-stage="loop1/implement"] .tr-diff')
        assert diff.get_attribute("data-long") == ""
        assert page.evaluate("(() => { const p = document.querySelector('section[data-stage=\"loop1/implement\"] .tr-diff pre'); return p.scrollHeight > p.clientHeight; })()")
    finally:
        context.close()


def test_a_broken_story_names_the_field_and_renders_nothing(browser, tmp_path: Path) -> None:
    def break_it(story):
        del story["stages"][1]["banner"]["title"]
    context, page, _errors = _open(browser, url=_variant(tmp_path, break_it))
    try:
        notice = page.locator("#trNotice")
        assert notice.is_visible()
        assert "stages[1].banner.title" in notice.inner_text()
        assert page.locator(".tr-banner").count() == 0, "a broken story renders no partial page"
        _go(page, "loop1/plan")
        assert notice.is_visible(), "the error stays visible on every stage"
    finally:
        context.close()
