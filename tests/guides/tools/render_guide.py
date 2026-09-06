"""Render the Nexus-Hub guide in a real browser and save screenshot evidence.

Dev-only tool for the v4.2.2 guide rebuild (plan sub-task 1.2). Renders
``guides/website/nexus-hub-guide.html`` via ``file://`` across every page,
theme, and width, and writes full-page PNGs under the release evidence tree.

Usage:
    python tests/guides/tools/render_guide.py --label phase-1
    python tests/guides/tools/render_guide.py --label phase-4 --pages training
    python tests/guides/tools/render_guide.py --label phase-3 --reduced-motion
    python tests/guides/tools/render_guide.py --label phase-1 --output-dir docs/releases/v4/v4.4/development/guide-rebuild/renders

Requires Playwright for rendering (the focused pytest smoke skips unless the browser is required):
    pip install playwright && playwright install chromium

The script is deliberately outside pytest collection (no ``test_`` prefix)
and outside ``scripts/`` (so it is never installer-copied).
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
OUT_BASE = (
    _ROOT
    / "docs"
    / "releases"
    / "v4"
    / "v4.2"
    / "development"
    / "guide-rebuild"
    / "renders"
)

PAGES = ("home", "foundations", "training", "cheatsheets")
THEMES = ("dark", "light")
WIDTHS = (420, 900, 1440)
INSTALL_HINT = (
    "Playwright is not installed. Run: pip install playwright && playwright install chromium"
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True, help="output subfolder, e.g. phase-1")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUT_BASE,
        help="output root (default: the v4.2 guide-rebuild renders directory)",
    )
    parser.add_argument(
        "--pages",
        nargs="*",
        default=list(PAGES),
        choices=list(PAGES),
        help="subset of pages to render (default: all)",
    )
    parser.add_argument(
        "--themes",
        nargs="*",
        default=list(THEMES),
        choices=list(THEMES),
        help="subset of themes (default: both)",
    )
    parser.add_argument(
        "--widths",
        nargs="*",
        type=int,
        default=list(WIDTHS),
        help="viewport widths in px (default: 420 900 1440)",
    )
    parser.add_argument(
        "--reduced-motion",
        action="store_true",
        help="emulate prefers-reduced-motion: reduce (suffixes files with -rm)",
    )
    parser.add_argument(
        "--hash",
        dest="extra_hash",
        default="",
        help="extra hash fragment appended after the page id (e.g. '/describe?beat=1')",
    )
    return parser.parse_args(argv)


def _display_path(path: Path) -> str:
    """Return a repository-relative path when possible, otherwise an absolute path."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(_ROOT))
    except ValueError:
        return str(resolved)


def _atomic_screenshot(page: object, dest: Path) -> None:
    """Write to a temp file in the same directory, then rename over dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(suffix=".png", dir=str(dest.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    page.screenshot(path=str(tmp), full_page=True)  # type: ignore[attr-defined]
    tmp.replace(dest)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if not GUIDE.is_file():
        print(f"ERROR: guide not found at {GUIDE}", file=sys.stderr)
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(f"ERROR: {INSTALL_HINT}", file=sys.stderr)
        return 3

    out_dir = args.output_dir / args.label
    url = GUIDE.resolve().as_uri()
    suffix = "-rm" if args.reduced_motion else ""
    written: list[Path] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for theme in args.themes:
                for width in args.widths:
                    context = browser.new_context(
                        viewport={"width": width, "height": 940},
                        reduced_motion="reduce" if args.reduced_motion else "no-preference",
                    )
                    # Set the theme before any document script runs.
                    context.add_init_script(
                        f'window.localStorage.setItem("portfolio-theme", "{theme}");'
                    )
                    page = context.new_page()
                    for page_id in args.pages:
                        page.goto(f"{url}#{page_id}{args.extra_hash}")
                        page.wait_for_timeout(900)  # settle reveals/typewriters
                        # Full-page shots never scroll, so scroll-gated reveals
                        # would render transparent; force their end state.
                        page.evaluate(
                            "document.querySelectorAll('.reveal:not(.in)')"
                            ".forEach(function (el) { el.classList.add('in'); });"
                            # Sticky + backdrop-filter headers stitch as a dark
                            # band in full-page shots; pin the header in flow.
                            "var h = document.querySelector('.site-header');"
                            "if (h) { h.style.position = 'static'; }"
                        )
                        # Staggered scene transitions run up to ~1.6s delay + .8s.
                        page.wait_for_timeout(2600)
                        dest = out_dir / f"{page_id}-{theme}-{width}{suffix}.png"
                        _atomic_screenshot(page, dest)
                        written.append(dest)
                    context.close()
        finally:
            browser.close()

    for path in written:
        print(_display_path(path))
    print(f"render_guide: wrote {len(written)} screenshot(s) to {_display_path(out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
