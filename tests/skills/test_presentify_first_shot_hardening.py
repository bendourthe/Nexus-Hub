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

Phase 3 (2026-08-13) adds the second lesson batch, from a VectorCAST decision-brief
session. That batch is a different failure CLASS: the page was offline, responsive,
browser-verified, and structurally clean, and was still the wrong artifact - it
critiqued a draft the audience had never seen, estimated a reusable platform when a
bounded pilot was requested, argued against an assumption the reader had granted, and
carried visuals that were present rather than explanatory. Guards: the content-intent
brief and Gate A, the decision-brief authoring rules, visual contracts and Gate B,
the composition rules (responsive-typography 8-11), the composition probes, and the
four named QA layers with their binary final-pass rule.
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
INTENT_TEXT = (_BUNDLE / "references" / "content-intent.md").read_text(encoding="utf-8")
TYPO_TEXT = (_BUNDLE / "references" / "responsive-typography.md").read_text(encoding="utf-8")
COMMAND_TEXT = (_ROOT / "catalog" / "commands" / "presentify.md").read_text(encoding="utf-8")
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
        check=False,
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
        check=False,
    )
    assert result.returncode == 2
    assert "too few" in result.stderr


# === Phase 3: the VectorCAST decision-brief lessons ==============================

# --- 3.1 content-intent brief ----------------------------------------------------

def test_content_intent_reference_exists_and_is_registered():
    # The orphan-bundle audit requires every bundled file to be referenced.
    assert "references/content-intent.md" in SKILL_TEXT
    assert "content-intent.md" in RUBRIC_TEXT


def test_content_brief_declares_all_four_fields():
    for field in ("source_relationship", "decision_to_enable", "assumptions", "scope_class"):
        assert field in INTENT_TEXT, f"content brief omits {field}"
        assert field in SKILL_TEXT, f"Step 5 does not resolve {field}"
    assert "exclusions" in INTENT_TEXT


def test_source_relationship_defaults_to_standalone_with_a_banned_phrase_list():
    assert "default `standalone`" in INTENT_TEXT
    for value in ("revision-aware", "comparative", "faithful-adaptation"):
        assert value in INTENT_TEXT
    # The observable criterion is a concrete phrase list, not a vibe.
    for phrase in ("the original", "the prior draft", "what was right", "original preserved"):
        assert phrase in INTENT_TEXT, f"banned-phrase list omits {phrase!r}"


def test_assumption_ledger_classifies_and_protects_accepted_premises():
    for status in ("accepted", "needs-verification", "bounded", "material-risk"):
        assert status in INTENT_TEXT, f"ledger omits status {status}"
    # The load-bearing consequence: an accepted premise is not argued with.
    assert "negates an `accepted`" in INTENT_TEXT
    assert "no section heading or lead sentence may negate one" in SKILL_TEXT


def test_scope_classes_are_named_and_bind_every_timeline():
    for cls in (
        "working-demonstration",
        "decision-grade-pilot",
        "controlled-rollout",
        "reusable-platform",
    ):
        assert cls in INTENT_TEXT, f"scope classes omit {cls}"
        assert cls in SKILL_TEXT
    assert "three planning assumptions" in INTENT_TEXT
    # Agent speed is the exact rationalization that produced the oversized estimate.
    assert "execution rate" in SKILL_TEXT.lower() or "execution RATE" in SKILL_TEXT


# --- 3.2 decision-brief authoring rules ------------------------------------------

def test_subject_capability_summary_precedes_comparison():
    assert "subject_capability_summary" in INTENT_TEXT
    assert "capability summary" in SKILL_TEXT


def test_comparison_visual_is_chosen_by_decision_shape():
    for form in ("Matrix", "Stacked bar", "Flow", "Iceberg"):
        assert form in INTENT_TEXT, f"visual-selection table omits {form}"
    # The iceberg is permitted, but only where the split IS the decision.
    assert "isible-versus-hidden is ITSELF the decision" in INTENT_TEXT


def test_hero_budget_and_responsibility_lanes_are_binary():
    assert "Hero-content budget (BINARY)" in INTENT_TEXT
    assert "Hero-content budget" in SKILL_TEXT
    assert "responsibility lanes" in SKILL_TEXT.lower()
    assert "ONE primary owner" in INTENT_TEXT


def test_credits_are_unobtrusive_and_reachable_three_ways():
    # Binary in BOTH directions: hidden by default, but never unreachable.
    assert "Credits are unobtrusive AND accessible" in INTENT_TEXT
    for route in ("hover", "focus", "touch"):
        assert route in INTENT_TEXT.lower(), f"credit disclosure omits the {route} route"
    assert "never permission to make" in SKILL_TEXT


# --- 3.3 visual contracts + Gate B -------------------------------------------------

