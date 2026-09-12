"""Independent inventory, rendered geometry and unavailable-capability regressions."""

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"
sys.path.insert(0, str(BUNDLE / "scripts"))
measurement = importlib.import_module("measure_handbook")
dual = importlib.import_module("dual_view")
DETECTOR = (
    ROOT
    / "catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py"
)


@pytest.fixture
def output(tmp_path):
    (tmp_path / "source.md").write_text("# Source\n\nMeasured work.", encoding="utf-8")
    model = {
        "schema_version": 2,
        "title": "Measured work",
        "sources": [{"path": "source.md", "format": "markdown"}],
        "sections": [
            {
                "id": "one",
                "heading": "Measured work",
                "blocks": [
                    {
                        "type": "paragraph",
                        "id": "body",
                        "text": "A complete explanation remains available in both views.",
                    }
                ],
            }
        ],
        "presentation": {
            "enabled": True,
            "theme": "dark",
            "depth": "balanced",
            "slide_budget": 1,
            "theme_sequence": ["dark"],
            "slides": [{"id": "one", "source_ids": ["one"]}],
        },
        "design": {"reading_themes": ["light"]},
    }
    (tmp_path / "model.json").write_text(json.dumps(model), encoding="utf-8")
    dual.assemble(tmp_path / "model.json", tmp_path / "page.html")
    return tmp_path / "page.html"


def run(output, **kwargs):
    return measurement.measure(
        output,
        kwargs or {"section_ids": ["one"], "slide_ids": ["one"]},
        DETECTOR,
        [(1366, 768)],
    )


def test_valid_reading_and_slide_measured_separately(output):
    result = run(output)
    assert result["status"] == "pass", result["errors"]
    assert result["coverage"]["measured_states"] == 4
    assert {row["view"] for row in result["rows"]} == {"reading", "presentation"}
    assert result["no_js_and_print"] == "pass"
    assert result["reduced_motion_fullscreen_fallback_escape"] == "pass"
    assert result["qualitative_review"] == "required separately"


def test_paused_reading_animation_does_not_block_presentation_settle(output):
    source = output.read_text(encoding="utf-8")
    source = source.replace(
        "</html>",
        "<script>window.readingReveal=document.querySelector('[data-dv-page] p').animate("
        "[{transform:'translateX(0)'},{transform:'translateX(0)'}],{duration:10000,fill:'both'});"
        "readingReveal.pause();</script></html>",
    )
    output.write_text(source, encoding="utf-8")
    result = run(output)
    assert result["status"] == "pass", result["errors"]
    assert result["coverage"]["measured_states"] == 4


@pytest.mark.parametrize(
    "css,error",
    [
        ("[data-dv-slide] p{font-size:8px!important}", "undersized"),
        ("[data-dv-slide]{height:50px!important;overflow:hidden!important}", "clipped"),
        ("[data-dv-page] p{max-width:400px}", "fixed-text-max-width"),
        # The v4.9.1 presentation case shipped this exact shape: a token
        # redefined inside the very rule that consumes it. It resolves at
        # computed-value time, so pairing token NAMES at root scope reads the
        # outer value and scores the pair clean while the text renders invisible.
        (
            (
                "[data-dv-page]{--ink:#f7f3e9}"
                "[data-dv-page] p{background:var(--ink);color:var(--ink);--ink:#172b3b}"
            ),
            "contrast",
        ),
    ],
)
def test_broken_rendering_fails_its_gate(output, css, error):
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</style>", f"</style><style>{css}</style>", 1
        ),
        encoding="utf-8",
    )
    assert css in output.read_text(encoding="utf-8")
    result = run(output)
    assert result["status"] == "fail"
    assert error in " ".join(result["errors"])


def test_wrong_independent_inventory_cannot_pass(output):
    result = run(output, section_ids=["absent"], slide_ids=["one"])
    assert result["status"] == "unverified" and "inventory mismatch" in str(
        result["errors"]
    )


@pytest.mark.parametrize(
    "size,declared,expected",
    [(16, None, "pass"), (15, {"heading": 16, "body": 1, "label": 12}, "fail")],
)
def test_body_floor_matches_owner_and_cannot_be_lowered(
    output, size, declared, expected
):
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</style>",
            f"</style><style>[data-dv-slide] p{{font-size:{size}px!important}}</style>",
            1,
        ),
        encoding="utf-8",
    )
    inventory = {"section_ids": ["one"], "slide_ids": ["one"]}
    if declared is not None:
        inventory["font_floors"] = declared
    result = run(output, **inventory)
    assert result["status"] == expected, result["errors"]
    if expected == "fail":
        assert any("undersized body" in error for error in result["errors"])


