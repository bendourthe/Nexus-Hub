"""v3.16.5 Phase 4: the two-round design intake.

Two surfaces have to agree, and they are authored in different files by different
edits, so drift between them is the failure mode worth guarding:

1. The four-option additional-imagery question (R8) - procedural visuals became the
   ALWAYS-ON baseline, so the question asks what to ADD rather than which tier to
   use. The legacy `--images` spellings must still bind, because a user's saved
   command line should not break silently.
2. Intake ROUND 2 (R10) - three content-derived color schemes plus Other, asked
   after extraction because that is the only point at which a scheme CAN be
   content-derived. The chosen scheme pins the palette through
   `design_seed.py --scheme-hint` while the sampler keeps rolling every other axis.

The `design_seed.py` assertions run the real script rather than asserting on its
prose, since `--scheme-hint` is behavior, not documentation.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = (
    _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
)
_SKILL = _BUNDLE / "SKILL.md"
_SEED_PATH = _BUNDLE / "scripts" / "design_seed.py"
_COMMAND = _ROOT / "catalog" / "commands" / "presentify.md"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


seed_mod = _load(_SEED_PATH, "design_seed")

SKILL_TEXT = _SKILL.read_text(encoding="utf-8")
COMMAND_TEXT = _COMMAND.read_text(encoding="utf-8")


# --- 1. the four-option additional-imagery question (R8) ---------------------


def test_both_surfaces_offer_the_four_imagery_values():
    for name, text in (("SKILL.md", SKILL_TEXT), ("presentify.md", COMMAND_TEXT)):
        for value in ("none", "stock", "ai", "both"):
            assert f"`{value}`" in text, f"{name} does not name the `{value}` option"


def test_the_command_usage_line_lists_exactly_the_current_values():
    assert "[--images <none|stock|ai|both>]" in COMMAND_TEXT
    # The superseded enumeration must be gone from the usage line, or a reader
    # copies a spelling the question no longer offers.
    assert "<procedural|stock|ai|auto|none>" not in COMMAND_TEXT


def test_legacy_images_spellings_are_documented_as_aliases():
    # A saved command line must not break silently. Both surfaces state the
    # mapping, because a user may read either one.
    for name, text in (("SKILL.md", SKILL_TEXT), ("presentify.md", COMMAND_TEXT)):
        assert "procedural" in text and "->" in text, f"{name} lacks an alias mapping"
        for legacy in ("`procedural`", "`auto`", "`mix`"):
            assert legacy in text, f"{name} does not mention the legacy {legacy}"


def test_procedural_is_stated_as_the_always_on_baseline():
    assert "ALWAYS-ON" in SKILL_TEXT or "always-on" in SKILL_TEXT
    # `None` must be described so it does not read as a bare page - the whole
    # reason the option is worded "additional imagery".
    assert "NOT a bare page" in COMMAND_TEXT or "not a bare page" in COMMAND_TEXT.lower()


def test_the_none_semantic_change_is_disclosed_rather_than_hidden():
    # The old `none` meant "no visuals at all". That mode is gone, and a silent
    # redefinition of a flag value is worse than a documented one.
    for name, text in (("SKILL.md", SKILL_TEXT), ("presentify.md", COMMAND_TEXT)):
        assert "no longer exists" in text, f"{name} hides the `none` behavior change"


def test_consent_invariants_survive_the_rewording():
    # The consent gate is load-bearing and its wording moved from tier names to
    # the new option names; the invariants themselves must not have been dropped.
    assert "consent" in SKILL_TEXT.lower()
    assert "`stock`, `ai`, or `both`" in SKILL_TEXT
    assert "fully offline" in SKILL_TEXT
    # A recalled preference must still never pre-answer a choice.
    assert "NEVER pre-answer" in SKILL_TEXT or "never pre-answers" in SKILL_TEXT


# --- 2. intake ROUND 2 (R10) -------------------------------------------------


def test_both_surfaces_describe_two_rounds():
    assert "ROUND 1" in SKILL_TEXT and "ROUND 2" in SKILL_TEXT
    assert "Round 1" in COMMAND_TEXT and "Round 2" in COMMAND_TEXT


def test_round_two_offers_three_schemes_plus_other():
    assert "THREE" in SKILL_TEXT and "Other" in SKILL_TEXT
    assert "three" in COMMAND_TEXT and "Other" in COMMAND_TEXT
    # The 5-swatch preview is what makes the choice meaningful in a menu.
    assert "5-swatch" in SKILL_TEXT and "5-swatch" in COMMAND_TEXT


def test_round_two_requires_a_cited_content_signal():
    # This is what separates a content-derived scheme from a random palette, and
    # it is the reason the round runs after extraction at all.
    assert "content signal" in SKILL_TEXT
    assert "not content-derived" in SKILL_TEXT or "no citable signal" in SKILL_TEXT


def test_round_two_runs_after_extraction_and_before_the_token_brainstorm():
    round_two = SKILL_TEXT.index("Design intake ROUND 2")
    classify = SKILL_TEXT.index("Classify and reconstruct figures")
    author = SKILL_TEXT.index("Author the interactive website")
    assert classify < round_two < author, "Round 2 is out of pipeline order"


def test_round_two_skips_are_documented_on_both_surfaces():
    for name, text in (("SKILL.md", SKILL_TEXT), ("presentify.md", COMMAND_TEXT)):
        assert "--theme" in text, f"{name} missing the --theme skip"
        assert "tokens.json" in text, f"{name} missing the brand-tokens skip"
        assert "non-interactive" in text.lower(), f"{name} missing the headless skip"


def test_the_pipeline_diagram_shows_both_rounds():
    diagram = SKILL_TEXT[SKILL_TEXT.index("```\ndesign intake") : SKILL_TEXT.index("unique interactive .html")]
    assert "ROUND 1" in diagram
    assert "ROUND 2" in diagram
    assert "PINNED" in diagram, "the diagram must show the palette being pinned"


# --- 3. design_seed.py --scheme-hint is BEHAVIOR, so exercise it -------------


def _roll(tmp_path: Path, *extra: str, seed: str = "7") -> dict:
    out = tmp_path / f"brief-{len(list(tmp_path.iterdir()))}.json"
    result = subprocess.run(
        [sys.executable, str(_SEED_PATH), "--preset", "technical", "--seed", seed,
         "-o", str(out), "--history", str(tmp_path / "history.json"), *extra],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(out.read_text(encoding="utf-8"))


_SCHEME = json.dumps({
    "name": "Field Slate",
    "base_variant": "dark",
    "base": "#0d1b1a",
    "surface": "#132724",
    "ink": "#e8f3f1",
    "accent": "#2fbfae",
    "accent_2": "#6ba3d6",
})


def test_scheme_hint_pins_the_palette(tmp_path):
    brief = _roll(tmp_path, "--scheme-hint", _SCHEME)
    assert brief["palette"]["base"] == "#0d1b1a"
    assert brief["palette"]["accent"] == "#2fbfae"
    assert brief["palette"]["accent_2"] == "#6ba3d6"
    assert brief["base_variant"] == "dark"
    assert "Field Slate" in brief["palette_source"]


def test_scheme_hint_leaves_the_other_axes_to_the_sampler(tmp_path):
    """The point of a CONSTRAINT rather than a replacement: uniqueness is preserved
    within the pinned palette instead of being traded away for it."""
    plain = _roll(tmp_path, seed="7")
    pinned = _roll(tmp_path, "--scheme-hint", _SCHEME, seed="7")
    for axis in ("type", "layout_signature", "motion_personality",
                 "signature_move", "spacing_rhythm", "mood"):
        assert pinned[axis] == plain[axis], f"{axis} should still come from the roll"
    # And a different seed still moves them, so they are genuinely rolled.
    other = _roll(tmp_path, "--scheme-hint", _SCHEME, seed="99")
    assert any(other[axis] != pinned[axis]
               for axis in ("type", "layout_signature", "signature_move"))


def test_scheme_hint_leaves_the_anti_convergence_axis_intact(tmp_path):
    """`hue_family` is one of the rejection axes, so pinning the palette must not
    rewrite it - otherwise the history comparison starts measuring the user's
    color choice instead of the sampler's variety."""
    plain = _roll(tmp_path, seed="7")
    pinned = _roll(tmp_path, "--scheme-hint", _SCHEME, seed="7")
    assert pinned["hue_family"] == plain["hue_family"]
    assert plain["palette_source"].startswith("rolled:")


