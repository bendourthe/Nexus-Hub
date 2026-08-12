#!/usr/bin/env python3
"""ensure_render_env.py - probe (and, only on request, provision) the local
headless-render environment the Step 9 visual-QA loop needs.

Why this exists: the visual-QA loop is only as good as its ability to actually
RENDER the page. Before v3.16.5 the loop degraded to the structural scorer
whenever no browser was importable, and it did so SILENTLY - so a run could
report a clean visual pass having never seen a pixel. Three browser-dependent
checks in this repo's own suite skipped for four minor versions for exactly that
reason (v3.15 known-gap MT-1). This script makes the environment's state
explicit and actionable instead of implicit.

It NEVER installs anything unless `--install` is passed. The install is a
one-time dev-host setup, not a per-run action, so the agent asks the user once,
up front, the first time a run finds no browser - and proceeds degraded (with a
disclosed note) if they decline.

LOCAL and OFFLINE by construction when probing: detection reads the filesystem
and attempts an import. Only `--install` reaches the network, and only for the
two commands it prints.

Usage:
    python ensure_render_env.py              # probe, print a human summary
    python ensure_render_env.py --json       # probe, emit machine-readable state
    python ensure_render_env.py --install    # consented one-time provisioning

Exit codes (distinct per state, so a caller can branch without parsing text):
    0   READY_PLAYWRIGHT     - playwright importable, bundled chromium present
    10  READY_LOCAL_BROWSER  - playwright importable, no bundled chromium, but a
                               local Chrome/Edge is usable via executable_path
    20  NEED_BROWSER         - playwright importable, no browser of any kind
    21  NEED_PLAYWRIGHT      - playwright missing, a local Chrome/Edge exists
    22  NEED_ALL             - neither playwright nor a local browser
    2   usage error
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

READY_PLAYWRIGHT = 0
READY_LOCAL_BROWSER = 10
NEED_BROWSER = 20
NEED_PLAYWRIGHT = 21
NEED_ALL = 22
USAGE_ERROR = 2

PIP_INSTALL = f"{Path(sys.executable).name} -m pip install playwright"
BROWSER_INSTALL = f"{Path(sys.executable).name} -m playwright install chromium"


def _candidate_browsers() -> list[Path]:
    """Likely Chrome / Edge locations, Windows first (this is the primary dev
    host for the skill), then macOS, then Linux."""
    candidates: list[Path] = []
    if os.name == "nt":
        roots = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        relatives = [
            r"Google\Chrome\Application\chrome.exe",
            r"Microsoft\Edge\Application\msedge.exe",
        ]
        candidates += [
            Path(root) / relative
            for root in roots
            if root
            for relative in relatives
        ]
    else:
        candidates += [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            Path("/usr/bin/google-chrome"),
            Path("/usr/bin/chromium"),
            Path("/usr/bin/chromium-browser"),
            Path("/usr/bin/microsoft-edge"),
        ]
    return candidates


def find_local_browser() -> Path | None:
    """The first existing Chrome / Edge executable, or None."""
    return next((path for path in _candidate_browsers() if path.is_file()), None)


def playwright_available() -> bool:
    """Whether `playwright` imports. Lazy by design: this script adds no
    dependency, and its absence is a reportable state rather than a crash."""
    try:
        import playwright  # noqa: F401
    except Exception:  # noqa: BLE001 - probe must classify, never crash: any import failure is a state
        return False
    return True


def bundled_chromium_available() -> bool:
    """Whether Playwright can actually launch its bundled chromium.

    Launching is the only honest test. A cache DIRECTORY can exist while the
    build inside it is incomplete or mismatched with the installed Playwright,
    which presents as a launch failure at the worst possible moment - inside the
    QA loop, where it degrades silently. Paying one real launch here converts
    that into an explicit state.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:  # noqa: BLE001 - same - an unimportable playwright is NEED_PLAYWRIGHT, not an error
        return False
    try:
        with sync_playwright() as play:
            browser = play.chromium.launch()
            browser.close()
    except Exception:  # noqa: BLE001 - a launch can fail many ways; all of them mean 'not launchable'
        return False
    return True


