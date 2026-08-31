"""Phase 4 contracts for the self-contained Asteroids training game."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE = REPO_ROOT / "guides" / "website" / "nexus-hub-guide.html"
SCENARIO = (
    REPO_ROOT
    / "docs"
    / "releases"
    / "v4"
    / "v4.4"
    / "development"
    / "asteroids-scenario.md"
)


def _training_markup() -> str:
    guide = GUIDE.read_text(encoding="utf-8")
    return guide.split('id="page-training"', 1)[-1].split(
        'id="page-cheatsheets"', 1
    )[0]


def _require_browser(render_gate: object) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        render_gate("Playwright is not installed")  # type: ignore[operator]
        return

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception as error:  # noqa: BLE001 - the render gate classifies launch failures
        render_gate(  # type: ignore[operator]
            f"Playwright Chromium cannot launch: {error}"
        )


def test_asteroids_scenario_freezes_bug_feature_and_observable_outcomes() -> None:
    assert SCENARIO.is_file(), "Phase 4 requires the decision artifact before game code"
    text = SCENARIO.read_text(encoding="utf-8")
    lower = text.lower()

    for heading in (
        "## Seeded bug",
        "## Added feature",
        "## Deterministic reproduction",
        "## Code seam",
        "## Observable states",
    ):
        assert heading in text
    assert "wrap-boundary-collision" in lower
    assert "asteroid-splitting" in lower
    assert "buggy" in lower and "fixed" in lower
    assert "hit-registration" in lower or "hit registration" in lower
    assert "bad aim" in lower or "player's aim" in lower
    assert re.search(r"\b[1-9]\d*\s+(?:steps?|seconds?)\b", lower)
    assert "logic.collides" in text
    assert "setSplittingEnabled" in text


def test_training_declares_accessible_game_controls_and_fallback() -> None:
    training = _training_markup()
    root = re.search(r'<[^>]+data-asteroids-game[^>]*>', training)
    assert root, "missing Asteroids game root"
    root_tag = root.group(0)
    assert 'data-seeded-bug="wrap-boundary-collision"' in root_tag
    assert 'data-added-feature="asteroid-splitting"' in root_tag
    assert 'tabindex="0"' in root_tag
    assert 'aria-describedby="nagInstructions"' in root_tag
    assert re.search(r'<[^>]+id="nagInstructions"[^>]*>', training)
    assert "Left and Right arrows or A and D" in training
    assert "Up Arrow or W" in training
    assert "equivalent touch controls" in training
    assert 'data-nhg-keys="self"' in training

    canvas = re.search(r'<canvas[^>]+data-asteroids-canvas[^>]*>', training)
    assert canvas and "aria-label=" in canvas.group(0)
    fallback = re.search(r'<[^>]+data-asteroids-fallback[^>]*>', training)
    assert fallback and re.search(r'role="(?:img|status)"', fallback.group(0))

    for control in ("left", "right", "thrust", "fire"):
        button = re.search(
            rf'<button[^>]+data-asteroids-control="{control}"[^>]*>', training
        )
        assert button, f"missing touch control: {control}"
        assert "aria-label=" in button.group(0)
    assert 'data-asteroids-step' in training
    assert 'data-asteroids-score' in training
    assert 'data-asteroids-lives' in training
    cue = re.search(r'<[^>]+data-asteroids-bug-cue[^>]*>', training)
    assert cue and 'aria-hidden="true"' in cue.group(0)
    live_status = re.search(r'<[^>]+data-asteroids-live-status[^>]*>', training)
    assert live_status and 'aria-live="polite"' in live_status.group(0)
    assert 'aria-atomic="true"' in live_status.group(0)
    assert not re.search(r"\shidden(?:\s|>)", live_status.group(0))


def test_asteroids_source_declares_runtime_and_pause_contracts() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    assert "window.NexusAsteroids" in guide
    for method in (
        "snapshot",
        "reset",
        "step",
        "fire",
        "setCollisionMode",
        "setSplittingEnabled",
        "pause",
        "resume",
        "collides",
        "fragmentsFor",
        "hitOutcome",
        "wrap",
    ):
        assert re.search(rf"\b{method}\b", guide), f"missing game API method: {method}"
    assert "requestAnimationFrame" in guide
    assert "visibilitychange" in guide and "document.hidden" in guide
    assert "IntersectionObserver" in guide
    assert "delta" in guide.lower()
    assert "prefers-reduced-motion" in guide


def test_asteroids_browser_logic_input_pause_and_fallback_contract(
    render_gate: object,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    guide_url = GUIDE.resolve().as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 900, "height": 940})
            context.add_init_script(
                'window.localStorage.setItem("portfolio-theme", "dark");'
            )
            external_requests: list[str] = []
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            page = context.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "request",
                lambda request: external_requests.append(request.url)
                if request.url.startswith(("http://", "https://"))
                else None,
            )

            try:
                page.goto(f"{guide_url}#training/describe", wait_until="load")
                page.wait_for_timeout(50)
                assert page.evaluate("location.hash") == "#training/describe"
                assert page.locator("[data-asteroids-game]").count() == 1
                assert page.evaluate("typeof window.NexusAsteroids") == "object"
                contract = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      return {
                        methods: [
                          "snapshot", "reset", "step", "fire",
                          "setCollisionMode", "setSplittingEnabled",
                          "pause", "resume",
                        ].filter((name) => typeof api[name] === "function"),
                        collides: typeof api.logic?.collides === "function",
                        fragmentsFor: typeof api.logic?.fragmentsFor === "function",
                        hitOutcome: typeof api.logic?.hitOutcome === "function",
                        wrap: typeof api.logic?.wrap === "function",
                        frozen: Object.isFrozen(api) && Object.isFrozen(api.logic),
                      };
                    }
                    """
                )
                assert contract["methods"] == [
                    "snapshot",
                    "reset",
                    "step",
                    "fire",
                    "setCollisionMode",
                    "setSplittingEnabled",
                    "pause",
                    "resume",
                ]
                assert contract["collides"]
                assert contract["fragmentsFor"]
                assert contract["hitOutcome"]
                assert contract["wrap"]
                assert contract["frozen"]

                collision = page.evaluate(
                    """
                    () => {
                      const hit = window.NexusAsteroids.logic.collides;
                      const bullet = {x: 2, y: 50, radius: 2};
                      const asteroid = {x: 98, y: 50, radius: 5};
                      const bounds = {width: 100, height: 100};
                      return {
                        direct: hit(
                          {x: 50, y: 50, radius: 2},
                          {x: 54, y: 50, radius: 3}, bounds, false,
                        ),
                        miss: hit(
                          {x: 10, y: 10, radius: 2},
                          {x: 50, y: 50, radius: 3}, bounds, true,
                        ),
                        buggy: hit(bullet, asteroid, bounds, false),
                        fixed: hit(bullet, asteroid, bounds, true),
                      };
                    }
                    """
                )
                assert collision == {
                    "direct": True,
                    "miss": False,
                    "buggy": False,
                    "fixed": True,
                }
                assert page.evaluate(
                    "[window.NexusAsteroids.logic.wrap(-1, 100), "
                    "window.NexusAsteroids.logic.wrap(101, 100)]"
                ) == [99, 1]

                fragment_logic = page.evaluate(
                    """
                    () => {
                      const logic = window.NexusAsteroids.logic;
                      const rock = {id: "edge-rock", x: 8, y: 180, radius: 32, size: 2};
                      return {
                        disabled: logic.hitOutcome(rock, false, 10, true),
                        tierOne: logic.hitOutcome({...rock, size: 1}, true, 10, true),
                        ordinary: logic.hitOutcome(rock, false, 10, false),
                        first: logic.hitOutcome(rock, true, 10, true),
                        repeated: logic.hitOutcome(rock, true, 10, true),
                      };
                    }
                    """
                )
                assert fragment_logic["disabled"] == {
                    "scoreDelta": 100,
                    "fragments": [],
                    "cueText": "WRAP HIT COUNTED +100",
                }
                assert fragment_logic["tierOne"] == {
                    "scoreDelta": 100,
                    "fragments": [],
                    "cueText": "WRAP HIT COUNTED +100",
                }
                assert fragment_logic["ordinary"] == {
                    "scoreDelta": 100,
                    "fragments": [],
                    "cueText": "HIT COUNTED +100",
                }
                assert fragment_logic["first"] == fragment_logic["repeated"]
                assert fragment_logic["first"]["scoreDelta"] == 100
                assert fragment_logic["first"]["cueText"] == (
                    "WRAP HIT COUNTED +100 - asteroid split"
                )
                assert fragment_logic["first"]["fragments"] == [
                    {
                        "id": "fragment-10",
                        "x": 8,
                        "y": 180,
                        "radius": 18.56,
                        "size": 1,
                        "vx": 64,
                        "vy": pytest.approx(-39.68),
                    },
                    {
                        "id": "fragment-11",
                        "x": 8,
                        "y": 180,
                        "radius": 18.56,
                        "size": 1,
                        "vx": -64,
                        "vy": pytest.approx(39.68),
                    },
                ]

                baseline = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      api.reset("wrap-boundary");
                      return api.snapshot();
                    }
                    """
                )
                assert baseline["score"] == 0
                assert baseline["lives"] == 3
                assert baseline["situation"] == "wrap-boundary"
                assert baseline["collisionMode"] == "buggy"
                assert baseline["splittingEnabled"] is False
                assert isinstance(baseline["pausedReasons"], list)
                assert isinstance(baseline["bullets"], list)
                assert isinstance(baseline["asteroids"], list)
                assert isinstance(baseline["ship"], dict)
                assert baseline["bullets"] == [
                    {
                        "id": "seed-shot",
                        "x": 624,
                        "y": 180,
                        "vx": 80,
                        "vy": 0,
                        "radius": 3,
                        "life": 1.8,
                    }
                ]
                assert baseline["asteroids"] == [
                    {
                        "id": "edge-rock",
                        "x": 8,
                        "y": 180,
                        "radius": 32,
                        "size": 2,
                        "vx": 0,
                        "vy": 0,
                    }
                ]
                assert baseline["missedWrapHits"] == 0
                assert baseline["bugCue"] is False
                assert baseline["cueText"] == ""
                canvas_paint = page.evaluate(
                    """
                    () => {
                      const canvas = document.querySelector("[data-asteroids-canvas]");
                      const pixel = canvas.getContext("2d").getImageData(0, 0, 1, 1).data;
                      return {width: canvas.width, height: canvas.height, alpha: pixel[3]};
                    }
                    """
                )
                assert canvas_paint["width"] > 0
                assert canvas_paint["height"] > 0
                assert canvas_paint["alpha"] == 255
                invalid_controls = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const rejects = (call) => {
                        try { call(); return false; } catch (error) { return true; }
                      };
                      return {
                        situation: rejects(() => api.reset("unknown")),
                        collision: rejects(() => api.setCollisionMode("unknown")),
                        splitting: rejects(() => api.setSplittingEnabled("yes")),
                      };
                    }
                    """
                )
                assert invalid_controls == {
                    "situation": True,
                    "collision": True,
                    "splitting": True,
                }

                reset_integrity = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      api.pause("reset-integrity");
                      const returned = api.reset("wrap-boundary");
                      const expected = JSON.parse(JSON.stringify(returned));
                      returned.ship.x = -999;
                      returned.bullets[0].x = -999;
                      returned.asteroids[0].x = -999;
                      returned.pausedReasons.push("forged");
                      const live = api.snapshot();
                      const repeated = api.reset("wrap-boundary");
                      api.resume("reset-integrity");
                      return {expected, live, repeated};
                    }
                    """
                )
                assert reset_integrity["live"] == reset_integrity["expected"]
                assert reset_integrity["repeated"] == reset_integrity["expected"]

                fired = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const before = api.snapshot().bullets.length;
                      api.fire();
                      const after = api.snapshot().bullets.length;
                      return {before, after};
                    }
                    """
                )
                assert fired["after"] > fired["before"]

                buggy = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      api.reset("wrap-boundary");
                      api.pause("test");
                      api.setCollisionMode("buggy");
                      api.step(1 / 60);
                      return api.snapshot();
                    }
                    """
                )
                assert buggy["score"] == 0
                assert buggy["bugCue"] is True
                assert buggy["missedWrapHits"] == 1
                assert buggy["cueText"] == (
                    "WRAP HIT MISSED - visual contact, score unchanged"
                )
                assert [rock["id"] for rock in buggy["asteroids"]] == ["edge-rock"]
                cue = page.locator("[data-asteroids-bug-cue]")
                assert cue.is_visible()
                assert cue.inner_text().strip() == buggy["cueText"]
                assert page.locator(
                    "[data-asteroids-live-status]"
                ).inner_text().strip() == buggy["cueText"]
                live_mutations = page.evaluate(
                    """
                    async () => {
                      const api = window.NexusAsteroids;
                      api.reset("wrap-boundary");
                      api.setCollisionMode("buggy");
                      const status = document.querySelector(
                        "[data-asteroids-live-status]"
                      );
                      let mutations = 0;
                      const observer = new MutationObserver((records) => {
                        mutations += records.length;
                      });
                      observer.observe(status, {
                        childList: true, characterData: true, subtree: true,
                      });
                      api.step(1 / 60);
                      for (let index = 0; index < 5; index += 1) api.step(0);
                      await new Promise((resolve) => setTimeout(resolve, 0));
                      observer.disconnect();
                      return {mutations, text: status.textContent};
                    }
                    """
                )
                assert live_mutations == {
                    "mutations": 1,
                    "text": "WRAP HIT MISSED - visual contact, score unchanged",
                }

                fixed = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      api.reset("wrap-boundary");
                      api.pause("test");
                      api.setCollisionMode("fixed");
                      api.setSplittingEnabled(false);
                      api.step(1 / 60);
                      return api.snapshot();
                    }
                    """
                )
                assert fixed["score"] == 100
                assert fixed["lives"] == 3
                assert fixed["bugCue"] is False
                assert fixed["missedWrapHits"] == 0
                assert fixed["cueText"] == "WRAP HIT COUNTED +100"
                assert fixed["asteroids"] == []
                fixed_again = page.evaluate("window.NexusAsteroids.step(1 / 60)")
                assert fixed_again["score"] == 100

                split_states = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const run = () => {
                        api.reset("wrap-boundary");
                        api.setCollisionMode("fixed");
                        api.setSplittingEnabled(true);
                        api.step(1 / 60);
                        return api.snapshot();
                      };
                      const first = run();
                      const repeated = run();
                      api.resume("test");
                      return {first, repeated};
                    }
                    """
                )
                assert split_states["first"]["score"] == 100
                assert split_states["first"]["cueText"] == (
                    "WRAP HIT COUNTED +100 - asteroid split"
                )
                assert split_states["first"]["asteroids"] == split_states["repeated"][
                    "asteroids"
                ]
                assert [rock["id"] for rock in split_states["first"]["asteroids"]] == [
                    "fragment-10",
                    "fragment-11",
                ]

                cue_contrast = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const cue = document.querySelector("[data-asteroids-bug-cue]");
                      const rgb = (value) => value.match(/[0-9.]+/g).slice(0, 3).map(Number);
                      const luminance = (value) => {
                        const channels = rgb(value).map((channel) => {
                          const scaled = channel / 255;
                          return scaled <= 0.04045
                            ? scaled / 12.92
                            : Math.pow((scaled + 0.055) / 1.055, 2.4);
                        });
                        return 0.2126 * channels[0] + 0.7152 * channels[1]
                          + 0.0722 * channels[2];
                      };
                      const ratio = () => {
                        const style = getComputedStyle(cue);
                        const first = luminance(style.color);
                        const second = luminance(style.backgroundColor);
                        return (Math.max(first, second) + 0.05)
                          / (Math.min(first, second) + 0.05);
                      };
                      const sample = (theme, mode) => {
                        document.documentElement.setAttribute("data-theme", theme);
                        api.reset("wrap-boundary");
                        api.setCollisionMode(mode);
                        api.setSplittingEnabled(false);
                        api.step(1 / 60);
                        return ratio();
                      };
                      api.pause("contrast-test");
                      const results = {
                        darkMiss: sample("dark", "buggy"),
                        darkHit: sample("dark", "fixed"),
                        lightMiss: sample("light", "buggy"),
                        lightHit: sample("light", "fixed"),
                      };
                      document.documentElement.setAttribute("data-theme", "dark");
                      api.resume("contrast-test");
                      return results;
                    }
                    """
                )
                assert min(cue_contrast.values()) >= 4.5

                ship_impact = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      api.pause("ship-test");
                      api.reset("ship-impact");
                      const first = api.step(0);
                      const repeated = api.step(0);
                      for (let index = 0; index < 32; index += 1) api.step(0.05);
                      const afterInvulnerability = api.snapshot();
                      api.resume("ship-test");
                      return {first, repeated, afterInvulnerability};
                    }
                    """
                )
                assert ship_impact["first"]["lives"] == 2
                assert ship_impact["first"]["bugCue"] is False
                assert ship_impact["first"]["cueText"] == "SHIP HIT - life lost"
                assert ship_impact["first"]["ship"]["x"] == 320
                assert ship_impact["first"]["ship"]["y"] == 270
                assert ship_impact["repeated"]["lives"] == 2
                assert ship_impact["afterInvulnerability"]["lives"] == 2

                delta_states = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const game = document.querySelector("[data-asteroids-game]");
                      const run = (steps) => {
                        api.reset("wrap-boundary");
                        api.pause("test-delta");
                        const start = api.snapshot().ship;
                        game.dispatchEvent(new KeyboardEvent("keydown", {
                          key: "ArrowUp", bubbles: true, cancelable: true,
                        }));
                        steps.forEach((delta) => api.step(delta));
                        game.dispatchEvent(new KeyboardEvent("keyup", {
                          key: "ArrowUp", bubbles: true, cancelable: true,
                        }));
                        return {start, end: api.snapshot().ship};
                      };
                      return {
                        coarse: run([1 / 20]),
                        fine: run(Array(6).fill(1 / 120)),
                      };
                    }
                    """
                )
                coarse = delta_states["coarse"]
                fine = delta_states["fine"]
                assert (coarse["end"]["x"], coarse["end"]["y"]) != (
                    coarse["start"]["x"],
                    coarse["start"]["y"],
                )
                for axis in ("x", "y", "angle"):
                    assert coarse["end"][axis] == pytest.approx(
                        fine["end"][axis], abs=0.05
                    )
                runtime_wrap = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const game = document.querySelector("[data-asteroids-game]");
                      api.reset("wrap-boundary");
                      api.setCollisionMode("fixed");
                      api.setSplittingEnabled(false);
                      api.step(1 / 60);
                      game.dispatchEvent(new KeyboardEvent("keydown", {
                        key: "ArrowUp", bubbles: true, cancelable: true,
                      }));
                      for (let index = 0; index < 20; index += 1) api.step(0.05);
                      game.dispatchEvent(new KeyboardEvent("keyup", {
                        key: "ArrowUp", bubbles: true, cancelable: true,
                      }));
                      return api.snapshot();
                    }
                    """
                )
                assert runtime_wrap["ship"]["x"] == pytest.approx(20, abs=0.05)
                assert runtime_wrap["ship"]["vx"] == pytest.approx(140, abs=0.05)
                assert 0 <= runtime_wrap["ship"]["x"] < 640
                page.evaluate("window.NexusAsteroids.resume('test-delta')")

                game = page.locator("[data-asteroids-game]")
                game.scroll_into_view_if_needed()
                touch_motion = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      api.pause("input-test");
                      api.reset("play");
                      const root = document.querySelector("[data-asteroids-game]");
                      const send = (name, type, pointerId) => {
                        root.querySelector(`[data-asteroids-control="${name}"]`)
                          .dispatchEvent(new PointerEvent(type, {
                            bubbles: true, cancelable: true, pointerType: "touch",
                            pointerId, isPrimary: true,
                          }));
                      };
                      const start = api.snapshot();
                      send("left", "pointerdown", 11);
                      api.step(1 / 30);
                      send("left", "pointerup", 11);
                      const afterLeft = api.snapshot();
                      send("right", "pointerdown", 12);
                      api.step(1 / 30);
                      send("right", "pointerup", 12);
                      const afterRight = api.snapshot();
                      send("thrust", "pointerdown", 13);
                      api.step(1 / 30);
                      send("thrust", "pointercancel", 13);
                      const afterThrust = api.snapshot();
                      api.step(1 / 30);
                      const afterCancel = api.snapshot();
                      return {
                        start, afterLeft, afterRight, afterThrust, afterCancel,
                        heldClasses: root.querySelectorAll(".nag-control.is-held").length,
                      };
                    }
                    """
                )
                assert touch_motion["afterLeft"]["ship"]["angle"] < touch_motion[
                    "start"
                ]["ship"]["angle"]
                assert touch_motion["afterRight"]["ship"]["angle"] > touch_motion[
                    "afterLeft"
                ]["ship"]["angle"]
                thrust_speed = (
                    touch_motion["afterThrust"]["ship"]["vx"] ** 2
                    + touch_motion["afterThrust"]["ship"]["vy"] ** 2
                ) ** 0.5
                cancel_speed = (
                    touch_motion["afterCancel"]["ship"]["vx"] ** 2
                    + touch_motion["afterCancel"]["ship"]["vy"] ** 2
                ) ** 0.5
                assert thrust_speed > 0
                assert cancel_speed == pytest.approx(thrust_speed, abs=0.01)
                assert touch_motion["heldClasses"] == 0
                game.focus()
                route_before = page.evaluate("location.hash")
                scroll_before = page.evaluate("window.scrollY")
                modified_shortcuts = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const root = document.querySelector("[data-asteroids-game]");
                      const before = api.snapshot();
                      const send = (key, modifiers) => {
                        const down = new KeyboardEvent("keydown", {
                          key, bubbles: true, cancelable: true, ...modifiers,
                        });
                        root.dispatchEvent(down);
                        const up = new KeyboardEvent("keyup", {
                          key, bubbles: true, cancelable: true, ...modifiers,
                        });
                        root.dispatchEvent(up);
                        return {down: down.defaultPrevented, up: up.defaultPrevented};
                      };
                      return {
                        before,
                        events: [
                          send("a", {ctrlKey: true}),
                          send("ArrowLeft", {altKey: true}),
                          send("w", {metaKey: true}),
                        ],
                        after: api.snapshot(),
                      };
                    }
                    """
                )
                assert all(
                    not event[phase]
                    for event in modified_shortcuts["events"]
                    for phase in ("down", "up")
                )
                assert modified_shortcuts["after"]["ship"] == modified_shortcuts[
                    "before"
                ]["ship"]
                assert modified_shortcuts["after"]["bullets"] == modified_shortcuts[
                    "before"
                ]["bullets"]
                assert page.evaluate("location.hash") == route_before
                assert page.evaluate("window.scrollY") == pytest.approx(
                    scroll_before, abs=1
                )
                bullets_before = page.evaluate(
                    "window.NexusAsteroids.snapshot().bullets.length"
                )
                page.keyboard.press("ArrowRight")
                page.keyboard.press("Space")
                assert page.evaluate("location.hash") == route_before
                assert page.evaluate("window.scrollY") == pytest.approx(
                    scroll_before, abs=1
                )
                assert page.evaluate(
                    "window.NexusAsteroids.snapshot().bullets.length"
                ) > bullets_before

                reset_button = page.locator('[data-asteroids-action="reset"]')
                reset_button.focus()
                page.keyboard.press("Space")
                native_button_state = page.evaluate(
                    "window.NexusAsteroids.snapshot()"
                )
                assert page.evaluate("location.hash") == route_before
                assert native_button_state["score"] == 0
                assert len(native_button_state["bullets"]) == 1

                touch_fire = page.locator('[data-asteroids-control="fire"]')
                before_touch = page.evaluate(
                    "window.NexusAsteroids.snapshot().bullets.length"
                )
                touch_fire.dispatch_event(
                    "pointerdown",
                    {"pointerType": "touch", "pointerId": 1, "isPrimary": True},
                )
                touch_fire.dispatch_event(
                    "pointercancel",
                    {"pointerType": "touch", "pointerId": 1, "isPrimary": True},
                )
                assert (
                    page.evaluate("window.NexusAsteroids.snapshot().bullets.length")
                    == before_touch
                )
                touch_fire.click()
                assert page.evaluate(
                    "window.NexusAsteroids.snapshot().bullets.length"
                ) > before_touch
                page.evaluate("window.NexusAsteroids.resume('input-test')")

                released_input = page.evaluate(
                    """
                    () => {
                      const api = window.NexusAsteroids;
                      const root = document.querySelector("[data-asteroids-game]");
                      api.pause("release-check");
                      api.reset("play");
                      root.dispatchEvent(new KeyboardEvent("keydown", {
                        key: "ArrowUp", bubbles: true, cancelable: true,
                      }));
                      window.dispatchEvent(new Event("blur"));
                      const stepped = api.step(1 / 30);
                      api.resume("release-check");
                      return stepped;
                    }
                    """
                )
                assert released_input["ship"]["vx"] == 0
                assert released_input["ship"]["vy"] == 0

                page.evaluate("window.NexusAsteroids.pause('manual-compose')")
                paused_frame = page.evaluate("window.NexusAsteroids.snapshot().frame")
                page.wait_for_timeout(120)
                assert (
                    page.evaluate("window.NexusAsteroids.snapshot().frame")
                    == paused_frame
                )
                composed_pause = page.evaluate(
                    """
                    const root = document.querySelector("[data-asteroids-game]");
                    const thrust = root.querySelector('[data-asteroids-control="thrust"]');
                    thrust.dispatchEvent(new PointerEvent("pointerdown", {
                      bubbles: true, cancelable: true, pointerType: "touch",
                      pointerId: 21, isPrimary: true,
                    }));
                    Object.defineProperty(document, "hidden", {
                      configurable: true,
                      get: () => true,
                    });
                    document.dispatchEvent(new Event("visibilitychange"));
                    const state = window.NexusAsteroids.step(1 / 30);
                    ({
                      state,
                      heldClasses: root.querySelectorAll(".nag-control.is-held").length,
                    });
                    """
                )
                assert set(composed_pause["state"]["pausedReasons"]) >= {
                    "manual-compose",
                    "document-hidden",
                }
                assert composed_pause["heldClasses"] == 0
                assert composed_pause["state"]["ship"]["vx"] == 0
                assert composed_pause["state"]["ship"]["vy"] == 0
                hidden_frame = page.evaluate("window.NexusAsteroids.snapshot().frame")
                page.wait_for_timeout(120)
                assert (
                    page.evaluate("window.NexusAsteroids.snapshot().frame")
                    == hidden_frame
                )
                page.evaluate(
                    """
                    delete document.hidden;
                    document.dispatchEvent(new Event("visibilitychange"));
                    """
                )
                assert "document-hidden" not in page.evaluate(
                    "window.NexusAsteroids.snapshot().pausedReasons"
                )
                assert "manual-compose" in page.evaluate(
                    "window.NexusAsteroids.snapshot().pausedReasons"
                )
                page.wait_for_timeout(120)
                assert (
                    page.evaluate("window.NexusAsteroids.snapshot().frame")
                    == hidden_frame
                )
                page.evaluate("window.NexusAsteroids.resume('manual-compose')")
                page.wait_for_function(
                    f"window.NexusAsteroids.snapshot().frame > {hidden_frame}",
                    timeout=3000,
                )

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_function(
                    "window.NexusAsteroids.snapshot().pausedReasons.includes('offscreen')",
                    timeout=3000,
                )
                offscreen_frame = page.evaluate(
                    "window.NexusAsteroids.snapshot().frame"
                )
                page.wait_for_timeout(120)
                assert (
                    page.evaluate("window.NexusAsteroids.snapshot().frame")
                    == offscreen_frame
                )
                game.scroll_into_view_if_needed()
                page.wait_for_function(
                    "!window.NexusAsteroids.snapshot().pausedReasons.includes('offscreen')",
                    timeout=3000,
                )

                assert not external_requests
                assert not console_errors
                assert not page_errors
            finally:
                context.close()

            reduced = browser.new_context(
                viewport={"width": 900, "height": 940},
                reduced_motion="reduce",
                has_touch=True,
            )
            reduced_requests: list[str] = []
            reduced.route(
                re.compile(r"^https?://"),
                lambda route: (reduced_requests.append(route.request.url), route.abort()),
            )
            reduced_page = reduced.new_page()
            reduced_console_errors: list[str] = []
            reduced_page_errors: list[str] = []
            reduced_page.on(
                "console",
                lambda message: reduced_console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            reduced_page.on(
                "pageerror", lambda error: reduced_page_errors.append(str(error))
            )
            try:
                reduced_page.goto(f"{guide_url}#training/describe", wait_until="load")
                game = reduced_page.locator("[data-asteroids-game]")
                assert game.count() == 1
                game.scroll_into_view_if_needed()
                state_before = reduced_page.evaluate(
                    "window.NexusAsteroids.snapshot()"
                )
                assert state_before["running"] is False
                assert "reduced-motion" in state_before["pausedReasons"]
                frame_before = state_before["frame"]
                reduced_page.wait_for_timeout(120)
                assert (
                    reduced_page.evaluate("window.NexusAsteroids.snapshot().frame")
                    == frame_before
                )
                step_button = reduced_page.locator("[data-asteroids-step]")
                fire_button = reduced_page.locator('[data-asteroids-control="fire"]')
                assert step_button.is_visible()
                assert fire_button.is_visible()

                directional_states = {}
                for control in ("left", "right", "thrust"):
                    reduced_page.evaluate("window.NexusAsteroids.reset('play')")
                    before = reduced_page.evaluate("window.NexusAsteroids.snapshot()")
                    reduced_page.locator(
                        f'[data-asteroids-control="{control}"]'
                    ).tap()
                    after = reduced_page.evaluate("window.NexusAsteroids.snapshot()")
                    assert after["frame"] == before["frame"] + 1
                    directional_states[control] = (before, after)
                assert directional_states["left"][1]["ship"]["angle"] < (
                    directional_states["left"][0]["ship"]["angle"]
                )
                assert directional_states["right"][1]["ship"]["angle"] > (
                    directional_states["right"][0]["ship"]["angle"]
                )
                assert directional_states["thrust"][1]["ship"]["vy"] < 0

                reduced_outcomes = []
                for collision_mode, splitting_enabled in (
                    ("buggy", False),
                    ("fixed", False),
                    ("fixed", True),
                ):
                    reduced_page.evaluate(
                        """
                        ([mode, splitting]) => {
                          const api = window.NexusAsteroids;
                          api.reset("wrap-boundary");
                          api.setCollisionMode(mode);
                          api.setSplittingEnabled(splitting);
                        }
                        """,
                        [collision_mode, splitting_enabled],
                    )
                    before = reduced_page.evaluate("window.NexusAsteroids.snapshot()")
                    fire_button.click()
                    after_fire = reduced_page.evaluate(
                        "window.NexusAsteroids.snapshot()"
                    )
                    step_button.click()
                    after = reduced_page.evaluate("window.NexusAsteroids.snapshot()")
                    assert after["frame"] == before["frame"] + 1
                    reduced_outcomes.append(after_fire)

                assert reduced_outcomes[0]["score"] == 0
                assert reduced_outcomes[0]["missedWrapHits"] == 2
                assert reduced_outcomes[0]["cueText"] == (
                    "WRAP HIT MISSED - visual contact, score unchanged"
                )
                assert len(reduced_outcomes[0]["asteroids"]) == 1
                assert reduced_outcomes[1]["score"] == 100
                assert reduced_outcomes[1]["cueText"] == "WRAP HIT COUNTED +100"
                assert reduced_outcomes[1]["asteroids"] == []
                assert reduced_outcomes[2]["score"] == 100
                assert reduced_outcomes[2]["cueText"] == (
                    "WRAP HIT COUNTED +100 - asteroid split"
                )
                assert len(reduced_outcomes[2]["asteroids"]) == 2

                reduced_page.emulate_media(reduced_motion="no-preference")
                reduced_page.wait_for_function(
                    "!window.NexusAsteroids.snapshot().pausedReasons.includes('reduced-motion')",
                    timeout=3000,
                )
                resumed_frame = reduced_page.evaluate(
                    "window.NexusAsteroids.snapshot().frame"
                )
                reduced_page.wait_for_function(
                    f"window.NexusAsteroids.snapshot().frame > {resumed_frame}",
                    timeout=3000,
                )
                reduced_page.emulate_media(reduced_motion="reduce")
                reduced_page.wait_for_function(
                    "window.NexusAsteroids.snapshot().pausedReasons.includes('reduced-motion')",
                    timeout=3000,
                )
                changed_frame = reduced_page.evaluate(
                    "window.NexusAsteroids.snapshot().frame"
                )
                reduced_page.wait_for_timeout(120)
                assert reduced_page.evaluate(
                    "window.NexusAsteroids.snapshot().frame"
                ) == changed_frame
                assert not reduced_requests
                assert not reduced_console_errors
                assert not reduced_page_errors
            finally:
                reduced.close()

            fallback = browser.new_context(viewport={"width": 900, "height": 940})
            fallback.add_init_script(
                """
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function (...args) {
                  if (this.hasAttribute("data-asteroids-canvas")) return null;
                  return originalGetContext.apply(this, args);
                };
                """
            )
            fallback_requests: list[str] = []
            fallback.route(re.compile(r"^https?://"), lambda route: route.abort())
            fallback_page = fallback.new_page()
            fallback_errors: list[str] = []
            fallback_console_errors: list[str] = []
            fallback_page.on(
                "pageerror", lambda error: fallback_errors.append(str(error))
            )
            fallback_page.on(
                "console",
                lambda message: fallback_console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            fallback_page.on(
                "request",
                lambda request: fallback_requests.append(request.url)
                if request.url.startswith(("http://", "https://"))
                else None,
            )
            try:
                fallback_page.goto(
                    f"{guide_url}#training/describe", wait_until="load"
                )
                fallback_copy = fallback_page.locator("[data-asteroids-fallback]")
                assert fallback_copy.is_visible()
                fallback_root = fallback_page.locator("[data-asteroids-game]")
                assert fallback_root.get_attribute("tabindex") is None
                assert fallback_root.get_attribute("aria-describedby") == "nagFallback"
                assert fallback_page.locator("#nagFallback").count() == 1
                assert fallback_root.get_attribute("aria-label") == (
                    "Static Asteroids wrap-boundary demonstration"
                )
                fallback_state = fallback_page.evaluate("window.NexusAsteroids.snapshot()")
                assert fallback_state["available"] is False
                assert fallback_state["running"] is False
                assert "canvas-unavailable" in fallback_state["pausedReasons"]
                assert "buggy collision path reports no hit" in fallback_copy.inner_text()

                fallback_page.evaluate(
                    "window.NexusAsteroids.setCollisionMode('fixed')"
                )
                assert "adds 100 points, and removes" in fallback_copy.inner_text()
                fallback_page.evaluate(
                    "window.NexusAsteroids.setSplittingEnabled(true)"
                )
                assert "two smaller fragments" in fallback_copy.inner_text()
                fallback_page.evaluate("window.NexusAsteroids.reset('play')")
                assert "three moving asteroids" in fallback_copy.inner_text()
                assert not fallback_requests
                assert not fallback_errors
                assert not fallback_console_errors
            finally:
                fallback.close()
        finally:
            browser.close()
