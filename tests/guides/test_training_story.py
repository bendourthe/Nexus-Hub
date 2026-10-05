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
    assert [s["id"] for s in _story()["stages"]] == re.findall(r'<section class="tr-stage" id="[^"]+" data-stage="([^"]+)"', page)


def test_both_loops_run_the_home_steps_and_loop_two_starts_at_review() -> None:
    steps = ["describe", "review", "plan", "implement", "test", "update"]
    loop1 = [s["step"] for s in _sessions() if s["loop"] == 1]
    loop2 = [s["step"] for s in _sessions() if s["loop"] == 2]
    assert loop1 == steps
    assert loop2 == steps[1:], "describe is already mapped in loop 2"
    assert all(s["id"] == f"loop{s['loop']}/{s['step']}" for s in _sessions())


def test_every_session_command_is_a_real_command_and_scope() -> None:
    """R4: prompts read like a real user's: /describe and /review bare, /plan a sentence citing their files."""
    for s in _sessions():
        cmd, arg = s["prompt"]["command"], s["prompt"]["argument"]
        path = ROOT / "catalog" / "commands" / f"{cmd.lstrip('/')}.md"
        assert path.is_file(), f"{s['id']}: {cmd} is not a catalog command"
        if arg and " " not in arg and "/" not in arg:
            scopes = re.search(r"Recognized scopes: ([^.\n]*)", path.read_text(encoding="utf-8"))
            assert scopes and f"`{arg}`" in scopes.group(1), f"{s['id']}: {arg} is not a scope of {cmd}"
    by_id = {s["id"]: s for s in _sessions()}
    for sid in ("loop1/describe", "loop1/review", "loop2/review"):
        assert by_id[sid]["prompt"]["argument"] == "", f"{sid} runs with no argument"
    plan = by_id["loop1/plan"]["prompt"]["argument"]
    assert len(plan.split()) > 12 and "docs/describe.md" in plan and "docs/review.md" in plan


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
    assert "### Not checked" in by_id["loop1/review"]["reply"], "the first review states what it could not observe"
    loop2 = by_id["loop2/review"]["reply"]
    assert "self-test" in loop2 and "### Why loop 1 missed it" in loop2
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
    page.evaluate(f"NexusTrainingPage.go('{stage}')")
    page.wait_for_function(f"NexusTrainingPage.stage() === '{stage}'")


def _open(browser, width: int = 1280, url: str | None = None, **ctx):
    context = browser.new_context(viewport={"width": width, "height": 900}, **ctx)
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto((url or TRAINING.as_uri()) + "#intro")
    page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.stage() === 'intro'")
    return context, page, errors


def test_every_session_is_an_ide_with_a_locked_prompt_and_runs_on_send(browser) -> None:
    """R4: explorer, editor, and chat; prompt, tier, and effort preset; Send gives steps, files, and a reply."""
    model_map = json.loads(MODEL_MAP.read_text(encoding="utf-8"))
    context, page, errors = _open(browser)
    try:
        for s in _sessions():
            _go(page, s["id"])
            sec = page.locator(f'section[data-stage="{s["id"]}"]')
            assert sec.locator(".tr-title").inner_text() == s["banner"]["title"]
            assert sec.locator(".tr-badge").is_visible(), "the badge is always visible"
            ide = sec.locator(".ide")
            for pane in (".ide-explorer", ".ide-editor", ".ide-chat"):
                assert ide.locator(pane).is_visible(), (s["id"], pane)
            box = ide.locator(".ide-input")
            assert box.get_attribute("aria-readonly") == "true" and box.get_attribute("contenteditable") is None
            assert box.locator(".ide-cmd").inner_text() == s["prompt"]["command"]
            assert box.locator(".ide-arg").count() == (1 if s["prompt"]["argument"] else 0)
            assert ide.locator(".ide-model-name").inner_text() == model_map["tiers"][s["badge"]["tier"]]["Anthropic"]
            assert ide.locator(".ide-chip").all_inner_texts() == [s["badge"]["tier"], s["badge"]["effort"] + " effort"]
            assert ide.locator(".ide-send").inner_text() == "Send" and ide.get_attribute("data-state") == "ready"
            page.evaluate(f"NexusTrainingPage.story().send('{s['id']}', {{ instant: true }})")
            assert ide.get_attribute("data-state") == "done"
            assert ide.locator(".ide-step").count() == len(s["steps"])
            assert ide.locator(".ide-msg--reply h3").count() >= 1, "the reply is structured"
            assert ide.locator(".ide-msg--reply li, .ide-msg--reply td").count() >= 2
            for step in s["steps"]:
                if step["kind"] in ("write", "edit"):
                    mark = ide.locator(f'.ide-file[data-path="{step["file"]}"]').get_attribute("data-status")
                    assert mark in ("created", "modified"), (s["id"], step["file"], mark)
            assert ide.locator(".ide-send").inner_text() == "Run again"
        assert not errors, errors
    finally:
        context.close()


