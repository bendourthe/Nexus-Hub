"""v3.15.4 Phase 5: iterative multi-agent visual-QA self-critique loop.

Two testable surfaces:

1. The deterministic STRUCTURAL scorer (`scripts/visual_qa_score.py`) flags a
   seeded defective fixture on each structural criterion (narrow full-width
   column, missing image caps, a dropped annotation overlay, a consented mix run
   with zero imagery, a non-offline page) and passes a clean fixture. It also
   degrades cleanly (structural mode, no browser needed) and drives the CLI exit
   codes.

1b. (v3.16.5) The four `references/responsive-typography.md` checks: fluid macro
   spacing, the rendered font-size floors (checked at BOTH the clamp minimum and
   1920px), emphasis-token distinctness, and WCAG contrast. Each is exercised on a
   clean fluid fixture plus one fixture per seeded defect class, including the
   near-miss cases that make the checks trustworthy rather than noisy: micro
   spacing is not flagged, SVG user-unit text is exempt from the px floors, a
   region-scoped `footer code` rule does not stand in for the page-wide one, and
   semantic status colors stay out of the contrast set.

2. The Dynamic-Workflow template (`assets/visual-qa-workflow.js`) and the rubric
   reference carry the required content: the three mandatory workflow rules
   (graceful degradation, scope-first token caution, skill-native) and the five
   rubric criteria. The template is an adapt-me artifact (not executed here), so
   these are structural assertions on the files.

The scorer is stdlib-only, so these tests are dependency-free (they run in both
the deps-light ci.yml tests job and the presentify-extractor workflow). The
scorer is loaded by path via importlib, matching test_media_key_setup.py.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = (
    _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
)
_SCORER_PATH = _BUNDLE / "scripts" / "visual_qa_score.py"
_WORKFLOW_PATH = _BUNDLE / "assets" / "visual-qa-workflow.js"
_RUBRIC_PATH = _BUNDLE / "references" / "visual-qa-rubric.md"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scorer = _load(_SCORER_PATH, "visual_qa_score")

# A clean full-width page: canvas vars filling the viewport, the image caps, an
# annotated overlay with a region + view-original toggle, and an embedded image.
_CLEAN = (
    '<html data-aspect="full">'
    "<style>:root{--page-max: 100%; --gutter: clamp(1rem, 2vw, 2rem);}"
    " figure img{max-height: 80vh; object-fit: contain;}</style>"
    '<figure class="fig-annotated"><div class="fig-figure">'
    '<img src="data:image/png;base64,AAAA">'
    '<div class="fig-overlay"><div class="fig-region">North</div></div></div>'
    '<label class="fig-view-original">View original</label></figure>'
    # Scored with expect_images=1 below, i.e. as a CONSENTED run - so it carries
    # the placement record such a run is required to write (v3.16.5 Phase 5).
    "<!--\nIMAGERY PLACEMENTS\n"
    "  placement: figure | contextual | embedded | the annotated source figure\n"
    "-->"
    "</html>"
)


def _fails(result: dict) -> set[str]:
    return {f["criterion"] for f in result["findings"] if f["status"] == "fail"}


# --- 1. structural scorer: clean passes, each seeded defect is flagged --------


def test_scorer_clean_page_passes():
    result = scorer.score_html(_CLEAN, expect_images=1)
    assert result["page_pass"] is True
    assert result["high_severity"] == 0
    assert result["mode"] == "structural"


def test_scorer_flags_narrow_full_width():
    narrow = _CLEAN.replace("--page-max: 100%", "--page-max: 600px")
    result = scorer.score_html(narrow)
    assert result["page_pass"] is False
    assert "full-width" in _fails(result)


def test_scorer_flags_missing_image_caps():
    nocaps = (
        '<html data-aspect="standard"><figure>'
        '<img src="data:image/png;base64,AAAA"></figure></html>'
    )
    result = scorer.score_html(nocaps)
    assert result["page_pass"] is False
    assert "image-sizing" in _fails(result)


def test_scorer_flags_dropped_overlay():
    dropped = (
        '<html data-aspect="standard"><style>figure img{max-height: 80vh;'
        " object-fit: contain;}</style>"
        '<figure class="fig-annotated"></figure></html>'
    )
    result = scorer.score_html(dropped)
    assert result["page_pass"] is False
    assert "annotation-fidelity" in _fails(result)


def test_scorer_flags_zero_imagery_on_consented_expectation():
    text_only = '<html data-aspect="standard"><p>text only</p></html>'
    result = scorer.score_html(text_only, expect_images=1)
    assert result["page_pass"] is False
    assert "imagery-integration" in _fails(result)


def test_scorer_flags_external_reference():
    not_offline = (
        '<html data-aspect="standard"><style>figure img{max-height: 80vh;'
        ' object-fit: contain;}</style>'
        '<link rel="stylesheet" href="https://cdn.example.com/x.css">'
        '<img src="data:image/png;base64,AAAA"></html>'
    )
    result = scorer.score_html(not_offline)
    assert result["page_pass"] is False
    assert "readability-layout" in _fails(result)


def test_scorer_na_criteria_do_not_block():
    # Standard aspect, no figures, no imagery expectation: the applicable
    # criteria are n/a and the page passes structurally.
    minimal = "<html data-aspect=\"standard\"><p>Just prose.</p></html>"
    result = scorer.score_html(minimal)
    assert result["page_pass"] is True
    statuses = {f["criterion"]: f["status"] for f in result["findings"]}
    assert statuses["full-width"] == "n/a"
    assert statuses["image-sizing"] == "n/a"
    assert statuses["imagery-integration"] == "n/a"


def test_scorer_cli_exit_codes(tmp_path):
    clean = tmp_path / "clean.html"
    clean.write_text(_CLEAN, encoding="utf-8")
    assert scorer.main([str(clean), "--expect-images", "1"]) == 0

    defect = tmp_path / "defect.html"
    defect.write_text(_CLEAN.replace("--page-max: 100%", "--page-max: 600px"), encoding="utf-8")
    assert scorer.main([str(defect)]) == 1

    assert scorer.main([str(tmp_path / "missing.html")]) == 2


# --- 1b. v3.16.5: the responsive-typography contract checks ------------------
#
# A clean fluid/readable page: a tokenized type scale whose clamp MINIMUMS sit at
# the role floors, fluid macro spacing, an AA-clearing palette, and an
# unqualified `code` rule distinct on both the color and the family axis.
_FLUID = (
    '<html data-aspect="standard"><style>'
    ":root{"
    "--base:#12141a; --surface:#1d212b; --ink:#f2f4f8; --ink-dim:#c3c9d6;"
    "--accent:#8fb6e8;"
    "--step--2: clamp(0.8125rem, 0.78rem + 0.16vw, 0.9375rem);"
    "--step-0: clamp(1rem, 0.94rem + 0.30vw, 1.1875rem);"
    "--gutter: clamp(1.25rem, 4vw, 2.5rem);"
    "}"
    "body{font-size:var(--step-0); color:var(--ink); background:var(--base)}"
    ".band{padding-inline:var(--gutter); padding-block:clamp(3.5rem,7vh,7rem)}"
    ".editorial{display:grid; gap:clamp(1.25rem,3vw,3.5rem)}"
    "footer b{font-size:var(--step--2)}"
    "code{font-family:Consolas,monospace; color:var(--accent)}"
    "</style><p>Prose with a <code>/review</code> token.</p></html>"
)


def test_scorer_clean_fluid_page_passes_all_typography_checks():
    result = scorer.score_html(_FLUID)
    statuses = {f["criterion"]: f["status"] for f in result["findings"]}
    assert statuses["fluid-spacing"] == "pass"
    assert statuses["font-floor"] == "pass"
    assert statuses["emphasis-token"] == "pass"
    assert statuses["contrast"] == "pass"
    assert result["page_pass"] is True


def test_scorer_flags_fixed_macro_spacing_on_a_band():
    fixed = _FLUID.replace(
        ".editorial{display:grid; gap:clamp(1.25rem,3vw,3.5rem)}",
        ".editorial{display:grid; gap:2rem}",
    )
    result = scorer.score_html(fixed)
    finding = next(f for f in result["findings"] if f["criterion"] == "fluid-spacing")
    assert finding["status"] == "fail"
    # One occurrence is a slip (MEDIUM), not a page-blocking layout failure.
    assert finding["severity"] == "medium"


def test_scorer_escalates_three_fixed_macro_dimensions_to_high():
    fixed = (
        _FLUID.replace(
            ".editorial{display:grid; gap:clamp(1.25rem,3vw,3.5rem)}",
            ".editorial{display:grid; gap:2rem}",
        )
        .replace("padding-inline:var(--gutter)", "padding-inline:40px")
        .replace("padding-block:clamp(3.5rem,7vh,7rem)", "padding-block:3rem")
    )
    result = scorer.score_html(fixed)
    finding = next(f for f in result["findings"] if f["criterion"] == "fluid-spacing")
    assert finding["severity"] == "high"
    assert result["page_pass"] is False


def test_scorer_ignores_component_internal_micro_spacing():
    # A chip's own padding is component-internal and may stay rem-based.
    micro = _FLUID.replace(
        "footer b{font-size:var(--step--2)}",
        "footer b{font-size:var(--step--2)} .chip{padding:.35rem .6rem}",
    )
    finding = next(
        f for f in scorer.score_html(micro)["findings"]
        if f["criterion"] == "fluid-spacing"
    )
    assert finding["status"] == "pass"


def test_scorer_flags_secondary_text_below_the_13px_floor():
    # The v3.16.5 root-cause defect: the fluid clamp sits on body while a child
    # is sized in rem, so it resolves against the 16px ROOT and never scales.
    small = _FLUID.replace("footer b{font-size:var(--step--2)}", "footer b{font-size:.7rem}")
    result = scorer.score_html(small)
    finding = next(f for f in result["findings"] if f["criterion"] == "font-floor")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "11.2px" in finding["evidence"]
    assert result["page_pass"] is False


def test_scorer_checks_the_clamp_minimum_not_only_the_1920px_value():
    # Resolves to 16px at 1920px but bottoms out at 11px on a laptop width, which
    # is the size most readers get. Checking only the wide viewport misses it.
    sneaky = _FLUID.replace(
        "footer b{font-size:var(--step--2)}",
        "footer b{font-size:clamp(0.6875rem, 0.5rem + 0.6vw, 1rem)}",
    )
    finding = next(
        f for f in scorer.score_html(sneaky)["findings"]
        if f["criterion"] == "font-floor"
    )
    assert finding["status"] == "fail"
    assert "11.0px" in finding["evidence"]


def test_scorer_exempts_svg_user_unit_text_from_the_font_floors():
    # SVG text declares its size in viewBox user units, so a px floor is
    # meaningless; the `fill:` declaration is the discriminator.
    svg_text = _FLUID.replace(
        "code{font-family:Consolas,monospace; color:var(--accent)}",
        "code{font-family:Consolas,monospace; color:var(--accent)}"
        " .nlabel{fill:var(--ink-dim); font-size:9px}",
    )
    finding = next(
        f for f in scorer.score_html(svg_text)["findings"]
        if f["criterion"] == "font-floor"
    )
    assert finding["status"] == "pass"


def test_scorer_resolves_step_tokens_instead_of_treating_var_as_opaque():
    # Regression guard against an inverted incentive: if `var(...)` read as
    # opaque, a page that correctly moved its type onto a tokenized scale would
    # be checked LESS than one hardcoding sizes, and a malformed step token would
    # ship silently.
    broken_token = _FLUID.replace(
        "--step--2: clamp(0.8125rem, 0.78rem + 0.16vw, 0.9375rem);",
        "--step--2: 0.6rem;",
    )
    result = scorer.score_html(broken_token)
    finding = next(f for f in result["findings"] if f["criterion"] == "font-floor")
    assert finding["status"] == "fail"
    # The message names the DECLARED token, not just the resolved pixels, so the
    # reader knows which scale step to fix.
    assert "var(--step--2)" in finding["evidence"]
    assert "9.6px" in finding["evidence"]


def test_resolve_var_follows_indirection_and_honors_a_fallback():
    props = {"--a": "var(--b)", "--b": "0.9rem"}
    assert scorer.resolve_var("var(--a)", props) == "0.9rem"
    assert scorer.resolve_var("var(--missing, 1.25rem)", props) == "1.25rem"
    # Undeclared with no fallback stays unresolved rather than silently becoming 0.
    assert scorer.resolve_var("var(--nope)", props) == "var(--nope)"


def test_scorer_flags_indistinguishable_emphasis_tokens():
    muted = _FLUID.replace(
        "code{font-family:Consolas,monospace; color:var(--accent)}",
        "code{font-family:Consolas,monospace}",
    )
    result = scorer.score_html(muted)
    finding = next(f for f in result["findings"] if f["criterion"] == "emphasis-token")
    assert finding["status"] == "fail"
    assert "no color" in finding["evidence"]
    assert result["page_pass"] is False


def test_scorer_does_not_accept_a_region_scoped_token_rule_as_page_wide_proof():
    # `footer code` styles ONE region. Accepting it would pass a page whose
    # page-wide tokens are still invisible - the observed shipping defect.
    scoped = _FLUID.replace(
        "code{font-family:Consolas,monospace; color:var(--accent)}",
        "code{font-family:Consolas,monospace} footer code{color:var(--accent)}",
    )
    finding = next(
        f for f in scorer.score_html(scoped)["findings"]
        if f["criterion"] == "emphasis-token"
    )
    assert finding["status"] == "fail"
    assert "base" in finding["evidence"]


def test_scorer_emphasis_token_is_na_without_token_markup():
    no_tokens = _FLUID.replace("<code>/review</code>", "/review")
    finding = next(
        f for f in scorer.score_html(no_tokens)["findings"]
        if f["criterion"] == "emphasis-token"
    )
    assert finding["status"] == "n/a"


def test_contrast_ratio_matches_the_wcag_reference_values():
    assert scorer.contrast_ratio("#ffffff", "#000000") == 21.0
    assert round(scorer.contrast_ratio("#777777", "#ffffff"), 2) == 4.48
    assert scorer.contrast_ratio("not-a-color", "#000000") is None


def test_scorer_flags_a_foreground_unusable_on_every_background_as_high():
    unusable = _FLUID.replace("--accent:#8fb6e8;", "--accent:#3d4d66;")
    result = scorer.score_html(unusable)
    finding = next(f for f in result["findings"] if f["criterion"] == "contrast")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert result["page_pass"] is False


def test_scorer_grades_a_single_failing_surface_as_medium():
    # --ink-dim clears AA on --base but not on the lighter --surface: the color is
    # usable, just not on that one surface.
    partial = _FLUID.replace("--surface:#1d212b;", "--surface:#8d93a3;")
    result = scorer.score_html(partial)
    finding = next(f for f in result["findings"] if f["criterion"] == "contrast")
    assert finding["status"] == "fail"
    assert finding["severity"] == "medium"
    assert result["page_pass"] is True  # MEDIUM alone does not block


def test_scorer_excludes_semantic_status_colors_from_the_contrast_set():
    # A badge color whose applicable floor is 3:1 (large / bordered text) must not
    # be graded against the 4.5:1 body floor, since its rendered size is unknown.
    status = _FLUID.replace("--accent:#8fb6e8;", "--accent:#8fb6e8; --stop:#c25050;")
    finding = next(
        f for f in scorer.score_html(status)["findings"]
        if f["criterion"] == "contrast"
    )
    assert finding["status"] == "pass"


def test_len_px_resolves_additive_clamp_preferred_terms():
    # `0.94rem + 0.30vw` at 1920px = 15.04 + 5.76 = 20.8, clamped to the 19px max.
    assert round(scorer._len_px("clamp(1rem, 0.94rem + 0.30vw, 1.1875rem)", 1920), 2) == 19.0
    assert round(scorer._clamp_min_px("clamp(1rem, 0.94rem + 0.30vw, 1.1875rem)"), 2) == 16.0


def test_css_rules_extracts_media_nested_rules_and_skips_the_prelude():
    rules = scorer.css_rules(
        "<style>@media (max-width:600px){.band{gap:1rem}}</style>"
    )
    assert rules == [(".band", {"gap": "1rem"})]


def test_responsive_typography_reference_states_the_floors_and_rules():
    text = (_BUNDLE / "references" / "responsive-typography.md").read_text(
        encoding="utf-8"
    )
    for anchor in (
        "Fluid space, never fixed space",
        "Wrapping serves the viewport",
        "Scale the ROOT, not the elements",
        "Minimum rendered sizes",
        "Emphasis tokens must be visually distinct",
        "Contrast floors",
    ):
        assert anchor in text, f"contract missing rule: {anchor}"
    # The floors are stated as numbers, not as "small but readable".
    assert "16px" in text and "13px" in text and "12px" in text
    # E1's corollary: root scaling does nothing below the root clamp's minimum,
    # which is where a page verified only at wide viewports carries its defects.
    assert "clamp's minimum" in text or "clamp minimum" in text
    assert "1366" in text, "the contract must name the width where the root pins"


# --- 1c. v3.16.5 Phase 2: the svg-diagram-quality contract -------------------
#
# A clean diagram: one marker definition, attached with marker-end, a connector
# terminating on the box edges, and a height-constrained sticky container.
_MARKER = (
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"'
    ' markerWidth="6" markerHeight="6" orient="auto" markerUnits="strokeWidth">'
    '<path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>'
)
_SVG_OK = (
    '<html data-aspect="standard"><style>'
    ".rail-sticky{position:sticky;top:5.5rem}"
    ".rail-sticky svg{width:100%;height:auto;max-height:calc(100vh - 7rem)}"
    "</style>"
    '<div class="rail-sticky"><svg viewBox="0 0 300 200">' + _MARKER +
    '<rect x="30" y="14" width="240" height="52"/>'
    '<path class="flow" d="M150 66 L150 96" marker-end="url(#arrow)"/>'
    '<rect x="30" y="96" width="240" height="52"/>'
    "</svg></div></html>"
)


def _svg_finding(html: str, criterion: str) -> dict:
    return next(
        f for f in scorer.score_html(html)["findings"] if f["criterion"] == criterion
    )


def test_scorer_clean_diagram_passes_all_svg_checks():
    result = scorer.score_html(_SVG_OK)
    statuses = {f["criterion"]: f["status"] for f in result["findings"]}
    assert statuses["svg-arrowhead"] == "pass"
    assert statuses["svg-viewport-fit"] == "pass"
    assert statuses["svg-marker-integrity"] == "pass"
    assert result["page_pass"] is True


def test_scorer_flags_a_hand_placed_triangle_arrowhead():
    # The 2026-08-10 defect: a filled triangle sitting near a line end, which
    # detaches from it the moment the geometry moves.
    detached = _SVG_OK.replace(
        '<path class="flow" d="M150 66 L150 96" marker-end="url(#arrow)"/>',
        '<path class="flow" d="M150 66 L150 96"/>'
        '<path d="M150 96 l -4 -8 l 8 0 z" fill="#5a3434"/>',
    )
    finding = _svg_finding(detached, "svg-arrowhead")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "detaches" in finding["evidence"]


def test_scorer_does_not_flag_the_triangle_inside_a_marker_definition():
    # A marker's own arrowhead IS a small filled triangle by design. Flagging it
    # would make the correct construction unusable.
    assert _svg_finding(_SVG_OK, "svg-arrowhead")["status"] == "pass"
    assert "M0 0 L10 5 L0 10 z" in _SVG_OK  # the marker triangle is really there


def test_scorer_flags_inconsistently_applied_arrowheads():
    # A pipeline whose first connector has a head and whose rest do not reads as
    # an unfinished drawing. Medium: the arrows exist, they are just uneven.
    uneven = _SVG_OK.replace(
        '<rect x="30" y="96" width="240" height="52"/>',
        '<rect x="30" y="96" width="240" height="52"/>'
        '<path class="flow" d="M150 148 L150 178"/>',
    )
    finding = _svg_finding(uneven, "svg-arrowhead")
    assert finding["status"] == "fail"
    assert finding["severity"] == "medium"
    assert "inconsistently" in finding["evidence"]


def test_scorer_accepts_a_marker_attached_from_css():
    # A marker does NOT inherit from the element referencing it, so a connector
    # whose stroke changes with state needs a second marker swapped in by CSS.
    # Reading attributes only would report this correct page as headless.
    css_attached = _SVG_OK.replace(
        ".rail-sticky{position:sticky;top:5.5rem}",
        ".rail-sticky{position:sticky;top:5.5rem} .flow{marker-end:url(#arrow)}",
    ).replace(' marker-end="url(#arrow)"', "")
    assert _svg_finding(css_attached, "svg-arrowhead")["status"] == "pass"
    assert _svg_finding(css_attached, "svg-marker-integrity")["status"] == "pass"


def test_scorer_flags_an_unconstrained_svg_in_a_sticky_container():
    unpinned = _SVG_OK.replace(
        ".rail-sticky svg{width:100%;height:auto;max-height:calc(100vh - 7rem)}",
        ".rail-sticky svg{width:100%;height:auto}",
    )
    result = scorer.score_html(unpinned)
    finding = next(
        f for f in result["findings"] if f["criterion"] == "svg-viewport-fit"
    )
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "unreachable" in finding["evidence"]
    assert result["page_pass"] is False


def test_scorer_ignores_a_sticky_container_that_holds_no_svg():
    # A sticky page nav or table header is not a pinned graphic.
    nav = (
        '<html data-aspect="standard"><style>#nav{position:sticky;top:0}</style>'
        '<nav id="nav"><a href="#a">A</a></nav>'
        '<svg viewBox="0 0 10 10"><rect x="1" y="1" width="2" height="2"/></svg>'
        "</html>"
    )
    assert _svg_finding(nav, "svg-viewport-fit")["status"] == "pass"


def test_scorer_flags_a_dangling_marker_reference_as_high():
    # A reference to a marker that does not exist renders NO arrowhead, silently.
    dangling = _SVG_OK.replace('marker-end="url(#arrow)"', 'marker-end="url(#nope)"')
    finding = _svg_finding(dangling, "svg-marker-integrity")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "#nope" in finding["evidence"]


def test_scorer_flags_an_unreferenced_marker_as_medium():
    unused = _SVG_OK.replace(' marker-end="url(#arrow)"', "")
    result = scorer.score_html(unused)
    finding = next(
        f for f in result["findings"] if f["criterion"] == "svg-marker-integrity"
    )
    assert finding["status"] == "fail"
    assert finding["severity"] == "medium"
    assert result["page_pass"] is True  # dead definition, not a broken render


def test_parse_svg_refuses_entity_declarations():
    # Hardening without a dependency: the entity-expansion DoS class needs an
    # inline <!ENTITY, so a block carrying one is refused unparsed. stdlib
    # ElementTree does not resolve external entities, so XXE does not apply.
    bomb = (
        '<svg viewBox="0 0 10 10"><!DOCTYPE svg [<!ENTITY a "aaaa">]>'
        "<rect/></svg>"
    )
    assert scorer._parse_svg(bomb) is None
    assert scorer._parse_svg('<svg viewBox="0 0 10 10"><rect/></svg>') is not None


def test_is_small_triangle_discriminates_arrowheads_from_real_shapes():
    assert scorer._is_small_triangle("M96 40 l -5 -8 l 10 0 z") is True
    assert scorer._is_small_triangle("M0 0 L10 5 L0 10 z") is True
    # A large closed triangle is a real shape, not an arrowhead.
    assert scorer._is_small_triangle("M0 0 L200 100 L0 200 z") is False
    # A connector is not closed.
    assert scorer._is_small_triangle("M150 66 L150 96") is False
    # A curve is not a triangle even when small and closed.
    assert scorer._is_small_triangle("M0 0 C 5 5, 8 8, 0 10 z") is False


def test_path_points_tracks_relative_and_absolute_commands():
    commands, points = scorer._path_points("M10 10 l 5 0 L 30 10 v 5 z")
    assert commands == ["M", "L", "L", "V", "Z"]
    assert points == [(10.0, 10.0), (15.0, 10.0), (30.0, 10.0), (30.0, 15.0)]


def test_svg_diagram_quality_reference_states_all_five_rules():
    text = (_BUNDLE / "references" / "svg-diagram-quality.md").read_text(
        encoding="utf-8"
    )
    for anchor in (
        "Arrowheads are `<marker>` elements",
        "Dash patterns must not collide",
        "Connectors terminate on node edges",
        "Viewport fit for pinned and sticky graphics",
        "Geometry self-check before shipping",
    ):
        assert anchor in text, f"contract missing rule: {anchor}"
    # The marker attributes that make a head behave are named, not implied.
    assert 'orient="auto"' in text and 'markerUnits="strokeWidth"' in text


# --- 1d. v3.16.5 Phase 3: the render environment + the calibration fixture ---

_ENSURE_RENDER = _BUNDLE / "scripts" / "ensure_render_env.py"
ensure_env = _load(_ENSURE_RENDER, "ensure_render_env")

# The calibration fixture is a STANDING gate rather than a one-time manual check.
# Homed here by v3.16.5 Phase 7 (closing MT-1); the dual-candidate lookup that
# carried it through the move is gone, since keeping it would leave a second
# accepted location nobody maintains. Skipped rather than failed when absent, so a
# checkout without it degrades instead of erroring.
_CALIBRATION_PATH = (
    _ROOT / "tests" / "fixtures" / "presentify" / "nexus-hub-unit-test-workflow.html"
)
_CALIBRATION = _CALIBRATION_PATH if _CALIBRATION_PATH.is_file() else None


@pytest.mark.skipif(_CALIBRATION is None, reason="calibration fixture not present")
def test_calibration_fixture_passes_every_structural_criterion():
    """The standing regression gate for the whole contract set.

    This is what turns the fixture from an artifact someone once fixed into a
    check that fails when either the fixture OR the scorer regresses. Both
    directions matter: a scorer change that stops detecting a defect is as bad as
    a fixture change that reintroduces one.
    """
    result = scorer.score_file(_CALIBRATION)
    failures = [
        f"{f['criterion']}: {f['evidence']}"
        for f in result["findings"]
        if f["status"] == "fail" and f.get("severity") == "high"
    ]
    assert not failures, "calibration fixture regressed:\n  " + "\n  ".join(failures)
    assert result["page_pass"] is True


@pytest.mark.skipif(_CALIBRATION is None, reason="calibration fixture not present")
def test_calibration_fixture_has_no_stale_palette_literals():
    """The superseded pre-v3.16.5 palette values must not reappear.

    A hex literal in a presentation attribute, a `data-*` attribute, or a canvas
    call is invisible to the CSS contrast check, so it can silently keep a value
    the palette abandoned. Five per-section accents did exactly that (BG-1); this
    pins the fix so it cannot quietly revert.
    """
    # Comments are stripped first, because the contract DOCUMENTS the superseded
    # values (both the design-record header and the CSS note explaining why they
    # were replaced). A live value can only be in markup, CSS, or script, never
    # inside a comment - so stripping comments is what separates a reintroduced
    # defect from a record of the fix. Both comment syntaxes matter: the note
    # sits in a CSS /* */ block, the header in an HTML <!-- --> one.
    text = _CALIBRATION.read_text(encoding="utf-8")
    live = scorer._CSS_COMMENT_RE.sub("", scorer._COMMENT_RE.sub("", text))
    # The needles are split so this test does not itself trip a grep for them.
    stale = {
        "#" + "c26565": "superseded --accent (4.36:1, below AA)",
        "#" + "4f6d8a": "superseded --accent-2 (3.17:1, below AA)",
        "#" + "9c7f7d": "superseded --ink-faint (failed AA on both surfaces)",
    }
    for literal, why in stale.items():
        occurrences = [line for line in live.splitlines() if literal in line]
        assert not occurrences, (
            f"stale palette literal {literal} ({why}) reappeared in live markup:\n  "
            + "\n  ".join(occurrences[:3])
        )


def test_bundled_scripts_are_marked_executable():
    """ruff EXE001 fails the presentify-extractor verify job when a shebang
    script is git mode 100644. Every sibling in this folder is 100755; a new
    script that ships without the bit (ensure_render_env.py on the v3.16.6
    release) turns a green local run into a red Linux CI job."""
    listed = subprocess.check_output(
        ["git", "ls-files", "-s", "--", "catalog/skills/specialized-domains/document-to-interactive-html/scripts"],
        cwd=_ROOT,
        text=True,
    )
    py_scripts = []
    for line in listed.splitlines():
        mode, _object, _stage, path = line.split(maxsplit=3)
        if path.endswith(".py"):
            py_scripts.append(path)
            assert mode == "100755", (
                f"{path} is git mode {mode}; ruff EXE001 will fail CI on Linux"
            )
    assert py_scripts, "expected bundled Python scripts under scripts/"


def test_ensure_render_env_probe_reports_a_state_and_never_installs():
    """The probe is read-only and always classifies the host."""
    state = ensure_env.probe()
    assert state["state"] in {
        "READY_PLAYWRIGHT", "READY_LOCAL_BROWSER",
        "NEED_BROWSER", "NEED_PLAYWRIGHT", "NEED_ALL",
    }
    assert state["ready"] is (state["exit_code"] in (0, 10))
    # A non-ready state must always hand the user something runnable.
    if not state["ready"]:
        assert state["remedy"], "a non-ready state must name its remedy commands"


def test_ensure_render_env_exit_codes_are_distinct_per_state(monkeypatch):
    """A caller must be able to branch on the exit code without parsing text."""
    cases = {
        (True, True, None): 0,        # READY_PLAYWRIGHT
        (True, False, "chrome"): 10,  # READY_LOCAL_BROWSER
        (True, False, None): 20,      # NEED_BROWSER
        (False, False, "chrome"): 21, # NEED_PLAYWRIGHT
        (False, False, None): 22,     # NEED_ALL
    }
    for (has_pw, has_chromium, browser), expected in cases.items():
        monkeypatch.setattr(ensure_env, "playwright_available", lambda v=has_pw: v)
        monkeypatch.setattr(
            ensure_env, "bundled_chromium_available", lambda v=has_chromium: v
        )
        monkeypatch.setattr(
            ensure_env, "find_local_browser",
            lambda v=browser: __import__("pathlib").Path(v) if v else None,
        )
        assert ensure_env.probe()["exit_code"] == expected, (
            f"playwright={has_pw} chromium={has_chromium} browser={browser}"
        )
        assert ensure_env.main(["--json"]) == expected


def test_ensure_render_env_degrades_on_a_host_with_nothing(monkeypatch, capsys):
    """The no-browser, no-pip host: report and exit, never crash, and name the
    remedy so the agent can offer it once rather than degrade silently."""
    monkeypatch.setattr(ensure_env, "playwright_available", lambda: False)
    monkeypatch.setattr(ensure_env, "bundled_chromium_available", lambda: False)
    monkeypatch.setattr(ensure_env, "find_local_browser", lambda: None)
    code = ensure_env.main([])
    assert code == 22
    text = capsys.readouterr().err
    assert "NEED_ALL" in text
    assert "pip install playwright" in text
    assert "DISCLOSE" in text  # the degradation must be disclosed, not silent


def test_ensure_render_env_install_is_never_implicit(monkeypatch):
    """No code path may install without --install; --dry-run proves the commands
    without running them."""
    calls: list = []
    monkeypatch.setattr(ensure_env.subprocess, "run", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(ensure_env, "playwright_available", lambda: False)
    monkeypatch.setattr(ensure_env, "bundled_chromium_available", lambda: False)
    monkeypatch.setattr(ensure_env, "find_local_browser", lambda: None)

    ensure_env.main([])                      # a bare probe
    ensure_env.main(["--json"])              # a JSON probe
    ensure_env.main(["--install", "--dry-run"])
    assert calls == [], "no subprocess may run without an explicit --install"

    assert ensure_env.main(["--dry-run"]) == 2  # --dry-run alone is a usage error


def test_render_gate_fails_instead_of_skipping_when_a_browser_was_promised():
    """The MT-1 lesson: a job that installed a browser and then skipped the
    browser-dependent checks anyway told nobody. NEXUS_REQUIRE_RENDER=1 converts
    that silence into a failure, while local behavior stays skip-with-note."""
    conftest_text = (_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "def render_gate()" in conftest_text
    assert "NEXUS_REQUIRE_RENDER" in conftest_text
    assert "pytest.fail" in conftest_text and "pytest.skip" in conftest_text
    # Every browser-dependent skip site routes through the gate, AND takes the
    # fixture as a parameter. v3.16.6 CI failed because test_rendered_overlay_toggle
    # called render_gate(...) as a bare name; without the fixture that is a
    # NameError, which is neither a skip nor an enforced fail.
    for name in (
        "test_presentify_layout.py",
        "test_presentify_annotations.py",
        "test_presentify_cinematic.py",
    ):
        path = _ROOT / "tests" / "skills" / name
        text = path.read_text(encoding="utf-8")
        assert "render_gate(" in text, f"{name} does not use the gate"
        assert "pytest.skip(\"no headless browser" not in text, (
            f"{name} still has a raw browser skip that CI cannot enforce"
        )
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            calls_gate = any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "render_gate"
                for child in ast.walk(node)
            )
            if calls_gate:
                args = [arg.arg for arg in node.args.args]
                assert "render_gate" in args, (
                    f"{name}::{node.name} calls render_gate but does not take the fixture"
                )


# --- 1e. v3.16.5 Phase 3: mutation-test the whole contract set ----------------
#
# The plan's acceptance bar for the render loop: "if the loop cannot catch a
# seeded regression (temporarily re-break the loop-back arrow and confirm
# detection), the loop is not done." Generalized from that one case to every
# contract family, because a gate that catches one seeded defect and misses the
# others is not proven. Each mutation is applied to an in-memory copy; the fixture
# on disk is never touched.
def _mutate_declaration(html: str, selector: str, prop: str, value: str) -> str:
    """Replace one declaration inside the rule whose selector matches exactly.

    Anchoring a mutation on a selector rather than on a substring is what lets
    this suite survive the page being re-authored - which it was, wholesale,
    between v3.16.5 Phase 3 and the errata pass.
    """
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", html):
        # `[^{}]+` reaches back to the previous `}`, so it swallows any CSS
        # comment sitting above the rule. Strip comments before comparing, the
        # same way css_rules() does, or a documented rule never matches.
        candidate = re.sub(r"/\*.*?\*/", " ", match.group(1), flags=re.S)
        # For the FIRST rule in a stylesheet, `[^{}]+` also reaches back through
        # the `<style>` tag, so drop anything up to it. Done by prefix rather than
        # by splitting on `>`, which would mangle a child combinator like
        # `.rail-steps>article`.
        candidate = re.sub(r"^[\s\S]*<style[^>]*>", "", candidate)
        if " ".join(candidate.split()) != selector:
            continue
        decl = re.search(rf"({re.escape(prop)}\s*:\s*)([^;}}]+)", match.group(2))
        if decl is None:
            continue
        start = match.start(2) + decl.start(2)
        return html[:start] + value + html[start + len(decl.group(2)):]
    raise AssertionError(f"no rule `{selector}` declaring `{prop}`")


# One seeded defect per contract family. The plan asked only for the loop-back
# arrow to be re-broken; a gate that catches one seeded defect and misses the
# others is not proven, so every family is covered.
_SEEDED_DECLARATIONS = [
    pytest.param(".rail-sticky svg", "height", "auto", "svg-viewport-fit", "high",
                 id="uncapped-pinned-graphic"),
    pytest.param("footer b", "font-size", ".6875rem", "font-floor", "high",
                 id="secondary-size-below-13px"),
    pytest.param(":root", "--accent", "#2f6f68", "contrast", "high",
                 id="accent-below-AA"),
    pytest.param("code", "color", "var(--ink)", "emphasis-token", "high",
                 id="token-colour-matches-body-ink"),
    pytest.param(".band", "padding-inline", "40px", "fluid-spacing", "medium",
                 id="fixed-px-band-padding"),
]

# Two defects are structural rather than declarative, so they stay literal.
_SEEDED_MARKUP = [
    pytest.param(
        '<path class="loopback" d="M270 368 C 322 368, 322 122, 270 122" marker-end="url(#mLoop)"/>',
        '<path class="loopback" d="M270 368 C 322 368, 322 122, 270 122"/>'
        '<path d="M270 122 l 8 -4 l 0 8 z" fill="var(--accent-2)"/>',
        "svg-arrowhead", id="detached-loopback-arrowhead",
    ),
    pytest.param('marker-end="url(#mLoop)"', 'marker-end="url(#gone)"',
                 "svg-marker-integrity", id="dangling-marker-reference"),
    pytest.param('style="font-family:var(--f-head);font-size:.8125rem',
                 'style="font-family:var(--f-head);font-size:.72rem',
                 "font-floor", id="inline-style-below-13px"),
]


def _assert_seeded_defect_caught(
    clean: str, seeded: str, criterion: str, severity: str = "high"
) -> None:
    assert seeded != clean, "the mutation did not apply - anchor drifted"
    result = scorer.score_html(seeded)
    finding = next(f for f in result["findings"] if f["criterion"] == criterion)
    assert finding["status"] == "fail", (
        f"seeded {criterion} defect went undetected: {finding['evidence']}"
    )
    assert finding.get("severity") == severity
    # Only HIGH blocks; a MEDIUM finding is surfaced for the fix pass but does not
    # by itself fail the page. Asserting otherwise would force the severity policy
    # to change to suit the test.
    assert result["page_pass"] is (severity != "high")


@pytest.mark.skipif(_CALIBRATION is None, reason="calibration fixture not present")
@pytest.mark.parametrize("selector,prop,value,criterion,severity", _SEEDED_DECLARATIONS)
def test_seeded_declaration_defect_is_detected(
    selector, prop, value, criterion, severity
):
    clean = _CALIBRATION.read_text(encoding="utf-8")
    assert scorer.score_html(clean)["page_pass"], "fixture must be clean before seeding"
    _assert_seeded_defect_caught(
        clean, _mutate_declaration(clean, selector, prop, value), criterion, severity
    )


@pytest.mark.skipif(_CALIBRATION is None, reason="calibration fixture not present")
@pytest.mark.parametrize("old,new,criterion", _SEEDED_MARKUP)
def test_seeded_markup_defect_is_detected(old, new, criterion):
    clean = _CALIBRATION.read_text(encoding="utf-8")
    assert scorer.score_html(clean)["page_pass"], "fixture must be clean before seeding"
    _assert_seeded_defect_caught(clean, clean.replace(old, new, 1), criterion)


# --- 1f. v3.16.5 Phase 3: the checker bugs a real render exposed --------------


def test_len_px_resolves_min_and_max():
    # max() is the idiomatic way to FLOOR a relative size, so a checker that
    # cannot read it would fail the construction the contract asks authors to use.
    assert scorer._len_px("max(.92em, 0.8125rem)", 1920) == 14.72  # .92 * 16
    assert scorer._len_px("max(.5em, 0.8125rem)", 1920) == 13.0
    assert scorer._len_px("min(2rem, 24px)", 1920) == 24.0


def test_font_role_reads_the_last_compound_and_distinguishes_class_from_element():
    # Both directions of the bug a 1920px render exposed: `#nav .brand` styles a
    # non-interactive brand label but contains `nav`, and `.cmd-bar .label` styles
    # a static caption whose CLASS is literally `label`. Grading either against
    # the 12px interactive floor let sub-13px text ship.
    assert scorer._font_role("#nav .brand") == "secondary"
    assert scorer._font_role(".cmd-bar .label") == "secondary"
    # Genuine controls still classify as interactive.
    assert scorer._font_role(".nav a") == "interactive"
    assert scorer._font_role(".cmd-bar button") == "interactive"
    assert scorer._font_role(".ctl label") == "interactive"
    assert scorer._font_role(".btn") == "interactive"
    assert scorer._font_role("a:hover") == "interactive"
    # Body prose and plain secondary text are unaffected.
    assert scorer._font_role("body") == "body"
    assert scorer._font_role("p") == "body"
    assert scorer._font_role("footer b") == "secondary"


def test_inline_style_declarations_are_graded_as_secondary_text():
    # An inline style has no selector to classify, so it takes the SECONDARY floor:
    # the strictest that is not body prose. Guessing `body` would over-fail;
    # guessing `interactive` would under-check, which is what a render caught.
    rules = scorer.inline_style_rules('<span style="font-size:.72rem">x</span>')
    assert rules == [("[style] #1", {"font-size": ".72rem"})]
    assert scorer._font_role("[style] #1") == "secondary"
    page = (
        '<html data-aspect="standard"><style>body{font-size:1rem}</style>'
        '<span style="font-size:.72rem">tiny</span></html>'
    )
    finding = next(
        f for f in scorer.score_html(page)["findings"] if f["criterion"] == "font-floor"
    )
    assert finding["status"] == "fail"
    assert "[style] #1" in finding["evidence"]



# --- 1g. v3.16.5 errata E5: the three defects only a render surfaces ---------

_E5_OK = (
    '<html data-aspect="standard"><style>'
    ":root{--nav-h:3.25rem}"
    "#nav{position:sticky;top:0;height:var(--nav-h)}"
    "thead th{position:sticky;top:var(--nav-h)}"
    "section[id]{scroll-margin-top:calc(var(--nav-h) + 1rem)}"
    "pre{white-space:pre-wrap;overflow-wrap:anywhere}"
    "</style>"
    '<nav id="nav"><a href="#a">A</a></nav>'
    '<section id="a"><pre>a very long command line</pre>'
    "<table><thead><tr><th>H</th></tr></thead></table></section></html>"
)


def _e5(html: str) -> dict:
    return next(
        f for f in scorer.score_html(html)["findings"]
        if f["criterion"] == "render-only-defects"
    )


def test_e5_clean_page_passes():
    assert _e5(_E5_OK)["status"] == "pass"


def test_e5_flags_two_sticky_layers_pinning_to_the_same_offset():
    # A sticky table header beneath a sticky nav stacks two bars, and the lower
    # one covers the content it labels. Invisible in markup, obvious on screen.
    stacked = _E5_OK.replace("thead th{position:sticky;top:var(--nav-h)}",
                             "thead th{position:sticky;top:0}")
    finding = _e5(stacked)
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "same offset" in finding["evidence"]


def test_e5_offsetting_the_lower_sticky_layer_is_accepted():
    # The rule is one layer per OFFSET, not one sticky element per page - a second
    # layer that clears the first is a legitimate construction.
    assert _e5(_E5_OK)["status"] == "pass"
    assert "top:var(--nav-h)" in _E5_OK


def test_e5_flags_anchor_targets_without_scroll_margin():
    # Anchor links that scroll are not the same as anchor links that work: under a
    # sticky nav the heading lands underneath it.
    no_margin = _E5_OK.replace(
        "section[id]{scroll-margin-top:calc(var(--nav-h) + 1rem)}", "")
    finding = _e5(no_margin)
    assert finding["status"] == "fail"
    assert "scroll-margin-top" in finding["evidence"]


def test_e5_anchor_check_is_quiet_without_a_sticky_layer():
    # With nothing pinned, an anchor jump lands correctly and the rule does not apply.
    no_sticky = _E5_OK.replace("#nav{position:sticky;top:0;height:var(--nav-h)}", "").replace(
        "thead th{position:sticky;top:var(--nav-h)}", "").replace(
        "section[id]{scroll-margin-top:calc(var(--nav-h) + 1rem)}", "")
    assert _e5(no_sticky)["status"] == "pass"


def test_e5_flags_a_pre_block_that_neither_wraps_nor_scrolls():
    clipping = _E5_OK.replace("pre{white-space:pre-wrap;overflow-wrap:anywhere}",
                              "pre{white-space:pre}")
    finding = _e5(clipping)
    assert finding["status"] == "fail"
    assert "clipped" in finding["evidence"]


def test_e5_accepts_a_scrolling_pre_block():
    # A scroll container does not LOSE the tail of a line, so it is not the defect
    # even though wrapping is preferred.
    scrolling = _E5_OK.replace("pre{white-space:pre-wrap;overflow-wrap:anywhere}",
                               "pre{white-space:pre;overflow-x:auto}")
    assert _e5(scrolling)["status"] == "pass"


@pytest.mark.skipif(_CALIBRATION is None, reason="calibration fixture not present")
def test_calibration_fixture_holds_the_e5_rules():
    assert _e5(_CALIBRATION.read_text(encoding="utf-8"))["status"] == "pass"


def test_svg_contract_forbids_rotated_labels():
    # E4: rotation is a defect, not a technique. The contract must say so and must
    # show the horizontal + tspan replacement, or the next author repeats it.
    text = (_BUNDLE / "references" / "svg-diagram-quality.md").read_text(encoding="utf-8")
    assert "Do not rotate label text" in text
    assert "tspan" in text
    assert "readability defect" in text


def test_typography_contract_documents_the_render_only_defects():
    text = (_BUNDLE / "references" / "responsive-typography.md").read_text(encoding="utf-8")
    assert "Three defects only a render surfaces" in text
    for anchor in ("scroll-margin-top", "pre-wrap", "sticky"):
        assert anchor in text, f"rule 7 missing {anchor}"

# --- 2. workflow template + rubric carry the required content ----------------


def test_workflow_template_carries_mandatory_rules():
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    # A valid Workflow script starts with the meta literal.
    assert "export const meta" in text
    # Rule 1: graceful degradation ladder (workflow + render).
    assert "isolated subagents" in text
    assert "single sequential agent" in text
    assert "visual_qa_score.py" in text  # structural fallback for the render
    # Rule 2: scope-first token caution.
    assert "5-15x" in text
    assert "CALIBRATE" in text or "Calibrate" in text or "calibrate" in text
    # Rule 3: skill-native (no outbound, local render).
    assert "No outbound call" in text or "no outbound" in text.lower()
    assert "LOCAL" in text
    # Cross-links to the orchestration + budget skills.
    assert "[[agent-orchestration-primitives]]" in text
    assert "[[ai-billing-safeguards]]" in text
    # The grade -> verify -> synthesize shape.
    assert "adversarially verify" in text.lower() or "REFUTE" in text


def test_rubric_reference_lists_all_criteria_and_pass_bar():
    text = _RUBRIC_PATH.read_text(encoding="utf-8")
    for criterion in (
        "Full-width compliance",
        "Image sizing",
        "Annotation fidelity",
        "Imagery integration",
        "Readability and layout integrity",
    ):
        assert criterion in text, f"rubric missing criterion: {criterion}"
    assert "page-level pass bar" in text.lower()
    assert "structural" in text.lower() and "agent-vision" in text.lower()


# --- 1h. v3.16.5 Phase 5: the imagery placement record -----------------------
#
# The placement pass is agent behavior, but its RECORD is an artifact, and the
# record is what makes a deliberate skip distinguishable from a forgotten section.
# That distinction is the whole of v3.15 MT-2, so it is checked deterministically.

_WITH_IMAGE = (
    '<html data-aspect="standard"><style>'
    "figure img{max-height: 80vh; object-fit: contain;}</style>"
    '<figure><img src="data:image/png;base64,AA"></figure>'
)
_RECORD = (
    "<!--\nIMAGERY PLACEMENTS\n"
    "  placement: intro | hero | embedded | the section opens on the coastline\n"
    "  placement: summary | none: no concrete visual subject to depict\n-->"
)


def _imagery(html: str, expect: int = 1) -> dict:
    return next(
        f for f in scorer.score_html(html, expect_images=expect)["findings"]
        if f["criterion"] == "imagery-integration"
    )


def test_placement_record_matching_the_page_passes():
    finding = _imagery(_WITH_IMAGE + _RECORD + "</html>")
    assert finding["status"] == "pass"
    assert "1 embedded" in finding["evidence"]
    assert "1 declined with a reason" in finding["evidence"]


def test_assets_with_no_placement_record_is_a_missing_decision_trail():
    # The MT-2 defect in its purest form: images appeared, and nobody can tell
    # which sections were skipped on purpose.
    finding = _imagery(_WITH_IMAGE + "</html>")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "NO `IMAGERY PLACEMENTS`" in finding["evidence"]


def test_a_record_claiming_more_assets_than_the_page_has_is_flagged():
    over = _WITH_IMAGE + _RECORD.replace(
        "placement: summary | none: no concrete visual subject to depict",
        "placement: summary | background | embedded | a laboratory backdrop",
    ) + "</html>"
    finding = _imagery(over)
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "does not match the page" in finding["evidence"]


def test_an_unexplained_decline_is_medium_not_high():
    # A decline is valid and common; an unexplained one is sloppy but does not
    # break the page, so it must not block it.
    vague = _WITH_IMAGE + (
        "<!--\nIMAGERY PLACEMENTS\n"
        "  placement: intro | hero | embedded | opens on the coastline\n"
        "  placement: summary | none:\n-->"
    ) + "</html>"
    finding = _imagery(vague)
    assert finding["status"] == "fail"
    assert finding["severity"] == "medium"
    result = scorer.score_html(vague, expect_images=1)
    assert result["page_pass"] is True


def test_the_none_path_expects_no_placement_pass_at_all():
    """A `none` / non-consented / non-interactive run stays on the procedural
    baseline by design. With no `--expect-images` expectation the criterion is
    n/a, so the absence of a placement block is not a defect - the procedural
    baseline is the whole design there, not a shortfall."""
    procedural = _WITH_IMAGE + "</html>"
    finding = next(
        f for f in scorer.score_html(procedural)["findings"]
        if f["criterion"] == "imagery-integration"
    )
    assert finding["status"] == "n/a"
    assert scorer.score_html(procedural)["page_pass"] is True


def test_placement_decisions_parses_roles_statuses_and_reasons():
    decisions = scorer.placement_decisions(_RECORD)
    assert [d["section"] for d in decisions] == ["intro", "summary"]
    assert decisions[0]["role"] == "hero"
    assert decisions[0]["status"] == "embedded"
    assert decisions[1]["status"] == "none"
    assert decisions[1]["reason"] == "no concrete visual subject to depict"


def test_placement_decisions_reads_inside_the_design_record_comment():
    # The record lives in an HTML comment on purpose - it is not user-visible - so
    # a parser that stripped comments first would find nothing.
    block = "<!--\nIMAGERY PLACEMENTS\n  placement: a | hero | embedded | x\n-->"
    assert len(scorer.placement_decisions(block)) == 1
    assert scorer.placement_decisions("no placements here") == []


def test_placement_decisions_requires_the_line_start_form():
    """The `placement:` anchor is line-start on purpose: prose that happens to
    contain the word must not be parsed as a decision, or the record's integrity
    check starts counting sentences."""
    assert scorer.placement_decisions(
        "<!-- we reconsidered the placement: hero was wrong here -->"
    ) == []
    # Indentation inside the block is fine; a mid-sentence mention is not.
    assert len(scorer.placement_decisions("\n      placement: a | hero | embedded | x")) == 1


def test_the_placement_taxonomy_and_scrim_recipe_are_documented():
    text = (_BUNDLE / "references" / "interactive-features.md").read_text(encoding="utf-8")
    for role in ("hero / header", "background", "contextual illustration", "gallery"):
        assert role in text, f"placement taxonomy missing the {role} role"
    # The scrim is mandatory and numeric, not "use a dark overlay".
    assert "82%" in text and "scrim" in text
    assert "IMAGERY PLACEMENTS" in text, "the record format must be specified"
