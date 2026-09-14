"""Deck defects are only visible while their slide is the current slide.

The load-bearing assertion here is
`test_measuring_every_slide_at_the_end_silently_misses_a_defect`, and it is not
the failure the plan predicted. The plan warned that a probe walking every slide
at the end would report them all hidden - a false alarm. Measured, this probe
does something different and worse: because `getBoundingClientRect` returns
zeros for an element inside a `display:none` slide, the naive walk finds NO
overflow at all and reports the deck clean.

A false alarm gets investigated. A silent miss ships. That is the real argument
for walking slide by slide while each one is current, and the test asserts the
measured difference rather than the predicted one.

The other three checks each fire on their own slide and on no other, the same
one-defect-per-fixture discipline the geometric audit uses.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

if os.environ.get("NEXUS_REQUIRE_RENDER") == "1":  # pragma: no cover
    importlib.import_module("playwright.sync_api")
else:
    pytest.importorskip("playwright.sync_api", reason="playwright is not installed")

from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"
sys.path.insert(0, str(BUNDLE / "scripts"))
measurement = importlib.import_module("measure_handbook")

FIXTURE = ROOT / "tests/fixtures/document-quality/deck-integrity.html"

# slide id -> the single rule it must report
SLIDES = {
    "s-clean": None,
    "s-overflow": "slide-overflow",
    "s-invisible": "invisible-after-animation",
    "s-dangling": "clone-reference-escapes-slide",
}


def walk_while_current() -> dict[str, list[str]]:
    """Measure each slide with that slide displayed, as the real gate does."""
    results: dict[str, list[str]] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(FIXTURE.resolve().as_uri())
        for slide_id in SLIDES:
            page.evaluate(
                "(id) => {"
                " for (const s of document.querySelectorAll('[data-dv-slide]'))"
                "   s.removeAttribute('data-dv-current');"
                " document.getElementById(id).setAttribute('data-dv-current','');"
                "}",
                slide_id,
            )
            handle = page.query_selector(f"#{slide_id}")
            results[slide_id] = [
                f["rule"] for f in page.evaluate(measurement.DECK_INTEGRITY, handle)
            ]
        browser.close()
    return results


def measure_all_at_the_end() -> dict[str, list[str]]:
    """The WRONG way, kept so the difference can be asserted rather than argued."""
    results: dict[str, list[str]] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(FIXTURE.resolve().as_uri())
        for slide_id in SLIDES:
            handle = page.query_selector(f"#{slide_id}")
            results[slide_id] = [
                f["rule"] for f in page.evaluate(measurement.DECK_INTEGRITY, handle)
            ]
        browser.close()
    return results


@pytest.fixture(scope="module")
def current() -> dict[str, list[str]]:
    return walk_while_current()


@pytest.mark.parametrize("slide_id", sorted(SLIDES))
def test_each_slide_reports_exactly_its_own_defect(current, slide_id: str) -> None:
    expected = SLIDES[slide_id]
    reported = set(current[slide_id])
    assert reported == (set() if expected is None else {expected}), (
        f"{slide_id} reported {sorted(reported)}; a second rule here means one "
        f"of them is over-broad"
    )


def test_measuring_every_slide_at_the_end_silently_misses_a_defect() -> None:
    """Why the per-slide walk exists, measured rather than assumed.

    Only the current slide is displayed, so every element on the others has a
    zero-sized rect. The naive walk therefore reports `s-overflow` as clean: the
    defect is not over-reported, it is INVISIBLE to that measurement.
    """
    naive = measure_all_at_the_end()
    honest = walk_while_current()

    assert "slide-overflow" not in naive["s-overflow"], (
        "if the naive walk now finds the overflow, this fixture no longer "
        "models a deck that shows one slide at a time"
    )
    assert honest["s-overflow"] == ["slide-overflow"]

    # The two rect-independent checks agree either way, which is worth knowing:
    # only the geometry check is sensitive to when it is taken.
    for slide in ("s-invisible", "s-dangling"):
        assert naive[slide] == honest[slide], (
            f"{slide} is measured from opacity and references, not rects, so "
            f"timing should not change its verdict"
        )


def test_a_clone_reference_resolving_only_against_the_original_is_reported(
    current,
) -> None:
    """The defect that looks like it works.

    `s-dangling` points at a marker defined on `s-clean`. It renders correctly
    while the original is in the document, and breaks the moment it is not.
    """
    assert "clone-reference-escapes-slide" in current["s-dangling"]
    assert current["s-clean"] == [], "the slide owning the marker is fine"


def test_overflow_is_measured_against_the_slide_canvas(current) -> None:
    """A slide has nowhere to scroll, so overflow is unreachable content."""
    assert current["s-overflow"] == ["slide-overflow"]
