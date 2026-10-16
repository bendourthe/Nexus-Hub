#!/usr/bin/env python3
"""Shared helpers for the landing-page fly-over scripts (references/landing-flyover.md).

Tool detection that never downloads, safe ffmpeg argument building, resource caps, and the
loopback-only server the scene is rendered from. Stdlib only.
"""

from __future__ import annotations

import functools
import http.server
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import ClassVar

SKILL_DIR = Path(__file__).resolve().parents[1]
SCENE_DIR = SKILL_DIR / "assets" / "flyover"
CONTRACT = "flyover-scene/1"

DURATION = 14.5
FPS_ALLOWED = (24, 25, 30, 50, 60)
MAX_DURATION = 20.0
MAX_SUBFRAMES = 32
MAX_FRAMES = int(MAX_DURATION * 60)
REVIEW_TIMES = (0.0, 1.6, 2.5, 5.0, 6.5, 9.3, 11.0)
AUDIO_DEMUXERS = {".mp3": "mp3", ".wav": "wav", ".m4a": "mov", ".aac": "aac", ".flac": "flac", ".ogg": "ogg"}

MIME = {
    ".html": "text/html", ".js": "text/javascript", ".json": "application/json",
    ".png": "image/png", ".woff2": "font/woff2", ".txt": "text/plain",
}


class ToolMissing(RuntimeError):
    """A required local tool is absent; the message carries the one-time install hint."""


class CapExceeded(ValueError):
    """A render request is outside the resource caps."""


def gpu_args() -> list[str]:
    """Launch flags that put WebGL2 on the real GPU for this platform."""
    base = ["--enable-gpu", "--ignore-gpu-blocklist"]
    if sys.platform == "win32":
        return ["--use-angle=d3d11", "--force_high_performance_gpu", *base]
    if sys.platform == "darwin":
        return ["--use-angle=metal", *base]
    return ["--use-angle=vulkan", "--enable-features=Vulkan", *base]


def isolation_args() -> list[str]:
    """Browser flags that make the render offline by construction (one layer of several)."""
    return [
        "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",
        "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    ]


def find_ffmpeg(explicit: str | None = None) -> str:
    """Resolve ffmpeg from an explicit path, NEXUS_FFMPEG, PATH, or an installed imageio-ffmpeg."""
    for candidate in (explicit, os.environ.get("NEXUS_FFMPEG")):
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    found = shutil.which("ffmpeg") or _bundled_ffmpeg()
    if found:
        return found
    raise ToolMissing(
        "ffmpeg not found. Install it once (Windows: winget install Gyan.FFmpeg; macOS: brew install "
        "ffmpeg; Linux: your package manager) or point NEXUS_FFMPEG at it. These scripts never download it."
    )


def _bundled_ffmpeg() -> str | None:
    """The binary an installed imageio-ffmpeg ships, or None when the package or binary is absent."""
    try:
        import imageio_ffmpeg  # noqa: PLC0415 - optional, lazy

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError, OSError):
        return None


def ffmpeg_input(path: str | Path) -> str:
    """An absolute `file:` input that ffmpeg can never read as an option or a remote protocol."""
    p = Path(path)
    if p.name.startswith("-"):
        raise ValueError(f"refusing a file name that starts with '-': {p.name}")
    return "file:" + str(p.resolve())


def ffmpeg_base(ffmpeg: str) -> list[str]:
    return [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y"]


def run_ffmpeg(args: list[str], timeout: float = 600) -> subprocess.CompletedProcess[str]:
    """Run ffmpeg without a shell; both pipes are drained together, so no Windows pipe deadlock."""
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, shell=False, check=False)


def check_caps(duration: float, fps: int, sub: int) -> int:
    """Validate a render request against the caps and return its frame count."""
    if not 0 < duration <= MAX_DURATION:
        raise CapExceeded(f"duration {duration}s outside (0, {MAX_DURATION}]")
    if fps not in FPS_ALLOWED:
        raise CapExceeded(f"fps {fps} not in {FPS_ALLOWED}")
    if not 1 <= sub <= MAX_SUBFRAMES:
        raise CapExceeded(f"subframes {sub} outside [1, {MAX_SUBFRAMES}]")
    frames = round(duration * fps)
    if frames > MAX_FRAMES:
        raise CapExceeded(f"{frames} frames exceeds {MAX_FRAMES}")
    return frames


def is_allowed(url: str, origin: str) -> bool:
    """True only for the scene's own loopback origin and inline data or blob URLs."""
    return url == origin or url.startswith((origin + "/", "data:", "blob:"))


class _SceneHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map: ClassVar[dict[str, str]] = {**http.server.SimpleHTTPRequestHandler.extensions_map, **MIME}

    def log_message(self, *args: object) -> None:  # quiet
        pass


def serve(root: Path) -> tuple[http.server.ThreadingHTTPServer, str]:
    """Serve `root` on an OS-assigned loopback port; the handler cannot leave that directory."""
    handler = functools.partial(_SceneHandler, directory=str(root.resolve()))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def drain(stream, sink: list[str]) -> threading.Thread:
    """Read a pipe on a thread so a long-running encoder never blocks on a full stderr buffer."""
    def pump() -> None:
        for line in iter(stream.readline, b""):
            sink.append(line.decode("utf-8", "replace"))
    thread = threading.Thread(target=pump, daemon=True)
    thread.start()
    return thread
