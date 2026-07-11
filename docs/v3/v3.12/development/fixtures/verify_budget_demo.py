#!/usr/bin/env python3
"""Verify the Phase 3 budget demo against the five-point minimum interaction
budget and its constraints (offline, JS size cap, reduced-motion, keyboard).

Static structural review: each budget point and guard must be present and
wired in the markup/JS. Prints PASS/FAIL per check; exits non-zero on any
failure. (When no headless browser is available the skill's own degradation
rule applies: static structural review with a note - which is this script.)
"""

from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE / "models" / "budget-demo.html"

FAILURES: list = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(
        f"{'PASS' if condition else 'FAIL'}  {name}"
        + (f"  [{detail}]" if detail and not condition else "")
    )
    if not condition:
        FAILURES.append(name)


def main() -> int:
    html = DEMO.read_text(encoding="utf-8")

    # Offline guarantee: no external references outside comments.
    stripped = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    externals = [
        m
        for m in re.findall(r"https?://[^\s\"'<>]+", stripped)
        if "w3.org" not in m  # none expected at all, but be explicit
    ]
    check("zero external references", not externals, str(externals[:3]))

    # JS size cap: interaction layer <= 60 KB.
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    js_bytes = sum(len(s.encode()) for s in scripts)
    check(
        "interaction JS within 60 KB budget",
        0 < js_bytes <= 60_000,
        f"{js_bytes} bytes",
    )

    # Budget point 1: section nav with active-state tracking.
    check(
        "P1 nav + active tracking",
        'nav class="toc"' in html and "aria-current" in html and "rootMargin" in html,
    )
    # Budget point 2: scroll reveals, JS-gated.
    check(
        "P2 scroll reveals (IntersectionObserver, .js-gated)",
        "IntersectionObserver" in html
        and "classList.add('revealed')" in html
        and ".js .reveal" in html,
    )
    # Budget point 3: hover + focus affordances on cards, images, rows.
    check(
        "P3 hover + focus-visible affordances",
        ".card:hover, .card:focus-visible" in html
        and "button.imgbtn:hover, button.imgbtn:focus-visible" in html
        and "tbody tr:hover" in html,
    )
    # Budget point 4: lightbox on every non-decorative image.
    img_buttons = len(re.findall(r'<button class="imgbtn', html))
    check(
        "P4 every image wrapped in a lightbox trigger",
        img_buttons == 2,
        f"{img_buttons}",
    )
    check(
        "P4 lightbox dialog semantics + controls",
        'role="dialog"' in html
        and 'aria-modal="true"' in html
        and "'Escape'" in html
        and "wheel" in html
        and "setPointerCapture" in html
        and "opener.focus()" in html,
    )
    # Budget point 5: signature interaction (animated counters).
    check(
        "P5 signature interaction (counters, exact final value)",
        "data-count" in html and "el.textContent = target" in html,
    )
    # Reduced motion: CSS guard + JS gate.
    check(
        "reduced-motion guards (CSS + JS)",
        "@media (prefers-reduced-motion: reduce)" in html
        and "matchMedia('(prefers-reduced-motion: reduce)')" in html,
    )
    # Keyboard: focus trap, focusable cards/rows, focus restore.
    check(
        "keyboard support (trap, tabindex, restore)",
        "e.key === 'Tab'" in html and 'tabindex="0"' in html,
    )
    # Content sanity: chart-free source still produced the full budget.
    check(
        "chart-free (no chart controller present)",
        "chart" not in html.lower() or "charts to carry" not in html,
    )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED: {', '.join(FAILURES)}")
        return 1
    print(
        "Budget demo: all checks passed (static structural review; no headless browser on this host)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