def test_scheme_hint_accepts_a_hue_family_shorthand(tmp_path):
    family = sorted(seed_mod.HUE_FAMILIES)[0]
    brief = _roll(
        tmp_path, "--scheme-hint",
        json.dumps({"name": "pool shorthand", "hue_family": family, "base_variant": "dark"}),
    )
    expected = seed_mod.HUE_FAMILIES[family]
    assert brief["palette"]["accent"] == expected["accents"][0]
    assert brief["palette"]["base"] == expected["dark"]["base"]


def test_scheme_hint_accepts_a_partial_pin(tmp_path):
    """A scheme may pin only its accents and let the neutrals roll."""
    plain = _roll(tmp_path, seed="7")
    brief = _roll(
        tmp_path, "--scheme-hint", json.dumps({"name": "accents only", "accent": "#ff8800"}),
        seed="7",
    )
    assert brief["palette"]["accent"] == "#ff8800"
    assert brief["palette"]["base"] == plain["palette"]["base"]


def test_scheme_hint_accepts_a_file_path(tmp_path):
    path = tmp_path / "scheme.json"
    path.write_text(_SCHEME, encoding="utf-8")
    brief = _roll(tmp_path, "--scheme-hint", str(path))
    assert brief["palette"]["accent"] == "#2fbfae"