def test_svg_secondary_floor_is_measured_after_scale(output):
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</h2>",
            '</h2><svg viewBox="0 0 200 60" width="200" height="60" aria-label="Label fixture">'
            '<text x="10" y="25" style="font-size:12.5px">Measured label</text></svg>',
            1,
        ),
        encoding="utf-8",
    )
    result = run(output)
    assert result["status"] == "fail"
    assert any("undersized label" in error for error in result["errors"])


def test_unavailable_detector_is_unverified(output):
    result = measurement.measure(
        output,
        {"section_ids": ["one"], "slide_ids": ["one"]},
        output.parent / "missing.py",
        [(1366, 768)],
    )
    assert result["status"] == "unverified"


def test_empty_or_malformed_inventory_is_not_vacuous_success(output):
    assert run(output, section_ids=[], slide_ids=[])["status"] == "unverified"
    assert run(output, section_ids=[{}], slide_ids=[])["status"] == "unverified"


def test_long_content_reflows_in_compact_mode_but_fails_desktop_stage(output):
    original = "A complete explanation remains available in both views."
    output.write_text(
        output.read_text(encoding="utf-8").replace(original, original * 90),
        encoding="utf-8",
    )
    inventory = {"section_ids": ["one"], "slide_ids": ["one"]}
    compact = measurement.measure(output, inventory, DETECTOR, [(390, 844)])
    assert compact["status"] == "pass", compact["errors"]
    final = next(
        row
        for row in compact["rows"]
        if row["view"] == "presentation" and row["state"] == "final"
    )
    assert final["height"] > 844
    desktop = measurement.measure(output, inventory, DETECTOR, [(1366, 768)])
    assert desktop["status"] == "fail"
    assert "desktop stage scroll" in " ".join(desktop["errors"])


def _inject(output, css):
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</style>", f"</style><style>{css}</style>", 1
        ),
        encoding="utf-8",
    )


def test_contrast_is_measured_on_rendered_colour_not_token_names(output):
    """The delivered defect: identical ink and background via a local token."""
    _inject(
        output,
        "[data-dv-page]{--ink:#f7f3e9}"
        "[data-dv-page] p{background:var(--ink);color:var(--ink);--ink:#172b3b}",
    )
    result = run(output)
    assert result["status"] == "fail"
    failures = [e for e in result["errors"] if "contrast" in e]
    assert failures, result["errors"]
    # Identical ink and background is exactly 1:1; nothing can be less readable.
    assert "1.0:1" in failures[0] or "1:1" in failures[0]


def test_large_text_uses_the_three_to_one_floor(output):
    """WCAG 1.4.3 gives large text a lower floor; do not over-report it."""
    # #7f7f7f on white is 4.00:1: above the 3:1 large-text floor, below 4.5:1.
    _inject(output, "[data-dv-page] p{font-size:30px;color:#7f7f7f;background:#ffffff}")
    assert not [e for e in run(output)["errors"] if "contrast" in e]
    _inject(output, "[data-dv-page] p{font-size:14px!important}")
    assert [e for e in run(output)["errors"] if "contrast" in e]


def test_transparent_text_is_not_reported_as_a_contrast_failure(output):
    """Fully transparent ink is an opacity concern, not a contrast one."""
    _inject(output, "[data-dv-page] p{color:rgba(0,0,0,0)}")
    assert not [e for e in run(output)["errors"] if "contrast" in e]


SVG_OPEN = (
    '<svg viewBox="0 0 400 120" width="400" height="120" aria-label="Process">'
    '<rect x="20" y="30" width="120" height="60" fill="#dddddd"/>'
)


def _with_svg(output, body):
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</h2>", f"</h2>{SVG_OPEN}{body}</svg>", 1
        ),
        encoding="utf-8",
    )


def test_label_straddling_a_shape_edge_is_a_collision(output):
    """The repo case shipped three edge labels sitting across card rectangles."""
    _with_svg(output, '<text x="110" y="65" style="font-size:14px">crosses edge</text>')
    errors = [e for e in run(output)["errors"] if "straddles" in e]
    assert errors, run(output)["errors"]
    assert "crosses edge" in errors[0]


def test_label_wholly_inside_a_shape_is_correct_labelling(output):
    """A node label belongs inside its box; flagging it would be noise."""
    _with_svg(output, '<text x="35" y="65" style="font-size:14px">in box</text>')
    assert not [e for e in run(output)["errors"] if "straddles" in e]


def test_label_clear_of_every_shape_is_not_reported(output):
    _with_svg(output, '<text x="250" y="65" style="font-size:14px">clear</text>')
    assert not [e for e in run(output)["errors"] if "straddles" in e]


def test_unfilled_shape_cannot_occlude_a_label(output):
    """fill:none is a stroke outline; a label crossing it is not obscured."""
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</h2>",
            '</h2><svg viewBox="0 0 400 120" width="400" height="120" aria-label="Outline">'
            '<rect x="20" y="30" width="120" height="60" fill="none" stroke="#333"/>'
            '<text x="110" y="65" style="font-size:14px">crosses outline</text></svg>',
            1,
        ),
        encoding="utf-8",
    )
    assert not [e for e in run(output)["errors"] if "straddles" in e]


