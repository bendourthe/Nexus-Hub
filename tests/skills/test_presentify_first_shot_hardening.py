"""v3.16.7: first-shot hardening from a real BOD-deck presentify session.

Five defects shipped past the first delivery in that session, each with a
distinct root cause the skill now guards:

1. A generic `.pin` class on the map pins collided with the cinematic stage's
   `.pin` wrapper and blanked the hero - zero console errors, clean structural
   pass. Guards: component-CSS namespacing rule, the regression smoke-set, and
   rubric criterion 11 (painted-surface integrity).
2. A mixed-scale chart series drew flat-clamped at the axis maximum (fabricated
   data). Guard: the mixed-scale series rule (startHidden + axis auto-refit).
3. The hero scrub ramp started at 25% opacity on first paint. Guard: the
   first-paint legibility rule.
4. A full QA iteration burned on scorer format repair. Guard: the
   "author to the scorer contract" checklist.
5. The deck's literal "enrolled xx subjects" placeholder surfaced only after
   delivery. Guards: extractor placeholder scan + intake surfacing rule.

Plus the geo-pin overlay path (2b) and its bundled projection fitter, derived
from calibrating pins against a conic map image in the same session.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = (
    _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
)
SKILL_TEXT = (_BUNDLE / "SKILL.md").read_text(encoding="utf-8")
FEATURES_TEXT = (_BUNDLE / "references" / "interactive-features.md").read_text(encoding="utf-8")
RECON_TEXT = (_BUNDLE / "references" / "figure-reconstruction.md").read_text(encoding="utf-8")
RUBRIC_TEXT = (_BUNDLE / "references" / "visual-qa-rubric.md").read_text(encoding="utf-8")
SCRUB_TEXT = (_BUNDLE / "references" / "scroll-scrub.md").read_text(encoding="utf-8")
_FITTER = _BUNDLE / "scripts" / "fit_map_projection.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- 1. component-CSS namespacing --------------------------------------------

def test_component_css_namespacing_rule_is_binary():
    assert "Component CSS is namespaced (BINARY)" in SKILL_TEXT
    assert "Component CSS namespacing (BINARY)" in FEATURES_TEXT
    # The rule names the concrete failure so the grader recognizes it.
    assert ".map-pin" in SKILL_TEXT


def test_regression_smoke_set_applies_to_every_rerender():
    assert "REGRESSION SMOKE-SET" in SKILL_TEXT
    assert "regression smoke-set" in RUBRIC_TEXT.lower()
    # The set is fixed and includes the hero - the section the collision blanked.
    assert "hero at load" in SKILL_TEXT


def test_rubric_has_painted_surface_criterion():
    assert "**Painted-surface integrity**" in RUBRIC_TEXT
    assert "painted-canvas" in RUBRIC_TEXT  # schema enum value
    assert "clientWidth" in RUBRIC_TEXT


# --- 2. mixed-scale chart series ----------------------------------------------

def test_mixed_scale_series_rule():
    assert "Mixed-scale series (BINARY)" in FEATURES_TEXT
    assert "startHidden" in FEATURES_TEXT
    assert "NEVER silently clamped" in SKILL_TEXT or "NEVER draw a value clamped" in FEATURES_TEXT


# --- 3. first-paint legibility -------------------------------------------------

def test_first_paint_legibility_rule():
    assert "First paint is fully legible" in SKILL_TEXT
    assert "First paint is fully legible" in SCRUB_TEXT
    # Direction matters: out on exit, never in from a dimmed start.
    assert "fade or drift content OUT" in SKILL_TEXT


# --- 4. scorer contract ---------------------------------------------------------

def test_scorer_contract_checklist_exists():
    assert "Author to the scorer contract" in SKILL_TEXT
    assert "Scorer contract" in FEATURES_TEXT
    for token in ('data-aspect="', "--page-max", "--gutter", "placement:"):
        assert token in FEATURES_TEXT, f"scorer contract omits {token}"


# --- 5. source placeholders -----------------------------------------------------

def test_extractor_scans_for_source_placeholders():
    extractor = _load(_BUNDLE / "scripts" / "extract_content.py", "extract_content_v3167")
    sections = [
        {
            "title": "Q3 Update",
            "blocks": [
                {"type": "paragraph", "text": "HRPCI enrolled xx subjects to date"},
                {"type": "table", "rows": [["Goal", "[insert Q3 figure]"]]},
                {"type": "code", "text": "const xx = 1;"},  # code is out of scope
            ],
        }
    ]
    found = extractor._scan_placeholders(sections)
    tokens = [entry["token"].lower() for entry in found]
    assert "xx" in tokens
    assert any(token.startswith("[insert") for token in tokens)
    # Prose-scope only: the code block's xx must not be reported.
    assert all(entry["block_type"] != "code" for entry in found)


def test_placeholder_rule_reaches_the_intake_and_never_invents():
    assert "placeholders" in SKILL_TEXT
    assert "never invent the missing number" in SKILL_TEXT


# --- geo-pin overlay path + fitter ----------------------------------------------

def test_geo_pin_overlay_path_documented():
    assert "Geo-pin overlay" in RECON_TEXT
    assert "fit_map_projection.py" in RECON_TEXT
    assert "collision-relaxation" in RECON_TEXT
    # Honesty boundary: positions come from geography, disclosed in the caption.
    assert "computed from city coordinates" in RECON_TEXT
    assert "fit_map_projection.py" in SKILL_TEXT  # bundled-resources registration


def test_fit_map_projection_fits_and_emits_js(tmp_path):
    anchors = [
        [249, 264, 41.10, -112.50, "Great Salt Lake"],
        [785, 258, 41.62, -87.10, "L Michigan S tip"],
        [864, 233, 42.45, -82.70, "Lake St Clair"],
        [687, 123, 46.78, -92.06, "L Superior W tip"],
        [979, 673, 25.20, -80.90, "Florida S tip"],
        [959, 622, 26.94, -80.80, "Okeechobee"],
        [71, 334, 37.80, -122.40, "SF Bay"],
        [112, 437, 32.53, -117.12, "San Diego"],
        [561, 622, 25.90, -97.50, "Texas S tip"],
        [1094, 118, 44.80, -67.00, "Maine E"],
        [628, 50, 49.38, -95.15, "Lake of the Woods"],
        [1034, 272, 40.70, -74.00, "NYC coast"],
    ]
    anchors_path = tmp_path / "anchors.json"
    anchors_path.write_text(json.dumps(anchors), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(_FITTER), str(anchors_path), "--width", "1160", "--height", "712"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "function projPct(lat,lon)" in result.stdout
    assert "per-anchor residuals" in result.stdout


def test_fit_map_projection_rejects_thin_anchor_sets(tmp_path):
    anchors_path = tmp_path / "anchors.json"
    anchors_path.write_text(
        json.dumps([[0, 0, 40.0, -100.0, "a"], [10, 10, 41.0, -101.0, "b"]]),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(_FITTER), str(anchors_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 2
    assert "too few" in result.stderr
