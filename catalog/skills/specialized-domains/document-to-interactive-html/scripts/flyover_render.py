#!/usr/bin/env python3
"""Render the landing-page fly-over on the real GPU (references/landing-flyover.md).

RUN is the run folder: RUN/capture from flyover_capture.py, RUN/scene from `init`, output in RUN/out.

  init    RUN                      copy the bundled scene (assets/flyover/) into RUN/scene
  check   RUN [--allow-software]   renderer, fonts, and the analytic curve self-check
  stills  RUN [--times ...]        review stills, 16 motion-blur subframes each (+ contact sheet)
  preview RUN [--fps 30]           single-sample frames and camera.json for flyover_motion_check.py
  final   RUN [--fps 60 --sub 16]  H.264 MP4, frames piped straight into ffmpeg
  verify  RUN                      duration, stream, frame count, and PSNR of review frames vs stills

The scene is served from a loopback server rooted at RUN and every other request is aborted and
fails the run. Chromium and ffmpeg are detected, never downloaded.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # annotations stay strings at runtime, so Python < 3.11 never imports Self
    from typing import Self

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flyover_common as fc  # noqa: E402

DETERMINISM_JS = """(() => {
  const T0 = 1700000000000;
  let s = 0x2545f491;
  Date.now = () => T0;
  performance.now = () => 0;
  Math.random = () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return (s >>> 0) / 4294967296; };
})();"""
SOFTWARE_GL = ("swiftshader", "basic render", "llvmpipe", "software")


class Scene:
    """A browser page serving RUN/scene, isolated from the network."""

    def __init__(self, run: Path) -> None:
        self.run = run
        self.blocked: list[str] = []
        self.errors: list[str] = []

    def __enter__(self) -> Self:
        if not (self.run / "scene" / "index.html").is_file():
            raise SystemExit(f"{self.run / 'scene'} is missing; run `init {self.run}` first")
        if not (self.run / "capture" / "layers.json").is_file():
            raise SystemExit(f"{self.run / 'capture' / 'layers.json'} is missing; run flyover_capture.py first")
        try:
            from playwright.sync_api import sync_playwright  # noqa: PLC0415 - lazy
        except ImportError as exc:
            raise SystemExit("Playwright is not importable; run scripts/ensure_render_env.py for the one-time setup") from exc
        self.server, self.origin = fc.serve(self.run)
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(channel="chromium", headless=True, args=fc.gpu_args() + fc.isolation_args())
        ctx = self.browser.new_context(viewport={"width": 1440, "height": 1152}, device_scale_factor=1, service_workers="block")
        ctx.route("**/*", self._route)
        if hasattr(ctx, "route_web_socket"):
            ctx.route_web_socket("**/*", lambda ws: ws.close())
        ctx.add_init_script(DETERMINISM_JS)
        self.page = ctx.new_page()
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.goto(f"{self.origin}/scene/index.html")
        self.page.wait_for_function("window.film && window.film.ready === true", timeout=180_000)
        contract = self.page.evaluate("[typeof window.DURATION, typeof window.seek]")
        if contract != ["number", "function"]:
            raise SystemExit(f"scene breaks {fc.CONTRACT}: window.DURATION/window.seek are {contract}")
        return self

    def _route(self, route) -> None:
        url = route.request.url
        if fc.is_allowed(url, self.origin):
            route.continue_()
        else:
            self.blocked.append(url)
            route.abort()

    def frame(self, t: float, sub: int, fps: int) -> bytes:
        url = self.page.evaluate("([t, o]) => window.film.frame(t, o)", [t, {"sub": sub, "fps": fps}])
        self.assert_clean()
        return base64.b64decode(url[url.index(",") + 1:])

    def assert_clean(self) -> None:
        if self.blocked or self.errors:
            raise SystemExit(f"render aborted: blocked requests {self.blocked[:3]}, page errors {self.errors[:3]}")

    def __exit__(self, *exc: object) -> None:
        self.browser.close()
        self._pw.stop()
        self.server.shutdown()


def cmd_init(run: Path) -> int:
    dest = run / "scene"
    dest.mkdir(parents=True, exist_ok=True)
    for f in fc.SCENE_DIR.iterdir():
        shutil.copyfile(f, dest / f.name)
    (run / "out").mkdir(exist_ok=True)
    print(f"scene copied to {dest}")
    return 0


def cmd_check(run: Path, allow_software: bool) -> int:
    with Scene(run) as s:
        info = s.page.evaluate("window.film.info()")
        s.assert_clean()
    print(json.dumps(info, indent=1))
    software = any(k in info["renderer"].lower() for k in SOFTWARE_GL)
    problems = []
    if not info["check"]["pass"]:
        problems.append("curve self-check failed")
    if software and not allow_software:
        problems.append(f"software WebGL ({info['renderer']}); the brief requires the real GPU")
    if not all(info["fonts"]):
        problems.append("title fonts missing; re-run capture with --fonts or accept system fonts")
    for p in problems:
        print("FINDING:", p)
    return 1 if problems else 0


def _contact_sheet(stills: list[Path], dest: Path) -> None:
    try:
        from PIL import Image, ImageDraw  # noqa: PLC0415 - optional
    except ImportError:
        print("Pillow not importable; contact sheet skipped (the stills are complete)")
        return
    cw, ch = 720, 576
    rows = (len(stills) + 1) // 2
    sheet = Image.new("RGB", (2 * cw, rows * (ch + 30)), (24, 26, 30))
    for i, path in enumerate(stills):
        x, y = (i % 2) * cw, (i // 2) * (ch + 30)
        sheet.paste(Image.open(path).convert("RGB").resize((cw, ch)), (x, y + 30))
        ImageDraw.Draw(sheet).text((x + 8, y + 8), path.stem.replace("still_", ""), fill=(235, 238, 240))
    sheet.save(dest)


def cmd_stills(run: Path, times: list[float]) -> int:
    out = run / "out" / "stills"
    out.mkdir(parents=True, exist_ok=True)
    written = []
    with Scene(run) as s:
        for t in times:
            path = out / f"still_{t:05.2f}s.png"
            path.write_bytes(s.frame(t, 16, 60))
            written.append(path)
    _contact_sheet(written, out / "contact-sheet.png")
    print(f"{len(written)} stills in {out}")
    return 0


def cmd_preview(run: Path, fps: int) -> int:
    frames = fc.check_caps(fc.DURATION, fps, 1)
    out = run / "out" / "preview"
    out.mkdir(parents=True, exist_ok=True)
    with Scene(run) as s:
        (out / "camera.json").write_text(json.dumps(s.page.evaluate(f"window.film.cameraTrack({fps})")), encoding="utf-8")
        for i in range(frames + 1):
            (out / f"f{i:04d}.png").write_bytes(s.frame(i / fps, 1, fps))
    print(f"{frames + 1} preview frames at {fps}fps in {out}")
    return 0


def encoder_args(ffmpeg: str, fps: int, dest: Path) -> list[str]:
    """ffmpeg arguments for PNG frames on stdin -> H.264 tagged BT.709 throughout."""
    return [
        *fc.ffmpeg_base(ffmpeg), "-protocol_whitelist", "file,pipe", "-f", "image2pipe", "-framerate", str(fps), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:out_color_matrix=bt709:out_range=tv",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        # The scale filter drops primaries/transfer from the frames, so stamp them into the H.264 VUI.
        "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
        "-movflags", "+faststart", fc.ffmpeg_input(dest),
    ]


def cmd_final(run: Path, fps: int, sub: int, budget: float, ffmpeg_path: str | None) -> int:
    frames = fc.check_caps(fc.DURATION, fps, sub)
    ffmpeg = fc.find_ffmpeg(ffmpeg_path)
    dest = run / "out" / "film.mp4"
    tmp = dest.with_name("film.partial.mp4")
    started = time.monotonic()
    log: list[str] = []
    with Scene(run) as s:
        proc = subprocess.Popen(encoder_args(ffmpeg, fps, tmp), stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        pump = fc.drain(proc.stderr, log)
        try:
            for i in range(frames):
                if time.monotonic() - started > budget:
                    raise SystemExit(f"wall-clock budget of {budget:.0f}s exceeded at frame {i}/{frames}")
                proc.stdin.write(s.frame(i / fps, sub, fps))
                if i % fps == 0:
                    print(f"frame {i}/{frames}  {time.monotonic() - started:.0f}s", flush=True)
            proc.stdin.close()
            proc.wait(timeout=600)
            pump.join(timeout=5)
        except BaseException:
            proc.kill()
            tmp.unlink(missing_ok=True)
            raise
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise SystemExit("ffmpeg failed: " + "".join(log)[-800:])
    tmp.replace(dest)
    print(f"wrote {dest} in {time.monotonic() - started:.0f}s")
    return 0


def cmd_verify(run: Path, ffmpeg_path: str | None, video: str | None, floor_db: float) -> int:
    ffmpeg = fc.find_ffmpeg(ffmpeg_path)
    mp4 = Path(video) if video else run / "out" / "film.mp4"
    info = fc.run_ffmpeg([ffmpeg, "-hide_banner", "-nostdin", "-i", fc.ffmpeg_input(mp4)]).stderr
    stream = next((ln.strip() for ln in info.splitlines() if "Video:" in ln), "no video stream")
    dur = re.search(r"Duration: ([\d:.]+)", info)
    count = fc.run_ffmpeg([ffmpeg, "-hide_banner", "-nostdin", "-i", fc.ffmpeg_input(mp4), "-map", "0:v", "-f", "null", "-"]).stderr
    frames = re.findall(r"frame=\s*(\d+)", count)
    print(f"duration {dur.group(1) if dur else '?'} | frames {frames[-1] if frames else '?'}\n{stream}")
    problems = [] if "bt709" in stream and "unknown" not in stream else ["color tags are not BT.709 throughout"]
    for still in sorted((run / "out" / "stills").glob("still_*s.png")):
        t = float(still.stem.removeprefix("still_").removesuffix("s"))
        n = round(t * 60)
        res = fc.run_ffmpeg([
            *fc.ffmpeg_base(ffmpeg)[:-1], "-loglevel", "info", "-i", fc.ffmpeg_input(mp4), "-i", fc.ffmpeg_input(still),
            "-filter_complex", f"[0:v]select=eq(n\\,{n}),setpts=PTS-STARTPTS[a];[a][1:v]psnr", "-f", "null", "-"])
        m = re.search(r"average:([\d.inf]+)", res.stderr)
        psnr = float(m.group(1)) if m else float("nan")
        verdict = "ok" if psnr >= floor_db else "LOW"
        if verdict == "LOW":
            problems.append(f"frame at {t}s differs from its approved still ({psnr:.1f} dB)")
        print(f"t={t:5.2f}s frame {n:4d}: PSNR vs approved still {psnr:5.1f} dB {verdict}")
    for p in problems:
        print("FINDING:", p)
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "check", "stills", "preview", "final", "verify"):
        p = sub.add_parser(name)
        p.add_argument("run", type=Path)
        if name == "check":
            p.add_argument("--allow-software", action="store_true")
        if name == "stills":
            p.add_argument("--times", type=float, nargs="+", default=list(fc.REVIEW_TIMES))
        if name in ("preview", "final"):
            p.add_argument("--fps", type=int, default=30 if name == "preview" else 60)
        if name == "final":
            p.add_argument("--sub", type=int, default=16)
            p.add_argument("--budget", type=float, default=3600, help="wall-clock seconds before the render aborts")
        if name in ("final", "verify"):
            p.add_argument("--ffmpeg")
        if name == "verify":
            p.add_argument("--video")
            p.add_argument("--floor-db", type=float, default=38.0)
    a = ap.parse_args(argv)
    run = a.run.resolve()
    if a.cmd == "init":
        return cmd_init(run)
    if a.cmd == "check":
        return cmd_check(run, a.allow_software)
    if a.cmd == "stills":
        return cmd_stills(run, a.times)
    if a.cmd == "preview":
        return cmd_preview(run, a.fps)
    if a.cmd == "final":
        return cmd_final(run, a.fps, a.sub, a.budget, a.ffmpeg)
    return cmd_verify(run, a.ffmpeg, a.video, a.floor_db)


if __name__ == "__main__":
    sys.exit(main())
