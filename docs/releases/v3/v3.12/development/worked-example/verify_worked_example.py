#!/usr/bin/env python3
"""Verify the Phase 5 worked example: both same-preset runs hold the fidelity
gates, the interaction budget, and the divergence requirement.

Static structural review over run-a.html / run-b.html plus the two committed
briefs; the rendered look is checkpointed separately via the headless-Edge
screenshots (run-a.png / run-b.png) read back during the visual-QA pass.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAILURES: list = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(
        f"{'PASS' if condition else 'FAIL'}  {name}"
        + (f"  [{detail}]" if detail and not condition else "")
    )
    if not condition:
        FAILURES.append(name)


def externals(html: str) -> list:
    stripped = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return re.findall(r"https?://[^\s\"'<>]+", stripped)


def main() -> int:
    runs = {}
    for name in ("run-a", "run-b"):
        runs[name] = (HERE / f"{name}.html").read_text(encoding="utf-8")
    brief_a = json.loads((HERE / "brief-a.json").read_text(encoding="utf-8"))
    brief_b = json.loads((HERE / "brief-b.json").read_text(encoding="utf-8"))

    for name, html in runs.items():
        check(f"{name}: zero external references", not externals(html))
        check(
            f"{name}: interaction budget wired (nav/reveals/hover/lightbox/move)",
            "aria-current" in html
            and "IntersectionObserver" in html
            and ":focus-visible" in html
            and html.count('<button class="imgbtn"') >= 3
            and 'role="dialog"' in html
            and ("scrolly-step" in html or "chip" in html),
        )
        check(
            f"{name}: reconstructed chart with provenance + controls",
            "reconstructed from source figure - confidence: medium" in html
            and "revchart-ymax" in html
            and "revchart-legend" in html
            and "revchart-reset" in html,
        )
        check(
            f"{name}: worksheet embedded with ground-truth readings",
            "FIGURE WORKSHEET" in html
            and "Q1 -> 120; Q2 -> 135; Q3 -> 150" in html
            and "nearest 5" in html,
        )
        check(
            f"{name}: coverage reconciliation ACCOUNTED",
            "COVERAGE RECONCILIATION" in html and "0 unaccounted" in html,
        )
        check(
            f"{name}: design record carries the roll seed",
            "DESIGN RECORD" in html and "seed" in html,
        )
        scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
        js_bytes = sum(len(s.encode()) for s in scripts)
        check(
            f"{name}: inline JS within budget",
            0 < js_bytes <= 60_000,
            f"{js_bytes} bytes",
        )
        check(
            f"{name}: reduced-motion guards present",
            "@media (prefers-reduced-motion: reduce)" in html
            and "matchMedia('(prefers-reduced-motion: reduce)')" in html,
        )

    # Divergence: the two briefs obey the 2-of-3 rule and the pages differ.
    triple_a = (
        brief_a["hue_family"],
        brief_a["layout_signature"]["name"],
        brief_a["type"]["voice"],
    )
    triple_b = (
        brief_b["hue_family"],
        brief_b["layout_signature"]["name"],
        brief_b["type"]["voice"],
    )
    shared = sum(1 for a, b in zip(triple_a, triple_b) if a == b)
    check(
        "briefs share <= 1 of {hue, layout, voice}",
        shared <= 1,
        f"{triple_a} vs {triple_b}",
    )
    check(
        "runs differ in base palette and heading type",
        "--base:#f2f8f8" in runs["run-a"]
        and "--base:#14202a" in runs["run-b"]
        and "'Arial Black'" in runs["run-a"]
        and "Consolas,'Cascadia Code'" in runs["run-b"],
    )
    check(
        "runs differ in layout signature markers",
        "mosaic" in runs["run-a"]
        and "scrolly" in runs["run-a"]
        and "offset" in runs["run-b"]
        and "chip" in runs["run-b"],
    )
    check(
        "screenshot evidence present (headless Edge renders)",
        all(
            (HERE / f"{n}.png").is_file()
            for n in ("run-a", "run-b", "run-a-mobile", "run-b-mobile")
        ),
    )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED: {', '.join(FAILURES)}")
        return 1
    print("Worked example: all checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
