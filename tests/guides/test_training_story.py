"""v4.13.10: the Training story, its workflow steps, and the IDE player (revision 2).

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

STEPS = ["describe", "review", "plan", "implement", "test", "update"]


def _picks(stage: dict) -> list[dict]:
    return [a for a in stage["script"] if a["do"] == "pick"]


def _prompts(stage: dict) -> list[dict]:
    return [a for a in stage["script"] if a["do"] == "prompt"]


def test_story_matches_its_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(_story(), json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_story_stages_are_the_page_stages_in_order() -> None:
    page = TRAINING.read_bytes().decode("utf-8")
    assert [s["id"] for s in _story()["stages"]] == re.findall(r'<section class="tr-stage" id="[^"]+" data-stage="([^"]+)"', page)


def test_one_pass_runs_the_six_workflow_steps_in_order() -> None:
    assert [s["step"] for s in _sessions()] == STEPS
    assert [s["id"] for s in _sessions()] == STEPS
    assert [w["step"] for w in _story()["workflow"]] == STEPS
    assert [w["command"] for w in _story()["workflow"]] == ["/" + k for k in STEPS]
    assert [s["game"] for s in _story()["stages"] if s["kind"] == "play"] == ["buggy", "fixed"]


def test_every_prompt_is_a_real_command_and_reads_like_a_person_wrote_it() -> None:
    for s in _sessions():
        for p in _prompts(s):
            cmd, arg = p["command"], p["argument"]
            path = ROOT / "catalog" / "commands" / f"{cmd.lstrip('/')}.md"
            assert path.is_file(), f"{s['id']}: {cmd} is not a catalog command"
            if arg and " " not in arg and "/" not in arg:
                scopes = re.search(r"Recognized scopes: ([^.\n]*)", path.read_text(encoding="utf-8"))
                assert scopes and f"`{arg}`" in scopes.group(1), f"{s['id']}: {arg} is not a scope of {cmd}"
    by_id = {s["id"]: s for s in _sessions()}
    for sid in ("describe", "review"):
        assert _prompts(by_id[sid])[0]["argument"] == "", f"{sid} runs with no argument"
    plan = _prompts(by_id["plan"])[0]["argument"]
    assert len(plan.split()) > 12 and "docs/describe.md" in plan and "docs/review.md" in plan


def test_every_pick_is_a_map_cell() -> None:
    tiers = json.loads(MODEL_MAP.read_text(encoding="utf-8"))["tiers"]
    for s in _sessions():
        assert _picks(s), f"{s['id']} picks a model"
        for p in _picks(s):
            assert tiers[p["tier"]][p["provider"]], (s["id"], p)


def test_one_review_finds_both_bugs_and_one_plan_fixes_both() -> None:
    by_id = {s["id"]: s for s in _story()["stages"]}
    review = " ".join(a["text"] for a in by_id["review"]["script"] if a["do"] == "reply")
    assert "P1" in review and "P2" in review and "self-test" in review
    plan = next(st for a in by_id["plan"]["script"] if a["do"] == "work" for st in a["steps"] if st["kind"] == "write")
    assert "## Phase 1" in plan["content"] and "## Phase 2" in plan["content"]
    edits = [st["file"] for a in by_id["implement"]["script"] if a["do"] == "work" for st in a["steps"] if st["kind"] == "edit"]
    assert edits == ["src/damage.js", "src/hazards.js"], "phase 1 fixes P1, phase 2 fixes P2"
    assert "Any hit destroys the ship" in by_id["play-buggy"]["notes"]["items"][0]


def test_implement_hits_the_limit_and_hands_off_to_another_provider() -> None:
    impl = next(s for s in _sessions() if s["id"] == "implement")
    kinds = [a["do"] for a in impl["script"]]
    at = kinds.index("limit")
    assert kinds[at + 1:at + 5] == ["prompt", "work", "reply", "copy"]
    assert impl["script"][at + 1]["command"] == "/handoff"
    switch = impl["script"][at + 5]
    assert switch["do"] == "pick" and switch["newchat"] and switch["provider"] != impl["script"][0]["provider"]
    assert impl["script"][at + 6]["do"] == "paste" and ".nexus-hub/handoff.md" in impl["script"][at + 6]["text"]
    later = [p["provider"] for s in _sessions() if s["id"] in ("test", "update") for p in _picks(s)]
    assert set(later) == {switch["provider"]}, "the rest of the workflow stays on the second provider"


def test_story_text_never_addresses_the_reader_or_says_loop() -> None:
    texts = list(_strings(_story()))
    offenders = [t for t in texts if SECOND_PERSON.search(t)]
    assert not offenders, offenders[:3]
    assert not [t for t in texts if re.search(r"\bloops?\b", t, re.I)], "the page follows the workflow once"
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


def _state(page, sid: str) -> dict:
    return page.evaluate(f"NexusTrainingPage.story().state('{sid}')")


def _first_time(page, sid: str, condition: str, step: int = 100) -> int | None:
    """Seek through a player and return the first time at which a DOM condition holds."""
    return page.evaluate(
        """([sid, cond, step]) => { const s = NexusTrainingPage.story(), d = s.state(sid).duration;
            const root = document.querySelector('section[data-stage="' + sid + '"]'), test = new Function('root', 'return ' + cond);
            for (let t = 0; t <= d; t += step) { s.seek(sid, t); if (test(root)) return t; } return null; }""",
        [sid, condition, step],
    )


def test_every_step_is_a_vs_code_like_ide_that_plays_to_a_structured_reply(browser) -> None:
    model_map = json.loads(MODEL_MAP.read_text(encoding="utf-8"))
    context, page, errors = _open(browser)
    try:
        for s in _sessions():
            sec = page.locator(f'section[data-stage="{s["id"]}"]')
            ide = sec.locator(".ide")
            for part in (".ide-titlebar", ".ide-activity", ".ide-explorer", ".ide-editor", ".ide-chat", ".ide-status",
                         ".ide-composer .ide-pick--model", ".ide-composer .ide-pick--effort", ".ide-send"):
                assert ide.locator(part).count() == 1, (s["id"], part)
            assert ide.locator(".ide-input").get_attribute("aria-readonly") == "true"
            page.evaluate(f"NexusTrainingPage.story().finish('{s['id']}')")
            last = _picks(s)[-1]
            name = page.evaluate(f"NexusTrainingPage.story().modelName('{model_map['tiers'][last['tier']][last['provider']]}')")
            assert ide.locator(".ide-pick--model .ide-pick-name").inner_text() == name
            assert ide.locator(".ide-pick--effort .ide-pick-name").inner_text() == last["effort"].capitalize()
            assert not re.search(r"\b(claude|gpt)-[\w.-]+", ide.inner_text()), f"{s['id']} shows a model id instead of its name"
            # After a handoff the chat starts over, so it lists only the second session's steps.
            works = [a for a in s["script"] if a["do"] == "work"]
            if any(a.get("newchat") for a in _picks(s)):
                works = works[-1:]
            assert ide.locator(".ide-step").count() == sum(len(a["steps"]) for a in works)
            assert ide.locator(".ide-reply h3").count() >= 1, "the reply is structured"
            assert sec.locator(".ide-player .ide-seek").count() == 1
        assert not errors, errors
    finally:
        context.close()


def test_model_names_read_as_products(browser) -> None:
    context, page, _ = _open(browser)
    try:
        names = page.evaluate("['claude-sonnet-5-5', 'claude-fable-5-1', 'claude-haiku-4-5', 'gpt-6.1-sol', 'gpt-6-astra'].map(NexusTrainingPage.story().modelName)")
        assert names == ["Claude Sonnet 5.5", "Claude Fable 5.1", "Claude Haiku 4.5", "GPT-6.1 Sol", "GPT-6 Astra"]
    finally:
        context.close()


def test_seeking_lands_on_the_same_frame_from_either_direction(browser) -> None:
    context, page, _ = _open(browser)
    try:
        for sid in ("review", "implement"):
            d = _state(page, sid)["duration"]
            snap = f"document.querySelector('section[data-stage=\"{sid}\"] .ide').innerText"
            page.evaluate(f"NexusTrainingPage.story().seek('{sid}', 0)")
            page.evaluate(f"NexusTrainingPage.story().seek('{sid}', {d * 0.6})")
            forward = page.evaluate(snap)
            page.evaluate(f"NexusTrainingPage.story().finish('{sid}')")
            page.evaluate(f"NexusTrainingPage.story().seek('{sid}', {d * 0.6})")
            assert page.evaluate(snap) == forward, f"{sid}: the frame depends on the direction of the seek"
    finally:
        context.close()


def test_controls_play_pause_replay_seek_and_change_speed(browser) -> None:
    context, page, errors = _open(browser)
    try:
        _go(page, "plan")
        sec = page.locator('section[data-stage="plan"]')
        page.evaluate("NexusTrainingPage.story().seek('plan', 0)")
        sec.locator(".ide-ctl--play").click()
        page.wait_for_function("NexusTrainingPage.story().state('plan').t > 300")
        assert _state(page, "plan")["playing"]
        sec.locator(".ide-ctl--play").click()
        t = _state(page, "plan")["t"]
        page.wait_for_timeout(300)
        assert not _state(page, "plan")["playing"] and _state(page, "plan")["t"] == t
        sec.locator('.ide-speed button[data-speed="2"]').click()
        assert _state(page, "plan")["speed"] == 2
        assert sec.locator('.ide-speed button[data-speed="2"]').get_attribute("aria-pressed") == "true"
        d = _state(page, "plan")["duration"]
        sec.locator(".ide-seek").fill(str(int(d * 0.5)))
        assert abs(_state(page, "plan")["t"] - d * 0.5) <= 20
        sec.locator(".ide-ctl--replay").click()
        st = _state(page, "plan")
        assert st["playing"] and st["t"] < 1500
        assert not errors, errors
    finally:
        context.close()


def test_a_step_starts_playing_when_scrolled_into_view(browser) -> None:
    context, page, _ = _open(browser)
    try:
        assert _state(page, "test")["t"] == 0
        page.locator('section[data-stage="test"] .ide').scroll_into_view_if_needed()
        page.wait_for_function("NexusTrainingPage.story().state('test').t > 0", timeout=5000)
    finally:
        context.close()


def test_reduced_motion_shows_every_step_finished_with_its_controls(browser) -> None:
    context, page, _ = _open(browser, reduced_motion="reduce")
    try:
        for s in _sessions():
            st = _state(page, s["id"])
            assert st["done"] and not st["playing"], s["id"]
            assert page.locator(f'section[data-stage="{s["id"]}"] .ide-reply h3').count() >= 1
            assert page.locator(f'section[data-stage="{s["id"]}"] .ide-player').is_visible()
    finally:
        context.close()


def test_the_handoff_plays_from_the_usage_limit_to_the_second_provider(browser) -> None:
    context, page, errors = _open(browser)
    try:
        _go(page, "implement")
        page.evaluate("NexusTrainingPage.story().seek('implement', 0)")
        assert _state(page, "implement")["provider"] == "Anthropic"
        t_limit = _first_time(page, "implement", "!!root.querySelector('.ide-limit')")
        assert t_limit is not None
        assert _state(page, "implement")["usage"] == 100
        assert page.locator('section[data-stage="implement"] .ide-usage').get_attribute("data-level") == "full"
        t_copy = _first_time(page, "implement", "[...root.querySelectorAll('.ide-copy')].some(c => c.textContent === 'Copied')")
        assert t_copy and t_copy > t_limit
        assert page.locator('section[data-stage="implement"] .ide-msg--user .ide-cmd').last.inner_text() == "/handoff"
        page.evaluate("NexusTrainingPage.story().finish('implement')")
        end = _state(page, "implement")
        assert end["provider"] == "OpenAI" and end["usageProvider"] == "OpenAI" and end["usage"] < 50
        log = page.locator('section[data-stage="implement"] .ide-log').inner_text()
        assert "Resume the task in .nexus-hub/handoff.md" in log and "Phase 2 of 2 done" in log
        assert page.locator('section[data-stage="implement"] .ide-file[data-path=".nexus-hub/handoff.md"]').count() == 1
        assert not errors, errors
    finally:
        context.close()


def test_implement_edits_the_file_live(browser) -> None:
    context, page, _ = _open(browser)
    try:
        _go(page, "implement")
        t = _first_time(page, "implement", "!!root.querySelector('.ide-lines li.ide-strike')", step=60)
        assert t is not None, "removed lines are struck out before they go"
        assert page.locator('section[data-stage="implement"] .ide-tab[aria-selected="true"]').inner_text().startswith("damage.js")
        t2 = _first_time(page, "implement", "root.querySelectorAll('.ide-lines li[data-op=add]').length >= 3", step=60)
        assert t2 and t2 > t
        page.evaluate("NexusTrainingPage.story().finish('implement')")
        page.locator('section[data-stage="implement"] .ide-file[data-path="src/damage.js"]').click()
        code = page.locator('section[data-stage="implement"] .ide-lines').inner_text()
        assert "INVULNERABLE_TICKS" in code and "TODO" not in code
    finally:
        context.close()


def test_the_project_carries_forward_from_step_to_step(browser) -> None:
    context, page, _ = _open(browser)
    try:
        def files(sid):
            return page.evaluate(f"[...document.querySelectorAll('section[data-stage=\"{sid}\"] .ide-file')].map(b => b.dataset.path)")
        for sid in ("describe", "implement", "update"):
            page.evaluate(f"NexusTrainingPage.story().seek('{sid}', 0)")
        assert "docs/describe.md" not in files("describe")
        assert {"docs/describe.md", "docs/review.md", "docs/plans/v1.1.0-damage-fix.md"} <= set(files("implement"))
        assert {"tests/damage.test.js", "tests/hazards.test.js", ".nexus-hub/handoff.md"} <= set(files("update"))
    finally:
        context.close()


def test_every_part_shows_the_workflow_strip_with_the_current_step(browser) -> None:
    context, page, _ = _open(browser)
    try:
        for st in _story()["stages"]:
            if st["kind"] == "intro":
                continue
            flow = page.locator(f'section[data-stage="{st["id"]}"] .tr-flow li')
            assert flow.count() == 6, st["id"]
            states = flow.evaluate_all("els => els.map(e => e.dataset.state)")
            if st["kind"] == "session":
                k = STEPS.index(st["step"])
                assert states == ["done"] * k + ["now"] + ["next"] * (5 - k), (st["id"], states)
            else:
                assert states == (["next"] * 6 if st["game"] == "buggy" else ["done"] * 6), (st["id"], states)
        text = page.evaluate("document.body.innerText")
        assert not re.search(r"\bloops?\b", text, re.I), "no loop wording on the page"
    finally:
        context.close()


def test_play_parts_show_plain_notes_and_the_game(browser) -> None:
    context, page, _ = _open(browser)
    try:
        for sid, tone in (("play-buggy", "bug"), ("play-fixed", "ok")):
            sec = page.locator(f'section[data-stage="{sid}"]')
            notes = sec.locator(".tr-notes")
            assert notes.get_attribute("data-tone") == tone
            assert sec.locator(".ss-host").count() == 1
            style = notes.evaluate("n => { const c = getComputedStyle(n); return [c.borderLeftWidth, c.backgroundColor]; }")
            assert style[0] == "0px" and style[1] in ("rgba(0, 0, 0, 0)", "transparent"), "plain type, not a tinted box with a side stripe"
        assert page.locator(".tr-callout, .tr-badge, .tr-provider").count() == 0
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
        del story["stages"][1]["head"]["title"]
    context, page, _errors = _open(browser, url=_variant(tmp_path, break_it))
    try:
        notice = page.locator("#trNotice")
        assert notice.is_visible()
        assert "stages[1].head.title" in notice.inner_text()
        assert page.locator(".tr-head, .ide").count() == 0, "a broken story renders no partial page"
        _go(page, "plan")
        assert notice.is_visible(), "the error stays visible on every part"
    finally:
        context.close()
