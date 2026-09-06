from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "catalog"
    / "skills"
    / "testing"
    / "functional-verification"
    / "scripts"
    / "detect_visual_defects.py"
)
FIXTURES = Path(__file__).parent / "fixtures" / "visual"

BROKEN_FIXTURES = (
    ("parent-padding-escape.html", "parent-padding-escape"),
    ("svg-viewbox-overflow.html", "svg-viewbox-overflow"),
    ("text-overlap.html", "text-overlap"),
    ("horizontal-overflow.html", "horizontal-overflow"),
    ("fixed-text-max-width.html", "fixed-text-max-width"),
    ("undersized-text-box.html", "undersized-text-box"),
    ("font-size-floor.html", "font-size-floor"),
)

_RENDER_PROBE: tuple[bool, str] | None = None


def _probe_renderer() -> tuple[bool, str]:
    global _RENDER_PROBE
    if _RENDER_PROBE is not None:
        return _RENDER_PROBE
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _RENDER_PROBE = (False, "Playwright is not installed")
        return _RENDER_PROBE
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception as error:  # noqa: BLE001 - environment probe classifies any launch failure
        _RENDER_PROBE = (False, f"Playwright Chromium cannot launch: {error}")
        return _RENDER_PROBE
    _RENDER_PROBE = (True, "")
    return _RENDER_PROBE


@pytest.fixture
def rendered_detector(render_gate: object) -> None:
    ready, reason = _probe_renderer()
    if not ready:
        render_gate(reason)  # type: ignore[operator]


def _run(
    fixture: str,
    *args: str,
    no_site: bool = False,
) -> subprocess.CompletedProcess[str]:
    return _run_path(FIXTURES / fixture, *args, no_site=no_site)