BRAND_DARK_ON_DARK = (
    '<div class="dv-brand" style="background:#172b3b">'
    '<svg viewBox="0 0 120 40" width="120" height="40" aria-label="Lockup">'
    '<rect x="0" y="0" width="30" height="30" fill="#e0a06a"/>'
    '<path d="M40 5 h70 v24 h-70 z" fill="#172b3b"/></svg></div>'
)
BRAND_READABLE = BRAND_DARK_ON_DARK.replace('fill="#172b3b"/></svg>', 'fill="#f7f3e9"/></svg>')


def test_invisible_brand_wordmark_fails_even_when_the_symbol_reads(output):
    """The repo case shipped a legible diamond beside a vanished wordmark."""
    output.write_text(
        output.read_text(encoding="utf-8").replace("</h2>", f"</h2>{BRAND_DARK_ON_DARK}", 1),
        encoding="utf-8",
    )
    errors = [e for e in run(output)["errors"] if "brand mark" in e]
    assert errors, run(output)["errors"]
    assert "SURFACE theme" in errors[0]


def test_a_brand_that_reads_against_its_surface_passes(output):
    output.write_text(
        output.read_text(encoding="utf-8").replace("</h2>", f"</h2>{BRAND_READABLE}", 1),
        encoding="utf-8",
    )
    assert not [e for e in run(output)["errors"] if "brand mark" in e]


def test_chart_with_non_uniform_scaling_is_reported(output):
    """preserveAspectRatio=none turns data points into ellipses."""
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</h2>",
            '</h2><div class="dv-chart"><svg viewBox="0 0 200 80" width="400" height="80" '
            'preserveAspectRatio="none" aria-label="Throughput">'
            '<circle data-dv-mark cx="20" cy="40" r="6" fill="#94491d"/>'
            '<circle data-dv-mark cx="60" cy="30" r="6" fill="#94491d"/></svg></div>',
            1,
        ),
        encoding="utf-8",
    )
    errors = [e for e in run(output)["errors"] if "preserveAspectRatio" in e]
    assert errors and "2 data mark" in errors[0], run(output)["errors"]


def test_decorative_artwork_may_still_stretch(output):
    """A background wave carries no data; stretching it is a design choice."""
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</h2>",
            '</h2><svg viewBox="0 0 200 40" width="400" height="40" '
            'preserveAspectRatio="none" aria-hidden="true">'
            '<path d="M0 20 Q50 0 100 20 T200 20" fill="#efe7d6"/></svg>',
            1,
        ),
        encoding="utf-8",
    )
    assert not [e for e in run(output)["errors"] if "preserveAspectRatio" in e]


def test_opening_screen_content_below_full_opacity_fails(output):
    """A scroll-reveal that starts faded ships its first screen unreadable."""
    _inject(output, "[data-dv-page] p{opacity:0.45}")
    errors = [e for e in run(output)["errors"] if "opening-screen" in e]
    assert errors, run(output)["errors"]
    assert "0.45" in errors[0]


def test_inherited_opacity_is_accumulated(output):
    """Two stacked 0.7 ancestors leave the text at 0.49, not 0.7."""
    _inject(output, "[data-dv-section]{opacity:0.7} [data-dv-page] p{opacity:0.7}")
    assert [e for e in run(output)["errors"] if "opening-screen" in e]


def test_fully_opaque_opening_screen_passes(output):
    _inject(output, "[data-dv-page] p{opacity:1}")
    assert not [e for e in run(output)["errors"] if "opening-screen" in e]


def test_content_below_the_fold_may_start_faded(output):
    """A reveal is legitimate for content the reader has to scroll to."""
    _inject(
        output,
        "[data-dv-page] p{margin-top:3000px;opacity:0.2}",
    )
    assert not [e for e in run(output)["errors"] if "opening-screen" in e]


# A bespoke-authored page that does not inherit the assembler base CSS, which
# already opts into background painting. This is the shape all three delivered
# qualification artifacts had.
DARK_BAND = (
    "[data-dv-page] [data-dv-section]{background:#172b3b;color:#f7f3e9}"
    "@media print{[data-dv-page]{print-color-adjust:economy}}"
)


def test_dark_band_without_print_color_adjust_fails_the_print_gate(output):
    """Chromium drops the band's background; the light ink survives on white."""
    _inject(output, DARK_BAND)
    errors = [e for e in run(output)["errors"] if e.startswith("print:")]
    assert errors, run(output)["errors"]
    assert "print-color-adjust: exact" in errors[0]