def probe() -> dict[str, Any]:
    """Resolve the environment state without changing anything."""
    has_playwright = playwright_available()
    local_browser = find_local_browser()
    has_chromium = bundled_chromium_available() if has_playwright else False

    if has_playwright and has_chromium:
        state, code = "READY_PLAYWRIGHT", READY_PLAYWRIGHT
    elif has_playwright and local_browser is not None:
        state, code = "READY_LOCAL_BROWSER", READY_LOCAL_BROWSER
    elif has_playwright:
        state, code = "NEED_BROWSER", NEED_BROWSER
    elif local_browser is not None:
        state, code = "NEED_PLAYWRIGHT", NEED_PLAYWRIGHT
    else:
        state, code = "NEED_ALL", NEED_ALL

    remedy: list[str] = []
    if not has_playwright:
        remedy.append(PIP_INSTALL)
    if not has_chromium and local_browser is None:
        remedy.append(BROWSER_INSTALL)

    return {
        "state": state,
        "exit_code": code,
        "ready": code in (READY_PLAYWRIGHT, READY_LOCAL_BROWSER),
        "playwright_importable": has_playwright,
        "bundled_chromium_launchable": has_chromium,
        "local_browser": str(local_browser) if local_browser else None,
        "remedy": remedy,
        "note": _NOTES[state],
    }


_NOTES = {
    "READY_PLAYWRIGHT": (
        "Bundled chromium launches. The Step 9 loop can render, screenshot, and "
        "grade at full fidelity."
    ),
    "READY_LOCAL_BROWSER": (
        "No bundled chromium, but a local Chrome/Edge is present and Playwright "
        "can drive it via executable_path. Render at full fidelity; note the "
        "browser build is the system one, not Playwright's pinned revision."
    ),
    "NEED_BROWSER": (
        "Playwright is installed but has no browser to drive. One consented "
        "command fixes it; until then the loop must degrade and DISCLOSE it."
    ),
    "NEED_PLAYWRIGHT": (
        "A local Chrome/Edge exists but Playwright is not installed, so nothing "
        "can drive it headlessly. One consented pip install fixes it."
    ),
    "NEED_ALL": (
        "Neither Playwright nor a local Chrome/Edge. The loop must degrade to the "
        "structural scorer and DISCLOSE the degradation in its final report."
    ),
}


def install(dry_run: bool = False) -> int:
    """Run the consented one-time provisioning. Only ever called via --install."""
    state = probe()
    if state["ready"]:
        print(f"Already usable ({state['state']}); nothing to install.")
        return int(state["exit_code"])
    for command in state["remedy"]:
        print(f"$ {command}")
        if dry_run:
            continue
        result = subprocess.run(command.split(), check=False)
        if result.returncode != 0:
            print(
                f"Provisioning command failed with {result.returncode}. The QA "
                "loop will degrade to the structural scorer; disclose it.",
                file=sys.stderr,
            )
            return int(state["exit_code"])
    if dry_run:
        return int(state["exit_code"])
    after = probe()
    print(f"After provisioning: {after['state']}")
    return int(after["exit_code"])


def _render_summary(state: dict[str, Any]) -> str:
    lines = [f"render environment: {state['state']}"]
    lines.append(f"  playwright importable    : {state['playwright_importable']}")
    lines.append(f"  bundled chromium launches: {state['bundled_chromium_launchable']}")
    lines.append(f"  local Chrome/Edge        : {state['local_browser'] or 'none found'}")
    lines.append(f"  {state['note']}")
    if state["remedy"]:
        lines.append("  to provision (ONE-TIME, requires your consent):")
        lines += [f"    $ {command}" for command in state["remedy"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe (and only on request provision) the headless-render "
        "environment the presentify Step 9 visual-QA loop needs."
    )
    parser.add_argument(
        "--install", action="store_true",
        help="run the consented one-time provisioning commands (never implicit)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="with --install, print the commands without running them",
    )
    parser.add_argument("--json", action="store_true", help="emit the state as JSON")
    args = parser.parse_args(argv)

    if args.dry_run and not args.install:
        print("Error: --dry-run only applies with --install", file=sys.stderr)
        return USAGE_ERROR

    if args.install:
        return install(dry_run=args.dry_run)

    state = probe()
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(_render_summary(state), file=sys.stderr)
    return int(state["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
