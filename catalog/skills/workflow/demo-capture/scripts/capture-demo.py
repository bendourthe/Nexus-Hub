#!/usr/bin/env python3
"""capture-demo.py - Local visual PR-evidence capture (zero-outbound).

Detects locally-installed capture tools and the project type, then either
reports a capture plan (``--mode probe``, the default) or drives a local
capture (``--mode capture``), writing artifacts to a local ``docs/demos/``
directory. It NEVER uploads, hosts, or shares anything: the upstream
"upload / approval / hosting" surface is deliberately dropped. When a
required tool is absent the script reports which tool to install and exits 0
(graceful degradation) rather than failing hard.

Python 3 stdlib only: imports no network module and opens no connection.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Candidate binaries per capability, in preference order. Detection is a pure
# PATH lookup (shutil.which) - no tool is invoked during a probe.
RECORDERS = ["asciinema", "termtosvg"]
GIF_TOOLS = ["agg", "ffmpeg"]
BROWSERS = [
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "chrome",
    "msedge",
]

INSTALL_HINTS = {
    "recorder": "Install a terminal recorder: 'asciinema' (pip install asciinema / brew install asciinema) or 'termtosvg'.",
    "gif": "Install a GIF tool: 'agg' (asciinema gif generator) or 'ffmpeg'.",
    "browser": "Install a Chromium-family browser (chromium / google-chrome / msedge) for headless screenshots.",
}


def detect_tools() -> dict[str, list[str]]:
    """Return the available binaries per capability (PATH lookup only)."""
    return {
        "recorder": [b for b in RECORDERS if shutil.which(b)],
        "gif": [b for b in GIF_TOOLS if shutil.which(b)],
        "browser": [b for b in BROWSERS if shutil.which(b)],
    }


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def detect_project_type(root: Path) -> str:
    """Heuristically classify the project so the right capture tier is picked."""
    pkg = root / "package.json"
    if pkg.is_file():
        text = _read(pkg).lower()
        web_markers = ("react", "vue", "svelte", "next", "astro", "vite", '"dev"', '"start"')
        if any(m in text for m in web_markers):
            return "web"
        if '"bin"' in text:
            return "cli"
    for candidate in ("index.html", "public/index.html", "src/index.html"):
        if (root / candidate).is_file():
            return "web"
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = _read(pyproject).lower()
        if "[project.scripts]" in text or "console_scripts" in text:
            return "cli"
        if any(m in text for m in ("fastapi", "flask", "django")):
            return "api"
    if (root / "Cargo.toml").is_file() and "[[bin]]" in _read(root / "Cargo.toml"):
        return "cli"
    if (root / "go.mod").is_file():
        return "cli"
    if (root / "bin").is_dir():
        return "cli"
    return "generic"


def recommend_tier(project_type: str) -> tuple[str, str]:
    """Map a project type to a capture tier and the capability it needs."""
    if project_type == "web":
        return "browser-screenshots", "browser"
    if project_type in ("cli", "tui", "api"):
        return "terminal-recording", "recorder"
    return "terminal-recording", "recorder"


def build_plan(root: Path, out_dir: Path, project_type: str) -> dict:
    """Assemble the probe plan: project type, tier, available + missing tools."""
    tools = detect_tools()
    tier, needed = recommend_tier(project_type)
    missing = [cap for cap in ("recorder", "gif", "browser") if not tools[cap]]
    blocking = [] if tools.get(needed) else [needed]
    return {
        "project_type": project_type,
        "recommended_tier": tier,
        "needed_capability": needed,
        "available_tools": {k: v for k, v in tools.items() if v},
        "missing_capabilities": missing,
        "blocking_capabilities": blocking,
        "install_hints": {cap: INSTALL_HINTS[cap] for cap in missing},
        "out_dir": str(out_dir),
        "upload": "disabled (local-only by design; no upload/host/share step exists)",
    }


def _slug(name: str | None, project_type: str) -> str:
    if name:
        return "".join(c if (c.isalnum() or c in "-_") else "-" for c in name)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{project_type}-demo-{stamp}"


def do_capture(root: Path, out_dir: Path, args: argparse.Namespace) -> dict:
    """Drive a local capture for the recommended tier; degrade gracefully."""
    project_type = args.type if args.type != "auto" else detect_project_type(root)
    plan = build_plan(root, out_dir, project_type)
    tools = detect_tools()
    slug = _slug(args.name, project_type)
    result = {"plan": plan, "captured": [], "skipped": []}

    if plan["recommended_tier"] == "browser-screenshots":
        browser = args.browser or (tools["browser"][0] if tools["browser"] else None)
        if not browser or not shutil.which(browser):
            result["skipped"].append(
                {"capability": "browser", "reason": "no Chromium-family browser found", "hint": INSTALL_HINTS["browser"]}
            )
            return result
        out_png = out_dir / f"{slug}.png"
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--screenshot={out_png}",
            "--window-size=1280,800",
            args.url,
        ]
        _run(cmd, result, out_png)
        return result

    # terminal-recording tier
    recorder = args.recorder or (tools["recorder"][0] if tools["recorder"] else None)
    if not recorder or not shutil.which(recorder):
        result["skipped"].append(
            {"capability": "recorder", "reason": "no terminal recorder found", "hint": INSTALL_HINTS["recorder"]}
        )
        return result
    if recorder != "asciinema":
        result["skipped"].append(
            {"capability": "recorder", "reason": f"{recorder} capture not automated; run it manually", "hint": INSTALL_HINTS["recorder"]}
        )
        return result
    out_cast = out_dir / f"{slug}.cast"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["asciinema", "rec", "--overwrite"]
    if args.cmd:
        cmd += ["--command", args.cmd]
    cmd.append(str(out_cast))
    _run(cmd, result, out_cast)
    if out_cast.is_file() and tools["gif"]:
        out_gif = out_dir / f"{slug}.gif"
        gif_tool = tools["gif"][0]
        gif_cmd = [gif_tool, str(out_cast), str(out_gif)] if gif_tool == "agg" else None
        if gif_cmd:
            _run(gif_cmd, result, out_gif)
    return result


def _run(cmd: list[str], result: dict, artifact: Path) -> None:
    """Run a local capture command; record outcome without ever raising."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0 and artifact.is_file():
            result["captured"].append({"artifact": str(artifact), "tool": cmd[0]})
        else:
            result["skipped"].append(
                {"capability": cmd[0], "reason": (proc.stderr or "non-zero exit").strip()[:200]}
            )
    except OSError as exc:  # tool vanished between detection and run, etc.
        result["skipped"].append({"capability": cmd[0], "reason": str(exc)})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local, zero-outbound visual PR-evidence capture.")
    parser.add_argument("--mode", choices=["probe", "capture"], default="probe")
    parser.add_argument("--type", choices=["auto", "cli", "tui", "web", "api", "generic"], default="auto")
    parser.add_argument("--root", default=".", help="Project root (defaults to CWD).")
    parser.add_argument("--out", default="docs/demos", help="Local output dir (relative to root).")
    parser.add_argument("--name", default=None, help="Artifact slug (default: <type>-demo-<timestamp>).")
    parser.add_argument("--url", default="http://localhost:3000", help="URL for the web screenshot tier.")
    parser.add_argument("--cmd", default=None, help="Command to record for the terminal tier.")
    parser.add_argument("--browser", default=None, help="Override the browser binary.")
    parser.add_argument("--recorder", default=None, help="Override the terminal recorder binary.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out_dir = (root / args.out).resolve()
    project_type = args.type if args.type != "auto" else detect_project_type(root)

    if args.mode == "probe":
        print(json.dumps(build_plan(root, out_dir, project_type), indent=2))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    print(json.dumps(do_capture(root, out_dir, args), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
