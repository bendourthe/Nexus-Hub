#!/usr/bin/env python3
"""
capture_screenshot.py - Best-effort headless-browser screenshot capture for the
visual-regression-testing skill.

Tier-3 bundled resource. Captures a PNG screenshot of a local HTML file or a URL
using an available headless Chromium-family browser (chrome / chromium / msedge).
It does NOT hard-depend on a browser: if none is found it prints a clear message
naming what to install and exits non-zero (code 3), so the skill falls back to
its documented CI / manual capture path instead of crashing.

By itself this launches only a local browser binary (zero-network); a URL target
obviously causes that browser to fetch the URL.

Exit codes: 0 = screenshot written, 2 = capture failed, 3 = no browser found.

Usage:
    python capture_screenshot.py index.html --out shot.png --width 1400 --height 900
    python capture_screenshot.py https://example.com --out shot.png
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_BROWSER_CANDIDATES = [
    "chrome",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "msedge",
    "microsoft-edge",
]


def _find_browser() -> str | None:
    for name in _BROWSER_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return None


def _to_target(target: str) -> str:
    if target.startswith(("http://", "https://", "file://")):
        return target
    return Path(target).resolve().as_uri()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture a headless-browser screenshot (best-effort)."
    )
    parser.add_argument("target", help="local HTML file path or URL")
    parser.add_argument(
        "--out", required=True, metavar="PNG", help="output screenshot path"
    )
    parser.add_argument("--width", type=int, default=1400)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args(argv)

    browser = _find_browser()
    if not browser:
        print(
            "error: no headless Chromium-family browser found (tried chrome / chromium / msedge). "
            "Install one, or use the skill's documented CI / manual capture path.",
            file=sys.stderr,
        )
        return 3

    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        f"--window-size={args.width},{args.height}",
        f"--screenshot={args.out}",
        _to_target(args.target),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"error: browser capture failed: {exc}", file=sys.stderr)
        return 2

    if not Path(args.out).is_file():
        print(f"error: screenshot not produced at {args.out}", file=sys.stderr)
        return 2
    print(f"captured {args.out} ({args.width}x{args.height}) via {browser}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