@pytest.mark.parametrize("bad,reason", [
    ("{not json", "malformed JSON"),
    ('["a"]', "not a readable file (a non-brace value is treated as a path)"),
    ('{"accent":"notahex"}', "not a hex color"),
    ('{"base_variant":"sideways"}', "invalid base_variant"),
    ('{"hue_family":"no-such-family"}', "unknown hue family"),
])
def test_a_malformed_scheme_hint_exits_2_rather_than_rolling_unpinned(
    tmp_path, bad, reason
):
    """Degrading to an unpinned palette would ship colors the user did not choose,
    silently. A usage error is the honest outcome."""
    result = subprocess.run(
        [sys.executable, str(_SEED_PATH), "--preset", "technical",
         "-o", str(tmp_path / "out.json"), "--history", str(tmp_path / "h.json"),
         "--scheme-hint", bad],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 2, f"{reason}: expected exit 2, got {result.returncode}"
    assert "--scheme-hint" in result.stderr
    assert not (tmp_path / "out.json").exists(), "no brief may be written on error"


def test_design_seed_documents_the_scheme_hint_flag():
    text = _SEED_PATH.read_text(encoding="utf-8")
    assert "--scheme-hint" in text
    assert "intake ROUND 2" in text or "intake round 2" in text


# --- 4. in-process unit tests for the two new helpers ------------------------
#
# The subprocess tests above prove real end-to-end behavior but are invisible to
# coverage, which cannot trace a child process. These exercise the same logic
# in-process so the new code is measured as well as demonstrated.


def test_load_scheme_hint_parses_inline_json():
    hint = seed_mod.load_scheme_hint('{"name":"X","accent":"#abc"}')
    assert hint == {"name": "X", "accent": "#abc"}


def test_load_scheme_hint_accepts_3_6_and_8_digit_hexes():
    for value in ("#abc", "#aabbcc", "#aabbccdd"):
        assert seed_mod.load_scheme_hint(json.dumps({"accent": value}))["accent"] == value


@pytest.mark.parametrize("raw", [
    "{not json",
    '{"base_variant":"sideways"}',
    '{"hue_family":"nope"}',
    '{"ink":"rgb(0,0,0)"}',
    '{"base":123}',
])
def test_load_scheme_hint_rejects_bad_inline_json(raw):
    with pytest.raises(ValueError):
        seed_mod.load_scheme_hint(raw)


def test_load_scheme_hint_rejects_a_file_whose_json_is_not_an_object(tmp_path):
    """The isinstance guard is reachable only through the FILE path.

    An inline value that does not start with `{` is treated as a path, so
    `load_scheme_hint('["a"]')` fails earlier on "not a readable file" - it never
    reaches the object check. Exercising the guard needs a real file.
    """
    path = tmp_path / "array.json"
    path.write_text('["not", "an", "object"]', encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        seed_mod.load_scheme_hint(str(path))


def test_load_scheme_hint_reports_a_missing_file_rather_than_guessing():
    with pytest.raises(ValueError, match="neither JSON nor a readable file"):
        seed_mod.load_scheme_hint("no/such/scheme.json")


def test_apply_scheme_hint_overlays_only_the_keys_it_declares():
    rolled = {"base": "#111", "surface": "#222", "ink": "#eee",
              "accent": "#f00", "accent_2": "#0f0"}
    merged, variant = seed_mod.apply_scheme_hint(
        dict(rolled), {"accent": "#ff8800"}, "light"
    )
    assert merged["accent"] == "#ff8800"
    assert variant == "light"
    # Everything not named falls through to the rolled palette.
    for key in ("base", "surface", "ink", "accent_2"):
        assert merged[key] == rolled[key]


def test_apply_scheme_hint_explicit_hexes_win_over_a_hue_family():
    family = sorted(seed_mod.HUE_FAMILIES)[0]
    merged, variant = seed_mod.apply_scheme_hint(
        {}, {"hue_family": family, "base_variant": "dark", "accent": "#ff8800"}, "light"
    )
    assert variant == "dark"
    assert merged["accent"] == "#ff8800", "an explicit hex must beat the family accent"
    assert merged["base"] == seed_mod.HUE_FAMILIES[family]["dark"]["base"]


def test_build_brief_records_where_the_palette_came_from():
    candidate = {
        "hue_family": sorted(seed_mod.HUE_FAMILIES)[0], "base_variant": "light",
        "mood": "calm", "neutral_temperature": seed_mod.NEUTRAL_TEMPERATURES[0],
        "type_voice": sorted(seed_mod.TYPE_VOICES)[0],
        "layout_signature": sorted(seed_mod.LAYOUT_SIGNATURES)[0],
        "motion_personality": "springy",
        "signature_move": sorted(seed_mod.SIGNATURE_MOVES)[0],
        "spacing_rhythm": seed_mod.SPACING_RHYTHMS[0],
    }
    rolled = seed_mod.build_brief(dict(candidate), "technical", 1)
    assert rolled["palette_source"].startswith("rolled:")
    pinned = seed_mod.build_brief(
        dict(candidate), "technical", 1, {"name": "Field Slate", "accent": "#2fbfae"}
    )
    assert pinned["palette_source"] == "pinned by intake round 2: Field Slate"
    assert pinned["palette"]["accent"] == "#2fbfae"
    # The rejection axis is untouched, so the history keeps measuring variety.
    assert pinned["hue_family"] == rolled["hue_family"]


# --- 4. coverage depth (verbosity) - v3.16.6 Phase 1 --------------------------
# Same drift-between-surfaces failure mode as the sections above: the question,
# the flag, the fallback, the authoring rules, and the rubric criterion are
# authored in three different files and must keep agreeing.

_RUBRIC = _BUNDLE / "references" / "visual-qa-rubric.md"
RUBRIC_TEXT = _RUBRIC.read_text(encoding="utf-8")


def test_the_usage_line_lists_the_verbosity_flag():
    assert "[--verbosity <distilled|balanced|comprehensive>]" in COMMAND_TEXT


def test_both_surfaces_offer_the_three_verbosity_levels():
    for name, text in (("SKILL.md", SKILL_TEXT), ("presentify.md", COMMAND_TEXT)):
        for level in ("distilled", "balanced", "comprehensive"):
            assert level in text.lower(), f"{name} does not name the {level} level"


def test_verbosity_is_distinguished_from_qa_depth():
    # The two axes are easy to conflate from the flag names alone; the command
    # must draw the line explicitly (content carried vs QA thoroughness).
    assert "--qa-depth" in COMMAND_TEXT
    assert "CONTENT axis" in COMMAND_TEXT or "content axis" in COMMAND_TEXT


def test_the_verbosity_question_is_part_of_round_two():
    # It must be content-derived, which is only possible after extraction.
    skill_round_two = SKILL_TEXT.index("Design intake ROUND 2")
    author = SKILL_TEXT.index("Author the interactive website")
    verbosity_q = SKILL_TEXT.index("Ask the coverage depth (verbosity) in the same round")
    assert skill_round_two < verbosity_q < author, "verbosity question out of pipeline order"
    assert "coverage depth" in COMMAND_TEXT.lower()


def test_the_question_stem_is_content_derived():
    # A generic low/medium/high asked blind is the design this axis rejects:
    # the options carry an approximate section count for THIS source set.
    assert "section count" in SKILL_TEXT
    assert "content-derived size hint" in COMMAND_TEXT or "size hint" in COMMAND_TEXT


def test_the_flag_is_a_preset_that_skips_the_question():
    assert "PRESET" in SKILL_TEXT, "SKILL.md must state the flag wins over the question"
    assert "skips the round-2 coverage-depth question" in COMMAND_TEXT


def test_the_fallback_is_balanced_on_both_surfaces():
    for name, text in (("SKILL.md", SKILL_TEXT), ("presentify.md", COMMAND_TEXT)):
        assert "`balanced`" in text, f"{name} does not name the balanced fallback"
    assert "verbosity -> balanced" in COMMAND_TEXT, "the auto-pick list must include verbosity"


def test_a_malformed_flag_value_degrades_instead_of_blocking():
    for name, text in (("SKILL.md", SKILL_TEXT), ("presentify.md", COMMAND_TEXT)):
        assert "usage note" in text, f"{name} does not document the malformed-value path"
        assert "never blocks" in text, f"{name} must state the run never blocks on it"


def test_the_design_record_carries_level_provenance_and_target():
    assert "`flag-preset` / `asked` / `defaulted`" in SKILL_TEXT
    assert "section-count target" in SKILL_TEXT


def test_the_authoring_step_defines_all_three_depth_rules():
    # The choice must change the outline, not just decorate the record.
    coverage = SKILL_TEXT.index("Coverage depth (apply the resolved verbosity level")
    author = SKILL_TEXT.index("Author the interactive website")
    assert coverage > author, "the depth rules belong to the authoring step"
    for marker in ("**Distilled**", "**Balanced**", "**Comprehensive**"):
        assert marker in SKILL_TEXT, f"authoring rules missing {marker}"


def test_attribution_wins_over_distillation_in_compile_mode():
    assert "WINS over distillation" in SKILL_TEXT or "WINS over" in SKILL_TEXT


def test_a_missing_record_grades_as_balanced_not_a_failure():
    assert "treat the run as `balanced`" in SKILL_TEXT
    assert "grade the page as `balanced`" in RUBRIC_TEXT


def test_the_rubric_has_the_coverage_depth_criterion():
    assert "## The twelve criteria" in RUBRIC_TEXT
    assert "**Coverage-depth match**" in RUBRIC_TEXT
    assert "coverage-depth" in RUBRIC_TEXT  # the schema enum value
    # Page-level, agent-vision only: the maintainer explicitly rejected a
    # deterministic scorer check (word/section-count bands false-positive).
    assert "AGENT-VISION only" in RUBRIC_TEXT
    assert "NEVER raw word counts" in RUBRIC_TEXT


def test_no_stale_criteria_count_survives():
    # The rubric grew to twelve (v3.18.3 slide-mode integrity); a surface still
    # claiming an older count would tell the grader to skip new criteria.
    for name, text in (("SKILL.md", SKILL_TEXT), ("visual-qa-rubric.md", RUBRIC_TEXT)):
        for stale in ("eight", "nine", "ten", "eleven"):
            assert f"{stale} criteria" not in text.lower(),                 f"{name} still says {stale} criteria"
    assert "all twelve criteria" in SKILL_TEXT
    assert "painted-canvas" in RUBRIC_TEXT  # the schema enum value
    assert "**Painted-surface integrity**" in RUBRIC_TEXT
    assert "**Slide-mode integrity**" in RUBRIC_TEXT


def test_depth_never_excuses_readability_floors():
    # A comprehensive run earns more sections, not smaller text; both the
    # authoring rules and the rubric must carry the boundary.
    assert "Depth never excuses" in SKILL_TEXT
    assert "Depth never excuses" in RUBRIC_TEXT


def test_the_rationalization_row_guards_both_directions():
    row = "The user picked comprehensive, but the page flows better short"
    assert row in SKILL_TEXT
    assert "padding a distilled page" in SKILL_TEXT