def test_visual_contract_declares_all_seven_fields():
    for field in (
        "Question",
        "Message",
        "Encoding",
        "States",
        "Trigger",
        "Fallback",
        "Evidence",
    ):
        assert f"| {field} |" in INTENT_TEXT, f"visual contract omits {field}"


def test_subtractive_test_permits_omission():
    assert "subtractive test" in INTENT_TEXT.lower()
    assert "subtractive test" in SKILL_TEXT.lower()
    # A gate that can only demand MORE visual work is a cost generator.
    assert "permitted" in INTENT_TEXT
    assert "OMIT" in SKILL_TEXT


def test_scrollytelling_sections_declare_a_state_table():
    assert "state table" in INTENT_TEXT.lower()
    assert "STATE TABLE" in SKILL_TEXT
    # It composes with criterion 11 rather than duplicating it.
    assert "criterion 11" in INTENT_TEXT


# --- 3.4 composition rules ---------------------------------------------------------

def test_typography_contract_carries_the_composition_rules():
    assert "Eleven rules" in TYPO_TEXT
    assert "wrap plan" in TYPO_TEXT.lower()
    assert "text ROLE" in TYPO_TEXT
    assert "Section height is earned by content or interaction (BINARY)" in TYPO_TEXT


def test_role_measure_and_utilization_floor():
    assert "70%" in TYPO_TEXT
    assert "70%" in SKILL_TEXT
    # Long-form prose is the ONLY default recipient of the character measure.
    assert "only default recipient" in TYPO_TEXT.lower()


def test_viewport_height_minimum_is_named_as_fluid_but_wrong():
    # The instructive part: it passes the fluid-spacing check and is still the defect.
    assert "82svh" in TYPO_TEXT
    assert "fluid and wrong" in TYPO_TEXT
    assert "content-height" in SKILL_TEXT


def test_density_is_revised_as_a_system_without_breaking_the_floors():
    assert "Density is a system" in TYPO_TEXT
    for var in ("Root type scale", "Line height", "Grid-track proportions"):
        assert var in TYPO_TEXT, f"density variable list omits {var}"
    # It composes with rule 4 rather than competing with it.
    assert "16px" in TYPO_TEXT and "13px" in TYPO_TEXT and "12px" in TYPO_TEXT


# --- 3.5 composition probes --------------------------------------------------------

def test_step9_records_the_composition_probes():
    for probe in (
        "rendered line count",
        "width utilization",
        "one-word final-line detection",
        "density deltas",
    ):
        assert probe.lower() in SKILL_TEXT.lower(), f"probe set omits {probe}"
    # Intersection is asserted, not merely recorded - the old probes stopped at boxes.
    assert "INTERSECTION" in SKILL_TEXT


def test_per_section_evidence_extends_rather_than_replaces_the_smoke_set():
    assert "PER-SECTION evidence" in SKILL_TEXT
    assert "contact sheets" in SKILL_TEXT
    assert "EXTENDS the regression smoke-set" in SKILL_TEXT
    assert "STICKY-LAYER INVENTORY" in SKILL_TEXT


def test_smaller_is_not_automatically_better():
    # Guards the obvious failure mode of a density-optimizing agent.
    assert "not automatically better" in SKILL_TEXT
    assert "not automatically better" in RUBRIC_TEXT


# --- 3.6 QA layers, gates, helper manifest ------------------------------------------

def test_rubric_names_all_four_qa_layers():
    for layer in ("Content QA", "Semantic-visual QA", "Structural QA", "Behavioral QA"):
        assert layer in RUBRIC_TEXT, f"QA layers omit {layer}"


def test_final_pass_requires_more_than_structural_and_behavioral():
    assert "cannot receive a final pass" in RUBRIC_TEXT
    assert "FOUR QA layers" in SKILL_TEXT


def test_gates_a_b_e_are_defined_with_their_failure_behavior():
    for gate in ("Gate A", "Gate B", "Gate E"):
        assert gate in RUBRIC_TEXT, f"rubric omits {gate}"
    # Placement is the whole value: Gate A revises the outline, not the HTML.
    assert "revise the OUTLINE" in RUBRIC_TEXT
    assert "redesign or REMOVE" in RUBRIC_TEXT
    # Gate E stays optional on purpose - a subjective judgment must not block.
    assert "OPTIONAL and reader-level" in RUBRIC_TEXT


def test_command_publishes_the_delegated_helper_manifest():
    assert "Runtime helper manifest" in COMMAND_TEXT
    for helper in (
        "extract_content.py",
        "ensure_render_env.py",
        "visual_qa_score.py",
        "fit_map_projection.py",
    ):
        assert helper in COMMAND_TEXT, f"helper manifest omits {helper}"
    # The defect was a guessed path, so the rule against guessing is explicit.
    assert "Do not search for a helper by name" in COMMAND_TEXT