def test_print_color_adjust_exact_keeps_the_band_and_passes(output):
    """Opting into background painting makes the declared pair the real pair."""
    _inject(
        output,
        DARK_BAND + "@media print{[data-dv-page]{print-color-adjust:exact}}",
    )
    assert not [e for e in run(output)["errors"] if e.startswith("print:")]


def test_a_print_palette_remap_also_passes(output):
    """Repainting the ink dark for print is the other legitimate remedy."""
    _inject(
        output,
        DARK_BAND
        + "@media print{[data-dv-page] [data-dv-section]{background:#ffffff;color:#172b3b}}",
    )
    assert not [e for e in run(output)["errors"] if e.startswith("print:")]


def test_ordinary_dark_on_light_text_is_unaffected_by_the_print_gate(output):
    _inject(output, "[data-dv-page] p{color:#172b3b;background:#ffffff}")
    assert not [e for e in run(output)["errors"] if e.startswith("print:")]


def test_declared_sticky_that_loses_the_cascade_is_reported(output):
    """A rail authored sticky, overridden to static by a later equal-specificity rule."""
    _inject(
        output,
        "[data-dv-page] header{position:sticky;top:0}"
        "[data-dv-page] header{position:static}",
    )
    errors = [e for e in run(output)["errors"] if e.startswith("layout:")]
    assert errors, run(output)["errors"]
    assert "declares position sticky" in errors[0] and "computes static" in errors[0]


def test_declared_sticky_that_applies_is_not_reported(output):
    _inject(output, "[data-dv-page] header{position:sticky;top:0}")
    assert not [e for e in run(output)["errors"] if e.startswith("layout:")]


def test_a_breakpoint_that_does_not_stick_is_not_a_finding(output):
    """A media query whose condition does not match is not a lost declaration."""
    _inject(
        output,
        "@media (max-width:200px){[data-dv-page] header{position:sticky;top:0}}",
    )
    assert not [e for e in run(output)["errors"] if e.startswith("layout:")]


def test_focus_returns_to_the_control_that_opened_the_deck(output):
    """R25 names focus restoration beside scroll restoration."""
    assert not [e for e in run(output)["errors"] if e.startswith("focus:")]


def test_a_lost_opener_is_reported_rather_than_silently_dropping_focus(output):
    """If the opener does not survive a shell rebuild, focus lands nowhere."""
    output.write_text(
        output.read_text(encoding="utf-8").replace(
            "</html>",
            "<script>document.addEventListener('keydown',e=>{if(e.key==='Escape')"
            "document.querySelectorAll('[data-dv-open]').forEach(n=>n.remove());},true);"
            "</script></html>",
            1,
        ),
        encoding="utf-8",
    )
    assert [e for e in run(output)["errors"] if e.startswith("focus:")]


def _long_directory(tmp_path, rows=30):
    """A directory long enough that a 200px cap would hide most of it."""
    model = json.loads((tmp_path / "model.json").read_text(encoding="utf-8"))
    model["sections"][0]["blocks"].append(
        {
            "type": "table",
            "id": "directory",
            "header": ["Key", "Value"],
            "rows": [[f"row {i}", f"value {i}"] for i in range(rows)],
        }
    )
    (tmp_path / "model.json").write_text(json.dumps(model), encoding="utf-8")
    dual.assemble(tmp_path / "model.json", tmp_path / "long.html")
    return tmp_path / "long.html"


def test_reading_directory_is_not_capped_so_content_is_not_hidden(output):
    """D1: a cap plus overlay scrollbars makes truncated and complete identical."""
    page = _long_directory(output.parent)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        tab = browser.new_page(viewport={"width": 1366, "height": 768})
        tab.goto(page.as_uri())
        tab.wait_for_timeout(300)
        hidden = tab.evaluate(
            "() => [...document.querySelectorAll('[data-dv-page] .dv-directory')]"
            ".map(d => d.scrollHeight - d.clientHeight)"
        )
        browser.close()
    assert hidden, "fixture produced no directory to measure"
    assert max(hidden) <= 2, f"reading-view directory still hides {max(hidden)}px"


def test_slide_directory_keeps_its_cap_and_reserves_a_scroll_gutter(output):
    """The slide must still fit its stage; the scroll must be visible, not hidden."""
    page = _long_directory(output.parent)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        tab = browser.new_page(viewport={"width": 1366, "height": 768})
        tab.goto(page.as_uri())
        tab.wait_for_timeout(300)
        styles = tab.evaluate(
            "() => {const d=document.querySelector('[data-dv-slide] .dv-directory');"
            " if(!d) return null; const s=getComputedStyle(d);"
            " return {maxHeight:s.maxHeight, gutter:s.scrollbarGutter};}"
        )
        browser.close()
    if styles is None:
        pytest.skip("this fixture puts no directory on a slide")
    assert styles["maxHeight"] == "200px"
    assert "stable" in styles["gutter"]
