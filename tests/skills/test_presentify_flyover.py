"""The /presentify --flyover route: the landing-page fly-over film.

Worth testing, without a GPU:

1. The bundle is wired: the reference, the five scripts and the scene are referenced from the
   skill or command, and the reference keeps the canonical brief and its versioned contract.
2. The scene is a pure function of time and makes no request: no clock, random or timer API in the
   curves, no external URL in any scene file, and the `window.DURATION` / `window.seek` contract.
3. The safety helpers: ffmpeg inputs can never be read as options or remote protocols, the caps
   reject oversized renders, only the loopback origin is allowed, and the server stays in its root.
4. The audio maths: the offset that lands a hit on 9.97s, the static gain bounded by the peak
   ceiling, and gap-then-hit detection on a synthetic track.
5. In a real headless browser (through `render_gate`): the camera curves never slow down the page
   or zoom in during the flight, and the hero lands as the 1018px card at y 283.

Deliberately NOT tested: a full GPU render or how the film looks. That is the route's own
check / stills / motion / verify gates, run on the user's machine.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
_SCRIPTS = _BUNDLE / "scripts"
_SCENE = _BUNDLE / "assets" / "flyover"
_REFERENCE = _BUNDLE / "references" / "landing-flyover.md"
_SKILL = _BUNDLE / "SKILL.md"
_COMMAND = _ROOT / "catalog" / "commands" / "presentify.md"
_SCRIPT_NAMES = ("flyover_capture.py", "flyover_render.py", "flyover_motion_check.py", "flyover_audio.py", "flyover_common.py")
_SCENE_NAMES = ("index.html", "film.js", "timeline.js")

sys.path.insert(0, str(_SCRIPTS))
import flyover_audio
import flyover_common as fc
import flyover_render


def _code(path: Path) -> str:
    """JS source without comments, so prose about banned APIs does not count as a use."""
    src = path.read_text(encoding="utf-8")
    return re.sub(r"(?m)^\s*//.*$", " ", re.sub(r"/\*.*?\*/", " ", src, flags=re.DOTALL))


# ---------- 1. wiring ----------

def test_every_bundled_file_exists_and_is_referenced():
    skill = _SKILL.read_text(encoding="utf-8")
    for name in _SCRIPT_NAMES:
        assert (_SCRIPTS / name).is_file()
        assert f"scripts/{name}" in skill, name
    for name in _SCENE_NAMES:
        assert (_SCENE / name).is_file()
        assert f"assets/flyover/{name}" in skill, name
    assert "references/landing-flyover.md" in skill


def test_command_dispatches_the_route():
    command = _COMMAND.read_text(encoding="utf-8")
    assert "/presentify --flyover <url>" in command
    assert "references/landing-flyover.md" in command
    for name in ("flyover_capture.py", "flyover_render.py", "flyover_motion_check.py", "flyover_audio.py"):
        assert f"scripts/{name}" in command, name


def test_reference_keeps_the_brief_and_contract():
    text = _REFERENCE.read_text(encoding="utf-8")
    assert text.isascii(), "catalog Markdown is ASCII-only"
    assert "Contract: `flyover-scene/1`" in text
    for heading in ("### Inputs", "### Direction", "### Structure", "### Build", "### Gotchas", "### Start"):
        assert heading in text, heading
    assert "Banned: cuts, crossfades" in text
    assert "stills at 0, 1.6, 2.5, 5, 6.5, 9.3 and 11 seconds before you render" in text


# ---------- 2. scene purity ----------

def test_curves_are_pure_functions_of_time():
    code = _code(_SCENE / "timeline.js")
    for banned in ("Date", "Math.random", "performance.now", "setTimeout", "setInterval", "requestAnimationFrame", "document", "window"):
        assert banned not in code, banned


def test_scene_exposes_the_contract_and_makes_no_external_request():
    film = _code(_SCENE / "film.js")
    assert "window.DURATION = DURATION" in film
    assert re.search(r"window\.seek\s*=\s*async", film)
    for name in _SCENE_NAMES:
        assert not re.search(r"https?://", _code(_SCENE / name)), f"{name} must render offline"


# ---------- 3. safety helpers ----------

def test_ffmpeg_inputs_cannot_be_options_or_protocols(tmp_path):
    with pytest.raises(ValueError):
        fc.ffmpeg_input(tmp_path / "-i.mp3")
    arg = fc.ffmpeg_input("track.mp3")
    assert arg.startswith("file:") and Path(arg[5:]).is_absolute()


def test_caps():
    assert fc.check_caps(14.5, 60, 16) == 870
    for bad in ((25, 60, 16), (14.5, 29, 16), (14.5, 60, 0), (14.5, 60, 33), (0, 60, 1)):
        with pytest.raises(fc.CapExceeded):
            fc.check_caps(*bad)


def test_only_the_loopback_origin_is_allowed():
    origin = "http://127.0.0.1:5123"
    assert fc.is_allowed(origin + "/scene/index.html", origin)
    assert fc.is_allowed("data:image/png;base64,AAAA", origin)
    for url in ("https://fonts.googleapis.com/css2", "http://127.0.0.1:5123.evil.test/x", "http://127.0.0.1:5124/scene/"):
        assert not fc.is_allowed(url, origin), url


def test_server_stays_in_its_root(tmp_path):
    root = tmp_path / "run"
    (root / "scene").mkdir(parents=True)
    (root / "scene" / "a.js").write_text("export {}", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("no", encoding="utf-8")
    server, origin = fc.serve(root)
    try:
        with urllib.request.urlopen(origin + "/scene/a.js", timeout=5) as res:
            assert res.headers["Content-Type"].startswith("text/javascript")
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(origin + "/../secret.txt", timeout=5)
    finally:
        server.shutdown()


def test_missing_ffmpeg_gives_an_install_hint_and_never_downloads(monkeypatch):
    monkeypatch.delenv("NEXUS_FFMPEG", raising=False)
    monkeypatch.setattr(fc.shutil, "which", lambda name: None)
    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", None)
    with pytest.raises(fc.ToolMissing, match="never download"):
        fc.find_ffmpeg()


def test_encoder_arguments_are_safe_and_tagged(tmp_path):
    args = flyover_render.encoder_args("ffmpeg", 60, tmp_path / "film.mp4")
    assert "-nostdin" in args and "yuv420p" in args
    assert args[args.index("-protocol_whitelist") + 1] == "file,pipe"
    assert any(a.startswith("h264_metadata=colour_primaries=1") for a in args)
    assert args[-1].startswith("file:")


# ---------- 4. audio maths ----------

def test_offset_and_gain():
    assert flyover_audio.offset_for(10.715, 9.97) == 0.745
    assert flyover_audio.gain_for(-7.9, 1.1) == -6.1  # loudness-bound
    assert flyover_audio.gain_for(-20.0, -0.5) == -0.5  # peak-bound: never above -1 dBTP
    with pytest.raises(SystemExit):
        flyover_audio.demuxer_for(Path("track.exe"))


def test_gap_then_hit_detection():
    np = pytest.importorskip("numpy")
    sr = flyover_audio.SR
    t = np.arange(int(6 * sr)) / sr
    x = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    gap = (t >= 3.80) & (t < 3.95)
    x[gap] *= 0.001
    found = flyover_audio.candidates(x, sr)
    hits = [c for c in found if c["kind"] == "gap-then-hit"]
    assert hits and abs(hits[0]["hit"] - 3.95) < 0.02, found[:3]


# ---------- 5. curves in a browser ----------

def test_camera_curves_in_a_browser(render_gate, tmp_path):
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        render_gate("Playwright is not importable")
    meta = {
        "page": {"width": 1440, "height": 7800, "bg": "rgb(7, 20, 26)"},
        "anchors": {"heroBottom": 940, "secondTitle": 1000, "footerTitle": 7300, "mockup": 400,
                    "button": {"x": 688, "y": 524, "w": 64, "h": 64}},
        "layers": [], "title": {"badge": "", "line1": "", "tail": ""},
    }
    (tmp_path / "probe.html").write_text(
        "<!doctype html><script type=module>import { makeTimeline } from './timeline.js';"
        f"window.result = makeTimeline({json.dumps(meta)}).check();</script>", encoding="utf-8")
    (tmp_path / "timeline.js").write_text((_SCENE / "timeline.js").read_text(encoding="utf-8"), encoding="utf-8")
    server, origin = fc.serve(tmp_path)
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Error as exc:
                render_gate(f"no launchable chromium ({exc.message.splitlines()[0]})")
            page = browser.new_page()
            page.goto(origin + "/probe.html")
            page.wait_for_function("window.result !== undefined", timeout=20_000)
            result = page.evaluate("window.result")
            browser.close()
    finally:
        server.shutdown()
    assert result["pass"], result
    assert result["minPageSpeed"] > -1e-6 and result["minZoomOut"] > -1e-6
    assert abs(result["card"]["x1"] - result["card"]["x0"] - 1018) < 0.5
    assert abs(result["card"]["top"] - 283) < 0.5