def test_the_project_carries_forward_from_step_to_step(browser) -> None:
    context, page, _errors = _open(browser)
    try:
        files = lambda sid: page.evaluate(f"[...document.querySelectorAll('section[data-stage=\"{sid}\"] .ide-file')].map(b => b.dataset.path)")
        assert "docs/describe.md" not in files("loop1/describe")
        assert "docs/describe.md" in files("loop1/review"), "describe's file is there for review"
        assert "docs/plans/v1.0.1-damage-fix.md" in files("loop1/implement")
        assert {"CHANGELOG.md", "tests/damage.test.js"} <= set(files("loop2/review"))
    finally:
        context.close()


def test_send_runs_step_by_step_and_skip_finishes(browser) -> None:
    context, page, errors = _open(browser)
    try:
        _go(page, "loop1/describe")
        ide = page.locator('section[data-stage="loop1/describe"] .ide')
        ide.locator(".ide-send").click()
        page.wait_for_function("NexusTrainingPage.story().state('loop1/describe') === 'running'")
        page.wait_for_function("document.querySelectorAll('section[data-stage=\"loop1/describe\"] .ide-step').length >= 2")
        assert ide.locator(".ide-send").inner_text() == "Skip"
        assert ide.locator(".ide-msg--user .ide-cmd").inner_text() == "/describe"
        ide.locator(".ide-send").click()
        assert page.evaluate("NexusTrainingPage.story().state('loop1/describe')") == "done"
        assert ide.locator(".ide-msg--reply h3").count() >= 1
        assert not errors, errors
    finally:
        context.close()


def test_implement_edits_the_file_live(browser) -> None:
    context, page, _errors = _open(browser)
    try:
        _go(page, "loop1/implement")
        ide = page.locator('section[data-stage="loop1/implement"] .ide')
        ide.locator(".ide-send").click()
        page.wait_for_function("document.querySelector('section[data-stage=\"loop1/implement\"] .ide-lines li.ide-strike')", timeout=15000)
        assert ide.locator(".ide-tab[aria-selected=true]").inner_text() == "damage.js"
        page.wait_for_function("document.querySelectorAll('section[data-stage=\"loop1/implement\"] .ide-lines li.ide-type[data-op=add]').length >= 3", timeout=15000)
        page.wait_for_function("NexusTrainingPage.story().state('loop1/implement') === 'done'", timeout=30000)
        code = ide.locator(".ide-lines").inner_text()
        assert "INVULNERABLE_TICKS" in code and "TODO" not in code
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


def _variant(tmp_path: Path, mutate) -> str:
    """A throwaway copy of training.html with a modified story block."""
    html = TRAINING.read_bytes().decode("utf-8")
    m = re.search(r'(<script type="application/json" id="nh-training-story">\r?\n)(.*?)(</script>)', html, re.S)
    story = json.loads(m.group(2))
    mutate(story)
    out = tmp_path / "training.html"
    out.write_text(html[: m.start(2)] + json.dumps(story) + "\n" + html[m.end(2):], encoding="utf-8")
    return out.as_uri()


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