def _run_path(
    path: Path,
    *args: str,
    no_site: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if no_site:
        command.append("-S")
    command.extend([str(SCRIPT), str(path), *args])
    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def _payload(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(result.stdout)


def _load_detector_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("detect_visual_defects", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_fixture_passes_full_viewport_matrix(rendered_detector: None) -> None:
    result = _run("clean.html")
    report = _payload(result)

    assert result.returncode == 0
    assert report["status"] == "pass"
    assert report["page_pass"] is True
    assert report["gate_findings"] == 0
    assert report["findings"] == []
    assert [viewport["width"] for viewport in report["viewports"]] == [420, 900, 1440]  # type: ignore[index]
    assert "PASS visual-defect detector" in result.stderr


def test_explicit_theme_override_is_applied_before_page_bootstrap(
    rendered_detector: None,
    tmp_path: Path,
) -> None:
    themed_page = tmp_path / "themed.html"
    themed_page.write_text(
        """<!doctype html>
<html lang="en">
<head>
<script>
(function () {
  var theme = window.localStorage.getItem("portfolio-theme");
  if (theme !== "light" && theme !== "dark") theme = "dark";
  document.documentElement.setAttribute("data-theme", theme);
})();
</script>
<style>
body { margin: 0; }
p { width: 100px; height: 30px; margin: 0; font: 16px/30px sans-serif; }
html[data-theme="light"] p { font-size: 8px; }
</style>
</head>
<body><p>Theme probe</p></body>
</html>
""",
        encoding="utf-8",
    )

    default_result = _run_path(themed_page, "--viewports", "900")
    dark_result = _run_path(themed_page, "--viewports", "900", "--theme", "dark")
    light_result = _run_path(themed_page, "--viewports", "900", "--theme", "light")

    assert default_result.returncode == 0
    assert _payload(default_result)["theme"] is None
    assert dark_result.returncode == 0
    assert _payload(dark_result)["theme"] == "dark"
    assert light_result.returncode == 1
    light_report = _payload(light_result)
    assert light_report["theme"] == "light"
    assert {finding["rule"] for finding in light_report["findings"]} == {"font-size-floor"}  # type: ignore[union-attr]


def test_unsupported_theme_is_rejected() -> None:
    result = _run("clean.html", "--theme", "sepia")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "invalid choice" in result.stderr.lower()


def test_fragment_activates_hash_routed_page(
    rendered_detector: None,
    tmp_path: Path,
) -> None:
    routed_page = tmp_path / "routed.html"
    routed_page.write_text(
        """<!doctype html>
<html lang="en">
<head>
<style>
body { margin: 0; }
.page { display: none; }
.page.active { display: block; }
p { width: 180px; height: 30px; margin: 0; font: 16px/30px sans-serif; }
#foundations p { font-size: 8px; }
</style>
</head>
<body>
<section class="page" id="home"><p>Home is clean</p></section>
<section class="page" id="foundations"><p>Foundations is broken</p></section>
<script>
const target = location.hash.slice(1) || "home";
document.getElementById(target).classList.add("active");
</script>
</body>
</html>
""",
        encoding="utf-8",
    )

    default_result = _run_path(routed_page, "--viewports", "900")
    fragment_result = _run_path(
        routed_page,
        "--viewports",
        "900",
        "--fragment",
        "foundations",
    )
    typo_result = _run_path(
        routed_page,
        "--viewports",
        "900",
        "--fragment",
        "foundatons",
    )

    assert default_result.returncode == 0
    assert _payload(default_result)["fragment"] is None
    assert fragment_result.returncode == 1
    fragment_report = _payload(fragment_result)
    assert fragment_report["fragment"] == "foundations"
    assert {finding["rule"] for finding in fragment_report["findings"]} == {  # type: ignore[union-attr]
        "font-size-floor"
    }
    assert typo_result.returncode == 1
    typo_report = _payload(typo_result)
    assert typo_report["fragment"] == "foundatons"
    assert {finding["rule"] for finding in typo_report["findings"]} == {  # type: ignore[union-attr]
        "fragment-target"
    }


@pytest.mark.parametrize("fragment", ("", "#", "../foundations", "foundations?next=home"))
def test_invalid_fragment_is_rejected(fragment: str) -> None:
    result = _run("clean.html", "--fragment", fragment)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "fragment" in result.stderr.lower()


@pytest.mark.parametrize(("fixture", "expected_rule"), BROKEN_FIXTURES)
def test_each_broken_fixture_yields_exactly_its_rule(
    rendered_detector: None,
    fixture: str,
    expected_rule: str,
) -> None:
    result = _run(fixture, "--viewports", "900")
    report = _payload(result)
    findings = report["findings"]

    assert result.returncode == 1
    assert report["status"] == "fail"
    assert report["page_pass"] is False
    assert report["gate_findings"] == 1
    assert len(findings) == 1  # type: ignore[arg-type]
    finding = findings[0]  # type: ignore[index]
    assert finding["rule"] == expected_rule
    assert finding["severity"] in {"high", "error"}
    assert finding["selector"]
    assert finding["viewport"] == {"width": 900, "height": 900}
    assert finding["measurements"]
    assert expected_rule in result.stderr


def test_false_positive_controls_are_present_in_clean_fixture(
    rendered_detector: None,
) -> None:
    html = (FIXTURES / "clean.html").read_text(encoding="utf-8")
    assert "overflow-x: auto" in html
    assert 'data-reveal="pending"' in html
    assert "opacity: 0" in html
    assert 'class="collapsed-copy"' in html
    assert "@media (max-width: 720px)" in html
    assert '.page-container { width: 100%; max-width: 1200px;' in html

    result = _run("clean.html", "--viewports", "420")
    assert result.returncode == 0
    assert _payload(result)["findings"] == []


def test_text_overlap_compares_only_painted_direct_text_fragments(
    rendered_detector: None,
    tmp_path: Path,
) -> None:
    fragment_page = tmp_path / "painted-text-fragments.html"
    fragment_page.write_text(
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Painted text fragments</title>
<style>
* { box-sizing: border-box; }
html { font: 16px/24px Arial, sans-serif; }
body { margin: 0; padding: 16px; }
.wrapped { width: 190px; margin: 0; }
.wrapped code, .wrapped a { font: inherit; }
.clip-stage { position: relative; width: 300px; height: 32px; margin-top: 24px; }
.scroller { width: 96px; height: 24px; overflow-x: auto; white-space: nowrap; }
.outside { position: absolute; top: 0; left: 150px; }
.captions { position: relative; width: 300px; height: 40px; margin-top: 24px; }
.caption { position: absolute; top: 0; width: 110px; height: 28px; padding: 2px 4px; background: #eef; }
.caption-one { left: 0; }
.caption-two { left: 55px; }
</style>
</head>
<body>
<p class="wrapped"><code>alpha beta gamma delta tail</code> <a id="wrapped-following" href="#target">Open guide</a></p>
<div class="clip-stage"><div class="scroller"><span>A long clipped line that extends behind the outside label</span></div><span id="outside-label" class="outside">Outside label</span></div>
<div class="captions"><span class="caption caption-one">First caption</span><span id="true-overlap" class="caption caption-two">Second caption</span></div>
</body>
</html>
""",
        encoding="utf-8",
    )

    result = _run_path(fragment_page, "--viewports", "900")
    report = _payload(result)
    findings = report["findings"]

    assert result.returncode == 1
    assert report["gate_findings"] == 1
    assert len(findings) == 1  # type: ignore[arg-type]
    assert findings[0]["rule"] == "text-overlap"  # type: ignore[index]
    assert findings[0]["selector"] == "#true-overlap"  # type: ignore[index]


def test_inline_overflow_does_not_erase_text_but_zero_sized_block_clip_does(
    rendered_detector: None,
    tmp_path: Path,
) -> None:
    inline_page = tmp_path / "inline-overflow-overlap.html"
    inline_page.write_text(
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Inline overflow overlap</title>
<style>
* { box-sizing: border-box; }
html { font: 16px/24px Arial, sans-serif; }
body { margin: 0; padding: 16px; }
p { width: 300px; margin: 0; }
.inline-source { overflow: hidden; }
.inline-target { position: relative; left: -56px; }
.zero-stage { position: relative; width: 300px; height: 24px; margin-top: 24px; }
.zero-clip { position: absolute; width: 0; height: 0; overflow: hidden; }
.visible-label { position: absolute; top: 0; left: 0; }
</style>
</head>
<body>
<p><span class="inline-source">First caption</span><span id="inline-overlap" class="inline-target">Second caption</span></p>
<div class="zero-stage"><div class="zero-clip"><span>Clipped collision</span></div><span id="visible-label" class="visible-label">Clipped collision</span></div>
</body>
</html>
""",
        encoding="utf-8",
    )

    result = _run_path(inline_page, "--viewports", "900")
    report = _payload(result)
    findings = report["findings"]

    assert result.returncode == 1
    assert report["gate_findings"] == 1
    assert len(findings) == 1  # type: ignore[arg-type]
    assert findings[0]["rule"] == "text-overlap"  # type: ignore[index]
    assert findings[0]["selector"] == "#inline-overlap"  # type: ignore[index]


def test_defect_repeats_once_per_requested_viewport(rendered_detector: None) -> None:
    result = _run("fixed-text-max-width.html")
    report = _payload(result)
    findings = report["findings"]

    assert result.returncode == 1
    assert len(findings) == 3  # type: ignore[arg-type]
    assert {finding["viewport"]["width"] for finding in findings} == {420, 900, 1440}  # type: ignore[index, union-attr]
    assert {finding["rule"] for finding in findings} == {"fixed-text-max-width"}  # type: ignore[union-attr]


def test_allowlist_matches_dom_selector_and_records_suppression(
    rendered_detector: None,
    tmp_path: Path,
) -> None:
    allowlist = tmp_path / "visual-allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "allow": [
                    {
                        "rule": "fixed-text-max-width",
                        "selector": ".responsive-copy",
                        "reason": "The fixture proves a recorded exception.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = _run(
        "fixed-text-max-width.html",
        "--viewports",
        "900",
        "--allowlist",
        str(allowlist),
    )
    report = _payload(result)

    assert result.returncode == 0
    assert report["findings"] == []
    assert report["suppressed_findings"] == 1
    assert report["page_pass"] is True


def test_tolerance_suppresses_subthreshold_geometry(rendered_detector: None) -> None:
    result = _run(
        "parent-padding-escape.html",
        "--viewports",
        "900",
        "--tolerance",
        "100",
    )
    report = _payload(result)

    assert result.returncode == 0
    assert report["findings"] == []


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("--tolerance", "Infinity"),
        ("--tolerance", "NaN"),
        ("--minimum-text-width", "Infinity"),
        ("--minimum-text-height", "NaN"),
        ("--font-floor", "Infinity"),
        ("--settle-ms", "NaN"),
    ],
)
def test_non_finite_float_controls_are_rejected(flag: str, value: str) -> None:
    result = _run("clean.html", flag, value)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "finite" in result.stderr.lower()


def test_custom_property_text_caps_are_detected_across_css_routes(
    rendered_detector: None,
) -> None:
    result = _run("fixed-text-max-width-variable.html", "--viewports", "900")
    report = _payload(result)
    findings = report["findings"]

    assert result.returncode == 1
    assert report["gate_findings"] == 3
    assert {finding["rule"] for finding in findings} == {"fixed-text-max-width"}  # type: ignore[union-attr]
    assert {finding["selector"] for finding in findings} == {  # type: ignore[union-attr]
        "#embedded-variable-cap",
        "#inline-variable-cap",
        "#linked-variable-cap",
    }
    assert all("resolved_value" in finding["measurements"]["declarations"][0] for finding in findings)  # type: ignore[union-attr]


def test_aria_hidden_pixels_remain_in_geometry_checks(
    rendered_detector: None,
) -> None:
    result = _run("aria-hidden-visible.html", "--viewports", "900")
    report = _payload(result)
    findings = report["findings"]
    rules = {finding["rule"] for finding in findings}  # type: ignore[union-attr]

    assert result.returncode == 1
    assert "horizontal-overflow" in rules
    assert "font-size-floor" not in rules
    assert any(finding["selector"] == "#aria-hidden-container" for finding in findings)  # type: ignore[union-attr]


def test_invalid_allowlist_selector_is_an_explicit_finding(
    rendered_detector: None,
    tmp_path: Path,
) -> None:
    allowlist = tmp_path / "invalid-selector.json"
    allowlist.write_text(
        json.dumps(
            {
                "allow": [
                    {
                        "rule": "parent-padding-escape",
                        "selector": "[",
                        "reason": "Exercise selector failure reporting.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = _run(
        "clean.html",
        "--viewports",
        "900",
        "--allowlist",
        str(allowlist),
    )
    report = _payload(result)
    finding = report["findings"][0]  # type: ignore[index]

    assert result.returncode == 1
    assert report["gate_findings"] == 1
    assert finding["rule"] == "selector-evaluation"
    assert finding["selector"] == "["
    assert "could not evaluate" in finding["message"].lower()


def test_generated_selector_escapes_css_special_id(rendered_detector: None) -> None:
    result = _run("fixed-text-max-width.html", "--viewports", "900")
    finding = _payload(result)["findings"][0]  # type: ignore[index]

    assert finding["selector"] == r"#fixed\:max"
    assert finding["measurements"]["text_evidence"] == "semantic-text-tag"


def test_same_element_reports_only_highest_severity_finding(
    rendered_detector: None,
) -> None:
    result = _run("dedup-same-element.html", "--viewports", "900")
    report = _payload(result)

    assert result.returncode == 1
    assert report["gate_findings"] == 1
    assert len(report["findings"]) == 1  # type: ignore[arg-type]
    assert report["findings"][0]["selector"] == r"#multi\:defect"  # type: ignore[index]


def test_missing_playwright_is_cannot_run_with_install_hint() -> None:
    result = _run("clean.html", "--viewports", "900", no_site=True)
    report = _payload(result)

    assert result.returncode == 3
    assert report["status"] == "cannot-run"
    assert report["page_pass"] is False
    assert report["findings"][0]["rule"] == "renderer-unavailable"  # type: ignore[index]
    assert "pip install playwright" in result.stderr
    assert "playwright install chromium" in result.stderr


def test_page_load_failure_is_a_gate_finding() -> None:
    detector = _load_detector_module()

    class FailingPage:
        def goto(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError("synthetic local load failure")

    result = detector._scan_viewport(
        FailingPage(),
        (FIXTURES / "clean.html").resolve().as_uri(),
        width=900,
        height=900,
        tolerance=1.0,
        minimum_text_width=16.0,
        minimum_text_height=12.0,
        font_floor=12.0,
        allowlist=[],
        timeout_ms=100,
        settle_ms=0,
    )
    finding = result["findings"][0]

    assert finding["rule"] == "page-load"
    assert finding["severity"] == "error"
    assert finding["viewport"] == {"width": 900, "height": 900}
    assert "synthetic local load failure" in finding["measurements"]["error"]


def test_theme_setup_failure_is_a_gate_finding() -> None:
    detector = _load_detector_module()

    class FailingPage:
        def add_init_script(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError("synthetic theme setup failure")

        def goto(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("navigation must not continue after theme setup fails")

    result = detector._scan_viewport(
        FailingPage(),
        (FIXTURES / "clean.html").resolve().as_uri(),
        width=900,
        height=900,
        tolerance=1.0,
        minimum_text_width=16.0,
        minimum_text_height=12.0,
        font_floor=12.0,
        allowlist=[],
        timeout_ms=100,
        settle_ms=0,
        theme="light",
    )
    finding = result["findings"][0]

    assert finding["rule"] == "theme-setup"
    assert finding["severity"] == "error"
    assert finding["viewport"] == {"width": 900, "height": 900}
    assert finding["measurements"]["requested_theme"] == "light"
    assert "synthetic theme setup failure" in finding["measurements"]["error"]


def test_route_boundary_allows_local_and_blocks_network() -> None:
    detector = _load_detector_module()

    class FakeRoute:
        def __init__(self, url: str) -> None:
            self.request = type("Request", (), {"url": url})()
            self.action: tuple[str, str | None] | None = None

        def continue_(self) -> None:
            self.action = ("continue", None)

        def abort(self, reason: str) -> None:
            self.action = ("abort", reason)

    local = FakeRoute((FIXTURES / "clean.html").resolve().as_uri())
    remote = FakeRoute("https://example.invalid/tracker.js")

    detector._route_local_only(local)
    detector._route_local_only(remote)

    assert local.action == ("continue", None)
    assert remote.action == ("abort", "blockedbyclient")
