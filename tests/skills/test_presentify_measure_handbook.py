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
