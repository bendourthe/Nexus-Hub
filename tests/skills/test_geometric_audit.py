"""Every geometric-audit check fires on its own fixture and on no other.

Two properties are asserted, and the second is the one that matters:

1. Each broken fixture reports EXACTLY its own check. A fixture carrying one
   defect that trips two checks means a check is over-broad, and an over-broad
   check hides the missing one next to it.
2. Every assertion is negative-controlled. The audit's `--disable` option
   switches one check off, and the test proves the fixture then falls silent.
   A check that cannot be shown to be the thing producing a finding is not
   evidence, however green it looks.

The two defence fixtures are the false positives that made the source
project's first audit useless: a rotated axis title (which `getBBox` calls
clipped) and a label inside a wiggly trace's bounding box but off its ink.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("playwright", reason="playwright is not installed in this job")

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/document-quality"
SCRIPT = (
    ROOT
    / "catalog/skills/specialized-domains/document-to-interactive-html"
    / "scripts/geometric_audit.py"
)

_spec = importlib.util.spec_from_file_location("geometric_audit", SCRIPT)
audit_mod = importlib.util.module_from_spec(_spec)
sys.modules["geometric_audit"] = audit_mod
_spec.loader.exec_module(audit_mod)

# fixture -> the single check it must report
BROKEN = {
    "clipped-text": "clipped-text",
    "label-overlap": "label-overlap",
    "label-on-trace": "label-on-trace",
    "legend-colour": "legend-colour-collision",
    "oversized-type": "oversized-type",
    "stroke-drift": "stroke-drift",
    "legend-not-drawn": "legend-entry-not-drawn",
    "tick-outside-range": "tick-outside-range",
    "viewbox-dead-space": "viewbox-dead-space",
}

# Fixtures that must report NOTHING. clean is the baseline; the other two are
# the false-positive defences.
SILENT = ("clean", "rotated-axis-title", "label-beside-wiggle", "viewbox-cropped")


def run(name: str, disabled: list[str] | None = None) -> dict:
    report = audit_mod.audit(
        FIXTURES / f"{name}.html",
        samples=audit_mod.TRACE_SAMPLES,
        oversize_multiple=3.0,
        disabled=disabled,
    )
    if report["status"] == "unverified":
        if os.environ.get("NEXUS_REQUIRE_RENDER") == "1":
            pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but the audit is unverified: {report['errors']}")
        pytest.skip(f"renderer unavailable: {report['errors']}")
    return report


def checks_in(report: dict) -> set[str]:
    return {finding["check"] for finding in report["findings"]}


@pytest.mark.parametrize("fixture", sorted(BROKEN))
def test_each_fixture_reports_exactly_its_own_check(fixture: str) -> None:
    report = run(fixture)
    assert checks_in(report) == {BROKEN[fixture]}, (
        f"{fixture} should report only {BROKEN[fixture]}; "
        f"a second check here means one of them is over-broad"
    )
    assert report["status"] == "fail"


@pytest.mark.parametrize("fixture", SILENT)
def test_clean_and_defence_fixtures_report_nothing(fixture: str) -> None:
    report = run(fixture)
    assert report["findings"] == [], f"{fixture} must stay silent"
    assert report["status"] == "pass"


@pytest.mark.parametrize("fixture", sorted(BROKEN))
def test_disabling_the_check_silences_its_fixture(fixture: str) -> None:
    """The negative control: prove the check is what produced the finding."""
    check = BROKEN[fixture]
    assert check in checks_in(run(fixture)), "precondition: the check fires"
    report = run(fixture, disabled=[check])
    assert check not in checks_in(report), (
        f"{fixture} still reports {check} with it disabled, so something else "
        f"is producing that finding"
    )


def test_a_rotated_title_is_judged_in_screen_space_not_by_getbbox() -> None:
    """Defence A, stated as its own case because it is why the audit exists.

    `getBBox` ignores transforms, so a rotated y-axis title sits outside its own
    untransformed box and every one of them was reported as clipped - about 220
    findings for one real defect.
    """
    assert "clipped-text" not in checks_in(run("rotated-axis-title"))
    # The same check still catches a genuinely out-of-viewport label.
    assert "clipped-text" in checks_in(run("clipped-text"))


def test_a_label_in_a_traces_bounding_box_is_not_on_its_ink() -> None:
    """Defence B: the bounding box of a wiggly trace is the whole panel.

    The fixture's path hugs the bottom band and takes one tall spike, so its
    bounding box covers the label while its ink comes nowhere near it. A
    bounding-box test reports a collision here; sampling with getPointAtLength
    does not.
    """
    assert "label-on-trace" not in checks_in(run("label-beside-wiggle"))
    # And the sampled test still catches a label actually sitting on the line.
    assert "label-on-trace" in checks_in(run("label-on-trace"))


def test_an_unavailable_renderer_is_unverified_never_a_pass(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.html"
    assert audit_mod.main([str(missing)]) == audit_mod.EXIT_UNVERIFIED


def test_exit_codes_separate_a_pass_from_a_finding() -> None:
    assert audit_mod.main([str(FIXTURES / "clean.html")]) == audit_mod.EXIT_PASS
    assert audit_mod.main([str(FIXTURES / "label-overlap.html")]) == audit_mod.EXIT_FINDINGS


def test_the_suggested_crop_is_actionable_not_advisory() -> None:
    """A suggestion nobody can apply is a complaint.

    `viewbox-dead-space.html` and `viewbox-cropped.html` are the same figure.
    The cropped one carries, verbatim, the viewBox the check suggested for the
    other, and it passes. That is what makes the suggestion worth emitting.
    """
    report = run("viewbox-dead-space")
    finding = next(f for f in report["findings"] if f["check"] == "viewbox-dead-space")
    assert finding["measurement"]["suggested_viewBox"], "a finding must suggest a crop"
    assert run("viewbox-cropped")["findings"] == []


def test_dead_space_threshold_is_what_decides_the_finding() -> None:
    """Negative control for the threshold rather than for the check."""
    assert "viewbox-dead-space" in checks_in(run("viewbox-dead-space"))
    generous = audit_mod.audit(
        FIXTURES / "viewbox-dead-space.html",
        samples=audit_mod.TRACE_SAMPLES,
        oversize_multiple=3.0,
        dead_space_fraction=0.95,
    )
    assert "viewbox-dead-space" not in {f["check"] for f in generous["findings"]}


def test_a_legend_entry_matching_a_drawn_colour_is_not_reported() -> None:
    """The clean fixture's legend keys both entries to colours the figure draws."""
    assert "legend-entry-not-drawn" not in checks_in(run("clean"))
